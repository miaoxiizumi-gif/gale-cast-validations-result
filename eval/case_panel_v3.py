"""Group D, selection v3 (spec/CASE_SELECTION_v3_panel_validation.md): baseline-failure validation requested by the panel.

Part 1 scores W1 on EVERY date where both persistence and climatology failed (thresholds from the 2015-2020 training period; W1 not
used to choose dates). Part 2 picks illustration windows where W1 did well from those dates. Saved rows only; no model is run.
Public outputs (run dir): aggregates and aggregate figures PF-L, PF-M, PF-N. Private outputs: cell ledger, selected dates and window
figures PF-O (per station), PF-P (common window) in _private/thesis_export/ (PAGASA CADS-07 Rev.6, condition 4).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import case_studies as CS
import common as C
import figstyle as S
import metrics as M

ONE = pd.Timedelta(days=1)
THR = 0.601
SRC_A = "w-cohort-20261024T205646Z-6b7a96"  # fixed by the amendment
SRC_B = "b-benchmark-20261023T162436Z-874640"
T0, T1 = pd.Timestamp("2015-01-01"), pd.Timestamp("2020-10-14")
VARS = {"wind": ("wind_speed", "m/s"), "mslp": ("mean_sea_level_pressure", "hPa"),
        "humidity": ("relative_humidity", "%"), "rainfall": ("rainfall", "mm")}
QS = (0.8, 0.9, 0.95)
Q = 0.9  # primary rule
BS = {"block_days": 14, "B": 2000, "seed": 20261025}
METHODS = ("W1", "persistence", "climatology", "control")
LABEL = ("Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; "
         "not representative of all historical dates.")
SCOPES = ["pooled", *C.PRIMARY]


# ------------------------------------------------------------------------------------------------ thresholds
def thresholds() -> dict:
    """T_pers / T_clim per quantile, station and variable, from raw training-period observations only."""
    r = C.load_raw()
    r = r[r["station_name"].isin(C.PRIMARY) & (r["date"] >= T0) & (r["date"] <= T1)]
    assert not r.duplicated(["station_name", "date"]).any()
    out = {q: {s: {} for s in C.PRIMARY} for q in QS}
    for s, g in r.groupby("station_name"):
        g = g.set_index("date").sort_index()
        days = pd.date_range(g.index.min(), g.index.max(), freq="D")
        for v, (col, _) in VARS.items():
            x = g[col].reindex(days)
            dchg = (x - x.shift(1)).abs().dropna()  # consecutive calendar days only
            mm = g[col].dropna().groupby(g[col].dropna().index.month).mean()
            dev = (x - mm.reindex(x.index.month).values).abs().dropna()
            for q in QS:
                out[q][s][v] = {"T_pers": float(dchg.quantile(q)), "T_clim": float(dev.quantile(q)),
                                "n_pers": int(len(dchg)), "n_clim": int(len(dev))}
    return out


# ------------------------------------------------------------------------------------------------ cells
def cells_A(W: pd.DataFrame, T: dict) -> pd.DataFrame:
    rows = []
    for v in VARS:
        d = pd.DataFrame({"station": W["station"], "date": W["date"], "var": v, "obs": W[f"obs_{v}"],
                          "W1": W[f"W1_{v}"], "persistence": W[f"pers_{v}"], "climatology": W[f"clim_{v}"]})
        rows.append(d)
    c = pd.concat(rows, ignore_index=True)
    return add_errors(c, T)


def add_errors(c: pd.DataFrame, T: dict) -> pd.DataFrame:
    c["complete"] = c[["obs", "W1", "persistence", "climatology"]].notna().all(axis=1)
    c["control"] = 0.5 * (c["persistence"] + c["climatology"])
    for m in METHODS:
        c[f"e_{m}"] = c[m] - c["obs"]
    c["change"] = c["obs"] - c["persistence"]  # observed day-to-day change (issue day -> target)
    for q in QS:
        tp = np.array([T[q][s][v]["T_pers"] for s, v in zip(c["station"], c["var"])])
        tc = np.array([T[q][s][v]["T_clim"] for s, v in zip(c["station"], c["var"])])
        ap, ac = c["e_persistence"].abs(), c["e_climatology"].abs()
        c[f"fail_{q}"] = c["complete"] & (ap >= tp) & (ac >= tc) & (ap > 0) & (ac > 0)
        if q == Q:
            c["T_pers"] = tp
    aw = c["e_W1"].abs()
    c["w1_beats_both"] = c["complete"] & (aw < c["e_persistence"].abs()) & (aw < c["e_climatology"].abs())
    c["success"] = c[f"fail_{Q}"] & c["w1_beats_both"]
    c["margin"] = np.where(c["success"], (np.minimum(c["e_persistence"].abs(), c["e_climatology"].abs()) - aw) / c["T_pers"], 0.0)
    return c


# ------------------------------------------------------------------------------------------------ Part 1 scoring
class Scorer:
    """Point metrics and paired circular block-bootstrap MAE differences over the cohort's target dates."""

    def __init__(self, dates: pd.Series):
        self.dates = np.array(sorted(pd.unique(dates)))
        self.Wt = np.vstack(list(M.block_weights(len(self.dates), BS["block_days"], BS["B"], BS["seed"])))

    def score(self, c: pd.DataFrame) -> dict:
        n = int(len(c))
        out = {"n": n, "n_dates": int(c["date"].nunique()) if n else 0}
        if n == 0:
            return out
        out["point"] = {m: M.wind_stats(c[f"e_{m}"].values) for m in METHODS}
        out["w1_beats_both_share"] = float(c["w1_beats_both"].mean())
        out["w1_beats_both_n"] = int(c["w1_beats_both"].sum())
        codes = np.searchsorted(self.dates, c["date"].values)
        w = self.Wt[:, codes]
        den = w.sum(1)
        ok = den > 0
        mae = {m: np.where(ok, (w @ c[f"e_{m}"].abs().values) / np.where(ok, den, 1), np.nan) for m in METHODS}
        out["ci"] = {}
        for b in ("persistence", "climatology", "control"):
            k = f"dmae_W1_{b}"
            ci = M.ci(list(mae["W1"] - mae[b]))
            ci["verdict"] = M.established(ci)
            out["ci"][k] = ci
            out["point"][k] = out["point"]["W1"]["mae"] - out["point"][b]["mae"]
        return out


