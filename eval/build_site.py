"""Build the static handoff site (docs/) and machine-readable exports from saved run outputs.

No new computation of results happens here: every number is read from runs/*/ JSON or CSV.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil

import pandas as pd

import common as C
import build_docs
from content import CLAIMS, LIMITS, OMISSIONS, REV

DOCS = C.WORKSPACE / "docs"
EVAL_ID = "GCV-W1-v1"
REPO_URL = "https://github.com/miaoxiizumi-gif/gale-cast-validations-result"
SITE_URL = "https://miaoxiizumi-gif.github.io/gale-cast-validations-result/"


def latest(prefix):
    c = [p for p in sorted(C.RUNS.glob(f"{prefix}-*")) if not (p / "FAILED.txt").exists()]
    return c[-1]


def J(p):
    return json.loads(p.read_text(encoding="utf-8"))


def e(s):
    return html.escape(str(s))


def md_inline(s: str) -> str:
    s = e(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def f(x, d=3):
    return "—" if x is None else f"{x:.{d}f}"


def table(headers, rows, cls=""):
    th = "".join(f"<th>{e(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def ci(c, d=3):
    return "—" if c is None or c.get("lo") is None else f"[{c['lo']:.{d}f}, {c['hi']:.{d}f}]"


def main():
    runs = {k: latest(p) for k, p in {"s1": "s1-identity", "s2": "s2-partitions", "s2b": "s2b-supplementary",
                                       "a": "a-legacy", "b": "b-benchmark", "d1": "diag-inputs", "d2": "diag-insample",
                                       "v": "s7-variants", "fig": "fig", "w": "w-cohort", "rp": "reg-prov",
                                       "sf": "split-facts", "case": "case", "pf": "pf"}.items()}
    s1 = J(runs["s1"] / "stage1_identity.json")
    s2 = J(runs["s2"] / "stage2_partitions.json")
    s2b = J(runs["s2b"] / "supplementary_counts.json")
    A = J(runs["a"] / "cohort_a_results.json")
    Bm = J(runs["b"] / "benchmark_results.json")
    D1 = J(runs["d1"] / "diag_inputs.json")
    D2 = J(runs["d2"] / "diag_insample.json")
    V = J(runs["v"] / "variants_results.json")
    figchk = J(runs["fig"] / "figure_checks.json")

    wp = Bm["wind"]["pooled"]["point"]
    ep = Bm["events"]["pooled"]
    cls = ep["classifiers"]
    x1 = cls["W1+X1@0.601"]
    ph = {k: v.name for k, v in runs.items()}
    ph.update({
        "prauc_x1_train": f(ep["probabilistic"]["W1+X1"]["pr_auc"]),
        "prauc_x1_leg": f(ep["probabilistic"]["W1+X1_legacy_inputs"]["pr_auc"]),
        "wind_n": f"{Bm['counts']['wind']['eligible']:,}", "w1_mae": f(wp["W1"]["mae"]), "pe_mae": f(wp["persistence"]["mae"]),
        "cl_mae": f(wp["climatology"]["mae"]), "w1_rmse": f(wp["W1"]["rmse"]), "w1_mae_kmh": f(wp["W1"]["mae"] * 3.6, 2),
        "w1_sd": f(wp["W1_pred_sd"], 2), "obs_sd": f(wp["obs_sd"], 2),
        "ev_n": Bm["counts"]["event"]["events_total"], "x1_tp": int(x1["tp"]), "x1_fp": int(x1["fp"]),
        "x1_f1": f(x1["f1"]), "x1_p": f(x1["precision"]), "x1_r": f(x1["recall"]),
        "pe_f1": f(cls["event_persistence"]["f1"]),
        "bss_x1": f(ep["probabilistic"]["W1+X1"]["brier_skill_vs_climatology"], 2),
        "allneg": f(x1["all_negative_accuracy"], 4), "imp": Bm["counts"]["window_has_imputed_value"],
        "w1_mase": f(wp["W1"]["mae"] / 0.7912, 2),
        "w10_x1": f(V["variants"]["_w10"]["S-TRAIN"]["pr_auc_x1"]),
    })

    def fill(s):
        return s.format(**ph)

    # ------------------------------------------------------------- copy figures and data
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "figures").mkdir(parents=True)
    (DOCS / "data").mkdir()
    for p in runs["fig"].glob("F*.png"):
        shutil.copy(p, DOCS / "figures" / p.name)
    for p in runs["fig"].glob("F*.csv"):
        shutil.copy(p, DOCS / "data" / p.name)
    X = build_docs.main()  # writes documentation/*.md and README.md from the same runs
    PH, LED, WA, RPv, CASE = X["ph"], X["ledger"], X["A"], X["RP"], X["case"]
    (DOCS / "figures" / "paper").mkdir()
    for p in (X["runs"]["pf"] / "figures").glob("PF-*"):
        shutil.copy(p, DOCS / "figures" / "paper" / p.name)
    (DOCS / "data" / "documentation").mkdir()
    for p in (C.WORKSPACE / "documentation").glob("*"):
        shutil.copy(p, DOCS / "data" / "documentation" / p.name)
    for p in ("AMENDMENT_A2_website_cohort.md", "CASE_SELECTION_v1.md"):
        shutil.copy(C.WORKSPACE / "spec" / p, DOCS / "data" / p)
    shutil.copy(runs["b"] / "wind_monthly_means_by_station.csv", DOCS / "data")
    shutil.copy(runs["b"] / "event_outcomes_monthly_by_station.csv", DOCS / "data")

    # metrics registry (stable IDs)
    M = []
    def m(id_, desc, val, ci_=None, src=None):
        M.append({"id": id_, "metric": desc, "value": val, "ci95": ci_, "source_run": src or runs["b"].name})
    for sc in ["pooled", *C.PRIMARY]:
        bw = Bm["wind"][sc]
        for meth in ("W1", "persistence", "climatology"):
            tag = f"M-W-{sc[:3].upper()}-{meth[:3].upper()}"
            m(tag + "-MAE", f"Wind MAE m/s, {sc}, {meth}", bw["point"][meth]["mae"], bw["ci"][f"mae_{meth}"])
            m(tag + "-RMSE", f"Wind RMSE m/s, {sc}, {meth}", bw["point"][meth]["rmse"])
            m(tag + "-BIAS", f"Wind bias m/s (forecast-observed), {sc}, {meth}", bw["point"][meth]["bias"])
        for k in ("dmae_W1_persistence", "dmae_W1_climatology"):
            m(f"M-W-{sc[:3].upper()}-{k.upper()}", f"Paired MAE difference W1 minus {k.split('_')[-1]}, {sc}",
              None, bw["ci"][k])
    for sc in ["pooled", *C.PRIMARY]:
        for n, c in Bm["events"][sc]["classifiers"].items():
            m(f"M-E-{sc[:3].upper()}-{n}", f"Event confusion matrix and scores, {sc}, {n}", c,
              {k: Bm["events"][sc]["ci"].get(f"{k}_{n}") for k in ("precision", "recall", "f1")})
        for n, c in Bm["events"][sc]["probabilistic"].items():
            m(f"M-P-{sc[:3].upper()}-{n}", f"Probabilistic scores, {sc}, {n}", c, Bm["events"][sc]["ci"].get(f"prauc_{n}"))
    m("M-A-REPRO", "Cohort A legacy reproduction (all checks)", A["reproduction"], None, runs["a"].name)
    (DOCS / "data" / "metrics.json").write_text(json.dumps({"evaluation_id": EVAL_ID, "metrics": M}, indent=2, default=str), encoding="utf-8")
    claims_j = [{"id": i, "class": k, "claim": fill(t), "evidence": fill(ev)} for i, k, t, ev in CLAIMS]
    (DOCS / "data" / "claims.json").write_text(json.dumps(claims_j, indent=2), encoding="utf-8")
    rev_j = [{"id": r[0], "chapter": r[1], "section": r[2], "claim": r[3], "verdict": r[4],
              "evidence": fill(r[5]), "replacement": fill(r[6])} for r in REV]
    (DOCS / "data" / "revisions.json").write_text(json.dumps({"evaluation_id": EVAL_ID, "status": "provisional",
                                                               "revisions": rev_j, "omissions": OMISSIONS,
                                                               "limitations": LIMITS}, indent=2), encoding="utf-8")
    pd.DataFrame(rev_j).to_csv(DOCS / "data" / "revision_ledger.csv", index=False)
    # aggregate result tables
    wrows = []
    for sc in ["pooled", *C.PRIMARY]:
        for meth in ("W1", "persistence", "climatology", "W1_legacy_inputs"):
            p = Bm["wind"][sc]["point"][meth]
            wrows.append({"scope": sc, "method": meth, **p})
    pd.DataFrame(wrows).to_csv(DOCS / "data" / "wind_results.csv", index=False)
    erows = []
    for sc in ["pooled", *C.PRIMARY]:
        for n, c in Bm["events"][sc]["classifiers"].items():
            erows.append({"scope": sc, "procedure": n, **c})
    pd.DataFrame(erows).to_csv(DOCS / "data" / "event_results.csv", index=False)
    vrows = []
    for v, r in V["variants"].items():
        for cons in ("S-TRAIN", "S-LEGACY"):
            if r.get("scored"):
                rr = r[cons]
                vrows.append({"variant": r["label"], "construction": cons, "threshold": r["threshold_documented"],
                              "pr_auc_raw": rr["pr_auc_raw"], "pr_auc_x1": rr["pr_auc_x1"], "brier_raw": rr["brier_raw"],
                              **{k: rr["raw_at_documented_threshold"][k] for k in ("tp", "fp", "fn", "tn")},
                              "wind_mae": rr["wind_mae"], "wind_pred_sd": rr["wind_pred_sd"]})
    pd.DataFrame(vrows).to_csv(DOCS / "data" / "variants_results.csv", index=False)
    shutil.copy(C.WORKSPACE / "spec" / "EVAL_SPEC_v1.md", DOCS / "data" / "EVAL_SPEC_v1.md")
    shutil.copy(C.WORKSPACE / "spec" / "EVAL_SPEC_v1.json", DOCS / "data" / "EVAL_SPEC_v1.json")

    # ------------------------------------------------------------- HTML sections
    S = []
    nav = []

    SECS = {}

    def sec(id_, title, body):
        SECS[id_] = (title, body)

    tr = s2["w1_split_reconstructed"]
    spec_commit = C.git(["log", "--format=%h %ad", "--date=iso", "--reverse", "--", "spec/EVAL_SPEC_v1.json"], cwd=C.WORKSPACE).splitlines()[0]

    ev = WA["events"]["pooled"]
    cA = ev["classifiers"]
    ckey = [k for k in cA if k.startswith("event_climatology")][0]
    xa, pa, ca = cA["W1+X1@0.601"], cA["event_persistence"], cA[ckey]
    sec("overview", "Overview in plain English", f"""
