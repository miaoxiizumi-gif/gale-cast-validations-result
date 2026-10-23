# Handoff: GALE-CAST W1 evaluation `GCV-W1-v1`

Last updated: 2026-10-24.

## Where things are

| Item | Location |
|---|---|
| Evaluation workspace (this repo) | cloned next to the source checkout → `github.com/miaoxiizumi-gif/gale-cast-validations-result` |
| Source repository (read-only here) | the GALE-CAST project checkout at `1f2d5dd` (set `GALECAST_SRC`; default: sibling folder `VS CODE LIVE SHARE`); W1 provenance on branch `exp/precision-targeting` |
| Python | a venv with Python 3.11.9, tensorflow-cpu 2.16.1, Keras 3.13.2 (numpy 1.26.4, pandas 2.2.2, scikit-learn 1.7.2) |
| Private, unpublished | `_private/` (raw-derived row tables, daily plots, chapter text, copied W1-branch files, variant model copies) |

## Run order (from `eval/`)

`stage1_identity.py` → `stage2_partitions.py` → `stage2b_supplementary.py` → `cohort_a_legacy.py` → `benchmark.py` → `variants.py` →
`diag_inputs.py`, `diag_insample.py` (post-hoc, labelled) → `figures.py` → `build_site.py`.
Every script creates a new run directory. Never overwrite or delete a run; mark failures with `FAILED.txt`.

## Key results (details on the website)

- Identity verified (model, scalers, thresholds file; Space `main` `8ffbbb5`). The live 24-step endpoint fails, and the dashboard tier ignores the model probability.
- The legacy scorecard (24/28, PR-AUC 0.8302) reproduces exactly, but it uses pooled input scaling, unlike training, and its threshold rule was adopted after test scores were seen.
- Benchmark (3,520 identical cases): W1 wind MAE 1.021 m/s vs persistence 0.467 and climatology 0.584 (W1 worse, established). There are 27 events, all pressure falls; W1+X1 at 0.601 gives 16 hits, 8 false alarms, 11 misses. F1 is better than event persistence (established), and the probabilities are not calibrated.
- The scaling choice moves W1+X1 PR-AUC between 0.487 (training-consistent) and 0.824 (legacy). The mechanism is unresolved.

## Open items (owner decisions; not decided here)

1. A prospective test on 2025+ observations, the only clean test.
2. The provenance of `Training.csv` / `processed_luzon_supplementary`.
3. PAGASA wind metadata (statistic, averaging period, height).
4. Whether to fix the live endpoint (24 vs 32 steps) and the tier logic. These are production changes and were not made here.
5. Chapter revisions: apply the ledger, then rerun `build_site.py` with any updated `content.py`.

## Rules followed

No retraining, rescoring of production, database access, server start, or production edits. The specification was committed before scoring. Only aggregates are published.
