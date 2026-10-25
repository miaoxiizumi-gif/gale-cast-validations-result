# Evaluation method

**Name used in the paper:** *Retrospective forecast verification with persistence and climatology benchmarking.*
The three-day examples are *retrospectively selected illustrative case studies*.

## What each term means

| Term | Meaning here | Is it cross-validation? |
|---|---|---|
| Chronological partitioning | How the primary-station records were divided: training (to 2020-10-14), tuning (2020-10-15 to 2021-10-14), evaluation (from 2021-10-15). | No. It is one split. |
| Retrospective verification | Running the frozen model on past dates and checking each next-day forecast against what was recorded. | No. |
| Baseline benchmarking | Scoring persistence and climatology on exactly the same cases and comparing. | No. |
| Selected case studies | A few dates chosen to explain behaviour, labelled as selected. | No, and not a performance estimate. |

No k-fold, rolling-origin or walk-forward cross-validation of the network was executed. Replaying a frozen model one day at a time over
a past period is repeated next-day verification, not cross-validation. The only `TimeSeriesSplit` in the project fitted post-processing
on evaluation-period outcomes (see `MODEL_AND_DATA_SUMMARY.md`, regression provenance).

## Three evidence groups (kept separate)

| Group | Cases | Inputs | Truth | Purpose |
|---|---|---|---|---|
| **A. Website historical scorecard** | the website's 3,423 next-day windows (1,141 per primary station; target dates 2021-11-16 to 2024-12-30) | historical scoring procedure: pooled `scaled_weather` inputs, 32-day windows | processed (forward-filled) label, as on the website; raw observations for regression | reproduce and explain what the website shows; add same-case baselines |
| **B. Training-consistent benchmark** | 3,520 event cases / 3,520 wind cases, target dates 2021-10-15 to 2024-12-31 | per-station scalers as in training | raw, unimputed observations | the declared benchmark of `spec/EVAL_SPEC_v1.md` |
| **D. Baseline-failure validation (panel request)** | every Group A station-date on which both persistence and climatology failed (training-period 90th-percentile rule, `CASE_SELECTION_v3_panel_validation.md`) and every event onset; then favourable example windows | as A (saved rows; no model run); wind and onsets also on B | raw observations | show where the reference forecasts fail and how W1 does there; examples not representative |
| **E. Persistence-worse dates (panel directive)** | station-dates on which persistence's wind AND MSLP errors were both larger than W1's (`CASE_SELECTION_v4_persistence_override.md`); favourable-error selection | as A (saved rows; no model run) | raw observations | show that and how often such dates occur; W1 < persistence there by construction |
| **C. Selected illustrative case studies** | set 1 (`CASE_SELECTION_v1.md`): 3 station windows + 1 common window around detected events; set 2 (`CASE_SELECTION_v2_regression.md`): 3 station windows + 1 common window with relatively high wind and favourable W1 wind error (favourable-error selection, disclosed) | as A (saved rows; no model run) | raw observations | explanation only; not representative |

### Selected illustrative case studies: what the two sets show

- **Set 1 (classification behaviour):** W1+X1 warned correctly on every day of the selected windows, and every event was a pressure fall.
  This is a classification success, not a regression success: W1's wind error was smaller than both baselines on only 3 of the 9
  station-days.
- **Set 2 (favourable regression example, requested by the panel):** chosen *because* W1's wind error was smaller than both baselines.
  Its rule was recorded before the search (relatively higher wind = observed wind ≥ the station's 2015-2020 90th percentile on at least one
  day). Results by station are in `FIGURE_GUIDE.md` (PF-J, PF-K). The pressure forecast was the closest on few of these days.
- Neither set establishes general superiority; the overall comparisons (Evidence A and B) do.

### Baseline-failure validation (Evidence D, panel request)

*Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates.*

