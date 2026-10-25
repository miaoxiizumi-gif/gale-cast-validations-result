"""Permanent presentation exclusions for the panel-review site.

These figures remain in historical run records. The website keeps its numerical
results and provenance, but no longer publishes these image assets or cards.
"""

REMOVED_FIGURES = frozenset({
    'PF-F_wind_mae_rmse',
    'PF-F2_website_regression_provenance',
    'PF-F3_regression_variables_mae',
    'F2_wind_mae_by_station',
    'F3_wind_monthly_means',
    'F4_wind_obs_vs_pred_counts',
    'F5_event_timeline_monthly',
    'F6_confusion_matrices',
    'F7_event_benchmarks',
})


def published_figure(name: str) -> bool:
    return name not in REMOVED_FIGURES


def current_references(text: str) -> str:
    """Point prose to the existing full-result table instead of retired cards.

    Artifact filenames and source paths remain unchanged for provenance.
    """
    import re
    text = re.sub(r'\bPF-F(?:2|3)?\b(?![\w.-])', 'Table PE-2', text)
    text = text.replace('Table PE-2 and Table PE-2 report', 'Table PE-2 reports')
    return re.sub(r'Table PE-2(?: and |, )Table PE-2', 'Table PE-2', text)
