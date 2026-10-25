"""Group C, selection v2 (spec/CASE_SELECTION_v2_regression.md): regression case chosen for low W1 error.

Searches the saved Group A rows only (no model run). Writes a private candidate ledger and private figures PF-J (per station) and
PF-K (common window) to _private/thesis_export/; the public run directory receives counts only (no dates, no readings).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import case_studies as CS
import common as C
import figstyle as S

ONE = pd.Timedelta(days=1)
THR = 0.601
VARS = {"wind": "m/s", "mslp": "hPa", "humidity": "%", "rainfall": "mm"}
SOURCE = "w-cohort-20261024T205646Z-6b7a96"  # fixed by the amendment


def p90_by_station() -> dict:
    r = C.load_raw()
    r = r[r["station_name"].isin(C.PRIMARY) & (r["date"] >= "2015-01-01") & (r["date"] <= "2020-10-14")]
    return {s: float(g["wind_speed"].dropna().quantile(0.9)) for s, g in r.groupby("station_name")}


def wins(win: pd.DataFrame, v: str) -> tuple[np.ndarray, np.ndarray]:
    ew = (win[f"W1_{v}"] - win[f"obs_{v}"]).abs().values
    eb = np.minimum((win[f"pers_{v}"] - win[f"obs_{v}"]).abs().values, (win[f"clim_{v}"] - win[f"obs_{v}"]).abs().values)
    return ew < eb, eb - ew


def candidates(W: pd.DataFrame, p90: dict) -> pd.DataFrame:
    idx = W.set_index(["station", "date"]).sort_index()
    rows = []
    for (s, d), _ in idx.iterrows():
        keys = [(s, d - ONE), (s, d), (s, d + ONE)]
        if not all(k in idx.index for k in keys):
            continue
        win = idx.loc[keys].reset_index()
        complete = bool(win[[f"obs_{v}" for v in VARS] + [f"pers_{v}" for v in VARS]].notna().all().all())
        rec = {"station": s, "date": d, "complete": complete}
        if complete:
            w, m = wins(win, "wind")
            tp = bool(((win["y"] == 1) & (win["x1"] >= THR)).any())
            rec.update({"max_obs_wind": float(win["obs_wind"].max()), "p90": p90[s],
                        "higher_wind": bool(win["obs_wind"].max() >= p90[s]), "tier": 1 if tp else 2,
                        "wind_wins": int(w.sum()), "wind_margin": float(m.sum()),
                        **{f"{v}_wins": int(wins(win, v)[0].sum()) for v in ("mslp", "humidity", "rainfall")}})
        rows.append(rec)
    return pd.DataFrame(rows)


def pick(df: pd.DataFrame):
    q = df[df["complete"] & df["higher_wind"] & (df["wind_wins"] >= 1)]
    if q.empty:
        return None
    return q.sort_values(["tier", "wind_wins", "wind_margin", "max_obs_wind", "date"],
                         ascending=[True, False, False, False, True]).iloc[0]


def err_axes(ax, win, v, unit):
    x = np.arange(3)
    for k, (m, col) in enumerate([("W1", f"W1_{v}"), ("persistence", f"pers_{v}"), ("climatology", f"clim_{v}")]):
        n, c, _, _ = S.METHOD[m]
        e = (win[col] - win[f"obs_{v}"]).abs().values
        ax.bar(x + (k - 1) * 0.26, e, width=0.24, color=c, label=n)
        for xi, ei in zip(x + (k - 1) * 0.26, e):
            ax.text(xi, ei, f"{ei:.1f}", ha="center", va="bottom", fontsize=7)
    ax.set_ylabel(f"|forecast − observed|, {unit}")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.18)
    ax.set_title(f"Absolute {v} error (lower is better)", loc="left")


def grid_axes(ax, win):
    ax.axis("off")
    vs = list(VARS)
    cells = []
    for v in vs:
        row = []
        for i in range(3):
            o = win[f"obs_{v}"].iloc[i]
            e = {"W1": abs(win[f"W1_{v}"].iloc[i] - o), "Persistence": abs(win[f"pers_{v}"].iloc[i] - o),
                 "Climatology": abs(win[f"clim_{v}"].iloc[i] - o)}
            best = min(e.values())
            winners = [k for k, val in e.items() if val == best]
            row.append(" / ".join(winners))
        cells.append(row)
    t = ax.table(cellText=cells, rowLabels=[f"{v} ({VARS[v]})" for v in vs],
                 colLabels=[f"{d:%d %b %Y}" for d in win["date"]], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(8); t.scale(1, 1.6)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor(S.GRID)
        if r > 0 and c >= 0 and "W1" in cell.get_text().get_text():
            cell.set_facecolor("#dbe8fa")
    ax.set_title("Closest forecast per variable and date (W1 shaded)", loc="left")


LABEL = ("Selected example, chosen retrospectively for illustration; not representative of all dates. "
         "Chosen because W1's wind error was smaller than both baselines (selected for low model error, spec/CASE_SELECTION_v2_regression.md).")


def main():
    run = C.new_run("case-v2")
    priv = C.private_dir(run)
    exp = C.PRIVATE / "thesis_export" / run.name
    exp.mkdir(parents=True)
    W = pd.read_csv(C.PRIVATE / "runs" / SOURCE / "website_cohort_rows.csv", parse_dates=["date", "issue_date"])
    p90 = p90_by_station()
    cand = candidates(W, p90)
    cand.to_csv(priv / "PRIVATE_candidate_ledger_v2.csv", index=False)
    comp = cand[cand["complete"]]
    pub = {"run_id": run.name, "criteria": "spec/CASE_SELECTION_v2_regression.md", "source_rows_run": SOURCE,
           "station_wind_p90_training_ms": p90, "windows_total": int(len(cand)), "windows_complete": int(len(comp)),
           "per_station": {}, "common": None, "dates": "withheld from public outputs"}
    summ = {"per_station": {}, "common": None}
    figs = []
    for s in C.PRIMARY:
        c = comp[comp["station"] == s]
        hw = c[c["higher_wind"]]
        pub["per_station"][s] = {
            "complete_windows": int(len(c)), "higher_wind_windows": int(len(hw)),
            "higher_wind_tier1": int((hw["tier"] == 1).sum()),
            "higher_wind_with_wind_win_ge1": int((hw["wind_wins"] >= 1).sum()),
            "higher_wind_tier1_with_wind_win_ge1": int(((hw["wind_wins"] >= 1) & (hw["tier"] == 1)).sum()),
            "higher_wind_with_wind_win_all3": int((hw["wind_wins"] == 3).sum())}
        top = pick(c)
        if top is None:
            pub["per_station"][s]["selected"] = None
            continue
        win = CS.window(W, s, top["date"])
        res = {v: [bool(b) for b in wins(win, v)[0]] for v in VARS}
        pub["per_station"][s].update({"selected": True, "tier": int(top["tier"]), "wind_wins_of_3": int(top["wind_wins"]),
                                      "wins_by_variable_of_3": {v: int(sum(r)) for v, r in res.items()},
                                      "outcomes": [CS.outcome(r.y, r.x1 >= THR) for r in win.itertuples()],
                                      "trigger_on_event_dates": sorted({("pressure fall" if r.L_press else "wind") for r in win.itertuples() if r.y == 1})})
        summ["per_station"][s] = {"window": [f"{t:%Y-%m-%d}" for t in win["date"]], "max_obs_wind": float(win["obs_wind"].max()),
                                  "p90": p90[s], "wins": res}
        fig, axs = plt.subplots(2, 3, figsize=(15, 9.6))
        fig.subplots_adjust(left=0.06, right=0.985, top=0.88, bottom=0.26, hspace=0.75, wspace=0.28)
        a = axs.ravel()
        CS.case_axes({"wind": a[0], "tend": a[4], "score": a[5]}, win)
        a[0].axhline(p90[s], color=S.INK2, lw=0.8, ls=":")
        a[0].text(-0.55, p90[s], f"station 90th percentile\n(2015-2020): {p90[s]:.1f} m/s", ha="left", va="bottom", fontsize=7, color=S.INK2)
        err_axes(a[1], win, "wind", "m/s")
        err_axes(a[2], win, "mslp", "hPa")
        grid_axes(a[3], win)
        for ax in (a[1], a[2]):
            ax.set_xticks(np.arange(3), [f"{t:%d %b %Y}\n(target date)" for t in win["date"]], fontsize=8)
        a[1].legend(loc="upper left", fontsize=7.5, ncol=3)
        S.title(fig, f"PF-J. {s}: selected regression case (low model error) around {top['date']:%d %B %Y}", LABEL)
        S.footer(fig, [CS.TIMING, CS.PROC, CS.BASE,
                       f"Station: {s} (primary). n = 3 station-days. Relatively higher wind = observed wind ≥ the station's training-period 90th percentile "
                       f"({p90[s]:.1f} m/s) on at least one date. Tier {int(top['tier'])} ({'contains a detected event' if top['tier'] == 1 else 'no detected event in the window'}). "
                       f"Pressure, humidity and rainfall were not used to select. Observations: PAGASA; not for online publication. Run {run.name}."], width=190)
        figs += S.save(fig, exp, f"PF-J_regression_case_{s.replace(' ', '_')}")

    # common window
    best = None
    for d, g in comp.groupby("date"):
        if len(g) == 3 and g["higher_wind"].any():
            key = (int(g["wind_wins"].sum()), float(g["wind_margin"].sum()), float(g["max_obs_wind"].max()), -d.value)
            if key[0] >= 1 and (best is None or key > best[0]):
                best = (key, d)
    if best:
        d = best[1]
        pub["common"] = {"selected": True, "station_dates_with_wind_win_of_9": best[0][0]}
        summ["common"] = {"window": [f"{t:%Y-%m-%d}" for t in (d - ONE, d, d + ONE)], "wins_of_9": best[0][0]}
        fig, axs = plt.subplots(3, 3, figsize=(14, 12.5))
        fig.subplots_adjust(left=0.06, right=0.985, top=0.9, bottom=0.18, hspace=0.92, wspace=0.3)
        for i, s in enumerate(C.PRIMARY):
            win = CS.window(W, s, d)
            scratch = plt.figure()  # v1 helper always draws a tendency panel; it is discarded here (space)
            CS.case_axes({"wind": axs[i][0], "score": axs[i][2], "tend": scratch.add_subplot()}, win, show_legend=(i == 0))
            plt.close(scratch)
            err_axes(axs[i][1], win, "wind", "m/s")
            axs[i][1].set_xticks(np.arange(3), [f"{t:%d %b %Y}" for t in win["date"]], fontsize=8)
            axs[i][0].set_title(f"{s}: wind speed", loc="left"); axs[i][1].set_title(f"{s}: absolute wind error", loc="left")
            axs[i][2].set_title(f"{s}: W1+X1 score and outcome", loc="left")
        axs[0][1].legend(loc="upper left", fontsize=7.5, ncol=3)
        S.title(fig, f"PF-K. All three primary stations: selected regression window (low model error) around {d:%d %B %Y}", LABEL)
        S.footer(fig, [CS.TIMING, CS.PROC, CS.BASE, f"Stations: NAIA, Sangley Point, Science Garden. n = 9 station-days. "
                       f"Common-window rule: spec/CASE_SELECTION_v2_regression.md. Observations: PAGASA; not for online publication. Run {run.name}."], width=190)
        figs += S.save(fig, exp, "PF-K_regression_common_window")
    plt.close("all")
    summ["figures"] = figs
    (priv / "PRIVATE_selection_summary_v2.json").write_text(json.dumps(summ, indent=2, default=str), encoding="utf-8")
    (run / "case_selection_v2_summary.json").write_text(json.dumps(pub, indent=2, default=str), encoding="utf-8")
    C.write_manifest(run, {"stage": "Group C selection v2 (regression case chosen for low W1 error)", "spec": "CASE_SELECTION_v2_regression"})
    print(json.dumps(pub, indent=1, default=str)); print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
