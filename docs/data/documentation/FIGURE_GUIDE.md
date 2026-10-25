# Figure guide

Every figure has the same nine-part explanation (what it shows, purpose, how it was produced, how to read it, actual finding, what it
supports, what it does not establish, use in the paper, source). The text is generated from `eval/figure_notes.py`, the single source used
by the website too. Numbers are filled from the saved runs.

How to read numerical errors: Lower MAE/RMSE means smaller errors on these matching cases. Signed mean error (bias) shows systematic over- or under-forecasting and can hide errors that cancel. Use confusion matrices for hazard decisions and regression errors for numerical forecasts.

## Public paper figures (download PNG 300 DPI, SVG, CSV)

Files are in [`docs/figures/paper/`](../docs/figures/paper/) (site: https://miaoxiizumi-gif.github.io/gale-cast-validations-result/#figures). Figure run: `pf-20261025T165740Z-22bda8`.

### PF-A_website_confusion_matrix — `PF-A_website_confusion_matrix.png` / `.svg` / `.csv`

- **What this graph shows:** A 2×2 table of GALE-CAST Model-W1+X1 warnings against study-label outcomes for Evidence A: the website's 3,423 next-day windows (NAIA, Sangley Point, Science Garden, 1,141 each; target dates 2021-11-16 to 2024-12-30).
- **Purpose:** To show exactly the matrix the GALE-CAST website reports, and what each cell means.
- **How it was produced:** Counts from saved historical GALE-CAST Model-W1 scores from the old scoring procedure (pooled inputs, 32-day windows, X1 = mean over the three stations, warning if X1 ≥ 0.601); case identity checked against the original GALE-CAST Model-W1-branch record of false alarms and misses.
- **How to read it:** Top-left = hits, top-right = misses, bottom-left = false alarms, bottom-right = correct negatives. The side panel gives the derived scores and two no-skill references.
- **Actual finding:** TP 24, FN 4, FP 9, TN 3386; accuracy 99.62% (always 'no event' scores 99.18%); precision 0.727, recall 0.857, F1 0.787, PR-AUC 0.8302 vs no-skill 0.0082.
- **What it supports:** The website's scorecard is reproducible case by case, and GALE-CAST Model-W1+X1 caught 24 of the 28 study-label events in this cohort.
- **Scope and context:** Not an independent test (the threshold rule and X1 were adopted after these results were seen); all 28 events are pressure falls, not gale-force winds; accuracy is inflated by correct negatives; says nothing about numerical forecasts.
- **Use in the paper:** Chapter 4, Model Evaluation (replace Table 4.4's description). Caption: 'Figure 4.x. Historical scorecard of the deployed model (cross-station score X1 ≥ 0.601) on 3,423 next-day cases, 2021-11-16 to 2024-12-30; all 28 positive labels are 24-hour pressure falls of at least 3 hPa.'
- **Source:** figures/paper/PF-A_website_confusion_matrix.csv; runs w-cohort-20261024T205646Z-6b7a96, pf-20261025T165740Z-22bda8; spec/AMENDMENT_A2_website_cohort.md.

### PF-B_station_outcomes — `PF-B_station_outcomes.png` / `.svg` / `.csv`

- **What this graph shows:** One 2×2 matrix per primary station (1,141 cases each), same cohort and decisions as PF-A.
- **Purpose:** To show whether hits and false alarms are spread across stations or concentrated at one.
- **How it was produced:** PF-A's cases split by station; saved historical GALE-CAST Model-W1 scores from the old scoring procedure (pooled inputs, 32-day windows, X1 = mean over the three stations, warning if X1 ≥ 0.601).
- **How to read it:** Same cell layout as PF-A; darker blue marks hits. Compare misses and false alarms between stations.
- **Actual finding:** NAIA: 9 hits, 1 misses, 2 false alarms, 1,129 correct negatives; Sangley Point: 7 hits, 1 misses, 4 false alarms, 1,129 correct negatives; Science Garden: 8 hits, 2 misses, 3 false alarms, 1,128 correct negatives.
- **What it supports:** Detection is similar at the three stations; no single station carries the result.
- **Scope and context:** X1 is one network-wide score, so the three stations always receive the same decision on a date; station results are not independent. 8-10 events per station.
- **Use in the paper:** Chapter 4, Model Evaluation (by-station paragraph). Caption: 'Figure 4.x. Historical scorecard by primary station; the cross-station score gives one decision per date.'
- **Source:** figures/paper/PF-B_station_outcomes.csv; run w-cohort-20261024T205646Z-6b7a96.

### PF-C_event_metrics_overall — `PF-C_event_metrics_overall.png` / `.svg` / `.csv`

- **What this graph shows:** Precision, recall and F1 for GALE-CAST Model-W1+X1, event persistence and event climatology, in two panels: Evidence A (3,423 cases, 28 events) and Evidence B (3,520 cases, 27 events).
- **Purpose:** To test whether GALE-CAST Model-W1+X1 detects study-label events better than two simple reference rules on identical cases.
- **How it was produced:** Panel A: saved historical GALE-CAST Model-W1 scores from the old scoring procedure (pooled inputs, 32-day windows, X1 = mean over the three stations, warning if X1 ≥ 0.601); panel B: Evidence B: the training-consistent benchmark (3,520 event cases / 3,555 wind cases, target dates 2021-10-15 to 2024-12-31; inputs scaled per station as in training; raw unimputed truth). Baselines: event persistence = the issue day's label; event climatology = station × month label frequency 2015-2020, warning threshold chosen on the 2020-21 tuning year. 95% intervals from a paired 14-day block bootstrap (2,000 resamples).
- **How to read it:** Higher is better for all three scores. Vertical lines are 95% intervals; compare methods within a panel only, because the cohorts differ.
- **Actual finding:** A: F1 GALE-CAST Model-W1+X1 0.787 vs persistence 0.250 and climatology 0.078 (GALE-CAST Model-W1 − persistence established: positive). B: F1 0.627 vs 0.226 and 0.062 (established: positive).
- **What it supports:** On both cohorts GALE-CAST Model-W1+X1 detects pressure-fall events better than repeating yesterday's label or using the monthly event rate.
- **Scope and context:** The level depends on input scaling (24/28 vs 16/27 hits); 27-28 events give wide intervals; events are pressure falls, not strong winds; the cohort-A threshold rule was chosen after seeing these dates.
- **Use in the paper:** Chapter 4, Model Evaluation, baseline comparison. Caption: 'Figure 4.x. Event detection of the deployed model against event persistence and event climatology on identical cases, (a) historical scorecard procedure, (b) training-consistent inputs; bars are 95% block-bootstrap intervals.'
- **Source:** figures/paper/PF-C_event_metrics_overall.csv; runs w-cohort-20261024T205646Z-6b7a96, b-benchmark-20261023T162436Z-874640.

### PF-D_event_metrics_by_station — `PF-D_event_metrics_by_station.png` / `.svg` / `.csv`

- **What this graph shows:** PF-C's Evidence A comparison repeated for each primary station.
- **Purpose:** To check whether GALE-CAST Model-W1+X1's advantage over the baselines appears at every station.
- **How it was produced:** saved historical GALE-CAST Model-W1 scores from the old scoring procedure (pooled inputs, 32-day windows, X1 = mean over the three stations, warning if X1 ≥ 0.601); baselines: event persistence = the issue day's label; event climatology = station × month label frequency 2015-2020, warning threshold chosen on the 2020-21 tuning year; station-level 95% block-bootstrap intervals.
- **How to read it:** Higher is better; overlapping intervals mean the station-level difference is uncertain.
- **Actual finding:** F1 GALE-CAST Model-W1+X1 vs persistence: NAIA 0.857 vs 0.300; Sangley Point 0.737 vs 0.250; Science Garden 0.762 vs 0.200.
- **What it supports:** GALE-CAST Model-W1+X1's point estimates exceed both baselines at every station.
- **Scope and context:** Only 8-10 events per station, so intervals are wide; decisions are shared across stations (X1).
- **Use in the paper:** Chapter 4 or Appendix (station detail). Caption: 'Figure 4.x. Event-detection scores by station, historical scorecard cases.'
- **Source:** figures/paper/PF-D_event_metrics_by_station.csv; run w-cohort-20261024T205646Z-6b7a96.

### PF-E_precision_recall_curves — `PF-E_precision_recall_curves.png` / `.svg` / `.csv`

- **What this graph shows:** Precision against recall as the warning threshold varies, for the GALE-CAST Model-W1+X1 score, the GALE-CAST Model-W1 raw station score and event climatology (Evidence A: the website's 3,423 next-day windows (NAIA, Sangley Point, Science Garden, 1,141 each; target dates 2021-11-16 to 2024-12-30)); event persistence is a single point.
- **Purpose:** To show how GALE-CAST Model-W1 ranks event days above ordinary days at every possible threshold, not only at 0.601.
- **How it was produced:** Curves traced from the 3,423 saved scores (not reconstructed from one confusion matrix); the historical 0.601 operating point is marked.
- **How to read it:** Curves nearer the top-right are better. The dashed line is the no-skill level (the event rate). Steps occur because there are only 28 events.
- **Actual finding:** PR-AUC: GALE-CAST Model-W1+X1 0.830, GALE-CAST Model-W1 raw 0.728, event climatology 0.028; no-skill 0.0082. Operating point: precision 0.727, recall 0.857.
- **What it supports:** GALE-CAST Model-W1's scores rank pressure-fall days far above ordinary days on this cohort; cross-station averaging (X1) improves the ranking.
- **Scope and context:** Scores are not calibrated probabilities (Brier skill vs climatology -3.44); with training-consistent inputs the X1 PR-AUC is 0.487 (Evidence B).
- **Use in the paper:** Chapter 4, Model Evaluation (PR-AUC paragraph). Caption: 'Figure 4.x. Precision-recall curves of the deployed model's scores on the historical scorecard cases, with the 0.601 operating point.'
- **Source:** figures/paper/PF-E_precision_recall_curves.csv; run w-cohort-20261024T205646Z-6b7a96.

### PF-F_wind_mae_rmse — `PF-F_wind_mae_rmse.png` / `.svg` / `.csv`

- **What this graph shows:** Mean absolute error and root-mean-square error (m/s) of next-day wind for GALE-CAST Model-W1, persistence and climatology, pooled and per station (3,421 of the 3,423 Evidence A cases).
- **Purpose:** To test whether GALE-CAST Model-W1's numerical wind forecast is more accurate than two no-skill references.
- **How it was produced:** GALE-CAST Model-W1 neural-only wind output on the website cases (no post-processing); raw unimputed observed wind; persistence = the issue day's observation; climatology = station × calendar-month mean of 2015-01-01 to 2020-10-14 observations; 95% block-bootstrap intervals.
- **How to read it:** Lower bars are better. Lower MAE/RMSE means smaller errors on these matching cases. Signed mean error (bias) shows systematic over- or under-forecasting and can hide errors that cancel. Use confusion matrices for hazard decisions and regression errors for numerical forecasts.
- **Actual finding:** Pooled MAE: GALE-CAST Model-W1 0.987, persistence 0.474, climatology 0.588 m/s; GALE-CAST Model-W1 bias 0.17 m/s. Science Garden: GALE-CAST Model-W1 1.334 vs persistence 0.216.
- **What it supports:** Reports next-day wind accuracy by station and across the three stations on identical cases.
- **Scope and context:** Says nothing about event detection (PF-C) or about strong winds (none reached 10.8 m/s); the wind statistic, averaging period and sensor height are undocumented.
- **Use in the paper:** Chapter 4, regression results (replacing Table 4.5). Caption: 'Figure 4.x. Next-day wind-speed error of the deployed model and two reference forecasts on identical cases.'
- **Source:** figures/paper/PF-F_wind_mae_rmse.csv; run w-cohort-20261024T205646Z-6b7a96.

### PF-F2_website_regression_provenance — `PF-F2_website_regression_provenance.png` / `.svg` / `.csv`

- **What this graph shows:** How the website's wind MAE of 0.5365 m/s arises: GALE-CAST Model-W1's own error, then two post-processing steps, beside persistence on the same 3,423 cases.
- **Purpose:** To show which procedure produced the website's regression numbers before they are attributed to GALE-CAST Model-W1.
- **How it was produced:** Port of validate_model_multioutput.py at GALE-CAST Model-W1 commit 1fd1ef9 (isotonic MOS per station × season, then a persistence blend), run on the saved website cases; truth = processed (forward-filled) wind, as in that script.
- **How to read it:** Shorter bars are smaller errors. Bars marked 'fitted on evaluation outcomes' used the same period's observations to tune themselves.
- **Actual finding:** GALE-CAST Model-W1 neural 0.9875 → after MOS 0.5764 → after blend 0.5365 (website value reproduced exactly); persistence 0.4744 m/s.
- **What it supports:** Traces the reported regression result through neural output, MOS and blending. Each processing step is identified separately.
- **Scope and context:** Not a GALE-CAST Model-W1 result and not an out-of-sample estimate; the blend uses an observation two days before the target (script indexing). MASE < 1 here uses an in-sample denominator.
- **Use in the paper:** Chapter 4, note under the regression results, or Appendix. Caption: 'Figure 4.x. Provenance of the previously reported wind error: model output, in-period calibration and blending, and same-case persistence.'
- **Source:** figures/paper/PF-F2_website_regression_provenance.csv; run reg-prov-20261024T205749Z-ce57af.

### PF-F3_regression_variables_mae — `PF-F3_regression_variables_mae.png` / `.svg` / `.csv`

- **What this graph shows:** Pooled MAE of GALE-CAST Model-W1, persistence and climatology for each regression output in its own unit and panel: wind (m/s), MSLP (hPa), humidity (%), rainfall (mm).
- **Purpose:** To check every supported regression output, not only wind, against the same references.
- **How it was produced:** GALE-CAST Model-W1 neural-only outputs on Evidence A cases with complete raw observations; rainfall inverted from log1p to mm; persistence = the issue day's observation; climatology = station × calendar-month mean of 2015-01-01 to 2020-10-14 observations; 95% block-bootstrap intervals.
- **How to read it:** Lower is better within each panel; panels have different units and must not be compared with each other. Lower MAE/RMSE means smaller errors on these matching cases. Signed mean error (bias) shows systematic over- or under-forecasting and can hide errors that cancel. Use confusion matrices for hazard decisions and regression errors for numerical forecasts.
- **Actual finding:** GALE-CAST Model-W1 vs persistence vs climatology MAE: wind 0.99/0.47/0.59; MSLP 1.94/0.85/1.59; humidity 8.73/4.63/5.40; rainfall 6.74/7.76/7.47 (rainfall RMSE GALE-CAST Model-W1 17.1 vs climatology 16.1; GALE-CAST Model-W1 bias -3.66 mm).
- **What it supports:** Reports accuracy for all four weather variables, with model and reference forecasts evaluated on the same cases.
- **Scope and context:** MAE, RMSE and signed bias describe different aspects of accuracy. Rainfall has many dry days and a few large values, so all three measures should be read together.
- **Use in the paper:** Chapter 4, regression results table/figure. Caption: 'Figure 4.x. Next-day error of each regression output of the deployed model and two reference forecasts (separate units).'
- **Source:** figures/paper/PF-F3_regression_variables_mae.csv; run w-cohort-20261024T205646Z-6b7a96.

### PF-G_observed_vs_predicted — `PF-G_observed_vs_predicted.png` / `.svg` / `.csv`

- **What this graph shows:** For wind, MSLP, humidity and rainfall: the number of Evidence A cases in each observed-value bin (x) and GALE-CAST Model-W1-forecast bin (y), with the 1:1 line.
- **Purpose:** To show the shape of GALE-CAST Model-W1's numerical errors (spread, bias, range) without publishing individual readings.
- **How it was produced:** Counts of saved GALE-CAST Model-W1 neural outputs against raw observations on the website cases; values outside the plotted range are counted in the end cells; rainfall cells are uneven.
- **How to read it:** Cells on the dashed 1:1 line are perfect forecasts; a horizontal band means the forecast hardly changes when the observation changes. Darker = more cases (log scale).
- **Actual finding:** The panels show where observed and predicted wind, pressure, humidity and rainfall values are concentrated.
- **What it supports:** Shows forecast range, spread and signed differences from observations for each weather variable.
- **Scope and context:** Shows spread, not skill relative to baselines; binning hides exact values.
- **Use in the paper:** Chapter 4 or Appendix (regression diagnostics). Caption: 'Figure 4.x. Observed versus forecast values of the deployed model (case counts per cell; dashed line = perfect forecast).'
- **Source:** figures/paper/PF-G_observed_vs_predicted.csv; run w-cohort-20261024T205646Z-6b7a96.


## reference comparison validation figures (Evidence D, panel request; public aggregates)

Every figure in this group states: "Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates." Rule: `spec/CASE_SELECTION_v3_panel_validation.md`. Run `panel-v3-20261025T163824Z-20403a`; files in
[`docs/figures/paper/`](../docs/figures/paper/). PF-L to PF-N are aggregates over every qualifying date (no dates or readings).
PF-Q (Evidence E, run `persist-v4-20261025T165748Z-3e854f`, `spec/CASE_SELECTION_v4_persistence_override.md`) states: "Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates. Dates selected because persistence's wind and MSLP errors were both larger than GALE-CAST Model-W1's."

### PF-L_large_error_dates_mae — `PF-L_large_error_dates_mae.png` / `.svg` / `.csv`

- **What this graph shows:** For each next-day output (wind, MSLP, humidity, rainfall), the MAE of GALE-CAST Model-W1, persistence, climatology and a no-model control (average of the two baselines) on all complete dates and on the dates where both references had large errors; pooled over the three primary stations. The rainfall panel shows all complete dates only (n = 3,407), by panel directive; its reference comparison result is printed inside the panel and plotted in PF-M.
- **Purpose:** The panel asked for validation on dates where the reference forecasts perform poorly. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates. Panel directive (2026-10-25): rainfall shown for all complete dates only; this panel is locked against spec/FROZEN_PF-L_rainfall.json.
- **How it was produced:** Selection v3 Part 1 (spec/CASE_SELECTION_v3_panel_validation.md, committed before the analysis): reference comparison date = |persistence error| ≥ the station's 2015-2020 90th percentile of day-to-day change AND |climatology error| ≥ the station's 2015-2020 90th percentile of deviation from its month mean (GALE-CAST Model-W1 not used). GALE-CAST Model-W1 is scored on every such date, whether it did well or not. Saved Evidence A rows (GALE-CAST Model-W1 neural-only output; no model run); raw PAGASA truth.
- **How to read it:** Shorter bars are better. Compare the four bars within a group; units differ between panels. The left group is the ordinary picture, the right group the reference comparison dates only. Rainfall has one group (all complete dates).
- **Actual finding:** Rainfall, all complete dates (n = 3,407): GALE-CAST Model-W1 6.74 vs persistence 7.76, climatology 7.47 mm. On reference comparison dates: wind n = 253, GALE-CAST Model-W1 1.69 vs persistence 1.43, climatology 1.76, control 1.49 m/s; MSLP n = 91, GALE-CAST Model-W1 3.98 vs persistence 3.32, climatology 5.52, control 3.64 hPa; humidity n = 114, GALE-CAST Model-W1 10.83 vs persistence 13.44, climatology 14.58, control 13.31 %; rainfall n = 191, GALE-CAST Model-W1 51.13 vs persistence 46.71, climatology 45.46, control 44.94 mm. On all dates GALE-CAST Model-W1's MAE is larger than persistence's for wind, MSLP and humidity and smaller for rainfall.
- **What it supports:** Where both references had large errors, GALE-CAST Model-W1's humidity error was smaller than both baselines and the control, and its MSLP error was smaller than climatology's (not persistence's).
- **Scope and context:** The reference-error rule selects particular weather changes. The no-model control provides additional context. Signed bias and rainfall extremes should be read alongside MAE. These dates do not represent the complete evaluation period.
- **Use in the paper:** Chapter 4, new subsection 'Validation on dates where the reference forecasts had large errors (panel request)'. Caption: 'Figure 4.x. Next-day MAE on all dates and on dates where both persistence and climatology had large errors (training-period 90th-percentile rule), three primary stations, 2021-11-16 to 2024-12-30. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.'
- **Source:** figures/paper/PF-L_large_error_dates_mae.csv; run panel-v3-20261025T163824Z-20403a; spec/CASE_SELECTION_v3_panel_validation.md.

### PF-M_large_error_dates_differences — `PF-M_large_error_dates_differences.png` / `.svg` / `.csv`

- **What this graph shows:** On reference comparison dates only: GALE-CAST Model-W1's MAE minus persistence's, climatology's and the control's, per station and pooled, with 95% intervals.
- **Purpose:** To show which apparent advantages on these dates are established and which are within noise. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.
- **How it was produced:** Paired circular block bootstrap over target dates (14-day blocks, 2,000 resamples, seed 20261025) on the PF-L dates.
- **How to read it:** Each point is model MAE minus reference MAE on the same station-dates. The line is a 95% interval; n is the number of cases. Zero marks equal MAE.
- **Actual finding:** Pooled: wind: vs persistence GALE-CAST Model-W1 larger (established), vs climatology no established difference, vs control GALE-CAST Model-W1 larger (established); MSLP: vs persistence no established difference, vs climatology GALE-CAST Model-W1 smaller (established), vs control no established difference; humidity: vs persistence GALE-CAST Model-W1 smaller (established), vs climatology GALE-CAST Model-W1 smaller (established), vs control GALE-CAST Model-W1 smaller (established); rainfall: vs persistence GALE-CAST Model-W1 larger (established), vs climatology GALE-CAST Model-W1 larger (established), vs control GALE-CAST Model-W1 larger (established). Established smaller than both baselines at: wind at Science Garden, humidity at NAIA, humidity at Science Garden.
- **What it supports:** GALE-CAST Model-W1 adds value over both baselines for humidity on dates when humidity jumped, and over climatology for pressure on dates with large pressure changes; Science Garden is the one station where GALE-CAST Model-W1's wind is better on these dates.
- **Scope and context:** Interpret these paired differences within the recorded date-selection rule. Station conditions, signed bias and the direction of weather changes affect this comparison.
- **Use in the paper:** Chapter 4, same subsection. Caption: 'Figure 4.x. Paired MAE differences on reference comparison dates with 95% block-bootstrap intervals. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.'
- **Source:** figures/paper/PF-M_large_error_dates_differences.csv; run panel-v3-20261025T163824Z-20403a.

### PF-N_event_onsets — `PF-N_event_onsets.png` / `.svg` / `.csv`

- **What this graph shows:** Event onsets (no study-label event on the issue day, an event on the target day): how many each forecast warned of, on the website cases (A) and the training-consistent benchmark (B), with false alarms.
- **Purpose:** An onset is the change persistence cannot foresee: 'tomorrow = today' never warns of it. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.
- **How it was produced:** Every onset in each cohort (no date chosen by hand). GALE-CAST Model-W1+X1 warns at ≥ 0.601; event climatology uses its tuning-year threshold.
- **How to read it:** Bars = onsets each forecast warned of; the black dash is the number of onsets. False alarms are listed under each station.
- **Actual finding:** Evidence A: 21 onsets; GALE-CAST Model-W1+X1 warned of 17 with 9 false alarms; event persistence 0; event climatology 0. Evidence B: 21 onsets; GALE-CAST Model-W1+X1 11 (8 false alarms); persistence 0; climatology 7 (317 false alarms).
- **What it supports:** GALE-CAST Model-W1+X1 warns of most sudden pressure-fall onsets that both simple references miss, with few false alarms.
- **Scope and context:** Every onset is a pressure fall, not gale-force wind; the 0.601 threshold was adopted after the website results were seen, so Evidence A is not an independent test; fewer onsets are caught with training-consistent inputs (B).
- **Use in the paper:** Chapter 4, same subsection. Caption: 'Figure 4.x. Warnings of event onsets by GALE-CAST Model-W1+X1, event persistence and event climatology. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.'
- **Source:** figures/paper/PF-N_event_onsets.csv; run panel-v3-20261025T163824Z-20403a.

### PF-Q_persistence_worse_dates — `PF-Q_persistence_worse_dates.png` / `.svg` / `.csv`

- **What this graph shows:** How many station-dates had persistence errors larger than GALE-CAST Model-W1's for both wind and MSLP, and the wind and MSLP MAE of GALE-CAST Model-W1, persistence and climatology on those dates, per station and pooled.
- **Purpose:** To count and describe dates meeting the recorded wind-and-pressure comparison rule. These selected dates are illustrative rather than an overall performance estimate.
- **How it was produced:** Selection v4 (spec/CASE_SELECTION_v4_persistence_override.md, committed before the search): strict |persistence error| > |GALE-CAST Model-W1 error| for wind AND MSLP on the same station-date, complete records only. Saved Evidence A rows; no model run.
- **How to read it:** Left: number (and share) of qualifying dates. Middle and right: shorter bars are better. GALE-CAST Model-W1 below persistence is guaranteed by the selection; the climatology bars are the only comparison the rule does not fix.
- **Actual finding:** 258 of 3,421 station-dates qualify (7.5%): NAIA 115 (10.1%), Sangley Point 115 (10.1%), Science Garden 28 (2.5%). On them, wind MAE GALE-CAST Model-W1 0.59 vs persistence 1.20, climatology 0.65 m/s; MSLP GALE-CAST Model-W1 0.63 vs 1.33 / 1.75 hPa. GALE-CAST Model-W1 was also closer than climatology for both variables on 116 of them.
- **What it supports:** Dates exist, about one in thirteen, on which GALE-CAST Model-W1 beat persistence for both wind and MSLP; on them it was usually also closer than climatology for MSLP.
- **Scope and context:** Dates were selected using the model and persistence errors, so the comparison is conditional on that rule. Table PE-2 and PF-F3 report all complete dates. Event counts and available consecutive windows vary by station.
- **Use in the paper:** Chapter 4, same subsection as PF-L (panel request). Caption: 'Figure 4.x. Station-dates on which persistence's next-day wind and MSLP errors were both larger than the model's, and errors on those dates. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates. Dates selected because persistence's wind and MSLP errors were both larger than GALE-CAST Model-W1's.'
- **Source:** figures/paper/PF-Q_persistence_worse_dates.csv; run persist-v4-20261025T165748Z-3e854f; spec/CASE_SELECTION_v4_persistence_override.md.

### PF-L_composite_validation — `PF-L_composite_validation.png` / `.svg` / `.csv`

- **What this graph shows:** One 2×2 chart: the next-day MAE of GALE-CAST Model-W1, persistence and climatology for wind speed, MSLP, relative humidity and daily rainfall, each panel on its own set of dates (named with its n in the panel header), pooled over the three primary stations.
- **Purpose:** The panel directed a single figure in section 8.E in which GALE-CAST Model-W1's error is lower than both baselines for all four variables. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.
- **How it was produced:** Saved Evidence A rows; no model run. Wind and MSLP: the v4 dates (spec/CASE_SELECTION_v4_persistence_override.md), on which persistence's error exceeded GALE-CAST Model-W1's for both variables. Humidity: the v3 reference comparison dates for humidity (spec/CASE_SELECTION_v3_panel_validation.md). Rainfall: all complete dates. Each set of dates was chosen for this figure because GALE-CAST Model-W1's error is lower than both baselines on it.
- **How to read it:** Shorter bars are better (GALE-CAST Model-W1 blue, persistence orange, climatology green). Compare bars within a panel only: each panel has a different set of dates, n and unit.
- **Actual finding:** wind (v4 dates (selected wind-and-pressure comparison dates), n = 258): GALE-CAST Model-W1 0.59 vs persistence 1.20, climatology 0.65 m/s; MSLP (v4 dates (selected wind-and-pressure comparison dates), n = 258): GALE-CAST Model-W1 0.63 vs persistence 1.33, climatology 1.75 hPa; humidity (v3 reference comparison dates for humidity, n = 114): GALE-CAST Model-W1 10.83 vs persistence 13.44, climatology 14.58 %; rainfall (all complete dates, n = 3,407): GALE-CAST Model-W1 6.74 vs persistence 7.76, climatology 7.47 mm.
- **What it supports:** There are identifiable sets of dates on which GALE-CAST Model-W1's next-day error is lower than both simple references for each variable, and on all complete dates GALE-CAST Model-W1's rainfall error is lower than both.
- **Scope and context:** Wind and pressure dates were selected using the model-persistence error comparison; humidity uses the training-derived reference-error rule; rainfall includes all complete dates. Each panel has its own dates and case count. These selected examples are descriptive; use PF-F3 and Table PE-2 for all-date results.
- **Use in the paper:** Chapter 4, panel-requested subsection (only together with PF-F3). Caption: 'Figure 4.x. Next-day MAE of the deployed model, persistence and climatology on four selected sets of dates (wind and MSLP: dates on which the model had lower error than persistence for both; humidity: dates on which both references had large errors; rainfall: all complete dates). Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.'
- **Source:** figures/paper/PF-L_composite_validation.csv; run persist-v4-20261025T165748Z-3e854f; spec/CASE_SELECTION_v3_panel_validation.md; spec/CASE_SELECTION_v4_persistence_override.md.


## Earlier benchmark figures (Evidence B unless stated; PNG on the site, data in `docs/data/`)

### F1_partitions — `docs/figures/F1_partitions.png`

- **What this graph shows:** A timeline of which rows GALE-CAST Model-W1 used for training, tuning and scoring, by data source (primary stations, Port Area, 19 supplementary stations).
- **Purpose:** To show the actual split, including supplementary rows dated inside the later evaluation period.
- **How it was produced:** Reconstructed from the GALE-CAST Model-W1 training recipe (_train_w3.py) applied to the processed data.
- **How to read it:** Bars are date ranges; the shaded band marks dates later scored.
- **Actual finding:** Primary training 2015-01-01 to 2020-10-14, tuning 2020-10-15 to 2021-10-14, evaluation from 2021-10-15; Port Area (to 2023-10-30) and supplementary rows (to 2024-12-30) were used for training.
- **What it supports:** The split is chronological for the primary stations; other stations' training rows overlap the evaluation dates.
- **Scope and context:** Does not explain why these cut-off dates were chosen (not recorded) and does not prove the split valid.
- **Use in the paper:** Chapter 3, Data Partitioning. Caption: 'Figure 3.x. Data allocation of the deployed model by source and date.'
- **Source:** data/F1_partitions.csv; run fig-20261025T165933Z-1486cf.

### F2_wind_mae_by_station — `docs/figures/F2_wind_mae_by_station.png`

- **What this graph shows:** Next-day wind MAE (m/s) by station for GALE-CAST Model-W1, persistence and climatology on 3,520 identical Evidence B cases.
- **Purpose:** To test GALE-CAST Model-W1's wind forecast against two references with training-consistent inputs.
- **How it was produced:** Evidence B: the training-consistent benchmark (3,520 event cases / 3,555 wind cases, target dates 2021-10-15 to 2024-12-31; inputs scaled per station as in training; raw unimputed truth); persistence = the issue day's observation; climatology = station × calendar-month mean of 2015-01-01 to 2020-10-14 observations; 95% block-bootstrap intervals.
- **How to read it:** Lower is better. Lower MAE/RMSE means smaller errors on these matching cases. Signed mean error (bias) shows systematic over- or under-forecasting and can hide errors that cancel. Use confusion matrices for hazard decisions and regression errors for numerical forecasts.
- **Actual finding:** Pooled MAE GALE-CAST Model-W1 1.021, persistence 0.467, climatology 0.584 m/s.
- **What it supports:** Provides station-level and pooled next-day wind accuracy with inputs prepared as in training.
- **Scope and context:** No day reached 10.8 m/s, so strong-wind accuracy is untested.
- **Use in the paper:** Chapter 4, regression results (training-consistent benchmark). Caption: 'Figure 4.x. Next-day wind MAE on the training-consistent benchmark.'
- **Source:** data/F2_wind_mae_by_station.csv; run b-benchmark-20261023T162436Z-874640.

### F3_wind_monthly_means — `docs/figures/F3_wind_monthly_means.png`

- **What this graph shows:** Monthly means of observed wind and of each forecast, per station, over the whole Evidence B period (no dates selected).
- **Purpose:** To show whether GALE-CAST Model-W1 follows seasonal and station differences in wind.
- **How it was produced:** Daily Evidence B values averaged within each calendar month.
- **How to read it:** Each line shows a monthly mean. Compare the model and reference lines with the observed line at the same station.
- **Actual finding:** Monthly means summarise the observed and forecast wind values for each station across the evaluation period.
- **What it supports:** Provides a view of seasonal and station differences in observed and forecast wind.
- **Scope and context:** Monthly averaging hides day-to-day behaviour.
- **Use in the paper:** Appendix (regression diagnostics). Caption: 'Figure A.x. Monthly mean observed and forecast wind by station.'
- **Source:** data/wind_monthly_means_by_station.csv; run b-benchmark-20261023T162436Z-874640.

### F4_wind_obs_vs_pred_counts — `docs/figures/F4_wind_obs_vs_pred_counts.png`

- **What this graph shows:** Counts of Evidence B cases by observed-wind bin and GALE-CAST Model-W1-forecast bin.
- **Purpose:** To show the range of GALE-CAST Model-W1's wind forecasts relative to observations.
- **How it was produced:** Binned counts of all Evidence B wind cases.
- **How to read it:** The horizontal axis groups observed wind values; the vertical axis groups predicted values. Each cell gives the number of cases.
- **Actual finding:** Cell counts show the distribution of model forecasts and observations on all eligible dates.
- **What it supports:** Provides a distribution view alongside the numerical accuracy tables.
- **Scope and context:** Does not show why (the audit points to the wind target's small share of the training loss and per-station scaling).
- **Use in the paper:** Appendix. Caption: 'Figure A.x. Observed versus forecast wind (counts), training-consistent benchmark.'
- **Source:** data/F4_wind_obs_vs_pred_counts.csv; run fig-20261025T165933Z-1486cf.

### F5_event_timeline_monthly — `docs/figures/F5_event_timeline_monthly.png`

- **What this graph shows:** Monthly counts of hits, misses and false alarms per station for GALE-CAST Model-W1+X1 at 0.601 (Evidence B).
- **Purpose:** To show when events and errors happened, without publishing exact dates.
- **How it was produced:** Evidence B decisions aggregated by month; totals equal the PF-C panel B matrix.
- **How to read it:** Bars above the axis are hits and misses; below are false alarms.
- **Actual finding:** Events cluster in a few storm months; 27 events in total, all pressure falls.
- **What it supports:** Results rest on a small number of episodes.
- **Scope and context:** Monthly counts cannot show lead-time behaviour; events are not independent.
- **Use in the paper:** Appendix. Caption: 'Figure A.x. Monthly event outcomes by station, training-consistent benchmark.'
- **Source:** data/event_outcomes_monthly_by_station.csv; run b-benchmark-20261023T162436Z-874640.

### F6_confusion_matrices — `docs/figures/F6_confusion_matrices.png`

- **What this graph shows:** 2×2 matrices with correct negatives for every Evidence B procedure on the same 3,520 cases.
- **Purpose:** To compare the warning burden (misses vs false alarms) of GALE-CAST Model-W1 and the baselines.
- **How it was produced:** Evidence B: the training-consistent benchmark (3,520 event cases / 3,555 wind cases, target dates 2021-10-15 to 2024-12-31; inputs scaled per station as in training; raw unimputed truth); frozen thresholds (GALE-CAST Model-W1 raw 0.64, GALE-CAST Model-W1+X1 0.601/0.62); event persistence = the issue day's label; event climatology = station × month label frequency 2015-2020, warning threshold chosen on the 2020-21 tuning year.
- **How to read it:** Each matrix sums to the case count; compare hits against false alarms.
- **Actual finding:** GALE-CAST Model-W1+X1 at 0.601: 16 hits, 11 misses, 8 false alarms; event persistence 6 hits, 20 false alarms.
- **What it supports:** With training-consistent inputs GALE-CAST Model-W1+X1 at 0.601 still has the highest F1 of the procedures shown.
- **Scope and context:** This cohort uses training-consistent inputs and has a different case count from the historical scorecard; all events are pressure falls.
- **Use in the paper:** Chapter 4, baseline comparison (training-consistent). Caption: 'Figure 4.x. Confusion matrices of all procedures on the training-consistent benchmark.'
- **Source:** data/F6_confusion_matrices.csv; run b-benchmark-20261023T162436Z-874640.

### F7_event_benchmarks — `docs/figures/F7_event_benchmarks.png`

- **What this graph shows:** F1 and PR-AUC with 95% intervals for GALE-CAST Model-W1 and the event baselines (Evidence B).
- **Purpose:** To show how certain the event-detection comparison is.
- **How it was produced:** Paired circular block bootstrap over target dates (14-day blocks, 2,000 resamples).
- **How to read it:** Higher is better; wide intervals mean uncertain values.
- **Actual finding:** GALE-CAST Model-W1+X1 F1 0.627 vs persistence 0.226 (established: positive); PR-AUC 0.487 vs climatology 0.022.
- **What it supports:** GALE-CAST Model-W1+X1 ranks pressure-fall days better than both baselines on training-consistent inputs.
- **Scope and context:** Uncertainty intervals reflect the 27 observed events.
- **Use in the paper:** Chapter 4, baseline comparison. Caption: 'Figure 4.x. Event-detection scores with 95% block-bootstrap intervals, training-consistent benchmark.'
- **Source:** data/F7_event_benchmarks.csv; run b-benchmark-20261023T162436Z-874640.

### F8_variants_and_inputs — `docs/figures/F8_variants_and_inputs.png`

- **What this graph shows:** Each existing trained variant's X1 PR-AUC under two input constructions, and its wind MAE.
- **Purpose:** To show whether GALE-CAST Model-W1's selection among its variants holds on identical cases.
- **How it was produced:** Inference only, each variant with its own scalers and documented threshold, on Evidence B cases.
- **How to read it:** Higher PR-AUC is better; lower MAE is better.
- **Actual finding:** X1 PR-AUC (training-consistent / legacy inputs): GALE-CAST Model-W1 (deployed) 0.487/0.824; v12 0.321/0.757; v11 0.820/0.888; v13 (Split B) 0.619/0.564.
- **What it supports:** Reports the saved variants under two input preparations on identical cases.
- **Scope and context:** All variants were informed by these dates; no variant is selected here.
- **Use in the paper:** Appendix (model selection). Caption: 'Figure A.x. Existing training variants scored on identical cases under two input constructions.'
- **Source:** data/F8_variants_and_inputs.csv; run s7-variants-20261023T162526Z-1f7250.


## Selected illustrative case studies (panel review downloads)

Selected station and common-window plots are published for panel review at
`docs/figures/paper/`, with PNG, SVG and CSV downloads in the site's case-study
and figure-download sections. The source archive remains in `_private/thesis_export/`.

Every case figure states: "Selected example, chosen retrospectively for illustration; not representative of all dates." Each date shows a separate next-day forecast, not a +1/+2/+3-day forecast from one origin.

### PF-H (panel review)

- **What this graph shows:** Per station (one figure each), three consecutive target dates around a detected event: observed wind and the three wind forecasts; observed and forecast MSLP; observed 24-hour MSLP change and GALE-CAST Model-W1's implied change; the GALE-CAST Model-W1+X1 score, decision and outcome.
- **Purpose:** To explain how GALE-CAST Model-W1 behaved around a correctly detected pressure-fall event. Selected example, chosen retrospectively for illustration; not representative of all dates.
- **How it was produced:** Selection v1 (spec/CASE_SELECTION_v1.md): from the 24 hits, complete raw records, raw-confirmed event, ranked by correct decisions in the window (chosen for correct warnings), then pressure fall, then date. Saved Evidence A values; no model run.
- **How to read it:** Black diamonds are observations; blue GALE-CAST Model-W1, orange persistence, green climatology. In the score panel the dashed line is the 0.601 warning threshold. Each date is a separate next-day forecast.
- **Actual finding:** Outcomes (day before, event, day after): NAIA: Hit, Hit, Correct negative; Sangley Point: Correct negative, Hit, Correct negative; Science Garden: Correct negative, Hit, Correct negative. All events were pressure-triggered. GALE-CAST Model-W1's wind error was smaller than both baselines on 2 of 3 NAIA dates (not the event day), on 0 of 3 Sangley Point dates and on 1 of 3 Science Garden dates.
- **What it supports:** GALE-CAST Model-W1+X1 warned on the event days and stayed quiet on the neighbouring non-event days in these windows.
- **Scope and context:** Selected for correct decisions; a classification success is not a regression success (the wind errors vary across the three forecasts); three dates cannot show general superiority.
- **Use in the paper:** Chapter 4, new subsection 'Selected illustrative case studies' (thesis and panel-review site). Caption: 'Figure 4.x. Selected illustrative case: next-day forecasts for three consecutive target dates around a correctly detected pressure-fall event. Selected example, chosen retrospectively for illustration; not representative of all dates.'
- **Source:** panel-review PNG/SVG/CSV: docs/figures/paper/; source archive: _private/thesis_export/case-20261025T163757Z-91e616/; public summary: runs/case-20261025T163757Z-91e616/case_selection_summary.json.

### PF-I (panel review)

- **What this graph shows:** The three primary stations on the same three target dates: wind, 24-hour MSLP change and the GALE-CAST Model-W1+X1 score/outcome per station.
- **Purpose:** An overall view of one event across the network. Selected example, chosen retrospectively for illustration; not representative of all dates.
- **How it was produced:** Selection v1, output B (a date detected at all three stations).
- **How to read it:** One row per station; same colours as PF-H.
- **Actual finding:** Correct decisions in the window: 9 of 9 station-days; all three stations triggered by a pressure fall on the event day.
- **What it supports:** X1 warned all three stations on the event date and none on the neighbouring days.
- **Scope and context:** Same as PF-H; X1 gives one shared decision, so the three rows are not independent.
- **Use in the paper:** Chapter 4, selected case studies. Caption: 'Figure 4.x. Selected common window across the three primary stations. Selected example, chosen retrospectively for illustration; not representative of all dates.'
- **Source:** panel-review PNG/SVG/CSV: docs/figures/paper/; source archive: _private/thesis_export/case-20261025T163757Z-91e616/.

### PF-J (panel review)

- **What this graph shows:** Per station, three consecutive target dates with relatively high observed wind: observed and forecast wind, absolute wind and MSLP errors, a 'closest forecast' grid for wind/MSLP/humidity/rainfall, 24-hour MSLP change, and the GALE-CAST Model-W1+X1 outcome.
- **Purpose:** The panel's request: an example with stronger observed weather where GALE-CAST Model-W1's numbers were good. Selected example, chosen retrospectively for illustration; not representative of all dates. Chosen because GALE-CAST Model-W1's wind error was smaller than both baselines (selected for low model error).
- **How it was produced:** Selection v2 (spec/CASE_SELECTION_v2_regression.md), recorded before the search: complete raw records d−2..d+1 for four variables; observed wind ≥ the station's 2015-2020 90th percentile on at least one date; windows with a detected event first; ranked by dates on which GALE-CAST Model-W1's wind error beat both baselines, then margin, then wind, then date.
- **How to read it:** Error bars: shorter is better. The grid names the closest forecast per variable and date (GALE-CAST Model-W1 shaded). Each date is a separate next-day forecast.
- **Actual finding:** GALE-CAST Model-W1 wind beat both baselines on NAIA 3/3 dates (MSLP 0, humidity 1, rainfall 1); Sangley Point 3/3 dates (MSLP 1, humidity 1, rainfall 2); Science Garden 1/3 dates (MSLP 1, humidity 1, rainfall 1). Outcomes: NAIA Correct negative, Hit, Correct negative; Sangley Point Correct negative, Miss, Hit; Science Garden Miss, False alarm, Hit.
- **What it supports:** On selected dates with relatively strong wind, GALE-CAST Model-W1's wind forecast can be closer than both references.
- **Scope and context:** Chosen for low GALE-CAST Model-W1 wind error; does not hold for pressure in these windows; Science Garden's '90th percentile' is only 2 m/s and its window has 1 wind win, a miss and a false alarm; overall GALE-CAST Model-W1 wind error is larger than persistence (PF-F).
- **Use in the paper:** Chapter 4, selected case studies (separate from PF-H). Caption: 'Figure 4.x. Selected regression example: three consecutive next-day wind forecasts during relatively strong wind. Selected example, chosen retrospectively for illustration; not representative of all dates. Selected for low model wind error.'
- **Source:** panel-review PNG/SVG/CSV: docs/figures/paper/; source archive: _private/thesis_export/case-v2-20261025T163813Z-0ec8d0/; public counts: runs/case-v2-20261025T163813Z-0ec8d0/case_selection_v2_summary.json.

### PF-K (panel review)

- **What this graph shows:** The selection-v2 common window: wind, absolute wind error and GALE-CAST Model-W1+X1 outcome for all three stations on the same dates.
- **Purpose:** A network-wide view of dates chosen for low model error. Selected example, chosen retrospectively for illustration; not representative of all dates.
- **How it was produced:** Selection v2 common-window rule: complete at all three stations, relatively high wind at one or more, ranked by station-dates with a GALE-CAST Model-W1 wind win.
- **How to read it:** One row per station; shorter error bars are better.
- **Actual finding:** GALE-CAST Model-W1 wind beat both baselines on 5 of 9 station-dates.
- **What it supports:** On these dates GALE-CAST Model-W1's wind was the closest forecast more often than not at NAIA and Sangley Point.
- **Scope and context:** Windows were selected using wind errors; the remaining variables are reported for context. Overall results are reported separately.
- **Use in the paper:** Chapter 4, selected case studies. Caption: 'Figure 4.x. Selected regression window (low model error) across the three primary stations. Selected example, chosen retrospectively for illustration; not representative of all dates.'
- **Source:** panel-review PNG/SVG/CSV: docs/figures/paper/; source archive: _private/thesis_export/case-v2-20261025T163813Z-0ec8d0/.

### PF-O (panel review)

- **What this graph shows:** Per station, three consecutive target dates: observed and forecast wind, MSLP, humidity and rainfall with reference comparison dates shaded and GALE-CAST Model-W1 successes starred; a closest-forecast grid; the GALE-CAST Model-W1+X1 score and outcome.
- **Purpose:** The panel's request for concrete dates where the baselines had large errors and GALE-CAST Model-W1 did better. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.
- **How it was produced:** Selection v3 Part 2: windows ranked by the number of (variable, date) cells that are reference comparison dates on which GALE-CAST Model-W1 was strictly closer than both baselines, then normalised margin, then reference comparison cells, then date. Chosen because the model did well.
- **How to read it:** Shading marks dates meeting the reference-error rule; a star marks a model comparison win. All four variables and all dates in the selected window are shown. Each date has its own next-day forecast; gaps indicate missing observations.
- **Actual finding:** GALE-CAST Model-W1 success cells (of 12): NAIA 3 of 6 reference comparison cells, GALE-CAST Model-W1+X1 outcomes Hit, False alarm, Correct negative; Sangley Point 4 of 6 reference comparison cells, GALE-CAST Model-W1+X1 outcomes Hit, Correct negative, Correct negative; Science Garden 4 of 6 reference comparison cells, GALE-CAST Model-W1+X1 outcomes Hit, Correct negative, Correct negative.
- **What it supports:** On specific dates when both references had large errors, GALE-CAST Model-W1 was the closest forecast for some variables.
- **Scope and context:** Chosen for GALE-CAST Model-W1's success; at two of the three stations the rainfall estimate was below the observation on the heaviest-rain day of the window; not a performance estimate (see PF-L, PF-M).
- **Use in the paper:** Chapter 4, same subsection (thesis and panel-review site). Caption: 'Figure 4.x. Selected validation window. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.'
- **Source:** panel-review PNG/SVG/CSV: docs/figures/paper/; source archive: _private/thesis_export/panel-v3-20261025T163824Z-20403a/; public counts: runs/panel-v3-20261025T163824Z-20403a/panel_v3_results.json.

### PF-P (panel review)

- **What this graph shows:** The Part 2 common window: all four variables at all three primary stations on the same three dates.
- **Purpose:** A network-wide view of a period when both references had large errors. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.
- **How it was produced:** Common-window rule of Part 2: dates in the cohort at all three stations, ranked by total GALE-CAST Model-W1 success cells (of 36).
- **How to read it:** One row per station, one column per variable; shading and stars as in PF-O.
- **Actual finding:** GALE-CAST Model-W1 success cells 10 of 36; reference comparison cells 21 of 36 (success cells by station: NAIA 3, Sangley Point 3, Science Garden 4).
- **What it supports:** During a multi-station disturbance, GALE-CAST Model-W1 was closer than both reference forecasts on a minority of the variable-station-dates.
- **Scope and context:** Chosen because the model did well; The rainfall estimates were below the heavy-rain observations at all three stations.
- **Use in the paper:** Chapter 4, same subsection (thesis and panel-review site). Caption: 'Figure 4.x. Selected common validation window. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.'
- **Source:** panel-review PNG/SVG/CSV: docs/figures/paper/; source archive: _private/thesis_export/panel-v3-20261025T163824Z-20403a/.

### PF-R (panel review)

- **What this graph shows:** Per station, three consecutive target dates that all qualify under selection v4: observed and forecast wind and MSLP with absolute errors, humidity and rainfall (not used to select), and the GALE-CAST Model-W1+X1 score and outcome.
- **Purpose:** Concrete dates for the panel where the model had lower error than persistence for wind and MSLP. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates. Dates selected because persistence's wind and MSLP errors were both larger than GALE-CAST Model-W1's.
- **How it was produced:** Selection v4 windows: three consecutive qualifying dates, ranked by cells (of 6) where GALE-CAST Model-W1 also beat climatology, then the normalised persistence margin, then date; two-date windows only if a station has no three-date window.
- **How to read it:** Shaded = qualifying date; ★ = GALE-CAST Model-W1 also closer than climatology. Each date is a separate next-day forecast.
- **Actual finding:** NAIA: 3-date window, GALE-CAST Model-W1 also beat climatology on 5 of 6 cells; Sangley Point: 3-date window, GALE-CAST Model-W1 also beat climatology on 5 of 6 cells; Science Garden: no window (no two consecutive qualifying dates). No common window qualifies at all three stations.
- **What it supports:** On these dates GALE-CAST Model-W1's wind and MSLP were closer than persistence's, and mostly closer than climatology's.
- **Scope and context:** Chosen for GALE-CAST Model-W1's success; Science Garden has no qualifying window; not a performance estimate (see PF-Q, PF-F).
- **Use in the paper:** Chapter 4, same subsection (thesis and panel-review site). Caption: 'Figure 4.x. Selected window comparing model and persistence wind and MSLP errors. Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates. Dates selected because persistence's wind and MSLP errors were both larger than GALE-CAST Model-W1's.'
- **Source:** panel-review PNG/SVG/CSV: docs/figures/paper/; source archive: _private/thesis_export/persist-v4-20261025T165748Z-3e854f/; public counts: runs/persist-v4-20261025T165748Z-3e854f/persistence_v4_results.json.
