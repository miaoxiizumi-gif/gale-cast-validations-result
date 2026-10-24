"""Write the documentation set (documentation/*.md) from saved run outputs, so documents, site and ledger agree.

Called by build_site.py. Every number is read from runs/*; prose that is not a number is written here once.
"""
from __future__ import annotations

import json

import pandas as pd

import common as C
import paper_ledger as PL

DOC = C.WORKSPACE / "documentation"
SITE = "https://miaoxiizumi-gif.github.io/gale-cast-validations-result/"

REFS = [
    ("Rasp, S., Dueben, P. D., Scher, S., Weyn, J. A., Mouatadid, S., & Thuerey, N. (2020). WeatherBench: A benchmark data set for "
     "data-driven weather forecasting. *Journal of Advances in Modeling Earth Systems*, 12(11), e2020MS002203.",
     "https://doi.org/10.1029/2020MS002203",
     "Defines a persistence forecast (\"the fields at initialization time are used as forecasts\") and climatologies computed from the "
     "training period, and states that \"to be useful, a forecast system needs to beat the weekly climatology and the persistence forecast\" "
     "(arXiv:2002.00469v3, read 2026-10-25). Used here for why persistence and training-period climatology are reference forecasts. "
     "It concerns gridded global forecasts; it does not validate GALE-CAST's architecture or its split dates."),
    ("Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting*, "
     "22(4), 679-688.", "https://doi.org/10.1016/j.ijforecast.2006.03.001",
     "Defines scaled errors and MASE: \"A scaled error is less than one if it arises from a better forecast than the average one-step "
     "naïve forecast computed in-sample\" (author preprint, read 2026-10-25). Used here to explain why MASE < 1 against an in-sample "
     "denominator does not establish a win against a same-case test baseline."),
]


def latest(prefix):
    return sorted(p for p in C.RUNS.glob(f"{prefix}-*") if not (p / "FAILED.txt").exists())[-1]


def J(p):
    return json.loads(p.read_text(encoding="utf-8"))


def placeholders() -> tuple[dict, dict]:
    r = {k: latest(p) for k, p in {"w": "w-cohort", "rp": "reg-prov", "b": "b-benchmark", "case": "case", "pf": "pf",
                                   "sf": "split-facts", "s2": "s2-partitions", "s2b": "s2b-supplementary", "s1": "s1-identity",
                                   "a": "a-legacy"}.items()}
    A, RP, B, SF, S2 = (J(r["w"] / "website_cohort_results.json"), J(r["rp"] / "regression_provenance.json"),
                        J(r["b"] / "benchmark_results.json"), J(r["sf"] / "split_facts.json"), J(r["s2"] / "stage2_partitions.json"))
    reg = A["regression"]
    pt = lambda v, m, k="mae": reg[v]["scopes"]["pooled"]["point"][m][k]
    bx = B["events"]["pooled"]["classifiers"]["W1+X1@0.601"]
    ph = {
        **{f"run_{k}": v.name for k, v in r.items()},
        "pa_rows_in_test": f"{S2['w1_split_reconstructed']['port_area_rows_dated_in_test_period']:,}",
        "supp_rows_in_test": f"{S2['supplementary_Training_csv']['rows_dated_in_test_period']:,}",
        "primary_rows": f"{6342 + 1095 + 3519:,}",
        "a_prauc_x1": f"{A['events']['pooled']['probabilistic']['W1+X1']['pr_auc']:.4f}",
        "a_bss_x1": f"{A['events']['pooled']['probabilistic']['W1+X1']['brier_skill_vs_climatology']:.2f}",
        "a_pos": A["label"]["positives"], "a_press_only": A["label"]["pressure_only"], "a_wind_only": A["label"]["wind_only"],
        "mos_fallback_rows": RP["mos_rows_from_fallback_fit_on_later_evaluation_rows"],
        "b_cases": f"{B['counts']['event']['eligible']:,}", "b_events": B["counts"]["event"]["events_total"],
        "b_tp": int(bx["tp"]), "b_fp": int(bx["fp"]),
        "a_wind_n": f"{reg['wind']['n_common']:,}", "a_w1_mae": f"{pt('wind', 'W1'):.3f}", "a_w1_mae_kmh": f"{pt('wind', 'W1') * 3.6:.2f}",
        "a_w1_rmse": f"{pt('wind', 'W1', 'rmse'):.3f}", "a_pe_mae": f"{pt('wind', 'persistence'):.3f}", "a_cl_mae": f"{pt('wind', 'climatology'):.3f}",
        "a_mslp_w1": f"{pt('mslp', 'W1'):.2f}", "a_mslp_pe": f"{pt('mslp', 'persistence'):.2f}",
        "a_hum_w1": f"{pt('humidity', 'W1'):.2f}", "a_hum_pe": f"{pt('humidity', 'persistence'):.2f}",
        "a_rain_w1": f"{pt('rainfall', 'W1'):.2f}", "a_rain_pe": f"{pt('rainfall', 'persistence'):.2f}", "a_rain_cl": f"{pt('rainfall', 'climatology'):.2f}",
        "a_rain_rmse_w1": f"{pt('rainfall', 'W1', 'rmse'):.1f}", "a_rain_rmse_cl": f"{pt('rainfall', 'climatology', 'rmse'):.1f}",
    }
    return ph, {"runs": r, "A": A, "RP": RP, "B": B, "SF": SF, "S2": S2, "case": J(r["case"] / "case_selection_summary.json"),
                "pf": J(r["pf"] / "figure_guide.json")}


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |" for r in rows]
    return "\n".join(out)


