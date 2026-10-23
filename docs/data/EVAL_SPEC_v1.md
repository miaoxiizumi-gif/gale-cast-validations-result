# Evaluation specification GCV-W1-v1 (declared before scoring)

- **Evaluation ID:** `GCV-W1-v1`
- **Declared:** 2026-10-24 (Asia/Manila). Committed to this repository **before** any Cohort A or Cohort B score was computed.
- **Scope:** retrospective, offline evaluation of the **frozen, deployed W1 model**. Nothing is retrained, fine-tuned or recalibrated, and no threshold is re-selected. The production files are not changed. No database is read or written.
- **Status of the period:** the evaluation dates (2021-10-15 to 2024-12-31) were already used historically to compare W1 with other variants, to adopt X1 and to choose the threshold-selection rule. Every score in this evaluation is therefore **retrospective and exploratory**. It is not an independent or untouched test.

Machine-readable copy: `EVAL_SPEC_v1.json`. If the two disagree, this Markdown file governs, and the disagreement is reported.

## 1. Frozen artifacts (SHA-256 of raw bytes)

| File (source repo `1f2d5dd`) | SHA-256 |
|---|---|
| `gale_cast_model_multioutput.keras` (= W1, `_w3`) | `f2db5aa93226225405914094a0855ac725734a0e2c1a2331e3ba69a8fd9d14b0` |
| `scaler_X_normal_mo.save` | `c6ea01cbc9724907703439d2f89e7bdc758a3e17ba05716ab819287f88dfab9a` |
| `scaler_X_anomaly_mo.save` | `d424175a99eeb9b10f106b2264ee9918ce1f374df29eb83b3b3a2a5820cef8f6` |
| `scaler_y_regression_mo.save` | `98dd17a012611d3fde29ac2a81daa784c74e02ed8de518a42885db33c04b9ec8` |
| `galecast_thresholds.json` | `476a5d0574a03ea4753fa395273da13832763de77582a585ce833a7723f3c13f` (LF: `a531fc53…`) |

Each run re-hashes these files and stops if any hash differs.

**Data:**
- `data/processed_weather.csv`: LF SHA-256 `6d5b7fb3…cf05b`.
- `data/scaled_weather.csv`: LF SHA-256 `271d1c35…3ee4`.
- Raw-equivalent `Normalized_Dataset(Sheet1).csv`: SHA-256 `f5b7bc02…6e167`. This file is private and never published.
- Assumption: the CSVs equal the Postgres tables that W1 historically read. This is **not proven**, because no database was accessed.

## 2. Cohorts

### Cohort A: legacy reproduction

This cohort reproduces the historical scoring procedure in `exp/precision-targeting:experiments/w1x1/_w1_recall_floor.py`, as written. Its purpose is to establish whether the saved counts can be reproduced. It is **not** the benchmark.

**TEST construction:**
- Rows: `scaled_weather` for the three primary stations, dated 2021-10-15 to 2024-12-31. Join `processed_weather` for `humidity_lag1`, `humidity_lag2`, `humidity_7day_avg` and `target_gale`.
- Cross-station columns: computed from these three stations only, so the Port Area columns are 0.
- Windows: strict, 32 days, per station, built inside the TEST pull.
- Label: `processed_weather.target_gale ≥ 1` on the window's last row, which is the class of the next day.
- Score date: the row after the window.

**TUNE construction:** permissive. The pull starts 40 days before 2020-10-15, and the label date is the window's last row, within 2020-10-15 to 2021-10-14.

**Scores:**
- W1 raw `gale_prob`.
- X1 = the same-date mean of `gale_prob` over the three stations.
- Decision rule: `score ≥ threshold`.

**Reproduction targets** (from `THRESHOLD_CONFIG.md`, `precision_floor_w3.json`, `variant_score_w3*.json`):
- TEST: 3,423 windows and 28 positives.
- PR-AUC: raw 0.7278, X1 0.8302. TUNE PR-AUC: raw 0.9062, X1 0.9258.
- X1 at 0.601: TEST TN 3386, FP 9, FN 4, TP 24. TUNE TN 1070, FP 3, FN 1, TP 18.
- Raw at 0.64 and X1 at 0.62: TEST TN 3388, FP 7, FN 8, TP 20.

**Tolerance:** counts must match exactly. PR-AUC must match within 0.001.

**Rule check:** the documented R-FP12, R-FP10 and R-REC85 rules are re-applied to the TUNE scores. This only verifies that they return 0.601. It is not a new selection.

**Not reproduced:** the legacy regression metrics (wind MAE 0.5365, etc.). They include MOS, persistence blending and RF/kNN post-processing fitted inside the evaluation period (`validate_model_multioutput.py`). Cohort A reports the neural-only next-day wind error on its windows instead, and labels it as such.