<p class="lead">GALE-CAST's deployed model, <strong>W1</strong>, reads the last 32 days of weather at a Metro Manila station and gives
(a) a score for whether <em>tomorrow</em> meets the study's hazard label (wind ≥ 10.8 m/s or a 24-hour pressure fall ≥ 3 hPa) and
(b) six next-day weather values. This site checks the frozen model, without changing it, against what was recorded and against two
simple reference forecasts. The method is <b>retrospective forecast verification with persistence and climatology benchmarking</b>;
it is not cross-validation.</p>
<div class="cards">
 <div class="card"><div class="k">Website scorecard, traced</div><div class="v">24 / 28</div><div class="s">events caught with 9 false alarms on the
 website's 3,423 cases. Every case was identified and matches the original saved record.</div></div>
 <div class="card good"><div class="k">Strength: event detection</div><div class="v">F1 {xa['f1']:.2f}</div><div class="s">vs {pa['f1']:.2f} for
 "tomorrow's label = today's" and {ca['f1']:.2f} for the monthly event rate, on the same cases (difference vs persistence established).
 PR-AUC {ev['probabilistic']['W1+X1']['pr_auc']:.2f} vs no-skill {xa['prevalence']:.3f}.</div></div>
 <div class="card bad"><div class="k">Weakness: weather values</div><div class="v">{PH['a_w1_mae']} m/s</div><div class="s">wind error (MAE) of W1 vs
 <b>{PH['a_pe_mae']}</b> for "tomorrow = today". W1 is also worse than persistence for pressure and humidity.</div></div>
 <div class="card"><div class="k">Training-consistent inputs</div><div class="v">{PH['b_tp']} / {PH['b_events']}</div><div class="s">events caught
 ({PH['b_fp']} false alarms) when inputs are scaled as in training: the scorecard depends on input scaling.</div></div>
</div>
<p><b>What this means.</b> W1 is genuinely better than simple rules at flagging the days on which station pressure falls sharply, and the
website's matrix can be reproduced case by case. But every event in 2021-2024 was a pressure fall (no gale-force wind was recorded), the
scores are not calibrated probabilities, the period was used to choose the scoring rule, and W1's own wind, pressure and humidity forecasts
are less accurate than persistence. The website's regression numbers come from post-processing fitted on the evaluation period, not from W1 alone.</p>
<div class="groups"><div><span class="tag new">A</span> <b>Website historical scorecard</b>: overall evidence on the website's own cases.</div>
<div><span class="tag hist">B</span> <b>Training-consistent benchmark</b>: overall evidence, declared before scoring (the two B sections).</div>
<div><span class="tag sel">C</span> <b>Selected case studies</b>: chosen retrospectively to explain behaviour; not representative.</div></div>
<p class="note">Evaluation <code>{EVAL_ID}</code> with amendment A2. Specification committed before scoring: <code>{e(spec_commit)}</code>.
Status: <b>provisional</b>; chapter corrections are proposals, not applied edits.</p>
<p class="legend"><span class="tag repo">repository fact</span> <span class="tag hist">historical claim with saved record</span>
<span class="tag new">new result (this evaluation)</span> <span class="tag interp">interpretation / limitation</span></p>
""")

    def fig(name, alt, cap):
        return (f'<figure><img src="figures/paper/{name}.png" alt="{e(alt)}" loading="lazy"><figcaption>{cap} '
                f'Download: <a href="figures/paper/{name}.png">PNG (300 DPI)</a> · <a href="figures/paper/{name}.svg">SVG</a> · '
                f'<a href="figures/paper/{name}.csv">CSV</a>.</figcaption></figure>')

    # Evidence A ----------------------------------------------------------------
    lab, chk = WA["label"], WA["checks"]
    erowsA = [[e(k), int(c["tp"]), int(c["fn"]), int(c["fp"]), int(c["tn"]), f(c["precision"]), f(c["recall"]), f(c["f1"]),
               ci(ev["ci"].get(f"f1_{k}"))] for k, c in cA.items()]
    dA = [[e(k), ci(v), e(v["verdict"])] for k, v in ev["ci"].items() if k.startswith("d")]
    sec("scorecard", "A. The website's historical scorecard, case by case", f"""
<p><span class="tag new">Evidence A</span> The website (<code>validation_cm3.json</code>) shows TN 3386, FP 9, FN 4, TP 24 at threshold 0.601.
These are the 3,423 next-day windows of the historical scoring script (1,141 per primary station; target dates 2021-11-16 to 2024-12-30).
No original per-case prediction file was saved, so the cases come from the reproduction run <code>a-legacy-20261023T162426Z-b5f446</code>,
checked against the <b>original</b> W1-branch record of the 9 false alarms and 4 misses (identity match:
{'✔' if chk['fp_identity_matches_original_record'] and chk['fn_identity_matches_original_record'] else '✘'}; re-run score differences ≤
{max(chk['rerun_prob_max_abs_diff'], chk['rerun_x1_max_abs_diff']):.0e}). This is a different cohort from the 3,520-case benchmark (B).</p>
<p><b>Label composition:</b> {lab['positives']} positives = {lab['pressure_only']} pressure-only, {lab['wind_only']} wind-only, {lab['both']} both.
The label uses processed (forward-filled) values, as on the website; recomputed from raw observations it agrees on {lab['raw_label_agrees']:,} of
{lab['raw_label_determinable']:,} determinable cases. These are study-label events, not observed gale-force winds.</p>
{fig("PF-A_website_confusion_matrix", "Two-by-two matrix: 24 hits, 4 misses, 9 false alarms, 3386 correct negatives", "<b>PF-A.</b> The exact website matrix. Its 99.62% accuracy sits next to the 99.18% of always saying 'no event'.")}
{fig("PF-B_station_outcomes", "Three small matrices, one per station", "<b>PF-B.</b> Hits, misses, false alarms and correct negatives by station. X1 averages the three stations, so a warning applies to all three on a date.")}
<h3>Same cases, simple baselines</h3>
{table(["Procedure", "Hits", "Misses", "False alarms", "Correct neg.", "Precision", "Recall", "F1", "F1 95% CI"], erowsA)}
{table(["Paired difference (W1 − baseline)", "95% CI", "Verdict"], dA)}
<p class="small">Event persistence = the issue day's label. Event climatology = station × month label frequency 2015-2020, warning if ≥
{WA['event_climatology_threshold']['threshold']:.4f} (chosen on the tuning year only). df1 / dprauc positive = W1 better; dbrier positive = W1 worse
(its scores are not calibrated: Brier skill {ev['probabilistic']['W1+X1']['brier_skill_vs_climatology']:.2f}).</p>
{fig("PF-C_event_metrics_overall", "Precision, recall and F1 for W1+X1, persistence and climatology on two cohorts", "<b>PF-C.</b> Overall event metrics on the website cases (A) and on the training-consistent benchmark (B), each with its own baselines. W1+X1 leads on F1 in both; the level depends on input scaling.")}
{fig("PF-D_event_metrics_by_station", "Event metrics per station", "<b>PF-D.</b> The same comparison per station; 8-10 events each, so intervals are wide.")}
{fig("PF-E_precision_recall_curves", "Precision-recall curves with the 0.601 operating point", "<b>PF-E.</b> Precision-recall curves traced from the 3,423 saved scores, with the historical operating point and event persistence marked.")}
""")

    # Evidence C ----------------------------------------------------------------
    crow = [[s_, v.get("trigger", "—"), ", ".join(v.get("outcomes", [])) or e(v.get("reason", "")),
             v.get("event_persistence_on_event_day", "—"), v.get("eligible_candidates", 0)] for s_, v in CASE["per_station"].items()]
    sec("cases", "C. Selected illustrative case studies", f"""
