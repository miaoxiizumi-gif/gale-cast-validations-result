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
from terms import MODEL, text as public_text


def attach(notes: dict, ctx: dict) -> None:
    """Attach two comprehensive explanation sections to each active record."""
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
    expand(notes, ctx)


def expand(notes: dict, ctx: dict) -> None:
    """Explain purpose, numerical evidence, reading, practical value and scope.

    Paragraphs have no sentence-count ceiling. Results are drawn from the saved
    runs, while chart-specific guidance explains what the evidence establishes.
    """
    guidance = {
        'PF-A_website_confusion_matrix': (
            'The matrix was constructed to make the alert decision auditable before interpreting any combined score. Its cells sum to the full case count, while true positives and false negatives sum to the observed event count. Precision evaluates the correspondence of issued warnings with events, and recall evaluates coverage of recorded events. Together these measures support the study objective of evaluating categorical reliability for localized hazard monitoring. The result applies to the historical scoring procedure and the pressure-fall events present in its recorded cases.',
            'Start by finding the box for a warning that matched an event and the box for a quiet forecast that matched a quiet day. The other two boxes show the two ways a warning decision can differ from the record: sounding an alert on a quiet day, or staying quiet when an event occurred. Add all four boxes to recover the total number of forecasts. High accuracy alone can be common when quiet days greatly outnumber hazard days, so also check how many of the actual events received warnings. This chart matters because an alert system needs both useful warnings and clear accounting of the decisions it makes.'),
        'PF-B_station_outcomes': (
            'The station separation was constructed to identify how the pooled confusion matrix is distributed geographically. The station matrices use the same warning threshold and historical procedure, so differences in counts can be read without introducing another decision rule. The warning score uses cross-station averaging, which links decisions issued on the same date; station rows therefore describe locations rather than independent replications. This provides station-resolved evidence for the study\'s localized warning objective while retaining the complete alert outcomes.',
            'Read one station table at a time before comparing locations. A correct warning means a recorded hazard day received an alert; a correct quiet decision means the station stayed quiet and no alert was issued. The event count at each location can differ, so use the number of events as context for the number caught. The shared scoring procedure helps readers compare locations fairly, but a shared warning day should not be counted as a separate storm at each station. The practical takeaway is where the recorded warning outcomes occurred within the monitoring network.'),
        'PF-C_event_metrics_overall': (
            'The graph was constructed to separate event-focused evaluation from the large number of non-event days. Precision, recall and F1-Score describe complementary aspects of categorical performance; the intervals describe uncertainty estimated from blocks of target dates. Evidence A uses the historical website procedure and Evidence B uses training-consistent inputs, with each reference evaluated on the corresponding cases. Signed Difference Gaps report the exact numerical comparison within each cohort on the 0-1 scale. This provides comparative retrospective evidence for hazard warning performance without treating the two input preparations as interchangeable experiments.',
            'Begin with the panel label to see which group of forecast days is being checked. Blue represents the deployed model, orange represents a forecast based on today\'s event status, and green represents the station\'s usual monthly event frequency. Precision asks how often an issued alert matched an event; recall asks how many recorded events were caught. F1 brings those two questions together in one score. The small lines on bars show the range of plausible scores from the uncertainty calculation. Use the table below the graph to read the numerical gaps, and compare panels only after noting that their input preparation and case counts differ.'),
        'PF-D_event_metrics_by_station': (
            'The graph was constructed to evaluate the event-focused metrics at the primary PAGASA stations rather than relying solely on a pooled score. Each station comparison retains the same historical case definition and warning procedure. Signed gaps and the plotted intervals distinguish the numerical comparison from its uncertainty; the limited number of events at a station affects interval width. The validation value is a location-specific record of precision, recall and F1-Score that supports interpretation of the system\'s localized alert behavior.',
            'Choose a station first, then compare bars for the same named score. Blue is the deployed model, orange is persistence, and green is climatology. A high recall bar means more actual events were warned about; a high precision bar means more issued warnings matched actual events. F1 summarizes both. Long uncertainty lines mean that the estimated score has a wider range, especially when only a few events were recorded. This chart matters because a useful combined result should also be understood at the individual stations where warnings are read.'),
        'PF-E_precision_recall_curves': (
            'The curves were constructed from saved scores to examine ranking across thresholds rather than only one binary decision. Recall is the horizontal coordinate and precision is the vertical coordinate; the raw station-score curve and cross-station-average curve show the documented scoring alternatives. The adopted operating point fixes the alert rule at 0.601, while event persistence is a single binary comparison point. The dashed prevalence line is an uninformative-ranking reference, not the station-month climatology forecast. The Difference Gap block gives same-cohort precision and recall at the recorded operating thresholds; a PR-AUC for the binary persistence point is not introduced. The graph therefore supports threshold-dependent interpretation of rare-event discrimination, with the historical nature of threshold adoption retained.',
            'The bottom axis asks what share of the recorded events was caught, and the side axis asks what share of the issued warnings matched events. Moving a warning cutoff changes both answers, so a score can trace a curve rather than produce just one dot. The two curves represent the raw station scores and the score averaged across stations; follow the legend to distinguish them. The marked operating point shows the adopted cutoff, and the persistence marker gives one fixed warning rule. The dashed horizontal line is the event frequency, not a monthly weather forecast. A curve near the top-right catches many events while keeping the warnings closely tied to events. This helps explain the trade-off involved in choosing a practical alert cutoff.'),
        'PF-G_observed_vs_predicted': (
            'The panels were constructed to inspect the distribution of regression outputs in physical units, complementing summary error metrics. The horizontal bins contain PAGASA observations and the vertical bins contain next-day model estimates; the color scale gives case counts on a logarithmic scale. Concentration near the one-to-one line indicates correspondence within the displayed bin resolution, while spread around it describes differences in level and range. Rainfall uses unequal bins and each variable has its own unit, so panels must be interpreted separately. These binned counts document forecast-observation correspondence; quantitative baseline comparisons remain in the numerical result tables.',
            'First choose a weather variable and read its units. Move across the bottom axis to find a recorded value, then move up the side axis to see the range of forecasts paired with it. Each colored box counts days with that combination, so the color describes how common the combination was, not how accurate it was by itself. The dashed line marks equal recorded and forecast values. Boxes near that line represent close matches; boxes farther away represent a greater difference at that scale. The color scale is compressed so both common and uncommon combinations can be seen, and rainfall uses wider boxes for larger amounts. This chart helps students see the shape of forecast behavior rather than relying only on one average score.'),
        'F1_partitions': (
            'The timeline was constructed to document the source and temporal allocation of records used in model development and retrospective evaluation. It distinguishes the primary-station chronological partitions from supplementary training data, including Port Area. The shaded evaluation interval allows overlap in calendar dates across sources to be read directly. This is methodological evidence about data provenance and temporal design; its validation role is to define the context in which the reported scores can be interpreted. It does not itself supply an accuracy metric.',
            'Read the dates from left to right. A bar tells you which years of records belonged to one data source or one stage of development. Training records were used to learn patterns, tuning records supported choices during development, and evaluation records were used to check saved forecasts. Port Area and the other extra stations are supplementary training sources. The shaded band makes it easier to notice which records share calendar dates with the evaluation period. This matters because understanding where the data came from helps readers interpret what an accuracy score can tell them.'),
        'F8_variants_and_inputs': (
            'The comparison was constructed to document existing model versions under the same evaluation cases and two input-scaling procedures. PR-AUC describes rare-event ranking in the left panel, while wind MAE describes the average numerical error in the right panel. The vertical reference lines belong to the wind comparison, and the Difference Gap block reports the deployed model\'s margins against both references for each preparation. Differences among saved versions are descriptive development evidence, rather than a new model-selection exercise. The result supports reproducible interpretation of preprocessing sensitivity while the deployed weights and thresholds remain fixed.',
            'Read each row as a saved model version. Blue circles and purple squares distinguish the two ways the inputs were prepared; the legend names them. In the left panel, a dot farther right has a higher score for ranking event days. In the right panel, a dot farther left has a smaller average wind error. The orange and green vertical lines are the two simple wind-reference forecasts. The gap table compares only the deployed model with those lines, separately for each input preparation. The main lesson is that the way inputs are prepared belongs in the explanation of a result, even when the model file itself has not changed.'),
        'PF-H': (
            'The window was constructed to connect a correctly detected historical pressure-fall event with the surrounding meteorological outputs. Wind and pressure trajectories are compared against both reference forecasts, while the pressure-change panel links the episode to the study-label trigger and the score panel records the warning decision. The Difference Gap block reports wind and pressure MAE over matching complete dates, followed by daily absolute-error differences. Each target date is forecast from its own preceding 32-day input sequence. This constitutes traceable case evidence for the relationship between weather estimates and alert behavior on the selected dates; complete-period accuracy is assessed separately.',
            'Read the dates across all panels together. Black diamonds are recorded values, the blue forecast belongs to the deployed model, and orange and green are the two reference forecasts. In the pressure-change panel, a downward change indicates falling pressure, and the dashed weather threshold helps connect that change with the event label. In the score panel, a bar crossing the warning cutoff means an alert was issued. A close weather estimate and a correct warning answer different questions, so inspect both panels. The gap block averages the errors over matching days, and its daily table lets you check each date. These are three separate forecasts for tomorrow, not a three-day forecast issued all at once.'),
        'PF-I': (
            'The common window was constructed to examine a shared pressure-fall episode across the three primary stations using synchronized target dates. Wind trajectories, pressure changes and the averaged warning score permit joint inspection of meteorological context and classification decisions. The wind Difference Gaps are computed separately by station using the same complete dates for all three forecasts. The shared cross-station score links decisions on a date, so the rows document geographic behavior rather than independent storm episodes. The selected window supports an auditable network-level illustration, while broader performance claims use the full evaluation cohorts.',
            'Move across a row to follow one station, then move down a column to compare the same date at all stations. The wind lines compare the recorded weather with the deployed model and both simple reference forecasts. The pressure-change panels show whether pressure was rising or falling. The warning bars show whether the shared score crossed the alert cutoff. Wind estimates close to the observation markers indicate close numerical matches, while the event labels show whether each alert matched the recorded pressure-fall event. The gap table keeps station results separate and lists the dates used. This view helps explain how one weather episode can be examined consistently across a station network.'),
        'PF-J': (
            'The window was constructed in response to the request for numerical examples during relatively higher observed wind. The documented selection rule uses complete records, a training-period wind threshold and the number of dates with lower model wind error than both references. Wind and pressure error bars, the closest-forecast grid, pressure change and warning outcome provide complementary views of the same selected dates. The Difference Gap block gives matched-record MAE and daily absolute-error differences for the four variables represented in the panels and grid. This is evidence about the selected episode and the transparency of its selection, with complete-period results providing the broader validation context.',
            'Start with the wind plot to see what happened on the selected dates. Then use the error bars: a shorter bar means that forecast was closer to the recorded value. The grid identifies the closest forecast for each variable and day, so it gives a quick way to compare the same weather record across methods. The pressure-change and warning panels add context about the event label and alert decision. The gap table summarizes all four variables shown by the graph and grid, and the daily section shows the individual differences. These dates were chosen using the wind comparison rule, so use them to understand this example rather than to describe every day in the full record.'),
        'PF-K': (
            'The shared window was constructed to extend the selected wind-regression illustration across all primary stations on common dates. The observed and forecast wind series are paired with absolute error and classification outcome, allowing the numerical and warning tasks to be interpreted together. The signed MAE gaps preserve station identity and use common complete records for both reference comparisons. Because the window was selected retrospectively using wind-error conditions, its validation contribution is a documented multi-station example under those stated conditions.',
            'Read one station row from left to right. The wind lines show forecasts beside recorded values, the error bars show how far each forecast was from the record, and the last panel shows the warning outcome. Shorter error bars mean closer wind estimates. The rows use the same dates, which makes a location-by-location comparison easier to follow. Check the gap table for the station, dates and number of complete records before comparing the numerical margins. The main takeaway is how the forecast values and warning decisions fit together during this selected shared window.'),
        'PF-L_large_error_dates_mae': (
            'The figure was constructed to evaluate all four supported regression variables under a reproducible reference-error condition, alongside the complete-date comparison. The condition is based on training-period 90th-percentile reference errors and does not use model outputs to choose dates. The control forecast averages persistence and climatology and provides context for interpreting a simple reference combination. The Difference Gaps reproduce the plotted MAE comparisons and retain each group\'s case count; rainfall follows the recorded all-complete-date presentation rule. The evidence therefore evaluates the specified conditions explicitly, with interpretation confined to each variable, unit and date group.',
            'First read the panel heading to identify the weather variable and unit. Inside each date group, the colored bars represent the deployed model, the two reference forecasts and their simple average control. A shorter bar means a smaller average difference from recorded weather. Some groups use every complete day, while another group uses days that met a rule for large reference errors. That rule was set from the earlier training records. The rainfall bars use all complete days, and the small annotation gives a separate result for reference-error dates. Keep those two date groups separate. Read the gap table within a group to see the numerical margin in the correct unit.'),
        'PF-M_large_error_dates_differences': (
            'The plot was constructed to express each conditional MAE comparison as a paired difference and an uncertainty interval. The point estimate is model MAE minus reference MAE on the same station-dates, and the line is a 95% interval from the saved circular block-bootstrap calculation. A third comparison uses the control, which is the average of persistence and climatology. The common zero line distinguishes equal error from differences in either direction; interval position and width describe how precisely the difference is estimated. The Difference Gap table reports the underlying three-method MAE values and the corresponding signed margins. Its validation role is to connect numerical comparison with sampling uncertainty under the recorded date-selection rule, rather than treating a point estimate alone as conclusive proof.',
            'Choose a weather panel, then read the station labels. Each point compares the deployed model with one reference forecast on the same days. The middle zero line means equal average errors. A point to the left means the model error is smaller, and one to the right means it is larger. The line around the point shows the uncertainty range calculated from groups of neighboring dates. If that line crosses zero, the calculation includes both directions of the comparison. Use the gap table for the exact values and the graph for the uncertainty, because the size of a difference and how clearly it is estimated are different questions.'),
        'PF-N_event_onsets': (
            'The comparison was constructed to examine the transition from a non-event issue day to an event target day, which directly addresses onset warning capability. Each cohort includes every qualifying onset, with no event-date search based on model success. The total-onset marker provides the denominator for the detected-onset bars, while accompanying false-alarm counts describe warning behavior on non-event cases. Difference Gaps report both types of count against both references using their respective denominators. The result is direct retrospective evidence for pressure-fall onset detection and the associated alert burden, with event type and cohort preparation stated explicitly.',
            'An onset means the previous day was not labeled as a hazard, but the target day was. The colored bars count how many of these new events each method warned about, and the black marker shows the total available to catch. A bar reaching that marker would mean every recorded onset in that group was warned about. The false-alarm numbers answer a different question: how often an alert appeared when no event was recorded. More onset warnings and fewer false alarms are both useful, but they should not be added into one count. The gap table keeps those outcomes and their totals separate. This matters for practical forecasting because a warning is especially useful when it appears before a new hazardous change.'),
        'PF-O': (
            'The selected window was constructed to inspect the meteorological outputs and warning decisions on dates satisfying the recorded reference-error condition. The four weather panels, closest-forecast grid and score panel connect numerical estimates with classification outcomes. Shading records the selection condition and stars identify model comparison wins, while all displayed dates and variables remain part of the illustration. The Difference Gap block supplies the exact target dates, matched-record counts, window MAE and daily differences for each plotted variable. This validates the traceability of the selected example and its computed comparisons; the selection rule defines the scope of the inference.',
            'Read the dates across the weather panels, grid and score panel together. Black markers are recorded weather; blue is the deployed model, orange is persistence and green is climatology. A forecast line near the black markers is a close estimate for that variable. Shading means the date met the reference-error rule, and a star identifies a model comparison win under that condition. The grid names the closest forecast for each variable and date, while the score panel shows whether a warning was issued and how it matched the event label. The gap block averages only days with all three forecasts and an observation available, and its daily section shows the individual comparisons. This makes it possible to check the selected example step by step rather than judging it only by the stars.'),
        'PF-P': (
            'The synchronized panels were constructed to examine a common weather episode across the three stations and four regression variables. Each row identifies a station and each column a variable, preserving temporal alignment across the network. Shading and stars carry the same recorded comparison conditions as the station windows. The Difference Gap block computes station-specific MAE over common complete records and provides daily absolute-error margins, with missing cells listed explicitly. This provides a reproducible multi-station case illustration and supports interpretation of spatial variation within the selected episode, with general accuracy evaluated on the full cohorts.',
            'Choose a column to follow one type of weather across all stations, or choose a row to follow several weather measurements at one station. The black markers are observations, the blue line is the deployed model and the other two lines are reference forecasts. Lines close to the observations indicate close numerical estimates in that panel\'s unit. Shading marks the reference-error condition and stars identify the selected model comparison wins. A gap in a plotted line means a value is missing; the gap calculation uses only dates complete for all compared methods. The table keeps station results separate and lists every excluded incomplete cell. The practical takeaway is how the same episode appears at several locations without mixing their units or treating one selected episode as a complete performance estimate.'),
        'PF-Q_persistence_worse_dates': (
            'The figure was constructed to quantify the frequency of the recorded joint wind-and-pressure comparison condition before examining the associated errors. Qualification requires smaller model absolute error than persistence for both variables on the same complete station-date. The first panel counts and describes those dates, while the remaining panels report the three forecasts\' wind and pressure MAE conditional on that selection. The Difference Gap block makes these conditional comparisons numerically explicit by station and pooled. The evidence establishes how often the rule was met and how the methods compare on those dates; it does not replace the all-date comparison.',
            'The first panel counts days that met the rule for both wind and pressure at the same station. Its percentages describe how often that condition occurred, not the percentage of all forecasts that were correct. The next panels compare average wind and pressure errors on those chosen days. Blue is the deployed model, orange is persistence and green is climatology. Shorter error bars mean closer estimates, and the gap table gives their numerical differences. Because the dates were chosen using the wind-and-pressure comparison itself, the takeaway is the frequency and behavior of these particular cases. Use the all-date result table for the broader picture.'),
        'PF-L_composite_validation': (
            'The composite was constructed to present four recorded comparisons in a common visual layout while preserving the distinct date definitions. Wind and pressure use the joint comparison condition, humidity uses the training-derived reference-error condition, and rainfall includes all complete records. Each panel reports its own sample size and physical unit, and the Difference Gap block reproduces those MAE values and their signed margins. This provides transparent evidence about the specified evaluation groups and facilitates variable-by-variable interpretation. The selection definitions remain essential to the validation claim, with Table PE-2 retaining the complete-period comparison.',
            'Read one panel at a time instead of comparing bar heights across different weather variables. Blue is the deployed model, orange is persistence and green is climatology. A shorter bar means a smaller average error in the unit printed on that panel. The heading tells you which days were chosen and how many records were used. Wind and pressure share one comparison rule, humidity uses another rule, and rainfall uses all complete days. The Difference Gap table states the signed margin against each reference, so the exact numerical comparison is visible as well as the bars. The main takeaway is what happened in each stated group of dates, while the all-date table supplies the overall context.'),
        'PF-R': (
            'The window was constructed to provide consecutive-date examples satisfying the recorded joint wind-and-pressure comparison rule. Wind and pressure forecasts and absolute errors are shown alongside humidity, rainfall and the hazard score, so the selection variables can be interpreted with additional atmospheric context. The Difference Gap block reports the dates and matched-record MAE for all four plotted weather variables and makes daily comparisons available for inspection. Each date retains its separate next-day forecast origin. The resulting evidence is a reproducible selected case study under the stated rule, with selection frequency and complete-period comparisons reported separately.',
            'Begin with the wind and pressure panels because those variables were used to choose the dates. Compare the black observation markers with the blue model line and the orange and green reference lines. A close line or a short error bar means a close estimate for that day. Humidity and rainfall add weather context even though they were not used to choose this window. Shading and stars identify the recorded comparison conditions, and the score panel shows whether a warning was issued. The gap table lists all four weather variables, their dates and the number of complete records used. These are separate forecasts for the next day, so read the window as a sequence of decisions rather than one forecast extending several days ahead.'),
    }
    assert guidance.keys() == {k for k in notes if site_policy.published_figure(k)}
    for name, (formal, plain) in guidance.items():
        result = notes[name]['finding']
        if name == 'PF-G_observed_vs_predicted':
            totals = ctx['A']['obs_vs_W1_binned_total']
            result = 'The exported panel totals are ' + ', '.join(f'{v}: {n:,} cases' for v, n in totals.items()) + '.'
        elif name == 'PF-L_large_error_dates_mae':
            summaries = []
            for variable, stations in ctx['case3']['part1_A_q90'].items():
                for group in ('all_complete', 'baseline_failure'):
                    r = stations['pooled'][group]
                    label = 'all complete dates' if group == 'all_complete' else 'training-derived reference-error dates'
                    if variable == 'rainfall' and group == 'baseline_failure':
                        label = 'rainfall annotation only, ' + label
                    summaries.append(f'{variable}, {label}, n = {r["n"]}: MAE ' + ', '.join(f'{k} {r["point"][k]["mae"]:.6f}' for k in ('W1', 'persistence', 'climatology', 'control')))
            result = '; '.join(summaries) + '. Units follow the corresponding panel.'
        elif name == 'PF-M_large_error_dates_differences':
            result = 'The plotted points report paired MAE differences by variable and station, including a pooled estimate. The numerical differences and all three method values are reproduced in the Difference Gap table; the saved 95% intervals remain on the graph.'
        notes[name]['paper_explanation'] += '\n\nRecorded result summary: ' + result + '\n\n' + formal
        notes[name]['plain_explanation'] += '\n\n' + plain + '\n\nTo check the result yourself, use the plotted-data download and read the case dates and counts before interpreting a score. Numerical forecast accuracy and correct hazard warnings describe complementary parts of the forecasting task.'
        for field in ('paper_explanation', 'plain_explanation'):
            notes[name][field] = site_policy.current_references(public_text(notes[name][field]))
