# Case-selection amendment v4: dates where persistence was worse than W1 for both wind and MSLP (panel directive; Group E)

- **Recorded:** 2026-10-25, committed **before** the search code was written or run.
- **Relation to earlier work:** EVAL_SPEC_v1, amendment A2 and selections v1-v3, their runs and figures are unchanged.
- **Why (panel mandate):** the thesis panel noted that the persistence baseline ("tomorrow equals today") is the main reference that beats W1
  on average for wind and mean sea-level pressure (MSLP), and directed a search of the historical prediction records for target dates on
  which persistence's error is larger than W1's for **both** wind and MSLP. Climatology is not part of this filter (panel directive).
- **This is a favourable-error selection.** Dates are chosen *because* W1 beat persistence on them, so W1 beats persistence on them by
  construction. It shows that such dates exist and how often; it is not a performance estimate.
- **Label on every output:** "Selected validation example chosen to demonstrate baseline limitations as requested by the thesis panel;
  not representative of all historical dates. Dates selected because persistence's wind and MSLP errors were both larger than W1's."
- **Frozen model:** no model is run, retrained, re-exported or changed; W1 values are saved historical predictions.

## Prior exposure (disclosed)

The author had seen the overall Evidence A/B results (W1's wind and MSLP MAE larger than persistence's), the v1-v3 selected windows and
the v3 Part 1 results. No result of the rule below had been computed.

## Records

Evidence A website-scorecard rows, run `w-cohort-20261024T205646Z-6b7a96` (3,423 next-day cases, NAIA / Sangley Point / Science Garden,
target dates 2021-11-16 to 2024-12-30). W1 = neural-only output. Persistence = raw observation on the issue day. Truth = raw PAGASA
observation on the target date. A station-date is used only if observation, persistence and W1 exist for **both** wind and MSLP; nothing is
imputed or edited.

## Rule

A station-date **qualifies** when, strictly,
|persistence wind − observed wind| > |W1 wind − observed wind| **and** |persistence MSLP − observed MSLP| > |W1 MSLP − observed MSLP|.

Ties are not wins. Climatology, humidity and rainfall are reported for qualifying dates but are not used to select.

## Outputs of the search

1. **All qualifying station-dates (public aggregate):** number and share per station and pooled; MAE of W1, persistence and climatology for
   wind and MSLP on them (W1 < persistence holds by construction; climatology is an independent comparison); counts by calendar month (no
   exact dates).
2. **Windows (private):** three consecutive target dates *d−1, d, d+1* at one station on which **every** date qualifies. Ranked by the
   number of the three dates on which W1 also beats climatology for wind and MSLP (0-6 cells), then the total persistence margin
   Σ(|persistence error| − |W1 error|) with wind in m/s and MSLP in hPa divided by the station's training-period (2015-2020) 90th percentile
   of day-to-day change for that variable (the v3 `T_pers`), then earlier date. If no three-date window exists at a station, two-date windows
   are used and reported as such. **Common window:** three dates qualifying at all three stations, if any, ranked the same way.
3. Private figures with individual readings stay in `_private/thesis_export/` (PAGASA CADS-07 Rev.6, condition 4); public outputs carry no
   dates.
