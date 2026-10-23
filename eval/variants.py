"""Stage 7: existing frozen variants scored (inference only) on the identical Cohort B cases.

Spec §10 + Amendment A1. Each variant uses its own scalers and its own documented TUNE max-F1 threshold.
Descriptive comparison only: nothing is selected here.
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

import cohort_b as B
import common as C
import metrics as M

BRANCH = "exp/precision-targeting"
VARIANTS = {"_w3": 0.64, **B.SPEC["variants"]}  # W1 itself first, for the same pipeline
LABELS = {"_w3": "W1 (deployed)", "v12": "v12", "v11": "v11", "v13": "v13 (Split B)", "v14": "v14 (Split C)",
          "_w6": "W2 (neg. weight x6)", "_w10": "W3 (neg. weight x10)", "_f1": "F1 (focal variant)",
          "_f2": "F2 (focal variant)"}


def suffix(v: str) -> str:
    return v if v.startswith("_") else f"_{v}"


def main():
    run = C.new_run("s7-variants")
    priv = C.private_dir(run)
    bench = sorted(p.name for p in (C.PRIVATE / "runs").glob("b-benchmark-*"))[-1]
    rows = pd.read_csv(C.PRIVATE / "runs" / bench / "cohort_b_rows.csv", parse_dates=["date"])
    Ecases = rows[rows["elig_event"]][["station", "date", "E"]]
    Wcases = rows[rows["elig_wind"]][["station", "date", "wind_obs"]]
    leg_frame, leg_Xn, leg_Xa = B.processed_inputs_legacy()
    leg_wi = B.window_index(leg_frame)
    out = {"run_id": run.name, "benchmark_rows_from": bench, "variants": {}}
    for v, thr in VARIANTS.items():
        s = suffix(v)
        path = C.lfs_model_copy(s)
        model = C.load_frozen_model(path)
        shapes = [list(t.shape) for t in model.inputs]
        rec = {"label": LABELS[v], "model_sha256": C.sha256_file(path), "params": int(model.count_params()),
               "input_shapes": shapes, "threshold_documented": thr}
        if sorted(shapes) != sorted([[None, 32, 32], [None, 32, 4]]):
            rec["scored"] = False
            rec["reason"] = "input shape differs from W1's"
            out["variants"][v] = rec
            continue
        sn = joblib.load(C.lfs_or_git_blob(f"scaler_X_normal_mo{s}.save"))
        sa = joblib.load(C.lfs_or_git_blob(f"scaler_X_anomaly_mo{s}.save"))
        sy = joblib.load(C.lfs_or_git_blob(f"scaler_y_regression_mo{s}.save"))
        rec["scalers_sha256"] = {k: C.sha256_file(C.lfs_or_git_blob(f"{k}{s}.save"))
                                 for k in ("scaler_X_normal_mo", "scaler_X_anomaly_mo", "scaler_y_regression_mo")}
        for cons in ("S-TRAIN", "S-LEGACY"):
            if cons == "S-TRAIN":
                frame, Xn, Xa = B.processed_inputs_train_consistent(sn, sa)
                wi = B.window_index(frame)
            else:
                Xn, Xa, wi = leg_Xn, leg_Xa, leg_wi.copy()
            p, w = B.predict(model, Xn, Xa, wi["start"].values, sy)
            wi = wi.assign(p=p, wind=w)
            wi["x1"] = wi.groupby("date")["p"].transform("mean")
            e = Ecases.merge(wi, on=["station", "date"], how="left")
            ww = Wcases.merge(wi, on=["station", "date"], how="left")
            assert e["p"].notna().all() and ww["wind"].notna().all()
            y = e["E"].values.astype(int)
            rec[cons] = {
                "event_cases": int(len(e)), "events": int(y.sum()),
                "pr_auc_raw": M.pr_auc(y, e["p"].values), "pr_auc_x1": M.pr_auc(y, e["x1"].values),
                "brier_raw": M.brier(y, e["p"].values),
                "raw_at_documented_threshold": M.confusion(y, (e["p"].values >= thr).astype(int)),
                "wind_cases": int(len(ww)), **{f"wind_{k}": v_ for k, v_ in
                                               M.wind_stats(ww["wind"].values - ww["wind_obs"].values).items()},
                "wind_pred_sd": float(ww["wind"].std()),
            }
            pd.DataFrame({"station": e["station"], "date": e["date"], "p": e["p"], "x1": e["x1"]}).to_csv(
                priv / f"variant{s}_{cons}_event_scores.csv", index=False)
        rec["scored"] = True
        out["variants"][v] = rec
        print(LABELS[v], {c: {k: (round(rec[c][k], 3) if isinstance(rec[c][k], float) else rec[c][k])
                              for k in ("pr_auc_raw", "pr_auc_x1", "wind_mae")} for c in ("S-TRAIN", "S-LEGACY")},
              {k: rec["S-TRAIN"]["raw_at_documented_threshold"][k] for k in ("tp", "fp", "fn")})
    out["not_scored"] = {"x1f": "extra input features not recorded", "x2f": "extra input features not recorded"}
    (run / "variants_results.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    C.write_manifest(run, {"stage": 7, "spec": "GCV-W1-v1 + Amendment A1"})
    print(run)


if __name__ == "__main__":
    main()
