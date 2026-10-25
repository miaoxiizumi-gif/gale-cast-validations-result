"""Read-only comparison summaries from saved plot tables.

Fractions retain the exact arithmetic of exported decimal values. No inference,
threshold adjustment, baseline fitting or model-artifact access occurs here.
"""
from __future__ import annotations

import csv
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path

from terms import MODEL, text as public_text

CASE_VARIABLES = {
    'PF-H': ('wind', 'mslp'), 'PF-I': ('wind',),
    'PF-J': ('wind', 'mslp', 'humidity', 'rainfall'), 'PF-K': ('wind',),
    'PF-O': ('wind', 'mslp', 'humidity', 'rainfall'),
    'PF-P': ('wind', 'mslp', 'humidity', 'rainfall'),
    'PF-R': ('wind', 'mslp', 'humidity', 'rainfall'),
}
NON_COMPARATORS = {'PF-A_website_confusion_matrix', 'PF-B_station_outcomes',
                   'PF-G_observed_vs_predicted', 'F1_partitions'}
VARIABLES = {'wind': ('Wind speed', 'm/s'), 'mslp': ('Mean sea level pressure', 'hPa'),
             'humidity': ('Relative humidity', '%'), 'rainfall': ('Daily rainfall', 'mm')}
PERIODS = {'A': '2021-11-16 to 2024-12-30', 'B': '2021-10-15 to 2024-12-31'}