def write(name, text):
    DOC.mkdir(exist_ok=True)
    (DOC / name).write_text(text.strip() + "\n", encoding="utf-8")


def main() -> dict:
    ph, X = placeholders()
    A, RP, B, SF, case, pf, runs = X["A"], X["RP"], X["B"], X["SF"], X["case"], X["pf"], X["runs"]
    ev = A["events"]["pooled"]["classifiers"]
    clim_key = [k for k in ev if k.startswith("event_climatology")][0]
    ci = A["events"]["pooled"]["ci"]
    ledger = PL.build(ph)

    # ------------------------------------------------------------ EVALUATION_METHOD.md
    write("EVALUATION_METHOD.md", f"""
# Evaluation method

**Name used in the paper:** *Retrospective forecast verification with persistence and climatology benchmarking.*
The three-day examples are *retrospectively selected illustrative case studies*.

## What each term means

| Term | Meaning here | Is it cross-validation? |
|---|---|---|
| Chronological partitioning | How the primary-station records were divided: training (to 2020-10-14), tuning (2020-10-15 to 2021-10-14), evaluation (from 2021-10-15). | No. It is one split. |
| Retrospective verification | Running the frozen model on past dates and checking each next-day forecast against what was recorded. | No. |
| Baseline benchmarking | Scoring persistence and climatology on exactly the same cases and comparing. | No. |
| Selected case studies | A few dates chosen to explain behaviour, labelled as selected. | No, and not a performance estimate. |

No k-fold, rolling-origin or walk-forward cross-validation of the network was executed. Replaying a frozen model one day at a time over
a past period is repeated next-day verification, not cross-validation. The only `TimeSeriesSplit` in the project fitted post-processing
on evaluation-period outcomes (see `MODEL_AND_DATA_SUMMARY.md`, regression provenance).

## Three evidence groups (kept separate)

| Group | Cases | Inputs | Truth | Purpose |
|---|---|---|---|---|
| **A. Website historical scorecard** | the website's 3,423 next-day windows (1,141 per primary station; target dates 2021-11-16 to 2024-12-30) | historical scoring procedure: pooled `scaled_weather` inputs, 32-day windows | processed (forward-filled) label, as on the website; raw observations for regression | reproduce and explain what the website shows; add same-case baselines |
| **B. Training-consistent benchmark** | {ph['b_cases']} event cases / {B['counts']['wind']['eligible']:,} wind cases, target dates 2021-10-15 to 2024-12-31 | per-station scalers as in training | raw, unimputed observations | the declared benchmark of `spec/EVAL_SPEC_v1.md` |
| **C. Selected case studies** | 3 station windows + 1 common window (3 days each) | as A | raw observations | explanation only |

Group A's case identity was recovered without regenerating predictions: the saved reproduction rows (`a-legacy-20261023T162426Z-b5f446`)
match the original W1-branch record `nine_fp_report.json` for all 9 false alarms and 4 misses (station, date and score), and the matrix is
TN 3386, FP 9, FN 4, TP 24. A single re-run (`{ph['run_w']}`) recovered the other regression outputs and reproduced the saved scores within
3e-8.

## Timing

Forecasts are issued after the daily observation of day *t* is complete, from the 32 days *t−31…t*; the target is day *t+1*. Every case is a
**next-day (+1 day)** forecast. W1 has no archived multi-day forecasts, so no +2 or +3 day skill is claimed. The three-day case windows are
three consecutive target dates, each with its own next-day forecast.

## Label

Study label (positive): wind ≥ 10.8 m/s **or** a same-station 24-hour MSLP fall ≥ 3 hPa. Pressure-triggered positives count as events.
In Group A all {ph['a_pos']} positives are pressure falls ({ph['a_press_only']} pressure-only, {ph['a_wind_only']} wind-triggered); no day
reached 10.8 m/s and none reached the gale-force threshold of 17.2 m/s. The study label is therefore distinct from independently observed
gale-force wind.

## Baselines (never built from target-day observations)

| Baseline | Definition | Fitted on |
|---|---|---|
| Wind / pressure / humidity / rainfall persistence | the raw observation of the issue day *t* | nothing |
| Climatology (regression) | station × calendar-month mean of raw observations | 2015-01-01 to 2020-10-14 (W1's primary training period) |
| Event persistence | the study label of the issue day *t* | nothing |
| Event climatology | station × month frequency of the label | 2015-01-02 to 2020-10-14; decision threshold {A['event_climatology_threshold']['threshold']:.4f} chosen by maximum F1 on the tuning year only |

W1's thresholds are unchanged: X1 ≥ 0.601 (website) and raw ≥ 0.64 (documented).

## Metrics and how to read them

- **MAE / RMSE:** lower means smaller numerical error *on the matching cases*. RMSE weights large errors more.
- **Mean signed error (bias):** forecast minus observed. It shows systematic over- or under-forecasting, and positive and negative errors can
  cancel, so a small bias does not mean small errors.
- **Better average error does not mean better event detection.** MAE is dominated by ordinary days; events here are pressure falls.
- **MASE:** error divided by an in-sample naïve error from training data. Below one does not prove a win against a separately computed
  same-case baseline (Hyndman & Koehler, 2006).
- **Precision, recall, F1, PR-AUC:** reported with all four confusion-matrix cells. Accuracy is shown with the all-negative reference.
- **Uncertainty:** paired circular block bootstrap over target dates (14-day blocks, 2,000 resamples). "Established" means the 95% interval
  excludes zero.
- **Selected dates cannot establish general forecasting superiority.**

## Why persistence and climatology

Persistence ("tomorrow = today") and climatology (the usual value for the station and month) need no model, so a forecast system must beat
them to show added value (Rasp et al., 2020). They are computed here on the identical cases used for W1.

## References

""" + "\n".join(f"- {t} {u}  \n  *Use:* {n}" for t, u, n in REFS))

    # ------------------------------------------------------------ MODEL_AND_DATA_SUMMARY.md
    S2, sfp = X["S2"], SF["partitions"]
    write("MODEL_AND_DATA_SUMMARY.md", f"""
# Model and data summary

## Deployed model W1

| Item | Value |
|---|---|
| File | `gale_cast_model_multioutput.keras`, SHA-256 `f2db5aa93226225405914094a0855ac725734a0e2c1a2331e3ba69a8fd9d14b0` (= `gale_cast_model_multioutput_w3.keras`, label "W1") |
| Provenance | branch `exp/precision-targeting`, `experiments/w1x1/_train_w3.py`; promoted to live in commit `1fd1ef9` (2026-09-18) |
| Architecture | dual-stream: `input_normal` (32 days × 32 features) → LSTM(64) → Dense(32); `input_anomaly` (32 × 4) → LSTM → additive attention over time steps → LSTM(32) → Dense(16); merged; heads `gale_prob` (sigmoid) and `weather_vars` (6 regression outputs); 40,872 parameters |
| Training | one `model.fit` on primary rows before 2020-10-15 + all Port Area rows + all supplementary rows; early stopping on the tuning year (`val_gale_prob_loss`, patience 12); no saved history or seed; no pre-training stage |
| Scoring procedure behind the website | `_w1_recall_floor.py`: pooled `scaled_weather` inputs, X1 = same-date mean over the three stations, threshold 0.601 |
| Live system | the dashboard tier uses wind/pressure rules, not the model score; the 24-step live endpoint fails on this 32-step model; displayed 2025+ values are simulated or imported PAGASA forecasts |

## Station groups

- **Primary (evaluated):** NAIA, Sangley Point, Science Garden.
- **Supplementary (training only):** Port Area (records to 2023-10-31) and 19 additional Luzon stations (`Training.csv`, 69,388 rows to
  2024-12-30). Described as *supplementary PAGASA observations, owner-confirmed*. No independent source verification has been done, and
  the earlier "SMOTE" reading of the filename has been withdrawn: SMOTE was used only in archived notebooks v2.6-v2.8.

## Actual split (primary stations)

| Partition | Dates | Rows | Study-label events | Event dates (episodes) | Pressure-only / wind-triggered |
|---|---|---|---|---|---|
""" + "\n".join(f"| {n} | {p['first']} to {p['last']} | {p['rows']:,} | {p['events']} | {p['event_dates']} ({p['episodes_consecutive_dates']}) | {p['pressure_only']} / {p['wind_only'] + p['both']} |"
                for n, p in sfp.items()) + f"""

Also used in training: Port Area (3,225 rows; {ph['pa_rows_in_test']} dated inside the evaluation period) and supplementary rows
({ph['supp_rows_in_test']} dated inside the evaluation period). Training total: 78,955 rows with 1,143 positive labels.

## Regression provenance (what the website's regression block is)

The website's wind row (MAE 0.5365 m/s, RMSE 0.7723, MASE 0.6782) is reproduced exactly (`{ph['run_rp']}`) by:
1. W1 neural wind output (MAE {RP['steps']['neural_only']['mae']:.3f});
2. linear + isotonic MOS per station × season, cross-fitted with an 8-fold `TimeSeriesSplit` **over the evaluation rows** ({ph['mos_fallback_rows']} rows
   calibrated by a fit on later evaluation rows) → MAE {RP['steps']['after_mos']['mae']:.3f};
3. a blend {RP['blend_weight_on_model']:.2f} × model + {1 - RP['blend_weight_on_model']:.2f} × the processed wind observed **two days before the target**
   (script indexing), weight chosen by `TimeSeriesSplit` MAE on evaluation rows → MAE {RP['steps']['after_blend']['mae']:.4f}.

Same-case issue-day persistence on the same truth: MAE {RP['steps']['persistence_same_cases_same_truth']['mae']:.3f}, RMSE
{RP['steps']['persistence_same_cases_same_truth']['rmse']:.3f}. MASE uses an in-sample lag-365 denominator ({RP['mase_denominator_lag365_train']:.4f} m/s).
The website's wind-direction row (43.40°) comes from a separate direction-only model. Chapter 4's Table 4.5 (wind 2.04 km/h = 0.5655 m/s)
is the same pipeline run on the model **before** W1. None of these are neural W1 results.

W1's neural-only next-day errors on the website's cases (raw truth): wind MAE {ph['a_w1_mae']} m/s (persistence {ph['a_pe_mae']},
climatology {ph['a_cl_mae']}); MSLP {ph['a_mslp_w1']} hPa (persistence {ph['a_mslp_pe']}); humidity {ph['a_hum_w1']}% (persistence
{ph['a_hum_pe']}); rainfall {ph['a_rain_w1']} mm (persistence {ph['a_rain_pe']}, climatology {ph['a_rain_cl']}).
""")

    # ------------------------------------------------------------ SPLIT_DESIGN_ASSESSMENT.md
    tr, tu, evp = sfp["training"], sfp["tuning"], sfp["evaluation"]
    write("SPLIT_DESIGN_ASSESSMENT.md", f"""
# Split design: documented facts and a present-day assessment

## Documented facts

- Primary-station cut-offs in the executed recipe (`_train_w3.py`): training dates before 2020-10-15; tuning 2020-10-15 to 2021-10-14
  (early stopping and threshold selection); evaluation from 2021-10-15. The code calls 2021-10-15 the "v12 canonical split". The date is
  already present in the repository's first commit (2026-07-26); earlier experiments used other cut-offs (2020-12-31 "Split B",
  2021-07-02 "Split C").
- **The exact calendar cutoff rationale was not preserved in the original experiment records.** No commit message, configuration comment or
  document states why these dates were chosen. No record shows that the panel approved this historical split.
- Port Area and supplementary rows were used for training regardless of date: {ph['pa_rows_in_test']} Port Area rows and
  {ph['supp_rows_in_test']} supplementary rows are dated inside the evaluation period.
- The evaluation period was later used to compare W1 with other trained variants, to adopt X1 and to choose the threshold rule
  (0.601 adopted after the max-F1 rule's 0.62 had been scored on it). It is therefore not an independent test.

## Facts checked for this assessment

| Partition | Years | Rows | Events | Event dates | Episodes | Events by season |
|---|---|---|---|---|---|---|
""" + "\n".join(f"| {n} | {p['years_covered']} | {p['rows']:,} | {p['events']} | {p['event_dates']} | {p['episodes_consecutive_dates']} | "
                + "; ".join(f"{k}: {v}" for k, v in sorted(p['events_by_season'].items())) + " |" for n, p in sfp.items()) + f"""

All three partitions contain all twelve calendar months. Episodes are runs of consecutive event dates (any station).

## Present-day assessment of the split's design

*This section is a retrospective assessment written on 2026-10-25. It is not the original documented reasoning.*

Design considerations supported by evidence:
- An LSTM needs ordered sequences, and each input window must precede its target. A chronological split respects this; a random split
  of overlapping 32-day windows would place near-duplicate windows on both sides.
- A 32-day window means each partition needs 32 days of earlier context; the evaluation cases start on 2021-11-16 for this reason.
- Multi-year training ({tr['years_covered']} years at the primary stations) exposes the model to several seasonal cycles.
- A separate one-year tuning block supports early stopping and threshold selection without using evaluation dates, and it covers every month once.

Weaknesses found:
- The tuning year holds only {tu['events']} events on {tu['event_dates']} dates ({tu['episodes_consecutive_dates']} episodes), {tu['events_by_season'].get('Sep-Nov (late typhoon season)', 0)} of them in
  September-November. A threshold chosen on so few episodes is fragile.
- The evaluation period's {evp['events']} events fall on {evp['event_dates']} dates ({evp['episodes_consecutive_dates']} episodes); events are not independent, so intervals are wide.
- Every evaluation-period event is a pressure fall; wind-triggered detection cannot be assessed on this split.
- Supplementary and Port Area records dated within the evaluation period, and the historical reuse of evaluation outcomes for selection,
  mean the split does not give an independent test.

These points explain aspects of the design. They do not establish why the October cut-offs were chosen, the architecture does not require
these exact dates, and good scores on the evaluation period do not prove the split valid. The only clean test available is a prospective
evaluation on observations from 2025 onward.
""")

    # ------------------------------------------------------------ FIGURE_GUIDE.md
    rows = [[f"`{g['png']}` / `{g['svg']}` / `{g['csv']}`", g["evidence_group"], g["caption"], ", ".join(f"`{s}`" for s in g["source_runs"])]
            for g in pf["figures"]]
    cs = case["per_station"]
    priv = [[f"PF-H ({s})", "C (selected)", (f"3-day window around a {v['trigger']}-triggered event; outcomes: {', '.join(v['outcomes'])}; "
                                              f"event persistence on the event day: {v['event_persistence_on_event_day']}; {v['eligible_candidates']} eligible candidates"
                                              if v.get("outcomes") else v.get("reason", "")), "private only"] for s, v in cs.items()]
    if case.get("common"):
        priv.append(["PF-I (all three stations)", "C (selected)", "3-day window around a date detected at all three stations", "private only"])
    write("FIGURE_GUIDE.md", f"""
# Figure guide

Public figures are aggregates. Each is downloadable as PNG (300 DPI), SVG and the CSV of the plotted numbers, from
[`docs/figures/paper/`](../docs/figures/paper/) (site: {SITE}#figures). Figure run: `{ph['run_pf']}`.

## Public paper figures

{md_table(["Files", "Evidence", "Caption and interpretation", "Source runs"], rows)}

Earlier evaluation figures F1-F8 (Group B benchmark and model variants) remain on the site and in `docs/figures/`.

## Selected case figures (private)

These plot individual PAGASA station-day readings. PAGASA's data terms (CADS-07 Rev.6, condition 4, as recorded in the source project)
forbid publishing station readings online and no permission was found, so they exist only in the private thesis-export folder and are
**not** publicly available. Selection run: `{ph['run_case']}`; criteria: `spec/CASE_SELECTION_v1.md`.

{md_table(["Figure", "Evidence", "Content", "Availability"], priv)}

Every case figure carries the label: "Selected successful case; chosen retrospectively for illustration; not representative of all dates."
Each date shows a separate next-day forecast; the windows are not three-day-ahead forecasts.
""")

    # ------------------------------------------------------------ PAPER_REVISION_LEDGER.md
    lrows = [[r["id"], f"Ch {r['chapter']}, {r['heading']}, PDF p. {r['pdf_page']}", f"\"{r['find_text']}\"", r["replacement"], r["reason"],
              r["evidence"], r["status"]] for r in ledger]
    write("PAPER_REVISION_LEDGER.md", f"""
# Paper revision ledger (Chapters 1-5)

Source: the chapter PDFs dated 2026-10-23 listed in `SOURCE_DOCUMENTS.md`. Only PDFs exist, so every entry is **proposed only**; no chapter
file was edited. "PDF p." is the page index within each chapter's PDF file. Every find text was checked against the PDFs' extracted text
({sum(r['find_check'] == 'found' for r in ledger)} of {len(ledger)} found). Short excerpts only; the chapters themselves are not published.

{md_table(["ID", "Location", "Find (exact)", "Replace with", "Reason", "Evidence", "Status"], lrows)}

The earlier chapter review notes (R-1-01 … R-5-05, 2026-10-24) remain on the site as background; where they differ, this ledger governs.
""")
    pd.DataFrame(ledger).to_csv(DOC / "paper_revision_ledger.csv", index=False)

    # ------------------------------------------------------------ SOURCE_DOCUMENTS.md
    write("SOURCE_DOCUMENTS.md", """
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
""")

    # ------------------------------------------------------------ README.md (root)
    x1 = ev["W1+X1@0.601"]; pe = ev["event_persistence"]; cl = ev[clim_key]
    (C.WORKSPACE / "README.md").write_text(f"""# GALE-CAST W1: retrospective forecast verification and paper evidence

Evidence for the thesis *GALE-CAST*, about the frozen, deployed model **W1** (`gale_cast_model_multioutput.keras`, SHA-256
`f2db5aa9…9d14b0`). Nothing was retrained, recalibrated or changed in production.

- **Website:** {SITE}
- **Method:** retrospective forecast verification with persistence and climatology benchmarking (not cross-validation).

## Evidence groups

| Group | What it is | Headline |
|---|---|---|
| **A. Website historical scorecard** | the 3,423 cases behind the website matrix, identified case by case | TN 3386, FP 9, FN 4, TP 24 at X1 ≥ 0.601; F1 {x1['f1']:.3f} vs event persistence {pe['f1']:.3f} and event climatology {cl['f1']:.3f} (difference vs persistence established) |
| **B. Training-consistent benchmark** | {ph['b_cases']} cases, inputs scaled as in training | {ph['b_tp']} of {ph['b_events']} events, {ph['b_fp']} false alarms |
| **C. Selected case studies** | three-day windows chosen retrospectively for illustration | private figures only (PAGASA terms) |

W1 ranks pressure-fall days well, but its neural wind, pressure and humidity forecasts are less accurate than persistence on the same
cases, its scores are not calibrated probabilities, and every evaluation-period event is a pressure fall rather than gale-force wind.

## Documents

| Document | Content |
|---|---|
| [`documentation/EVALUATION_METHOD.md`](documentation/EVALUATION_METHOD.md) | method, baselines, metrics, references |
| [`documentation/MODEL_AND_DATA_SUMMARY.md`](documentation/MODEL_AND_DATA_SUMMARY.md) | W1 identity, split, station groups, data status, regression provenance |
| [`documentation/FIGURE_GUIDE.md`](documentation/FIGURE_GUIDE.md) | every figure, its cohort, source run and interpretation |
| [`documentation/PAPER_REVISION_LEDGER.md`](documentation/PAPER_REVISION_LEDGER.md) | exact find/replace corrections for Chapters 1-5 |
| [`documentation/SPLIT_DESIGN_ASSESSMENT.md`](documentation/SPLIT_DESIGN_ASSESSMENT.md) | documented split facts and a labelled present-day assessment |
| [`documentation/SOURCE_DOCUMENTS.md`](documentation/SOURCE_DOCUMENTS.md) | source documents, branches, commits and chapter versions |
| [`spec/`](spec/) | specification and amendments, each committed before its analysis |
| [`HANDOFF.md`](HANDOFF.md) | run order and open items |

## Layout

`spec/` declarations · `eval/` code · `runs/<stage>-<UTC>-<hex>/` aggregate outputs and manifests (failed runs kept, marked `FAILED.txt`) ·
`docs/` GitHub Pages site · `documentation/` the documents above. Row-level observations, predictions, case figures and chapter text stay
in the git-ignored `_private/` folder.

## Credits

| Person / account | Role (from repository evidence) |
|---|---|
| Courtney ([miaoxiizumi-gif](https://github.com/miaoxiizumi-gif)) | repository owner; author of every commit in this repository |
| Christine Tamayo ([Tinenen-cs](https://github.com/Tinenen-cs)) | front-end contributor to the GALE-CAST application repository (commit history of its `master` branch); not a contributor to this repository |

Other thesis-team members, and the thesis authorship list, are not recorded in either repository and need confirmation before they are
added. AI tool use is disclosed separately: commits in this repository carry a
`Co-Authored-By: Claude` trailer recording assistance by an AI coding tool, which is not a human author.

PAGASA is the source of the station observations.
""", encoding="utf-8")
    return {"ph": ph, "ledger": ledger, **X}


if __name__ == "__main__":
    main()
