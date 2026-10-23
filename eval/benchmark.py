"""Cohort B benchmark: frozen W1 vs persistence and climatology on identical next-day cases."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import cohort_b as B
import common as C
import metrics as M

SPEC = B.SPEC
BS = SPEC["bootstrap"]
THR = SPEC["thresholds"]


def date_codes(df: pd.DataFrame) -> tuple[np.ndarray, int]:
    u = np.sort(df["date"].unique())
    return np.searchsorted(u, df["date"].values), len(u)


# ------------------------------------------------------------------ wind
WIND_METHODS = {"W1": "wind_W1", "persistence": "wind_persist", "climatology": "wind_clim"}


def wind_block(W: pd.DataFrame, extra: dict | None = None) -> dict:
    methods = dict(WIND_METHODS, **(extra or {}))
    obs = W["wind_obs"].values
    errs = {m: W[c].values - obs for m, c in methods.items()}
    scopes = {"pooled": np.ones(len(W), bool), **{s: (W["station"] == s).values for s in B.C.PRIMARY}}
    codes, nd = date_codes(W)
    res = {}
    point = {sc: {m: {**M.wind_stats(e[mask]), "n": int(mask.sum())} for m, e in errs.items()} for sc, mask in scopes.items()}
    boot = {sc: {k: [] for k in [f"mae_{m}" for m in methods] + [f"dmae_W1_{m}" for m in methods if m != "W1"]
                 + [f"drmse_W1_{m}" for m in methods if m != "W1"]} for sc in scopes}
    for dw in M.block_weights(nd, BS["block_days"], BS["B"], BS["seed"]):
        w = dw[codes]
        for sc, mask in scopes.items():
            st = {m: M.wind_stats(e[mask], w[mask]) for m, e in errs.items()}
            for m in methods:
                boot[sc][f"mae_{m}"].append(st[m]["mae"])
                if m != "W1":
                    boot[sc][f"dmae_W1_{m}"].append(st["W1"]["mae"] - st[m]["mae"])
                    boot[sc][f"drmse_W1_{m}"].append(st["W1"]["rmse"] - st[m]["rmse"])
    for sc in scopes:
        res[sc] = {"point": point[sc], "ci": {k: M.ci(v) for k, v in boot[sc].items()}}
        for k in list(res[sc]["ci"]):
            if k.startswith("d"):
                res[sc]["ci"][k]["verdict"] = M.established(res[sc]["ci"][k])
        res[sc]["point"]["W1_pred_sd"] = float(W.loc[scopes[sc], "wind_W1"].std())
        res[sc]["point"]["obs_sd"] = float(W.loc[scopes[sc], "wind_obs"].std())
    return res


# ------------------------------------------------------------------ events
def event_block(E: pd.DataFrame, clim_thr: float | None, extra_prob: dict | None = None) -> dict:
    y = E["E"].values.astype(int)
    classifiers = {
        "W1_raw@0.64": (E["p_raw"].values >= THR["w1_raw"]).astype(int),
        "W1+X1@0.601": (E["p_x1"].values >= THR["w1_x1_primary"]).astype(int),
        "W1+X1@0.62": (E["p_x1"].values >= THR["w1_x1_secondary"]).astype(int),
        "event_persistence": E["E_persist"].values.astype(int),
    }
    if clim_thr is not None:
        classifiers[f"event_climatology@{clim_thr:.4f}"] = (E["E_clim"].values >= clim_thr).astype(int)
    probs = {"W1_raw": E["p_raw"].values, "W1+X1": E["p_x1"].values, "event_climatology": E["E_clim"].values,
             **(extra_prob or {})}
    scopes = {"pooled": np.ones(len(E), bool), **{s: (E["station"] == s).values for s in B.C.PRIMARY}}
    codes, nd = date_codes(E)
    res = {}
    for sc, mask in scopes.items():
        r = {"classifiers": {k: M.confusion(y[mask], v[mask]) for k, v in classifiers.items()},
             "probabilistic": {k: {"pr_auc": M.pr_auc(y[mask], p[mask]), "brier": M.brier(y[mask], p[mask])}
                               for k, p in probs.items()}}
        bc = r["probabilistic"]["event_climatology"]["brier"]
        for k in r["probabilistic"]:
            r["probabilistic"][k]["brier_skill_vs_climatology"] = 1 - r["probabilistic"][k]["brier"] / bc if bc else None
        res[sc] = r
    keys = ([f"{m}_{k}" for k in classifiers for m in ("precision", "recall", "f1")]
            + [f"prauc_{k}" for k in probs] + [f"brier_{k}" for k in probs]
            + ["df1_X1601_persist", "df1_raw064_persist", "dprauc_X1_clim", "dprauc_raw_clim",
               "dbrier_X1_clim", "dbrier_raw_clim"])
    boot = {sc: {k: [] for k in keys} for sc in scopes}
    for dw in M.block_weights(nd, BS["block_days"], BS["B"], BS["seed"] + 1):
        w = dw[codes]
        for sc, mask in scopes.items():
            yy, ww = y[mask], w[mask]
            cms = {k: M.confusion(yy, v[mask], ww) for k, v in classifiers.items()}
            for k, cm in cms.items():
                for m in ("precision", "recall", "f1"):
                    boot[sc][f"{m}_{k}"].append(cm[m])
            pa = {k: M.pr_auc(yy, p[mask], ww) for k, p in probs.items()}
            br = {k: M.brier(yy, p[mask], ww) for k, p in probs.items()}
            for k in probs:
                boot[sc][f"prauc_{k}"].append(pa[k]); boot[sc][f"brier_{k}"].append(br[k])
            boot[sc]["df1_X1601_persist"].append(cms["W1+X1@0.601"]["f1"] - cms["event_persistence"]["f1"])
            boot[sc]["df1_raw064_persist"].append(cms["W1_raw@0.64"]["f1"] - cms["event_persistence"]["f1"])
            boot[sc]["dprauc_X1_clim"].append(pa["W1+X1"] - pa["event_climatology"])
            boot[sc]["dprauc_raw_clim"].append(pa["W1_raw"] - pa["event_climatology"])
            boot[sc]["dbrier_X1_clim"].append(br["W1+X1"] - br["event_climatology"])
            boot[sc]["dbrier_raw_clim"].append(br["W1_raw"] - br["event_climatology"])
    for sc in scopes:
        res[sc]["ci"] = {k: M.ci(v) for k, v in boot[sc].items()}
        for k in res[sc]["ci"]:
            if k.startswith("d"):
                res[sc]["ci"][k]["verdict"] = M.established(res[sc]["ci"][k])
    res["_classifier_predictions"] = classifiers  # removed before writing
    return res


def monthly_public(W: pd.DataFrame, E: pd.DataFrame, classifiers: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    wm = W.assign(month=W["date"].dt.to_period("M").astype(str)).groupby(["station", "month"]).agg(
        n=("wind_obs", "size"), obs_mean=("wind_obs", "mean"), W1_mean=("wind_W1", "mean"),
        persistence_mean=("wind_persist", "mean"), climatology_mean=("wind_clim", "mean")).reset_index()
    rows = []
    ym = E["date"].dt.to_period("M").astype(str).values
    y = E["E"].values.astype(int)
    for name, pred in classifiers.items():
        df = pd.DataFrame({"station": E["station"].values, "month": ym, "hit": (pred == 1) & (y == 1),
                           "miss": (pred == 0) & (y == 1), "false_alarm": (pred == 1) & (y == 0),
                           "correct_negative": (pred == 0) & (y == 0)})
        g = df.groupby(["station", "month"])[["hit", "miss", "false_alarm", "correct_negative"]].sum().reset_index()
        g.insert(0, "procedure", name)
        rows.append(g)
    return wm, pd.concat(rows, ignore_index=True)


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, float) and np.isnan(o):
        return None
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


def main():
    run = C.new_run("b-benchmark")
    priv = C.private_dir(run)
    assert C.frozen_artifact_hashes() == SPEC["frozen_sha256"], "frozen artifact hash changed"

    wi = B.build()
    leg = B.build(legacy_inputs=True)[["station", "date", "p_raw", "p_x1", "wind_W1"]].rename(
        columns={"p_raw": "p_raw_legacyin", "p_x1": "p_x1_legacyin", "wind_W1": "wind_W1_legacyin"})
    wi = wi.merge(leg, on=["station", "date"], how="left")
    clim = B.dev_climatology_threshold()

    cand = len(wi)
    all_targets = len(B.C.PRIMARY) * len(pd.date_range(B.D0, B.D1))
    counts = {
        "target_station_days_in_period": all_targets,
        "with_32day_window": cand,
        "excluded_no_window": all_targets - cand,
        "wind": {"eligible": int(wi["elig_wind"].sum()),
                 "excluded_target_wind_missing": int(wi["wind_obs"].isna().sum()),
                 "excluded_issue_day_wind_missing_only": int((wi["wind_obs"].notna() & wi["wind_persist"].isna()).sum())},
        "event": {"eligible": int(wi["elig_event"].sum()),
                  "excluded_target_label_undeterminable": int(wi["E"].isna().sum()),
                  "excluded_issue_day_label_undeterminable_only": int((wi["E"].notna() & wi["E_persist"].isna()).sum())},
        "window_has_imputed_value": int(wi["window_has_imputed"].sum()),
    }
    W = wi[wi["elig_wind"]].copy()
    E = wi[wi["elig_event"]].copy()
    counts["wind"]["by_station"] = W.groupby("station").size().to_dict()
    counts["event"]["by_station"] = E.groupby("station").agg(cases=("E", "size"), events=("E", "sum")).to_dict("index")
    counts["event"]["events_total"] = int(E["E"].sum())
    counts["event"]["label_parts"] = {k: int(E[k].sum()) for k in ("E_pressure_only", "E_wind_only", "E_both")}
    counts["event"]["gale_wind_ge_17_2_days"] = int(E["gale_wind"].sum())
    counts["wind"]["obs_ge_10_8_days"] = int((W["wind_obs"] >= 10.8).sum())
    pwt = C.load_processed().rename(columns={"station_name": "station"})
    pwt["date"] = pwt["date"] + pd.Timedelta(days=1)  # target_gale on row t is the class of t+1
    legacy_lab = E.merge(pwt[["station", "date", "target_gale"]], on=["station", "date"], how="left")
    counts["event"]["legacy_imputed_label_disagreements"] = int(((legacy_lab["target_gale"] >= 1).astype(int)
                                                                  != legacy_lab["E"].astype(int)).sum())

    res = {"run_id": run.name, "spec": "GCV-W1-v1", "counts": counts, "event_climatology_threshold": clim}
    res["wind"] = wind_block(W, extra={"W1_legacy_inputs": "wind_W1_legacyin"})
    ev = event_block(E, clim["threshold"], extra_prob={"W1_raw_legacy_inputs": E["p_raw_legacyin"].values,
                                                       "W1+X1_legacy_inputs": E["p_x1_legacyin"].values})
    classifiers = ev["_classifier_predictions"]
    res["events"] = ev

    # declared breakdowns: by year (point estimates; bootstrap would be too thin per year)
    res["by_year"] = {}
    for yv, g in W.groupby(W["date"].dt.year):
        res["by_year"].setdefault(str(yv), {})["wind"] = {
            m: {**M.wind_stats(g[c].values - g["wind_obs"].values), "n": int(len(g))} for m, c in B_W.items()}
    for yv, g in E.groupby(E["date"].dt.year):
        yy = g["E"].values.astype(int)
        res["by_year"].setdefault(str(yv), {})["events"] = {
            "cases": int(len(g)), "events": int(yy.sum()),
            "W1+X1@0.601": M.confusion(yy, (g["p_x1"].values >= THR["w1_x1_primary"]).astype(int)),
            "event_persistence": M.confusion(yy, g["E_persist"].values.astype(int))}
    # S-NOIMPUTE
    Wn, En = W[~W["window_has_imputed"]], E[~E["window_has_imputed"]]
    res["S_NOIMPUTE"] = {"wind_cases": int(len(Wn)), "event_cases": int(len(En)), "events": int(En["E"].sum()),
                         "wind": {m: M.wind_stats(Wn[c].values - Wn["wind_obs"].values) for m, c in B_W.items()},
                         "W1+X1@0.601": M.confusion(En["E"].values.astype(int), (En["p_x1"].values >= THR["w1_x1_primary"]).astype(int)),
                         "event_persistence": M.confusion(En["E"].values.astype(int), En["E_persist"].values.astype(int)),
                         "pr_auc_X1": M.pr_auc(En["E"].values.astype(int), En["p_x1"].values),
                         "pr_auc_clim": M.pr_auc(En["E"].values.astype(int), En["E_clim"].values)}
    res["S_LEGACY_classifier"] = M.confusion(E["E"].values.astype(int),
                                             (E["p_x1_legacyin"].values >= THR["w1_x1_primary"]).astype(int))
    res["W1_prob_summary"] = {"p_raw_mean": float(E["p_raw"].mean()), "p_raw_sd": float(E["p_raw"].std()),
                              "p_raw_max": float(E["p_raw"].max()),
                              "share_p_raw_ge_0.5": float((E["p_raw"] >= 0.5).mean())}

    wm, em = monthly_public(W, E, classifiers)
    # consistency: monthly totals must equal the confusion matrices
    chk = {}
    for name, g in em.groupby("procedure"):
        cm = res["events"]["pooled"]["classifiers"][name]
        chk[name] = (int(g["hit"].sum()) == cm["tp"] and int(g["miss"].sum()) == cm["fn"]
                     and int(g["false_alarm"].sum()) == cm["fp"] and int(g["correct_negative"].sum()) == cm["tn"])
    res["timeline_equals_confusion_matrix"] = chk

    wm.to_csv(run / "wind_monthly_means_by_station.csv", index=False)
    em.to_csv(run / "event_outcomes_monthly_by_station.csv", index=False)
    wi.drop(columns=["start"]).to_csv(priv / "cohort_b_rows.csv", index=False)
    out = strip(res)
    (run / "benchmark_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": "cohort B benchmark", "spec": "GCV-W1-v1"})
    print(json.dumps({"counts": out["counts"], "clim": clim, "timeline_check": chk}, indent=1))
    p = out["wind"]["pooled"]
    print("WIND pooled", json.dumps(p["point"], indent=0))
    print(json.dumps({k: v for k, v in p["ci"].items() if k.startswith("d")}, indent=0))
    pe = out["events"]["pooled"]
    for k, v in pe["classifiers"].items():
        print(k, {m: (round(v[m], 4) if isinstance(v[m], float) else v[m]) for m in ("tp", "fn", "fp", "tn", "precision", "recall", "f1")})
    print(json.dumps(pe["probabilistic"], indent=0))
    print(json.dumps({k: v for k, v in pe["ci"].items() if k.startswith("d")}, indent=0))
    print(run)


B_W = {"W1": "wind_W1", "persistence": "wind_persist", "climatology": "wind_clim"}

if __name__ == "__main__":
    main()
