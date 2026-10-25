"""Check rendered presentation language, downloads and figure metadata.

Read-only: does not change evidence, model artifacts or generated assets.
"""
from html.parser import HTMLParser
from pathlib import Path
import re

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
    cases = list((docs / 'figures' / 'paper').glob('PF-[HIJKOPR]_*.png'))
    assert len(cases) == 14, len(cases)
    for png in cases:
        assert png.with_suffix('.svg').exists(), png
        assert png.with_suffix('.csv').exists(), png
    print(f'PASS: rendered HTML, {len(figures)} SVGs, all figure notes, '
          f'{len(cases)} case download sets, {len(page.links)} links and unique IDs.')


if __name__ == '__main__':
    main()