def part1(c: pd.DataFrame, sc: Scorer, q: float = Q, full: bool = True) -> dict:
    res = {}
    for v in VARS:
        res[v] = {}
        cv = c[(c["var"] == v) & c["complete"]]
        for s in SCOPES:
            cs = cv if s == "pooled" else cv[cv["station"] == s]
            f_ = cs[cs[f"fail_{q}"]]
            r = {"baseline_failure": sc.score(f_)}
            if full:
                r["all_complete"] = sc.score(cs)
                r["non_failure"] = sc.score(cs[~cs[f"fail_{q}"]])
                sub = {"wind": ("rise", f_["change"] > 0), "rainfall": ("rise", f_["change"] > 0),
                       "mslp": ("fall", f_["change"] < 0), "humidity": ("fall", f_["change"] < 0)}[v]
                r[f"baseline_failure_{sub[0]}"] = sc.score(f_[sub[1]])
            res[v][s] = r
    return res


def onsets(E: pd.DataFrame, clim_thr: float) -> dict:
    """E columns: station, y, persist, p_x1, clim_p."""
    out = {}
    for s in SCOPES:
        e = E if s == "pooled" else E[E["station"] == s]
        on = e[(e["y"] == 1) & (e["persist"] == 0)]
        neg = e[e["y"] == 0]
        out[s] = {"events": int((e["y"] == 1).sum()), "onsets": int(len(on)),
                  "onset_hits": {"W1+X1@0.601": int((on["p_x1"] >= THR).sum()), "event_persistence": int((on["persist"] == 1).sum()),
                                 "event_climatology": int((on["clim_p"] >= clim_thr).sum())},
                  "false_alarms_on_non_events": {"W1+X1@0.601": int((neg["p_x1"] >= THR).sum()),
                                                 "event_persistence": int((neg["persist"] == 1).sum()),
                                                 "event_climatology": int((neg["clim_p"] >= clim_thr).sum())},
                  "non_events": int(len(neg))}
    return out


