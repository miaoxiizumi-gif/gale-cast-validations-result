# Case-selection criteria v1 (Group C: retrospectively selected illustrative case studies)

- **Recorded:** 2026-10-25, committed before the selection was run and before any case figure was drawn.
- **Disclosure of prior exposure:** before writing these criteria, the author of this file had seen the list of the 24
  Group A true positives (station, date, W1 raw score, X1 score). Completeness, neighbouring-day outcomes, observed values and
  errors had **not** been examined.
- **Label on every figure:** "Selected successful case; chosen retrospectively for illustration. Not representative of all dates."

## Purpose

To explain how W1 behaved around correctly detected study-label events. This is **not** a performance estimate. The overall
results (Groups A and B) remain the evidence of performance, including results unfavourable to W1.

## Candidate pool

The 24 true positives of the website scorecard: Cohort A rows with X1 ≥ 0.601 and label 1.

## Window

Three consecutive **target dates** at one station: *d−1*, *d* (the detected event) and *d+1*. Each date shows the separate
next-day (+1) forecast issued after the previous day's observations. This is **not** a +1/+2/+3-day forecast from one origin;
W1 has no archived multi-day forecasts.

## Eligibility (all required)

- **E1.** The station has Group A rows for *d−1*, *d* and *d+1*.
- **E2.** Raw observations of wind speed and MSLP exist (not missing) for *d−2*, *d−1*, *d* and *d+1*, so issue-day persistence,
  the pressure change and the label on every plotted date use observed values, not filled ones.
- **E3.** The study label recomputed from raw observations is 1 on *d*.

## Ranking (applied in this order; deterministic)

- **P1 (favourable criterion, disclosed).** The number of correct W1+X1 decisions in the window (0–3). Higher is preferred.
- **P2 (interpretability).** The larger raw 24-hour pressure fall on *d*. A wind-triggered event ranks first if one exists.
- **P3.** The earlier date.

**Not used for selection:** W1's wind or pressure error; any comparison of W1's error with persistence or climatology; event
persistence's outcome. These are reported in the figures, whatever they show.

## Outputs

- **A. One window per primary station** (NAIA, Sangley Point, Science Garden), chosen independently. A station's window may share
  its date with the common window. If no candidate passes E1–E3 at a station, the absence is reported; no other station or date
  is substituted.
- **B. One common window**: a date *d* that is a true positive at all three stations, with every station passing E1–E3. It is ranked
  by the sum of P1 over the stations, then by the smallest of the three pressure falls (larger preferred), then by date. If none
  qualifies, this is reported.
- **Ledger:** every candidate, its E1–E3 results and ranking keys are written to a private ledger (`_private/`), so the choice can
  be reproduced. Only the selected dates and the criteria are reported outside `_private/`.

## Public display

Case figures show individual PAGASA station-day readings. Publishing station readings online is not permitted under PAGASA's data
terms (CADS-07 Rev.6, condition 4, recorded in the source project), and no permission was found. The figures are therefore kept in
`_private/thesis_export/` for the printed thesis. The public site describes the protocol and the selected dates only.