The panel asked for historical dates on which persistence and climatology perform poorly. `spec/CASE_SELECTION_v3_panel_validation.md`
(committed before the analysis) defines them **without using W1**: a station-date is a *baseline-failure date* for a variable when the
persistence error is at least the station's 2015-2020 90th percentile of day-to-day change **and** the climatology error is at least the
90th percentile of deviation from the station × month mean. W1 is then scored on **every** such date (Part 1); favourable example windows
are picked only afterwards (Part 2, private figures). A no-model control (the average of the two baselines) shows how much of any advantage
on these dates a simple hedge also gets, because choosing dates by baseline error favours any forecast that does not copy a baseline.

| Variable (pooled) | Baseline-failure dates | MAE W1 / persistence / climatology / control | W1 − persistence | W1 − climatology | W1 − control |
|---|---|---|---|---|---|
| wind | 253 | 1.69 / 1.43 / 1.76 / 1.49 | established: positive | no established difference | established: positive |
| mslp | 91 | 3.98 / 3.32 / 5.52 / 3.64 | no established difference | established: negative | no established difference |
| humidity | 114 | 10.83 / 13.44 / 14.58 / 13.31 | established: negative | established: negative | established: negative |
| rainfall | 191 | 51.13 / 46.71 / 45.46 / 44.94 | established: positive | established: positive | established: positive |

"established: negative" = W1's error is smaller and the 95% interval excludes zero; "positive" = W1's error is larger. Event onsets (no
event on the issue day, an event on the target day): Evidence A 21 onsets, W1+X1 warned of 17
(9 false alarms on all non-event days), event persistence 0, event climatology 0;
Evidence B 21 onsets, W1+X1 11 (8 false alarms), event climatology 7
(317 false alarms).

Reading: where the references fail, W1's clearest advantage is **warning of pressure-fall onsets**. For numerical forecasts the advantage
is limited to humidity (helped by W1's high humidity bias, since these dates are mostly humidity rises) and to MSLP against climatology
only; for wind (except Science Garden, again a bias effect) and rainfall W1 is not better on these dates. Per-station detail:
`FIGURE_GUIDE.md` (PF-L to PF-P).

**Panel directive on PF-L (2026-10-25):** PF-L's rainfall panel shows all complete dates only (n = 3,407; MAE W1
6.74, persistence 7.76, climatology 7.47 mm). The panel is locked: the site build
fails if the plotted values differ from `spec/FROZEN_PF-L_rainfall.json`. The baseline-failure rainfall result is still computed and
reported (inside the panel, in PF-M, in the CSV and in the table above). The humidity panel keeps its baseline-failure values under their
correct label and sample size (n = 114); a request to relabel them "All complete dates (n = 3,421)" was not applied,
because those values come from 114 station-dates, not 3,421 (on all dates W1's humidity MAE is larger than persistence's).

### Dates where persistence was worse than W1 for wind and MSLP (Evidence E, panel directive)

*Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel; not representative of all historical dates. Dates selected because persistence's wind and MSLP errors were both larger than W1's.*

The panel noted that persistence is the reference that beats W1 on average for wind and MSLP, and directed a search for target dates on
which persistence's error was larger than W1's for **both** (climatology not part of the filter). `spec/CASE_SELECTION_v4_persistence_override.md`
was committed before the search. 258 of 3,421 complete station-dates qualify (7.5%; NAIA 115,
Sangley Point 115, Science Garden 28). On them, wind MAE is W1 0.59 vs persistence 1.20
and climatology 0.65 m/s; MSLP W1 0.63 vs 1.33 / 1.75 hPa; W1 also beat climatology
for both variables on 116 of them. W1 < persistence holds on these dates **by construction**. On all
3,421 dates persistence remains better (wind 0.47 vs W1 0.99 m/s; MSLP 0.85
vs 1.94 hPa). Windows (private, PF-R): NAIA: 3-date window; W1 also beat climatology on 5 of 6 cells; Sangley Point: 3-date window; W1 also beat climatology on 5 of 6 cells; Science Garden:
no window (no two consecutive qualifying dates). No common window qualifies at all three stations.

Group A's case identity was recovered without regenerating predictions: the saved reproduction rows (`a-legacy-20261023T162426Z-b5f446`)
match the original W1-branch record `nine_fp_report.json` for all 9 false alarms and 4 misses (station, date and score), and the matrix is
TN 3386, FP 9, FN 4, TP 24. A single re-run (`w-cohort-20261024T205646Z-6b7a96`) recovered the other regression outputs and reproduced the saved scores within
3e-8.

