"""Canonical explanations for every figure (public and private). One source for the site, FIGURE_GUIDE.md and the private
thesis-export index. Numbers are filled from saved run outputs through `ctx`, except the PF-H day counts (W1 closer than both
baselines on 2/0/1 of 3 dates), which were tallied from the private case rows and can be checked in _private/thesis_export/INDEX.md.

Fields: shows, purpose, produced, read, finding, supports, limits, paper (chapter/section + clean caption), source.
"""
from __future__ import annotations

FIELDS = [("shows", "What this graph shows"), ("purpose", "Purpose"), ("produced", "How it was produced"),
          ("read", "How to read it"), ("finding", "Actual finding"), ("supports", "What it supports"),
          ("limits", "What it does not establish"), ("paper", "Use in the paper"), ("source", "Source")]

SELECTED = "Selected favourable example, chosen retrospectively for illustration; not representative of all dates."
ERRORS = ("Lower MAE/RMSE means smaller errors on these matching cases. Signed mean error (bias) shows systematic over- or "
          "under-forecasting and can hide errors that cancel. A good confusion matrix does not establish accurate numerical wind forecasts.")
A_COH = "Evidence A: the website's 3,423 next-day windows (NAIA, Sangley Point, Science Garden, 1,141 each; target dates 2021-11-16 to 2024-12-30)"
A_PROC = "saved historical W1 scores from the old scoring procedure (pooled inputs, 32-day windows, X1 = mean over the three stations, warning if X1 ≥ 0.601)"
B_COH = "Evidence B: the training-consistent benchmark (3,520 event cases / 3,555 wind cases, target dates 2021-10-15 to 2024-12-31; inputs scaled per station as in training; raw unimputed truth)"
EV_BASE = "event persistence = the issue day's label; event climatology = station × month label frequency 2015-2020, warning threshold chosen on the 2020-21 tuning year"
REG_BASE = "persistence = the issue day's observation; climatology = station × calendar-month mean of 2015-01-01 to 2020-10-14 observations"


def f(x, d=3):
    return "—" if x is None else f"{x:.{d}f}"


