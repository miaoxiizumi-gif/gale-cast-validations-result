"""POST-HOC DIAGNOSTIC 2 (not in the declared spec; selects nothing).

Which input scaling did W1 actually learn from? If training used per-station scaling (as the committed
_train_w3.py says), W1 should fit its own TRAINING-period windows better under per-station scaling than
under the pooled scaled_weather values. Checked on primary-station target dates before 2020-10-15
(in-sample) and on the early-stopping period 2020-10-15..2021-10-14.
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

import cohort_b as B
import common as C
import metrics as M
from diag_inputs import frame


def main():
    run = C.new_run("diag-insample")
    model, sy = C.load_frozen_model(), joblib.load(C.SCALER_Y)
    truth = B.truth_table()[["station", "date", "E"]]
    periods = {"train_in_sample": ("2015-03-01", "2020-10-14"), "early_stop": ("2020-10-15", "2021-10-14")}
    out = {"run_id": run.name, "label": "post-hoc diagnostic; selects nothing", "results": {}}
    for scaling in ("station", "pooled"):
        base, Xn, Xa = frame(scaling, "processed", "4")
        for pname, (a, b) in periods.items():
            B.D0, B.D1 = pd.Timestamp(a), pd.Timestamp(b)
            wi = B.window_index(base)
            p, w = B.predict(model, Xn, Xa, wi["start"].values, sy)
            wi["p"] = p
            m = wi.merge(truth, on=["station", "date"]).dropna(subset=["E"])
            y = m["E"].values.astype(int)
            out["results"][f"{scaling}|{pname}"] = {"cases": int(len(m)), "events": int(y.sum()),
                                                    "pr_auc_raw": M.pr_auc(y, m["p"].values),
                                                    "brier_raw": M.brier(y, m["p"].values)}
            print(scaling, pname, out["results"][f"{scaling}|{pname}"])
    (run / "diag_insample.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    C.write_manifest(run, {"stage": "post-hoc diagnostic 2", "spec": "GCV-W1-v1 (not part of it)"})
    print(run)


if __name__ == "__main__":
    main()