def read(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def number(value):
    return None if value is None or str(value).lower() in ('', 'nan', 'none') else Fraction(str(value))


def decimal(value):
    if value is None:
        return None
    with localcontext() as ctx:
        ctx.prec = 40
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def row(context, metric, unit, n, model, persistence, climatology, *, aggregation='summary'):
    values = [number(v) if not isinstance(v, Fraction) else v for v in (model, persistence, climatology)]
    assert all(v is not None for v in values), (context, metric)
    m, p, c = values
    return {'context': public_text(context), 'metric': public_text(metric), 'unit': unit, 'n': int(n), 'aggregation': aggregation,
            'model': decimal(m), 'persistence': decimal(p), 'climatology': decimal(c),
            'gap_persistence': decimal(m - p), 'gap_climatology': decimal(m - c),
            'model_fraction': str(m), 'persistence_fraction': str(p), 'climatology_fraction': str(c),
            'gap_persistence_fraction': str(m - p), 'gap_climatology_fraction': str(m - c)}


def case_rows(name, records):
    family = name.split('_')[0]
    summary, daily, omissions = [], [], []
    for station in dict.fromkeys(r['station'] for r in records):
        selected = [r for r in records if r['station'] == station]
        dates = sorted(r['date'] for r in selected)
        for variable in CASE_VARIABLES[family]:
            title, unit = VARIABLES[variable]
            errors = []
            for r in selected:
                values = [number(r[key]) for key in ('obs_' + variable, MODEL + '_' + variable,
                                                     'pers_' + variable, 'clim_' + variable)]
                if any(v is None for v in values):
                    omissions.append(f'{station}, {r["date"]}, {title}')
                    continue
                observed, *predictions = values
                e = [abs(predicted - observed) for predicted in predictions]
                errors.append(e)
                daily.append(row(f'{station} | {r["date"]}', title + ' absolute error', unit, 1, *e, aggregation='daily'))
            if errors:
                means = [sum((e[i] for e in errors), Fraction()) / len(errors) for i in range(3)]
                summary.append(row(f'{station} | ' + ', '.join(dates), title + ' window MAE', unit, len(errors), *means))
    assert summary, name
    return summary, daily, omissions


def make(name, path, X):
    if name in NON_COMPARATORS:
        return None
    records = read(path)
    rows, daily, omissions, note = [], [], [], ''
    family = name.split('_')[0]
    if family in CASE_VARIABLES:
        rows, daily, omissions = case_rows(name, records)
        note = ('Window MAE is calculated from the plotted next-day forecasts, separately by station and variable. '
                'Every comparison uses the same dates with observations and all three forecasts present. '
                'Daily absolute-error gaps are provided below; selected windows describe these dates only.')
    elif name in ('PF-C_event_metrics_overall', 'PF-D_event_metrics_by_station'):
        group_key = 'group' if name.startswith('PF-C') else 'station'
        for group in dict.fromkeys(r[group_key] for r in records):
            for metric in ('precision', 'recall', 'f1'):
                subset = {r['procedure']: r for r in records if r[group_key] == group and r['metric'] == metric}
                cohort = group if group_key == 'group' else 'A'
                station = 'pooled' if group_key == 'group' else group
                n = X[cohort]['events'][station]['classifiers']['W1+X1@0.601']['n']
                rows.append(row(f'{cohort} | {station} | {PERIODS[cohort]}', metric.upper() if metric == 'f1' else metric.title(),
                                'score (0-1)', n, *[subset[p]['value'] for p in ('W1+X1 (0.601)', 'Event persistence', 'Event climatology')]))
        note = 'Score gaps are differences on the 0-1 scale, not relative percentage changes. Cohorts and stations are compared separately.'
    elif name == 'PF-E_precision_recall_curves':
        classifiers = X['A']['events']['pooled']['classifiers']
        clim = next(k for k in classifiers if k.startswith('event_climatology'))
        for metric in ('precision', 'recall'):
            rows.append(row(f'A | operating threshold 0.601 | {PERIODS["A"]}', metric.title(), 'score (0-1)',
                            classifiers['W1+X1@0.601']['n'], *[classifiers[k][metric] for k in ('W1+X1@0.601', 'event_persistence', clim)]))
        note = ('These are operating-point precision and recall comparisons from the same saved cohort. '
                'Climatology uses its saved tuning-year warning threshold and is additional context, not the dashed prevalence line. '
                'No persistence PR-AUC is inferred from its single plotted point.')
    elif name == 'PF-L_composite_validation':
        for r in records:
            title, unit = VARIABLES[r['variable']]
            rows.append(row(r['dates_evaluated'], title + ' MAE', unit, r['n'],
                            r['mae_W1'], r['mae_persistence'], r['mae_climatology']))
        note = 'Each variable uses the date definition and case count in its own panel. These are selected wind, pressure and humidity comparisons; rainfall uses all complete dates.'
    elif name == 'PF-L_large_error_dates_mae':
        for r in records:
            annotation = r['variable'] == 'rainfall' and r['group'] == 'baseline_failure'
            if r['scope'] != 'pooled' or (r['shown_in_PF-L'].lower() != 'true' and not annotation):
                continue
            title, unit = VARIABLES[r['variable']]
            group = 'all complete dates' if r['group'] == 'all_complete' else 'training-derived reference-error dates'
            if annotation:
                group = 'rainfall annotation only | ' + group
            rows.append(row(group, title + ' MAE', unit, r['n'], r['mae_W1'], r['mae_persistence'], r['mae_climatology']))
        note = 'Bar groups and the separately labeled rainfall annotation are summarized. The control is the average of the two reference forecasts; its results remain in the source table.'
    elif name == 'PF-M_large_error_dates_differences':
        points = X['case3']['part1_A_q90']
        for variable, stations in points.items():
            title, unit = VARIABLES[variable]
            for station, groups in stations.items():
                data = groups['baseline_failure']
                if not data['n']:
                    continue
                rows.append(row(station + ' | training-derived reference-error dates', title + ' MAE', unit, data['n'],
                                *[data['point'][k]['mae'] for k in ('W1', 'persistence', 'climatology')]))
        note = 'These gaps are the model-minus-reference MAE differences plotted as points. Use the plotted 95% intervals when interpreting uncertainty; a gap alone is not a significance test.'
    elif name == 'PF-N_event_onsets':
        for r in records:
            for metric, count, label in (('hits', 'onsets', 'Onsets warned'), ('false_alarms', 'non_events', 'Non-event false alarms')):
                rows.append(row(f'{r["evidence"]} | {r["scope"]} | {PERIODS[r["evidence"]]}', label, 'count', r[count],
                                *[r[metric + '_' + k] for k in ('W1+X1@0.601', 'event_persistence', 'event_climatology')]))
        note = 'Onset-warning counts and non-event false-alarm counts have different denominators. More onset warnings and fewer false alarms describe different aspects of the warning decision.'
    elif name == 'PF-Q_persistence_worse_dates':
        for r in records:
            for variable in ('wind', 'mslp'):
                title, unit = VARIABLES[variable]
                rows.append(row(r['scope'] + ' | selected comparison dates', title + ' MAE', unit, r['qualifying'],
                                *[r[f'{variable}_mae_{k}_qualifying'] for k in ('W1', 'persistence', 'climatology')]))
        note = 'The comparison uses only dates selected by the recorded joint wind-and-pressure rule. Counts and shares in the first panel are selection frequencies, not accuracy scores.'
    elif name == 'F8_variants_and_inputs':
        b = X['B']['wind']['pooled']['point']
        for r in records:
            if r['variant'] == 'W1 (deployed)':
                rows.append(row(r['construction'] + ' | ' + PERIODS['B'], 'Wind speed MAE', 'm/s', b['W1']['n'],
                                r['wind_mae'], b['persistence']['mae'], b['climatology']['mae']))
        note = 'Gaps describe the deployed model dots and the two wind-MAE reference lines in the right panel. Other saved variants and the PR-AUC panel are contextual comparisons.'
    else:
        raise ValueError(f'Unclassified active figure: {name}')
    assert rows, name
    return {'figure': name, 'formula': MODEL + ' metric minus reference metric', 'note': note,
            'rounding': 'Scores and errors are displayed to six decimal places; counts are integers. Values are calculated before rounding from saved decimal exports. Exact rational gaps are included in the downloads.',
            'rows': rows, 'daily': daily, 'omitted_incomplete_cells': omissions}


def prepare(X, docs):
    destination = docs / 'data' / 'difference_gaps'
    destination.mkdir(parents=True, exist_ok=True)
    plots = [*sorted((docs / 'figures' / 'paper').glob('*.png')),
             *sorted((docs / 'figures').glob('*.png'))]
    catalog = {}
    for png in plots:
        source = png.with_suffix('.csv') if png.parent.name == 'paper' else docs / 'data' / (png.stem + '.csv')
        item = make(png.stem, source, X)
        if item is None:
            continue
        item['source_csv'] = source.relative_to(docs).as_posix()
        extra = {
            'PF-E_precision_recall_curves': [('w', 'website_cohort_results.json')],
            'PF-M_large_error_dates_differences': [('case3', 'panel_v3_results.json')],
            'F8_variants_and_inputs': [('b', 'benchmark_results.json')],
            'PF-C_event_metrics_overall': [('w', 'website_cohort_results.json'), ('b', 'benchmark_results.json')],
            'PF-D_event_metrics_by_station': [('w', 'website_cohort_results.json')],
        }
        item['source_records'] = ['runs/' + X['runs'][key].name + '/' + file for key, file in extra.get(png.stem, [])]
        catalog[png.stem] = item
        (destination / (png.stem + '.json')).write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding='utf-8')
        with (destination / (png.stem + '.csv')).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(item['rows'][0]))
            writer.writeheader()
            writer.writerows([*item['rows'], *item['daily']])
    (destination / 'index.json').write_text(json.dumps({'figures': list(catalog), 'formula': MODEL + ' minus reference'}, indent=2), encoding='utf-8')
    return catalog


