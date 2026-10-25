# Model and data summary

## Deployed model GALE-CAST Model-W1

| Item | Value |
|---|---|
| File | `gale_cast_model_multioutput.keras`, SHA-256 `f2db5aa93226225405914094a0855ac725734a0e2c1a2331e3ba69a8fd9d14b0` (= `gale_cast_model_multioutput_w3.keras`, label "GALE-CAST Model-W1") |
| Provenance | branch `exp/precision-targeting`, `experiments/w1x1/_train_w3.py`; promoted to live in commit `1fd1ef9` (2026-09-18) |
| Architecture | dual-stream: `input_normal` (32 days × 32 features) → LSTM(64) → Dense(32); `input_anomaly` (32 × 4) → LSTM → additive attention over time steps → LSTM(32) → Dense(16); merged; heads `gale_prob` (sigmoid) and `weather_vars` (6 regression outputs); 40,872 parameters |
| Training | one `model.fit` on primary rows before 2020-10-15 + all Port Area rows + all supplementary rows; early stopping on the tuning year (`val_gale_prob_loss`, patience 12); no saved history or seed; no pre-training stage |
| Scoring procedure behind the website | `_w1_recall_floor.py`: pooled `scaled_weather` inputs, X1 = same-date mean over the three stations, threshold 0.601 |
| Live system | the dashboard tier uses wind/pressure rules, not the model score; the 24-step live endpoint fails on this 32-step model; displayed 2025+ values are simulated or imported PAGASA forecasts |

Implementation technologies around the model (web, API, database, hosting) are listed separately in `TECH_STACK.md`; they are not
evidence of forecast accuracy.

## Station groups

- **Primary (evaluated):** NAIA, Sangley Point, Science Garden.
- **Supplementary (training only):** Port Area (records to 2023-10-31) and 19 additional Luzon stations (`Training.csv`, 69,388 rows to
  2024-12-30). Described as *supplementary PAGASA observations, owner-confirmed*. No independent source verification has been done, and
  the earlier "SMOTE" reading of the filename has been withdrawn: SMOTE was used only in archived notebooks v2.6-v2.8.

## Actual split (primary stations)

| Partition | Dates | Rows | Study-label events | Event dates (episodes) | Pressure-only / wind-triggered |
|---|---|---|---|---|---|
| training | 2015-01-01 to 2020-10-14 | 6,342 | 51 | 30 (27) | 50 / 1 |
| tuning | 2020-10-15 to 2021-10-14 | 1,095 | 19 | 7 (6) | 19 / 0 |
| evaluation | 2021-10-15 to 2024-12-30 | 3,519 | 28 | 12 (7) | 28 / 0 |

Also used in training: Port Area (3,225 rows; 746 dated inside the evaluation period) and supplementary rows
(22,306 dated inside the evaluation period). Training total: 78,955 rows with 1,143 positive labels.

## Regression provenance (what the website's regression block is)

The website's wind row (MAE 0.5365 m/s, RMSE 0.7723, MASE 0.6782) is reproduced exactly (`reg-prov-20261024T205749Z-ce57af`) by:
1. GALE-CAST Model-W1 neural wind output (MAE 0.987);
2. linear + isotonic MOS per station × season, cross-fitted with an 8-fold `TimeSeriesSplit` **over the evaluation rows** (399 rows
   calibrated by a fit on later evaluation rows) → MAE 0.576;
3. a blend 0.55 × model + 0.45 × the processed wind observed **two days before the target**
   (script indexing), weight chosen by `TimeSeriesSplit` MAE on evaluation rows → MAE 0.5365.

Same-case issue-day persistence on the same truth: MAE 0.474, RMSE
0.800. MASE uses an in-sample lag-365 denominator (0.7912 m/s).
The website's wind-direction row (43.40°) comes from a separate direction-only model. Chapter 4's Table 4.5 (wind 2.04 km/h = 0.5655 m/s)
is the same pipeline run on the model **before** GALE-CAST Model-W1. None of these are neural GALE-CAST Model-W1 results.

GALE-CAST Model-W1's neural-only next-day errors on the website's cases (raw truth): wind MAE 0.987 m/s (persistence 0.474,
climatology 0.588); MSLP 1.94 hPa (persistence 0.85); humidity 8.73% (persistence
4.63); rainfall 6.74 mm (persistence 7.76, climatology 7.47).
