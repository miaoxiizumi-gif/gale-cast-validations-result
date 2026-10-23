"""POST-HOC DIAGNOSTIC (not in the declared spec; selects nothing).

Explains why the two declared input constructions (S-TRAIN vs S-LEGACY) give very different event
scores on identical Cohort B cases, by swapping one factor at a time:
  scaling   : per-station W1 scalers (training)   vs pooled scaled_weather values (legacy)
  passthrough flags (heavy_rain_flag, low_pressure_flag, storm_signal): processed vs scaled_weather
  cross-station lag columns: 4 stations (training) vs 3 stations with Port Area zeroed (legacy)
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

import cohort_b as B
import common as C
import metrics as M

FLAGS = ["heavy_rain_flag", "low_pressure_flag", "storm_signal"]


def frame(scaling: str, flags: str, cross: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    pw = C.load_processed()
    sw = C.load_scaled()
    if cross == "4":
        base = C.add_cross_station(pw)
    else:
        base = C.add_cross_station(pw[pw["station_name"].isin(C.PRIMARY)])
    base = base[base["station_name"].isin(C.PRIMARY)].reset_index(drop=True)
    swk = sw.set_index(["station_name", "date"])
    key = pd.MultiIndex.from_arrays([base["station_name"], base["date"]])
    if flags == "scaled":
        for f in FLAGS:
            base[f] = swk[f].reindex(key).values
    if scaling == "station":
        Xn = C.apply_station_scalers(base, joblib.load(C.SCALER_N), C.COLS_SCALE_N, C.FEATURES_NORMAL)
        Xa = C.apply_station_scalers(base, joblib.load(C.SCALER_A), C.COLS_SCALE_A, C.FEATURES_ANOMALY)
    else:
        b2 = base.copy()
        for c in set(C.COLS_SCALE_N) | set(C.COLS_SCALE_A):
            b2[c] = swk[c].reindex(key).values
        Xn, Xa = b2[C.FEATURES_NORMAL].values, b2[C.FEATURES_ANOMALY].values
    return base, Xn.astype(np.float32), Xa.astype(np.float32)


def main():
    run = C.new_run("diag-inputs")
    rows = pd.read_csv(C.PRIVATE / "runs" / sorted(p.name for p in (C.PRIVATE / "runs").glob("b-benchmark-*"))[-1]
                       / "cohort_b_rows.csv", parse_dates=["date"])
    E = rows[rows["elig_event"]][["station", "date", "E"]]
    model = C.load_frozen_model()
    sy = joblib.load(C.SCALER_Y)
    out = {"run_id": run.name, "label": "post-hoc diagnostic; selects nothing", "configs": {}}
    for scaling in ("station", "pooled"):
        for flags in ("processed", "scaled"):
            for cross in ("4", "3"):
                base, Xn, Xa = frame(scaling, flags, cross)
                wi = B.window_index(base)
                p, w = B.predict(model, Xn, Xa, wi["start"].values, sy)
                wi["p"] = p
                wi["x1"] = wi.groupby("date")["p"].transform("mean")
                m = E.merge(wi, on=["station", "date"], how="left")
                y = m["E"].values.astype(int)
                name = f"scaling={scaling}|flags={flags}|cross={cross}"
                out["configs"][name] = {
                    "pr_auc_raw": M.pr_auc(y, m["p"].values), "pr_auc_x1": M.pr_auc(y, m["x1"].values),
                    "x1@0.601": {k: M.confusion(y, (m["x1"].values >= 0.601).astype(int))[k] for k in ("tp", "fp", "fn")},
                    "p_mean": float(m["p"].mean())}
                print(name, round(out["configs"][name]["pr_auc_raw"], 3), round(out["configs"][name]["pr_auc_x1"], 3),
                      out["configs"][name]["x1@0.601"], round(out["configs"][name]["p_mean"], 3))
    # where do the two scalings differ most? (aggregate mean |difference| per scaled column, primary stations, eval rows)
    pw = C.load_processed(); sw = C.load_scaled()
    pw = pw[pw["station_name"].isin(C.PRIMARY) & (pw["date"] >= "2021-09-01")]
    st = C.apply_station_scalers(pw, joblib.load(C.SCALER_N), C.COLS_SCALE_N, C.COLS_SCALE_N)
    key = pd.MultiIndex.from_arrays([pw["station_name"], pw["date"]])
    sv = sw.set_index(["station_name", "date"])[C.COLS_SCALE_N].reindex(key).values
    out["mean_abs_scaled_diff_eval_rows"] = dict(zip(C.COLS_SCALE_N, np.nanmean(np.abs(st - sv), axis=0).round(4).tolist()))
    fl = {f: float((pw.set_index(["station_name", "date"])[f].reindex(key).values
                    != sw.set_index(["station_name", "date"])[f].reindex(key).values).mean()) for f in FLAGS}
    out["flag_disagreement_rate_eval_rows"] = fl
    (run / "diag_inputs.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    C.write_manifest(run, {"stage": "post-hoc diagnostic", "spec": "GCV-W1-v1 (not part of it)"})
    print(json.dumps({k: out[k] for k in ("mean_abs_scaled_diff_eval_rows", "flag_disagreement_rate_eval_rows")}, indent=1))
    print(run)


if __name__ == "__main__":
    main()
