"""Amendment A2 §4: trace the website's regression block (validate_model_multioutput.py @ W1 commit 1fd1ef9).

Ports only the wind-speed path of that script, as written (lines 1066-1205, 1836-1850, 315-370):
neural wind -> per-station x per-season linear+isotonic MOS (8-fold TimeSeriesSplit over the EVALUATION rows)
-> model/lag-1 persistence blend with weight chosen by 5-fold TimeSeriesSplit MAE on the EVALUATION rows.
Provenance check only: the result is not a W1 result.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression as _ISO
from sklearn.linear_model import LinearRegression as _LR
from sklearn.model_selection import TimeSeriesSplit as _TSS

import common as C
import metrics as M

WEBSITE = {"mae": 0.5365, "rmse": 0.7723, "mase": 0.6782}  # validation_cm3.json regression_metrics.wind_speed


def latest(prefix):
    return sorted(p for p in C.RUNS.glob(f"{prefix}-*") if not (p / "FAILED.txt").exists())[-1]


def _mos_calibrate(pred, true, n_splits=8):  # verbatim logic, validate_model_multioutput.py@1fd1ef9 lines 1066-1090
    cal = np.empty_like(pred, dtype=float)
    for tr, te in _TSS(n_splits=n_splits).split(pred):
        lr = _LR().fit(pred[tr].reshape(-1, 1), true[tr])
        iso = _ISO(out_of_bounds="clip").fit(lr.predict(pred[tr].reshape(-1, 1)), true[tr])
        cal[te] = iso.predict(lr.predict(pred[te].reshape(-1, 1)))
    covered = np.zeros(len(pred), dtype=bool)
    for _, te in _TSS(n_splits=n_splits).split(pred):
        covered[te] = True
    if (~covered).any() and covered.sum() > 10:
        lr = _LR().fit(pred[covered].reshape(-1, 1), true[covered])
        iso = _ISO(out_of_bounds="clip").fit(lr.predict(pred[covered].reshape(-1, 1)), true[covered])
        cal[~covered] = iso.predict(lr.predict(pred[~covered].reshape(-1, 1)))
    return cal, covered


def mase_denominator() -> float:
    """Lines 334-365: lag-365 positional seasonal-naive MAE, processed rows dated < 2021-10-15, every station."""
    p = C.load_processed()
    p = p[p["date"] < "2021-10-15"]
    diffs = []
    for _, g in p.groupby("station_name"):
        v = g.sort_values("date")["wind_speed"].values.astype(float)
        if (~np.isnan(v)).sum() < 366:
            continue
        a, b = v[365:], v[:-365]
        ok = ~np.isnan(a) & ~np.isnan(b)
        diffs.extend(np.abs(a[ok] - b[ok]).tolist())
    return float(np.mean(diffs))


def main():
    run = C.new_run("reg-prov")
    src = latest("w-cohort")
    W = pd.read_csv(C.private_dir(src) / "website_cohort_rows.csv", parse_dates=["date", "issue_date"])
    W = W.sort_values(["station", "date"]).reset_index(drop=True)  # = valid_mask order (station, date)
    pred = W["W1_wind"].values.astype(float).copy()
    true = W["proc_wind_d"].values.astype(float)       # processed_weather wind of the target day
    pers = W["proc_wind_t"].values.astype(float)       # processed wind of the issue day t (true lag-1 of the target)
    # The script's "lag-1" reads y_reg_true_raw[seq_length - 2 + i] (line 1177) = row i+30 = day t-1, while the
    # target is row i+32 (= t+1, line 448): its blend partner is a two-day-old observation. Reproduced as written.
    pw = C.load_processed().set_index(["station_name", "date"])["wind_speed"]
    lag_script = pw.reindex(pd.MultiIndex.from_arrays([W["station"], W["issue_date"] - pd.Timedelta(days=1)])).values.astype(float)
    wet = W["issue_date"].dt.month.isin([6, 7, 8, 9, 10, 11]).values  # season of the window's last row (line 1160)

    steps = {"neural_only": M.wind_stats(pred - true)}
    fallback_rows = 0
    for s in C.PRIMARY:
        for is_wet in (True, False):
            m = (W["station"].values == s) & (wet if is_wet else ~wet)
            if m.sum() > 20:
                cal, cov = _mos_calibrate(pred[m], true[m])
                pred[m] = np.maximum(cal, 0.0)
                fallback_rows += int((~cov).sum())
    steps["after_mos"] = M.wind_stats(pred - true)

    best_a, best = 0.0, np.inf
    for a in np.linspace(0.0, 1.0, 21):
        cv = [np.mean(np.abs(a * pred[te] + (1 - a) * lag_script[te] - true[te])) for _, te in _TSS(n_splits=5).split(pred)]
        if np.mean(cv) < best:
            best, best_a = float(np.mean(cv)), float(a)
    final = np.maximum(best_a * pred + (1 - best_a) * lag_script, 0.0)
    steps["after_blend"] = M.wind_stats(final - true)
    steps["persistence_same_cases_same_truth"] = M.wind_stats(pers - true)
    steps["script_blend_partner_two_day_old_obs"] = M.wind_stats(lag_script - true)
    denom = mase_denominator()
    res = {
        "run_id": run.name, "amendment": "A2 §4", "source_rows_run": src.name, "n": int(len(W)),
        "truth": "processed_weather.wind_speed of the target day (forward-filled), as in the website script",
        "steps": steps, "blend_weight_on_model": best_a, "blend_cv_mae": best,
        "blend_partner": "processed wind of day t-1 (two days before the target), as indexed by the script",
        "mos_rows_from_fallback_fit_on_later_evaluation_rows": fallback_rows,
        "mase_denominator_lag365_train": denom, "mase_after_blend": steps["after_blend"]["mae"] / denom,
        "mase_neural_only": steps["neural_only"]["mae"] / denom,
        "website_values": WEBSITE,
        "reproduces_website": {k: abs(round(v, 4) - WEBSITE[k]) < 1e-4 for k, v in
                               {"mae": steps["after_blend"]["mae"], "rmse": steps["after_blend"]["rmse"],
                                "mase": steps["after_blend"]["mae"] / denom}.items()},
        "fitted_on_evaluation_outcomes": {"mos": True, "blend_weight": True},
    }
    (run / "regression_provenance.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": "regression provenance check (amendment A2 §4)", "spec": "GCV-W1-v1 + A2"})
    print(json.dumps(res, indent=1))
    print(run)


if __name__ == "__main__":
    main()