# ------------------------------------------------------------------------------------------------ Part 2 selection
def windows(c: pd.DataFrame, W: pd.DataFrame) -> pd.DataFrame:
    g = c.groupby(["station", "date"]).agg(succ=("success", "sum"), margin=("margin", "sum"), fails=(f"fail_{Q}", "sum"))
    have = set(zip(W["station"], W["date"]))
    rows = []
    for (s, d) in g.index:
        keys = [(s, d - ONE), (s, d), (s, d + ONE)]
        if not all(k in have for k in keys):
            continue
        sub = g.loc[keys]
        rows.append({"station": s, "date": d, "succ": int(sub["succ"].sum()), "margin": float(sub["margin"].sum()),
                     "fails": int(sub["fails"].sum())})
    return pd.DataFrame(rows)


def rank(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["succ", "margin", "fails", "date"], ascending=[False, False, False, True])


# ------------------------------------------------------------------------------------------------ figures
MCOL = {"W1": S.W1C, "persistence": S.PERC, "climatology": S.CLIMC, "control": "#8a8984"}
MNAME = {"W1": "W1", "persistence": "Persistence", "climatology": "Climatology", "control": "Control: mean of the two baselines"}


# Panel directive (2026-10-25): PF-L's rainfall panel shows 'All complete dates' only. Locked: build_site.py checks the plotted values
# against spec/FROZEN_PF-L_rainfall.json. The baseline-failure rainfall result is still computed and reported (PF-M, CSV, notes).
PFL_GROUPS = {"wind": ("all_complete", "baseline_failure"), "mslp": ("all_complete", "baseline_failure"),
              "humidity": ("all_complete", "baseline_failure"), "rainfall": ("all_complete",)}
GROUP_LABEL = {"all_complete": "All complete\ndates", "baseline_failure": "Baseline-failure\ndates"}


def fig_L(P1: dict, T: dict, out, run) -> list[str]:
    fig, axs = plt.subplots(1, 4, figsize=(15, 6.2))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.84, bottom=0.25, wspace=0.32)
    for ax, (v, (_, unit)) in zip(axs, VARS.items()):
        r = P1[v]["pooled"]
        groups = [(GROUP_LABEL[g], r[g]) for g in PFL_GROUPS[v]]
        x = np.arange(len(groups))
        if len(groups) == 1:
            ax.set_xlim(-0.75, 0.75)
            b = r["baseline_failure"]
            ax.text(0.02, 0.97, f"Shown: all complete dates only\n(panel directive). Baseline-failure\nrainfall dates (n = {b['n']}): W1 "
                    f"{b['point']['W1']['mae']:.1f} vs\npersistence {b['point']['persistence']['mae']:.1f}, climatology "
                    f"{b['point']['climatology']['mae']:.1f} mm\n(see PF-M).", transform=ax.transAxes, ha="left", va="top", fontsize=6.8, color=S.INK2)
        for k, m in enumerate(METHODS):
            vals = [g["point"][m]["mae"] if g["n"] else np.nan for _, g in groups]
            xs = x + (k - 1.5) * 0.2
            ax.bar(xs, vals, width=0.19, color=MCOL[m], label=MNAME[m], hatch="//" if m == "control" else None,
                   edgecolor=S.SURF if m != "control" else "#5d5c58", linewidth=0.4)
            for xi, val in zip(xs, vals):
                ax.text(xi, val, f"{val:.2f}" if val < 10 else f"{val:.1f}", ha="center", va="bottom", fontsize=6.6, rotation=90)
        ax.set_xticks(x, [f"{lab}\n(n = {g['n']:,})" for lab, g in groups], fontsize=8)
        ax.set_ylabel(f"MAE, {unit}")
        ax.set_ylim(0, ax.get_ylim()[1] * (1.28 if len(groups) > 1 else 2.1))
        ax.set_title(v.replace("mslp", "MSLP").capitalize() if v != "mslp" else "MSLP", loc="left")
    axs[0].legend(loc="upper left", fontsize=7.2, ncol=1)
    S.title(fig, "PF-L. Next-day error on dates when both references had large errors, compared with all dates (pooled, three stations)",
            "Evidence D (panel request). " + LABEL + " Dates chosen only by baseline error; W1 is scored on every such date.")
    S.footer(fig, ["Baseline-failure date (per station and variable): |persistence error| ≥ the station's 2015-2020 90th percentile of day-to-day change AND "
                   "|climatology error| ≥ the 90th percentile of deviation from the station × month mean. Persistence = issue-day observation; climatology = "
                   "station × month mean 2015-01-01 to 2020-10-14; control = their average (no model). W1 = saved neural-only next-day output (website scorecard cohort, "
                   f"target dates 2021-11-16 to 2024-12-30). Truth: raw PAGASA observations. Lower is better. Rainfall panel: all complete dates only, by panel "
                   f"directive (locked; spec/FROZEN_PF-L_rainfall.json). Spec: spec/CASE_SELECTION_v3_panel_validation.md. Run {run.name}."],
             width=200)
    return S.save(fig, out, "PF-L_large_error_dates_mae")


