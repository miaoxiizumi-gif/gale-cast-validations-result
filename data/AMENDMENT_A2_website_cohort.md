# Amendment A2: website-scorecard cohort, matching baselines, regression provenance, paper figures

- **Recorded:** 2026-10-25 (Asia/Manila), committed **before** any of the analyses below were run.
- **Applies to:** evaluation `GCV-W1-v1` (`EVAL_SPEC_v1.md`). Nothing in the original specification, its runs or its scores is changed.
  This amendment adds analyses; it does not replace Cohort B.
- **Why:** the thesis panel asked for figures that explain the deployed W1's behaviour, including favourable examples.
  The website shows a historical scorecard (Cohort A cases) that is not the same cohort as the Cohort B benchmark.
  Comparing W1 with baselines on the website's own cases needs a declared procedure.

## 1. Three evidence groups (kept separate everywhere)

| Group | What | Cases |
|---|---|---|
| **A. Website historical scorecard** | the matrix shown by the GALE-CAST website (`validation_cm3.json`: TN 3386, FP 9, FN 4, TP 24, threshold 0.601) and new same-case baselines for it | the 3,423 Cohort A windows |
| **B. Training-consistent retrospective benchmark** | Cohort B as declared in `EVAL_SPEC_v1.md` (unchanged) | 3,520 event cases / 3,555 wind cases (from the existing run) |
| **C. Selected illustrative case studies** | three-day windows chosen retrospectively under `CASE_SELECTION_v1.md` | a few station-days; not a performance estimate |

## 2. Group A case identity (no new predictions substituted)

- The original W1-branch scripts saved only aggregate files. No original per-case prediction file exists.
- Case identity is taken from the separately identified reproduction run `a-legacy-20261023T162426Z-b5f446` (Cohort A, unchanged).
  It is checked against the **original** saved record `nine_fp_report.json` (branch `exp/precision-targeting`):
  all 9 false alarms and 4 misses must match by station, date and X1 score (|Δ| ≤ 1e-5), and the confusion matrix must equal 3386/9/4/24.
- To obtain the other five regression outputs (only wind was saved in that run), the same legacy procedure is re-run once
  in a new run directory (`w-cohort-*`). That run must reproduce the saved `prob`, `x1` and `wind_pred` of the Cohort A rows to
  |Δ| ≤ 1e-6, or it stops. It never overwrites an earlier run.

## 3. Group A label, timing and baselines

- **Timing.** The window holds processed rows *t−31…t*; the forecast is issued after day *t*; the target date is *d = t+1* (+1 day).
  This is checked for every row.
- **Label (as on the website).** `processed_weather.gale_flag(d) ≥ 1`, i.e. processed (forward-filled) wind(d) ≥ 10.8 m/s **or**
  processed pressure_drop(d) = MSLP(d−1) − MSLP(d) ≥ 3 hPa. Reported in three parts: wind-only, pressure-only, both.
  Its agreement with the same rule on raw, unimputed observations is reported.
- **Event persistence:** the label of the issue day, `gale_flag(t) ≥ 1` (known at issue time).
- **Event climatology:** frequency of the processed label for (station, calendar month of *d*), fitted on primary-station dates
  2015-01-02…2020-10-14. Its decision threshold is chosen on development dates 2020-10-15…2021-10-14 only (distinct values, max F1,
  ties → larger), the same rule as `EVAL_SPEC_v1.md` §4.
- **W1:** the historical scores and decisions: X1 ≥ 0.601 (primary, the website's) and raw ≥ 0.64 (documented). No threshold is changed.
- **Regression truth:** raw, unimputed observations of day *d* (wind m/s, MSLP hPa, relative humidity %, rainfall mm with the
  pipeline's trace rule −1 → 0.05 mm). Persistence = raw observation of day *t*; climatology = raw station × month mean over
  2015-01-01…2020-10-14. Cases where any of the three is missing are excluded **per variable**, and the common-case count is reported.
  A secondary table scores wind against processed (imputed) truth on all 3,423 cases, matching the website's truth source.
- **W1 regression output:** the neural-only `weather_vars` head under the legacy inputs, inverse-scaled with
  `scaler_y_regression_mo`, clamped as in the historical script (wind ≥ 0; humidity 0–100; MSLP 850–1050; rainfall log1p ≥ 0, then
  converted to mm with `expm1`).
- **Uncertainty:** paired circular block bootstrap over target dates as in `EVAL_SPEC_v1.md` §7 (14-day blocks, B = 2,000).

## 4. Regression provenance check (the website's regression block)

The website's regression numbers (for example wind MAE 0.5365 m/s, MASE 0.6782) come from `validate_model_multioutput.py`
at W1 commit `1fd1ef9`. Their wind step is reproduced from the CSV copies, for provenance only, as written in that file:
per-station, per-season (Jun–Nov / Dec–May) linear + isotonic MOS with an 8-fold `TimeSeriesSplit` over the evaluation rows,
then a model/lag-1 persistence blend whose weight is chosen by 5-fold `TimeSeriesSplit` MAE on the evaluation rows.
Whether this reproduces 0.5365 is reported either way. Same-case persistence on the same (processed) truth is reported beside it.
This check is **not** a W1 result and is never presented as one.

## 5. Figures

Paper figures PF-A … PF-G are aggregates and are published. Each is exported as PNG (≥ 300 DPI) and SVG with its source CSV.
Figures that plot individual station-day PAGASA readings (PF-H, PF-I) are written **only** to `_private/thesis_export/`, because
PAGASA's data terms (CADS-07 Rev.6, condition 4, as recorded in the source project) forbid publishing station readings online and
no permission for public display was found. Only their selection protocol and descriptions are published.
