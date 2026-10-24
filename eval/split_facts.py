"""Facts for SPLIT_DESIGN_ASSESSMENT.md: rows, study-label events and seasonal coverage per primary-station partition.

Label = processed gale_flag(d) >= 1 (wind >= 10.8 m/s or same-station pressure fall >= 3 hPa), as used by W1 training.
Aggregates only.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import common as C

PARTS = {"training": ("2015-01-01", "2020-10-14"), "tuning": ("2020-10-15", "2021-10-14"),
         "evaluation": ("2021-10-15", "2024-12-31")}
SEASON = {12: "Dec-Feb (NE monsoon)", 1: "Dec-Feb (NE monsoon)", 2: "Dec-Feb (NE monsoon)",
          3: "Mar-May (dry/hot)", 4: "Mar-May (dry/hot)", 5: "Mar-May (dry/hot)",
          6: "Jun-Aug (SW monsoon)", 7: "Jun-Aug (SW monsoon)", 8: "Jun-Aug (SW monsoon)",
          9: "Sep-Nov (late typhoon season)", 10: "Sep-Nov (late typhoon season)", 11: "Sep-Nov (late typhoon season)"}


def main():
    run = C.new_run("split-facts")
    p = C.load_processed()
    p = p[p["station_name"].isin(C.PRIMARY)].copy()
    p["L_wind"] = p["wind_speed"] >= C.WIND_MOD
    p["L_press"] = p["pressure_drop"] >= C.PDROP_MOD
    p["L"] = p["L_wind"] | p["L_press"]
    res, rows = {"run_id": run.name, "label": "processed gale_flag >= 1", "partitions": {}}, []
    for name, (a, b) in PARTS.items():
        g = p[(p["date"] >= a) & (p["date"] <= b)]
        ev = g[g["L"]]
        dates = np.sort(ev["date"].unique())
        episodes = int(1 + (np.diff(dates).astype("timedelta64[D]").astype(int) > 1).sum()) if len(dates) else 0
        r = {"first": f"{g['date'].min():%Y-%m-%d}", "last": f"{g['date'].max():%Y-%m-%d}", "rows": int(len(g)),
             "years_covered": round((g["date"].max() - g["date"].min()).days / 365.25, 2),
             "events": int(ev.shape[0]), "event_dates": int(len(dates)), "episodes_consecutive_dates": episodes,
             "pressure_only": int((ev.L_press & ~ev.L_wind).sum()), "wind_only": int((ev.L_wind & ~ev.L_press).sum()),
             "both": int((ev.L_wind & ev.L_press).sum()),
             "calendar_months_present": int(g["date"].dt.month.nunique()),
             "events_by_season": ev["date"].dt.month.map(SEASON).value_counts().to_dict(),
             "rows_by_season": g["date"].dt.month.map(SEASON).value_counts().to_dict(),
             "events_by_station": ev["station_name"].value_counts().to_dict()}
        res["partitions"][name] = r
        for s, n in r["events_by_season"].items():
            rows.append({"partition": name, "season": s, "events": n, "rows": r["rows_by_season"][s]})
    pd.DataFrame(rows).to_csv(run / "events_by_partition_season.csv", index=False)
    (run / "split_facts.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    C.write_manifest(run, {"stage": "split facts (amendment A2 documentation)"})
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