<div class="selected"><p><span class="tag sel">Evidence C</span> <b>Selected successful cases; chosen retrospectively for illustration.</b>
They explain how W1 behaved around correctly detected events. They are not representative of all dates and say nothing about overall
performance, which sections A and B show.</p>
<p><b>How they were chosen</b> (criteria committed before selection: <a href="data/CASE_SELECTION_v1.md">CASE_SELECTION_v1.md</a>): from the 24 hits,
three consecutive target dates (day before, event day, day after) at one station, with complete raw wind and pressure observations and a
raw-confirmed event; ranked by the number of correct W1 decisions in the window (a favourable criterion, disclosed), then the size of the
pressure fall, then date. W1's error relative to the baselines was <b>not</b> used. {CASE['eligible']} of {CASE['candidates']} candidates passed.</p>
<p><b>Timing:</b> each date shows its own next-day forecast. The three dates are not a +1/+2/+3-day forecast.</p>
{table(["Station", "Event trigger", "W1+X1 outcomes (day before, event, day after)", "Event persistence on the event day", "Eligible candidates"], crow)}
<p><b>Why the figures are not on this site:</b> they plot individual PAGASA station-day readings, which PAGASA's data terms (CADS-07 Rev.6,
condition 4) do not allow online, and no permission was found. The per-station figures and the all-station common window are kept in a
private thesis-export folder for the printed thesis. Exact dates are withheld here, as for every event date on this site.</p>
<p><b>What they show</b> (described without readings): in every selected window the label is triggered by a same-station pressure fall of
at least 3 hPa, and the W1+X1 score is above 0.601 on the event day and below it on the neighbouring non-event days. W1's own next-day
pressure value showed a fall in some windows but not in others, and at Science Garden its wind value was well above the observed wind.
These examples illustrate behaviour; the overall comparisons (Sections A, B and the regression evidence) are the basis for any claim.</p></div>
""")

    # regression ----------------------------------------------------------------
    sec("regression", "Regression evidence: what the numbers really are", f"""
<p><span class="tag new">Evidence A</span> The website's regression block (wind MAE 0.5365 m/s, RMSE 0.7723, MASE 0.6782) was traced to
<code>validate_model_multioutput.py</code> at W1 commit <code>1fd1ef9</code> and reproduced <b>exactly</b> (run <code>{PH['run_rp']}</code>). It is not
W1's own output: isotonic MOS and a persistence blend were fitted on the same evaluation period. Chapter 4's Table 4.5 (2.04 km/h) is the same
pipeline on the model before W1, and its wind-direction row comes from a separate direction-only model.</p>
{fig("PF-F2_website_regression_provenance", "Bars: neural 0.987, after MOS 0.576, after blend 0.5365, persistence 0.474", "<b>PF-F2.</b> From W1's neural wind error to the website's 0.5365 m/s, with issue-day persistence on the same cases and truth for reference.")}
{fig("PF-F_wind_mae_rmse", "Wind MAE and RMSE by station for W1, persistence and climatology", f"<b>PF-F.</b> W1's neural next-day wind against both baselines on {PH['a_wind_n']} website cases with raw observations: W1 is worse everywhere.")}
{fig("PF-F3_regression_variables_mae", "MAE of four regression outputs, one panel each", "<b>PF-F3.</b> Every supported regression output in its own unit. Rainfall is the one variable where W1's MAE is lower than both baselines; its RMSE is not lower than climatology's, and it under-forecasts.")}
{fig("PF-G_observed_vs_predicted", "Binned observed versus forecast counts with a 1:1 line", "<b>PF-G.</b> Observed vs W1-forecast values as counts per cell (no individual readings), with the 1:1 line.")}
""")

    # identity
    layers = "".join(f"<li><code>{e(l['name'])}</code> {e(l['class'])}{(' ' + str(l['units'])) if l.get('units') else ''}"
                     f"{(' ' + e(l['activation'])) if l.get('activation') else ''}</li>" for l in s1["layers"])
    ident_rows = [[f"<code>{e(k)}</code>", f"<code>{e(v)}</code>"] for k, v in s1["deployed_files_in_source_checkout"]["sha256"].items()]
    paths = [
        ["Training", "<code>_train_w3.py</code> (" + "exp/precision-targeting" + ")", "32", "per-station W1 scalers", "—", "—", "historical, not reproducible (no seed/log)"],
        ["Historical scoring", "<code>_w1_recall_floor.py</code>", "32", "pooled <code>scaled_weather</code>", "yes", "0.601", "reproduced exactly (Cohort A)"],
        ["Live endpoint <code>/api/predict-next</code>", "<code>app.py:923-974</code>", "24 + recency weights", "pooled <code>scaled_weather</code> + stored predictions", "no", "none", "<b>fails</b> (InvalidArgumentError)"],
        ["Batch predictions 2022-2030", "<code>predict_live.py</code>", "32", "AR(1)-simulated inputs (SEED=42)", "no", "none", "runs; inputs are simulated"],
        ["Displayed values & tiers", "<code>predict_live.py:451</code>, <code>app.py:764</code>, PAGASA overwrite", "—", "—", "no", "wind ≥10.8/17.2 m/s or Δp ≥3/6 hPa", "tier ignores model probability"],
        ["This benchmark (S-TRAIN)", "<code>eval/cohort_b.py</code>", "32", "per-station W1 scalers", "reported both", "0.64 raw; 0.601/0.62 X1", "new retrospective procedure"],
    ]
    sec("identity", "Verified identity of the deployed W1", f"""
<p><span class="tag repo">repository fact</span> {md_inline(fill(CLAIMS[0][2]))} {md_inline(fill(CLAIMS[1][2]))}</p>
{table(["File (" + "1f2d5dd" + ")", "SHA-256"], ident_rows)}
<p>Saved by Keras {e(s1['keras_archive_metadata']['keras_version'])} on {e(s1['keras_archive_metadata']['date_saved'])}; {s1['model']['params_total']:,} parameters;
inputs <code>input_normal (None, 32, 32)</code> and <code>input_anomaly (None, 32, 4)</code>; outputs <code>gale_prob (None, 1)</code> (sigmoid) and
<code>weather_vars (None, 6)</code> (wind speed, humidity, direction sine, direction cosine, log1p rainfall, MSLP; scaled 0-1, inverted with <code>scaler_y_regression_mo</code>).
The 32 normal-stream features are 24 station features plus lag-1 direction sine/cosine of four stations; the anomaly stream holds pressure tendency, precipitation anomaly, pressure drop and storm signal (<code>_train_w3.py</code> 304-318).
Twelve normal and three anomaly features are min-max scaled per station; the rest enter unscaled. The wind-output scaler's range (0-35 m/s) is set by four invented "extreme rows" (lines 480-486).</p>
<details><summary>Layer list (from the saved archive)</summary><ul class="cols">{layers}</ul></details>
<h3>Model vs procedure vs what the website shows</h3>
{table(["Path", "Code", "Window", "Input scaling", "X1", "Threshold", "Status"], paths)}
<p><span class="tag repo">repository fact</span> {md_inline(fill(CLAIMS[3][2]))} {md_inline(fill(CLAIMS[4][2]))} {md_inline(fill(CLAIMS[5][2]))}
We did not change the inputs to make the live endpoint work; it is reported as failing.</p>
""")

    # data
    def sp(x):
        return f"{x['rows']:,}", x.get("first", ""), x.get("last", ""), x.get("label_pos_ge1", "")
    prow = [
        ["Primary 3 stations: training", *sp(tr["train_real"]["by_station"]["NAIA"])[:0],
         f"{sum(v['rows'] for k, v in tr['train_real']['by_station'].items() if k != 'Port Area'):,}", "2015-01-01", "2020-10-14",
         sum(v['label_pos_ge1'] for k, v in tr['train_real']['by_station'].items() if k != 'Port Area'), "fit"],
        ["Port Area (all dates)", *sp(tr["train_real"]["by_station"]["Port Area"]), "fit"],
        ["Supplementary 19 stations", f"{s2b['section_A_study_rule']['rows']:,}", "2015-01-01", "2024-12-30",
         s2b["section_A_study_rule"]["positives_ge1"], "fit (provenance unresolved)"],
        ["Primary 3 stations: tuning", *sp(tr["early_stop_narrow"]["total"]), "early stopping, threshold rules"],
        ["Primary 3 stations: test / benchmark", *sp(tr["test"]["total"]), "historical scoring; this benchmark"],
    ]
    raw = s2["raw_observations"]
    rawrows = [[k, f"{v['rows']:,}", v["first"], v["last"], v["missing_wind_speed"], v["missing_mslp"], v["missing_rainfall"],
                v["days_wind_ge_10_8"], v["days_wind_ge_17_2"]] for k, v in raw.items()]
    bc = Bm["counts"]
    casetab = [
        ["Target station-days 2021-10-15..2024-12-31", f"{bc['target_station_days_in_period']:,}", ""],
        ["with a complete 32-day input window", f"{bc['with_32day_window']:,}", f"excluded {bc['excluded_no_window']}"],
        ["Wind cohort (identical for all methods)", f"{bc['wind']['eligible']:,}", f"target wind missing {bc['wind']['excluded_target_wind_missing']}; issue-day wind missing {bc['wind']['excluded_issue_day_wind_missing_only']}"],
        ["Event cohort (identical for all methods)", f"{bc['event']['eligible']:,}", f"target label undeterminable {bc['event']['excluded_target_label_undeterminable']}; issue-day label undeterminable {bc['event']['excluded_issue_day_label_undeterminable_only']}"],
        ["Events (study label)", bc["event"]["events_total"], f"pressure-only {bc['event']['label_parts']['E_pressure_only']}, wind-only {bc['event']['label_parts']['E_wind_only']}, both {bc['event']['label_parts']['E_both']}"],
        ["Cases with an imputed value in the window", bc["window_has_imputed_value"], "kept (causal fill); S-NOIMPUTE removes them"],
        ["Legacy (imputed) label disagreements", bc["event"]["legacy_imputed_label_disagreements"], "none on eligible cases"],
    ]
    sec("data", "Data, splits and training history", f"""
