"""Cohort B builder: identical next-day cases for W1, baselines and variants (spec §2-§4)."""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

import common as C

SPEC = json.loads((C.WORKSPACE / "spec" / "EVAL_SPEC_v1.json").read_text())
D0, D1 = pd.Timestamp(SPEC["target_dates"][0]), pd.Timestamp(SPEC["target_dates"][1])
CLIM0, CLIM1 = pd.Timestamp(SPEC["climatology_fit_dates"][0]), pd.Timestamp(SPEC["climatology_fit_dates"][1])
DEV0, DEV1 = pd.Timestamp(SPEC["development_dates"][0]), pd.Timestamp(SPEC["development_dates"][1])
CORE = ["wind_speed", "mean_sea_level_pressure", "relative_humidity", "rainfall", "wind_direction"]


def truth_table() -> pd.DataFrame:
    """Per primary station and date: unimputed wind, pressure fall, event label E and its parts."""
    raw = C.load_raw()
    raw = raw[raw["station_name"].isin(C.PRIMARY)].copy()
    raw["mslp_prev"] = raw.groupby("station_name")["mean_sea_level_pressure"].shift(1)
    prev_date = raw.groupby("station_name")["date"].shift(1)
    raw.loc[(raw["date"] - prev_date) != pd.Timedelta(days=1), "mslp_prev"] = np.nan
    raw["pfall"] = raw["mslp_prev"] - raw["mean_sea_level_pressure"]
    det = raw["wind_speed"].notna() & raw["pfall"].notna()
    w_ev = raw["wind_speed"] >= C.WIND_MOD
    p_ev = raw["pfall"] >= C.PDROP_MOD
    raw["E"] = np.where(det, (w_ev | p_ev).astype(float), np.nan)
    raw["E_wind_only"] = np.where(det, (w_ev & ~p_ev).astype(float), np.nan)
    raw["E_pressure_only"] = np.where(det, (p_ev & ~w_ev).astype(float), np.nan)
    raw["E_both"] = np.where(det, (p_ev & w_ev).astype(float), np.nan)
    raw["gale_wind"] = np.where(raw["wind_speed"].notna(), (raw["wind_speed"] >= C.WIND_HIGH).astype(float), np.nan)
    raw["any_core_missing"] = raw[CORE].isna().any(axis=1)
    return raw[["station_name", "date", "wind_speed", "pfall", "E", "E_wind_only", "E_pressure_only", "E_both",
                "gale_wind", "any_core_missing"]].rename(columns={"station_name": "station"})


def processed_inputs_train_consistent(scaler_n, scaler_a) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """S-TRAIN: processed_weather (4 stations for cross-station lags) + per-station scalers."""
    pw = C.add_cross_station(C.load_processed())
    Xn = C.apply_station_scalers(pw, scaler_n, C.COLS_SCALE_N, C.FEATURES_NORMAL)
    Xa = C.apply_station_scalers(pw, scaler_a, C.COLS_SCALE_A, C.FEATURES_ANOMALY)
    return pw, Xn.astype(np.float32), Xa.astype(np.float32)


def processed_inputs_legacy() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """S-LEGACY: pooled scaled_weather + processed humidity lags; cross-station from the 3 stations only."""
    sw, pw = C.load_scaled(), C.load_processed()
    sw = sw[sw["station_name"].isin(C.PRIMARY)]
    df = sw.merge(pw[["station_name", "date", "humidity_lag1", "humidity_lag2", "humidity_7day_avg"]],
                  on=["station_name", "date"], how="left")
    df = C.add_cross_station(df.sort_values(["station_name", "date"]).reset_index(drop=True))
    return df, df[C.FEATURES_NORMAL].values.astype(np.float32), df[C.FEATURES_ANOMALY].values.astype(np.float32)


