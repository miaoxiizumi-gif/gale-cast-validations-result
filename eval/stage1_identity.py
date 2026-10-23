"""Stage 1: identity of the deployed W1 (read-only checks, no scoring)."""
from __future__ import annotations

import json
import zipfile

import joblib
import numpy as np

import common as C

BRANCH = "exp/precision-targeting"


def lfs_oid(ref_path: str) -> str | None:
    try:
        txt = C.git(["show", ref_path])
    except Exception:
        return None
    for line in txt.splitlines():
        if line.startswith("oid sha256:"):
            return line.split(":", 1)[1]
    return None


def blob_sha256(ref_path: str) -> str:
    import hashlib
    import subprocess
    data = subprocess.run(["git", "show", ref_path], cwd=C.SRC, capture_output=True, check=True).stdout
    return hashlib.sha256(data).hexdigest()


def main():
    run = C.new_run("s1-identity")
    out: dict = {"run_id": run.name}

    live = C.frozen_artifact_hashes()
    out["deployed_files_in_source_checkout"] = {"commit": C.git(["rev-parse", "HEAD"]), "sha256": live}
    out["w1_branch_artifacts"] = {
        "branch_head": C.git(["rev-parse", BRANCH]),
        "gale_cast_model_multioutput_w3.keras_lfs_oid": lfs_oid(f"{BRANCH}:gale_cast_model_multioutput_w3.keras"),
        "scaler_X_normal_mo_w3.save": blob_sha256(f"{BRANCH}:scaler_X_normal_mo_w3.save"),
        "scaler_X_anomaly_mo_w3.save": blob_sha256(f"{BRANCH}:scaler_X_anomaly_mo_w3.save"),
        "scaler_y_regression_mo_w3.save": blob_sha256(f"{BRANCH}:scaler_y_regression_mo_w3.save"),
        "scaler_X_normal_mo_v12.save": blob_sha256(f"{BRANCH}:scaler_X_normal_mo_v12.save"),
    }
    w = out["w1_branch_artifacts"]
    out["identity_checks"] = {
        "model_equals_w3": live["gale_cast_model_multioutput.keras"] == w["gale_cast_model_multioutput_w3.keras_lfs_oid"],
        "scaler_normal_equals_w3": live["scaler_X_normal_mo.save"] == w["scaler_X_normal_mo_w3.save"],
        "scaler_anomaly_equals_w3": live["scaler_X_anomaly_mo.save"] == w["scaler_X_anomaly_mo_w3.save"],
        "scaler_y_equals_w3": live["scaler_y_regression_mo.save"] == w["scaler_y_regression_mo_w3.save"],
        "w3_scalers_equal_v12_scalers": w["scaler_X_normal_mo_w3.save"] == w["scaler_X_normal_mo_v12.save"],
    }

    with zipfile.ZipFile(C.MODEL_FILE) as z:
        meta = json.loads(z.read("metadata.json"))
        cfg = json.loads(z.read("config.json"))
    out["keras_archive_metadata"] = meta
    layers = cfg["config"]["layers"]
    out["layers"] = [
        {"name": l["config"].get("name", l.get("name")), "class": l["class_name"],
         **({"units": l["config"]["units"]} if "units" in l["config"] else {}),
         **({"activation": l["config"]["activation"]} if isinstance(l["config"].get("activation"), str) else {}),
         **({"rate": l["config"]["rate"]} if "rate" in l["config"] else {})}
        for l in layers
    ]

    model = C.load_frozen_model()
    out["model"] = {
        "name": model.name,
        "inputs": {t.name: list(t.shape) for t in model.inputs},
        "outputs": [list(t.shape) for t in model.outputs],
        "output_names": list(getattr(model, "output_names", []) or []),
        "params_total": int(model.count_params()),
    }

    rng = np.random.default_rng(0)
    xn32, xa32 = rng.random((2, 32, 32), dtype=np.float32), rng.random((2, 32, 4), dtype=np.float32)
    p = model.predict([xn32, xa32], verbose=0)
    out["inference_32_step"] = {"ok": True, "output_shapes": [list(np.asarray(a).shape) for a in p]}
    try:
        model.predict([xn32[:, :24], xa32[:, :24]], verbose=0)
        out["inference_24_step"] = {"ok": True}
    except Exception as e:  # record the class only; tracebacks can contain local paths
        out["inference_24_step"] = {"ok": False, "error_class": type(e).__name__,
                                    "message_head": str(e).splitlines()[0][:160]}

    sn, sa, sy = joblib.load(C.SCALER_N), joblib.load(C.SCALER_A), joblib.load(C.SCALER_Y)
    out["scalers"] = {
        "scaler_X_normal_mo": {"type": type(sn).__name__, "keys": sorted(sn.keys()),
                               "n_features_each": sorted({int(s.n_features_in_) for s in sn.values()})},
        "scaler_X_anomaly_mo": {"type": type(sa).__name__, "keys": sorted(sa.keys()),
                                "n_features_each": sorted({int(s.n_features_in_) for s in sa.values()})},
        "scaler_y_regression_mo": {"type": type(sy).__name__, "n_features": int(sy.n_features_in_),
                                   # wind column range is set by the 4 invented extreme_rows (_train_w3.py:480-486)
                                   "wind_col_data_min": float(sy.data_min_[0]), "wind_col_data_max": float(sy.data_max_[0])},
    }
    out["thresholds_file"] = json.loads(C.THRESH_FILE.read_text(encoding="utf-8"))

    # recency-weight transform that app.py run_prediction applies (never used in training)
    out["notes"] = [
        "Hugging Face Space main 8ffbbb5 (2026-10-13) pointer oid and scaler blob hashes were checked separately "
        "by a read-only blobless clone; see STAGE1 report.",
    ]
    (run / "stage1_identity.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": 1})
    print(json.dumps({k: out[k] for k in ("identity_checks", "model", "inference_24_step", "scalers")}, indent=2))
    print(run)


if __name__ == "__main__":
    main()