<h3>Table D1. What W1 was actually trained, tuned and scored on</h3>
{table(["Partition", "Rows", "First", "Last", "Positive labels", "Use"], prow)}
<p class="small">Reconstructed from <code>_train_w3.py</code>'s rules on <code>data/processed_weather.csv</code> (run <code>{ph['s2']}</code>).
Every documented count reproduces: 9,567 real training rows, 1,095 tuning rows, 3,519 test rows, 3,423 test windows, 69,388 supplementary rows,
78,955 total. Training windows built from real rows: {tr['windows_train_real_only']['windows']:,} ({tr['windows_train_real_only']['positive_windows']} positive).</p>
<img src="figures/F1_partitions.png" alt="Timeline of W1 data allocation by source; Port Area and supplementary training rows extend into the test period">
<h3>Table D2. Raw observations (unimputed)</h3>
{table(["Station", "Days", "First", "Last", "Wind missing", "MSLP missing", "Rain missing", "Days ≥10.8 m/s", "Days ≥17.2 m/s"], rawrows)}
<h3>Table D3. Benchmark cases and exclusions</h3>
{table(["Step", "Count", "Notes"], casetab)}
<h3>The split in simple English</h3>
<p>Weather data come in time order, so a fair test must forecast days that come <em>after</em> the days the model learned from;
otherwise the model can "peek" at neighbouring days. GALE-CAST split the three primary stations' records into three blocks:
about 5.8 years to learn (2015 to mid-October 2020), one full year to decide when to stop training and where to set the alarm
threshold (mid-October 2020 to mid-October 2021), and about 3.2 years to grade (mid-October 2021 to end-2024). One full tuning year
covers every season once, including one typhoon season. <b>The exact calendar cutoff rationale was not preserved in the original
experiment records</b>: the code calls 2021-10-15 the "v12 canonical split" and gives no reason. A labelled present-day assessment is in
<a href="data/documentation/SPLIT_DESIGN_ASSESSMENT.md">SPLIT_DESIGN_ASSESSMENT.md</a>.</p>
<p>The split was not clean, though: training also used Port Area records up to 2023 and 19 extra stations up to 2024, the test years were
used to compare model versions and pick the scoring method, and nothing was saved from training (no learning curves, no seed).</p>
<h3>Academic wording</h3>
<p class="para">The primary-station records were partitioned chronologically to preserve temporal ordering and to approximate forecasting of
future conditions: target dates from 1 January 2015 to 14 October 2020 were used for training, 15 October 2020 to 14 October 2021 for early
stopping and threshold selection, and 15 October 2021 to 31 December 2024 for evaluation. The tuning block spans one complete annual cycle.
The exact calendar cutoff rationale was not preserved in the original experiment records. Training additionally included all Port Area records
(to 30 October 2023) and 69,388 supplementary rows (to 30 December 2024), so that records dated within the evaluation period contributed to
training at stations other than those evaluated. Because the evaluation period was also used to compare model variants and to choose the
scoring procedure, results on it are reported as retrospective rather than independent.</p>
<h3>Supplementary data provenance</h3>
<p><span class="tag hist">historical claim with saved record</span> {md_inline(fill(CLAIMS[19][2]))} Port Area belongs to the supplementary
group; the primary (evaluated) stations are NAIA, Sangley Point and Science Garden. Split facts and a labelled present-day assessment are in
<a href="data/documentation/SPLIT_DESIGN_ASSESSMENT.md">SPLIT_DESIGN_ASSESSMENT.md</a>. The exact calendar cutoff rationale was not preserved
in the original experiment records.</p>
""")

    # validation history
    vh = [
        ["Validation during training", "configured: <code>validation_data</code> = tuning block (<code>_train_w3.py</code> 876-890)", "no history or log saved", "cannot show learning curves"],
        ["Early stopping", "configured: <code>val_gale_prob_loss</code>, patience 12, best weights restored", "epoch 49 / best 37 stated in <code>THRESHOLD_CONFIG.md</code> only", "stopping point unverifiable"],
        ["Chronological holdout", "test block ≥ 2021-10-15", "saved scorecards; reproduced exactly (Cohort A)", "not independent (selection used it)"],
        ["Cross-validation of the network", "none", "—", "do not call the single split cross-validation"],
        ["Cross-validation for post-processing", "<code>TimeSeriesSplit</code> in <code>validate_model_multioutput.py:1075</code>", "inside the evaluation period", "regression metrics in the scorecard are post-processed"],
        ["Benchmark comparisons", "none for W1 before this evaluation", "MASE uses an in-sample lag-365 denominator", "added here (Cohort B)"],
        ["Prospective test (2025+)", "pre-registered for v12 (<code>pre_registration_6g.json</code>)", "no result found", "not executed"],
    ]
    cmp = [
        ["Generated", "2026-10-05 sync (W1+X1, commit <code>84d9ae3</code>)", "2026-07-02 (before W1 existed)"],
        ["Threshold", "0.601 on X1", "0.5834 (raw score)"],
        ["Event definition", "study label (wind ≥ 10.8 or Δp ≥ 3 hPa) for binary; OR-rule 3×3 matrix on other rows", "wind ≥ 17.2 m/s"],
        ["Cases", "3,423 (binary); 3,487 (3×3, includes cross-station windows)", "3,426 (from 2021-11-15); outcomes only TN/FP"],
        ["Model", "W1", "an earlier model"],
    ]
    sec("validation", "What validation already existed", f"""
{table(["Question", "Configured in code", "Proof of execution", "Consequence"], vh)}
<h3><code>validation_cm3.json</code> vs <code>validation_timeline.json</code></h3>
{table(["", "validation_cm3.json", "validation_timeline.json"], cmp)}
<p><span class="tag repo">repository fact</span> The two files have different provenance and must not be combined. Within <code>validation_cm3.json</code>
the binary scorecard and the 3×3 matrix also use different cases, labels and thresholds (AUDIT F-08). Its regression block includes
post-processing fitted in the evaluation period. {md_inline(fill(CLAIMS[17][2]))}</p>
<h3>Threshold provenance</h3>
<p><span class="tag hist">historical claim with saved record</span> {md_inline(fill(CLAIMS[9][2]))} {md_inline(fill(CLAIMS[10][2]))}</p>
""")

    # spec
    sec("design", "B. Benchmark design (declared before scoring)", f"""
<p>The full specification is <a href="data/EVAL_SPEC_v1.md">EVAL_SPEC_v1.md</a> (<a href="data/EVAL_SPEC_v1.json">JSON</a>), committed at
<code>{e(spec_commit)}</code> before any score. Amendment A1 (recorded before running it) added the legacy input construction to the variant comparison.</p>
<ul>
<li><b>Cohort A, legacy reproduction:</b> the historical procedure, as written, to test whether saved counts can be reproduced.</li>
<li><b>Cohort B, benchmark:</b> next-day target dates 2021-10-15 to 2024-12-31; three primary stations; inputs built as in training (per-station scalers, 32 days, no recency weights); truth from raw, unimputed observations; identical cases for every method.</li>
<li><b>Baselines:</b> wind persistence (today's wind), wind climatology (station × month mean, 2015-01-01 to 2020-10-14); event persistence (today's label), event climatology (station × month frequency over the same years; its classification threshold chosen on the tuning year only: {f(Bm['event_climatology_threshold']['threshold'], 4)}).</li>
<li><b>Thresholds (frozen):</b> W1 raw 0.64 (documented max-F1 on tuning); W1+X1 0.601 (adopted) and 0.62 (originally declared rule).</li>
<li><b>Uncertainty:</b> paired circular block bootstrap over target dates, 14-day blocks, 2,000 resamples, all stations of a date resampled together. A difference is "established" only if its 95% interval excludes zero.</li>
<li><b>Horizons:</b> next day only. W1 outputs 6 of its 36 inputs, so a 2- or 3-day forecast would need a new recursive procedure inventing 30 inputs; none is produced.</li>
</ul>
""")

    # results
    arows = [[k, "✔" if v else "✘"] for k, v in A["reproduction"].items()]
    wtab = []
    for sc in ["pooled", *C.PRIMARY]:
        bw = Bm["wind"][sc]
        for meth in ("W1", "persistence", "climatology"):
            p = bw["point"][meth]
            wtab.append([sc if meth == "W1" else "", meth, p["n"], f(p["mae"]), ci(bw["ci"][f"mae_{meth}"]), f(p["rmse"]), f(p["bias"], 3)])
    wdiff = []
    for sc in ["pooled", *C.PRIMARY]:
        bw = Bm["wind"][sc]["ci"]
        for k, lab in (("dmae_W1_persistence", "W1 − persistence"), ("dmae_W1_climatology", "W1 − climatology")):
            pt = Bm["wind"][sc]["point"]["W1"]["mae"] - Bm["wind"][sc]["point"][k.split("_")[-1]]["mae"]
            wdiff.append([sc, lab, f(pt), ci(bw[k]), e(bw[k]["verdict"].replace("positive", "W1 worse"))])
    etab = []
    for n, c in cls.items():
        etab.append([e(n), int(c["tp"]), int(c["fn"]), int(c["fp"]), int(c["tn"]), f(c["accuracy"], 4), f(c["precision"]),
                     ci(ep["ci"][f"precision_{n}"]), f(c["recall"]), ci(ep["ci"][f"recall_{n}"]), f(c["f1"]), ci(ep["ci"][f"f1_{n}"])])
    ptab = [[e(k), f(v["pr_auc"]), ci(ep["ci"].get(f"prauc_{k}")), f(v["brier"], 4), f(v["brier_skill_vs_climatology"], 2)]
            for k, v in ep["probabilistic"].items()]
    dtab = [[e(k), ci(v), e(v["verdict"])] for k, v in ep["ci"].items() if k.startswith("d")]
    stn = []
    for s in C.PRIMARY:
        c = Bm["events"][s]["classifiers"]["W1+X1@0.601"]; pp = Bm["events"][s]["classifiers"]["event_persistence"]
        stn.append([s, int(c["tp"] + c["fn"]), f"{int(c['tp'])}/{int(c['fp'])}/{int(c['fn'])}", f(c["f1"]),
                    f"{int(pp['tp'])}/{int(pp['fp'])}/{int(pp['fn'])}", f(Bm["events"][s]["probabilistic"]["W1+X1"]["pr_auc"])])
    yrs = [[y, d["wind"]["W1"]["n"], f(d["wind"]["W1"]["mae"]), f(d["wind"]["persistence"]["mae"]), f(d["wind"]["climatology"]["mae"]),
            d["events"]["events"], f"{int(d['events']['W1+X1@0.601']['tp'])}/{int(d['events']['W1+X1@0.601']['fp'])}",
            f"{int(d['events']['event_persistence']['tp'])}/{int(d['events']['event_persistence']['fp'])}"]
           for y, d in Bm["by_year"].items()]
    sn = Bm["S_NOIMPUTE"]
    dg = D1["configs"]
    sec("results", "B. Benchmark results (training-consistent inputs)", f"""
