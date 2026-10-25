"""Write the documentation set (documentation/*.md) from saved run outputs, so documents, site and ledger agree.

Called by build_site.py. Every number is read from runs/*; prose that is not a number is written here once.
"""
from __future__ import annotations

import json

import pandas as pd

import common as C
import figure_notes as FN
import paper_ledger as PL
import tech_stack
import terms

PANEL_PUB = ["PF-L_large_error_dates_mae", "PF-M_large_error_dates_differences", "PF-N_event_onsets", "PF-Q_persistence_worse_dates",
             "PF-L_composite_validation"]

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
    return sorted(p for p in C.RUNS.glob(f"{prefix}-2*") if not (p / "FAILED.txt").exists())[-1]


def J(p):
    return json.loads(p.read_text(encoding="utf-8"))


def placeholders() -> tuple[dict, dict]:
    r = {k: latest(p) for k, p in {"w": "w-cohort", "rp": "reg-prov", "b": "b-benchmark", "case": "case", "pf": "pf",
                                   "sf": "split-facts", "s2": "s2-partitions", "s2b": "s2b-supplementary", "s1": "s1-identity",
                                   "a": "a-legacy", "case2": "case-v2", "case3": "panel-v3", "case4": "persist-v4", "v": "s7-variants", "fig": "fig"}.items()}
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
    case1, case2 = J(r["case"] / "case_selection_summary.json"), J(r["case2"] / "case_selection_v2_summary.json")
    case3 = J(r["case3"] / "panel_v3_results.json")
    ph.update(panel_placeholders(case3))
    case4 = J(r["case4"] / "persistence_v4_results.json")
    ph.update(persistence_placeholders(case4, case3))
    V = J(r["v"] / "variants_results.json")
    ctx = {"A": A, "B": B, "RP": RP, "V": V, "case1": case1, "case2": case2, "run_w": r["w"].name, "run_rp": r["rp"].name,
           "run_pf": r["pf"].name, "run_b": r["b"].name, "run_fig": r["fig"].name, "run_v": r["v"].name,
           "run_case1": r["case"].name, "run_case2": r["case2"].name, "case3": case3, "run_case3": r["case3"].name,
           "case4": case4, "run_case4": r["case4"].name}
    return ph, {"runs": r, "A": A, "RP": RP, "B": B, "SF": SF, "S2": S2, "case": case1, "case2": case2, "case3": case3, "case4": case4,
                "pf": J(r["pf"] / "figure_guide.json"), "NOTES": FN.notes(ctx), "ctx": ctx}


def panel_placeholders(D: dict) -> dict:
    """Numbers of selection v3 (baseline-failure validation) used by the ledger and documents."""
    P = D["part1_A_q90"]
    out = {}
    for v in P:
        r = P[v]["pooled"]["baseline_failure"]
        out[f"v3_{v}_n"] = r["n"]
        for m, k in (("W1", "w1"), ("persistence", "pe"), ("climatology", "cl"), ("control", "ctl")):
            out[f"v3_{v}_{k}"] = f"{r['point'][m]['mae']:.2f}"
        for b, k in (("persistence", "pe"), ("climatology", "cl"), ("control", "ctl")):
            out[f"v3_{v}_vs_{k}"] = r["ci"][f"dmae_W1_{b}"]["verdict"]
    for ev in ("A", "B"):
        o = D["onsets"][ev]["pooled"]
        out[f"v3_on_{ev}"] = o["onsets"]
        out[f"v3_on_{ev}_x1"] = o["onset_hits"]["W1+X1@0.601"]
        out[f"v3_on_{ev}_pe"] = o["onset_hits"]["event_persistence"]
        out[f"v3_on_{ev}_cl"] = o["onset_hits"]["event_climatology"]
        out[f"v3_fa_{ev}_x1"] = o["false_alarms_on_non_events"]["W1+X1@0.601"]
        out[f"v3_fa_{ev}_cl"] = o["false_alarms_on_non_events"]["event_climatology"]
    return out