def notes(ctx: dict) -> dict:
    A, B, RP, V = ctx["A"], ctx["B"], ctx["RP"], ctx["V"]
    ea, eb = A["events"]["pooled"], B["events"]["pooled"]
    ca, cb = ea["classifiers"], eb["classifiers"]
    kca = [k for k in ca if k.startswith("event_climatology")][0]
    kcb = [k for k in cb if k.startswith("event_climatology")][0]
    x, pe, cl = ca["W1+X1@0.601"], ca["event_persistence"], ca[kca]
    xb, peb = cb["W1+X1@0.601"], cb["event_persistence"]
    reg = A["regression"]
    rp = lambda v, m, k="mae": reg[v]["scopes"]["pooled"]["point"][m][k]
    rs = lambda v, s, m: reg[v]["scopes"][s]["point"][m]["mae"]
    st = {s: A["events"][s]["classifiers"]["W1+X1@0.601"] for s in ("NAIA", "Sangley Point", "Science Garden")}
    bw = B["wind"]
    var = {r["label"]: r for r in V["variants"].values() if r.get("scored")}
    run_a, run_rp, run_pf, run_b = ctx["run_w"], ctx["run_rp"], ctx["run_pf"], ctx["run_b"]
    N = {}

    # -------------------------------------------------------------- public paper figures (Evidence A unless stated)
    N["PF-A_website_confusion_matrix"] = dict(
        shows=f"A 2×2 table of W1+X1 warnings against study-label outcomes for {A_COH}.",
        purpose="To show exactly the matrix the GALE-CAST website reports, and what each cell means.",
        produced=f"Counts from {A_PROC}; case identity checked against the original W1-branch record of false alarms and misses.",
        read="Top-left = hits, top-right = misses, bottom-left = false alarms, bottom-right = correct negatives. The side panel gives the derived scores and two no-skill references.",
        finding=f"TP {int(x['tp'])}, FN {int(x['fn'])}, FP {int(x['fp'])}, TN {int(x['tn'])}; accuracy {x['accuracy']*100:.2f}% (always 'no event' scores {x['all_negative_accuracy']*100:.2f}%); precision {f(x['precision'])}, recall {f(x['recall'])}, F1 {f(x['f1'])}, PR-AUC {f(ea['probabilistic']['W1+X1']['pr_auc'],4)} vs no-skill {f(x['prevalence'],4)}.",
        supports="The website's scorecard is reproducible case by case, and W1+X1 caught 24 of the 28 study-label events in this cohort.",
        limits="Not an independent test (the threshold rule and X1 were adopted after these results were seen); all 28 events are pressure falls, not gale-force winds; accuracy is inflated by correct negatives; says nothing about numerical forecasts.",
        paper="Chapter 4, Model Evaluation (replace Table 4.4's description). Caption: 'Figure 4.x. Historical scorecard of the deployed model (cross-station score X1 ≥ 0.601) on 3,423 next-day cases, 2021-11-16 to 2024-12-30; all 28 positive labels are 24-hour pressure falls of at least 3 hPa.'",
        source=f"figures/paper/PF-A_website_confusion_matrix.csv; runs {run_a}, {run_pf}; spec/AMENDMENT_A2_website_cohort.md.")
    N["PF-B_station_outcomes"] = dict(
        shows=f"One 2×2 matrix per primary station (1,141 cases each), same cohort and decisions as PF-A.",
        purpose="To show whether hits and false alarms are spread across stations or concentrated at one.",
        produced=f"PF-A's cases split by station; {A_PROC}.",
        read="Same cell layout as PF-A; darker blue marks hits. Compare misses and false alarms between stations.",
        finding="; ".join(f"{s}: {int(c['tp'])} hits, {int(c['fn'])} misses, {int(c['fp'])} false alarms, {int(c['tn']):,} correct negatives" for s, c in st.items()) + ".",
        supports="Detection is similar at the three stations; no single station carries the result.",
        limits="X1 is one network-wide score, so the three stations always receive the same decision on a date; station results are not independent. 8-10 events per station.",
        paper="Chapter 4, Model Evaluation (by-station paragraph). Caption: 'Figure 4.x. Historical scorecard by primary station; the cross-station score gives one decision per date.'",
        source=f"figures/paper/PF-B_station_outcomes.csv; run {run_a}.")
    N["PF-C_event_metrics_overall"] = dict(
        shows=f"Precision, recall and F1 for W1+X1, event persistence and event climatology, in two panels: Evidence A (3,423 cases, 28 events) and Evidence B (3,520 cases, 27 events).",
        purpose="To test whether W1+X1 detects study-label events better than two simple reference rules on identical cases.",
        produced=f"Panel A: {A_PROC}; panel B: {B_COH}. Baselines: {EV_BASE}. 95% intervals from a paired 14-day block bootstrap (2,000 resamples).",
        read="Higher is better for all three scores. Vertical lines are 95% intervals; compare methods within a panel only, because the cohorts differ.",
        finding=f"A: F1 W1+X1 {f(x['f1'])} vs persistence {f(pe['f1'])} and climatology {f(cl['f1'])} (W1 − persistence {ea['ci']['df1_X1601_persist']['verdict']}). B: F1 {f(xb['f1'])} vs {f(peb['f1'])} and {f(cb[kcb]['f1'])} ({eb['ci']['df1_X1601_persist']['verdict']}).",
        supports="On both cohorts W1+X1 detects pressure-fall events better than repeating yesterday's label or using the monthly event rate.",
        limits="The level depends on input scaling (24/28 vs 16/27 hits); 27-28 events give wide intervals; events are pressure falls, not strong winds; the cohort-A threshold rule was chosen after seeing these dates.",
        paper="Chapter 4, Model Evaluation, baseline comparison. Caption: 'Figure 4.x. Event detection of the deployed model against event persistence and event climatology on identical cases, (a) historical scorecard procedure, (b) training-consistent inputs; bars are 95% block-bootstrap intervals.'",
        source=f"figures/paper/PF-C_event_metrics_overall.csv; runs {run_a}, {run_b}.")
    N["PF-D_event_metrics_by_station"] = dict(
        shows="PF-C's Evidence A comparison repeated for each primary station.",
        purpose="To check whether W1+X1's advantage over the baselines appears at every station.",
        produced=f"{A_PROC}; baselines: {EV_BASE}; station-level 95% block-bootstrap intervals.",
        read="Higher is better; overlapping intervals mean the station-level difference is uncertain.",
        finding="F1 W1+X1 vs persistence: " + "; ".join(f"{s} {f(A['events'][s]['classifiers']['W1+X1@0.601']['f1'])} vs {f(A['events'][s]['classifiers']['event_persistence']['f1'])}" for s in st) + ".",
        supports="W1+X1's point estimates exceed both baselines at every station.",
        limits="Only 8-10 events per station, so intervals are wide; decisions are shared across stations (X1).",
        paper="Chapter 4 or Appendix (station detail). Caption: 'Figure 4.x. Event-detection scores by station, historical scorecard cases.'",
        source=f"figures/paper/PF-D_event_metrics_by_station.csv; run {run_a}.")
    N["PF-E_precision_recall_curves"] = dict(
        shows=f"Precision against recall as the warning threshold varies, for the W1+X1 score, the W1 raw station score and event climatology ({A_COH}); event persistence is a single point.",
        purpose="To show how W1 ranks event days above ordinary days at every possible threshold, not only at 0.601.",
        produced="Curves traced from the 3,423 saved scores (not reconstructed from one confusion matrix); the historical 0.601 operating point is marked.",
        read="Curves nearer the top-right are better. The dashed line is the no-skill level (the event rate). Steps occur because there are only 28 events.",
        finding=f"PR-AUC: W1+X1 {f(ea['probabilistic']['W1+X1']['pr_auc'])}, W1 raw {f(ea['probabilistic']['W1_raw']['pr_auc'])}, event climatology {f(ea['probabilistic']['event_climatology']['pr_auc'])}; no-skill {f(x['prevalence'],4)}. Operating point: precision {f(x['precision'])}, recall {f(x['recall'])}.",
        supports="W1's scores rank pressure-fall days far above ordinary days on this cohort; cross-station averaging (X1) improves the ranking.",
        limits=f"Scores are not calibrated probabilities (Brier skill vs climatology {f(ea['probabilistic']['W1+X1']['brier_skill_vs_climatology'],2)}); with training-consistent inputs the X1 PR-AUC is {f(eb['probabilistic']['W1+X1']['pr_auc'])} (Evidence B).",
        paper="Chapter 4, Model Evaluation (PR-AUC paragraph). Caption: 'Figure 4.x. Precision-recall curves of the deployed model's scores on the historical scorecard cases, with the 0.601 operating point.'",
        source=f"figures/paper/PF-E_precision_recall_curves.csv; run {run_a}.")
    N["PF-F_wind_mae_rmse"] = dict(
        shows=f"Mean absolute error and root-mean-square error (m/s) of next-day wind for W1, persistence and climatology, pooled and per station ({reg['wind']['n_common']:,} of the 3,423 Evidence A cases).",
        purpose="To test whether W1's numerical wind forecast is more accurate than two no-skill references.",
        produced=f"W1 neural-only wind output on the website cases (no post-processing); raw unimputed observed wind; {REG_BASE}; 95% block-bootstrap intervals.",
        read="Lower bars are better. " + ERRORS,
        finding=f"Pooled MAE: W1 {f(rp('wind','W1'))}, persistence {f(rp('wind','persistence'))}, climatology {f(rp('wind','climatology'))} m/s; W1 bias {f(rp('wind','W1','bias'),2)} m/s. Science Garden: W1 {f(rs('wind','Science Garden','W1'))} vs persistence {f(rs('wind','Science Garden','persistence'))}.",
        supports="W1's wind forecast is less accurate than persistence at every station and less accurate than climatology overall.",
        limits="Says nothing about event detection (PF-C) or about strong winds (none reached 10.8 m/s); the wind statistic, averaging period and sensor height are undocumented.",
        paper="Chapter 4, regression results (replacing Table 4.5). Caption: 'Figure 4.x. Next-day wind-speed error of the deployed model and two reference forecasts on identical cases.'",
        source=f"figures/paper/PF-F_wind_mae_rmse.csv; run {run_a}.")
    N["PF-F2_website_regression_provenance"] = dict(
        shows="How the website's wind MAE of 0.5365 m/s arises: W1's own error, then two post-processing steps, beside persistence on the same 3,423 cases.",
        purpose="To show which procedure produced the website's regression numbers before they are attributed to W1.",
        produced="Port of validate_model_multioutput.py at W1 commit 1fd1ef9 (isotonic MOS per station × season, then a persistence blend), run on the saved website cases; truth = processed (forward-filled) wind, as in that script.",
        read="Shorter bars are smaller errors. Bars marked 'fitted on evaluation outcomes' used the same period's observations to tune themselves.",
        finding=f"W1 neural {f(RP['steps']['neural_only']['mae'],4)} → after MOS {f(RP['steps']['after_mos']['mae'],4)} → after blend {f(RP['steps']['after_blend']['mae'],4)} (website value reproduced exactly); persistence {f(RP['steps']['persistence_same_cases_same_truth']['mae'],4)} m/s.",
        supports="The website's regression block is post-processed, partly in-sample, and still has a larger MAE than persistence (its RMSE is slightly lower).",
        limits="Not a W1 result and not an out-of-sample estimate; the blend uses an observation two days before the target (script indexing). MASE < 1 here uses an in-sample denominator.",
        paper="Chapter 4, note under the regression results, or Appendix. Caption: 'Figure 4.x. Provenance of the previously reported wind error: model output, in-period calibration and blending, and same-case persistence.'",
        source=f"figures/paper/PF-F2_website_regression_provenance.csv; run {run_rp}.")
    N["PF-F3_regression_variables_mae"] = dict(
        shows="Pooled MAE of W1, persistence and climatology for each regression output in its own unit and panel: wind (m/s), MSLP (hPa), humidity (%), rainfall (mm).",
        purpose="To check every supported regression output, not only wind, against the same references.",
        produced=f"W1 neural-only outputs on Evidence A cases with complete raw observations; rainfall inverted from log1p to mm; {REG_BASE}; 95% block-bootstrap intervals.",
        read="Lower is better within each panel; panels have different units and must not be compared with each other. " + ERRORS,
        finding=f"W1 vs persistence vs climatology MAE: wind {f(rp('wind','W1'),2)}/{f(rp('wind','persistence'),2)}/{f(rp('wind','climatology'),2)}; MSLP {f(rp('mslp','W1'),2)}/{f(rp('mslp','persistence'),2)}/{f(rp('mslp','climatology'),2)}; humidity {f(rp('humidity','W1'),2)}/{f(rp('humidity','persistence'),2)}/{f(rp('humidity','climatology'),2)}; rainfall {f(rp('rainfall','W1'),2)}/{f(rp('rainfall','persistence'),2)}/{f(rp('rainfall','climatology'),2)} (rainfall RMSE W1 {f(rp('rainfall','W1','rmse'),1)} vs climatology {f(rp('rainfall','climatology','rmse'),1)}; W1 bias {f(rp('rainfall','W1','bias'),2)} mm).",
        supports="Rainfall is the only output where W1's MAE is lower than both references; for wind, pressure and humidity persistence is better.",
        limits="The rainfall MAE advantage comes with under-forecasting and a higher RMSE than climatology; a skewed variable can reward low forecasts on MAE.",
        paper="Chapter 4, regression results table/figure. Caption: 'Figure 4.x. Next-day error of each regression output of the deployed model and two reference forecasts (separate units).'",
        source=f"figures/paper/PF-F3_regression_variables_mae.csv; run {run_a}.")
    N["PF-G_observed_vs_predicted"] = dict(
        shows="For wind, MSLP, humidity and rainfall: the number of Evidence A cases in each observed-value bin (x) and W1-forecast bin (y), with the 1:1 line.",
        purpose="To show the shape of W1's numerical errors (spread, bias, range) without publishing individual readings.",
        produced="Counts of saved W1 neural outputs against raw observations on the website cases; values outside the plotted range are counted in the end cells; rainfall cells are uneven.",
        read="Cells on the dashed 1:1 line are perfect forecasts; a horizontal band means the forecast hardly changes when the observation changes. Darker = more cases (log scale).",
        finding="Most wind forecasts sit at 2-3 m/s whatever was observed; humidity forecasts stay near 75-90%; pressure forecasts follow higher pressures but stay too high on low-pressure days; rainfall forecasts sit at 1-5 mm, too wet on dry days and too dry on wet days.",
        supports="W1's regression outputs vary much less than the observations; this explains the larger errors in PF-F and PF-F3.",
        limits="Shows spread, not skill relative to baselines; binning hides exact values.",
        paper="Chapter 4 or Appendix (regression diagnostics). Caption: 'Figure 4.x. Observed versus forecast values of the deployed model (case counts per cell; dashed line = perfect forecast).'",
        source=f"figures/paper/PF-G_observed_vs_predicted.csv; run {run_a}.")

    # -------------------------------------------------------------- earlier benchmark figures (Evidence B unless stated)
    N["F1_partitions"] = dict(
        shows="A timeline of which rows W1 used for training, tuning and scoring, by data source (primary stations, Port Area, 19 supplementary stations).",
        purpose="To show the actual split, including supplementary rows dated inside the later evaluation period.",
        produced="Reconstructed from the W1 training recipe (_train_w3.py) applied to the processed data.",
        read="Bars are date ranges; the shaded band marks dates later scored.",
        finding="Primary training 2015-01-01 to 2020-10-14, tuning 2020-10-15 to 2021-10-14, evaluation from 2021-10-15; Port Area (to 2023-10-30) and supplementary rows (to 2024-12-30) were used for training.",
        supports="The split is chronological for the primary stations; other stations' training rows overlap the evaluation dates.",
        limits="Does not explain why these cut-off dates were chosen (not recorded) and does not prove the split valid.",
        paper="Chapter 3, Data Partitioning. Caption: 'Figure 3.x. Data allocation of the deployed model by source and date.'",
        source=f"data/F1_partitions.csv; run {ctx['run_fig']}.")
    N["F2_wind_mae_by_station"] = dict(
        shows=f"Next-day wind MAE (m/s) by station for W1, persistence and climatology on {B['counts']['wind']['eligible']:,} identical Evidence B cases.",
        purpose="To test W1's wind forecast against two references with training-consistent inputs.",
        produced=f"{B_COH}; {REG_BASE}; 95% block-bootstrap intervals.",
        read="Lower is better. " + ERRORS,
        finding=f"Pooled MAE W1 {f(bw['pooled']['point']['W1']['mae'])}, persistence {f(bw['pooled']['point']['persistence']['mae'])}, climatology {f(bw['pooled']['point']['climatology']['mae'])} m/s.",
        supports="With training-consistent inputs too, W1's wind forecast is less accurate than both references.",
        limits="No day reached 10.8 m/s, so strong-wind accuracy is untested.",
        paper="Chapter 4, regression results (training-consistent benchmark). Caption: 'Figure 4.x. Next-day wind MAE on the training-consistent benchmark.'",
        source=f"data/F2_wind_mae_by_station.csv; run {run_b}.")
    N["F3_wind_monthly_means"] = dict(
        shows="Monthly means of observed wind and of each forecast, per station, over the whole Evidence B period (no dates selected).",
        purpose="To show whether W1 follows seasonal and station differences in wind.",
        produced="Daily Evidence B values averaged within each calendar month.",
        read="A good forecast line follows the observed line; a flat line means the forecast ignores seasons.",
        finding=f"W1 stays near 2.5 m/s at every station (forecast SD {f(bw['pooled']['point']['W1_pred_sd'],2)} vs observed {f(bw['pooled']['point']['obs_sd'],2)} m/s) and is far too high at Science Garden.",
        supports="W1's wind output barely varies with season or station.",
        limits="Monthly averaging hides day-to-day behaviour.",
        paper="Appendix (regression diagnostics). Caption: 'Figure A.x. Monthly mean observed and forecast wind by station.'",
        source=f"data/wind_monthly_means_by_station.csv; run {run_b}.")
    N["F4_wind_obs_vs_pred_counts"] = dict(
        shows="Counts of Evidence B cases by observed-wind bin and W1-forecast bin.",
        purpose="To show the range of W1's wind forecasts relative to observations.",
        produced="Binned counts of all Evidence B wind cases.",
        read="Cases on the diagonal are accurate; a single row means the forecast hardly changes.",
        finding="W1 never forecasts below about 2.25 m/s while observed winds range from 0 to above 6 m/s.",
        supports="W1's wind forecasts occupy a narrow band regardless of the observation.",
        limits="Does not show why (the audit points to the wind target's small share of the training loss and per-station scaling).",
        paper="Appendix. Caption: 'Figure A.x. Observed versus forecast wind (counts), training-consistent benchmark.'",
        source=f"data/F4_wind_obs_vs_pred_counts.csv; run {ctx['run_fig']}.")
    N["F5_event_timeline_monthly"] = dict(
        shows="Monthly counts of hits, misses and false alarms per station for W1+X1 at 0.601 (Evidence B).",
        purpose="To show when events and errors happened, without publishing exact dates.",
        produced="Evidence B decisions aggregated by month; totals equal the PF-C panel B matrix.",
        read="Bars above the axis are hits and misses; below are false alarms.",
        finding=f"Events cluster in a few storm months; {B['counts']['event']['events_total']} events in total, all pressure falls.",
        supports="Results rest on a small number of episodes.",
        limits="Monthly counts cannot show lead-time behaviour; events are not independent.",
        paper="Appendix. Caption: 'Figure A.x. Monthly event outcomes by station, training-consistent benchmark.'",
        source=f"data/event_outcomes_monthly_by_station.csv; run {run_b}.")
    N["F6_confusion_matrices"] = dict(
        shows="2×2 matrices with correct negatives for every Evidence B procedure on the same 3,520 cases.",
        purpose="To compare the warning burden (misses vs false alarms) of W1 and the baselines.",
        produced=f"{B_COH}; frozen thresholds (W1 raw 0.64, W1+X1 0.601/0.62); {EV_BASE}.",
        read="Each matrix sums to the case count; compare hits against false alarms.",
        finding=f"W1+X1 at 0.601: {int(xb['tp'])} hits, {int(xb['fn'])} misses, {int(xb['fp'])} false alarms; event persistence {int(peb['tp'])} hits, {int(peb['fp'])} false alarms.",
        supports="With training-consistent inputs W1+X1 at 0.601 still has the highest F1 of the procedures shown.",
        limits="Fewer hits than the historical scorecard (16 vs 24); events are pressure falls.",
        paper="Chapter 4, baseline comparison (training-consistent). Caption: 'Figure 4.x. Confusion matrices of all procedures on the training-consistent benchmark.'",
        source=f"data/F6_confusion_matrices.csv; run {run_b}.")
    N["F7_event_benchmarks"] = dict(
        shows="F1 and PR-AUC with 95% intervals for W1 and the event baselines (Evidence B).",
        purpose="To show how certain the event-detection comparison is.",
        produced="Paired circular block bootstrap over target dates (14-day blocks, 2,000 resamples).",
        read="Higher is better; wide intervals mean uncertain values.",
        finding=f"W1+X1 F1 {f(xb['f1'])} vs persistence {f(peb['f1'])} ({eb['ci']['df1_X1601_persist']['verdict']}); PR-AUC {f(eb['probabilistic']['W1+X1']['pr_auc'])} vs climatology {f(eb['probabilistic']['event_climatology']['pr_auc'])}.",
        supports="W1+X1 ranks pressure-fall days better than both baselines on training-consistent inputs.",
        limits="27 events make intervals wide; no precise level of skill is established.",
        paper="Chapter 4, baseline comparison. Caption: 'Figure 4.x. Event-detection scores with 95% block-bootstrap intervals, training-consistent benchmark.'",
        source=f"data/F7_event_benchmarks.csv; run {run_b}.")
    N["F8_variants_and_inputs"] = dict(
        shows="Each existing trained variant's X1 PR-AUC under two input constructions, and its wind MAE.",
        purpose="To show whether W1's selection among its variants holds on identical cases.",
        produced="Inference only, each variant with its own scalers and documented threshold, on Evidence B cases.",
        read="Higher PR-AUC is better; lower MAE is better.",
        finding="X1 PR-AUC (training-consistent / legacy inputs): " + "; ".join(f"{k} {f(v['S-TRAIN']['pr_auc_x1'])}/{f(v['S-LEGACY']['pr_auc_x1'])}" for k, v in list(var.items())[:4]) + "; every variant's wind MAE is far above persistence.",
        supports="Variant rankings change with input construction; no variant beats persistence on wind.",
        limits="All variants were informed by these dates; no variant is selected here.",
        paper="Appendix (model selection). Caption: 'Figure A.x. Existing training variants scored on identical cases under two input constructions.'",
        source=f"data/F8_variants_and_inputs.csv; run {ctx['run_v']}.")

    # -------------------------------------------------------------- private case figures (Evidence C)
    c1 = ctx["case1"]["per_station"]; c2 = ctx["case2"]["per_station"]
    N["PF-H"] = dict(
        shows="Per station (one figure each), three consecutive target dates around a detected event: observed wind and the three wind forecasts; observed and forecast MSLP; observed 24-hour MSLP change and W1's implied change; the W1+X1 score, decision and outcome.",
        purpose="To explain how W1 behaved around a correctly detected pressure-fall event. " + SELECTED,
        produced="Selection v1 (spec/CASE_SELECTION_v1.md): from the 24 hits, complete raw records, raw-confirmed event, ranked by correct decisions in the window (favourable), then pressure fall, then date. Saved Evidence A values; no model run.",
        read="Black diamonds are observations; blue W1, orange persistence, green climatology. In the score panel the dashed line is the 0.601 warning threshold. Each date is a separate next-day forecast.",
        finding="Outcomes (day before, event, day after): " + "; ".join(f"{s}: {', '.join(v['outcomes'])}" for s, v in c1.items()) + ". All events were pressure-triggered. W1's wind error was smaller than both baselines on 2 of 3 NAIA dates (not the event day), on 0 of 3 Sangley Point dates and on 1 of 3 Science Garden dates.",
        supports="W1+X1 warned on the event days and stayed quiet on the neighbouring non-event days in these windows.",
        limits="Selected for correct decisions; a classification success is not a regression success (W1's wind was often the worst forecast); three dates cannot show general superiority.",
        paper="Chapter 4, new subsection 'Selected illustrative case studies' (printed thesis only). Caption: 'Figure 4.x. Selected illustrative case: next-day forecasts for three consecutive target dates around a correctly detected pressure-fall event. " + SELECTED + "'",
        source=f"private: _private/thesis_export/{ctx['run_case1']}/; public summary: runs/{ctx['run_case1']}/case_selection_summary.json.")
    N["PF-I"] = dict(
        shows="The three primary stations on the same three target dates: wind, 24-hour MSLP change and the W1+X1 score/outcome per station.",
        purpose="An overall view of one event across the network. " + SELECTED,
        produced="Selection v1, output B (a date detected at all three stations).",
        read="One row per station; same colours as PF-H.",
        finding=f"Correct decisions in the window: {ctx['case1']['common']['sum_P1'] if ctx['case1'].get('common') else '—'} of 9 station-days; all three stations triggered by a pressure fall on the event day.",
        supports="X1 warned all three stations on the event date and none on the neighbouring days.",
        limits="Same as PF-H; X1 gives one shared decision, so the three rows are not independent.",
        paper="Chapter 4, selected case studies. Caption: 'Figure 4.x. Selected common window across the three primary stations. " + SELECTED + "'",
        source=f"private: _private/thesis_export/{ctx['run_case1']}/.")
    N["PF-J"] = dict(
        shows="Per station, three consecutive target dates with relatively high observed wind: observed and forecast wind, absolute wind and MSLP errors, a 'closest forecast' grid for wind/MSLP/humidity/rainfall, 24-hour MSLP change, and the W1+X1 outcome.",
        purpose="The panel's request: an example with stronger observed weather where W1's numbers were favourable. " + SELECTED + " Chosen because W1's wind error was smaller than both baselines (favourable-error selection).",
        produced="Selection v2 (spec/CASE_SELECTION_v2_regression.md), recorded before the search: complete raw records d−2..d+1 for four variables; observed wind ≥ the station's 2015-2020 90th percentile on at least one date; windows with a detected event first; ranked by dates on which W1's wind error beat both baselines, then margin, then wind, then date.",
        read="Error bars: shorter is better. The grid names the closest forecast per variable and date (W1 shaded). Each date is a separate next-day forecast.",
        finding="W1 wind beat both baselines on " + "; ".join(f"{s} {v.get('wind_wins_of_3', 0)}/3 dates (MSLP {v.get('wins_by_variable_of_3', {}).get('mslp', 0)}, humidity {v.get('wins_by_variable_of_3', {}).get('humidity', 0)}, rainfall {v.get('wins_by_variable_of_3', {}).get('rainfall', 0)})" for s, v in c2.items()) + ". Outcomes: " + "; ".join(f"{s} {', '.join(v.get('outcomes', []))}" for s, v in c2.items()) + ".",
        supports="On selected dates with relatively strong wind, W1's wind forecast can be closer than both references.",
        limits="Chosen for low W1 wind error; does not hold for pressure in these windows; Science Garden's '90th percentile' is only 2 m/s and its window has 1 wind win, a miss and a false alarm; overall W1 wind error is larger than persistence (PF-F).",
        paper="Chapter 4, selected case studies (separate from PF-H). Caption: 'Figure 4.x. Selected favourable regression example: three consecutive next-day wind forecasts during relatively strong wind. " + SELECTED + " Selected for low model wind error.'",
        source=f"private: _private/thesis_export/{ctx['run_case2']}/; public counts: runs/{ctx['run_case2']}/case_selection_v2_summary.json.")
    N["PF-K"] = dict(
        shows="The selection-v2 common window: wind, absolute wind error and W1+X1 outcome for all three stations on the same dates.",
        purpose="An overall favourable-regression view across the network. " + SELECTED,
        produced="Selection v2 common-window rule: complete at all three stations, relatively high wind at one or more, ranked by station-dates with a W1 wind win.",
        read="One row per station; shorter error bars are better.",
        finding=f"W1 wind beat both baselines on {ctx['case2']['common']['station_dates_with_wind_win_of_9'] if ctx['case2'].get('common') else 0} of 9 station-dates.",
        supports="On these dates W1's wind was the closest forecast more often than not at NAIA and Sangley Point.",
        limits="At Science Garden W1's wind was the worst forecast on every date of this window; selected for favourable error.",
        paper="Chapter 4, selected case studies. Caption: 'Figure 4.x. Selected favourable regression window across the three primary stations. " + SELECTED + "'",
        source=f"private: _private/thesis_export/{ctx['run_case2']}/.")
    N.update(panel_notes(ctx))
    N.update(persistence_notes(ctx))
    return N