<h3>5.1 Cohort A: can the historical scorecard be reproduced?</h3>
<p><span class="tag new">new result</span> {md_inline(fill(CLAIMS[11][2]))} Neural-only next-day wind on those windows: MAE
{f(A['neural_only_wind_legacy_windows']['mae'])} m/s (the scorecard's 0.5365 includes post-processing fitted on the test period and is not reproduced).</p>
<details><summary>Reproduction checks (run <code>{ph['a']}</code>)</summary>{table(["Check", "Result"], arows)}</details>

<h3>5.2 Wind speed, next day (identical cases)</h3>
{table(["Scope", "Method", "n", "MAE m/s", "MAE 95% CI", "RMSE m/s", "Bias m/s"], wtab)}
{table(["Scope", "Difference in MAE", "Point", "95% CI", "Verdict"], wdiff)}
<figure><img src="figures/F2_wind_mae_by_station.png" alt="Bar chart: W1 wind MAE is higher than persistence and climatology at every station">
<figcaption><b>F2.</b> <b>Shows</b> mean absolute next-day wind error by station for W1, persistence and climatology. <b>Calculated</b> on {ph['wind_n']} identical cases; bars are block-bootstrap 95% intervals. <b>Matters</b> because a model must beat trivial forecasts to add value.
<b>Supports</b> that W1's wind output is less accurate than both references at every station. <b>Does not prove</b> anything about strong winds (none ≥ 10.8 m/s occurred) or about other output variables. Source: <a href="data/F2_wind_mae_by_station.csv">CSV</a>.</figcaption></figure>
<figure><img src="figures/F3_wind_monthly_means.png" alt="Monthly mean wind: W1 is almost flat near 2.5-2.7 m/s while observations vary; at Science Garden W1 is far above observations">
<figcaption><b>F3.</b> <b>Shows</b> monthly means of the daily observed wind and of each forecast, for every eligible date (no dates selected). <b>Calculated</b> by averaging daily values within each calendar month. <b>Matters</b> because it reveals the error's structure: W1 forecasts sit near 2.5 m/s at every station (forecast SD {ph['w1_sd']} vs observed {ph['obs_sd']} m/s) and are far too high at Science Garden.
<b>Supports</b> that W1 does not track seasonal or station differences in wind. <b>Does not prove</b> day-to-day skill or its absence (monthly averaging hides daily variation; the daily series is kept private). Source: <a href="data/wind_monthly_means_by_station.csv">CSV</a>.</figcaption></figure>
<figure><img src="figures/F4_wind_obs_vs_pred_counts.png" alt="Count table: W1 never forecasts below 2.25 m/s while observed winds range from 0 to above 6 m/s">
<figcaption><b>F4.</b> <b>Shows</b> how many cases fall in each observed-wind and W1-forecast bin. <b>Calculated</b> from all {ph['wind_n']} wind cases (total checked: {'✔' if figchk['F4_total_equals_wind_cases'] else '✘'}). <b>Matters</b> because a useful forecast puts most cases near the diagonal. <b>Supports</b> that W1's forecasts occupy a narrow band regardless of the observed wind. <b>Does not prove</b> why (the earlier audit points to the wind target's small share of the loss and per-station input scaling). Source: <a href="data/F4_wind_obs_vs_pred_counts.csv">CSV</a>.</figcaption></figure>

<h3>5.3 Events (study label: wind ≥ 10.8 m/s or pressure fall ≥ 3 hPa), identical cases</h3>
<p>{bc['event']['eligible']:,} cases, {ph['ev_n']} events (prevalence {f(x1['prevalence'], 4)}); every event is a pressure fall; no wind event; no gale-force day.</p>
{table(["Procedure", "Hits", "Misses", "False alarms", "Correct negatives", "Accuracy", "Precision", "95% CI", "Recall", "95% CI", "F1", "95% CI"], etab)}
{table(["Probabilistic score", "PR-AUC", "95% CI", "Brier", "Brier skill vs climatology"], ptab)}
<p class="small">PR-AUC with no skill equals the prevalence ({f(x1['prevalence'], 4)}). Brier skill below 0 means worse than climatology: W1's scores are not calibrated probabilities.</p>
{table(["Paired difference", "95% CI", "Verdict"], dtab)}
<p class="small">df1 = F1 difference (positive: W1 better); dprauc = PR-AUC difference (positive: W1 better); dbrier = Brier difference (positive: W1 <em>worse</em>).</p>
<h4>By station (W1+X1 at 0.601; hits/false alarms/misses)</h4>
{table(["Station", "Events", "W1+X1 H/FA/M", "W1+X1 F1", "Persistence H/FA/M", "W1+X1 PR-AUC"], stn)}
<figure><img src="figures/F6_confusion_matrices.png" alt="Five binary confusion matrices including correct negatives">
<figcaption><b>F6.</b> <b>Shows</b> 2×2 matrices (with correct negatives) for every procedure on the same {bc['event']['eligible']:,} cases. <b>Calculated</b> with the frozen thresholds listed in the benchmark design section; each matrix sums to the case count (checked). <b>Matters</b> because accuracy alone hides the trade-off between misses and false alarms. <b>Supports</b> comparing burdens: W1+X1 at 0.601 has the fewest false alarms and the most hits here. <b>Does not prove</b> detection of strong wind: every event is a pressure fall. Source: <a href="data/F6_confusion_matrices.csv">CSV</a>.</figcaption></figure>
<figure><img src="figures/F5_event_timeline_monthly.png" alt="Monthly hits, misses and false alarms per station; events cluster in typhoon seasons 2022-2024">
<figcaption><b>F5.</b> <b>Shows</b> hits and misses (above the axis) and false alarms (below) per station per month for W1+X1 at 0.601. <b>Calculated</b> from the same cases as F6; monthly totals equal the matrix (checked: {'✔' if figchk['F5_timeline_equals_confusion'] else '✘'}). Exact dates are kept private. <b>Matters</b> because events are clustered in a few storm months, so cases are not independent. <b>Supports</b> that results rest on a handful of episodes. <b>Does not prove</b> seasonal generalisation. Source: <a href="data/F5_event_timeline_monthly.csv">CSV</a>.</figcaption></figure>
<figure><img src="figures/F7_event_benchmarks.png" alt="F1 and PR-AUC with confidence intervals; W1+X1 above persistence and climatology, with wide intervals">
<figcaption><b>F7.</b> <b>Shows</b> F1 and PR-AUC with 95% block-bootstrap intervals. <b>Calculated</b> from the paired bootstrap described in the benchmark design section. <b>Matters</b> because 27 events give wide intervals. <b>Supports</b> that W1+X1 ranks pressure-fall days better than persistence and climatology (established). <b>Does not prove</b> a precise level of skill: the F1 interval for W1+X1 spans roughly 0.3 to 0.8. Source: <a href="data/F7_event_benchmarks.csv">CSV</a>.</figcaption></figure>