def persistence_placeholders(D: dict, D3: dict) -> dict:
    """Numbers of selection v4 (persistence worse than W1 for wind and MSLP) and the frozen PF-L rainfall panel."""
    q, a = D["qualifying"]["pooled"], D["all_complete"]["pooled"]
    rf = D3["part1_A_q90"]["rainfall"]["pooled"]["all_complete"]
    out = {"v4_n": q["n"], "v4_total": f"{D['complete']['pooled']:,}", "v4_share": f"{D['share']['pooled'] * 100:.1f}",
           "v4_clim_both": q["both_beat_climatology_too"], "v4_events": q["events"],
           "v4_rain_all_n": f"{rf['n']:,}", "v4_rain_all_w1": f"{rf['point']['W1']['mae']:.2f}",
           "v4_rain_all_pe": f"{rf['point']['persistence']['mae']:.2f}", "v4_rain_all_cl": f"{rf['point']['climatology']['mae']:.2f}"}
    for v in ("wind", "mslp"):
        for m, k in (("W1", "w1"), ("persistence", "pe"), ("climatology", "cl")):
            out[f"v4_{v}_{k}"] = f"{q[v][m]:.2f}"
            out[f"v4_{v}_{k}_all"] = f"{a[v][m]:.2f}"
    for s, k in (("NAIA", "na"), ("Sangley Point", "sp"), ("Science Garden", "sg")):
        out[f"v4_n_{k}"] = D["qualifying"][s]["n"]
        w = D["windows"]["per_station"][s]
        out[f"v4_win_{k}"] = (f"{w['length']}-date window; W1 also beat climatology on {w['W1_beats_climatology_cells']} of {w['of_cells']} cells"
                              if w.get("selected") else "no window (no two consecutive qualifying dates)")
    return out


def v3_table(ph: dict) -> str:
    return md_table(["Variable (pooled)", "Baseline-failure dates", "MAE W1 / persistence / climatology / control", "W1 − persistence",
                     "W1 − climatology", "W1 − control"],
                    [[v, ph[f"v3_{v}_n"], f"{ph[f'v3_{v}_w1']} / {ph[f'v3_{v}_pe']} / {ph[f'v3_{v}_cl']} / {ph[f'v3_{v}_ctl']}",
                      ph[f"v3_{v}_vs_pe"], ph[f"v3_{v}_vs_cl"], ph[f"v3_{v}_vs_ctl"]] for v in ("wind", "mslp", "humidity", "rainfall")])


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |" for r in rows]
    return "\n".join(out)


def public_md(text: str, where: str = "document") -> str:
    """Panel naming rules for a public Markdown document (model name; no banned words)."""
    text = terms.markdown(text)
    terms.check(text, where)
    return text


def write(name, text):
    DOC.mkdir(exist_ok=True)
    (DOC / name).write_text(public_md(text.strip(), name) + "\n", encoding="utf-8")