def fig_M(P1: dict, out, run) -> list[str]:
    fig, axs = plt.subplots(1, 4, figsize=(15, 6.0))
    fig.subplots_adjust(left=0.1, right=0.99, top=0.8, bottom=0.25, wspace=0.42)
    comps = [("persistence", S.PERC, "s"), ("climatology", S.CLIMC, "^"), ("control", "#5d5c58", "D")]
    for ax, (v, (_, unit)) in zip(axs, VARS.items()):
        ys = np.arange(len(SCOPES))[::-1]
        for k, (b, col, mk) in enumerate(comps):
            for y, s in zip(ys, SCOPES):
                r = P1[v][s]["baseline_failure"]
                if not r["n"]:
                    continue
                ci = r["ci"][f"dmae_W1_{b}"]; pt = r["point"][f"dmae_W1_{b}"]
                yy = y + (1 - k) * 0.22
                ax.plot([ci["lo"], ci["hi"]], [yy, yy], color=col, lw=1.6)
                ax.plot(pt, yy, marker=mk, color=col, ms=6, ls="none", label=f"W1 − {MNAME[b].split(':')[0].lower()}" if y == ys[0] else None)
        ax.axvline(0, color=S.INK2, lw=0.9)
        ax.set_yticks(ys, [f"{s}\n(n = {P1[v][s]['baseline_failure']['n']})" for s in SCOPES], fontsize=8)
        ax.set_xlabel(f"MAE difference, {unit}\n(left of 0 = W1 better)", fontsize=8)
        ax.set_title("MSLP" if v == "mslp" else v.capitalize(), loc="left")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper left", bbox_to_anchor=(0.05, 0.895), fontsize=8, ncol=3)
    S.title(fig, "PF-M. On baseline-failure dates, how much smaller (or larger) is W1's error? Paired differences with 95% intervals",
            "Evidence D (panel request). " + LABEL)
    S.footer(fig, ["Point = W1 MAE minus the comparison's MAE on the same baseline-failure station-dates; line = 95% paired circular block-bootstrap interval "
                   "over target dates (14-day blocks, 2,000 resamples). An interval entirely left of 0 means W1's smaller error is established on these dates. "
                   "The grey control (average of persistence and climatology, no model) shows how much of any advantage a simple hedge also gets. "
                   f"Rule and data as PF-L. Run {run.name}."], width=200)
    return S.save(fig, out, "PF-M_large_error_dates_differences")


def fig_N(OA: dict, OB: dict, out, run) -> list[str]:
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.6))
    fig.subplots_adjust(left=0.07, right=0.99, top=0.8, bottom=0.31, wspace=0.25)
    keys = [("W1+X1@0.601", "W1+X1 (≥ 0.601)", S.W1C), ("event_persistence", "Event persistence", S.PERC),
            ("event_climatology", "Event climatology", S.CLIMC)]
    for ax, (lab, O) in zip(axs, (("Evidence A: website scorecard cases", OA), ("Evidence B: training-consistent benchmark", OB))):
        x = np.arange(len(SCOPES))
        for k, (key, name, col) in enumerate(keys):
            vals = [O[s]["onset_hits"][key] for s in SCOPES]
            xs = x + (k - 1) * 0.26
            ax.bar(xs, vals, width=0.24, color=col, label=name)
            for xi, val in zip(xs, vals):
                ax.text(xi, val, str(val), ha="center", va="bottom", fontsize=7.5)
        ax.plot(x, [O[s]["onsets"] for s in SCOPES], ls="none", marker="_", ms=26, mew=1.6, color=S.INK, label="Event onsets (all)")
        ax.set_xticks(x, [f"{s}\n{O[s]['onsets']} onsets\nfalse alarms:\nW1+X1 {O[s]['false_alarms_on_non_events']['W1+X1@0.601']}, "
                          f"clim. {O[s]['false_alarms_on_non_events']['event_climatology']}" for s in SCOPES], fontsize=7.4)
        ax.set_ylabel("Onsets warned (hits)")
        ax.set_ylim(0, max(O["pooled"]["onsets"], 1) * 1.25)
        ax.set_title(lab, loc="left")
    axs[0].legend(loc="upper right", fontsize=7.5)
    S.title(fig, "PF-N. Event onsets (no event on the issue day, event on the target day): which forecasts warned in time?",
            "Evidence D (panel request). " + LABEL + " Event persistence cannot warn of an onset by construction.")
    S.footer(fig, ["Event = study label (24-hour MSLP fall ≥ 3 hPa or wind ≥ 10.8 m/s; every event here is a pressure fall). Hit = warning issued for the onset date. "
                   "W1+X1 = cross-station mean of W1 probabilities, warning at ≥ 0.601 (threshold adopted after the website results were seen; not an independent test). "
                   "Event climatology = station × month event frequency 2015-2020 against its tuning-year threshold. False alarms are counted on all non-event days. "
                   f"Run {run.name}."], width=190)
    return S.save(fig, out, "PF-N_event_onsets")