<h3>5.4 Declared sensitivities</h3>
<ul>
<li><b>S-LEGACY inputs</b> (pooled scaling, as in the historical scorecard) on the same cases: W1+X1 PR-AUC {ph['prauc_x1_leg']}; at 0.601: {int(Bm['S_LEGACY_classifier']['tp'])} hits, {int(Bm['S_LEGACY_classifier']['fp'])} false alarms, {int(Bm['S_LEGACY_classifier']['fn'])} misses. Wind MAE {f(wp['W1_legacy_inputs']['mae'])} m/s.</li>
<li><b>S-NOIMPUTE</b> (remove windows with imputed values): {sn['event_cases']:,} event cases, {sn['events']} events; W1+X1 at 0.601: {int(sn['W1+X1@0.601']['tp'])} hits, {int(sn['W1+X1@0.601']['fp'])} false alarms; wind MAE W1 {f(sn['wind']['W1']['mae'])}, persistence {f(sn['wind']['persistence']['mae'])}.</li>
</ul>
<h4>By target year (point estimates)</h4>
{table(["Year", "Wind n", "W1 MAE", "Persistence MAE", "Climatology MAE", "Events", "W1+X1 hits/FA", "Persistence hits/FA"], yrs)}
<h3>5.5 Post-hoc diagnostics (explain; select nothing)</h3>
<p><span class="tag new">new result</span> Swapping one input factor at a time (run <code>{ph['d1']}</code>): per-station vs pooled scaling changes W1+X1 PR-AUC from
{f(dg['scaling=station|flags=processed|cross=4']['pr_auc_x1'])} to {f(dg['scaling=pooled|flags=processed|cross=4']['pr_auc_x1'])}; cross-station columns and passthrough flags change nothing.
On W1's own training-period windows (run <code>{ph['d2']}</code>) per-station scaling fits better (raw PR-AUC {f(D2['results']['station|train_in_sample']['pr_auc_raw'])} vs {f(D2['results']['pooled|train_in_sample']['pr_auc_raw'])}), consistent with the code's statement that training used per-station scalers;
on the tuning year the order reverses ({f(D2['results']['station|early_stop']['pr_auc_raw'])} vs {f(D2['results']['pooled|early_stop']['pr_auc_raw'])}).</p>
<p><span class="tag interp">interpretation</span> One possible explanation, not established: every historical selection (W1 among its variants, X1, the threshold rule) was made on pooled-input scores over these same periods, which would favour whatever works best under pooled inputs. The mechanism has not been identified. Report both constructions; do not quote either alone.</p>
""")

    # model selection
    vt = []
    for v, r in V["variants"].items():
        if not r.get("scored"):
            continue
        st, lg = r["S-TRAIN"], r["S-LEGACY"]
        c = st["raw_at_documented_threshold"]
        vt.append([e(r["label"]), r["threshold_documented"], f(st["pr_auc_x1"]), f(lg["pr_auc_x1"]), f(st["pr_auc_raw"]),
                   f"{int(c['tp'])}/{int(c['fp'])}/{int(c['fn'])}", f(st["wind_mae"])])
    hist = [
        ["W1 (<code>_w3</code>)", "×3 negative weight; v12 split", "TEST X1 PR-AUC 0.8302 at the adopted rule", "selected; reasons in <code>THRESHOLD_CONFIG.md</code> cite TEST scores"],
        ["v12", "×1 (balanced); same split; same scalers as W1", "TEST raw PR-AUC 0.6916", "superseded by W1"],
        ["v11", "earlier recipe; early-stopped on the TEST period", "TEST raw PR-AUC 0.8034", "rejected as contaminated (documented)"],
        ["W2 (<code>_w6</code>), W3 (<code>_w10</code>)", "×6, ×10 negative weight", "TEST X1 PR-AUC 0.7168, 0.3565", "'rejected'; recorded evidence is TEST scores"],
        ["F1, F2", "focal-loss variants", "TEST X1 PR-AUC 0.6306, 0.7295", "not adopted; no reason recorded"],
        ["v13, v14", "different splits (60/40, 65/35)", "own test periods; PR-AUC 0.518, 0.523", "partition-sensitivity references"],
        ["x1f, x2f", "extra input features (not recorded)", "TEST X1 PR-AUC 0.7976, 0.4734", "not re-scored here (feature list unavailable)"],
    ]
    sec("selection", "Model selection: existing variants", f"""
<p>These are genuinely existing trained variants on <code>exp/precision-targeting</code>. All share W1's architecture (40,872 parameters); they differ in
training recipe, split or class weights, so they are <b>training variants, not different architectures</b>. Three random seeds would not count as three models, and no seeds exist here anyway.</p>
<h3>Historical record</h3>
{table(["Variant", "What differs", "Saved evidence", "Selection status"], hist)}
<h3>Re-scored on identical cases (inference only; own scalers; own documented threshold)</h3>
{table(["Variant", "Thr", "X1 PR-AUC (S-TRAIN)", "X1 PR-AUC (S-LEGACY)", "Raw PR-AUC (S-TRAIN)", "Raw H/FA/M at thr", "Wind MAE"], vt)}
<figure><img src="figures/F8_variants_and_inputs.png" alt="Dot plots: variants' X1 PR-AUC under two input constructions, and wind MAE all far above persistence">
<figcaption><b>F8.</b> <b>Shows</b> each variant's X1 PR-AUC under both input constructions and its wind MAE. <b>Calculated</b> on the same cases as the benchmark results. <b>Matters</b> because a selection is only meaningful on identical cases. <b>Supports</b> three statements: no variant beats persistence or climatology on wind; W1 is not the top event ranker under either construction (v11, rejected for contamination, scores highest); and rankings change with the input construction.
<b>Does not prove</b> that any variant would do better in future: this period informed all of them. Source: <a href="data/F8_variants_and_inputs.csv">CSV</a>.</figcaption></figure>
<p><span class="tag interp">interpretation</span> The recorded reason for choosing W1 is its TEST-period scorecard after X1 and the recall-floor rule. W1 should not be described as
superior because it is deployed. A defensible statement is: "W1 was selected from training variants using test-period scores; on a re-evaluation with identical cases, its ranking among variants depends on input scaling."</p>
""")

    # defense
    allneg = x1["all_negative_accuracy"]
    D = [
        ("Why can accuracy be high when many cases are negative?",
         f"If almost every day is a non-event, a forecast that always says 'no event' is almost always right. Here, {bc['event']['eligible']:,} cases include only {ph['ev_n']} events, so always saying 'no' scores {allneg*100:.2f}% accuracy while catching nothing.",
         f"With an event prevalence of {x1['prevalence']*100:.2f}%, the trivial all-negative forecast attains {allneg*100:.2f}% accuracy; accuracy is therefore dominated by correct negatives and is uninformative about detection. Precision, recall and PR-AUC, which exclude correct negatives, are reported instead."),
        ("What does precision measure?",
         f"Of the alarms raised, how many were real? W1+X1 at 0.601 raised {int(x1['tp']+x1['fp'])} alarms; {int(x1['tp'])} were real, so precision is {x1['precision']*100:.1f}%. Low precision means users chase false alarms.",
         "Precision, TP/(TP+FP), quantifies the false-alarm burden: the share of issued warnings that correspond to an observed event."),
        ("What does recall measure?",
         f"Of the real events, how many were caught? {int(x1['tp'])} of {ph['ev_n']}, so recall is {x1['recall']*100:.1f}%; {int(x1['fn'])} were missed.",
         "Recall, TP/(TP+FN), quantifies the missed-event burden. Where a missed hazard is costly, recall deserves weight, but raising it generally increases false alarms; the acceptable balance is a stakeholder decision that this study has not elicited."),
        ("Why is F1 alone not enough?",
         "F1 averages precision and recall into one number, so very different trade-offs can share an F1. It also ignores correct negatives, lead time, how bad each miss is, and whether the event matters to users.",
         "The F1 score weights precision and recall equally and is insensitive to correct negatives and to the relative costs of errors; it cannot by itself establish the adequacy of a warning system, which requires explicit, user-defined costs and prospective verification."),
        ("Why can better wind MAE fail to improve event detection?",
         f"MAE is an average over all days, dominated by ordinary calm days. The events here are pressure falls, not windy days, so even a perfect wind forecast would not detect them. W1's wind error ({ph['w1_mae']} m/s) is poor while its pressure-fall ranking is better than baselines: the two are separate tasks.",
         "Lower MAE indicates smaller average numerical error on the same cases; it does not imply better discrimination of rare events, which depends on the tail of the distribution and, here, on a pressure-based label unrelated to the wind output."),
        ("Does low or falling pressure prove strong wind?",
         "No. A pressure fall shows the atmosphere is changing, often near a storm, but whether strong wind arrives at a station depends on distance, track and local exposure. In 2021-2024 all 27 events were pressure falls of ≥ 3 hPa, yet no day reached 10.8 m/s.",
         "The study label is satisfied by a 24-hour pressure fall of at least 3 hPa; it is a meteorological risk indicator, not evidence of gale-force wind. Low absolute pressure (an input flag) and pressure tendency (the label) are also distinct quantities."),
        ("Why compare with baselines?",
         f"Without a baseline, a number like 'MAE 1.02 m/s' sounds small. Saying 'tomorrow = today' gives {ph['pe_mae']} m/s on the same days, so the model is worse than doing nothing clever.",
         "Skill is defined relative to a reference forecast evaluated on identical cases. Persistence and climatology are the standard minimal references in forecast verification; a model that does not outperform them provides no demonstrated forecast value for that quantity."),
    ]
    dhtml = "".join(f"<details open><summary>{e(q)}</summary><p><b>Simple:</b> {e(s)}</p><p class='para'><b>Academic:</b> {e(a)}</p></details>" for q, s, a in D)
    sec("defense", "Defense explanations", dhtml)

    paras = [
        ("P-1 Methods: evaluation design", f"The frozen deployed model (W1; SHA-256 f2db5aa9…9d14b0) was evaluated retrospectively without retraining or recalibration. For each of the three primary stations and each target date from 15 October 2021 to 31 December 2024, a next-day forecast was issued from the 32 preceding daily records, scaled with the station-specific scalers used in training. Forecasts were compared with two reference forecasts on identical cases: persistence (the latest observation) and climatology (station-by-month means from 2015 to 14 October 2020). Wind speed was verified against unimputed observations using MAE, RMSE and bias; events under the study label (wind ≥ 10.8 m/s or a 24-hour pressure fall ≥ 3 hPa) were verified with contingency-table measures and PR-AUC. Uncertainty was estimated with a paired circular block bootstrap over dates (14-day blocks, 2,000 resamples). The evaluation specification was fixed before scoring."),
        ("P-2 Results: wind", f"On {ph['wind_n']} identical cases, W1's next-day wind forecasts had an MAE of {ph['w1_mae']} m/s, compared with {ph['pe_mae']} m/s for persistence and {ph['cl_mae']} m/s for climatology; both differences were statistically established. The model's forecasts varied little (standard deviation {ph['w1_sd']} m/s against {ph['obs_sd']} m/s observed). Lower MAE indicates a smaller average numerical error on the same cases; on this measure W1 provides no improvement over simple references, and the result says nothing about gale-force winds, none of which occurred."),
        ("P-3 Results: events", f"The evaluation period contained {ph['ev_n']} hazard-label events, all defined by pressure falls. With cross-station averaging and the adopted threshold of 0.601, W1 detected {ph['x1_tp']} events with {ph['x1_fp']} false alarms (precision {ph['x1_p']}, recall {ph['x1_r']}, F1 {ph['x1_f1']}), outperforming event persistence (F1 {ph['pe_f1']}); its PR-AUC was {ph['prauc_x1_train']} against a prevalence of {f(x1['prevalence'], 4)}. Its scores were not calibrated (Brier skill relative to climatology {ph['bss_x1']}). When inputs were scaled as in the historical scorecard, the same procedure reproduced the previously reported PR-AUC of 0.830, showing that the reported performance depends strongly on input preprocessing."),
        ("P-4 Limitations", "The evaluation period was used historically to compare model variants and to choose the scoring procedure, and training included records from other stations dated within it; results are therefore retrospective rather than independent. The event sample is small and consists entirely of pressure falls, so no conclusion about gale-force wind detection is possible. No training history or random seed was preserved, so training cannot be reproduced. Only next-day forecasts were assessed. A prospective evaluation on observations from 2025 onward is required before any operational claim."),
    ]
    sec("paragraphs", "Paper-ready paragraphs", "".join(f"<h3>{e(t)}</h3><p class='para'>{e(p)}</p>" for t, p in paras))

    # ledger
    lh = []
    for ch in range(1, 6):
        rows = [[e(r[0]), md_inline(r[2]), md_inline(r[3]), f'<span class="v v{r[4][:2].lower().replace(" ", "")}">{e(r[4])}</span>',
                 md_inline(fill(r[5])), md_inline(fill(r[6])) or "—"] for r in REV if r[1] == ch]
        lh.append(f"<h3>Chapter {ch}</h3>" + table(["#", "Section", "Short claim", "Verdict", "Evidence", "Full replacement text"], rows, "ledger"))
    om = "".join(f"<li><code>{i}</code> {e(t)}</li>" for i, t in OMISSIONS)
    exact = [[e(r["id"]), f"Ch {r['chapter']}, {e(r['heading'])}, PDF p. {r['pdf_page']}", f"<q>{e(r['find_text'])}</q>", md_inline(r["replacement"]),
              e(r["reason"]), md_inline(r["evidence"])] for r in LED]
    nfound = sum(r["find_check"] == "found" for r in LED)
    sec("ledger", "Paper revisions: exact find-and-replace ledger", f"""
