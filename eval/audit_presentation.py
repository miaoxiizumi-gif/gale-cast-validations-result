"""Check rendered presentation language, downloads and figure metadata.

Read-only: does not change evidence, model artifacts or generated assets.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import csv
import json
from fractions import Fraction

import build_docs
import common as C
import terms
import site_policy


class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.links, self.ids = [], [], []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        self.skip += tag in ('script', 'style', 'code')
        attrs = dict(attrs)
        self.links.extend(attrs[k] for k in ('href', 'src') if k in attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])

    def handle_endtag(self, tag):
        self.skip -= tag in ('script', 'style', 'code')

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


class FigureCallouts(HTMLParser):
    """Inventory explanations inside each individual card, including station plots."""
    def __init__(self):
        super().__init__()
        self.cards, self.current = [], None
        self.field, self.paragraph = None, False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'figure':
            self.current = {'image': None, 'paper': [], 'plain': [], 'counts': {'paper': 0, 'plain': 0}}
        if self.current is None:
            return
        if tag == 'img':
            self.current['image'] = attrs.get('src')
        if tag == 'aside':
            classes = attrs.get('class', '').split()
            self.field = next((name for name in ('paper', 'plain') if name + '-explanation' in classes), None)
            if self.field:
                self.current['counts'][self.field] += 1
        if tag == 'p' and self.field:
            self.paragraph = True

    def handle_endtag(self, tag):
        if tag == 'p':
            if self.current is not None and self.field and self.paragraph:
                self.current[self.field].append('\n\n')
            self.paragraph = False
        if tag == 'aside':
            self.field = None
        if tag == 'figure':
            self.cards.append(self.current)
            self.current = None

    def handle_data(self, data):
        if self.current is not None and self.field and self.paragraph:
            self.current[self.field].append(data)


def check_explanations(paper, plain, source):
    for text in (paper, plain):
        assert text.strip(), f'{source}: empty explanation'
        assert terms.MODEL in text, f'{source}: full model name missing'
        check_text(text, source)


def check_gaps(docs, html, cards):
    """Independently check exact arithmetic and matching records, without writes."""
    folder = docs / 'data' / 'difference_gaps'
    names = json.loads((folder / 'index.json').read_text(encoding='utf-8'))['figures']
    assert len(names) == 23, names
    fragments = re.findall(r'<figure>(.*?)</figure>', html, re.S)
    count, checked = 0, 0
    for card, fragment in zip(cards, fragments):
        name = Path(card['image']).stem
        blocks = re.findall(r'class="difference-gap"', fragment)
        assert len(blocks) == int(name in names), name
        if blocks:
            assert re.search(r'<img\b[^>]*>(?:</a>)?<div class="difference-gap"', fragment), name
            count += 1
    assert count == 22, count
    for name in names:
        item = json.loads((folder / (name + '.json')).read_text(encoding='utf-8'))
        for r in [*item['rows'], *item['daily']]:
            for baseline in ('persistence', 'climatology'):
                expected = Fraction(r['model_fraction']) - Fraction(r[baseline + '_fraction'])
                assert expected == Fraction(r['gap_' + baseline + '_fraction']), (name, r)
                assert abs(expected - Fraction(r['gap_' + baseline])) < Fraction(1, 10**37), (name, r)
                checked += 1
            assert r['n'] > 0, (name, r)
        if name.split('_')[0] in ('PF-H', 'PF-I', 'PF-J', 'PF-K', 'PF-O', 'PF-P', 'PF-R'):
            with (docs / item['source_csv']).open(encoding='utf-8', newline='') as stream:
                source = list(csv.DictReader(stream))
            variables = {'Wind speed': 'wind', 'Mean sea level pressure': 'mslp', 'Relative humidity': 'humidity', 'Daily rainfall': 'rainfall'}
            for r in item['rows']:
                station = r['context'].split(' | ')[0]
                variable = next(v for title, v in variables.items() if r['metric'].startswith(title))
                columns = ['obs_' + variable, terms.MODEL + '_' + variable, 'pers_' + variable, 'clim_' + variable]
                valid = [s for s in source if s['station'] == station and all(s[k].lower() not in ('', 'nan', 'none') for k in columns)]
                assert len(valid) == r['n'], (name, r)
                for method, column in zip(('model', 'persistence', 'climatology'), columns[1:]):
                    expected = sum((abs(Fraction(s[column]) - Fraction(s[columns[0]])) for s in valid), Fraction()) / len(valid)
                    assert expected == Fraction(r[method + '_fraction']), (name, r, method)
    # Compare the displayed uncertainty-chart gaps with the original plot points.
    item = json.loads((folder / 'PF-M_large_error_dates_differences.json').read_text(encoding='utf-8'))
    with (docs / item['source_csv']).open(encoding='utf-8', newline='') as stream:
        points = list(csv.DictReader(stream))
    variables = {'Wind speed': 'wind', 'Mean sea level pressure': 'mslp', 'Relative humidity': 'humidity', 'Daily rainfall': 'rainfall'}
    for r in item['rows']:
        station = r['context'].split(' | ')[0]
        variable = next(v for title, v in variables.items() if r['metric'].startswith(title))
        for baseline in ('persistence', 'climatology'):
            point = next(p for p in points if p['scope'] == station and p['variable'] == variable and p['comparison'] == baseline)
            assert abs(Fraction(point['dmae']) - Fraction(r['gap_' + baseline + '_fraction'])) < Fraction(1, 10**12)
    print(f'PASS: {count} directly placed gap blocks, {len(names)} gap exports, {checked} signed arithmetic identities, matched-date case MAEs and plotted interval-chart points.')


JUDGMENT = re.compile(
    r'\b(?:worse|worst|underperform\w*|fails|failing|failure)\b|'
    r'less accurate than|no improvement over|largest error|'
    r'persistence (?:is|remains) (?:better|more accurate)|'
    r'references stay closer|still the closer forecast|'
    r'model[^.\n]{0,80}provides no', re.I)


def check_text(text, source):
    terms.check(text, str(source))
    match = JUDGMENT.search(text)
    assert not match, f'{source}: {match.group()}'


def main():
    docs = C.WORKSPACE / 'docs'
    page = Visible()
    page.feed((docs / 'index.html').read_text(encoding='utf-8'))
    check_text(' '.join(page.parts), 'index.html')
    assert len(page.ids) == len(set(page.ids)), 'Duplicate HTML IDs'
    missing = [url for url in page.links
               if not url.startswith(('http:', 'https:', '#', 'mailto:', 'data:'))
               and not (docs / url.split('#')[0]).exists()]
    assert not missing, missing
    assert all(url[1:] in page.ids for url in page.links if url.startswith('#')), 'Broken page anchor'
    html = (docs / 'index.html').read_text(encoding='utf-8')
    assert not re.search(r'<h[1-6][^>]*>\s*5\.2\b', html), 'Removed subsection restored'
    result_section = re.search(r'<section\b[^>]*id="results"[^>]*>(.*?)</section>', html, re.S)
    assert result_section, 'Benchmark results section missing'
    images = re.findall(r'<img\b[^>]*src="([^"]+)"', result_section[1])
    assert images == ['figures/paper/PF-G_observed_vs_predicted.png'], images
    assert result_section[1].count('<figure>') == 1, 'Extra figure card in Section 5'
    assert result_section[1].count('class="fignotes"') == 1, 'Extra figure notes in Section 5'
    callouts = FigureCallouts()
    callouts.feed(html)
    assert len(callouts.cards) == 26, len(callouts.cards)
    for card in callouts.cards:
        assert card['counts'] == {'paper': 1, 'plain': 1}, card
        check_explanations(''.join(card['paper']), ''.join(card['plain']), card['image'])
    check_gaps(docs, html, callouts.cards)
    guide = (docs / 'data' / 'documentation' / 'FIGURE_GUIDE.md').read_text(encoding='utf-8')
    for name in site_policy.REMOVED_FIGURES:
        assert not list((docs / 'figures').rglob(name + '.png')), name
        assert not list((docs / 'figures').rglob(name + '.svg')), name
        assert not re.search(r'^### ' + re.escape(name) + r'\b', guide, re.M), name
        assert not any(name + ext in html for ext in ('.png', '.svg')), name
    figures = list((docs / 'figures').rglob('*.svg'))
    for path in figures:
        svg = Visible()
        svg.feed(path.read_text(encoding='utf-8'))
        check_text(' '.join(svg.parts), path.name)
    # Check all metadata fields, including notes not expanded into a figure card.
    _, context = build_docs.placeholders()
    for name, note in context['NOTES'].items():
        for field, value in note.items():
            check_text(terms.text(value), f'{name}.{field}')
        if site_policy.published_figure(name):
            check_explanations(note['paper_explanation'], note['plain_explanation'], name)
    cases = list((docs / 'figures' / 'paper').glob('PF-[HIJKOPR]_*.png'))
    assert len(cases) == 14, len(cases)
    for png in cases:
        assert png.with_suffix('.svg').exists(), png
        assert png.with_suffix('.csv').exists(), png
    print(f'PASS: rendered HTML, {len(figures)} SVGs, all figure notes, '
          f'{len(cases)} case download sets, {len(page.links)} links and unique IDs; '
          f'both explanation callouts in all {len(callouts.cards)} figure cards.')


if __name__ == '__main__':
    main()
