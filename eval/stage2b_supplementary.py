"""Stage 2b: does Training.csv reproduce W1's documented supplementary counts? (aggregate only)

The paper states 1,143 'gale events' in a 78,955-row training set. The real-station training rows
(reconstructed in Stage 2) hold 86 positives. If Training.csv, processed by process_weather.py's
Section A rules, yields 1,143 - 86 = 1,057 positives, that is consistent with (not proof of) it being the
source of `processed_luzon_supplementary`. Both labelling rules in process_weather.py are tried.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import common as C


def process(t: pd.DataFrame, rule: str) -> pd.DataFrame:
    t = t.copy()
    num = ["rainfall", "wind_speed", "wind_direction", "mean_sea_level_pressure", "relative_humidity",
           "station_pressure"]
    t[num] = t[num].apply(pd.to_numeric, errors="coerce")
    t = t.replace(-999.0, np.nan)
    t["rainfall"] = t["rainfall"].replace(-1.0, 0.05)
    t[num] = t.groupby("station_name")[num].ffill().bfill()  # same (ungrouped bfill) as process_weather.py:48
    t["date"] = pd.to_datetime(t[["year", "month", "day"]])
    t = t.sort_values(["station_name", "date"]).reset_index(drop=True)
    pt = t.groupby("station_name")["mean_sea_level_pressure"].diff().fillna(0)
    pdrop = -pt
    if rule == "section_A_study_rule":  # process_weather.py:106-118
        flag = np.where((t["wind_speed"] >= 17.2) | (pdrop >= 6.0), 2,
                        np.where((t["wind_speed"] >= 10.8) | (pdrop >= 3.0), 1, 0))
    else:  # process_weather.py:247 (synthetic/processed_gales rule)
        flag = ((t["wind_speed"] >= 12) | (pdrop <= -3)).astype(int)
    t["gale_flag"] = flag
    t["target_gale"] = t.groupby("station_name")["gale_flag"].shift(-1)
    return t[t["target_gale"].notna()]


def main():
    run = C.new_run("s2b-supplementary")
    raw = pd.read_csv(C.TRAINING_CSV)
    raw.columns = [c.replace("_training", "") for c in raw.columns]
    out = {"run_id": run.name, "documented": {"train_rows": 78955, "train_gale_events_paper": 1143,
                                              "real_station_train_positives_stage2": 86}}
    for rule in ("section_A_study_rule", "section_B_sign_reversed_rule"):
        p = process(raw, rule)
        out[rule] = {"rows": int(len(p)), "positives_ge1": int((p["target_gale"] >= 1).sum()),
                     "positives_eq2": int((p["target_gale"] == 2).sum()),
                     "positives_plus_real_86": int((p["target_gale"] >= 1).sum()) + 86}
    out["matches_1143_under"] = [r for r in ("section_A_study_rule", "section_B_sign_reversed_rule")
                                 if out[r]["positives_plus_real_86"] == 1143]
    (run / "supplementary_counts.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    C.write_manifest(run, {"stage": "2b"})
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