def case_context(name, catalog):
    """Bind group-level explanations to the exact station window on a card."""
    if name not in catalog or name.split('_')[0] not in CASE_VARIABLES:
        return ''
    rows = catalog[name]['rows']
    contexts = list(dict.fromkeys(r['context'] for r in rows))
    counts = '; '.join(f'{r["context"].split(" | ")[0]}, {r["metric"]}: n = {r["n"]}' for r in rows)
    return ('The target dates for this individual card are ' + '; '.join(contexts) + '. '
            'Matching-record counts are ' + counts + '. '
            'The Difference Gap block records the three method values and signed margins for these exact dates, with daily calculations available for inspection.')


def html(name, catalog, esc):
    if name not in catalog:
        return ''
    item = catalog[name]

    def display(value, signed=False, unit=''):
        with localcontext() as ctx:
            ctx.prec = 60
            number = Decimal(value)
            if unit == 'count':
                return format(int(number), '+d' if signed else 'd')
            # Avoid signed zero suggesting a nonzero margin after rounding.
            rounded = number.quantize(Decimal('0.000001'))
            return format(rounded.copy_abs() if rounded == 0 else rounded, '+.6f' if signed else '.6f')

    def table(records):
        head = ['Context / target dates', 'Variable / metric', 'n', MODEL, 'Persistence', 'Climatology',
                'Δ vs Persistence', 'Δ vs Climatology', 'Unit']
        body = []
        for r in records:
            cells = [esc(r['context']), esc(r['metric']), str(r['n']), *[display(r[k], unit=r['unit']) for k in ('model', 'persistence', 'climatology')],
                     *[display(r[k], True, r['unit']) for k in ('gap_persistence', 'gap_climatology')], esc(r['unit'])]
            body.append('<tr>' + ''.join('<td>' + x + '</td>' for x in cells) + '</tr>')
        return '<div class="tw"><table><thead><tr>' + ''.join('<th>' + esc(x) + '</th>' for x in head) + '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div>'

    daily = '<details><summary>Daily absolute-error values and gaps</summary>' + table(item['daily']) + '</details>' if item['daily'] else ''
    omitted = ('<p class="small">Incomplete observation/forecast cells omitted from all three methods: ' + esc('; '.join(item['omitted_incomplete_cells'])) + '.</p>') if item['omitted_incomplete_cells'] else ''
    provenance = ' '.join(f'<a href="https://github.com/miaoxiizumi-gif/gale-cast-validations-result/blob/main/{esc(path)}">saved run JSON</a>' for path in item['source_records'])
    return (f'<div class="difference-gap" data-gap-figure="{esc(name)}"><h4>Difference Gap</h4>'
            f'<p><b>Δ = {esc(item["formula"])}.</b> For MAE and absolute error, negative means a smaller model error and positive means a larger model error. '
            'For precision, recall and F1, positive means a higher model score. For counts, read the named outcome: more onset warnings and fewer false alarms have different meanings. An exact zero means equal values; a displayed zero can also reflect rounding.</p>'
            + table(item['rows']) + f'<p class="small">{esc(item["note"])} {esc(item["rounding"])}</p>' + daily + omitted
            + f'<p class="small">Source: <a href="{esc(item["source_csv"])}">plotted data</a> {provenance}. Difference-gap downloads: '
            f'<a href="data/difference_gaps/{esc(name)}.csv">CSV</a> · <a href="data/difference_gaps/{esc(name)}.json">JSON</a>.</p></div>')
