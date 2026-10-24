"""Shared helpers for the GALE-CAST frozen-W1 retrospective evaluation.

The source repository is READ-ONLY here. Nothing in this package writes to it,
to a database, or to any model/scaler file. Row-level outputs go to _private/.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import platform
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get("GALECAST_SRC", WORKSPACE.parent / "GALE-CAST_PROJECT"))  # source checkout, read-only (folder renamed 2026-10-24)
PRIVATE = WORKSPACE / "_private"
RUNS = WORKSPACE / "runs"

RAW_CSV = SRC / "Normalized_Dataset(Sheet1).csv"
PROCESSED_CSV = SRC / "data" / "processed_weather.csv"
SCALED_CSV = SRC / "data" / "scaled_weather.csv"
TRAINING_CSV = SRC / "Training.csv"

MODEL_FILE = SRC / "gale_cast_model_multioutput.keras"
SCALER_N = SRC / "scaler_X_normal_mo.save"
SCALER_A = SRC / "scaler_X_anomaly_mo.save"
SCALER_Y = SRC / "scaler_y_regression_mo.save"
THRESH_FILE = SRC / "galecast_thresholds.json"

PRIMARY = ["NAIA", "Sangley Point", "Science Garden"]
SEQ_LEN = 32

# exactly as experiments/w1x1/_train_w3.py lines 157-165, 304-318, 327-345
CS_SHORT = {"Science Garden": "SG", "NAIA": "NA", "Sangley Point": "SP", "Port Area": "PA"}
CROSS_STATION_COLS = [f"{st}_dir_{trig}_lag1" for st in CS_SHORT.values() for trig in ("sin", "cos")]
FEATURES_NORMAL = [
    "wind_speed", "rainfall",
    "mean_sea_level_pressure", "relative_humidity",
    "wind_acceleration", "pressure_tendency", "pressure_drop",
    "rainfall_change", "humidity_change", "humidity_lag1", "humidity_lag2", "humidity_7day_avg",
    "precip_anomaly", "wind_speed_3day_avg", "wind_speed_3day_max",
    "wind_std_3", "wind_speed_lag1", "wind_speed_lag2",
    "pressure_lag1", "month_sin", "month_cos",
    "heavy_rain_flag", "low_pressure_flag", "storm_signal",
] + CROSS_STATION_COLS
FEATURES_ANOMALY = ["pressure_tendency", "precip_anomaly", "pressure_drop", "storm_signal"]
COLS_SCALE_N = [
    "wind_acceleration", "pressure_tendency", "pressure_drop",
    "rainfall_change", "humidity_change", "precip_anomaly",
    "wind_speed_3day_avg", "wind_speed_3day_max", "wind_std_3",
    "wind_speed_lag1", "wind_speed_lag2", "pressure_lag1",
]
COLS_SCALE_A = ["pressure_tendency", "precip_anomaly", "pressure_drop"]

# Legacy event thresholds (process_weather.py lines 106-117; galecast_thresholds.json)
WIND_MOD, WIND_HIGH, PDROP_MOD, PDROP_HIGH = 10.8, 17.2, 3.0, 6.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lf(path: Path) -> str:
    """Hash with CRLF normalised to LF (git autocrlf makes raw bytes checkout-dependent)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def git(args: list[str], cwd: Path = SRC) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def new_run(prefix: str) -> Path:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{prefix}-{stamp}-{secrets.token_hex(3)}"
    d = RUNS / run_id
    d.mkdir(parents=True, exist_ok=False)
    (PRIVATE / "runs" / run_id).mkdir(parents=True, exist_ok=False)
    return d


def private_dir(run_dir: Path) -> Path:
    return PRIVATE / "runs" / run_dir.name


def environment() -> dict:
    import sklearn
    import tensorflow as tf
    import keras
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "tensorflow": tf.__version__,
        "keras": keras.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }


def frozen_artifact_hashes() -> dict:
    return {p.name: sha256_file(p) for p in (MODEL_FILE, SCALER_N, SCALER_A, SCALER_Y, THRESH_FILE)}


def _workspace_head() -> str | None:
    try:
        head = git(["rev-parse", "HEAD"], cwd=WORKSPACE)
        dirty = git(["status", "--porcelain", "--", "eval", "spec"], cwd=WORKSPACE)
        return head + ("+uncommitted-eval-changes" if dirty else "")
    except subprocess.CalledProcessError:
        return None  # no commit yet


def write_manifest(run_dir: Path, extra: dict) -> None:
    eval_code = {p.name: sha256_lf(p) for p in sorted((WORKSPACE / "eval").glob("*.py"))}
    m = {
        "run_id": run_dir.name,
        "written_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "source_repo_head": git(["rev-parse", "HEAD"]),
        "workspace_head": _workspace_head(),
        "frozen_artifacts_sha256": frozen_artifact_hashes(),
        "eval_code_sha256_lf": eval_code,
        "environment": environment(),
        **extra,
    }
    (run_dir / "manifest.json").write_text(json.dumps(m, indent=2, default=str), encoding="utf-8")


