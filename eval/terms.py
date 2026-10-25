"""Public naming and wording rules (panel directive, 2026-10-25), applied to every public text and figure at build/save time.

- The deployed model is called "GALE-CAST Model-W1" in displayed text (not inside code, URLs or file names).
- "baseline-failure" is shown as "large-baseline-error" (the term refers to the reference forecasts, not to the model).
- The words "favourable", "favorable" and "subset" must not appear in public text or figures; sources are written without them and
  `check()` fails the build if one slips through. Selection rules are still stated in plain words wherever dates were selected.
"""
from __future__ import annotations

import re

MODEL = "GALE-CAST Model-W1"
_W1 = re.compile(r"(?<!Model-)(?<![\w/.-])W1(?!\w)(?!\.\w)")
_SWAPS = [(re.compile(r"[Bb]aseline-failure"), lambda m: ("L" if m.group(0)[0] == "B" else "l") + "arge-baseline-error")]
BANNED = re.compile(r"favourabl|favorabl|subset", re.I)


def text(s: str) -> str:
    """Displayed prose or a figure label."""
    s = re.sub(r"GALE-CAST(?: model)? W1(?![\w.])", MODEL, s)
    s = re.sub(r"(?<![\w/.-])W1 [Mm]odel\b", MODEL, s)
    s = re.sub(r"(?<![\w/.-])W1_raw\b", MODEL + " raw", s)  # classifier label W1_raw@0.64 in figures and tables
    s = re.sub(r"\bpre-W1\b", "pre-" + MODEL, s)
    s = _W1.sub(MODEL, s)
    for rx, rep in _SWAPS:
        s = rx.sub(rep, s)
    return s


def html(page: str) -> str:
    """Apply text() to HTML text nodes only, leaving tags, attributes and <code> contents unchanged."""
    out, in_code = [], 0
    for part in re.split(r"(<[^>]+>)", page):
        if part.startswith("<"):
            tag = part[1:].split()[0].rstrip(">").lower() if len(part) > 2 else ""
            in_code += 1 if tag in ("code", "style", "script") else -1 if tag in ("/code", "/style", "/script") else 0
            out.append(part)
        else:
            out.append(part if in_code else text(part))
    return "".join(out)


def markdown(doc: str) -> str:
    """Apply text() to Markdown outside `code` spans and link targets."""
    parts = re.split(r"(`[^`]*`|\]\([^)]*\))", doc)
    return "".join(p if p.startswith("`") or p.startswith("](") else text(p) for p in parts)


def bake(fig) -> None:
    """Rename the model in every text element of a matplotlib figure and refuse banned words."""
    from matplotlib.text import Text
    fig.canvas.draw()  # tick labels of categorical axes exist only after a draw
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            labels = [t.get_text() for t in axis.get_ticklabels()]
            if any(text(s) != s for s in labels):
                axis.set_ticks(axis.get_majorticklocs())
                axis.set_ticklabels([text(s).replace(MODEL, "GALE-CAST\nModel-W1") for s in labels])  # two lines: fits beside neighbours
    for t in fig.findobj(Text):
        s = t.get_text()
        if s:
            new = text(s)
            if new != s and "\n" in s and t.axes is not None:  # small multi-line labels inside a panel: name on two lines
                new = new.replace(MODEL, "GALE-CAST\nModel-W1")
            t.set_text(new)
            check(t.get_text(), "figure text")
    _fit_titles(fig)


def _fit_titles(fig) -> None:
    """Wrap panel titles that became wider than their panel after the rename."""
    import textwrap
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    for ax in fig.axes:
        width = ax.get_window_extent(r).width
        for t in (ax.title, ax._left_title, ax._right_title):
            s = t.get_text()
            w = t.get_window_extent(r).width
            if s and "\n" not in s and w > width * 1.02:
                t.set_text(textwrap.fill(s, max(20, int(len(s) * width / w))))


def check(s: str, where: str) -> None:
    m = BANNED.search(s)
    if m:
        raise ValueError(f"banned public term {m.group(0)!r} in {where}: …{s[max(0, m.start() - 60):m.end() + 60]}…")