def window_index(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per (primary station, target date d in range) whose 32 rows t-31..t (t=d-1) exist consecutively."""
    rec = []
    for s in C.PRIMARY:
        idx = np.where(frame["station_name"].values == s)[0]
        dates = frame["date"].values[idx]
        pos = {pd.Timestamp(d): i for d, i in zip(dates, idx)}
        for d in pd.date_range(D0, D1, freq="D"):
            t = d - pd.Timedelta(days=1)
            if t not in pos:
                continue
            end = pos[t]
            start = end - (C.SEQ_LEN - 1)
            if start < idx.min():
                continue
            span = pd.Timestamp(frame["date"].values[end]) - pd.Timestamp(frame["date"].values[start])
            if frame["station_name"].values[start] != s or span != pd.Timedelta(days=C.SEQ_LEN - 1):
                continue
            rec.append((s, d, start))
    return pd.DataFrame(rec, columns=["station", "date", "start"])


def predict(model, Xn, Xa, starts: np.ndarray, scaler_y) -> tuple[np.ndarray, np.ndarray]:
    off = np.arange(C.SEQ_LEN)
    bn, ba = Xn[starts[:, None] + off], Xa[starts[:, None] + off]
    out = model.predict([bn, ba], verbose=0, batch_size=512)
    wind = np.maximum(scaler_y.inverse_transform(out[1])[:, 0], 0.0)
    return out[0].ravel(), wind


def climatologies(truth: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    fit = truth[(truth["date"] >= CLIM0) & (truth["date"] <= CLIM1)].copy()
    fit["month"] = fit["date"].dt.month
    wind_clim = fit.dropna(subset=["wind_speed"]).groupby(["station", "month"])["wind_speed"].mean()
    ev = fit[fit["date"] >= CLIM0 + pd.Timedelta(days=1)].dropna(subset=["E"])
    ev_clim = ev.groupby(["station", "month"])["E"].mean()
    return wind_clim, ev_clim


def build(model=None, scaler_n=None, scaler_a=None, scaler_y=None, legacy_inputs=False) -> pd.DataFrame:
    """Return the full candidate table (all target dates/stations with a window); eligibility flags included."""
    model = model or C.load_frozen_model()
    scaler_n = scaler_n or joblib.load(C.SCALER_N)
    scaler_a = scaler_a or joblib.load(C.SCALER_A)
    scaler_y = scaler_y or joblib.load(C.SCALER_Y)
    frame, Xn, Xa = processed_inputs_legacy() if legacy_inputs else processed_inputs_train_consistent(scaler_n, scaler_a)
    wi = window_index(frame)
    p, w = predict(model, Xn, Xa, wi["start"].values, scaler_y)
    wi["p_raw"], wi["wind_W1"] = p, w
    wi["p_x1"] = wi.groupby("date")["p_raw"].transform("mean")
    wi["n_stations_on_date"] = wi.groupby("date")["p_raw"].transform("size")

    truth = truth_table()
    tt = truth.set_index(["station", "date"])
    key_d = pd.MultiIndex.from_arrays([wi["station"], wi["date"]])
    key_t = pd.MultiIndex.from_arrays([wi["station"], wi["date"] - pd.Timedelta(days=1)])
    for c in ["wind_speed", "pfall", "E", "E_wind_only", "E_pressure_only", "E_both", "gale_wind"]:
        wi[c if c != "wind_speed" else "wind_obs"] = tt[c].reindex(key_d).values
    wi["wind_persist"] = tt["wind_speed"].reindex(key_t).values
    wi["E_persist"] = tt["E"].reindex(key_t).values

    # imputed values inside the 32-day window (raw core value missing on any date t-31..t)
    miss = truth.set_index(["station", "date"])["any_core_missing"]
    flags = []
    for s, d in zip(wi["station"], wi["date"]):
        dates = pd.date_range(d - pd.Timedelta(days=C.SEQ_LEN), d - pd.Timedelta(days=1), freq="D")
        flags.append(bool(miss.reindex(pd.MultiIndex.from_arrays([[s] * len(dates), dates])).fillna(False).any()))
    wi["window_has_imputed"] = flags

    wind_clim, ev_clim = climatologies(truth)
    mk = pd.MultiIndex.from_arrays([wi["station"], wi["date"].dt.month])
    wi["wind_clim"] = wind_clim.reindex(mk).values
    wi["E_clim"] = ev_clim.reindex(mk).values

    wi["elig_wind"] = wi["wind_obs"].notna() & wi["wind_persist"].notna() & wi["wind_clim"].notna()
    wi["elig_event"] = wi["E"].notna() & wi["E_persist"].notna() & (wi["n_stations_on_date"] == 3) & wi["E_clim"].notna()
    return wi


def dev_climatology_threshold() -> dict:
    """Event-climatology classification threshold, chosen on development target dates only (spec §4)."""
    truth = truth_table()
    _, ev_clim = climatologies(truth)
    dev = truth[(truth["date"] >= DEV0) & (truth["date"] <= DEV1)].dropna(subset=["E"]).copy()
    dev["p"] = ev_clim.reindex(pd.MultiIndex.from_arrays([dev["station"], dev["date"].dt.month])).values
    best = (-1.0, None, None)
    for thr in sorted(dev["p"].dropna().unique()):
        pred = dev["p"] >= thr
        tp = int((pred & (dev["E"] == 1)).sum()); fp = int((pred & (dev["E"] == 0)).sum())
        fn = int((~pred & (dev["E"] == 1)).sum())
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        if f1 >= best[0]:
            best = (f1, float(thr), dict(tp=tp, fp=fp, fn=fn, tn=int(len(dev) - tp - fp - fn)))
    return {"dev_cases": int(len(dev)), "dev_events": int(dev["E"].sum()), "best_dev_f1": best[0],
            "threshold": best[1] if best[0] > 0 else None, "dev_matrix": best[2]}
