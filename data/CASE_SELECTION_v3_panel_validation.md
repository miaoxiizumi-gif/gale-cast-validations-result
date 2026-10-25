# Case-selection amendment v3: baseline-failure validation (panel request; Group D, separate from v1 and v2)

- **Recorded:** 2026-10-25, committed **before** the analysis code was written or run.
- **Relation to earlier work:** `EVAL_SPEC_v1`, amendment A2, `CASE_SELECTION_v1.md` and `CASE_SELECTION_v2_regression.md`, their runs and
  figures are unchanged. This is an additional, separately labelled analysis.
- **Why:** the thesis panel asked for validation on historical station dates where the simple reference forecasts (persistence,
  "tomorrow equals today", and climatology) perform poorly, to show where W1 adds value relative to them.
- **Disclosure (printed on every output):** "Selected validation example chosen to demonstrate baseline limitations as requested by the
  thesis panel; not representative of all historical dates."
- **Frozen model:** no model is run, retrained, re-exported or changed. Every W1 value is a saved historical prediction.

## Prior exposure (disclosed)

Before writing this file the author had seen: the overall Group A and Group B results (W1's neural wind, MSLP and humidity errors are
larger than persistence overall; rainfall MAE is lower than both baselines, RMSE not lower than climatology's); the v1 and v2 selected
windows (dates recorded privately). No per-date result of the rule below had been computed.

## Two parts, in this order

**Part 1 (the evaluation): every baseline-failure date, W1 scored on all of them.** Dates are chosen only by how badly the two baselines
did. W1's own error is **not** used to choose dates in Part 1. The result is reported whether it favours W1 or not.

**Part 2 (illustration, favourable by design): example windows** taken from Part 1's dates in which W1 was closer than both baselines.
Part 2 is chosen for W1's success and is labelled as such; it is not a performance estimate.

## Records

- **Primary (Evidence A):** the website-scorecard cohort, private rows of run `w-cohort-20261024T205646Z-6b7a96` (3,423 next-day cases,
  NAIA / Sangley Point / Science Garden, target dates 2021-11-16 to 2024-12-30). Variables: wind (m/s), MSLP (hPa), relative humidity (%),
  rainfall (mm). W1 = neural-only output (no MOS, no blend). Persistence = raw observation on the issue day (target − 1). Climatology =
  station × calendar-month mean of raw observations, 2015-01-01 to 2020-10-14. Truth = raw PAGASA observation on the target date.
- **Sensitivity (Evidence B, wind and events only):** training-consistent benchmark rows of run `b-benchmark-20261023T162436Z-874640`
  (wind-eligible cases, target dates 2021-10-15 to 2024-12-31), its own W1, persistence and climatology columns.
- **Complete-data rule:** a (station, date, variable) cell is used only if the observation, persistence, climatology and W1 values all exist.
  No value is imputed, edited or replaced.

## Baseline-failure thresholds (training period only; W1 not involved)

For each station *s* and variable *v*, from raw observations 2015-01-01 to 2020-10-14 (consecutive calendar days only):
- `T_pers(s, v)` = 90th percentile of |obs(t) − obs(t−1)| (the error persistence would have made in training);
- `T_clim(s, v)` = 90th percentile of |obs(t) − training station × month mean| (the error climatology would have made in training).

A cell is a **baseline-failure date** for *v* when |persistence − obs| ≥ `T_pers` **and** |climatology − obs| ≥ `T_clim`, and both
errors are > 0. Since persistence error equals the observed day-to-day change, every such date is also a large observed change.

Sub-groups reported (not used to select): MSLP baseline-failure dates with a **fall** (obs(d) < obs(d−1)) — the "sharp pressure drop"
group; wind dates with a **rise**; rainfall dates with a **rise**.

Sensitivity: the same analysis at the 80th and 95th percentiles is reported next to the 90th.

## Part 1 metrics (all baseline-failure cells, per station and pooled)

- n; MAE and RMSE of W1, persistence, climatology; paired MAE differences W1 − persistence and W1 − climatology with 95 % paired circular
  block-bootstrap intervals over target dates (14-day blocks, 2,000 resamples, seed 20261025; `metrics.block_weights`), verdict
  "established" only if the interval excludes 0;
- share of cells on which W1 is strictly closer than **both** baselines;
- the same numbers on all complete cells and on the non-failure cells, so the reader sees the trade-off;
- **Conditioning control:** the mean of persistence and climatology (a forecast that needs no model). Conditioning on baseline failure
  favours any forecast that sits between the two baselines; if this control does as well as W1 on these dates, W1's edge there is a
  hedging effect, not evidence of skill. This control is reported, not used to select.

**Event transitions (classification).** Onset dates = study-label event on the target date and **no** event on the issue day. Event
persistence misses every onset by construction. Reported: number of onsets, hits by W1+X1 (≥ 0.601), by event persistence and by event
climatology (A2 threshold), per station, on Evidence A and Evidence B. False alarms of W1+X1 on non-event days are reported alongside.

## Part 2 selection (favourable illustration; deterministic)

Window = three consecutive target dates *d−1, d, d+1* at one primary station, all in the Evidence A cohort.
A **W1 success cell** = a baseline-failure cell (90th-percentile rule) on which |W1 − obs| < |persistence − obs| and |W1 − obs| <
|climatology − obs| (strict).
For each station, rank windows by:
1. number of W1 success cells over the four variables and three dates (0-12); a window with 0 is never selected;
2. total normalised margin: Σ over success cells of (smaller baseline |error| − W1 |error|) / `T_pers(s, v)`;
3. number of baseline-failure cells in the window;
4. earlier date.

**Common window:** three target dates in the cohort at all three stations, ranked by total success cells (0-36), then margin, then
baseline-failure cells, then earlier date; selected only if the total is at least 1.

Every variable, error and W1+X1 outcome in each selected window is shown, including cells where W1 was worse.

## Outputs

- **Public (aggregates only; no dates, no readings):** thresholds, counts, Part 1 metrics and intervals, onset counts, Part 2 success-cell
  counts; public figures of aggregate errors on baseline-failure dates.
- **Private (`_private/`):** the per-cell ledger, the selected dates and the Part 2 window figures, because they show individual PAGASA
  station-day readings (PAGASA CADS-07 Rev.6, condition 4).