def write_private_index(X) -> None:
    """_private/thesis_export/INDEX.md: files, explanations and day-by-day values of the selected cases (never published)."""
    ctx, NOTES = X["ctx"], X["NOTES"]
    exp = C.PRIVATE / "thesis_export"
    rows = pd.read_csv(C.private_dir(X["runs"]["w"]) / "website_cohort_rows.csv", parse_dates=["date"])
    s1 = J(C.private_dir(X["runs"]["case"]) / "PRIVATE_selection_summary.json")
    s2 = J(C.private_dir(X["runs"]["case2"]) / "PRIVATE_selection_summary_v2.json")
    s3 = J(C.private_dir(X["runs"]["case3"]) / "PRIVATE_selection_summary_v3.json")
    s4 = J(C.private_dir(X["runs"]["case4"]) / "PRIVATE_selection_summary_v4.json")
    FIGN = {"v1": ("PF-H_case_{}", "PF-I_common_window_all_stations"), "v2": ("PF-J_regression_case_{}", "PF-K_regression_common_window"),
            "v3": ("PF-O_panel_window_{}", "PF-P_panel_common_window"), "v4": ("PF-R_persistence_window_{}", None)}

    def table(station, dates):
        out = ["| Target date (issued after the previous day) | Variable | Observed | W1 | Persistence | Climatology | abs err W1 / P / C | Closest |",
               "|---|---|---|---|---|---|---|---|"]
        for d in dates:
            r = rows[(rows["station"] == station) & (rows["date"] == pd.Timestamp(d))].iloc[0]
            dec = int(r["x1"] >= 0.601)
            oc = {(1, 1): "Hit", (0, 0): "Correct negative", (1, 0): "Miss", (0, 1): "False alarm"}[(int(r["y"]), dec)]
            for v, u in (("wind", "m/s"), ("mslp", "hPa"), ("humidity", "%"), ("rainfall", "mm")):
                o = r[f"obs_{v}"]; e = {k: abs(r[c] - o) for k, c in (("W1", f"W1_{v}"), ("P", f"pers_{v}"), ("C", f"clim_{v}"))}
                best = "/".join(k for k, x in e.items() if x == min(e.values()))
                out.append(f"| {d} | {v} ({u}) | {o:.1f} | {r[f'W1_{v}']:.1f} | {r[f'pers_{v}']:.1f} | {r[f'clim_{v}']:.1f} | "
                           f"{e['W1']:.2f} / {e['P']:.2f} / {e['C']:.2f} | {best} |")
            out.append(f"| {d} | warning | X1 = {r['x1']:.2f} | {'warning' if dec else 'no warning'} | "
                       f"{'warning' if r['E_persist'] == 1 else 'no warning'} | — | label: {'pressure fall' if r['L_press'] else ('wind' if r['L_wind'] else 'no event')} | {oc} |")
        return "\n".join(out)

    parts = ["# Private thesis-export index (NOT for publication)", "",
             "Contains exact dates and individual PAGASA readings. PAGASA CADS-07 Rev.6 condition 4: do not post online. For the printed thesis only.",
             f"Every figure: {FN.SELECTED}", "", f"Source rows: `_private/runs/{X['runs']['w'].name}/website_cohort_rows.csv`.", ""]
    for key, run, summ, figs in (("v1", ctx["run_case1"], s1, ("PF-H", "PF-I")), ("v2", ctx["run_case2"], s2, ("PF-J", "PF-K")),
                                 ("v3", ctx["run_case3"], s3, ("PF-O", "PF-P")), ("v4", ctx["run_case4"], s4, ("PF-R",))):
        parts += [f"## Selection {key}: folder `{run}/`", ""]
        if key in ("v3", "v4"):
            parts += [f"Every {key} figure: {FN.PANEL if key == 'v3' else FN.PERSIST}", ""]
        for fid in figs:
            parts.append(FN.markdown(fid, NOTES[fid]))
        for s, v in summ["per_station"].items():
            if v.get("window"):
                fn = FIGN[key][0].format(s.replace(" ", "_"))
                parts += [f"### {s}: {', '.join(v['window'])}  (files `{fn}.png`, `{fn}.svg`)", "", table(s, v["window"]), ""]
        if summ.get("common"):
            fn = FIGN[key][1]
            parts += [f"### Common window: {', '.join(summ['common']['window'])}  (files `{fn}.png`, `{fn}.svg`)", ""]
            for s in C.PRIMARY:
                parts += [f"#### {s}", "", table(s, summ["common"]["window"]), ""]
    (exp / "INDEX.md").write_text("\n".join(parts) + "\n", encoding="utf-8")


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
| **D. Baseline-failure validation (panel request)** | every Group A station-date on which both persistence and climatology failed (training-period 90th-percentile rule, `CASE_SELECTION_v3_panel_validation.md`) and every event onset; then example windows where W1 did well | as A (saved rows; no model run); wind and onsets also on B | raw observations | show where the reference forecasts fail and how W1 does there; examples not representative |
| **E. Persistence-worse dates (panel directive)** | station-dates on which persistence's wind AND MSLP errors were both larger than W1's (`CASE_SELECTION_v4_persistence_override.md`); dates selected for low W1 error | as A (saved rows; no model run) | raw observations | show that and how often such dates occur; W1 < persistence there by construction |
| **C. Selected illustrative case studies** | set 1 (`CASE_SELECTION_v1.md`): 3 station windows + 1 common window around detected events; set 2 (`CASE_SELECTION_v2_regression.md`): 3 station windows + 1 common window with relatively high wind, selected for low W1 wind error (disclosed) | as A (saved rows; no model run) | raw observations | explanation only; not representative |

### Selected illustrative case studies: what the two sets show

- **Set 1 (classification behaviour):** W1+X1 warned correctly on every day of the selected windows, and every event was a pressure fall.
  This is a classification success, not a regression success: W1's wind error was smaller than both baselines on only 3 of the 9
  station-days.