def _fmt(v, x):
    return f"{x:.1f}" if v != "rainfall" or x >= 1 else f"{x:.2f}"


def window_axes(ax, cw: pd.DataFrame, v: str, legend=False):
    """cw: the 3 cells (sorted dates) of one variable."""
    x = np.arange(3)
    ax.plot(x, cw["obs"], color=S.OBS, marker="D", lw=2, ms=6.5, label="Observed (PAGASA)", zorder=5)
    for m in ("W1", "persistence", "climatology"):
        n, col, mk, ls = S.METHOD[m]
        ax.plot(x, cw[m], color=col, marker=mk, ls=ls, lw=1.8, ms=6, label=n, zorder=4)
    for i, r in enumerate(cw.itertuples()):
        if r.fail:
            ax.axvspan(i - 0.42, i + 0.42, color="#f3e3d6", zorder=0, lw=0)
        if r.success:
            ax.text(i, 1.0, "★", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=9, color=S.W1C, fontweight="bold")  # meaning in the footer
    vals = cw[["obs", "W1", "persistence", "climatology"]].values.astype(float)
    lo, hi = np.nanmin(vals), np.nanmax(vals)
    pad = max((hi - lo) * 0.25, 0.5 if v != "rainfall" else 1.0)
    ax.set_ylim(max(0, lo - pad) if v in ("wind", "rainfall") else lo - pad, hi + pad)
    ax.set_xticks(x, [f"{d:%d %b %Y}" for d in cw["date"]], fontsize=7.8)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylabel(f"{'MSLP' if v == 'mslp' else v.capitalize()}, {VARS[v][1]}")
    ax.set_title(f"{'MSLP' if v == 'mslp' else v.capitalize()}: observed vs next-day forecasts", loc="left", pad=14)
    if legend:
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.13), fontsize=7.2, ncol=4)