### Cohort B: benchmark cohort (primary)

- **Stations:** NAIA, Sangley Point, Science Garden. Port Area and the supplementary stations are excluded from every score.
- **Forecast timing:** the forecast is issued after the daily observation of day *t* is complete. The target is day *t+1* (next day, +1). Target dates run from **2021-10-15 to 2024-12-31**.
- **Input construction, primary (S-TRAIN, "training-consistent"):**
  - Take `processed_weather` rows *t−31…t* of the station (32 consecutive calendar days; any gap makes the case ineligible).
  - Cross-station columns are computed from all four real stations, exactly as in `_train_w3.py` (lines 166-179). After Port Area's records end, its columns are 0.0, as the training code's fill rule gives.
  - Scaling uses the deployed per-station scalers `scaler_X_normal_mo` and `scaler_X_anomaly_mo`. The other 20 normal features pass through unscaled, as in training.
  - No recency weighting is applied, and windows are 32 steps.
  - This is a **new retrospective procedure**. It differs from the legacy scoring, which used pooled `scaled_weather` inputs, and from the deployed app, which uses 24 steps with recency weights and fails on this model.
- **Input construction, declared sensitivity (S-LEGACY):** the same cases, but inputs are built as in Cohort A (pooled `scaled_weather`, three-station cross-station columns).
- **Outputs:**
  - `p_raw` = `gale_prob`.
  - `p_X1` = the mean of `p_raw` over the three stations for the same target date. All three must be available.
  - `wind_W1` = `scaler_y_regression_mo.inverse_transform(weather_vars)[:,0]`, clipped at ≥ 0, in m/s.
  - These are **neural-only** outputs, with no post-processing.
- **Truth:** raw observations with sentinels set to missing and **no imputation**.
  - Wind: `wind_obs(d)`, the recorded daily wind speed in m/s. The statistic, averaging period and height are undocumented.
  - Study event label: `E(d) = 1` if `wind(d) ≥ 10.8` **or** `MSLP(d−1) − MSLP(d) ≥ 3.0 hPa`. `E(d)` is determinable only when `wind(d)`, `MSLP(d)` and `MSLP(d−1)` are all present.
  - The label is decomposed into: pressure-fall only, wind only, and both.
  - Confirmed gale-force wind (`wind(d) ≥ 17.2`) is counted separately.
- **Eligibility, wind cohort:** the W1 input window is available, and `wind_obs(d)` and `wind_obs(t)` are both present. The same cases are used for W1, persistence and climatology.
- **Eligibility, event cohort:** the W1 window is available for all three stations on date *d*, `E(d)` is determinable, and `E(t)` is determinable. The same cases are used for W1 raw, W1+X1, event persistence and event climatology.
- **Imputed inputs:** the inputs keep the causal forward-fill of `process_weather.py`. The number of cases whose window contains at least one imputed raw value is reported. A declared sensitivity analysis (S-NOIMPUTE) removes those cases.

## 3. Baselines

