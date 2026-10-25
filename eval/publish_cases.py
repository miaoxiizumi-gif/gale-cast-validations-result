"""Publish the selected thesis figures authorized for panel review (2026-10-26).

Only the selected windows are exported; model artifacts and the full row archive
are never copied. Run folders and selection records remain unchanged.
"""
from pathlib import Path
import json
import shutil

import pandas as pd

import common as C


def publish(X, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    rows = pd.read_csv(C.private_dir(X['runs']['w']) / 'website_cohort_rows.csv')
    outputs = []
    for key, summary in [('case', 'PRIVATE_selection_summary.json'),
                         ('case2', 'PRIVATE_selection_summary_v2.json'),
                         ('case3', 'PRIVATE_selection_summary_v3.json'),
                         ('case4', 'PRIVATE_selection_summary_v4.json')]:
        run = X['runs'][key]
        selections = json.loads((C.private_dir(run) / summary).read_text(encoding='utf-8'))
        source = C.PRIVATE / 'thesis_export' / run.name
        for png in sorted(source.glob('PF-*.png')):
            station = next((s for s in C.PRIMARY if png.stem.endswith(s.replace(' ', '_'))), None)
            window = selections['per_station'].get(station, {}) if station else selections.get('common', {})
            dates = window.get('window', [])
            assert dates, f'No selected dates for {png}'
            selected = rows[rows['date'].isin(dates)]
            if station:
                selected = selected[selected['station'] == station]
            assert len(selected), png
            # Readable labels in CSV; values stay exactly as stored.
            selected.rename(columns=lambda c: c.replace('W1', 'GALE-CAST Model-W1')).to_csv(destination / f'{png.stem}.csv', index=False)
            for suffix in ('.png', '.svg'):
                shutil.copy2(png.with_suffix(suffix), destination / (png.stem + suffix))
            outputs.append(destination / png.name)
    return outputs
