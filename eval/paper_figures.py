"""Public paper figures PF-A ... PF-G (amendment A2). Aggregates only; each figure is saved as PNG (300 DPI) + SVG
with a CSV of exactly the numbers it plots. Row-level inputs are read from _private/ and never written out.
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

import common as C
import figstyle as S

THR = 0.601
SCOPES = ["pooled", *C.PRIMARY]
BINS = {"wind": np.arange(0, 12.5, 1.0), "mslp": np.arange(996, 1018, 1.0),
        "humidity": np.arange(40, 101, 5.0), "rainfall": np.array([0, 0.1, 1, 2, 5, 10, 20, 50, 100, 1000])}
SLAB = {"pooled": "All 3 stations", "NAIA": "NAIA", "Sangley Point": "Sangley Point", "Science Garden": "Science Garden"}


def latest(prefix):
    return sorted(p for p in C.RUNS.glob(f"{prefix}-*") if not (p / "FAILED.txt").exists())[-1]


def J(p):
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    run = C.new_run("pf")
    wr, rp, br = latest("w-cohort"), latest("reg-prov"), latest("b-benchmark")
    A = J(wr / "website_cohort_results.json")
    RP = J(rp / "regression_provenance.json")
    B = J(br / "benchmark_results.json")
    rows = pd.read_csv(C.private_dir(wr) / "website_cohort_rows.csv", parse_dates=["date"])
    out = run / "figures"
    made, guide = [], []
    clim_name = [k for k in A["events"]["pooled"]["classifiers"] if k.startswith("event_climatology")][0]
    cthr = A["event_climatology_threshold"]["threshold"]
    PROC_A = ("Model: deployed W1 (SHA-256 f2db5aa9…9d14b0), historical scoring procedure (_w1_recall_floor.py: pooled scaled_weather "
              "inputs, 32-day windows); X1 = same-date mean of the three stations' scores; warning if X1 ≥ 0.601 (threshold unchanged).")
    COH_A = ("Cases: the website's 3,423 next-day windows, NAIA, Sangley Point and Science Garden (1,141 each); target dates "
             "2021-11-16 to 2024-12-30; lead +1 day. Study label: wind ≥ 10.8 m/s OR same-station 24-h MSLP fall ≥ 3 hPa "
             "(processed values, as on the website); all 28 positives are pressure falls, 0 wind-triggered.")
    BASE_E = (f"Baselines: event persistence = label of the issue day; event climatology = station × month label frequency, "
              f"2015-01-02 to 2020-10-14, warning if ≥ {cthr:.4f} (chosen on 2020-10-15 to 2021-10-14 only).")
    CI = "Intervals: paired circular block bootstrap over target dates, 14-day blocks, 2,000 resamples, 95% percentile."

    def add(fig, name, table, caption, cohort, lines):
        S.footer(fig, lines)
        made.extend(S.save(fig, out, name))
        table.to_csv(out / f"{name}.csv", index=False)
        guide.append({"figure": name, "png": f"{name}.png", "svg": f"{name}.svg", "csv": f"{name}.csv",
                      "evidence_group": cohort, "caption": caption,
                      "source_runs": sorted({wr.name, rp.name, br.name} if cohort == "A+B" else {wr.name, rp.name})})

    # ---------------- PF-A exact website confusion matrix
    cm = A["events"]["pooled"]["classifiers"]["W1+X1@0.601"]
    tab = pd.DataFrame([{"tn": cm["tn"], "fp": cm["fp"], "fn": cm["fn"], "tp": cm["tp"], "n": cm["n"],
                         "accuracy": cm["accuracy"], "precision": cm["precision"], "recall": cm["recall"], "f1": cm["f1"],
                         "pr_auc_x1": A["events"]["pooled"]["probabilistic"]["W1+X1"]["pr_auc"],
                         "all_negative_accuracy": cm["all_negative_accuracy"], "prevalence": cm["prevalence"]}])
    fig = plt.figure(figsize=(9, 6.4))
    ax = fig.add_axes([0.08, 0.30, 0.42, 0.52])
    mat = np.array([[cm["tp"], cm["fn"]], [cm["fp"], cm["tn"]]])
    lab = [["Hits (TP)", "Misses (FN)"], ["False alarms (FP)", "Correct negatives (TN)"]]
    shade = np.array([[S.W1C, "#c9ddf6"], ["#c9ddf6", "#eef4fc"]])
    for i in range(2):
        for j in range(2):
            ax.add_patch(plt.Rectangle((j, 1 - i), 0.98, 0.98, color=shade[i, j]))
            col = "white" if (i, j) == (0, 0) else S.INK
            ax.text(j + 0.49, 1 - i + 0.56, f"{int(mat[i, j]):,}", ha="center", va="center", fontsize=22, fontweight="bold", color=col)
            ax.text(j + 0.49, 1 - i + 0.28, lab[i][j], ha="center", va="center", fontsize=9, color=col)
    ax.set_xlim(0, 2); ax.set_ylim(0, 2); ax.grid(False)
    ax.set_xticks([0.49, 1.49], ["Warning\n(X1 ≥ 0.601)", "No warning"]); ax.set_yticks([1.49, 0.49], ["Event\n(label = 1)", "No event"])
    ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
    ax.set_xlabel("W1+X1 decision"); ax.set_ylabel("Study-label outcome")
    tx = fig.add_axes([0.56, 0.30, 0.42, 0.52]); tx.axis("off")
    txt = [("Cases", f"{int(cm['n']):,}"), ("Events (all pressure falls)", f"{int(cm['tp'] + cm['fn'])}"),
           ("Accuracy", f"{cm['accuracy'] * 100:.2f}%"), ("  always 'no event' would score", f"{cm['all_negative_accuracy'] * 100:.2f}%"),
           ("Precision", f"{cm['precision'] * 100:.2f}%"), ("Recall", f"{cm['recall'] * 100:.2f}%"), ("F1", f"{cm['f1']:.3f}"),
           ("PR-AUC (X1 scores)", f"{tab.pr_auc_x1[0]:.4f}"), ("  no-skill PR-AUC (prevalence)", f"{cm['prevalence']:.4f}")]
    for k, (a, b) in enumerate(txt):
        tx.text(0, 1 - k * 0.105, a, fontsize=9.5, color=S.INK2 if a.startswith("  ") else S.INK, va="top")
        tx.text(1, 1 - k * 0.105, b, fontsize=9.5, ha="right", va="top", fontweight="semibold")
    S.title(fig, "PF-A. The website's historical W1 scorecard, exactly as shown", S.EVIDENCE["A"])
    add(fig, "PF-A_website_confusion_matrix", tab,
        "The GALE-CAST website's binary scorecard (validation_cm3.json), reproduced case by case: 24 hits, 4 misses, 9 false alarms, "
        "3,386 correct negatives. Accuracy is dominated by correct negatives; the all-negative forecast scores 99.18%.", "A",
        [PROC_A, COH_A, "Identity: all 9 false alarms and 4 misses match the original W1-branch record nine_fp_report.json by station, date and score. "
         "Retrospective: the threshold rule and X1 were adopted after test-period results were seen; not an independent test."])

    # ---------------- PF-B station matrices
    recs = []
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.9))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.78, bottom=0.36, wspace=0.35)
    for ax, s in zip(axs, C.PRIMARY):
        c = A["events"][s]["classifiers"]["W1+X1@0.601"]
        recs.append({"station": s, "hits": c["tp"], "misses": c["fn"], "false_alarms": c["fp"], "correct_negatives": c["tn"],
                     "events": c["tp"] + c["fn"], "cases": c["n"]})
        m = np.array([[c["tp"], c["fn"]], [c["fp"], c["tn"]]])
        for i in range(2):
            for j in range(2):
                ax.add_patch(plt.Rectangle((j, 1 - i), 0.97, 0.97, color=shade[i, j]))
                col = "white" if (i, j) == (0, 0) else S.INK
                ax.text(j + 0.48, 1 - i + 0.55, f"{int(m[i, j]):,}", ha="center", va="center", fontsize=17, fontweight="bold", color=col)
                ax.text(j + 0.48, 1 - i + 0.25, lab[i][j], ha="center", va="center", fontsize=7.8, color=col)
        ax.set_xlim(0, 2); ax.set_ylim(0, 2); ax.grid(False); ax.tick_params(length=0)
        ax.set_xticks([0.48, 1.48], ["Warning", "No warning"]); ax.set_yticks([1.48, 0.48], ["Event", "No event"])
        [sp.set_visible(False) for sp in ax.spines.values()]
        ax.set_title(f"{s} (n = {int(c['n']):,}; {int(c['tp'] + c['fn'])} events)", loc="left")
    S.title(fig, "PF-B. Hits, misses, false alarms and correct negatives by station (website scorecard cases)", S.EVIDENCE["A"])
    add(fig, "PF-B_station_outcomes", pd.DataFrame(recs),
        "The same 3,423 cases split by primary station. Because X1 averages the three stations, a warning is issued for all three stations "
        "on the same date; station results are therefore not independent.", "A",
        [PROC_A, COH_A, "X1 is a network-wide score: on any date the decision is identical at all three stations."])

    # ---------------- PF-C overall event metrics, A and B side by side
    meth = [("W1+X1@0.601", "W1+X1 (0.601)", S.W1C, "o"), ("event_persistence", "Event persistence", S.PERC, "s")]
    recs = []
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.4), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.8, bottom=0.36, wspace=0.08)
    for ax, (grp, E, cname, n_lab) in zip(axs, [("A", A["events"]["pooled"], clim_name, "website scorecard cases, n = 3,423, 28 events"),
                                                ("B", B["events"]["pooled"], [k for k in B["events"]["pooled"]["classifiers"] if k.startswith("event_climatology")][0],
                                                 f"training-consistent benchmark, n = {B['counts']['event']['eligible']:,}, {B['counts']['event']['events_total']} events")]):
        ms = meth + [(cname, "Event climatology", S.CLIMC, "^")]
        for k, (key, name, col, mk) in enumerate(ms):
            c = E["classifiers"][key]
            for j, met in enumerate(["precision", "recall", "f1"]):
                ci = E["ci"].get(f"{met}_{key}", {})
                x = j + (k - 1) * 0.22
                v = c[met]
                ax.errorbar(x, v, yerr=[[v - ci["lo"]], [ci["hi"] - v]] if ci.get("lo") is not None else None,
                            fmt=mk, color=col, ms=8, lw=1.6, capsize=3, label=name if j == 0 else None)
                ax.text(x + 0.03, v, f"{v:.2f}", fontsize=7.5, color=S.INK, va="center", ha="left")
                recs.append({"group": grp, "procedure": name, "metric": met, "value": v, "ci_lo": ci.get("lo"), "ci_hi": ci.get("hi"),
                             "tp": c["tp"], "fp": c["fp"], "fn": c["fn"], "tn": c["tn"]})
        ax.set_xticks([0, 1, 2], ["Precision", "Recall", "F1"]); ax.set_ylim(0, 1.05)
        ax.set_title(f"{grp}. {n_lab}", loc="left", fontsize=9.5)
    axs[0].set_ylabel("Score (higher is better)"); axs[0].legend(loc="upper left", fontsize=8)
    S.title(fig, "PF-C. Event detection: W1+X1 versus event persistence and event climatology",
            "Evidence A (website scorecard) and Evidence B (training-consistent benchmark), each on its own identical cases; overall evidence")
    add(fig, "PF-C_event_metrics_overall", pd.DataFrame(recs),
        "Precision, recall and F1 with 95% intervals. On both cohorts W1+X1 beats both event baselines on F1 (established). "
        "The level depends on the input construction: 24/28 hits with the website's procedure, fewer with training-consistent inputs.", "A+B",
        [PROC_A + " Panel B: per-station scalers as in training (EVAL_SPEC_v1 Cohort B).", BASE_E, CI,
         "Cohorts differ (cases, input scaling, label truth: processed in A, raw unimputed in B); compare methods within a panel, not across panels."])

    # ---------------- PF-D by station (A)
    recs = []
    fig, axs = plt.subplots(1, 3, figsize=(13, 5.0), sharey=True)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.34, wspace=0.08)
    for ax, s in zip(axs, C.PRIMARY):
        E = A["events"][s]
        for k, (key, name, col, mk) in enumerate(meth + [(clim_name, "Event climatology", S.CLIMC, "^")]):
            c = E["classifiers"][key]
            for j, met in enumerate(["precision", "recall", "f1"]):
                ci = E["ci"].get(f"{met}_{key}", {})
                x = j + (k - 1) * 0.22; v = c[met]
                ax.errorbar(x, v, yerr=[[v - ci["lo"]], [ci["hi"] - v]] if ci.get("lo") is not None else None,
                            fmt=mk, color=col, ms=7, lw=1.4, capsize=2.5, label=name if j == 0 else None)
                recs.append({"station": s, "procedure": name, "metric": met, "value": v, "ci_lo": ci.get("lo"), "ci_hi": ci.get("hi")})
        ax.set_xticks([0, 1, 2], ["Precision", "Recall", "F1"]); ax.set_ylim(0, 1.05)
        ax.set_title(f"{s} ({int(E['classifiers']['W1+X1@0.601']['tp'] + E['classifiers']['W1+X1@0.601']['fn'])} events)", loc="left")
    axs[0].set_ylabel("Score (higher is better)"); axs[0].legend(loc="upper left", fontsize=8)
    S.title(fig, "PF-D. Event detection by station (website scorecard cases)", S.EVIDENCE["A"])
    add(fig, "PF-D_event_metrics_by_station", pd.DataFrame(recs),
        "The PF-C comparison for each primary station. With 8-10 events per station the intervals are wide.", "A", [PROC_A, COH_A, BASE_E, CI])

    # ---------------- PF-E precision-recall curves from saved scores
    y = rows["y"].values
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    fig.subplots_adjust(left=0.1, right=0.97, top=0.85, bottom=0.3)
    recs = []
    for key, col, name, ls in (("x1", S.W1C, "W1+X1 score", "-"), ("prob", "#6250d6", "W1 raw station score", "--"),
                               ("E_clim", S.CLIMC, "Event climatology", ":")):
        p, r, t = precision_recall_curve(y, rows[key].values)
        ax.step(r, p, where="post", color=col, lw=2, ls=ls, label=f"{name} (PR-AUC {A['events']['pooled']['probabilistic'][{'x1': 'W1+X1', 'prob': 'W1_raw', 'E_clim': 'event_climatology'}[key]]['pr_auc']:.3f})")
        recs += [{"score": name, "recall": rr, "precision": pp} for rr, pp in zip(r, p)]
    op = A["events"]["pooled"]["classifiers"]["W1+X1@0.601"]
    ax.plot(op["recall"], op["precision"], "o", ms=11, mfc=S.W1C, mec="white", mew=2, zorder=5)
    ax.annotate("historical operating point\nX1 ≥ 0.601: 24 hits, 9 false alarms", (op["recall"], op["precision"]),
                xytext=(0.32, 0.52), fontsize=8.5, arrowprops=dict(arrowstyle="-", color=S.INK2))
    pe = A["events"]["pooled"]["classifiers"]["event_persistence"]
    ax.plot(pe["recall"], pe["precision"], "s", ms=9, color=S.PERC, label="Event persistence (single point; binary)")
    ax.axhline(op["prevalence"], color=S.INK2, lw=1, ls="--")
    ax.text(0.99, op["prevalence"] + 0.015, f"no skill = prevalence {op['prevalence']:.4f}", ha="right", fontsize=7.5, color=S.INK2)
    ax.set_xlabel("Recall (share of events warned)"); ax.set_ylabel("Precision (share of warnings that were events)")
    ax.set_xlim(0, 1.02); ax.set_ylim(0, 1.05); ax.legend(loc="lower left", fontsize=8)
    S.title(fig, "PF-E. Precision-recall curves from the actual saved scores", S.EVIDENCE["A"])
    recs.append({"score": "operating point X1>=0.601", "recall": op["recall"], "precision": op["precision"]})
    add(fig, "PF-E_precision_recall_curves", pd.DataFrame(recs),
        "Curves traced from the 3,423 saved W1 scores (not reconstructed from a confusion matrix), with the historical 0.601 point marked.", "A",
        [PROC_A, COH_A, BASE_E, "W1 scores come from a model trained with focal loss, class weights and oversampling; they are rankings, not calibrated "
         f"probabilities (Brier skill vs climatology {A['events']['pooled']['probabilistic']['W1+X1']['brier_skill_vs_climatology']:.2f})."])

    # ---------------- PF-F wind MAE and RMSE vs baselines
    Rw = A["regression"]["wind"]
    recs = []
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.2))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.33, wspace=0.18)
    for ax, met in zip(axs, ["mae", "rmse"]):
        for k, mth in enumerate(["W1", "persistence", "climatology"]):
            name, col, _, _ = S.METHOD[mth]
            xs = np.arange(4) + (k - 1) * 0.26
            vals = [Rw["scopes"][sc]["point"][mth][met] for sc in SCOPES]
            ci = [Rw["scopes"][sc]["ci"][f"{met}_{mth}"] for sc in SCOPES]
            ax.bar(xs, vals, width=0.24, color=col, label=name)
            ax.errorbar(xs, vals, yerr=[[v - c["lo"] for v, c in zip(vals, ci)], [c["hi"] - v for v, c in zip(vals, ci)]],
                        fmt="none", ecolor=S.INK, lw=1, capsize=2)
            for x_, v in zip(xs, vals):
                ax.text(x_, v + 0.04, f"{v:.2f}", ha="center", fontsize=7.2, color=S.INK)
            for sc, v, c in zip(SCOPES, vals, ci):
                recs.append({"metric": met, "scope": sc, "method": name, "value_ms": v, "ci_lo": c["lo"], "ci_hi": c["hi"],
                             "n": Rw["scopes"][sc]["point"][mth]["n"]})
        ax.set_xticks(np.arange(4), [SLAB[s] for s in SCOPES], fontsize=8.5)
        ax.set_ylabel(f"{met.upper()}, m/s (lower is better)")
        ax.set_title(f"{met.upper()} of next-day wind speed", loc="left")
    axs[0].legend(loc="upper left", fontsize=8)
    S.title(fig, "PF-F. Next-day wind speed: W1 versus persistence and climatology (website scorecard cases)", S.EVIDENCE["A"])
    add(fig, "PF-F_wind_mae_rmse", pd.DataFrame(recs),
        "W1's neural wind output has larger MAE and RMSE than both baselines overall and at every station (established for MAE vs persistence "
        "everywhere). W1 does not show wind-forecast superiority.", "A",
        [PROC_A, f"Cases: {Rw['n_common']:,} of the 3,423 website cases with raw observed wind on the target and issue days "
         f"(excluded: target missing {Rw['excluded']['target_obs_missing']}, issue day missing {Rw['excluded']['issue_day_obs_missing_only']}). "
         "Truth: raw, unimputed PAGASA daily wind (m/s; statistic, averaging period and height undocumented). W1 = neural-only output, "
         "no MOS or blending.", "Baselines: persistence = observed wind of the issue day; climatology = station × month mean, 2015-01-01 to 2020-10-14.", CI])

    # ---------------- PF-F2 regression provenance of the website's wind number
    st = RP["steps"]
    tb = pd.DataFrame([
        {"step": "1. W1 neural output", "mae": st["neural_only"]["mae"], "rmse": st["neural_only"]["rmse"], "fitted_on_evaluation_outcomes": False},
        {"step": "2. + isotonic MOS per station and season", "mae": st["after_mos"]["mae"], "rmse": st["after_mos"]["rmse"], "fitted_on_evaluation_outcomes": True},
        {"step": f"3. + blend {RP['blend_weight_on_model']:.2f}×model with obs. two days earlier (website value)", "mae": st["after_blend"]["mae"], "rmse": st["after_blend"]["rmse"], "fitted_on_evaluation_outcomes": True},
        {"step": "Persistence (issue-day obs.), same cases and truth", "mae": st["persistence_same_cases_same_truth"]["mae"], "rmse": st["persistence_same_cases_same_truth"]["rmse"], "fitted_on_evaluation_outcomes": False},
    ])
    fig, ax = plt.subplots(figsize=(11, 5.4))
    fig.subplots_adjust(left=0.4, right=0.97, top=0.8, bottom=0.3)
    cols = [S.W1C, "#7aa9e6", "#a9c8f0", S.PERC]
    yy = np.arange(len(tb))[::-1]
    ax.barh(yy, tb["mae"], color=cols, height=0.55)
    for yv, v, r, f in zip(yy, tb["mae"], tb["rmse"], tb["fitted_on_evaluation_outcomes"]):
        ax.text(v + 0.01, yv, f"MAE {v:.4f}   RMSE {r:.4f}" + ("   [fitted on evaluation outcomes]" if f else ""), va="center", fontsize=8.3)
    ax.set_yticks(yy, tb["step"], fontsize=8.5); ax.set_xlim(0, 1.45); ax.set_xlabel("Next-day wind MAE, m/s (processed truth, 3,423 cases)")
    S.title(fig, "PF-F2. Where the website's wind MAE of 0.5365 m/s comes from",
            "Regression provenance (validate_model_multioutput.py at W1 commit 1fd1ef9), reproduced exactly; not a W1 neural result")
    add(fig, "PF-F2_website_regression_provenance", tb,
        "The website's wind MAE 0.5365 / RMSE 0.7723 / MASE 0.6782 are reproduced exactly only after two post-processing steps fitted on the "
        "evaluation period itself. W1's own wind output has MAE 0.987; issue-day persistence on the same cases has MAE 0.474.", "A",
        [PROC_A, "Truth: processed_weather wind of the target day (forward-filled), as used by the website script. MOS: linear + isotonic, per station × season "
         "(Jun-Nov / Dec-May), 8-fold TimeSeriesSplit over evaluation rows; 399 rows calibrated by a fallback fitted on later evaluation rows. "
         "Blend weight chosen by 5-fold TimeSeriesSplit MAE on evaluation rows; its partner is the observation two days before the target (script indexing).",
         f"MASE 0.6782 uses an in-sample lag-365 denominator from training rows ({RP['mase_denominator_lag365_train']:.4f} m/s); MASE < 1 does not mean the "
         "forecast beats a same-case baseline. The website's wind-direction row (43.40°) comes from a separate direction-only model."])

    # ---------------- PF-F3 other regression variables (pooled), separate units
    names = {"wind": "Wind speed (m/s)", "mslp": "Mean sea-level pressure (hPa)", "humidity": "Relative humidity (%)", "rainfall": "Daily rainfall (mm)"}
    recs = []
    fig, axs = plt.subplots(1, 4, figsize=(14, 4.8))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.78, bottom=0.36, wspace=0.35)
    for ax, v in zip(axs, ["wind", "mslp", "humidity", "rainfall"]):
        R = A["regression"][v]["scopes"]["pooled"]
        for k, mth in enumerate(["W1", "persistence", "climatology"]):
            name, col, _, _ = S.METHOD[mth]
            val = R["point"][mth]["mae"]; c = R["ci"][f"mae_{mth}"]
            ax.bar(k, val, color=col, width=0.6)
            ax.errorbar(k, val, yerr=[[val - c["lo"]], [c["hi"] - val]], fmt="none", ecolor=S.INK, capsize=3, lw=1)
            ax.text(k, val * 1.02 + 0.02, f"{val:.2f}", ha="center", fontsize=8)
            recs.append({"variable": v, "unit": A["regression"][v]["unit"], "method": name, "mae": val, "ci_lo": c["lo"], "ci_hi": c["hi"],
                         "rmse": R["point"][mth]["rmse"], "bias": R["point"][mth]["bias"], "n": R["point"][mth]["n"]})
        ax.set_xticks([0, 1, 2], ["W1", "Persist.", "Clim."]); ax.set_title(names[v], loc="left", fontsize=9)
        ax.set_ylabel("MAE (lower is better)")
    S.title(fig, "PF-F3. Next-day error for each supported regression output, pooled over the three stations", S.EVIDENCE["A"])
    rf = A["regression"]["rainfall"]["scopes"]["pooled"]["point"]
    add(fig, "PF-F3_regression_variables_mae", pd.DataFrame(recs),
        "Each output in its own unit and panel. W1 has larger MAE than both baselines for wind, pressure and humidity. For rainfall W1's MAE is "
        f"lower than both baselines (established), but its RMSE ({rf['W1']['rmse']:.1f} mm) is above climatology's ({rf['climatology']['rmse']:.1f} mm) "
        f"and it under-forecasts on average (bias {rf['W1']['bias']:.2f} mm): a low forecast lowers MAE on skewed rainfall.", "A",
        [PROC_A, "Cases: website cases with raw observations on the target and issue days; n = " +
         ", ".join(f"{v} {A['regression'][v]['n_common']:,}" for v in names) + ". Truth: raw, unimputed PAGASA values; rainfall in mm (W1 output "
         "inverted from log1p; trace −1 → 0.05 mm as in the pipeline).", "Baselines: persistence = issue-day observation; climatology = station × month mean, "
         "2015-01-01 to 2020-10-14. W1 = neural-only outputs.", CI])

    # ---------------- PF-G observed vs predicted (binned counts, 1:1 line)
    bc = pd.read_csv(wr / "obs_vs_W1_binned_counts.csv")
    fig, axs = plt.subplots(1, 4, figsize=(15, 5.0))
    fig.subplots_adjust(left=0.04, right=0.99, top=0.8, bottom=0.34, wspace=0.32)
    cmap = plt.get_cmap("Blues")
    for ax, v in zip(axs, ["wind", "mslp", "humidity", "rainfall"]):
        g = bc[bc["variable"] == v]
        edges = BINS[v]  # identical to website_cohort.py's bins_spec
        pos = {round(float(e), 6): i for i, e in enumerate(edges)}
        nb = len(edges) - 1
        H = np.zeros((nb, nb))
        for r in g.itertuples():
            H[pos[round(r.pred_lo, 6)], pos[round(r.obs_lo, 6)]] += r.count
        im = ax.imshow(np.where(H > 0, H, np.nan), origin="lower", cmap=cmap, norm=matplotlib_lognorm(H), aspect="auto",
                       extent=[0, nb, 0, nb])
        ax.plot([0, nb], [0, nb], color=S.INK, lw=1, ls="--", label="1:1 (perfect)")
        tick = range(0, nb + 1, max(1, nb // 5))
        ax.set_xticks(list(tick), [f"{edges[i]:g}" for i in tick], fontsize=7.5)
        ax.set_yticks(list(tick), [f"{edges[i]:g}" for i in tick], fontsize=7.5)
        ax.set_xlabel(f"Observed ({A['regression'][v]['unit']})"); ax.set_ylabel(f"W1 forecast ({A['regression'][v]['unit']})")
        ax.set_title(f"{names[v]}  n = {int(g['count'].sum()):,}", loc="left", fontsize=8.8)
        ax.grid(False)
    axs[0].legend(loc="upper left", fontsize=7.5)
    fig.colorbar(im, ax=axs, shrink=0.75, pad=0.01, label="cases per cell (log scale)")
    S.title(fig, "PF-G. Observed versus W1-forecast values (counts of cases per cell, 1:1 line dashed)", S.EVIDENCE["A"])
    add(fig, "PF-G_observed_vs_predicted", bc,
        "Binned counts replace a scatter so that no individual station-day reading is published. Wind forecasts sit in a narrow 2-3 m/s band "
        "whatever was observed; pressure and humidity forecasts vary little; rainfall is mostly under-forecast on wet days.", "A",
        [PROC_A, "Cases: website cases with a raw observation of the variable on the target date. Values beyond the plotted range are counted in the end "
         "cells. Rainfall cells are uneven (0, 0.1, 1, 2, 5, 10, 20, 50, 100 mm). Truth: raw, unimputed PAGASA observations.",
         "A useful forecast concentrates cases along the 1:1 line; this figure shows spread, not skill relative to baselines (see PF-F, PF-F3)."])

    checks = {"PF-A_matches_website": [cm["tn"], cm["fp"], cm["fn"], cm["tp"]] == [3386, 9, 4, 24],
              "PF-B_sums_to_total": sum(r["hits"] + r["misses"] + r["false_alarms"] + r["correct_negatives"] for r in
                                         pd.read_csv(out / "PF-B_station_outcomes.csv").to_dict("records")) == 3423,
              "PF-F2_reproduces_website": all(RP["reproduces_website"].values()),
              "PF-G_totals": {v: int(bc[bc.variable == v]["count"].sum()) == A["obs_vs_W1_binned_total"][v] for v in names}}
    (run / "figure_guide.json").write_text(json.dumps({"run_id": run.name, "figures": guide, "checks": checks}, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": "paper figures (amendment A2)", "inputs": [wr.name, rp.name, br.name]})
    print(json.dumps(checks), run)


def matplotlib_lognorm(H):
    from matplotlib.colors import LogNorm
    return LogNorm(vmin=1, vmax=max(1, H.max()))


if __name__ == "__main__":
    main()
