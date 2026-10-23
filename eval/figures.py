"""Figures for GCV-W1-v1. Every figure is drawn from a saved run output and written with its source CSV.
Public figures use aggregates only; the daily observed-vs-predicted series goes to _private/.
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import common as C

BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})


def latest(prefix: str):
    return sorted(C.RUNS.glob(f"{prefix}-*"), key=lambda p: p.name)[-1]


def save(fig, out, name, table: pd.DataFrame):
    fig.savefig(out / f"{name}.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    table.to_csv(out / f"{name}.csv", index=False)


def main():
    run = C.new_run("fig")
    priv = C.private_dir(run)
    b = json.loads((latest("b-benchmark") / "benchmark_results.json").read_text())
    s2 = json.loads((latest("s2-partitions") / "stage2_partitions.json").read_text())
    var = json.loads((latest("s7-variants") / "variants_results.json").read_text())
    checks = {}

    # F1 partitions ------------------------------------------------------------
    rows = [("Primary 3 stations: training", "2015-01-01", "2020-10-14", "train"),
            ("Primary 3 stations: tuning / early stopping", "2020-10-15", "2021-10-14", "tune"),
            ("Primary 3 stations: legacy TEST = benchmark period", "2021-10-15", "2024-12-31", "test"),
            ("Port Area: training (all dates)", "2015-01-01", "2023-10-30", "train"),
            ("Supplementary 19 stations: training (all dates)", "2015-01-01", "2024-12-30", "train")]
    t1 = pd.DataFrame(rows, columns=["partition", "start", "end", "role"])
    col = {"train": BLUE, "tune": ORANGE, "test": AQUA}
    fig, ax = plt.subplots(figsize=(9, 2.9))
    for i, r in t1.iloc[::-1].reset_index(drop=True).iterrows():
        s, e = pd.Timestamp(r.start), pd.Timestamp(r.end)
        ax.barh(i, (e - s).days, left=matplotlib.dates.date2num(s), height=0.55, color=col[r.role])
        ax.text(matplotlib.dates.date2num(pd.Timestamp("2014-12-01")), i, r.partition, ha="right", va="center", color=INK)
    ax.axvspan(matplotlib.dates.date2num(pd.Timestamp("2021-10-15")), matplotlib.dates.date2num(pd.Timestamp("2024-12-31")),
               color=AQUA, alpha=0.08, lw=0)
    ax.xaxis_date(); ax.set_yticks([]); ax.grid(axis="y", visible=False)
    ax.set_title("W1 data allocation by source (shaded: dates later scored)", loc="left", color=INK)
    save(fig, run, "F1_partitions", t1)

    # F2 wind error by station -------------------------------------------------
    recs = []
    for sc in ["pooled", *C.PRIMARY]:
        p, ci = b["wind"][sc]["point"], b["wind"][sc]["ci"]
        for m in ["W1", "persistence", "climatology"]:
            recs.append({"scope": sc, "method": m, "n": p[m]["n"], "mae": p[m]["mae"], "rmse": p[m]["rmse"],
                         "bias": p[m]["bias"], "mae_ci_lo": ci[f"mae_{m}"]["lo"], "mae_ci_hi": ci[f"mae_{m}"]["hi"]})
    t2 = pd.DataFrame(recs)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    scopes = ["pooled", *C.PRIMARY]
    for j, (m, c) in enumerate([("W1", BLUE), ("persistence", ORANGE), ("climatology", AQUA)]):
        d = t2[t2.method == m].set_index("scope").loc[scopes]
        x = np.arange(len(scopes)) + (j - 1) * 0.22
        ax.bar(x, d.mae, width=0.2, color=c, label=m)
        ax.errorbar(x, d.mae, yerr=[d.mae - d.mae_ci_lo, d.mae_ci_hi - d.mae], fmt="none", ecolor=INK, lw=1, capsize=2)
    ax.set_xticks(np.arange(len(scopes)), ["All 3 stations"] + C.PRIMARY)
    ax.set_ylabel("MAE, m/s (lower = smaller error)")
    ax.set_title("Next-day wind: mean absolute error on identical cases (95% block-bootstrap CI)", loc="left", color=INK)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    save(fig, run, "F2_wind_mae_by_station", t2)

    # F3 monthly means (public) ------------------------------------------------
    wm = pd.read_csv(latest("b-benchmark") / "wind_monthly_means_by_station.csv")
    fig, axs = plt.subplots(3, 1, figsize=(9, 7.2), sharex=True)
    for ax, s in zip(axs, C.PRIMARY):
        d = wm[wm.station == s]
        x = pd.to_datetime(d.month)
        ax.plot(x, d.obs_mean, color=INK, lw=2, label="observed")
        ax.plot(x, d.W1_mean, color=BLUE, lw=2, label="W1")
        ax.plot(x, d.persistence_mean, color=ORANGE, lw=1.5, ls="--", label="persistence")
        ax.plot(x, d.climatology_mean, color=AQUA, lw=1.5, ls=":", label="climatology")
        ax.set_title(s, loc="left", color=INK, fontsize=10); ax.set_ylabel("m/s")
    axs[0].legend(frameon=False, ncol=4, loc="upper left")
    fig.suptitle("Monthly mean of daily next-day wind: observed vs forecasts (all eligible dates)", x=0.01, ha="left", color=INK)
    save(fig, run, "F3_wind_monthly_means", wm)

    # F4 binned observed vs W1 (counts) ----------------------------------------
    rows_b = pd.read_csv(sorted((C.PRIVATE / "runs").glob("b-benchmark-*"))[-1] / "cohort_b_rows.csv", parse_dates=["date"])
    W = rows_b[rows_b.elig_wind]
    obs_bins = pd.cut(W.wind_obs, [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 20], labels=["0", "1", "2", "3", "4", "5", "6+"])
    pred_bins = pd.cut(W.wind_W1, [0, 2.0, 2.25, 2.5, 2.75, 3.0, 20], labels=["<2.0", "2.0-2.25", "2.25-2.5", "2.5-2.75", "2.75-3.0", "3.0+"], include_lowest=True)
    ct = pd.crosstab(obs_bins, pred_bins).reindex(index=obs_bins.cat.categories, columns=pred_bins.cat.categories, fill_value=0)
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.imshow(ct.values, cmap="Blues", aspect="auto"); ax.grid(False)
    for i in range(ct.shape[0]):
        for k in range(ct.shape[1]):
            v = ct.values[i, k]
            ax.text(k, i, str(v), ha="center", va="center", color="white" if v > ct.values.max() * 0.55 else INK, fontsize=9)
    ax.set_xticks(range(ct.shape[1]), ct.columns); ax.set_yticks(range(ct.shape[0]), ct.index)
    ax.set_xlabel("W1 forecast wind (m/s)"); ax.set_ylabel("observed wind (m/s)")
    ax.set_title("Observed vs W1 next-day wind: case counts (n=%d)" % len(W), loc="left", color=INK)
    t4 = ct.reset_index().rename(columns={"wind_obs": "observed_bin"})
    checks["F4_total_equals_wind_cases"] = int(ct.values.sum()) == b["counts"]["wind"]["eligible"]
    save(fig, run, "F4_wind_obs_vs_pred_counts", t4)

    # private daily series (whole period, no selection)
    fig, axs = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
    for ax, s in zip(axs, C.PRIMARY):
        d = W[W.station == s]
        ax.plot(d.date, d.wind_obs, color=INK, lw=0.7, label="observed")
        ax.plot(d.date, d.wind_W1, color=BLUE, lw=1.2, label="W1")
        ax.set_title(s, loc="left")
    axs[0].legend(frameon=False)
    fig.savefig(priv / "PRIVATE_daily_wind_obs_vs_W1.png", dpi=130, bbox_inches="tight"); plt.close(fig)

    # F5 event timeline (monthly counts) ---------------------------------------
    em = pd.read_csv(latest("b-benchmark") / "event_outcomes_monthly_by_station.csv")
    proc = "W1+X1@0.601"
    d5 = em[em.procedure == proc]
    fig, axs = plt.subplots(3, 1, figsize=(9, 6.6), sharex=True, sharey=True)
    months = pd.period_range("2021-10", "2024-12", freq="M").astype(str)
    for ax, s in zip(axs, C.PRIMARY):
        d = d5[d5.station == s].set_index("month").reindex(months, fill_value=0)
        x = pd.to_datetime(months)
        ax.bar(x, d.hit, width=20, color=BLUE, label="hit")
        ax.bar(x, d.miss, width=20, bottom=d.hit, color=ORANGE, label="miss")
        ax.bar(x, -d.false_alarm, width=20, color=AQUA, label="false alarm (below axis)")
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_title(f"{s}: hits {int(d.hit.sum())}, misses {int(d.miss.sum())}, false alarms {int(d.false_alarm.sum())}",
                     loc="left", fontsize=10, color=INK)
        ax.set_ylabel("cases")
    axs[0].legend(frameon=False, ncol=3, loc="upper left")
    fig.suptitle(f"Study-label events by month, {proc} (events above axis, false alarms below)", x=0.01, ha="left", color=INK)
    cm = b["events"]["pooled"]["classifiers"][proc]
    checks["F5_timeline_equals_confusion"] = (int(d5.hit.sum()), int(d5.miss.sum()), int(d5.false_alarm.sum()),
                                              int(d5.correct_negative.sum())) == (cm["tp"], cm["fn"], cm["fp"], cm["tn"])
    save(fig, run, "F5_event_timeline_monthly", d5)

    # F6 confusion matrices ----------------------------------------------------
    cls = b["events"]["pooled"]["classifiers"]
    names = list(cls)
    fig, axs = plt.subplots(1, len(names), figsize=(3.3 * len(names), 3.2))
    fig.subplots_adjust(wspace=0.45)
    t6 = []
    for ax, n in zip(axs, names):
        c = cls[n]
        mat = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
        ax.imshow(np.log1p(mat), cmap="Blues"); ax.grid(False)
        for i in range(2):
            for k in range(2):
                ax.text(k, i, f"{int(mat[i, k])}", ha="center", va="center",
                        color="white" if np.log1p(mat[i, k]) > np.log1p(mat).max() * 0.6 else INK, fontsize=11)
        ax.set_xticks([0, 1], ["no event", "event"]); ax.set_yticks([0, 1], ["no event", "event"])
        ax.set_xlabel("forecast")
        if ax is axs[0]:
            ax.set_ylabel("observed (study label)")
        ax.set_title(n, fontsize=9, color=INK)
        t6.append({"procedure": n, "TN": c["tn"], "FP": c["fp"], "FN": c["fn"], "TP": c["tp"],
                   "accuracy": c["accuracy"], "precision": c["precision"], "recall": c["recall"], "f1": c["f1"]})
        checks[f"F6_{n}_sums_to_cases"] = c["tn"] + c["fp"] + c["fn"] + c["tp"] == b["counts"]["event"]["eligible"]
    fig.suptitle("Binary confusion matrices, identical 3,520 cases (27 events, all pressure-fall-only)", x=0.01, ha="left", color=INK)
    save(fig, run, "F6_confusion_matrices", pd.DataFrame(t6))

    # F7 event benchmark comparison -------------------------------------------
    pe = b["events"]["pooled"]
    t7 = []
    for n in names:
        key = n
        t7.append({"procedure": n, "metric": "F1", "value": cls[n]["f1"],
                   "ci_lo": pe["ci"][f"f1_{key}"]["lo"], "ci_hi": pe["ci"][f"f1_{key}"]["hi"]})
    for k in ["W1_raw", "W1+X1", "event_climatology"]:
        t7.append({"procedure": k, "metric": "PR-AUC", "value": pe["probabilistic"][k]["pr_auc"],
                   "ci_lo": pe["ci"][f"prauc_{k}"]["lo"], "ci_hi": pe["ci"][f"prauc_{k}"]["hi"]})
    t7 = pd.DataFrame(t7)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
    for ax, met in zip(axs, ["F1", "PR-AUC"]):
        d = t7[t7.metric == met].reset_index(drop=True)
        y = np.arange(len(d))[::-1]
        ax.hlines(y, d.ci_lo, d.ci_hi, color=INK2, lw=1.5)
        ax.plot(d.value, y, "o", color=BLUE, ms=8)
        ax.set_yticks(y, d.procedure); ax.set_xlim(0, 1)
        ax.set_title(f"{met} (95% block-bootstrap CI)", loc="left", fontsize=10, color=INK)
    if met == "PR-AUC":
        axs[1].axvline(b["counts"]["event"]["events_total"] / b["counts"]["event"]["eligible"], color=ORANGE, ls="--", lw=1)
        axs[1].text(0.03, -0.6, "dashed: prevalence (no-skill PR-AUC)", color=INK2, fontsize=8)
    save(fig, run, "F7_event_benchmarks", t7)

    # F8 input construction and variants --------------------------------------
    t8 = []
    for v, r in var["variants"].items():
        if not r.get("scored"):
            continue
        for cons in ("S-TRAIN", "S-LEGACY"):
            t8.append({"variant": r["label"], "construction": cons, "pr_auc_x1": r[cons]["pr_auc_x1"],
                       "pr_auc_raw": r[cons]["pr_auc_raw"], "wind_mae": r[cons]["wind_mae"]})
    t8 = pd.DataFrame(t8)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    labs = list(dict.fromkeys(t8.variant))
    y = np.arange(len(labs))[::-1]
    for cons, c, mk in (("S-TRAIN", BLUE, "o"), ("S-LEGACY", VIOLET, "s")):
        d = t8[t8.construction == cons].set_index("variant").loc[labs]
        axs[0].plot(d.pr_auc_x1, y, mk, color=c, ms=7, label=cons)
        axs[1].plot(d.wind_mae, y, mk, color=c, ms=7, label=cons)
    axs[1].axvline(b["wind"]["pooled"]["point"]["persistence"]["mae"], color=ORANGE, ls="--", lw=1.2, label="persistence MAE")
    axs[1].axvline(b["wind"]["pooled"]["point"]["climatology"]["mae"], color=AQUA, ls=":", lw=1.2, label="climatology MAE")
    for ax in axs:
        ax.set_yticks(y, labs)
    axs[0].set_title("X1 PR-AUC on identical event cases", loc="left", fontsize=10, color=INK); axs[0].set_xlim(0, 1)
    axs[1].set_title("Next-day wind MAE (m/s)", loc="left", fontsize=10, color=INK)
    fig.legend(*axs[1].get_legend_handles_labels(), frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.06))
    fig.subplots_adjust(wspace=0.55)
    fig.suptitle("Existing frozen variants, two input constructions (descriptive; nothing selected)", x=0.01, ha="left", color=INK)
    save(fig, run, "F8_variants_and_inputs", t8)

    (run / "figure_checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": "figures", "sources": {"benchmark": latest("b-benchmark").name,
                                                           "variants": latest("s7-variants").name,
                                                           "partitions": latest("s2-partitions").name}})
    print(checks); print(run)


if __name__ == "__main__":
    main()