<p>Chapters 1-5 exist only as PDFs (2026-10-23; versions in <a href="data/documentation/SOURCE_DOCUMENTS.md">SOURCE_DOCUMENTS.md</a>), so every entry is
<b>proposed only</b>; no chapter file was edited. Each find text was checked against the PDFs ({nfound} of {len(LED)} found); "PDF p." is the page
index within that chapter's PDF. Only short excerpts are quoted. Download: <a href="data/documentation/PAPER_REVISION_LEDGER.md">Markdown</a>,
<a href="data/documentation/paper_revision_ledger.csv">CSV</a>.</p>
{table(["ID", "Location", "Find (exact)", "Replace with", "Reason", "Evidence"], exact, "ledger")}
<details><summary>Earlier chapter review notes (2026-10-24; background; this ledger governs where they differ)</summary>
<p>Verdicts: Correct, Partly correct, Wrong, Not found in the code. Literature claims in Chapter 2 were not checked.
Download: <a href="data/revision_ledger.csv">CSV</a>, <a href="data/revisions.json">JSON</a>.</p>{''.join(lh)}<h3>Important omissions</h3><ul>{om}</ul></details>""")

    figs = sorted((X["runs"]["pf"] / "figures").glob("PF-*.png"))
    frows = [[e(p.stem), f'<a href="figures/paper/{p.name}">PNG</a> · <a href="figures/paper/{p.stem}.svg">SVG</a> · <a href="figures/paper/{p.stem}.csv">CSV</a>',
              next((g["evidence_group"] for g in X["pf"]["figures"] if g["figure"] == p.stem), "")] for p in figs]
    sec("figures", "Figures for the paper (downloads)", f"""
<p>Individually downloadable figures, PNG at 300 DPI and SVG, with the CSV of the plotted numbers. Each figure states its model and processing,
variable and units, stations, dates, sample size, forecast lead, baselines and evidence group. Captions, cohorts and source runs:
<a href="data/documentation/FIGURE_GUIDE.md">FIGURE_GUIDE.md</a>. Figure run <code>{PH['run_pf']}</code>.</p>
{table(["Figure", "Download", "Evidence group"], frows)}
<p class="small">Selected case figures (PF-H per station, PF-I all stations) are private: they plot individual PAGASA readings. They are not available here.</p>
""")

    sec("method", 'What "validation" means in this paper', f"""
<p>The evaluation is a <b>retrospective forecast verification with persistence and climatology benchmarking</b>. The three-day examples are
<b>retrospectively selected illustrative case studies</b>.</p>
<ul>
<li><b>Chronological partitioning</b> describes how the data were divided (training, tuning, evaluation, in time order).</li>
<li><b>Retrospective verification</b> means checking the frozen model's past next-day forecasts against what was recorded.</li>
<li><b>Baseline benchmarking</b> compares the model with reference forecasts (persistence, climatology) on exactly the same cases.</li>
<li><b>Selected case studies</b> explain behaviour on specific dates and are not performance estimates.</li>
</ul>
<p>None of these is cross-validation. No k-fold, rolling-origin or walk-forward cross-validation of the network was executed, and replaying a
frozen model day by day over a past period is not cross-validation. Full method: <a href="data/documentation/EVALUATION_METHOD.md">EVALUATION_METHOD.md</a>;
W1 identity, split and data status: <a href="data/documentation/MODEL_AND_DATA_SUMMARY.md">MODEL_AND_DATA_SUMMARY.md</a>.</p>
<h3>Reading the numbers</h3>
<ul>
<li>Lower MAE/RMSE means smaller numerical error on the matching cases only.</li>
<li>Mean signed error (bias) shows systematic over- or under-forecasting; positive and negative errors can cancel.</li>
<li>Better average error does not establish better event detection, and vice versa.</li>
<li>Three selected dates cannot establish general forecasting superiority.</li>
<li>MASE below one compares with an in-sample naïve error from training data; it does not prove a win against a same-case test baseline.</li>
</ul>
<h3>References</h3>
<ul>{''.join(f'<li>{md_inline(t.replace("*", ""))} <a href="{u}">{u}</a><br><span class="small">{e(n)}</span></li>' for t, u, n in build_docs.REFS)}</ul>
""")

    sec("credits", "Credits", f"""
<table><thead><tr><th>Person / account</th><th>Role (from repository evidence)</th></tr></thead><tbody>
<tr><td>Courtney (<a href="https://github.com/miaoxiizumi-gif">miaoxiizumi-gif</a>)</td><td>repository owner; author of every commit in this repository</td></tr>
<tr><td>Christine Tamayo (<a href="https://github.com/Tinenen-cs">Tinenen-cs</a>)</td><td>front-end contributor to the GALE-CAST application repository (its commit history); not a contributor to this repository</td></tr>
</tbody></table>
<p class="small">Other thesis-team members and the thesis authorship list are not recorded in either repository and await confirmation.
AI tool use is disclosed separately from authorship: commits here carry a <code>Co-Authored-By: Claude</code> trailer recording assistance
by an AI coding tool, which is not a human author. PAGASA is the source of the station observations.</p>
""")

    lim = "".join(f"<li><code>{i}</code> {e(t)}</li>" for i, t in LIMITS)
    sec("limits", "Limitations and unresolved issues", f"<ul>{lim}</ul>")

    cl = "".join(f'<tr><td><code>{i}</code></td><td><span class="tag {k}">{k}</span></td><td>{md_inline(fill(t))}</td><td>{md_inline(fill(ev))}</td></tr>'
                 for i, k, t, ev in CLAIMS)
    sec("claims", "Claims register", f'<div class="tw"><table><thead><tr><th>ID</th><th>Class</th><th>Claim</th><th>Evidence</th></tr></thead><tbody>{cl}</tbody></table></div>')

    runlist = "".join(f"<li><code>{e(k)}</code>: <code>{e(v.name)}</code></li>" for k, v in runs.items())
    sec("repro", "Reproducibility and sources", f"""
