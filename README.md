# GALE-CAST W1: retrospective evaluation and thesis handoff

Evaluation **`GCV-W1-v1`** of the frozen, deployed GALE-CAST model **W1**
(`gale_cast_model_multioutput.keras`, SHA-256 `f2db5aa9…9d14b0`). Nothing was retrained, recalibrated or changed in production.

- **Website:** https://miaoxiizumi-gif.github.io/gale-cast-validations-result/
- **Specification (declared before scoring):** [`spec/EVAL_SPEC_v1.md`](spec/EVAL_SPEC_v1.md) (commit `7870045`, plus amendment A1 at `6525d9d`)
- **Handoff notes:** [`HANDOFF.md`](HANDOFF.md)
- **Machine-readable outputs:** [`docs/data/`](docs/data) (claims, metrics, revision ledger, aggregate CSVs, `REPORT.md`)

## Layout

| Folder | Content |
|---|---|
| `spec/` | Dated evaluation specification (Markdown + JSON) |
| `eval/` | Evaluation scripts (read-only use of the source repository; offline inference only) |
| `runs/<stage>-<UTC>-<hex>/` | Aggregate outputs and a manifest per run (code, data and artifact hashes). Failed runs are kept and marked `FAILED.txt` |
| `docs/` | The static GitHub Pages site and downloadable data |

Row-level observations and individual predictions are kept in a local, git-ignored `_private/` folder and are **not** published.

## Status

Provisional. The Chapters 1-5 review covers the drafts supplied on 2026-10-24; update the ledger in `eval/content.py` and rebuild as revisions arrive.
