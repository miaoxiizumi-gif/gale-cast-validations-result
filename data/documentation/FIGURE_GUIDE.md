# Figure guide

Public figures are aggregates. Each is downloadable as PNG (300 DPI), SVG and the CSV of the plotted numbers, from
[`docs/figures/paper/`](../docs/figures/paper/) (site: https://miaoxiizumi-gif.github.io/gale-cast-validations-result/#figures). Figure run: `pf-20261024T210214Z-61902c`.

## Public paper figures

| Files | Evidence | Caption and interpretation | Source runs |
|---|---|---|---|
| `PF-A_website_confusion_matrix.png` / `PF-A_website_confusion_matrix.svg` / `PF-A_website_confusion_matrix.csv` | A | The GALE-CAST website's binary scorecard (validation_cm3.json), reproduced case by case: 24 hits, 4 misses, 9 false alarms, 3,386 correct negatives. Accuracy is dominated by correct negatives; the all-negative forecast scores 99.18%. | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-B_station_outcomes.png` / `PF-B_station_outcomes.svg` / `PF-B_station_outcomes.csv` | A | The same 3,423 cases split by primary station. Because X1 averages the three stations, a warning is issued for all three stations on the same date; station results are therefore not independent. | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-C_event_metrics_overall.png` / `PF-C_event_metrics_overall.svg` / `PF-C_event_metrics_overall.csv` | A+B | Precision, recall and F1 with 95% intervals. On both cohorts W1+X1 beats both event baselines on F1 (established). The level depends on the input construction: 24/28 hits with the website's procedure, fewer with training-consistent inputs. | `b-benchmark-20261023T162436Z-874640`, `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-D_event_metrics_by_station.png` / `PF-D_event_metrics_by_station.svg` / `PF-D_event_metrics_by_station.csv` | A | The PF-C comparison for each primary station. With 8-10 events per station the intervals are wide. | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-E_precision_recall_curves.png` / `PF-E_precision_recall_curves.svg` / `PF-E_precision_recall_curves.csv` | A | Curves traced from the 3,423 saved W1 scores (not reconstructed from a confusion matrix), with the historical 0.601 point marked. | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-F_wind_mae_rmse.png` / `PF-F_wind_mae_rmse.svg` / `PF-F_wind_mae_rmse.csv` | A | W1's neural wind output has larger MAE and RMSE than both baselines overall and at every station (established for MAE vs persistence everywhere). W1 does not show wind-forecast superiority. | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-F2_website_regression_provenance.png` / `PF-F2_website_regression_provenance.svg` / `PF-F2_website_regression_provenance.csv` | A | The website's wind MAE 0.5365 / RMSE 0.7723 / MASE 0.6782 are reproduced exactly only after two post-processing steps fitted on the evaluation period itself. W1's own wind output has MAE 0.987; issue-day persistence on the same cases has MAE 0.474. | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-F3_regression_variables_mae.png` / `PF-F3_regression_variables_mae.svg` / `PF-F3_regression_variables_mae.csv` | A | Each output in its own unit and panel. W1 has larger MAE than both baselines for wind, pressure and humidity. For rainfall W1's MAE is lower than both baselines (established), but its RMSE (17.1 mm) is above climatology's (16.1 mm) and it under-forecasts on average (bias -3.66 mm): a low forecast lowers MAE on skewed rainfall. | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |
| `PF-G_observed_vs_predicted.png` / `PF-G_observed_vs_predicted.svg` / `PF-G_observed_vs_predicted.csv` | A | Binned counts replace a scatter so that no individual station-day reading is published. Most wind forecasts sit at 2-3 m/s whatever was observed; humidity forecasts stay near 75-90%; pressure forecasts follow higher pressures but stay too high on low-pressure days; rainfall forecasts sit at 1-5 mm almost regardless of the observed amount (too wet on dry days, too dry on wet days). | `reg-prov-20261024T205749Z-ce57af`, `w-cohort-20261024T205646Z-6b7a96` |

Earlier evaluation figures F1-F8 (Group B benchmark and model variants) remain on the site and in `docs/figures/`.

## Selected case figures (private)

These plot individual PAGASA station-day readings. PAGASA's data terms (CADS-07 Rev.6, condition 4, as recorded in the source project)
forbid publishing station readings online and no permission was found, so they exist only in the private thesis-export folder and are
**not** publicly available. Selection run: `case-20261024T205908Z-bc687f`; criteria: `spec/CASE_SELECTION_v1.md`.

| Figure | Evidence | Content | Availability |
|---|---|---|---|
| PF-H (NAIA) | C (selected) | 3-day window around a pressure fall-triggered event; outcomes: Hit, Hit, Correct negative; event persistence on the event day: warning; 9 eligible candidates | private only |
| PF-H (Sangley Point) | C (selected) | 3-day window around a pressure fall-triggered event; outcomes: Correct negative, Hit, Correct negative; event persistence on the event day: no warning; 5 eligible candidates | private only |
| PF-H (Science Garden) | C (selected) | 3-day window around a pressure fall-triggered event; outcomes: Correct negative, Hit, Correct negative; event persistence on the event day: no warning; 8 eligible candidates | private only |
| PF-I (all three stations) | C (selected) | 3-day window around a date detected at all three stations | private only |

Every case figure carries the label: "Selected successful case; chosen retrospectively for illustration; not representative of all dates."
Each date shows a separate next-day forecast; the windows are not three-day-ahead forecasts.
