"""Stage 2: reconstruct W1's historical split from _train_w3.py's rules and count every partition.

Aggregate counts only. Reads the tracked processed_weather.csv (assumed, not proven, to equal the
Postgres processed_weather table W1 read) and the untracked Training.csv (unverified provenance).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import common as C

ES_START, ES_END, TEST_START = pd.Timestamp("2020-10-15"), pd.Timestamp("2021-10-14"), pd.Timestamp("2021-10-15")


def span(d: pd.DataFrame) -> dict:
    if d.empty:
        return {"rows": 0}
    return {"rows": int(len(d)), "first": str(d["date"].min().date()), "last": str(d["date"].max().date()),
            "label_pos_ge1": int((d["target_gale"] >= 1).sum()),
            "label_pos_eq2": int((d["target_gale"] == 2).sum())}


def by_station(d: pd.DataFrame) -> dict:
    return {s: span(g) for s, g in d.groupby("station_name")}


def windows(d: pd.DataFrame) -> dict:
    """create_sequences_safe (_train_w3.py 536-637) on a (station,date)-sorted frame: count only."""
    d = d.sort_values(["station_name", "date"]).reset_index(drop=True)
    st = d["station_name"].values
    y = (d["target_gale"].values >= 1).astype(int)
    n, keep, pos, dropped = len(d), 0, 0, 0
    per = {}
    for i in range(n - C.SEQ_LEN):
        s = st[i]
        if st[i + C.SEQ_LEN - 1] == s and st[i + C.SEQ_LEN] == s:
            keep += 1
            pos += int(y[i + C.SEQ_LEN - 1] >= 1)
            per.setdefault(s, [0, 0])
            per[s][0] += 1
            per[s][1] += int(y[i + C.SEQ_LEN - 1] >= 1)
        else:
            dropped += 1
    return {"windows": keep, "positive_windows": pos, "dropped_cross_station": dropped,
            "by_station": {k: {"windows": v[0], "positive": v[1]} for k, v in per.items()}}


def raw_inventory(raw: pd.DataFrame) -> dict:
    out = {}
    for s, g in raw.groupby("station_name"):
        full = pd.date_range(g["date"].min(), g["date"].max(), freq="D")
        out[s] = {
            "rows": int(len(g)), "first": str(g["date"].min().date()), "last": str(g["date"].max().date()),
            "missing_calendar_days": int(len(full.difference(g["date"]))),
            "duplicate_dates": int(g["date"].duplicated().sum()),
            "missing_wind_speed": int(g["wind_speed"].isna().sum()),
            "missing_mslp": int(g["mean_sea_level_pressure"].isna().sum()),
            "missing_rainfall": int(g["rainfall"].isna().sum()),
            "non_integer_wind_values": int(((g["wind_speed"].dropna() % 1) != 0).sum()),
            "days_wind_ge_10_8": int((g["wind_speed"] >= C.WIND_MOD).sum()),
            "days_wind_ge_17_2": int((g["wind_speed"] >= C.WIND_HIGH).sum()),
            "max_wind_ms": float(g["wind_speed"].max()),
        }
    return out


def supplementary_diagnostics() -> dict:
    if not C.TRAINING_CSV.exists():
        return {"available": False}
    t = pd.read_csv(C.TRAINING_CSV)
    t.columns = [c.replace("_training", "") for c in t.columns]
    t["date"] = pd.to_datetime(t[["year", "month", "day"]])
    for c in ["wind_speed", "mean_sea_level_pressure", "relative_humidity", "rainfall"]:
        t[c] = pd.to_numeric(t[c], errors="coerce").replace(-999.0, np.nan)
    t = t.sort_values(["station_name", "date"])
    pdrop = -t.groupby("station_name")["mean_sea_level_pressure"].diff()
    study_rule = (t["wind_speed"] >= C.WIND_MOD) | (pdrop >= C.PDROP_MOD)
    smote_rule = (t["wind_speed"] >= 12) | (pdrop <= -3)  # process_weather.py:247 rule for synthetic rows
    days = t.groupby("station_name")["date"].agg(["min", "max", "count"])
    w = t["wind_speed"].dropna()
    mslp = t["mean_sea_level_pressure"].dropna()
    return {
        "available": True,
        "file_sha256": C.sha256_file(C.TRAINING_CSV),
        "rows": int(len(t)), "stations": int(t["station_name"].nunique()),
        "first": str(t["date"].min().date()), "last": str(t["date"].max().date()),
        "rows_per_station_min_max": [int(days["count"].min()), int(days["count"].max())],
        "fraction_wind_non_integer": float(((w % 1) != 0).mean()),
        "fraction_mslp_not_0p1_resolution": float((np.abs(mslp * 10 - np.round(mslp * 10)) > 1e-6).mean()),
        "fraction_days_study_rule_positive": float(study_rule.mean()),
        "fraction_days_sign_reversed_rule_positive": float(smote_rule.mean()),
        "days_wind_ge_10_8": int((t["wind_speed"] >= C.WIND_MOD).sum()),
        "days_wind_ge_17_2": int((t["wind_speed"] >= C.WIND_HIGH).sum()),
        "overlaps_primary_test_dates": bool(t["date"].max() >= TEST_START),
        "rows_dated_in_es_period": int(((t["date"] >= ES_START) & (t["date"] <= ES_END)).sum()),
        "rows_dated_in_test_period": int((t["date"] >= TEST_START).sum()),
        "rows_minus_one_per_station": int(len(t) - t["station_name"].nunique()),
    }


def main():
    run = C.new_run("s2-partitions")
    raw, pw = C.load_raw(), C.load_processed()
    is_val = pw["station_name"].isin(C.PRIMARY)
    is_test = pw["date"] >= TEST_START
    is_es = (pw["date"] >= ES_START) & (pw["date"] <= ES_END)

    test_df = pw[is_val & is_test]
    es_df = pw[is_val & is_es]
    train_real = pw[~(is_val & (is_test | is_es))]
    es_ctx_start = ES_START - pd.Timedelta(days=32)
    es_wide = pw[is_val & (pw["date"] >= es_ctx_start) & (pw["date"] <= ES_END)]

    pa = train_real[train_real["station_name"] == "Port Area"]
    out = {
        "run_id": run.name,
        "inputs": {"processed_weather.csv_sha256_lf": C.sha256_lf(C.PROCESSED_CSV),
                   "raw_csv_sha256": C.sha256_file(C.RAW_CSV)},
        "raw_observations": raw_inventory(raw),
        "processed_rows": by_station(pw),
        "w1_split_reconstructed": {
            "rule_source": "exp/precision-targeting:experiments/w1x1/_train_w3.py lines 37-38, 68-69, 205-211, 262-264",
            "train_real": {"total": span(train_real), "by_station": by_station(train_real)},
            "early_stop_narrow": {"total": span(es_df), "by_station": by_station(es_df)},
            "early_stop_widened_context": {"total": span(es_wide)},
            "test": {"total": span(test_df), "by_station": by_station(test_df)},
            "port_area_rows_dated_in_es_period": int(((pa["date"] >= ES_START) & (pa["date"] <= ES_END)).sum()),
            "port_area_rows_dated_in_test_period": int((pa["date"] >= TEST_START).sum()),
            "windows_train_real_only": windows(train_real),
            "windows_early_stop_widened": windows(es_wide),
            "windows_test_strict_per_station": {
                "windows": int(sum(max(0, len(g) - C.SEQ_LEN) for _, g in test_df.groupby("station_name"))),
            },
        },
        "documented_claims": {
            "THRESHOLD_CONFIG.md": {"TRAIN_rows": 78955, "TUNE_rows": 1095, "TEST_rows": 3519, "TEST_windows": 3423,
                                    "real_train_rows_implied": 6342 + 3225, "supplementary_rows_implied": 69388},
            "_train_w3.py comment line 247": {"tune_rows": 1095, "tune_gale_days": 17},
        },
        "supplementary_Training_csv": supplementary_diagnostics(),
    }
    tr = out["w1_split_reconstructed"]
    out["claim_checks"] = {
        "train_real_rows_match_9567": tr["train_real"]["total"]["rows"] == 9567,
        "tune_rows_match_1095": tr["early_stop_narrow"]["total"]["rows"] == 1095,
        "test_rows_match_3519": tr["test"]["total"]["rows"] == 3519,
        "test_windows_match_3423": tr["windows_test_strict_per_station"]["windows"] == 3423,
        "supplementary_rows_match_69388_plus_one_per_station":
            out["supplementary_Training_csv"].get("rows_minus_one_per_station") == 69388,
        "TRAIN_78955_equals_real_plus_69388": tr["train_real"]["total"]["rows"] + 69388 == 78955,
    }
    (run / "stage2_partitions.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": 2})
    print(json.dumps(out["claim_checks"], indent=2))
    print(json.dumps({k: tr[k] for k in ("port_area_rows_dated_in_es_period", "port_area_rows_dated_in_test_period")}))
    print(json.dumps({k: v["total"] for k, v in tr.items() if isinstance(v, dict) and "total" in v}, indent=1))
    print(json.dumps(tr["windows_train_real_only"]["by_station"]), tr["windows_train_real_only"]["windows"],
          tr["windows_train_real_only"]["positive_windows"], tr["windows_early_stop_widened"]["windows"],
          tr["windows_early_stop_widened"]["positive_windows"])
    print(json.dumps(out["supplementary_Training_csv"], indent=1))
    print(json.dumps(out["raw_observations"], indent=1))
    print(run)


if __name__ == "__main__":
    main()
