# Split design: documented facts and a present-day assessment

## Documented facts

- Primary-station cut-offs in the executed recipe (`_train_w3.py`): training dates before 2020-10-15; tuning 2020-10-15 to 2021-10-14
  (early stopping and threshold selection); evaluation from 2021-10-15. The code calls 2021-10-15 the "v12 canonical split". The date is
  already present in the repository's first commit (2026-07-26); earlier experiments used other cut-offs (2020-12-31 "Split B",
  2021-07-02 "Split C").
- **The exact calendar cutoff rationale was not preserved in the original experiment records.** No commit message, configuration comment or
  document states why these dates were chosen. No record shows that the panel approved this historical split.
- Port Area and supplementary rows were used for training regardless of date: 746 Port Area rows and
  22,306 supplementary rows are dated inside the evaluation period.
- The evaluation period was later used to compare W1 with other trained variants, to adopt X1 and to choose the threshold rule
  (0.601 adopted after the max-F1 rule's 0.62 had been scored on it). It is therefore not an independent test.

## Facts checked for this assessment

| Partition | Years | Rows | Events | Event dates | Episodes | Events by season |
|---|---|---|---|---|---|---|
| training | 5.79 | 6,342 | 51 | 30 | 27 | Dec-Feb (NE monsoon): 4; Jun-Aug (SW monsoon): 18; Mar-May (dry/hot): 2; Sep-Nov (late typhoon season): 27 |
| tuning | 1.0 | 1,095 | 19 | 7 | 6 | Mar-May (dry/hot): 1; Sep-Nov (late typhoon season): 18 |
| evaluation | 3.21 | 3,519 | 28 | 12 | 7 | Dec-Feb (NE monsoon): 3; Jun-Aug (SW monsoon): 4; Mar-May (dry/hot): 3; Sep-Nov (late typhoon season): 18 |

All three partitions contain all twelve calendar months. Episodes are runs of consecutive event dates (any station).

## Present-day assessment of the split's design

*This section is a retrospective assessment written on 2026-10-25. It is not the original documented reasoning.*

Design considerations supported by evidence:
- An LSTM needs ordered sequences, and each input window must precede its target. A chronological split respects this; a random split
  of overlapping 32-day windows would place near-duplicate windows on both sides.
- A 32-day window means each partition needs 32 days of earlier context; the evaluation cases start on 2021-11-16 for this reason.
- Multi-year training (5.79 years at the primary stations) exposes the model to several seasonal cycles.
- A separate one-year tuning block supports early stopping and threshold selection without using evaluation dates, and it covers every month once.

Weaknesses found:
- The tuning year holds only 19 events on 7 dates (6 episodes), 18 of them in
  September-November. A threshold chosen on so few episodes is fragile.
- The evaluation period's 28 events fall on 12 dates (7 episodes); events are not independent, so intervals are wide.
- Every evaluation-period event is a pressure fall; wind-triggered detection cannot be assessed on this split.
- Supplementary and Port Area records dated within the evaluation period, and the historical reuse of evaluation outcomes for selection,
  mean the split does not give an independent test.

These points explain aspects of the design. They do not establish why the October cut-offs were chosen, the architecture does not require
these exact dates, and good scores on the evaluation period do not prove the split valid. The only clean test available is a prospective
evaluation on observations from 2025 onward.