## Timing

Forecasts are issued after the daily observation of day *t* is complete, from the 32 days *t−31…t*; the target is day *t+1*. Every case is a
**next-day (+1 day)** forecast. W1 has no archived multi-day forecasts, so no +2 or +3 day skill is claimed. The three-day case windows are
three consecutive target dates, each with its own next-day forecast.

## Label

Study label (positive): wind ≥ 10.8 m/s **or** a same-station 24-hour MSLP fall ≥ 3 hPa. Pressure-triggered positives count as events.
In Group A all 28 positives are pressure falls (28 pressure-only, 0 wind-triggered); no day
reached 10.8 m/s and none reached the gale-force threshold of 17.2 m/s. The study label is therefore distinct from independently observed
gale-force wind.

## Baselines (never built from target-day observations)

| Baseline | Definition | Fitted on |
|---|---|---|
| Wind / pressure / humidity / rainfall persistence | the raw observation of the issue day *t* | nothing |
| Climatology (regression) | station × calendar-month mean of raw observations | 2015-01-01 to 2020-10-14 (W1's primary training period) |
| Event persistence | the study label of the issue day *t* | nothing |
| Event climatology | station × month frequency of the label | 2015-01-02 to 2020-10-14; decision threshold 0.0355 chosen by maximum F1 on the tuning year only |

W1's thresholds are unchanged: X1 ≥ 0.601 (website) and raw ≥ 0.64 (documented).

## Metrics and how to read them

- **MAE / RMSE:** lower means smaller numerical error *on the matching cases*. RMSE weights large errors more.
- **Mean signed error (bias):** forecast minus observed. It shows systematic over- or under-forecasting, and positive and negative errors can
  cancel, so a small bias does not mean small errors.
- **Better average error does not mean better event detection.** MAE is dominated by ordinary days; events here are pressure falls.
- **MASE:** error divided by an in-sample naïve error from training data. Below one does not prove a win against a separately computed
  same-case baseline (Hyndman & Koehler, 2006).
- **Precision, recall, F1, PR-AUC:** reported with all four confusion-matrix cells. Accuracy is shown with the all-negative reference.
- **Uncertainty:** paired circular block bootstrap over target dates (14-day blocks, 2,000 resamples). "Established" means the 95% interval
  excludes zero.
- **Selected dates cannot establish general forecasting superiority.** Conditioning on baseline failure (Evidence D) is a stratified
  view of the same cases, not a new test, and it favours forecasts that do not copy a baseline.

## Why persistence and climatology

Persistence ("tomorrow = today") and climatology (the usual value for the station and month) need no model, so a forecast system must beat
them to show added value (Rasp et al., 2020). They are computed here on the identical cases used for W1.

## References

- Rasp, S., Dueben, P. D., Scher, S., Weyn, J. A., Mouatadid, S., & Thuerey, N. (2020). WeatherBench: A benchmark data set for data-driven weather forecasting. *Journal of Advances in Modeling Earth Systems*, 12(11), e2020MS002203. https://doi.org/10.1029/2020MS002203  
  *Use:* Defines a persistence forecast ("the fields at initialization time are used as forecasts") and climatologies computed from the training period, and states that "to be useful, a forecast system needs to beat the weekly climatology and the persistence forecast" (arXiv:2002.00469v3, read 2026-10-25). Used here for why persistence and training-period climatology are reference forecasts. It concerns gridded global forecasts; it does not validate GALE-CAST's architecture or its split dates.
- Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting*, 22(4), 679-688. https://doi.org/10.1016/j.ijforecast.2006.03.001  
  *Use:* Defines scaled errors and MASE: "A scaled error is less than one if it arises from a better forecast than the average one-step naïve forecast computed in-sample" (author preprint, read 2026-10-25). Used here to explain why MASE < 1 against an in-sample denominator does not establish a win against a same-case test baseline.