- **Set 2 (regression example chosen for low model error, requested by the panel):** chosen *because* W1's wind error was smaller than both baselines.
  Its rule was recorded before the search (relatively higher wind = observed wind ≥ the station's 2015-2020 90th percentile on at least one
  day). Results by station are in `FIGURE_GUIDE.md` (PF-J, PF-K). The pressure forecast was the closest on few of these days.
- Neither set establishes general superiority; the overall comparisons (Evidence A and B) do.

### Baseline-failure validation (Evidence D, panel request)

*{FN.PANEL}*

The panel asked for historical dates on which persistence and climatology perform poorly. `spec/CASE_SELECTION_v3_panel_validation.md`
(committed before the analysis) defines them **without using W1**: a station-date is a *baseline-failure date* for a variable when the
persistence error is at least the station's 2015-2020 90th percentile of day-to-day change **and** the climatology error is at least the
90th percentile of deviation from the station × month mean. W1 is then scored on **every** such date (Part 1); example windows where W1 did
well are picked only afterwards (Part 2, private figures). A no-model control (the average of the two baselines) shows how much of any advantage
on these dates a simple hedge also gets, because choosing dates by baseline error favours any forecast that does not copy a baseline.

{v3_table(ph)}

"established: negative" = W1's error is smaller and the 95% interval excludes zero; "positive" = W1's error is larger. Event onsets (no
event on the issue day, an event on the target day): Evidence A {ph['v3_on_A']} onsets, W1+X1 warned of {ph['v3_on_A_x1']}
({ph['v3_fa_A_x1']} false alarms on all non-event days), event persistence {ph['v3_on_A_pe']}, event climatology {ph['v3_on_A_cl']};
Evidence B {ph['v3_on_B']} onsets, W1+X1 {ph['v3_on_B_x1']} ({ph['v3_fa_B_x1']} false alarms), event climatology {ph['v3_on_B_cl']}
({ph['v3_fa_B_cl']} false alarms).

Reading: where the references fail, W1's clearest advantage is **warning of pressure-fall onsets**. For numerical forecasts the advantage
is limited to humidity (helped by W1's high humidity bias, since these dates are mostly humidity rises) and to MSLP against climatology
only; for wind (except Science Garden, again a bias effect) and rainfall W1 is not better on these dates. Per-station detail:
`FIGURE_GUIDE.md` (PF-L to PF-P).

**Panel directive on PF-L (2026-10-25):** PF-L's rainfall panel shows all complete dates only (n = {ph['v4_rain_all_n']}; MAE W1
{ph['v4_rain_all_w1']}, persistence {ph['v4_rain_all_pe']}, climatology {ph['v4_rain_all_cl']} mm). The panel is locked: the site build
fails if the plotted values differ from `spec/FROZEN_PF-L_rainfall.json`. The baseline-failure rainfall result is still computed and
reported (inside the panel, in PF-M, in the CSV and in the table above). The humidity panel keeps its baseline-failure values under their
correct label and sample size (n = {ph['v3_humidity_n']}); a request to relabel them "All complete dates (n = 3,421)" was not applied,
because those values come from {ph['v3_humidity_n']} station-dates, not 3,421 (on all dates W1's humidity MAE is larger than persistence's).

### Dates where persistence was worse than W1 for wind and MSLP (Evidence E, panel directive)

*{FN.PERSIST}*

The panel noted that persistence is the reference that beats W1 on average for wind and MSLP, and directed a search for target dates on
which persistence's error was larger than W1's for **both** (climatology not part of the filter). `spec/CASE_SELECTION_v4_persistence_override.md`
was committed before the search. {ph['v4_n']} of {ph['v4_total']} complete station-dates qualify ({ph['v4_share']}%; NAIA {ph['v4_n_na']},
Sangley Point {ph['v4_n_sp']}, Science Garden {ph['v4_n_sg']}). On them, wind MAE is W1 {ph['v4_wind_w1']} vs persistence {ph['v4_wind_pe']}
and climatology {ph['v4_wind_cl']} m/s; MSLP W1 {ph['v4_mslp_w1']} vs {ph['v4_mslp_pe']} / {ph['v4_mslp_cl']} hPa; W1 also beat climatology
for both variables on {ph['v4_clim_both']} of them. W1 < persistence holds on these dates **by construction**. On all
{ph['v4_total']} dates persistence remains better (wind {ph['v4_wind_pe_all']} vs W1 {ph['v4_wind_w1_all']} m/s; MSLP {ph['v4_mslp_pe_all']}
vs {ph['v4_mslp_w1_all']} hPa). Windows (private, PF-R): NAIA: {ph['v4_win_na']}; Sangley Point: {ph['v4_win_sp']}; Science Garden:
{ph['v4_win_sg']}. No common window qualifies at all three stations.