| ID | Definition | Fitted on |
|---|---|---|
| `wind_persistence` | `wind_obs(t)` (latest observed wind) | nothing |
| `wind_climatology` | mean raw wind for (station, calendar month of *d*) | raw primary-station records dated 2015-01-01 … 2020-10-14 (W1's primary-station training period) |
| `event_persistence` | `E(t)` (latest observable event label) | nothing |
| `event_climatology` | frequency of `E` for (station, month of *d*) | target dates 2015-01-02 … 2020-10-14, primary stations, determinable `E` only |

## 4. Thresholds (all frozen; none chosen on Cohort B outcomes)

| Procedure | Threshold | Source | Note |
|---|---|---|---|
| W1 raw, station level | 0.64 | `variant_score_w3.json`: max-F1 on TUNE (0.01 grid, largest among ties) | the originally declared rule |
| W1+X1 (primary) | 0.601 | `THRESHOLD_CONFIG.md`, R-FP12/R-FP10/R-REC85 on TUNE | these rules were introduced after the max-F1 X1 result (0.62) had been scored on TEST; the R-FP rules also scale by the TEST negative count |
| W1+X1 (secondary) | 0.62 | `variant_score_w3_x1.json`: max-F1 on TUNE | the originally declared rule |
| Event climatology | chosen here on the **development period only** (target dates 2020-10-15 … 2021-10-14, primary stations): the distinct climatology value maximising F1 (`≥`, ties → larger) | this specification | if the best development F1 is 0, no confusion matrix is reported, only probabilistic scores |
| Event persistence | none (binary) | | |

## 5. Horizons

Only **+1 day** is evaluated. W1 is a direct next-day model. Its regression head outputs 6 of the 36 input variables, so a two- or three-day forecast would need a new recursive procedure that invents the missing 30 inputs, including cross-station lags. **No +2 or +3 day results are produced.** This is reported as a limitation.

## 6. Metrics

- **Wind:** MAE, RMSE and mean signed bias (forecast − observed) in m/s, with *n*, per station and pooled. Paired differences in MAE and RMSE (W1 − baseline). The descriptive skill `1 − MAE_W1 / MAE_ref`.
- **Events:**
  - TP, FN, FP, TN; accuracy, precision, recall, F1; prevalence, and the all-negative accuracy `1 − prevalence`.
  - For probabilistic scores (W1 raw, W1+X1, event climatology): PR-AUC (average precision), Brier score, and Brier skill score against event climatology.
  - W1's probabilities come from a model trained with focal loss, class weights and oversampling, so they are **not calibrated** probabilities. Brier results are reported with that caveat.
- **Undefined ratios** (zero denominator) are reported as undefined, never as 0 or 1.

## 7. Uncertainty

- **Method:** paired circular block bootstrap over target dates.
  - Sorted unique target dates are resampled in circular blocks of **14 days**.
  - All stations of a resampled date travel together, which preserves cross-station dependence.
  - **B = 2,000**, seed `20261024`, percentile 95% intervals.
- **Undefined resamples:** for event ratios, resamples with an undefined value are dropped and counted.
- **Wording:** a difference is "established" only if its 95% interval excludes 0. Otherwise it is reported as "no established difference", never as "equal".
- **Limitations, reported:**
  - The block length is a judgement call, and longer-range dependence (for example the monsoon season) is not fully captured.
  - With about 20-30 events, event intervals are wide.

## 8. Declared breakdowns and sensitivities (all reported, none used to choose anything)

By station; by target-date year (2021 is partial: Oct 15 to Dec 31); S-LEGACY inputs; S-NOIMPUTE.

## 9. Figures

1. Partition and case-count tables.
2. Wind MAE/RMSE by station (one horizon only, +1).
3. Observed versus predicted wind:
   - **public:** monthly means of observed wind, W1, persistence and climatology per station over the **whole** period, plus a binned observed-versus-predicted count table;
   - **private only:** daily series for the whole period.
   - No dates are selected.
4. Event timelines: **public** monthly counts of hits, misses and false alarms per station; the **private** version has exact dates. Monthly totals must equal the confusion-matrix totals.
5. Binary confusion matrices with TN.
6. Event benchmark comparison.
7. Learning curves: **not drawn**. No W1 training history exists, and learning curves are never reconstructed from final scores.

## 10. Model variants (Stage 7)

Existing frozen variants on `exp/precision-targeting` are re-run for inference only, on the Cohort B event and wind cases, with each variant's own scalers (S-TRAIN construction) and its own documented TUNE max-F1 threshold:

| Variant | Threshold |
|---|---|
| v12 | 0.57 |
| v11 | 0.6614 (early-stopped on the TEST period: contaminated) |
| v13 | 0.53 (Split B) |
| v14 | 0.53 (Split C) |
| W2 (`_w6`) | 0.58 |
| W3 (`_w10`) | 0.56 |
| F1 | 0.45 |
| F2 | 0.36 |

- **Shape check:** a variant whose input shape differs from (32×32, 32×4) is not scored.
- **x1f and x2f are not scored:** their extra input features are not recorded.
- **No variant is selected** by this evaluation. The comparison is descriptive.

## 11. Run discipline

- **Run directories:** every execution writes a new `runs/<stage>-<UTC>-<hex>` directory with a manifest (code hashes, artifact hashes, environment). Failed runs are kept and marked `FAILED.txt`.
- **Changes after scoring:** if this specification is changed after any score is seen, the change is recorded as an amendment with its date and reason, and both versions are kept.
- **Public versus private outputs:** row-level predictions and observations stay in `_private/`, which is git-ignored. Only aggregates are published.

## Amendment A1 (2026-10-24, after Cohort A, the Cohort B benchmark and two diagnostics were run)

**What changed.** §10 (variants) adds a second input construction: the variants are also scored under **S-LEGACY** (pooled `scaled_weather` inputs), alongside S-TRAIN. Nothing else changes. The primary construction remains S-TRAIN for W1 and for the variants. No threshold, case, metric or baseline changes.

**Why.**
- The declared S-LEGACY sensitivity for W1 differed sharply from S-TRAIN on events (X1 PR-AUC 0.824 vs 0.487 on identical cases).
- A post-hoc diagnostic (`runs/diag-inputs-*`) traced the whole difference to input scaling. Cross-station columns and flags had no effect.
- The historical variant thresholds were all selected under pooled inputs.
- Scoring every variant under both constructions avoids presenting only the construction that suits one model.

**This amendment selects nothing.** The two post-hoc diagnostics (`diag_inputs.py`, `diag_insample.py`) are labelled as such and are not part of the declared evaluation.