# ---------------------------------------------------------------- data
def load_processed() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_CSV, parse_dates=["date"])
    return df.sort_values(["station_name", "date"]).reset_index(drop=True)


def load_scaled() -> pd.DataFrame:
    df = pd.read_csv(SCALED_CSV, parse_dates=["date"])
    return df.sort_values(["station_name", "date"]).reset_index(drop=True)


def load_raw() -> pd.DataFrame:
    """Raw-equivalent observations with sentinels converted to NaN (no imputation)."""
    r = pd.read_csv(RAW_CSV)
    r["date"] = pd.to_datetime(r[["year", "month", "day"]])
    for c in ["rainfall", "relative_humidity", "wind_speed", "wind_direction",
              "station_pressure", "mean_sea_level_pressure"]:
        r[c] = pd.to_numeric(r[c], errors="coerce")
    r = r.replace(-999.0, np.nan)
    return r.sort_values(["station_name", "date"]).reset_index(drop=True)


def add_cross_station(df: pd.DataFrame) -> pd.DataFrame:
    """_train_w3.py lines 166-179: lag-1 bearing sin/cos of each real station, by date; NaN -> 0.0."""
    df = df.copy()
    b = np.arctan2(-df["u"].values, -df["v"].values)
    df["_cs_dir_sin"], df["_cs_dir_cos"] = np.sin(b), np.cos(b)
    wide = df.pivot(index="date", columns="station_name", values=["_cs_dir_sin", "_cs_dir_cos"])
    wide.columns = [f"{CS_SHORT.get(st, st)}_{col.replace('_cs_', '')}_lag1" for col, st in wide.columns]
    wide = wide.reindex(columns=CROSS_STATION_COLS).shift(1).reset_index()
    df = df.drop(columns=[c for c in CROSS_STATION_COLS if c in df.columns]).merge(wide, on="date", how="left")
    df = df.drop(columns=["_cs_dir_sin", "_cs_dir_cos"])
    df[CROSS_STATION_COLS] = df[CROSS_STATION_COLS].fillna(0.0)
    return df.sort_values(["station_name", "date"]).reset_index(drop=True)


def apply_station_scalers(df: pd.DataFrame, scalers: dict, cols_scale: list[str], features: list[str]) -> np.ndarray:
    """_train_w3.py apply_selective_scaler (lines 385-399)."""
    out = np.empty((len(df), len(cols_scale)), dtype=float)
    st = df["station_name"].values
    for s in np.unique(st):
        m = st == s
        out[m] = scalers.get(s, scalers["_global_fallback"]).transform(df.loc[m, cols_scale].values)
    scaled = pd.DataFrame(out, columns=cols_scale, index=df.index)
    passthrough = df[[c for c in features if c not in cols_scale]]
    return pd.concat([scaled, passthrough], axis=1)[features].values


# ---------------------------------------------------------------- model
def _register():
    import tensorflow as tf

    @tf.keras.utils.register_keras_serializable()
    def apply_reg_activations(x):  # identical to _train_w3.py lines 764-771
        wind_speed = tf.nn.relu(tf.gather(x, [0], axis=1))
        humidity = tf.sigmoid(tf.gather(x, [1], axis=1))
        sin_cos = tf.sigmoid(tf.gather(x, [2, 3], axis=1))
        rainfall = tf.sigmoid(tf.gather(x, [4], axis=1))
        pressure = tf.sigmoid(tf.gather(x, [5], axis=1))
        return tf.concat([wind_speed, humidity, sin_cos, rainfall, pressure], axis=1)

    return apply_reg_activations


_REGISTERED = None


def load_frozen_model(path: Path = MODEL_FILE):
    """Load read-only; compile=False so nothing about training state is touched."""
    global _REGISTERED
    import keras
    if _REGISTERED is None:
        _REGISTERED = _register()
    return keras.models.load_model(str(path), compile=False, safe_mode=False)


def lfs_model_copy(suffix: str, branch: str = "exp/precision-targeting") -> Path:
    """Copy a variant's LFS blob (read from .git/lfs) into _private/models/ with a .keras name."""
    pointer = git(["show", f"{branch}:gale_cast_model_multioutput{suffix}.keras"])
    oid = [l.split(":", 1)[1] for l in pointer.splitlines() if l.startswith("oid sha256:")][0]
    blob = SRC / ".git" / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    dst = PRIVATE / "models" / f"gale_cast_model_multioutput{suffix or '_live'}.keras"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copyfile(blob, dst)
    assert sha256_file(dst) == oid, f"hash mismatch for {suffix}"
    return dst


def lfs_or_git_blob(path_in_branch: str, branch: str = "exp/precision-targeting") -> Path:
    """Write a (non-LFS) git blob such as a .save scaler into _private/blobs/ and return its path."""
    dst = PRIVATE / "blobs" / branch.replace("/", "_") / path_in_branch
    dst.parent.mkdir(parents=True, exist_ok=True)
    data = subprocess.run(["git", "show", f"{branch}:{path_in_branch}"], cwd=SRC,
                          capture_output=True, check=True).stdout
    dst.write_bytes(data)
    return dst
