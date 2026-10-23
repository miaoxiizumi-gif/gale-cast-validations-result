"""Cohort A: reproduce the historical W1+X1 scoring (_w1_recall_floor.py) from the tracked CSVs.

Faithful to the legacy code paths (cited by line in spec/EVAL_SPEC_v1.md §2), including its known
problems (pooled scaled_weather inputs, Port Area cross-station columns zeroed). Reproduction only.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix

import common as C

SPEC = json.loads((C.WORKSPACE / "spec" / "EVAL_SPEC_v1.json").read_text())
TEST_START, TEST_END = "2021-10-15", "2024-12-31"
TUNE_START, TUNE_END = "2020-10-15", "2021-10-14"


def legacy_frame(start: str, end: str) -> pd.DataFrame:
    """SELECT sw.*, pw.humidity_lag1, pw.humidity_lag2, pw.humidity_7day_avg, pw.target_gale AS pw_target_gale ..."""
    sw, pw = C.load_scaled(), C.load_processed()
    sw = sw[(sw["date"] >= start) & (sw["date"] <= end) & sw["station_name"].isin(C.PRIMARY)]
    pwj = pw[["station_name", "date", "humidity_lag1", "humidity_lag2", "humidity_7day_avg", "target_gale",
              "wind_speed"]].rename(columns={"target_gale": "pw_target_gale", "wind_speed": "pw_wind_speed"})
    df = sw.merge(pwj, on=["station_name", "date"], how="left")
    df = df.sort_values(["station_name", "date"]).reset_index(drop=True)
    return C.add_cross_station(df)  # 3 stations only -> PA columns NaN -> 0.0 (legacy lines 247-259)


def cm_row(y, pred) -> dict:
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return dict(tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp), precision=p, recall=r,
                f1=2 * p * r / (p + r) if p + r else 0.0)


def main():
    run = C.new_run("a-legacy")
    priv = C.private_dir(run)
    assert C.frozen_artifact_hashes() == SPEC["frozen_sha256"], "frozen artifact hash changed"
    model = C.load_frozen_model()

    # ---------------- TEST (strict, lines 552-590, 784-796)
    df = legacy_frame(TEST_START, TEST_END)
    y_true = (df["pw_target_gale"].values >= 1).astype(int)
    Xn, Xa = df[C.FEATURES_NORMAL].values, df[C.FEATURES_ANOMALY].values
    st = df["station_name"].values
    xs_n, xs_a, ys, gis = [], [], [], []
    for s in dict.fromkeys(st):
        idx = np.where(st == s)[0]
        s0, s1 = int(idx.min()), int(idx.max()) + 1
        for li in range(s1 - s0 - C.SEQ_LEN):
            gi = s0 + li
            xs_n.append(Xn[gi:gi + C.SEQ_LEN]); xs_a.append(Xa[gi:gi + C.SEQ_LEN])
            ys.append(y_true[gi + C.SEQ_LEN - 1]); gis.append(gi)
    gis = np.array(gis)
    out = model.predict([np.array(xs_n, dtype=np.float32), np.array(xs_a, dtype=np.float32)], verbose=0)
    import joblib
    sy = joblib.load(C.SCALER_Y)
    wind_pred = np.maximum(sy.inverse_transform(out[1])[:, 0], 0.0)
    test = pd.DataFrame({
        "station": st[gis + C.SEQ_LEN], "date": df["date"].values[gis + C.SEQ_LEN],
        "y": np.array(ys), "prob": out[0].ravel(),
        "wind_pred": wind_pred, "wind_obs_processed": df["pw_wind_speed"].values[gis + C.SEQ_LEN],
    })
    test["x1"] = test.groupby("date")["prob"].transform("mean")

    # ---------------- TUNE (permissive, build_tune_pp lines 799-858)
    pull_start = (pd.Timestamp(TUNE_START) - pd.Timedelta(days=40)).strftime("%Y-%m-%d")
    tdf = legacy_frame(pull_start, TUNE_END)
    ty = (tdf["pw_target_gale"].values >= 1).astype(int)
    tXn, tXa, tst, tdates = tdf[C.FEATURES_NORMAL].values, tdf[C.FEATURES_ANOMALY].values, tdf["station_name"].values, tdf["date"].values
    rows, bn, ba = [], [], []
    ls, le = np.datetime64(TUNE_START), np.datetime64(TUNE_END)
    for s in dict.fromkeys(tst):
        idx = np.where(tst == s)[0]
        s0, s1 = int(idx.min()), int(idx.max()) + 1
        for li in range(s1 - s0 - C.SEQ_LEN):
            gi = s0 + li
            ld = tdates[gi + C.SEQ_LEN - 1]
            if ls <= ld <= le:
                bn.append(tXn[gi:gi + C.SEQ_LEN]); ba.append(tXa[gi:gi + C.SEQ_LEN])
                rows.append((s, ld, ty[gi + C.SEQ_LEN - 1]))
    tp_ = model.predict([np.array(bn, dtype=np.float32), np.array(ba, dtype=np.float32)], verbose=0)[0].ravel()
    tune = pd.DataFrame(rows, columns=["station", "date", "y"]); tune["prob"] = tp_
    tune["x1"] = tune.groupby("date")["prob"].transform("mean")

    # ---------------- scores at the documented thresholds
    res = {"run_id": run.name, "test_windows": int(len(test)), "test_pos": int(test["y"].sum()),
           "tune_windows": int(len(tune)), "tune_pos": int(tune["y"].sum())}
    res["pr_auc"] = {k: float(average_precision_score(d["y"], d[c]))
                     for k, (d, c) in {"test_raw": (test, "prob"), "test_x1": (test, "x1"),
                                       "tune_raw": (tune, "prob"), "tune_x1": (tune, "x1")}.items()}
    res["test_x1_0601"] = cm_row(test["y"], (test["x1"] >= 0.601).astype(int))
    res["tune_x1_0601"] = cm_row(tune["y"], (tune["x1"] >= 0.601).astype(int))
    res["test_raw_064"] = cm_row(test["y"], (test["prob"] >= 0.64).astype(int))
    res["test_x1_062"] = cm_row(test["y"], (test["x1"] >= 0.62).astype(int))

    # ---------------- rule re-application on TUNE (verification only)
    grid01 = np.round(np.arange(0.01, 1.00, 0.01), 2)

    def maxf1(score):
        best, thr = -1.0, None
        for t in grid01:
            f = cm_row(tune["y"], (tune[score] >= t).astype(int))["f1"]
            if f >= best:
                best, thr = f, float(t)
        return thr, best

    res["rule_check"] = {"maxF1_raw": maxf1("prob"), "maxF1_x1": maxf1("x1")}
    scale = (len(test) - test["y"].sum()) / (len(tune) - tune["y"].sum())  # uses TEST negatives (legacy line 1033)
    sweep = []
    for t in np.round(np.arange(0.001, 1.000, 0.001), 3):
        r = cm_row(tune["y"], (tune["x1"] >= t).astype(int)); r["thr"] = float(t); r["fp_scaled"] = r["fp"] * scale
        sweep.append(r)
    fp12 = [r for r in sweep if r["fp_scaled"] <= 12]
    fp10 = [r for r in sweep if r["fp_scaled"] <= 10]
    rec85 = [r for r in sweep if r["recall"] >= 0.85]
    res["rule_check"].update({
        "fp_scale_factor_uses_TEST_negatives": float(scale),
        "R_FP12": min(fp12, key=lambda r: r["thr"])["thr"] if fp12 else None,
        "R_FP10": min(fp10, key=lambda r: r["thr"])["thr"] if fp10 else None,
        "R_REC85": max(rec85, key=lambda r: (r["precision"], -r["thr"]))["thr"] if rec85 else None,
    })
    # how wide is the band of TUNE thresholds giving the same TUNE matrix as 0.601?
    same = [r["thr"] for r in sweep if (r["tn"], r["fp"], r["fn"], r["tp"]) == (1070, 3, 1, 18)]
    res["rule_check"]["tune_threshold_band_with_same_matrix"] = [min(same), max(same)] if same else None

    # ---------------- neural-only next-day wind on legacy windows (legacy truth = processed, imputed)
    e = test["wind_pred"] - test["wind_obs_processed"]
    res["neural_only_wind_legacy_windows"] = {"n": int(e.notna().sum()), "mae": float(e.abs().mean()),
                                              "rmse": float(np.sqrt((e ** 2).mean())), "bias": float(e.mean()),
                                              "pred_mean": float(test["wind_pred"].mean()),
                                              "pred_sd": float(test["wind_pred"].std())}

    t = SPEC["legacy_reproduction_targets"]
    def tup(r): return [r["tn"], r["fp"], r["fn"], r["tp"]]
    res["reproduction"] = {
        "test_windows": res["test_windows"] == t["test_windows"],
        "test_pos": res["test_pos"] == t["test_pos"],
        "pr_auc_raw": abs(res["pr_auc"]["test_raw"] - t["pr_auc_raw"]) <= t["pr_auc_tolerance"],
        "pr_auc_x1": abs(res["pr_auc"]["test_x1"] - t["pr_auc_x1"]) <= t["pr_auc_tolerance"],
        "pr_auc_tune_raw": abs(res["pr_auc"]["tune_raw"] - t["pr_auc_tune_raw"]) <= t["pr_auc_tolerance"],
        "pr_auc_tune_x1": abs(res["pr_auc"]["tune_x1"] - t["pr_auc_tune_x1"]) <= t["pr_auc_tolerance"],
        "x1_0601_test": tup(res["test_x1_0601"]) == t["x1_0601_test"],
        "x1_0601_tune": tup(res["tune_x1_0601"]) == t["x1_0601_tune"],
        "raw_064_test": tup(res["test_raw_064"]) == t["raw_064_test"],
        "x1_062_test": tup(res["test_x1_062"]) == t["x1_062_test"],
        "rules_return_0601": all(res["rule_check"][k] == 0.601 for k in ("R_FP12", "R_FP10", "R_REC85")),
        "maxF1_raw_064": res["rule_check"]["maxF1_raw"][0] == 0.64,
        "maxF1_x1_062": res["rule_check"]["maxF1_x1"][0] == 0.62,
    }
    test.to_csv(priv / "cohort_a_test_rows.csv", index=False)
    tune.to_csv(priv / "cohort_a_tune_rows.csv", index=False)
    (run / "cohort_a_results.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    C.write_manifest(run, {"stage": "cohort A", "spec": "GCV-W1-v1"})
    print(json.dumps(res, indent=1, default=float))
    print(run)


if __name__ == "__main__":
    main()
