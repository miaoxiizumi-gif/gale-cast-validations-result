"""Group E, selection v4 (spec/CASE_SELECTION_v4_persistence_override.md): dates where persistence was worse than W1 for BOTH wind and
MSLP (panel directive). Favourable-error selection: W1 beats persistence on these dates by construction.

Saved Evidence A rows only; no model is run. Public outputs (run dir): aggregates and figure PF-Q. Private outputs: qualifying-date
ledger, selected windows and figures PF-R (per station) / PF-S (common window) in _private/thesis_export/ (PAGASA CADS-07 Rev.6, cond. 4).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import case_panel_v3 as V3
import case_regression as CR
import case_studies as CS
import common as C
import figstyle as S

ONE = pd.Timedelta(days=1)
SRC_A = V3.SRC_A
SCOPES = V3.SCOPES
LABEL = ("Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of "
         "all historical dates. Dates selected because persistence's wind and MSLP errors were both larger than W1's.")
SEL = ("wind", "mslp")
UNIT = {"wind": "m/s", "mslp": "hPa"}


def qualify(W: pd.DataFrame, Tp: dict) -> pd.DataFrame:
    q = W[["station", "date", "y", "x1"]].copy()
    q["complete"] = True
    for v in SEL:
        q["complete"] &= W[[f"obs_{v}", f"pers_{v}", f"W1_{v}"]].notna().all(axis=1)
        q[f"ew_{v}"] = (W[f"W1_{v}"] - W[f"obs_{v}"]).abs()
        q[f"ep_{v}"] = (W[f"pers_{v}"] - W[f"obs_{v}"]).abs()
        q[f"ec_{v}"] = (W[f"clim_{v}"] - W[f"obs_{v}"]).abs()
        q[f"beats_pers_{v}"] = q[f"ep_{v}"] > q[f"ew_{v}"]
        q[f"beats_clim_{v}"] = q[f"ec_{v}"] > q[f"ew_{v}"]
        q[f"nmargin_{v}"] = (q[f"ep_{v}"] - q[f"ew_{v}"]) / q["station"].map(lambda s: Tp[s][v]["T_pers"])
    q["qual"] = q["complete"] & q["beats_pers_wind"] & q["beats_pers_mslp"]
    q["clim_cells"] = q["beats_clim_wind"].astype(int) + q["beats_clim_mslp"].astype(int)
    q["nmargin"] = q["nmargin_wind"] + q["nmargin_mslp"]
    return q


def stats(q: pd.DataFrame) -> dict:
    out = {"n": int(len(q))}
    for v in SEL:
        out[v] = {m: float(q[f"e{k}_{v}"].mean()) if len(q) else None for m, k in (("W1", "w"), ("persistence", "p"), ("climatology", "c"))}
        out[v]["W1_beats_climatology_share"] = float(q[f"beats_clim_{v}"].mean()) if len(q) else None
    out["both_beat_climatology_too"] = int((q["clim_cells"] == 2).sum())
    out["events"] = int((q["y"] == 1).sum())
    return out


def windows(q: pd.DataFrame, length: int) -> pd.DataFrame:
    ok = q[q["qual"]].set_index(["station", "date"])
    rows = []
    for (s, d) in ok.index:
        keys = [(s, d + i * ONE) for i in range(length)]
        if all(k in ok.index for k in keys):
            sub = ok.loc[keys]
            rows.append({"station": s, "start": d, "length": length, "clim_cells": int(sub["clim_cells"].sum()),
                         "nmargin": float(sub["nmargin"].sum())})
    return pd.DataFrame(rows, columns=["station", "start", "length", "clim_cells", "nmargin"])


def rank(df):
    return df.sort_values(["clim_cells", "nmargin", "start"], ascending=[False, False, True])


def window_fig(W, cA, q, s, dates, qual_dates, title, out, name, run):
    win = W.set_index(["station", "date"]).loc[[(s, d) for d in dates]].reset_index()
    cw = cA[(cA["station"] == s) & cA["date"].isin(dates)].copy()
    qd = set(qual_dates)
    qq = q.set_index(["station", "date"])
    cw["fail"] = cw["var"].isin(SEL) & cw["date"].isin(qd)  # shaded = qualifying date (persistence worse than W1 for wind AND MSLP)
    cw["success"] = cw["fail"] & cw["w1_beats_both"]          # star = W1 also closer than climatology
    fig, axs = plt.subplots(2, 4, figsize=(19, 10))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.83, bottom=0.2, hspace=0.62, wspace=0.32)
    V3.window_axes(axs[0][0], cw[cw["var"] == "wind"].sort_values("date"), "wind", legend=True)
    CR.err_axes(axs[0][1], win, "wind", "m/s")
    V3.window_axes(axs[0][2], cw[cw["var"] == "mslp"].sort_values("date"), "mslp")
    CR.err_axes(axs[0][3], win, "mslp", "hPa")
    axs[0][3].set_title("Absolute MSLP error (lower is better)", loc="left")
    for ax in (axs[0][1], axs[0][3]):
        ax.set_xticks(np.arange(3), [f"{d:%d %b %Y}" for d in dates], fontsize=7.8)
    axs[0][1].legend(loc="upper left", fontsize=7, ncol=3)
    for ax, v in ((axs[1][0], "humidity"), (axs[1][1], "rainfall")):
        V3.window_axes(ax, cw[cw["var"] == v].sort_values("date"), v)
        ax.set_title(f"{v.capitalize()} (not used to select)", loc="left", pad=14)
    V3.score_axes(axs[1][2], win)
    axs[1][3].axis("off")
    lines = [f"{d:%d %b %Y}: " + ("qualifies" if d in qd else "context date (does not qualify)") +
             (f"; W1 also beats climatology on {int(qq.loc[(s, d), 'clim_cells'])} of 2 (wind, MSLP)" if d in qd else "") for d in dates]
    axs[1][3].text(0, 1, "Selection outcome per date\n\n" + "\n\n".join(lines), va="top", ha="left", fontsize=8.5, transform=axs[1][3].transAxes, wrap=True)
    S.title(fig, title, LABEL)
    S.footer(fig, ["Shaded (wind and MSLP panels) = qualifying date: |persistence error| > |W1 error| for both wind and MSLP (spec/CASE_SELECTION_v4_persistence_override.md). "
                   "★ = W1 also closer than climatology there. W1 beats persistence on shaded dates by construction. Each date is its own next-day forecast issued after the "
                   "previous day's observation; not a +1/+2/+3-day forecast from one origin. A gap in a line = PAGASA observation missing (not imputed). W1 = saved neural-only "
                   f"output; persistence = issue-day observation; climatology = station × month mean 2015-2020. Observations: PAGASA; not for online publication. Run {run.name}."],
             width=230)
    return S.save(fig, out, name)


def fig_Q(P: dict, out, run) -> list[str]:
    fig, axs = plt.subplots(1, 3, figsize=(15, 6))
    fig.subplots_adjust(left=0.06, right=0.99, top=0.8, bottom=0.27, wspace=0.3)
    x = np.arange(len(SCOPES))
    ax = axs[0]
    ax.bar(x, [P["qualifying"][s]["n"] for s in SCOPES], color=S.W1C, width=0.55)
    for i, s in enumerate(SCOPES):
        ax.text(i, P["qualifying"][s]["n"], f"{P['qualifying'][s]['n']}\n({P['share'][s] * 100:.1f}% of {P['complete'][s]})", ha="center", va="bottom", fontsize=7.6)
    ax.set_xticks(x, SCOPES, fontsize=8); ax.set_ylabel("Qualifying station-dates")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.25)
    ax.set_title("How many dates qualify", loc="left")
    for ax, v in zip(axs[1:], SEL):
        for k, m in enumerate(("W1", "persistence", "climatology")):
            n, col, _, _ = S.METHOD[m]
            vals = [P["qualifying"][s][v][m] for s in SCOPES]
            xs = x + (k - 1) * 0.26
            ax.bar(xs, vals, width=0.24, color=col, label=n)
            for xi, val in zip(xs, vals):
                ax.text(xi, val, f"{val:.2f}", ha="center", va="bottom", fontsize=7, rotation=90)
        ax.set_xticks(x, SCOPES, fontsize=8); ax.set_ylabel(f"MAE on qualifying dates, {UNIT[v]}")
        ax.set_ylim(0, ax.get_ylim()[1] * 1.3)
        ax.set_title(f"{'Wind' if v == 'wind' else 'MSLP'}: error on qualifying dates", loc="left")
    axs[1].legend(loc="upper left", fontsize=7.5, ncol=3)
    S.title(fig, "PF-Q. Dates on which persistence was worse than W1 for both wind and MSLP: how many, and errors on them",
            "Evidence E (panel directive). " + LABEL + " W1 < persistence on these dates holds by construction; climatology is not used to select.")
    S.footer(fig, ["Qualifying station-date: |persistence error| > |W1 error| for wind AND for MSLP (strict). Share = qualifying / station-dates with complete wind and MSLP. "
                   "W1 = saved neural-only next-day output (website scorecard cohort, target dates 2021-11-16 to 2024-12-30); persistence = issue-day observation; "
                   f"climatology = station × month mean 2015-2020; truth = raw PAGASA observations. Spec: spec/CASE_SELECTION_v4_persistence_override.md. Run {run.name}."], width=200)
    return S.save(fig, out, "PF-Q_persistence_worse_dates")


# Panel directive (2026-10-25): one 2x2 composite in section 8.E, each panel on its own favourably selected subset.
COMPOSITE_NAME = "PF-L_composite_favourable"
COMPOSITE_LABEL = ("Selected favorable validation example chosen to demonstrate baseline limitations as requested by the thesis panel; "
                   "not representative of all historical dates.")
COMPOSITE_SCOPE = {"wind": "v4 dates (persistence worse than W1 for wind and MSLP)", "mslp": "v4 dates (persistence worse than W1 for wind and MSLP)",
                   "humidity": "v3 baseline-failure dates for humidity", "rainfall": "all complete dates"}
COMPOSITE_TITLE = {"wind": "Wind speed (m/s)", "mslp": "Mean sea-level pressure (hPa)", "humidity": "Relative humidity (%)", "rainfall": "Daily rainfall (mm)"}
M3 = ("W1", "persistence", "climatology")


def composite(q: pd.DataFrame, cA: pd.DataFrame) -> dict:
    """MAE of W1, persistence and climatology per panel, each on its own subset (pooled over the three primary stations)."""
    out = {}
    qq = q[q["complete"] & q["qual"]]
    for v in ("wind", "mslp"):
        out[v] = {"n": int(len(qq)), **{m: float(qq[f"e{k}_{v}"].mean()) for m, k in zip(M3, ("w", "p", "c"))}}
    for v, mask in (("humidity", cA["fail_0.9"]), ("rainfall", cA["complete"])):
        c = cA[(cA["var"] == v) & cA["complete"] & mask]
        out[v] = {"n": int(len(c)), **{m: float(c[f"e_{m}"].abs().mean()) for m in M3}}
    for v, r in out.items():
        r.update({"scope": COMPOSITE_SCOPE[v], "w1_lower_than_both": bool(r["W1"] < r["persistence"] and r["W1"] < r["climatology"])})
    return out


def fig_composite(CP: dict, P: dict, out, run) -> list[str]:
    fig, axs = plt.subplots(2, 2, figsize=(13, 10.4))
    fig.subplots_adjust(left=0.07, right=0.985, top=0.84, bottom=0.15, wspace=0.24, hspace=0.46)
    x = np.arange(3)
    for ax, v in zip(axs.ravel(), ("wind", "mslp", "humidity", "rainfall")):
        r = CP[v]
        vals = [r[m] for m in M3]
        ax.bar(x, vals, width=0.6, color=[S.METHOD[m][1] for m in M3])
        for xi, val in zip(x, vals):
            ax.text(xi, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)
        ax.set_xticks(x, [S.METHOD[m][0] for m in M3], fontsize=9)
        ax.set_ylabel("MAE (lower is better)")
        ax.set_ylim(0, max(vals) * 1.18)
        ax.set_title(f"{COMPOSITE_TITLE[v]}\nSubset: {r['scope']} · n = {r['n']:,}", loc="left", fontsize=9.5)
    S.title(fig, "PF-L composite. Next-day error of W1, persistence and climatology on four favourably selected subsets",
            COMPOSITE_LABEL + " Each panel uses a different subset; the subsets were chosen so that W1's error is lower than both baselines.", width=150)
    S.footer(fig, ["Wind and MSLP: station-dates on which persistence's error exceeded W1's for both wind and MSLP (spec/CASE_SELECTION_v4_persistence_override.md; "
                   "W1 < persistence there by construction). Humidity: dates on which persistence and climatology both failed for humidity (training 90th-percentile rule, "
                   "spec/CASE_SELECTION_v3_panel_validation.md). Rainfall: all complete dates. On all complete dates persistence is more accurate than W1 for wind "
                   f"({P['all_complete']['pooled']['wind']['persistence']:.2f} vs {P['all_complete']['pooled']['wind']['W1']:.2f} m/s), MSLP "
                   f"({P['all_complete']['pooled']['mslp']['persistence']:.2f} vs {P['all_complete']['pooled']['mslp']['W1']:.2f} hPa) and humidity (PF-F3). "
                   "W1 = saved neural-only next-day output (website scorecard cohort, three primary stations, 2021-11-16 to 2024-12-30); persistence = issue-day "
                   f"observation; climatology = station × month mean 2015-2020; truth = raw PAGASA observations. Run {run.name}."], width=175)
    return S.save(fig, out, COMPOSITE_NAME)


def main():
    run = C.new_run("persist-v4")
    priv = C.private_dir(run)
    exp = C.PRIVATE / "thesis_export" / run.name
    exp.mkdir(parents=True)
    W = pd.read_csv(C.PRIVATE / "runs" / SRC_A / "website_cohort_rows.csv", parse_dates=["date", "issue_date"])
    assert len(W) == 3423
    T = V3.thresholds()
    Tp = T[0.9]
    cA = V3.cells_A(W, T)
    q = qualify(W, Tp)
    q.to_csv(priv / "PRIVATE_qualifying_ledger_v4.csv", index=False)
    comp = q[q["complete"]]
    Q = comp[comp["qual"]]
    P = {"complete": {}, "qualifying": {}, "share": {}, "all_complete": {}}
    for s in SCOPES:
        cs = comp if s == "pooled" else comp[comp["station"] == s]
        qs = cs[cs["qual"]]
        P["complete"][s], P["share"][s] = int(len(cs)), float(len(qs) / len(cs))
        P["qualifying"][s], P["all_complete"][s] = stats(qs), stats(cs)
    monthly = Q.assign(month=Q["date"].dt.to_period("M").astype(str)).groupby(["station", "month"]).size().rename("qualifying_dates").reset_index()

    # windows
    priv_sum = {"per_station": {}, "common": None, "figures": []}
    pub_w = {"per_station": {}, "common": None}
    for s in C.PRIMARY:
        qs = q[q["station"] == s]
        w3 = windows(qs, 3)
        w2 = windows(qs, 2) if w3.empty else pd.DataFrame()
        pub_w["per_station"][s] = {"three_date_windows": int(len(w3)), "two_date_windows_used": bool(w3.empty)}
        pick = rank(w3).iloc[0] if len(w3) else (rank(w2).iloc[0] if len(w2) else None)
        if pick is None:
            pub_w["per_station"][s]["selected"] = None
            continue
        qual_dates = [pick["start"] + i * ONE for i in range(int(pick["length"]))]
        dates = qual_dates if len(qual_dates) == 3 else [qual_dates[0] - ONE, *qual_dates]
        pub_w["per_station"][s].update({"selected": True, "length": int(pick["length"]), "W1_beats_climatology_cells": int(pick["clim_cells"]),
                                        "of_cells": 2 * int(pick["length"])})
        priv_sum["per_station"][s] = {"window": [f"{d:%Y-%m-%d}" for d in dates], "qualifying": [f"{d:%Y-%m-%d}" for d in qual_dates],
                                      "clim_cells": int(pick["clim_cells"]), "nmargin": float(pick["nmargin"])}
        priv_sum["figures"] += window_fig(W, cA, q, s, dates, qual_dates,
                                          f"PF-R. {s}: persistence worse than W1 for wind and MSLP, around {dates[1]:%d %B %Y}", exp,
                                          f"PF-R_persistence_window_{s.replace(' ', '_')}", run)
    # common window: three consecutive dates qualifying at all three stations
    common = None
    for s0, d in windows(q[q["station"] == C.PRIMARY[0]], 3)[["station", "start"]].itertuples(index=False):
        per = [windows(q[(q["station"] == s) & q["date"].between(d, d + 2 * ONE)], 3) for s in C.PRIMARY]
        if all(len(p) for p in per):
            key = (sum(int(p.iloc[0]["clim_cells"]) for p in per), sum(float(p.iloc[0]["nmargin"]) for p in per))
            if common is None or key > common[0] or (key == common[0] and d < common[1]):
                common = (key, d)
    pub_w["common"] = {"exists": common is not None}
    if common:
        d = common[1]
        dates = [d, d + ONE, d + 2 * ONE]
        pub_w["common"].update({"W1_beats_climatology_cells_of_18": common[0][0]})
        priv_sum["common"] = {"window": [f"{t:%Y-%m-%d}" for t in dates], "clim_cells": common[0][0]}
    # public figure and data
    figdir = run / "figures"
    pubfigs = fig_Q(P, figdir, run)
    CP = composite(q, cA)
    pubfigs += fig_composite(CP, P, figdir, run)
    pd.DataFrame([{"variable": v, "subset": r["scope"], "n": r["n"], **{f"mae_{m}": r[m] for m in M3}, "w1_lower_than_both": r["w1_lower_than_both"]}
                  for v, r in CP.items()]).to_csv(figdir / f"{COMPOSITE_NAME}.csv", index=False)
    pd.DataFrame([{"scope": s, "complete_station_dates": P["complete"][s], "qualifying": P["qualifying"][s]["n"], "share": P["share"][s],
                   **{f"{v}_mae_{m}_qualifying": P["qualifying"][s][v][m] for v in SEL for m in ("W1", "persistence", "climatology")},
                   **{f"{v}_mae_{m}_all": P["all_complete"][s][v][m] for v in SEL for m in ("W1", "persistence", "climatology")}}
                  for s in SCOPES]).to_csv(figdir / "PF-Q_persistence_worse_dates.csv", index=False)
    monthly.to_csv(run / "qualifying_dates_by_month.csv", index=False)
    pub = {"run_id": run.name, "spec": "spec/CASE_SELECTION_v4_persistence_override.md", "label": LABEL, "source_rows": SRC_A,
           "complete": P["complete"], "share": P["share"], "qualifying": P["qualifying"], "all_complete": P["all_complete"],
           "windows": pub_w, "composite": CP, "figures": pubfigs, "dates": "withheld from public outputs"}
    (run / "persistence_v4_results.json").write_text(json.dumps(pub, indent=2, default=str), encoding="utf-8")
    (priv / "PRIVATE_selection_summary_v4.json").write_text(json.dumps(priv_sum, indent=2, default=str), encoding="utf-8")
    C.write_manifest(run, {"stage": "Group E selection v4 (persistence worse than W1 for wind and MSLP, panel directive)",
                           "spec": "CASE_SELECTION_v4_persistence_override"})
    plt.close("all")
    print(run.name)
    print(json.dumps({"share": P["share"], "qualifying_n": {s: P["qualifying"][s]["n"] for s in SCOPES}, "windows": pub_w}, indent=1, default=str))
    print(json.dumps(priv_sum, indent=1, default=str))


if __name__ == "__main__":
    main()