PERSIST = PANEL + " Dates selected because persistence's wind and MSLP errors were both larger than W1's."


def persistence_notes(ctx: dict) -> dict:
    """Evidence E (spec/CASE_SELECTION_v4_persistence_override.md): public PF-Q, private PF-R."""
    D, run = ctx["case4"], ctx["run_case4"]
    q, a, sh, cp = D["qualifying"], D["all_complete"], D["share"], D["complete"]
    st = ("NAIA", "Sangley Point", "Science Garden")
    w = D["windows"]["per_station"]
    N = {}
    N["PF-Q_persistence_worse_dates"] = dict(
        shows="How many station-dates had persistence errors larger than W1's for both wind and MSLP, and the wind and MSLP MAE of W1, "
              "persistence and climatology on those dates, per station and pooled.",
        purpose="The panel directed a search for dates on which persistence, the reference that beats W1 on average for wind and MSLP, was "
                "worse than W1 for both. " + PERSIST,
        produced="Selection v4 (spec/CASE_SELECTION_v4_persistence_override.md, committed before the search): strict |persistence error| > "
                 "|W1 error| for wind AND MSLP on the same station-date, complete records only. Saved Evidence A rows; no model run.",
        read="Left: number (and share) of qualifying dates. Middle and right: shorter bars are better. W1 below persistence is guaranteed by "
             "the selection; the climatology bars are the only comparison the rule does not fix.",
        finding=f"{q['pooled']['n']} of {cp['pooled']:,} station-dates qualify ({sh['pooled'] * 100:.1f}%): "
                + ", ".join(f"{s} {q[s]['n']} ({sh[s] * 100:.1f}%)" for s in st) +
                f". On them, wind MAE W1 {q['pooled']['wind']['W1']:.2f} vs persistence {q['pooled']['wind']['persistence']:.2f}, climatology "
                f"{q['pooled']['wind']['climatology']:.2f} m/s; MSLP W1 {q['pooled']['mslp']['W1']:.2f} vs {q['pooled']['mslp']['persistence']:.2f} / "
                f"{q['pooled']['mslp']['climatology']:.2f} hPa. W1 was also closer than climatology for both variables on "
                f"{q['pooled']['both_beat_climatology_too']} of them.",
        supports="Dates exist, about one in thirteen, on which W1 beat persistence for both wind and MSLP; on them it was usually also closer "
                 "than climatology for MSLP.",
        limits=f"Selected for W1's success against persistence, so W1 < persistence here proves nothing about general skill. On all dates "
               f"persistence is better: wind {a['pooled']['wind']['persistence']:.2f} vs W1 {a['pooled']['wind']['W1']:.2f} m/s, MSLP "
               f"{a['pooled']['mslp']['persistence']:.2f} vs {a['pooled']['mslp']['W1']:.2f} hPa (n = {cp['pooled']:,}). Only "
               f"{q['pooled']['events']} qualifying dates are study-label events. Science Garden has few qualifying dates.",
        paper="Chapter 4, same subsection as PF-L (panel request). Caption: 'Figure 4.x. Station-dates on which persistence's next-day wind "
              "and MSLP errors were both larger than the model's, and errors on those dates. " + PERSIST + "'",
        source=f"figures/paper/PF-Q_persistence_worse_dates.csv; run {run}; spec/CASE_SELECTION_v4_persistence_override.md.")
    N["PF-R"] = dict(
        shows="Per station, three consecutive target dates that all qualify under selection v4: observed and forecast wind and MSLP with "
              "absolute errors, humidity and rainfall (not used to select), and the W1+X1 score and outcome.",
        purpose="Concrete dates for the panel where persistence was worse than W1 for wind and MSLP. " + PERSIST,
        produced="Selection v4 windows: three consecutive qualifying dates, ranked by cells (of 6) where W1 also beat climatology, then the "
                 "normalised persistence margin, then date; two-date windows only if a station has no three-date window.",
        read="Shaded = qualifying date; ★ = W1 also closer than climatology. Each date is a separate next-day forecast.",
        finding="; ".join(f"{s}: " + (f"{v['length']}-date window, W1 also beat climatology on {v['W1_beats_climatology_cells']} of {v['of_cells']} cells"
                                      if v.get("selected") else "no window (no two consecutive qualifying dates)") for s, v in w.items())
                + ". No common window qualifies at all three stations.",
        supports="On these dates W1's wind and MSLP were closer than persistence's, and mostly closer than climatology's.",
        limits="Chosen for W1's success; Science Garden has no qualifying window; not a performance estimate (see PF-Q, PF-F).",
        paper="Chapter 4, same subsection (printed thesis only). Caption: 'Figure 4.x. Selected window where persistence was worse than the "
              "model for wind and MSLP. " + PERSIST + "'",
        source=f"private: _private/thesis_export/{run}/; public counts: runs/{run}/persistence_v4_results.json.")
    return N