**Composite figure for section 8.E (panel directive, 2026-10-25).** *Selected validation example chosen to demonstrate baseline
limitations as requested by the thesis panel; not representative of all historical dates.* At the panel's direction the site was first
returned to the state of commit `5255788` (by `git revert`, history kept), and section 8.E then shows a single 2×2 figure,
`PF-L_composite_validation`, in which W1's MAE is lower than both baselines in every panel. Each panel uses its own set of dates: wind and
MSLP on the v4 dates ({ph['v4_n']} station-dates), humidity on the v3 baseline-failure dates for humidity ({ph['v3_humidity_n']}), rainfall
on all complete dates ({ph['v4_rain_all_n']}). These dates were chosen for this outcome, so the figure shows that such dates exist; it does
not show that the model is better in general. On all complete dates persistence is more accurate than W1 for wind, MSLP and humidity (PF-F3).

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
- **Selected dates cannot establish general forecasting superiority.** Conditioning on baseline failure (Evidence D) is a stratified
  view of the same cases, not a new test, and it favours forecasts that do not copy a baseline.

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

Implementation technologies around the model (web, API, database, hosting) are listed separately in `TECH_STACK.md`; they are not
evidence of forecast accuracy.

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
    NOTES = X["NOTES"]
    pub_ids = [g["figure"] for g in pf["figures"]]
    legacy = ["F1_partitions", "F2_wind_mae_by_station", "F3_wind_monthly_means", "F4_wind_obs_vs_pred_counts",
              "F5_event_timeline_monthly", "F6_confusion_matrices", "F7_event_benchmarks", "F8_variants_and_inputs"]
    write("FIGURE_GUIDE.md", f"""
# Figure guide

Every figure has the same nine-part explanation (what it shows, purpose, how it was produced, how to read it, actual finding, what it
supports, what it does not establish, use in the paper, source). The text is generated from `eval/figure_notes.py`, the single source used
by the website too. Numbers are filled from the saved runs.

How to read numerical errors: {FN.ERRORS}

## Public paper figures (download PNG 300 DPI, SVG, CSV)

Files are in [`docs/figures/paper/`](../docs/figures/paper/) (site: {SITE}#figures). Figure run: `{ph['run_pf']}`.

""" + "\n".join(FN.markdown(f"{i} — `{i}.png` / `.svg` / `.csv`", NOTES[i]) for i in pub_ids) + f"""

## Baseline-failure validation figures (Evidence D, panel request; public aggregates)

Every figure in this group states: "{FN.PANEL}" Rule: `spec/CASE_SELECTION_v3_panel_validation.md`. Run `{ph['run_case3']}`; files in
[`docs/figures/paper/`](../docs/figures/paper/). PF-L to PF-N are aggregates over every qualifying date (no dates or readings).
PF-Q (Evidence E, run `{ph['run_case4']}`, `spec/CASE_SELECTION_v4_persistence_override.md`) states: "{FN.PERSIST}"

""" + "\n".join(FN.markdown(f"{i} — `{i}.png` / `.svg` / `.csv`", NOTES[i]) for i in PANEL_PUB) + f"""

## Earlier benchmark figures (Evidence B unless stated; PNG on the site, data in `docs/data/`)

""" + "\n".join(FN.markdown(f"{i} — `docs/figures/{i}.png`", NOTES[i]) for i in legacy) + f"""

## Selected illustrative case studies (panel review downloads)

Selected station and common-window plots are published for panel review at
`docs/figures/paper/`, with PNG, SVG and CSV downloads in the site's case-study
and figure-download sections. The source archive remains in `_private/thesis_export/`.

Every case figure states: "{FN.SELECTED}" Each date shows a separate next-day forecast, not a +1/+2/+3-day forecast from one origin.

""" + "\n".join(FN.markdown(f"{i} (panel review)", NOTES[i]) for i in ("PF-H", "PF-I", "PF-J", "PF-K", "PF-O", "PF-P", "PF-R")))
    write_private_index(X)

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

