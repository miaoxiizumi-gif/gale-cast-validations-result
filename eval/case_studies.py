"""Group C: retrospectively selected illustrative case studies (spec/CASE_SELECTION_v1.md).

Applies the committed criteria to the Group A true positives, writes a private candidate ledger and the
private case figures (PF-H per station, PF-I common window). Case figures plot individual PAGASA station-day
readings, so they are written ONLY to _private/thesis_export/ (PAGASA CADS-07 Rev.6 condition 4). The public run
directory receives only the selection summary (dates and criteria outcomes, no readings).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import common as C
import figstyle as S

THR = 0.601
ONE = pd.Timedelta(days=1)


def latest(prefix):
    return sorted(p for p in C.RUNS.glob(f"{prefix}-*") if not (p / "FAILED.txt").exists())[-1]


def outcome(y, dec):
    return {(1, 1): "Hit", (0, 0): "Correct negative", (1, 0): "Miss", (0, 1): "False alarm"}[(int(y), int(dec))]


def candidates(W: pd.DataFrame) -> pd.DataFrame:
    idx = W.set_index(["station", "date"])
    tps = W[(W["y"] == 1) & (W["x1"] >= THR)]
    rows = []
    for _, r in tps.iterrows():
        s, d = r["station"], r["date"]
        keys = [(s, d - ONE), (s, d), (s, d + ONE)]
        e1 = all(k in idx.index for k in keys)
        e2 = e3 = False
        correct = None
        if e1:
            win = idx.loc[keys]
            e2 = bool(win[["obs_wind", "obs_mslp"]].notna().all().all()
                      and pd.notna(win.iloc[0]["pers_wind"]) and pd.notna(win.iloc[0]["pers_mslp"]))
            e3 = bool(win.iloc[1]["E_raw"] == 1)
            correct = int(sum((win["x1"] >= THR).astype(int).values == win["y"].values))
        rows.append({"station": s, "date": d, "x1": r["x1"], "E1": e1, "E2": e2, "E3": e3,
                     "eligible": e1 and e2 and e3, "P1_correct_in_window": correct,
                     "wind_triggered": bool(r["L_wind"] == 1), "P2_raw_pressure_fall_d": r["raw_pfall_d"]})
    return pd.DataFrame(rows)


def rank_key(df):
    return df.sort_values(["P1_correct_in_window", "wind_triggered", "P2_raw_pressure_fall_d", "date"],
                          ascending=[False, False, False, True])


def window(W, s, d):
    return W.set_index(["station", "date"]).loc[[(s, d - ONE), (s, d), (s, d + ONE)]].reset_index()


def case_axes(axs: dict, win, show_legend=True):
    """Panels by key: wind, mslp (optional), tend, score."""
    x = np.arange(3)
    lab = [f"{t:%d %b %Y}\n(target date)" for t in win["date"]]
    ax = axs["wind"]
    ax.plot(x, win["obs_wind"], color=S.OBS, marker="D", lw=2, ms=7, label="Observed (PAGASA)", zorder=4)
    for k, col in (("W1", "W1_wind"), ("persistence", "pers_wind"), ("climatology", "clim_wind")):
        n, c, m, ls = S.METHOD[k]
        ax.plot(x, win[col], color=c, marker=m, ls=ls, lw=2, ms=7, label=n, zorder=3)
    ax.set_ylabel("Daily wind speed, m/s"); ax.set_title("Wind speed: observed vs next-day forecasts", loc="left")
    lo = float(np.nanmin(win[["obs_wind", "W1_wind", "pers_wind", "clim_wind"]].values))
    hi = float(np.nanmax(win[["obs_wind", "W1_wind", "pers_wind", "clim_wind"]].values))
    ax.set_ylim(max(0, lo - 1), hi + 1.2)
    if show_legend:
        ax.legend(loc="upper left", ncol=2, fontsize=7.5)

    ax = axs.get("mslp")
    if ax is None:
        ax = plt.figure().add_subplot()  # scratch axis, discarded
        scratch = ax
    else:
        scratch = None
    ax.plot(x, win["obs_mslp"], color=S.OBS, marker="D", lw=2, ms=7, label="Observed MSLP", zorder=4)
    for k, col in (("W1", "W1_mslp"), ("persistence", "pers_mslp"), ("climatology", "clim_mslp")):
        n, c, m, ls = S.METHOD[k]
        ax.plot(x, win[col], color=c, marker=m, ls=ls, lw=2, ms=7, label=n, zorder=3)
    ax.set_ylabel("Mean sea-level pressure, hPa"); ax.set_title("Pressure: observed vs next-day forecasts", loc="left")
    if show_legend:
        ax.legend(loc="best", fontsize=8)
    if scratch is not None:
        plt.close(scratch.figure)

    ax = axs["tend"]
    obs_ch = -win["raw_pfall_d"].values                      # MSLP(d) - MSLP(d-1), negative = fall
    w1_ch = win["W1_mslp"].values - win["pers_mslp"].values  # W1 forecast minus last observed MSLP
    ax.bar(x - 0.18, obs_ch, width=0.34, color=S.OBS, label="Observed 24-h change")
    ax.bar(x + 0.18, w1_ch, width=0.34, color=S.W1C, label="W1 forecast MSLP minus last observed")
    ax.axhline(-3, color=S.INK2, lw=1, ls="--")
    ax.text(2.58, -3.2, "−3 hPa: label threshold", va="top", ha="right", fontsize=7.5, color=S.INK2)
    ax.axhline(0, color=S.INK2, lw=0.6)
    ax.set_ylabel("24-hour MSLP change, hPa"); ax.set_title("Pressure tendency (the label's trigger)", loc="left")
    lim = np.nanmax(np.abs(np.concatenate([obs_ch, w1_ch, [3.5]])))
    ax.set_ylim(-lim * 1.25, lim * 1.6)
    ax.legend(loc="upper left", fontsize=8)

    ax = axs["score"]
    ax.bar(x, win["x1"], width=0.5, color=S.W1C)
    ax.axhline(THR, color=S.INK, lw=1.2, ls="--")
    ax.text(2.58, THR + 0.015, "warning threshold 0.601", fontsize=7.5, color=S.INK, ha="right", va="bottom")
    for i, r in win.iterrows():
        dec = int(r["x1"] >= THR)
        part = "pressure fall" if r["L_press"] == 1 else ("wind" if r["L_wind"] == 1 else "no event")
        ax.text(i, min(r["x1"] + 0.09, 1.04), f"{r['x1']:.2f}", ha="center", fontsize=8.5, color=S.INK, fontweight="semibold")
        ax.text(i, -0.30, f"W1: {'warning' if dec else 'no warning'}\nLabel: {part}\n{outcome(r['y'], dec)}\n"
                f"Persistence:\n{'warning' if r['E_persist'] == 1 else 'no warning'}",
                ha="center", va="top", fontsize=7.5, color=S.INK)
    ax.set_ylim(0, 1.1); ax.set_ylabel("W1+X1 score (not a calibrated probability)")
    ax.set_title("W1+X1 score, decision and study-label outcome", loc="left")
    for k, a in axs.items():
        a.set_xticks(x, lab, fontsize=8)
        a.set_xlim(-0.6, 2.6)


TIMING = ("Timing: each target date shows its own next-day (+1 day) forecast, issued after the previous day's observations "
          "(inputs = the 32 preceding days). The three dates are three separate forecasts, NOT a +1/+2/+3-day forecast from one origin.")
PROC = ("Model: deployed W1 (SHA-256 f2db5aa9…9d14b0), historical scoring procedure (pooled scaled_weather inputs); X1 = mean of the "
        "three stations' scores on the date; warning if X1 ≥ 0.601. W1 values are neural-only outputs (no MOS, no blending).")
BASE = ("Baselines: persistence = observation of the issue day; climatology = station × calendar-month mean of raw observations, "
        "2015-01-01 to 2020-10-14. Event persistence = study label of the issue day. Study label: wind ≥ 10.8 m/s OR same-station "
        "24-hour MSLP fall ≥ 3 hPa.")


def main():
    run = C.new_run("case")
    priv = C.private_dir(run)
    exp = C.PRIVATE / "thesis_export" / run.name
    exp.mkdir(parents=True)
    src = latest("w-cohort")
    W = pd.read_csv(C.private_dir(src) / "website_cohort_rows.csv", parse_dates=["date", "issue_date"])

    cand = candidates(W)
    cand.to_csv(priv / "PRIVATE_candidate_ledger.csv", index=False)
    summary = {"run_id": run.name, "criteria": "spec/CASE_SELECTION_v1.md", "source_rows_run": src.name,
               "candidates": int(len(cand)), "eligible": int(cand["eligible"].sum()),
               "fail_E1": int((~cand["E1"]).sum()), "fail_E2": int((cand["E1"] & ~cand["E2"]).sum()),
               "fail_E3": int((cand["E1"] & cand["E2"] & ~cand["E3"]).sum()), "per_station": {}, "common": None,
               "public_display": "private only (PAGASA CADS-07 Rev.6 condition 4); figures in _private/thesis_export/"}
    figs = []
    for s in C.PRIMARY:
        el = rank_key(cand[(cand["station"] == s) & cand["eligible"]])
        if el.empty:
            summary["per_station"][s] = {"selected": None, "reason": "no candidate passed E1-E3"}
            continue
        top = el.iloc[0]
        win = window(W, s, top["date"])
        summary["per_station"][s] = {"selected_event_date": f"{top['date']:%Y-%m-%d}",
                                     "window": [f"{t:%Y-%m-%d}" for t in win["date"]],
                                     "eligible_candidates": int(len(el)),
                                     "P1_correct_decisions_in_window": int(top["P1_correct_in_window"]),
                                     "trigger": "wind" if top["wind_triggered"] else "pressure fall",
                                     "outcomes": [outcome(r.y, r.x1 >= THR) for r in win.itertuples()],
                                     "event_persistence_on_event_day": "warning" if win.iloc[1]["E_persist"] == 1 else "no warning"}
        fig, axs = plt.subplots(2, 2, figsize=(12, 9.6))
        fig.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.27, hspace=0.72, wspace=0.22)
        a = axs.ravel()
        case_axes({"wind": a[0], "mslp": a[1], "tend": a[2], "score": a[3]}, win)
        S.title(fig, f"PF-H. {s}: selected successful case around {top['date']:%d %B %Y}",
                S.EVIDENCE["C"])
        S.footer(fig, [TIMING, PROC, BASE,
                       f"Station: {s} (primary). Dates: {win['date'].iloc[0]:%Y-%m-%d} to {win['date'].iloc[2]:%Y-%m-%d}; n = 3 station-days. "
                       f"Selection: spec/CASE_SELECTION_v1.md (E1-E3; ranked by correct decisions in the window [favourable, disclosed], then pressure fall, then date); "
                       f"W1 error relative to baselines was NOT used to select. Observations: PAGASA; not for online publication. Run {run.name}."])
        figs += S.save(fig, exp, f"PF-H_case_{s.replace(' ', '_')}")

    # common window
    el = cand[cand["eligible"]]
    by_date = el.groupby("date").agg(n=("station", "size"), p1=("P1_correct_in_window", "sum"),
                                     minfall=("P2_raw_pressure_fall_d", "min")).reset_index()
    by_date = by_date[by_date["n"] == 3].sort_values(["p1", "minfall", "date"], ascending=[False, False, True])
    summary["common_candidate_dates"] = int(len(by_date))
    if len(by_date):
        d = by_date.iloc[0]["date"]
        summary["common"] = {"selected_event_date": f"{d:%Y-%m-%d}",
                             "window": [f"{t:%Y-%m-%d}" for t in (d - ONE, d, d + ONE)],
                             "sum_P1": int(by_date.iloc[0]["p1"])}
        fig, axs = plt.subplots(3, 3, figsize=(14, 12.5))
        fig.subplots_adjust(left=0.06, right=0.985, top=0.9, bottom=0.18, hspace=0.92, wspace=0.3)
        for i, s in enumerate(C.PRIMARY):
            win = window(W, s, d)
            row = axs[i]
            case_axes({"wind": row[0], "tend": row[1], "score": row[2]}, win, show_legend=(i == 0))  # MSLP level omitted for space
            row[0].set_title(f"{s}: wind speed", loc="left")
            row[1].set_title(f"{s}: 24-h MSLP change", loc="left")
            row[2].set_title(f"{s}: W1+X1 score and outcome", loc="left")
        S.title(fig, f"PF-I. All three primary stations: selected common window around {d:%d %B %Y}", S.EVIDENCE["C"])
        S.footer(fig, [TIMING, PROC, BASE,
                       f"Stations: NAIA, Sangley Point, Science Garden (primary; Port Area is supplementary and not shown). "
                       f"n = 9 station-days. Selection: spec/CASE_SELECTION_v1.md output B. Observations: PAGASA; not for online publication. Run {run.name}."], width=190)
        figs += S.save(fig, exp, "PF-I_common_window_all_stations")
    summary["private_figures"] = figs
    (priv / "PRIVATE_selection_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    # public copy: criteria outcomes only; exact dates stay private, as for every event date in this evaluation
    public = {k: v for k, v in summary.items() if k not in ("private_figures", "per_station", "common")}
    public["per_station"] = {s: {k: v for k, v in d.items() if k not in ("selected_event_date", "window")}
                             for s, d in summary["per_station"].items()}
    public["common"] = None if summary["common"] is None else {"selected": True, "sum_P1": summary["common"]["sum_P1"]}
    public["dates"] = "withheld from public outputs; recorded in _private/runs/<run>/PRIVATE_selection_summary.json"
    (run / "case_selection_summary.json").write_text(json.dumps(public, indent=2, default=str), encoding="utf-8")
    C.write_manifest(run, {"stage": "Group C case studies (CASE_SELECTION_v1)", "spec": "GCV-W1-v1 + A2",
                           "private_outputs": "figures in _private/thesis_export/"})
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
