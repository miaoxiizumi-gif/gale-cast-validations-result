# GALE-CAST Model-W1: retrospective forecast verification and paper evidence

Evidence for the thesis *GALE-CAST*, about the frozen, deployed model **GALE-CAST Model-W1** (`gale_cast_model_multioutput.keras`, SHA-256
`f2db5aa9…9d14b0`). Nothing was retrained, recalibrated or changed in production.

- **Website:** https://miaoxiizumi-gif.github.io/gale-cast-validations-result/
- **Method:** retrospective forecast verification with persistence and climatology benchmarking (not cross-validation).

## Evidence groups

| Group | What it is | Headline |
|---|---|---|
| **A. Website historical scorecard** | the 3,423 cases behind the website matrix, identified case by case | TN 3386, FP 9, FN 4, TP 24 at X1 ≥ 0.601; F1 0.787 vs event persistence 0.250 and event climatology 0.078 (difference vs persistence established) |
| **B. Training-consistent benchmark** | 3,520 cases, inputs scaled as in training | 16 of 27 events, 8 false alarms |
| **D. reference comparison validation (panel request)** | every date on which both persistence and climatology had large errors (GALE-CAST Model-W1 not used to choose), every event onset, then example windows where GALE-CAST Model-W1 did well | onsets: GALE-CAST Model-W1+X1 warned of 17 of 21 (persistence and climatology 0 and 0); humidity MAE 10.83 vs 13.44 / 14.58 %; wind and rainfall not better; not representative of all dates |
| **E. Persistence-worse dates (panel directive)** | station-dates on which persistence's wind and MSLP errors were both larger than GALE-CAST Model-W1's (dates selected for low GALE-CAST Model-W1 error) | 258 of 3,421 (7.5%); GALE-CAST Model-W1 < persistence there by construction; on all dates persistence is better |
| **C. Selected illustrative case studies** | three-day windows chosen retrospectively for illustration: set 1 around detected events; set 2 with relatively high wind, selected for low GALE-CAST Model-W1 wind error (disclosed) | downloadable selected figures; not representative |

GALE-CAST Model-W1 ranks pressure-fall days well, but its neural wind, pressure and humidity forecasts are less accurate than persistence on the same
cases, its scores are not calibrated probabilities, and every evaluation-period event is a pressure fall rather than gale-force wind.

## Documents

| Document | Content |
|---|---|
| [`documentation/EVALUATION_METHOD.md`](documentation/EVALUATION_METHOD.md) | method, baselines, metrics, references |
| [`documentation/MODEL_AND_DATA_SUMMARY.md`](documentation/MODEL_AND_DATA_SUMMARY.md) | GALE-CAST Model-W1 identity, split, station groups, data status, regression provenance |
| [`documentation/FIGURE_GUIDE.md`](documentation/FIGURE_GUIDE.md) | every figure, its cohort, source run and interpretation |
| [`documentation/PAPER_REVISION_LEDGER.md`](documentation/PAPER_REVISION_LEDGER.md) | exact find/replace corrections for Chapters 1-5 |
| [`documentation/SPLIT_DESIGN_ASSESSMENT.md`](documentation/SPLIT_DESIGN_ASSESSMENT.md) | documented split facts and a labelled present-day assessment |
| [`documentation/SOURCE_DOCUMENTS.md`](documentation/SOURCE_DOCUMENTS.md) | source documents, branches, commits and chapter versions |
| [`documentation/TECH_STACK.md`](documentation/TECH_STACK.md) | verified implementation stack with source and version evidence, and a Chapter 3 paragraph |
| [`spec/`](spec/) | specification and amendments, each committed before its analysis |
| [`HANDOFF.md`](HANDOFF.md) | run order and open items |

## Layout

`spec/` declarations · `eval/` code · `runs/<stage>-<UTC>-<hex>/` aggregate outputs and manifests (had large errors runs kept, marked `FAILED.txt`) ·
`docs/` GitHub Pages site · `documentation/` the documents above. The full row archive and chapter text stay in the git-ignored `_private/` folder. Selected case figures and their plotted rows are published for panel review.

## Credits

| Person / account | Role (from repository evidence) |
|---|---|
| Courtney ([miaoxiizumi-gif](https://github.com/miaoxiizumi-gif)) | repository owner; original evaluation contributor |
| Christine Tamayo ([Tinenen-cs](https://github.com/Tinenen-cs)) | front-end contributor to the GALE-CAST application; implementation-stack documentation contributor to this results repository |

Other thesis-team members, and the thesis authorship list, are not recorded in either repository and need confirmation before they are
added. AI tool use is disclosed separately: commits in this repository carry a
`Co-Authored-By: Claude` trailer recording assistance by an AI coding tool, which is not a human author.

PAGASA is the source of the station observations.

## Implementation technology stack

See [TECH_STACK.md](documentation/TECH_STACK.md) for the source-backed frontend, backend, database, ML, hosting, and report tooling inventory,
including a proposed Chapter 3 paragraph. Versions are configuration or environment evidence, not a live runtime audit.
