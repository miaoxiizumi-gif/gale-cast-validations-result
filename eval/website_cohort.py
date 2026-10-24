"""Group A (amendment A2): the website's 3,423-case scorecard, with matching same-case baselines.

Case identity comes from the Cohort A reproduction run and is checked against the ORIGINAL saved
false-alarm/miss record (nine_fp_report.json on exp/precision-targeting). The legacy procedure is re-run
once here only to recover the five regression outputs the Cohort A run did not save; it must reproduce
the saved scores exactly or the run stops.
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

import benchmark as BM
import cohort_a_legacy as A
import common as C
import metrics as M

SPEC = json.loads((C.WORKSPACE / "spec" / "EVAL_SPEC_v1.json").read_text())
A_RUN = "a-legacy-20261023T162426Z-b5f446"
CLIM0, CLIM1 = pd.Timestamp("2015-01-01"), pd.Timestamp("2020-10-14")
DEV0, DEV1 = pd.Timestamp("2020-10-15"), pd.Timestamp("2021-10-14")
REG = {  # name: (weather_vars column, raw column, unit)
    "wind": (0, "wind_speed", "m/s"), "humidity": (1, "relative_humidity", "%"),
    "rainfall": (4, "rainfall", "mm"), "mslp": (5, "mean_sea_level_pressure", "hPa"),
}


def legacy_rows_with_all_outputs() -> pd.DataFrame:
    """cohort_a_legacy.py's TEST loop, unchanged, keeping every output and the window's last date."""
    model = C.load_frozen_model()
    sy = joblib.load(C.SCALER_Y)
    df = A.legacy_frame(A.TEST_START, A.TEST_END)
    y_true = (df["pw_target_gale"].values >= 1).astype(int)
    Xn, Xa, st = df[C.FEATURES_NORMAL].values, df[C.FEATURES_ANOMALY].values, df["station_name"].values
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
    reg = sy.inverse_transform(out[1])
    reg[:, 0] = np.maximum(reg[:, 0], 0.0)                 # clamps as validate_model_multioutput.py@1fd1ef9
    reg[:, 1] = np.clip(reg[:, 1], 0.0, 100.0)
    reg[:, 4] = np.maximum(reg[:, 4], 0.0)
    reg[:, 5] = np.clip(reg[:, 5], 850.0, 1050.0)
    rows = pd.DataFrame({
        "station": st[gis + C.SEQ_LEN], "date": pd.to_datetime(df["date"].values[gis + C.SEQ_LEN]),
        "issue_date": pd.to_datetime(df["date"].values[gis + C.SEQ_LEN - 1]),
        "y": np.array(ys), "prob": out[0].ravel(),
        "W1_wind": reg[:, 0], "W1_humidity": reg[:, 1], "W1_rainfall": np.expm1(reg[:, 4]), "W1_mslp": reg[:, 5],
    })
    rows["x1"] = rows.groupby("date")["prob"].transform("mean")
    return rows


def raw_table() -> pd.DataFrame:
    r = C.load_raw()
    r = r[r["station_name"].isin(C.PRIMARY)].rename(columns={"station_name": "station"}).copy()
    r["rainfall"] = r["rainfall"].replace(-1.0, 0.05)       # pipeline's trace rule (process_weather.py:47)
    r["mslp_prev"] = r.groupby("station")["mean_sea_level_pressure"].shift(1)
    gap = (r["date"] - r.groupby("station")["date"].shift(1)) != pd.Timedelta(days=1)
    r.loc[gap, "mslp_prev"] = np.nan
    r["pfall"] = r["mslp_prev"] - r["mean_sea_level_pressure"]
    det = r["wind_speed"].notna() & r["pfall"].notna()
    r["E_raw"] = np.where(det, ((r["wind_speed"] >= C.WIND_MOD) | (r["pfall"] >= C.PDROP_MOD)).astype(float), np.nan)
    return r[["station", "date", "wind_speed", "relative_humidity", "rainfall", "mean_sea_level_pressure", "pfall", "E_raw"]]


def label_parts(proc: pd.DataFrame) -> pd.DataFrame:
    p = proc.rename(columns={"station_name": "station"})[["station", "date", "wind_speed", "pressure_drop",
                                                          "mean_sea_level_pressure"]].copy()
    p["L_wind"] = (p["wind_speed"] >= C.WIND_MOD).astype(int)
    p["L_press"] = (p["pressure_drop"] >= C.PDROP_MOD).astype(int)
    p["L"] = (p["L_wind"] | p["L_press"]).astype(int)
    return p


def clim_threshold(dev: pd.DataFrame) -> dict:
    best = (-1.0, None, None)
    for thr in sorted(dev["p"].dropna().unique()):
        pred = dev["p"] >= thr
        tp = int((pred & (dev["L"] == 1)).sum()); fp = int((pred & (dev["L"] == 0)).sum())
        fn = int((~pred & (dev["L"] == 1)).sum())
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        if f1 >= best[0]:
            best = (f1, float(thr), dict(tp=tp, fp=fp, fn=fn, tn=int(len(dev) - tp - fp - fn)))
    return {"dev_cases": int(len(dev)), "dev_events": int(dev["L"].sum()), "best_dev_f1": best[0],
            "threshold": best[1] if best[0] > 0 else None, "dev_matrix": best[2]}


def main():
    run = C.new_run("w-cohort")
    priv = C.private_dir(run)
    assert C.frozen_artifact_hashes() == SPEC["frozen_sha256"], "frozen artifact hash changed"
    checks = {}

    # ---------------- identity: saved reproduction rows vs ORIGINAL saved false-alarm/miss record
    saved = pd.read_csv(C.PRIVATE / "runs" / A_RUN / "cohort_a_test_rows.csv", parse_dates=["date"])
    orig = json.loads(C.git(["show", "exp/precision-targeting:nine_fp_report.json"]))
    saved["dec"] = (saved["x1"] >= 0.601).astype(int)

    def same(rows, ref):
        if len(rows) != len(ref):
            return False
        for r in ref:
            m = rows[(rows["date"] == pd.Timestamp(r["date"])) & (rows["station"] == r["station"])]
            if len(m) != 1 or abs(float(m["x1"].iloc[0]) - r["score"]) > 1e-5:
                return False
        return True
    checks["fp_identity_matches_original_record"] = same(saved[(saved.dec == 1) & (saved.y == 0)], orig["fp_detail"])
    checks["fn_identity_matches_original_record"] = same(saved[(saved.dec == 0) & (saved.y == 1)], orig["fn_detail"])
    cm = M.confusion(saved["y"].values, saved["dec"].values)
    checks["matrix_3386_9_4_24"] = [cm["tn"], cm["fp"], cm["fn"], cm["tp"]] == [3386, 9, 4, 24]
    assert all(checks.values()), checks

    # ---------------- re-run once for the other regression outputs; must equal the saved rows
    rows = legacy_rows_with_all_outputs()
    mg = rows.merge(saved[["station", "date", "y", "prob", "x1", "wind_pred"]], on=["station", "date"],
                    suffixes=("", "_saved"), validate="one_to_one")
    checks["rerun_rows_equal_saved"] = len(mg) == len(saved) == 3423
    checks["rerun_prob_max_abs_diff"] = float((mg["prob"] - mg["prob_saved"]).abs().max())
    checks["rerun_x1_max_abs_diff"] = float((mg["x1"] - mg["x1_saved"]).abs().max())
    checks["rerun_wind_max_abs_diff"] = float((mg["W1_wind"] - mg["wind_pred"]).abs().max())
    checks["rerun_labels_equal"] = bool((mg["y"] == mg["y_saved"]).all())
    assert checks["rerun_rows_equal_saved"] and checks["rerun_labels_equal"]
    assert max(checks["rerun_prob_max_abs_diff"], checks["rerun_x1_max_abs_diff"], checks["rerun_wind_max_abs_diff"]) <= 1e-6, checks
    W = mg.drop(columns=["prob_saved", "x1_saved", "y_saved", "wind_pred"])
    checks["issue_date_is_target_minus_1_all_rows"] = bool(((W["date"] - W["issue_date"]) == pd.Timedelta(days=1)).all())
    assert checks["issue_date_is_target_minus_1_all_rows"]

    # ---------------- label (processed, as on the website) and its parts
    proc = C.load_processed()
    lp = label_parts(proc).set_index(["station", "date"])
    kd = pd.MultiIndex.from_arrays([W["station"], W["date"]])
    kt = pd.MultiIndex.from_arrays([W["station"], W["issue_date"]])
    for c in ("L", "L_wind", "L_press"):
        W[c] = lp[c].reindex(kd).values
    W["proc_wind_d"] = lp["wind_speed"].reindex(kd).values
    W["proc_wind_t"] = lp["wind_speed"].reindex(kt).values
    W["E_persist"] = lp["L"].reindex(kt).values
    checks["label_equals_processed_gale_flag_rule"] = bool((W["L"] == W["y"]).all())
    assert checks["label_equals_processed_gale_flag_rule"]

    # event climatology (processed label), fit 2015-01-02..2020-10-14, threshold on development dates only
    lpr = label_parts(proc)
    lpr = lpr[lpr["station"].isin(C.PRIMARY)].copy()
    lpr["month"] = lpr["date"].dt.month
    fit = lpr[(lpr["date"] >= CLIM0 + pd.Timedelta(days=1)) & (lpr["date"] <= CLIM1)]
    ev_clim = fit.groupby(["station", "month"])["L"].mean()
    dev = lpr[(lpr["date"] >= DEV0) & (lpr["date"] <= DEV1)].copy()
    dev["p"] = ev_clim.reindex(pd.MultiIndex.from_arrays([dev["station"], dev["month"]])).values
    clim = clim_threshold(dev)
    W["E_clim"] = ev_clim.reindex(pd.MultiIndex.from_arrays([W["station"], W["date"].dt.month])).values

    # ---------------- raw truth, persistence, climatology per regression variable
    raw = raw_table()
    rt = raw.set_index(["station", "date"])
    rfit = raw[(raw["date"] >= CLIM0) & (raw["date"] <= CLIM1)].assign(month=lambda d: d["date"].dt.month)
    for name, (_, col, _) in REG.items():
        W[f"obs_{name}"] = rt[col].reindex(kd).values
        W[f"pers_{name}"] = rt[col].reindex(kt).values
        cl = rfit.dropna(subset=[col]).groupby(["station", "month"])[col].mean()
        W[f"clim_{name}"] = cl.reindex(pd.MultiIndex.from_arrays([W["station"], W["date"].dt.month])).values
    W["raw_pfall_d"] = rt["pfall"].reindex(kd).values
    W["E_raw"] = rt["E_raw"].reindex(kd).values

    res = {"run_id": run.name, "amendment": "A2", "source_cohort_a_run": A_RUN, "checks": checks,
           "event_climatology_threshold": clim}
    # label composition
    P = W[W["L"] == 1]
    res["label"] = {
        "cases": int(len(W)), "positives": int(len(P)),
        "pressure_only": int(((P.L_press == 1) & (P.L_wind == 0)).sum()),
        "wind_only": int(((P.L_wind == 1) & (P.L_press == 0)).sum()),
        "both": int(((P.L_wind == 1) & (P.L_press == 1)).sum()),
        "by_station": {s: {"cases": int((W.station == s).sum()), "positives": int(((W.station == s) & (W.L == 1)).sum()),
                           "pressure_only": int(((W.station == s) & (W.L_press == 1) & (W.L_wind == 0)).sum()),
                           "wind_only": int(((W.station == s) & (W.L_wind == 1) & (W.L_press == 0)).sum()),
                           "both": int(((W.station == s) & (W.L_wind == 1) & (W.L_press == 1)).sum())} for s in C.PRIMARY},
        "processed_wind_ge_10_8_days": int((W["proc_wind_d"] >= C.WIND_MOD).sum()),
        "processed_wind_ge_17_2_days": int((W["proc_wind_d"] >= C.WIND_HIGH).sum()),
        "raw_label_determinable": int(W["E_raw"].notna().sum()),
        "raw_label_agrees": int((W["E_raw"].notna() & (W["E_raw"] == W["L"])).sum()),
        "raw_label_disagrees": int((W["E_raw"].notna() & (W["E_raw"] != W["L"])).sum()),
        "tp_raw_label_1": int(((W.L == 1) & (W.x1 >= 0.601) & (W.E_raw == 1)).sum()),
    }

    # ---------------- events: same cases, same bootstrap as Cohort B
    E = W.rename(columns={"L": "E", "prob": "p_raw", "x1": "p_x1"}).copy()
    E["E_persist"] = E["E_persist"].astype(int)
    ev = BM.event_block(E, clim["threshold"])
    res["events"] = ev
    classifiers = ev["_classifier_predictions"]
    res["events_all_classifiers_n"] = {k: int(len(v)) for k, v in classifiers.items()}

    # ---------------- regression: raw truth, common cases per variable
    res["regression"] = {}
    codes_all = None
    for name in REG:
        m = W[f"obs_{name}"].notna() & W[f"pers_{name}"].notna() & W[f"clim_{name}"].notna()
        R = W[m]
        errs = {"W1": R[f"W1_{name}"].values - R[f"obs_{name}"].values,
                "persistence": R[f"pers_{name}"].values - R[f"obs_{name}"].values,
                "climatology": R[f"clim_{name}"].values - R[f"obs_{name}"].values}
        excl = {"target_obs_missing": int(W[f"obs_{name}"].isna().sum()),
                "issue_day_obs_missing_only": int((W[f"obs_{name}"].notna() & W[f"pers_{name}"].isna()).sum()),
                "climatology_missing_only": int((W[f"obs_{name}"].notna() & W[f"pers_{name}"].notna() & W[f"clim_{name}"].isna()).sum())}
        out = {"unit": REG[name][2], "n_common": int(m.sum()), "excluded": excl, "scopes": {}}
        scopes = {"pooled": np.ones(len(R), bool), **{s: (R["station"] == s).values for s in C.PRIMARY}}
        u = np.sort(R["date"].unique()); codes = np.searchsorted(u, R["date"].values)
        boot = {sc: {k: [] for k in ("mae_W1", "mae_persistence", "mae_climatology", "rmse_W1", "rmse_persistence",
                                     "rmse_climatology", "dmae_W1_persistence", "dmae_W1_climatology",
                                     "drmse_W1_persistence", "drmse_W1_climatology")} for sc in scopes}
        for dw in M.block_weights(len(u), SPEC["bootstrap"]["block_days"], SPEC["bootstrap"]["B"], SPEC["bootstrap"]["seed"]):
            w = dw[codes]
            for sc, mk in scopes.items():
                st = {k: M.wind_stats(e[mk], w[mk]) for k, e in errs.items()}
                for k in errs:
                    boot[sc][f"mae_{k}"].append(st[k]["mae"]); boot[sc][f"rmse_{k}"].append(st[k]["rmse"])
                for k in ("persistence", "climatology"):
                    boot[sc][f"dmae_W1_{k}"].append(st["W1"]["mae"] - st[k]["mae"])
                    boot[sc][f"drmse_W1_{k}"].append(st["W1"]["rmse"] - st[k]["rmse"])
        for sc, mk in scopes.items():
            point = {k: {**M.wind_stats(e[mk]), "n": int(mk.sum())} for k, e in errs.items()}
            point["W1_pred_sd"] = float(R.loc[mk, f"W1_{name}"].std()); point["obs_sd"] = float(R.loc[mk, f"obs_{name}"].std())
            cis = {k: M.ci(v) for k, v in boot[sc].items()}
            for k in cis:
                if k.startswith("d"):
                    cis[k]["verdict"] = M.established(cis[k])
            out["scopes"][sc] = {"point": point, "ci": cis}
        res["regression"][name] = out

    # wind on processed truth (the website's truth source), all 3,423 cases, no bootstrap
    e_w1 = W["W1_wind"].values - W["proc_wind_d"].values
    e_pe = W["proc_wind_t"].values - W["proc_wind_d"].values
    res["wind_processed_truth_all_cases"] = {"n": int(len(W)), "W1": M.wind_stats(e_w1), "persistence": M.wind_stats(e_pe)}

    # aggregate public tables
    bins_spec = {"wind": np.arange(0, 12.5, 1.0), "mslp": np.arange(996, 1018, 1.0),
                 "humidity": np.arange(40, 101, 5.0), "rainfall": np.array([0, 0.1, 1, 2, 5, 10, 20, 50, 100, 1000])}
    agg = []
    for name in REG:
        R = W[W[f"obs_{name}"].notna()]
        b = bins_spec[name]
        h, xe, ye = np.histogram2d(np.clip(R[f"obs_{name}"], b[0], b[-1] - 1e-9), np.clip(R[f"W1_{name}"], b[0], b[-1] - 1e-9), bins=[b, b])
        for i in range(len(b) - 1):
            for j in range(len(b) - 1):
                if h[i, j]:
                    agg.append({"variable": name, "obs_lo": xe[i], "obs_hi": xe[i + 1], "pred_lo": ye[j], "pred_hi": ye[j + 1], "count": int(h[i, j])})
    pd.DataFrame(agg).to_csv(run / "obs_vs_W1_binned_counts.csv", index=False)
    res["obs_vs_W1_binned_total"] = {name: int(W[f"obs_{name}"].notna().sum()) for name in REG}

    W.to_csv(priv / "website_cohort_rows.csv", index=False)
    out = BM.strip(res)
    (run / "website_cohort_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": "Group A website cohort (amendment A2)", "spec": "GCV-W1-v1 + A2"})
    print(json.dumps({"checks": checks, "label": out["label"], "clim": clim}, indent=1))
    for k, v in out["events"]["pooled"]["classifiers"].items():
        print(k, {m: v[m] for m in ("tp", "fn", "fp", "tn", "precision", "recall", "f1")})
    print(json.dumps(out["events"]["pooled"]["probabilistic"], indent=0))
    for name, r in out["regression"].items():
        p = r["scopes"]["pooled"]["point"]
        print(name, r["n_common"], {k: round(p[k]["mae"], 3) for k in ("W1", "persistence", "climatology")},
              r["scopes"]["pooled"]["ci"]["dmae_W1_persistence"]["verdict"])
    print(json.dumps(out["wind_processed_truth_all_cases"]))
    print(run)


if __name__ == "__main__":
    main()
