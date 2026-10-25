"""Formal and accessible explanations for the active figure families.

Draft terminology reviewed directly from Chapter-1.pdf through Chapter-5.pdf in
GALE-CAST_PAPERS_CHAPTERS. Principal anchors (PDF page numbers): Chapter 1,
11 and 13-14 (objectives); Chapter 2, 22 (synthesis); Chapter 3, 19-24 and
31-39 (architecture and verification); Chapter 4, 14-18 (results); Chapter 5,
1, 3 and 7-8 (summary and conclusions). Local extraction and source hashes are
kept in _private/chapter_caption_review/; no chapter text is published.

The drafts supply terminology, not replacement results. Explanations describe
the saved evaluation cohorts, units and selection rules. They do not attribute
gale-force observations or independent testing to the pressure-fall scorecard.
"""
from __future__ import annotations

import site_policy
from terms import MODEL


def attach(notes: dict, ctx: dict) -> None:
    """Attach two curated paragraphs to every active metadata record."""
    m = MODEL
    event = ctx['A']['events']['pooled']['classifiers']['W1+X1@0.601']
    onsets = ctx['case3']['onsets']['A']['pooled']
    paragraphs = {
        'PF-A_website_confusion_matrix': (
            f'The confusion matrix evaluates the categorical performance of {m} by comparing next-day hazard warnings with PAGASA-derived study labels across 3,423 historical forecast windows. '
            'The true-positive, true-negative, false-positive and false-negative counts provide the basis for accuracy, precision, recall and F1-Score; the recorded events in this cohort are pressure falls.',
            'The four boxes count correct warnings, correct quiet days, false alarms and missed events. '
            'More correct decisions and fewer false alarms or misses mean more accurate warning decisions. '
            f'Here, {m} correctly warned of {int(event["tp"])} of the {int(event["tp"] + event["fn"])} recorded pressure-fall events.'),
        'PF-B_station_outcomes': (
            f'The station-level confusion matrices describe the categorical performance of {m} at NAIA, Sangley Point and Science Garden. '
            'Disaggregating the same historical scorecard by station supports localized assessment of hazard detection and alert outcomes.',
            'Each small table shows the warning results for one weather station. '
            'Correct warnings and correct quiet days are matches with the recorded weather, while the other boxes count false alarms and misses. '
            f'Read all three tables to see how {m} warning outcomes are distributed across the stations.'),
        'PF-C_event_metrics_overall': (
            f'Precision, recall and F1-Score summarize the hazard-warning performance of {m} and the reference forecasts on the historical website cohort and the training-consistent benchmark. '
            'The separate cohort panels and uncertainty intervals support a transparent assessment of rare-event detection under the two documented input preparations.',
            f'The bars show warning scores for {m}, persistence and climatology. '
            'Taller bars mean better scores: precision describes how often a warning matches an event, recall describes how many events are caught, and F1 combines the two. '
            'Compare methods inside the same panel because the two panels use different groups of forecast cases.'),
        'PF-D_event_metrics_by_station': (
            f'The station-level precision, recall and F1-Score comparisons evaluate the localized hazard-warning performance of {m} against the reference forecasts. '
            'Reporting each primary station separately, with uncertainty intervals, connects the categorical evaluation to the study objective of localized hazard monitoring.',
            'Each station has its own warning-score comparison. '
            'Taller bars mean better scores, and the thin lines show how much the estimated scores may vary. '
            f'This helps readers examine {m} warning performance at each location rather than relying only on a combined score.'),
        'PF-E_precision_recall_curves': (
            f'The precision-recall curves evaluate how {m} distinguishes pressure-fall events from non-events as the warning threshold changes. '
            'The marked operating point and reference procedures place the historical PR-AUC result in the context of rare-event warning sensitivity and precision.',
            'Each curve shows the balance between catching recorded events and issuing warnings that match those events. '
            'A curve closer to the upper-right corner combines high recall with high precision. '
            f'The marked point shows the warning cutoff used for {m} in this historical scorecard.'),
        'PF-G_observed_vs_predicted': (
            f'The binned observed-versus-predicted panels support regression-based forecasting validation of {m} for wind speed, mean sea level pressure, relative humidity and daily rainfall. '
            'Case concentrations relative to the one-to-one line describe correspondence between the next-day regression outputs and PAGASA observations in each variable\'s physical units.',
            f'Each panel compares what {m} predicted with what PAGASA recorded for one weather variable. '
            'Darker boxes contain more days, and boxes near the dashed diagonal indicate predictions close to the recorded values. '
            'This makes it easier to see where forecasts and observations line up for each type of weather measurement.'),
        'F1_partitions': (
            f'The data-allocation timeline documents the temporal context of {m} by displaying the training, tuning and evaluation periods for the primary stations and supplementary training sources. '
            'It supports interpretation of the validation design by making the dates associated with each data source explicit.',
            f'Each horizontal bar shows when a group of weather records was used for {m}. '
            'The shaded area marks the dates later used for evaluation. '
            'Use this chart to understand the data timeline before interpreting the accuracy results.'),
        'F8_variants_and_inputs': (
            f'The saved-variant comparison places {m} within the documented model-development record using PR-AUC and next-day wind-speed MAE under two input preparations. '
            'Evaluating the existing versions on identical cases describes the relationship between input preparation, rare-event ranking and numerical forecast accuracy without additional training.',
            'Each dot represents an already trained model version using one way of preparing its inputs. '
            'Farther right is better for PR-AUC in the left panel, while farther left means a smaller average wind error in the right panel. '
            f'The chart places {m} alongside the other saved versions using the same forecast cases.'),
        'PF-H': (
            f'The selected station window relates the next-day wind, mean sea level pressure, pressure change and hazard-warning score of {m} to the corresponding PAGASA records. '
            'The three dates are separate next-day forecasts selected retrospectively to illustrate classification behavior around a detected pressure-fall event.',
            f'The black markers show recorded weather, and the blue line shows {m} forecasts beside the reference lines. '
            'Forecast lines close to the recorded values indicate close weather estimates, and a score above the dashed cutoff produces a warning. '
            'Read the weather panels and warning panel together to follow this selected pressure-fall episode.'),
        'PF-I': (
            f'The common-window panels describe the wind forecasts, pressure changes and hazard-warning decisions of {m} across the three primary stations on the same target dates. '
            'This retrospectively selected example connects the station-level outputs to a shared pressure-fall episode while preserving the next-day forecast interpretation.',
            'Each row represents one station on the same three dates. '
            f'Compare the {m} forecast lines with the recorded-weather markers; closer lines indicate closer estimates, while the score panel shows whether a warning was issued. '
            'The shared dates help show how the weather and warning decisions relate across the station network.'),
        'PF-J': (
            f'The selected higher-wind station window examines the wind and pressure errors, additional regression outputs and hazard-warning decisions of {m} alongside PAGASA observations. '
            'The dates were chosen using the recorded wind-error selection rule, so the panels provide a retrospective case illustration rather than an estimate for all historical dates.',
            f'The lines compare recorded weather with {m} and the two reference forecasts. '
            'Shorter error bars mean closer estimates, and the grid names the forecast closest to the recorded value on each date. '
            'Use the weather and warning panels together to understand this selected example.'),
        'PF-K': (
            f'The common regression window compares observed wind, forecast wind, absolute wind error and the hazard-warning outcomes of {m} at all three stations. '
            'The shared dates were selected using the documented wind-error rule and support a coordinated station-level interpretation of the retrospective example.',
            'Each row shows one station over the same three dates. '
            f'Lines close to the recorded weather and shorter error bars indicate closer wind estimates from {m} or a reference forecast. '
            'The final panel adds the warning outcome so readers can compare numerical estimates with hazard decisions.'),
        'PF-L_large_error_dates_mae': (
            f'Mean Absolute Error compares the next-day wind speed, mean sea level pressure, relative humidity and rainfall outputs of {m} with persistence, climatology and the reference-average control. '
            'The labeled date groups distinguish complete records from dates meeting the training-derived reference-error rule, with the rainfall panel reporting all complete dates.',
            'Each colored bar gives the average size of the forecast error for one method. '
            'Shorter bars mean estimates closer to the recorded weather, but compare bars only within the same variable and date group. '
            f'The panel headings show which dates were used to assess {m}, including all complete dates for rainfall.'),
        'PF-M_large_error_dates_differences': (
            f'The paired MAE differences quantify the next-day regression comparison between {m} and each reference method on dates meeting the recorded reference-error rule. '
            'The station-level and pooled 95% block-bootstrap intervals describe uncertainty in these conditional numerical comparisons.',
            f'Each dot is the average error of {m} minus the average error of one reference forecast on the same days. '
            'Zero means equal average error; a dot to the left means a smaller model error, and a dot to the right means a larger model error. '
            'The line around each dot shows the uncertainty range, helping readers judge how clearly the two methods differ.'),
        'PF-N_event_onsets': (
            f'The onset comparison evaluates the capacity of {m} to issue warnings when a study-label hazard appears after a non-event day, using both documented evaluation cohorts. '
            'Detected onsets and the accompanying non-event false-alarm counts directly describe pressure-fall onset detection and alert behavior.',
            'Each bar counts how many new pressure-fall events a method warned about. '
            'A taller bar closer to the black total marker means more of those new events were detected. '
            f'On the historical website cases, {m} warned of {onsets["onset_hits"]["W1+X1@0.601"]} of {onsets["onsets"]} onsets.'),
        'PF-O': (
            f'The selected station window compares the wind, mean sea level pressure, relative humidity, rainfall and hazard-warning outputs of {m} with PAGASA observations and the reference forecasts. '
            'Shading identifies the recorded reference-error conditions, and stars identify model comparison wins within these retrospectively selected next-day cases.',
            f'The black markers show recorded weather, and the blue line shows {m} forecasts. '
            'Lines near the recorded values indicate close estimates, while a score above the dashed cutoff means a warning was issued. '
            'Shading marks the selected reference-error conditions, and stars point out the model comparison wins on those dates.'),
        'PF-P': (
            f'The aligned common-window panels examine the next-day wind speed, mean sea level pressure, relative humidity and rainfall outputs of {m} at NAIA, Sangley Point and Science Garden. '
            'Using the same three retrospectively selected dates supports a coordinated view of the regression forecasts during a shared weather episode.',
            'Each row is a station, and each column is a weather variable. '
            f'Black markers show recorded values, the blue line shows {m}, and the other lines show the reference forecasts. '
            'Lines closer to the recorded values mean closer estimates; follow the shared dates to see how the weather changes across stations.'),
        'PF-Q_persistence_worse_dates': (
            f'The station counts and MAE panels describe dates on which the absolute wind and pressure errors of {m} were both below persistence errors under the recorded selection rule. '
            'The counts establish the frequency of these conditional cases, while the error panels compare all three forecasts on the selected dates.',
            'The first panel counts station-days that met the wind-and-pressure comparison rule. '
            'The next two panels show average forecast errors, where shorter bars mean closer estimates. '
            f'These chosen dates illustrate particular {m} results; the counts describe how often the rule was met, rather than an accuracy percentage.'),
        'PF-L_composite_validation': (
            f'The composite summarizes the MAE of {m}, persistence and climatology for wind speed, mean sea level pressure, relative humidity and daily rainfall using the date definition shown in each panel. '
            'Wind and pressure use the recorded model-persistence comparison rule, humidity uses the training-derived reference-error rule, and rainfall uses all complete dates, making this a descriptive comparison of distinct evaluation groups.',
            f'The blue bars show {m} average errors, and the orange and green bars show the two reference forecasts. '
            'Shorter bars mean estimates closer to the recorded weather, so compare bars within one panel at a time. '
            'Each heading gives the dates used and their count, because the four panels do not all use the same days.'),
        'PF-R': (
            f'The selected station window examines the wind and pressure forecasts of {m} on consecutive dates meeting the recorded joint error-comparison rule, with humidity, rainfall and hazard-warning outcomes provided as context. '
            'Each date is a separate next-day forecast, and the selected window illustrates the specified comparison conditions rather than performance over the complete period.',
            f'The lines compare {m} and the reference forecasts with the recorded weather on each selected day. '
            'Lines near the observations and shorter error bars mean closer estimates, while stars mark the selected model comparison wins. '
            'The score panel shows whether a warning was issued for each separate next-day forecast.'),
    }
    active = {name for name in notes if site_policy.published_figure(name)}
    assert active == paragraphs.keys(), f'Explanation coverage mismatch: {active ^ paragraphs.keys()}'
    for name, (paper, plain) in paragraphs.items():
        notes[name].update(paper_explanation=paper, plain_explanation=plain)
