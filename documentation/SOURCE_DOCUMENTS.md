# Source documents

Reviewed 2026-10-25. Paths are relative to their repository. Nothing below is copied wholesale into this public repository; public files
contain summaries.

## GALE-CAST source repository (private)

| Document | Branch @ commit | Status |
|---|---|---|
| `docs/project/README.md`, `PRD.md`, `Architecture.md`, `Architecture-essentials.md`, `ORGANIZATION_REVIEW.md`, `TOOLING.md` | `docs/project-home` @ `e0280de` (contains `aac1006`) | local branch, not pushed (checked 2026-10-25) |
| `docs/project/FILE_GUIDE.md` | `docs/project-home` @ `e0280de` | local, not pushed |
| `CODEX_HANDOFF.md`, `docs/PROJECT_STRUCTURE.md`, `docs/MODEL_REGISTRY.md`, `docs/data/DATA_SOURCES.md` | `docs/project-home` @ `e0280de` | local, not pushed |
| `docs/validation/AUDIT.md`, `HANDOFF.md`, `W1PANEL.md`, `W1STATION.md`, `PHASE4_WIND.md` | `docs/project-home` @ `e0280de` | validation handoffs and audit corrections |
| `experiments/w1x1/_train_w3.py`, `_w1_recall_floor.py`, `_nine_fp_analysis.py`, `THRESHOLD_CONFIG.md`, `nine_fp_report.json`, `w1_recall_floor_report.json` | `exp/precision-targeting` | W1 recipe, historical scoring and its saved case records |
| `validate_model_multioutput.py`, `validation_cm3.json` | `exp/precision-targeting` @ `1fd1ef9`; `84d9ae3` (website sync) | source of the website scorecard and regression block |
| `process_weather.py` | `backend-pagasa-privacy` @ `1f2d5dd` | label construction |
| Commit `1f2d5dd` message | `backend-pagasa-privacy` | records PAGASA data terms CADS-07 Rev.6 condition 4 (no online publication of station readings) |

## Thesis chapters (owner's PC; not published)

| File | SHA-256 (first 16) | Date |
|---|---|---|
| `Downloads/GALE-CAST_PAPERS_CHAPTERS/Chapter-1.pdf` | `143fa4c0f879e11e` | 2026-10-23 |
| `…/Chapter-2.pdf` | `afd6175d8c93a870` | 2026-10-23 |
| `…/Chapter-3.pdf` | `91580eee1b7e8475` | 2026-10-23 |
| `…/Chapter-4.pdf` | `5f3b58105c1f8ee8` | 2026-10-23 |
| `…/Chapter-5.pdf` | `e28ef32275b43fd7` | 2026-10-23 |

The hashes match those recorded in `docs/project/PRD.md` §0, so these are the same versions reviewed by the documentation work. No editable
(.docx) source was found.

## External references

See `EVALUATION_METHOD.md` § References (each read from the primary source on 2026-10-25).

## Implementation-stack supplement (2026-10-25)

`TECH_STACK.md` reviews the application at GALE-CAST commit `bb056a9` (`requirements.txt`, `requirements-dev.txt`, `Dockerfile`, `app.py`,
`dashboard.html`, `static/sw.js`, `hosting/vercel.json`, `docker/db-init/schema.sql`, `.github/workflows/tests.yml`) together with
`docs/PROJECT_STRUCTURE.md` and `docs/handoff/DEPLOYMENT_AND_GITHUB.md`. It was first compiled by Tinenen-cs (commit `8b32465`) and verified
line by line on the same date. It is a separate implementation inventory; it does not change or re-execute the W1 evaluation, and no live
package inventory or private case values were used for it.

## Selection amendments

`spec/CASE_SELECTION_v1.md` (classification case studies) and `spec/CASE_SELECTION_v2_regression.md` (favourable regression case), each
committed before its search.