<p>Source repository: the GALE-CAST project at <code>1f2d5dd</code> (private); W1 provenance on branch <code>exp/precision-targeting</code>
(<code>experiments/w1x1/_train_w3.py</code>, <code>_w1_recall_floor.py</code>, <code>THRESHOLD_CONFIG.md</code>). Evaluation code and aggregate run outputs:
<a href="{REPO_URL}">{REPO_URL}</a> (folders <code>eval/</code>, <code>spec/</code>, <code>runs/</code>).</p>
<pre>python -m venv (Python 3.11.9, tensorflow-cpu 2.16.1, keras 3.13.2, numpy 1.26.4, pandas 2.2.2, scikit-learn 1.7.2)
cd eval
python stage1_identity.py      # identity, signature, 24-step check
python stage2_partitions.py    # split reconstruction and counts
python stage2b_supplementary.py
python cohort_a_legacy.py      # legacy reproduction
python benchmark.py            # Cohort B
python variants.py             # Stage 7
python diag_inputs.py; python diag_insample.py   # post-hoc diagnostics
python figures.py
# amendment A2 (spec/AMENDMENT_A2_website_cohort.md, spec/CASE_SELECTION_v1.md)
python website_cohort.py; python regression_provenance.py; python split_facts.py
python case_studies.py         # private case figures -> _private/thesis_export/
python paper_figures.py; python build_site.py</pre>
<p>Requires the private raw file and the source checkout (paths in <code>eval/common.py</code>). Each run writes a manifest with code, data and artifact hashes. Runs used for this page:</p>
<ul>{runlist}</ul>
<p>Machine-readable files: <a href="data/claims.json">claims.json</a>, <a href="data/metrics.json">metrics.json</a>, <a href="data/revisions.json">revisions.json</a>,
<a href="data/wind_results.csv">wind_results.csv</a>, <a href="data/event_results.csv">event_results.csv</a>, <a href="data/variants_results.csv">variants_results.csv</a>.
No row-level observations or individual predictions are published.</p>
""")

    ORDER = ["overview", "identity", "scorecard", "design", "results", "regression", "cases", "method", "data", "validation",
             "selection", "figures", "ledger", "paragraphs", "defense", "limits", "claims", "credits", "repro"]
    assert sorted(ORDER) == sorted(SECS), set(ORDER) ^ set(SECS)
    for n, id_ in enumerate(ORDER):
        title, body = SECS[id_]
        nav.append((id_, title))
        S.append(f'<section id="{id_}"><h2>{"" if n == 0 else f"{n}. "}{e(title)}</h2>{body}</section>')
    navh = "".join(f'<a href="#{i}">{e(t)}</a>' for i, t in nav)
    built = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GALE-CAST W1 Evaluation</title><meta name="description" content="Retrospective forecast verification of the frozen GALE-CAST W1 model with persistence and climatology benchmarks: the website scorecard case by case, regression provenance, selected case studies, paper figures and revision ledger.">
<link rel="stylesheet" href="style.css"></head><body>
<header><div class="wrap"><h1>GALE-CAST W1: retrospective forecast verification</h1>
<p class="sub">Evaluation <code>{EVAL_ID}</code> + amendment A2 · built {built} · provisional · <a href="{REPO_URL}">repository</a></p></div></header>
<nav><div class="wrap">{navh}</div></nav><main class="wrap">{''.join(S)}</main>
<footer><div class="wrap">Aggregate results only; no individual station-day readings are published. PAGASA is the source of the station observations. Maintained by Courtney (miaoxiizumi-gif); see Credits. Generated by <code>eval/build_site.py</code>.</div></footer>
</body></html>"""
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    # markdown report
    md = [f"# GALE-CAST W1 evaluation `{EVAL_ID}` + amendment A2 (provisional)\n", f"Site: {SITE_URL}\n",
          "Method: retrospective forecast verification with persistence and climatology benchmarking (not cross-validation). "
          "Evidence groups: A = website historical scorecard (3,423 cases); B = training-consistent benchmark; C = retrospectively "
          "selected illustrative case studies (private figures). Documents: documentation/*.md in the repository.\n",
          "## Evidence A: website scorecard with same-case baselines\n",
          "| Procedure | TP | FN | FP | TN | Precision | Recall | F1 |", "|---|---|---|---|---|---|---|---|"]
    md += [f"| {k} | {int(c['tp'])} | {int(c['fn'])} | {int(c['fp'])} | {int(c['tn'])} | {f(c['precision'])} | {f(c['recall'])} | {f(c['f1'])} |"
           for k, c in WA["events"]["pooled"]["classifiers"].items()]
    md += ["\n| Variable (raw truth) | n | W1 MAE | Persistence MAE | Climatology MAE |", "|---|---|---|---|---|"]
    md += [f"| {v} ({r['unit']}) | {r['n_common']:,} | {f(r['scopes']['pooled']['point']['W1']['mae'])} | "
           f"{f(r['scopes']['pooled']['point']['persistence']['mae'])} | {f(r['scopes']['pooled']['point']['climatology']['mae'])} |"
           for v, r in WA["regression"].items()]
    md += [f"\nWebsite regression block reproduced exactly from W1 + MOS + persistence blend fitted on the evaluation period "
           f"(run {PH['run_rp']}); neural-only wind MAE {RPv['steps']['neural_only']['mae']:.3f} m/s.\n", "## Claims\n"]
    md += [f"- **{c['id']}** ({c['class']}): {c['claim']}  \n  Evidence: {c['evidence']}" for c in claims_j]
    md += ["\n## Limitations\n"] + [f"- **{i}** {t}" for i, t in LIMITS]
    md += ["\n## Paper-ready paragraphs\n"] + [f"### {t}\n\n{p}\n" for t, p in paras]
    md += ["\n## Paper revision ledger (exact find and replace; proposed only)\n",
           "| ID | Location | Find | Replace with | Reason |", "|---|---|---|---|---|"]
    md += [f"| {r['id']} | Ch {r['chapter']}, {r['heading']}, PDF p. {r['pdf_page']} | \"{r['find_text']}\" | {r['replacement']} | {r['reason']} |"
           for r in LED]
    md += ["\n## Earlier chapter review notes (background)\n", "| # | Ch | Section | Claim | Verdict | Evidence | Replacement |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['id']} | {r['chapter']} | {r['section']} | {r['claim']} | {r['verdict']} | {r['evidence']} | {r['replacement'] or '—'} |" for r in rev_j]
    (DOCS / "data" / "REPORT.md").write_text("\n".join(md), encoding="utf-8")

    # publication safety scan
    bad = []
    for p in DOCS.rglob("*"):
        if p.is_file() and p.suffix in (".html", ".md", ".json", ".csv", ".css"):
            t = p.read_text(encoding="utf-8")
            for pat in ("GALECAST@", "postgresql://", "C:\\Users", "VAPID", "ADMIN_API_KEY="):
                if pat in t:
                    bad.append((p.name, pat))
    assert not bad, f"publication scan failed: {bad}"
    print("site built:", DOCS, "| sections:", len(nav), "| revisions:", len(rev_j))


CSS = """:root{--bg:#fcfcfb;--panel:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3df;--accent:#2a78d6;--soft:#f3f2ee;
--ok:#0f7a3a;--warn:#9a6200;--bad:#b42318;--nf:#5b4bc4;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1a1a19;--panel:#222221;--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3a37;--accent:#3987e5;--soft:#2a2a28;--ok:#5ccf8a;--warn:#e0b04e;--bad:#f08b80;--nf:#a99ef2;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#1a1a19;--panel:#222221;--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3a37;--accent:#3987e5;--soft:#2a2a28;--ok:#5ccf8a;--warn:#e0b04e;--bad:#f08b80;--nf:#a99ef2;color-scheme:dark}
*{box-sizing:border-box}main,section,figure,.card,p,li,td,th,summary{min-width:0;overflow-wrap:anywhere}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}header{border-bottom:1px solid var(--line);padding:24px 0 12px}h1{font-size:1.6rem;margin:0 0 4px;line-height:1.25}
.sub{color:var(--ink2);margin:0}nav{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);z-index:5}
nav .wrap{display:flex;gap:14px;overflow-x:auto;padding:8px 16px;white-space:nowrap}nav a{color:var(--ink2);text-decoration:none;font-size:.9rem}nav a:hover{color:var(--accent)}
section{padding:28px 0;border-bottom:1px solid var(--line)}h2{font-size:1.35rem;margin:0 0 12px}h3{font-size:1.1rem;margin:22px 0 8px}h4{margin:16px 0 6px}
a{color:var(--accent)}code{background:var(--soft);padding:1px 4px;border-radius:4px;font-size:.88em;overflow-wrap:anywhere}
.lead{font-size:1.08rem}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:16px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}.card .k{color:var(--ink2);font-size:.85rem}.card .v{font-size:1.7rem;font-weight:650}.card .s{font-size:.9rem;color:var(--ink2)}
.tw{overflow-x:auto;margin:10px 0;border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;font-size:.88rem;background:var(--panel)}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--soft);font-weight:600;position:sticky;top:0}
table.ledger td:nth-child(3){min-width:180px}table.ledger td:nth-child(5){min-width:240px}table.ledger td:nth-child(6){min-width:300px}
figure{margin:18px 0;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}img{max-width:100%;height:auto;display:block;background:#fcfcfb;border-radius:6px}
figcaption{font-size:.9rem;color:var(--ink2);margin-top:8px}.small,.note{font-size:.88rem;color:var(--ink2)}.para{background:var(--soft);border-left:3px solid var(--accent);padding:10px 14px;border-radius:4px}
details{margin:8px 0}summary{cursor:pointer;font-weight:600}ul.cols{columns:2}@media(max-width:640px){ul.cols{columns:1}h1{font-size:1.3rem}}
.tag{display:inline-block;font-size:.72rem;padding:1px 7px;border-radius:999px;border:1px solid var(--line);margin-right:4px;white-space:nowrap}
.tag.repo{color:var(--accent)}.tag.hist{color:var(--warn)}.tag.new{color:var(--ok)}.tag.interp{color:var(--nf)}
.v{font-weight:600;white-space:nowrap}.vco{color:var(--ok)}.vpa{color:var(--warn)}.vwr{color:var(--bad)}.vno{color:var(--nf)}
pre{background:var(--soft);padding:12px;border-radius:8px;overflow-x:auto;font-size:.85rem}footer{padding:24px 0;color:var(--ink2);font-size:.85rem}
.card.good{border-left:4px solid var(--ok)}.card.bad{border-left:4px solid var(--bad)}.tag.sel{color:var(--warn);border-color:var(--warn);font-weight:600}
.groups{display:grid;gap:6px;margin:12px 0;font-size:.92rem}.selected{border:2px dashed var(--warn);border-radius:10px;padding:4px 16px;background:var(--panel)}
q{font-style:italic}q::before,q::after{content:'"'}
"""

if __name__ == "__main__":
    main()
