# Case-selection amendment v2: favourable regression case (Group C, separate from v1)

- **Recorded:** 2026-10-25, committed **before** the search below was run.
- **Relation to v1:** `CASE_SELECTION_v1.md`, its selection run and its figures are unchanged. This is an additional, separately labelled
  selection, made because the thesis panel asked for an example with relatively stronger observed weather and favourable numerical
  (regression) performance.
- **Label on every output:** "Selected favourable example, chosen retrospectively for illustration; not representative of all dates.
  Chosen because W1's numerical wind error was smaller than both baselines (favourable-error selection)."

## Prior exposure (disclosed)

Before writing this file the author had seen: the overall Group A results (W1's wind MAE is larger than persistence and climatology at every
station); the day-by-day values of the three set-1 windows (one station-window had observed wind up to 7 m/s with W1 wind error smaller than both baselines on two of its three dates; the other two windows had W1 wind beating both baselines on at most one date). Their dates are recorded privately, not here. No other window had been examined.

## Candidate data

- **Records:** the website-scorecard cohort (Group A), private rows of run `w-cohort-20261024T205646Z-6b7a96`. W1 values are the saved
  historical reproduction (wind identical to `a-legacy-20261023T162426Z-b5f446` within 2e-7 m/s; other outputs from the same frozen model and
  inputs). No model is run.
- **Allowed dates:** any three consecutive target dates *d−1, d, d+1* at one primary station (NAIA, Sangley Point, Science Garden) that are all
  in the cohort (target dates 2021-11-16 to 2024-12-30).
- **Complete data (all required):** raw observations of wind (m/s), MSLP (hPa), relative humidity (%) and rainfall (mm) on *d−2, d−1, d, d+1*
  at that station, so every target date has an observation, a persistence value and a climatology value for all four variables.
- **Forecasts compared:** W1 neural-only output (no MOS or blending); persistence = raw observation of the issue day; climatology = station ×
  calendar-month mean of raw observations, 2015-01-01 to 2020-10-14 (as in amendment A2).

## Definitions

- **Relatively higher wind:** at least one of the three target dates has observed wind ≥ that station's 90th percentile of raw daily wind over
  its training period (2015-01-01 to 2020-10-14). Percentiles are computed from training data only.
- **W1 wins on a date (wind):** |W1 − observed| < |persistence − observed| **and** |W1 − observed| < |climatology − observed| (strict; ties are
  not wins).
- **Event requirement, where available:** the window contains a correctly detected study-label event (W1+X1 ≥ 0.601 and label 1) at that
  station. Tier 1 = windows meeting it; if no Tier-1 window qualifies at a station, Tier 2 windows (no detected event) are used and reported as such.

## Selection objective (applied in order; deterministic)

For each station, among complete windows with relatively higher wind, Tier 1 before Tier 2:
1. **Most dates (0-3) on which W1 wins on wind** (favourable-error selection, disclosed). A window with 0 wins is never selected; if none has
   at least one win, "no qualifying window" is reported.
2. Larger total wind margin: Σ over the three dates of (smaller baseline |error| − W1 |error|).
3. Higher maximum observed wind in the window.
4. Earlier date.

**Common window (all three stations):** three target dates complete at all three stations, with relatively higher wind at one station or more;
ranked by total station-dates with a W1 wind win (0-9), then total margin, then the maximum of the stations' observed wind, then earlier date.
Selected only if the total is at least 1.

Pressure, humidity and rainfall are **reported** for every selected window (errors and wins) but are **not** used to select. Thresholds,
observations, labels, forecasts and exclusions are not changed.

## Outputs

- Private ledger of every candidate window (keys and results) and private figures in `_private/thesis_export/`, because they show individual
  PAGASA readings (PAGASA CADS-07 Rev.6, condition 4).
- Public: the rule, the number of qualifying windows, win counts by variable and tier; no dates or readings.