def grid_axes(ax, cwin: pd.DataFrame):
    ax.axis("off")
    dates = sorted(cwin["date"].unique())
    cells, colours = [], []
    for v in VARS:
        row, crow = [], []
        for d in dates:
            r = cwin[(cwin["var"] == v) & (cwin["date"] == d)].iloc[0]
            if not r["complete"]:
                row.append("incomplete"); crow.append(S.SURF); continue
            e = {"W1": abs(r["e_W1"]), "Pers.": abs(r["e_persistence"]), "Clim.": abs(r["e_climatology"])}
            best = min(e.values())
            row.append(" / ".join(k for k, val in e.items() if val == best) + ("  [BF]" if r["fail"] else ""))
            crow.append("#dbe8fa" if r["success"] else ("#f3e3d6" if r["fail"] else S.SURF))
        cells.append(row); colours.append(crow)
    t = ax.table(cellText=cells, rowLabels=["Wind", "MSLP", "Humidity", "Rainfall"], colLabels=[f"{d:%d %b %Y}" for d in dates],
                 cellColours=colours, loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(8); t.scale(1, 1.7)
    for cell in t.get_celld().values():
        cell.set_edgecolor(S.GRID)
    ax.set_title("Closest forecast per variable and date\n[BF] = baseline-failure date\nblue = W1 closest on a BF date", loc="left", fontsize=9)


def score_axes(ax, Wwin: pd.DataFrame):
    x = np.arange(3)
    ax.bar(x, Wwin["x1"], color=S.W1C, width=0.5)
    ax.axhline(THR, color=S.INK2, ls="--", lw=1)
    ax.text(2.45, THR + 0.01, "0.601", va="bottom", ha="right", fontsize=7, color=S.INK2)
    for i, r in enumerate(Wwin.itertuples()):
        ax.text(i, r.x1 + 0.03, CS.outcome(r.y, r.x1 >= THR), ha="center", va="bottom", fontsize=7.5)
    ax.set_ylim(0, 1.15)
    ax.set_xticks(x, [f"{d:%d %b %Y}" for d in Wwin["date"]], fontsize=7.8)
    ax.set_ylabel("W1+X1 score")
    ax.set_title("Event warning: W1+X1 score and outcome", loc="left")


# ------------------------------------------------------------------------------------------------ main
def main():
    run = C.new_run("panel-v3")
    priv = C.private_dir(run)
    exp = C.PRIVATE / "thesis_export" / run.name
    exp.mkdir(parents=True)
    figdir = run / "figures"

    W = pd.read_csv(C.PRIVATE / "runs" / SRC_A / "website_cohort_rows.csv", parse_dates=["date", "issue_date"])
    assert len(W) == 3423 and ((W["date"] - W["issue_date"]) == ONE).all()
    T = thresholds()
    cA = cells_A(W, T)
    cA["fail"] = cA[f"fail_{Q}"]
    sc = Scorer(W["date"])
    P1 = part1(cA, sc)
    sens = {str(q): part1(cA, sc, q, full=False) for q in QS if q != Q}

    # Evidence B wind sensitivity
    Bv = pd.read_csv(C.PRIVATE / "runs" / SRC_B / "cohort_b_rows.csv", parse_dates=["date"])
    Bw = Bv[Bv["elig_wind"]]
    cB = pd.DataFrame({"station": Bw["station"], "date": Bw["date"], "var": "wind", "obs": Bw["wind_obs"], "W1": Bw["wind_W1"],
                       "persistence": Bw["wind_persist"], "climatology": Bw["wind_clim"]}).reset_index(drop=True)
    cB = add_errors(cB, T)
    scB = Scorer(Bv["date"])
    PB = {}
    for s in SCOPES:
        cs = cB[cB["complete"]] if s == "pooled" else cB[cB["complete"] & (cB["station"] == s)]
        PB[s] = {"baseline_failure": scB.score(cs[cs[f"fail_{Q}"]]), "all_complete": scB.score(cs)}

    # event onsets
    Bres = json.loads((C.RUNS / SRC_B / "benchmark_results.json").read_text(encoding="utf-8"))
    kB = [k for k in Bres["events"]["pooled"]["classifiers"] if k.startswith("event_climatology@")][0]
    Ares = json.loads((C.RUNS / SRC_A / "website_cohort_results.json").read_text(encoding="utf-8"))
    thrA, thrB = Ares["event_climatology_threshold"]["threshold"], float(kB.split("@")[1])
    OA = onsets(pd.DataFrame({"station": W["station"], "y": W["y"], "persist": W["E_persist"], "p_x1": W["x1"], "clim_p": W["E_clim"]}), thrA)
    Be = Bv[Bv["elig_event"]]
    OB = onsets(pd.DataFrame({"station": Be["station"], "y": Be["E"], "persist": Be["E_persist"], "p_x1": Be["p_x1"], "clim_p": Be["E_clim"]}), thrB)

    # Part 2
    win = windows(cA, W)
    win.to_csv(priv / "PRIVATE_window_ledger_v3.csv", index=False)
    cA.drop(columns=["control"]).to_csv(priv / "PRIVATE_cell_ledger_v3.csv", index=False)
    Widx = W.set_index(["station", "date"])
    priv_sum = {"per_station": {}, "common": None, "figures": []}
    pub2 = {"per_station": {}, "common": None}
    for s in C.PRIMARY:
        ws = win[win["station"] == s]
        q = rank(ws[ws["succ"] >= 1])
        pub2["per_station"][s] = {"windows": int(len(ws)), "windows_with_success_cell": int((ws["succ"] >= 1).sum()),
                                  "max_success_cells_of_12": int(ws["succ"].max()) if len(ws) else 0}
        if q.empty:
            pub2["per_station"][s]["selected"] = None
            continue
        top = q.iloc[0]
        d = top["date"]
        dates = [d - ONE, d, d + ONE]
        cw = cA[(cA["station"] == s) & cA["date"].isin(dates)].sort_values(["var", "date"])
        Ww = Widx.loc[[(s, t) for t in dates]].reset_index()
        tally = {v: {"baseline_failure_dates": int(cw[cw["var"] == v]["fail"].sum()),
                     "w1_success": int(cw[cw["var"] == v]["success"].sum()),
                     "w1_closest_any_date": int(cw[cw["var"] == v]["w1_beats_both"].sum())} for v in VARS}
        pub2["per_station"][s].update({"selected": True, "success_cells_of_12": int(top["succ"]),
                                       "baseline_failure_cells_of_12": int(top["fails"]), "by_variable": tally,
                                       "outcomes": [CS.outcome(r.y, r.x1 >= THR) for r in Ww.itertuples()]})
        priv_sum["per_station"][s] = {"window": [f"{t:%Y-%m-%d}" for t in dates], "succ": int(top["succ"]), "fails": int(top["fails"]),
                                      "cells": cw[["var", "date", "obs", "W1", "persistence", "climatology", "fail", "success"]]
                                      .assign(date=lambda x: x["date"].dt.strftime("%Y-%m-%d")).to_dict("records")}
        fig, axs = plt.subplots(2, 3, figsize=(15.5, 10))
        fig.subplots_adjust(left=0.06, right=0.985, top=0.83, bottom=0.2, hspace=0.62, wspace=0.3)
        a = axs.ravel()
        for ax, v, lg in zip((a[0], a[1], a[3], a[4]), VARS, (True, False, False, False)):
            window_axes(ax, cw[cw["var"] == v].sort_values("date"), v, legend=lg)
        grid_axes(a[2], cw)
        score_axes(a[5], Ww)
        S.title(fig, f"PF-O. {s}: baseline-failure validation window around {d:%d %B %Y}", LABEL + " Chosen because W1 was closer than both "
                "baselines on dates where both failed (chosen because the model did well; Part 2 of spec/CASE_SELECTION_v3_panel_validation.md).")
        S.footer(fig, ["Shaded date = baseline-failure date for that variable (both baseline errors ≥ the station's 2015-2020 90th percentiles). "
                       "★ = W1 strictly closer than both baselines on that baseline-failure date. Each date is its own next-day forecast issued after the previous "
                       "day's observation; the three dates are not a +1/+2/+3-day forecast from one origin. A gap in a line = PAGASA observation missing (not imputed). "
                       "W1 = saved neural-only output; persistence = issue-day "
                       "observation; climatology = station × month mean 2015-2020. "
                       f"W1 success cells {int(top['succ'])} of 12; baseline-failure cells {int(top['fails'])} of 12. Observations: PAGASA; panel review export. Run {run.name}."],
                 width=200)
        priv_sum["figures"] += S.save(fig, exp, f"PF-O_panel_window_{s.replace(' ', '_')}")

    # common window
    piv = win.pivot_table(index="date", columns="station", values=["succ", "margin", "fails"])
    piv = piv.dropna()
    if len(piv):
        tot = pd.DataFrame({"succ": piv["succ"].sum(1), "margin": piv["margin"].sum(1), "fails": piv["fails"].sum(1)}).reset_index()
        tot = tot[tot["succ"] >= 1]
        if len(tot):
            top = rank(tot).iloc[0]
            d = top["date"]; dates = [d - ONE, d, d + ONE]
            pub2["common"] = {"selected": True, "success_cells_of_36": int(top["succ"]), "baseline_failure_cells_of_36": int(top["fails"]),
                              "by_station_success": {s: int(piv.loc[d, ("succ", s)]) for s in C.PRIMARY}}
            priv_sum["common"] = {"window": [f"{t:%Y-%m-%d}" for t in dates], **pub2["common"]}
            fig, axs = plt.subplots(3, 4, figsize=(17, 12.5))
            fig.subplots_adjust(left=0.05, right=0.99, top=0.87, bottom=0.12, hspace=0.85, wspace=0.32)
            for i, s in enumerate(C.PRIMARY):
                cw = cA[(cA["station"] == s) & cA["date"].isin(dates)]
                for j, v in enumerate(VARS):
                    window_axes(axs[i][j], cw[cw["var"] == v].sort_values("date"), v, legend=(i == 0 and j == 0))
                    axs[i][j].set_title(f"{s}: {'MSLP' if v == 'mslp' else v}", loc="left", pad=14)
            S.title(fig, f"PF-P. All three primary stations: baseline-failure validation window around {d:%d %B %Y}", LABEL)
            S.footer(fig, [f"Common-window rule: Part 2 of spec/CASE_SELECTION_v3_panel_validation.md. W1 success cells {int(top['succ'])} of 36; "
                           f"baseline-failure cells {int(top['fails'])} of 36. Shading and ★ as in PF-O; a gap in a line = PAGASA observation missing (not imputed). Observations: PAGASA; panel review export. Run {run.name}."], width=200)
            priv_sum["figures"] += S.save(fig, exp, "PF-P_panel_common_window")

    # public figures (aggregates only)
    pubfigs = fig_L(P1, T, figdir, run) + fig_M(P1, figdir, run) + fig_N(OA, OB, figdir, run)
    rows = []
    for v in VARS:
        for s in SCOPES:
            for grp in ("all_complete", "baseline_failure", "non_failure"):
                r = P1[v][s][grp]
                if r["n"]:
                    rows.append({"variable": v, "scope": s, "group": grp, "shown_in_PF-L": s == "pooled" and grp in PFL_GROUPS[v], "n": r["n"], **{f"mae_{m}": r["point"][m]["mae"] for m in METHODS},
                                 **{f"rmse_{m}": r["point"][m]["rmse"] for m in METHODS}, "w1_beats_both_share": r["w1_beats_both_share"]})
    pd.DataFrame(rows).to_csv(figdir / "PF-L_large_error_dates_mae.csv", index=False)
    pd.DataFrame([{"variable": v, "scope": s, "n": P1[v][s]["baseline_failure"]["n"], "comparison": b,
                   "dmae": P1[v][s]["baseline_failure"]["point"].get(f"dmae_W1_{b}"),
                   "lo": P1[v][s]["baseline_failure"].get("ci", {}).get(f"dmae_W1_{b}", {}).get("lo"),
                   "hi": P1[v][s]["baseline_failure"].get("ci", {}).get(f"dmae_W1_{b}", {}).get("hi"),
                   "verdict": P1[v][s]["baseline_failure"].get("ci", {}).get(f"dmae_W1_{b}", {}).get("verdict")}
                  for v in VARS for s in SCOPES for b in ("persistence", "climatology", "control")]).to_csv(figdir / "PF-M_large_error_dates_differences.csv", index=False)
    pd.DataFrame([{"evidence": ev, "scope": s, "onsets": O[s]["onsets"], **{f"hits_{k}": n for k, n in O[s]["onset_hits"].items()},
                   **{f"false_alarms_{k}": n for k, n in O[s]["false_alarms_on_non_events"].items()}, "non_events": O[s]["non_events"]}
                  for ev, O in (("A", OA), ("B", OB)) for s in SCOPES]).to_csv(figdir / "PF-N_event_onsets.csv", index=False)

    pub = {"run_id": run.name, "spec": "spec/CASE_SELECTION_v3_panel_validation.md", "label": LABEL, "source_rows": {"A": SRC_A, "B": SRC_B},
           "bootstrap": BS, "thresholds_training_2015_2020": {str(q): T[q] for q in QS}, "part1_A_q90": P1, "part1_A_sensitivity": sens,
           "part1_B_wind_q90": PB, "onsets": {"A": OA, "B": OB, "climatology_thresholds": {"A": thrA, "B": thrB}},
           "part2": pub2, "figures": pubfigs, "dates": "withheld from public outputs"}
    (run / "panel_v3_results.json").write_text(json.dumps(pub, indent=2, default=str), encoding="utf-8")
    (priv / "PRIVATE_selection_summary_v3.json").write_text(json.dumps(priv_sum, indent=2, default=str), encoding="utf-8")
    C.write_manifest(run, {"stage": "Group D selection v3 (baseline-failure validation, panel request)", "spec": "CASE_SELECTION_v3_panel_validation"})
    plt.close("all")
    print(run.name)


if __name__ == "__main__":
    main()