PANEL = ("Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; "
         "not representative of all historical dates.")
VNAME = {"wind": ("wind", "m/s"), "mslp": ("MSLP", "hPa"), "humidity": ("humidity", "%"), "rainfall": ("rainfall", "mm")}
BF_RULE = ("baseline-failure date = |persistence error| ≥ the station's 2015-2020 90th percentile of day-to-day change AND |climatology error| ≥ "
           "the station's 2015-2020 90th percentile of deviation from its month mean (W1 not used)")


def panel_notes(ctx: dict) -> dict:
    """Evidence D (spec/CASE_SELECTION_v3_panel_validation.md): public PF-L, PF-M, PF-N and private PF-O, PF-P."""
    D, run = ctx["case3"], ctx["run_case3"]
    P = D["part1_A_q90"]
    bf = lambda v, s="pooled": P[v][s]["baseline_failure"]
    al = lambda v, s="pooled": P[v][s]["all_complete"]
    mae = lambda r, m: r["point"][m]["mae"]
    verdict = lambda r, b: r["ci"][f"dmae_W1_{b}"]["verdict"].replace("established: negative", "W1 smaller (established)").replace(
        "established: positive", "W1 larger (established)")
    OA, OB = D["onsets"]["A"]["pooled"], D["onsets"]["B"]["pooled"]
    wins = [f"{VNAME[v][0]} at {s}" for v in P for s in ("NAIA", "Sangley Point", "Science Garden")
            if bf(v, s)["n"] and all(bf(v, s)["ci"][f"dmae_W1_{b}"]["verdict"] == "established: negative" for b in ("persistence", "climatology"))]
    hum_bias = al("humidity")["point"]["W1"]["bias"]
    sg_bias = al("wind", "Science Garden")["point"]["W1"]["bias"]
    hum_fall = P["humidity"]["pooled"]["baseline_failure_fall"]
    pf_fall = P["mslp"]["pooled"]["baseline_failure_fall"]
    B = D["part1_B_wind_q90"]["pooled"]["baseline_failure"]
    p2 = D["part2"]
    N = {}
    N["PF-L_baseline_failure_mae"] = dict(
        shows="For each next-day output (wind, MSLP, humidity, rainfall), the MAE of W1, persistence, climatology and a no-model control "
              "(average of the two baselines) on all complete dates and on the dates where both baselines failed; pooled over the three primary stations. "
              f"The rainfall panel shows all complete dates only (n = {al('rainfall')['n']:,}), by panel directive; its baseline-failure result is "
              "printed inside the panel and plotted in PF-M.",
        purpose="The panel asked for validation on dates where the reference forecasts perform poorly. " + PANEL +
                " Panel directive (2026-10-25): rainfall shown for all complete dates only; this panel is locked against spec/FROZEN_PF-L_rainfall.json.",
        produced=f"Selection v3 Part 1 (spec/CASE_SELECTION_v3_panel_validation.md, committed before the analysis): {BF_RULE}. W1 is scored on every "
                 "such date, whether it did well or not. Saved Evidence A rows (W1 neural-only output; no model run); raw PAGASA truth.",
        read="Shorter bars are better. Compare the four bars within a group; units differ between panels. The left group is the ordinary "
             "picture, the right group the baseline-failure dates only. Rainfall has one group (all complete dates).",
        finding=f"Rainfall, all complete dates (n = {al('rainfall')['n']:,}): W1 {mae(al('rainfall'), 'W1'):.2f} vs persistence "
                f"{mae(al('rainfall'), 'persistence'):.2f}, climatology {mae(al('rainfall'), 'climatology'):.2f} mm. On baseline-failure dates: " + "; ".join(
            f"{VNAME[v][0]} n = {bf(v)['n']}, W1 {mae(bf(v), 'W1'):.2f} vs persistence {mae(bf(v), 'persistence'):.2f}, climatology "
            f"{mae(bf(v), 'climatology'):.2f}, control {mae(bf(v), 'control'):.2f} {VNAME[v][1]}" for v in P) +
            ". On all dates W1's MAE is larger than persistence's for wind, MSLP and humidity and smaller for rainfall.",
        supports="Where both baselines failed, W1's humidity error was smaller than both baselines and the control, and its MSLP error was "
                 "smaller than climatology's (not persistence's).",
        limits=f"Choosing dates by baseline error favours any forecast that does not follow persistence or climatology; the control shows how much "
               f"of that a no-model hedge also gets. W1's humidity forecasts run {hum_bias:+.1f} percentage points high on average, so dates with "
               f"sudden humidity rises favour it; on humidity falls (n = {hum_fall['n']}) W1 is worse ({mae(hum_fall, 'W1'):.1f} vs persistence "
               f"{mae(hum_fall, 'persistence'):.1f} %). On heavy-rain baseline-failure dates W1 under-forecasts and has the largest error. These "
               f"dates are {bf('wind')['n']} of {al('wind')['n']} wind cases; they do not change the overall result.",
        paper="Chapter 4, new subsection 'Validation on dates where the reference forecasts failed (panel request)'. Caption: 'Figure 4.x. Next-day "
              "MAE on all dates and on dates where both persistence and climatology failed (training-period 90th-percentile rule), three primary "
              "stations, 2021-11-16 to 2024-12-30. " + PANEL + "'",
        source=f"figures/paper/PF-L_baseline_failure_mae.csv; run {run}; spec/CASE_SELECTION_v3_panel_validation.md.")
    N["PF-M_baseline_failure_differences"] = dict(
        shows="On baseline-failure dates only: W1's MAE minus persistence's, climatology's and the control's, per station and pooled, with 95% intervals.",
        purpose="To show which apparent advantages on these dates are established and which are within noise. " + PANEL,
        produced="Paired circular block bootstrap over target dates (14-day blocks, 2,000 resamples, seed 20261025) on the PF-L dates.",
        read="Left of the zero line = W1's error smaller. A difference is established only if its whole interval is on one side of zero. "
             "n is the number of baseline-failure station-dates.",
        finding="Pooled: " + "; ".join(f"{VNAME[v][0]}: vs persistence {verdict(bf(v), 'persistence')}, vs climatology "
                                       f"{verdict(bf(v), 'climatology')}, vs control {verdict(bf(v), 'control')}" for v in P) +
                ". Established smaller than both baselines at: " + (", ".join(wins) or "none") + ".",
        supports="W1 adds value over both baselines for humidity on dates when humidity jumped, and over climatology for pressure on dates "
                 "with large pressure changes; Science Garden is the one station where W1's wind is better on these dates.",
        limits=f"Science Garden's wind advantage comes from W1's high wind level there (bias {sg_bias:+.2f} m/s on all dates): almost all of its "
               f"baseline-failure dates are wind rises. On large MSLP falls (n = {pf_fall['n']}) W1 is not established better than persistence. "
               f"Training-consistent inputs (Evidence B) give the same wind picture: n = {B['n']}, W1 {mae(B, 'W1'):.2f} vs persistence "
               f"{mae(B, 'persistence'):.2f}, climatology {mae(B, 'climatology'):.2f} m/s.",
        paper="Chapter 4, same subsection. Caption: 'Figure 4.x. Paired MAE differences on baseline-failure dates with 95% block-bootstrap "
              "intervals. " + PANEL + "'",
        source=f"figures/paper/PF-M_baseline_failure_differences.csv; run {run}.")
    N["PF-N_event_onsets"] = dict(
        shows="Event onsets (no study-label event on the issue day, an event on the target day): how many each forecast warned of, on the "
              "website cases (A) and the training-consistent benchmark (B), with false alarms.",
        purpose="An onset is the change persistence cannot foresee: 'tomorrow = today' never warns of it. " + PANEL,
        produced="Every onset in each cohort (no date chosen by hand). W1+X1 warns at ≥ 0.601; event climatology uses its tuning-year threshold.",
        read="Bars = onsets each forecast warned of; the black dash is the number of onsets. False alarms are listed under each station.",
        finding=f"Evidence A: {OA['onsets']} onsets; W1+X1 warned of {OA['onset_hits']['W1+X1@0.601']} with {OA['false_alarms_on_non_events']['W1+X1@0.601']} "
                f"false alarms; event persistence {OA['onset_hits']['event_persistence']}; event climatology {OA['onset_hits']['event_climatology']}. "
                f"Evidence B: {OB['onsets']} onsets; W1+X1 {OB['onset_hits']['W1+X1@0.601']} ({OB['false_alarms_on_non_events']['W1+X1@0.601']} false "
                f"alarms); persistence {OB['onset_hits']['event_persistence']}; climatology {OB['onset_hits']['event_climatology']} "
                f"({OB['false_alarms_on_non_events']['event_climatology']} false alarms).",
        supports="W1+X1 warns of most sudden pressure-fall onsets that both simple references miss, with few false alarms.",
        limits="Every onset is a pressure fall, not gale-force wind; the 0.601 threshold was adopted after the website results were seen, so "
               "Evidence A is not an independent test; fewer onsets are caught with training-consistent inputs (B).",
        paper="Chapter 4, same subsection. Caption: 'Figure 4.x. Warnings of event onsets by W1+X1, event persistence and event climatology. " + PANEL + "'",
        source=f"figures/paper/PF-N_event_onsets.csv; run {run}.")
    N["PF-O"] = dict(
        shows="Per station, three consecutive target dates: observed and forecast wind, MSLP, humidity and rainfall with baseline-failure dates "
              "shaded and W1 successes starred; a closest-forecast grid; the W1+X1 score and outcome.",
        purpose="The panel's request for concrete dates where the baselines failed and W1 did better. " + PANEL,
        produced="Selection v3 Part 2: windows ranked by the number of (variable, date) cells that are baseline-failure dates on which W1 was "
                 "strictly closer than both baselines, then normalised margin, then baseline-failure cells, then date. Favourable by design.",
        read="Shaded = both baselines failed for that variable; ★ = W1 closest there. Every variable and date is shown, including those where W1 "
             "was worse. Each date is a separate next-day forecast; a gap in a line is a missing observation.",
        finding="W1 success cells (of 12): " + "; ".join(f"{s} {v.get('success_cells_of_12', 0)} of {v.get('baseline_failure_cells_of_12', 0)} "
                                                       f"baseline-failure cells, W1+X1 outcomes {', '.join(v.get('outcomes', []))}"
                                                       for s, v in p2["per_station"].items()) + ".",
        supports="On specific dates when both baselines failed, W1 was the closest forecast for some variables.",
        limits="Chosen for W1's success; at two of the three stations W1 badly under-forecast the heaviest-rain day of the window; not a "
               "performance estimate (see PF-L, PF-M).",
        paper="Chapter 4, same subsection (printed thesis only). Caption: 'Figure 4.x. Selected validation window. " + PANEL + "'",
        source=f"private: _private/thesis_export/{run}/; public counts: runs/{run}/panel_v3_results.json.")
    N["PF-P"] = dict(
        shows="The Part 2 common window: all four variables at all three primary stations on the same three dates.",
        purpose="A network-wide view of a period when both baselines failed. " + PANEL,
        produced="Common-window rule of Part 2: dates in the cohort at all three stations, ranked by total W1 success cells (of 36).",
        read="One row per station, one column per variable; shading and stars as in PF-O.",
        finding=(f"W1 success cells {p2['common']['success_cells_of_36']} of 36; baseline-failure cells {p2['common']['baseline_failure_cells_of_36']} "
                 "of 36 (success cells by station: " + ", ".join(f"{s} {n}" for s, n in p2["common"]["by_station_success"].items()) + ")."
                 ) if p2.get("common") else "No common window qualified.",
        supports="During a multi-station disturbance, W1 was closer than both failed baselines on a minority of the variable-station-dates.",
        limits="Favourable selection; W1 missed the heavy rainfall of the window at every station.",
        paper="Chapter 4, same subsection (printed thesis only). Caption: 'Figure 4.x. Selected common validation window. " + PANEL + "'",
        source=f"private: _private/thesis_export/{run}/.")
    return N


def html(n: dict, esc) -> str:
    rows = "".join(f'<p><b>{esc(lab)}:</b> {esc(n[k])}</p>' for k, lab in FIELDS)
    return f'<div class="fignotes">{rows}</div>'


def markdown(name: str, n: dict) -> str:
    return f"### {name}\n\n" + "\n".join(f"- **{lab}:** {n[k]}" for k, lab in FIELDS) + "\n"