## Implementation-stack supplement (2026-10-25)

`TECH_STACK.md` reviews the application at GALE-CAST commit `bb056a9` (`requirements.txt`, `requirements-dev.txt`, `Dockerfile`, `app.py`,
`dashboard.html`, `static/sw.js`, `hosting/vercel.json`, `docker/db-init/schema.sql`, `.github/workflows/tests.yml`) together with
`docs/PROJECT_STRUCTURE.md` and `docs/handoff/DEPLOYMENT_AND_GITHUB.md`. It was first compiled by Tinenen-cs (commit `8b32465`) and verified
line by line on the same date. It is a separate implementation inventory; it does not change or re-execute the W1 evaluation, and no live
package inventory or private case values were used for it.

## Selection amendments

`spec/CASE_SELECTION_v1.md` (classification case studies), `spec/CASE_SELECTION_v2_regression.md` (regression case chosen for low model error) and
`spec/CASE_SELECTION_v3_panel_validation.md` (baseline-failure validation, panel request) and
`spec/CASE_SELECTION_v4_persistence_override.md` (persistence worse than W1 for wind and MSLP, panel directive), each committed before its
search. `spec/FROZEN_PF-L_rainfall.json` locks PF-L's rainfall panel (panel directive).
""")
    tech_stack.write_documents(C.WORKSPACE)

    # ------------------------------------------------------------ README.md (root)
    x1 = ev["W1+X1@0.601"]; pe = ev["event_persistence"]; cl = ev[clim_key]
    (C.WORKSPACE / "README.md").write_text(public_md(f"""# GALE-CAST W1: retrospective forecast verification and paper evidence

Evidence for the thesis *GALE-CAST*, about the frozen, deployed model **W1** (`gale_cast_model_multioutput.keras`, SHA-256
`f2db5aa9…9d14b0`). Nothing was retrained, recalibrated or changed in production.

- **Website:** {SITE}
- **Method:** retrospective forecast verification with persistence and climatology benchmarking (not cross-validation).

## Evidence groups

| Group | What it is | Headline |
|---|---|---|
| **A. Website historical scorecard** | the 3,423 cases behind the website matrix, identified case by case | TN 3386, FP 9, FN 4, TP 24 at X1 ≥ 0.601; F1 {x1['f1']:.3f} vs event persistence {pe['f1']:.3f} and event climatology {cl['f1']:.3f} (difference vs persistence established) |
| **B. Training-consistent benchmark** | {ph['b_cases']} cases, inputs scaled as in training | {ph['b_tp']} of {ph['b_events']} events, {ph['b_fp']} false alarms |
| **D. Baseline-failure validation (panel request)** | every date on which both persistence and climatology failed (W1 not used to choose), every event onset, then example windows where W1 did well | onsets: W1+X1 warned of {ph['v3_on_A_x1']} of {ph['v3_on_A']} (persistence and climatology {ph['v3_on_A_pe']} and {ph['v3_on_A_cl']}); humidity MAE {ph['v3_humidity_w1']} vs {ph['v3_humidity_pe']} / {ph['v3_humidity_cl']} %; wind and rainfall not better; not representative of all dates |
| **E. Persistence-worse dates (panel directive)** | station-dates on which persistence's wind and MSLP errors were both larger than W1's (dates selected for low W1 error) | {ph['v4_n']} of {ph['v4_total']} ({ph['v4_share']}%); W1 < persistence there by construction; on all dates persistence is better |
| **C. Selected illustrative case studies** | three-day windows chosen retrospectively for illustration: set 1 around detected events; set 2 with relatively high wind, selected for low W1 wind error (disclosed) | downloadable selected figures; not representative |

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
| [`documentation/TECH_STACK.md`](documentation/TECH_STACK.md) | verified implementation stack with source and version evidence, and a Chapter 3 paragraph |
| [`spec/`](spec/) | specification and amendments, each committed before its analysis |
| [`HANDOFF.md`](HANDOFF.md) | run order and open items |

## Layout

`spec/` declarations · `eval/` code · `runs/<stage>-<UTC>-<hex>/` aggregate outputs and manifests (failed runs kept, marked `FAILED.txt`) ·
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
""", "README.md"), encoding="utf-8")
    return {"ph": ph, "ledger": ledger, **X}


if __name__ == "__main__":
    main()
