"""Redraw assets/writing.svg from the five newest essays on the blog index.
Text is drawn as outlines so the card keeps its fonts when GitHub shows it as an image."""
import html
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

BLOG = "https://thedrowsywinger.github.io/blog/"
HERE = Path(__file__).parent
OUT = HERE.parent.parent / "assets" / "writing.svg"
FONTS = {k: TTFont(HERE / "fonts" / v) for k, v in {
    "serif": "Literata-Regular.ttf", "mono": "DMMono-Medium.ttf", "cond": "BarlowCondensed-Bold.ttf"}.items()}
C = dict(card="#1d1a17", line="#2c2824", line2="#3d3732", ink="#ebe5dc", muted="#9c938a")
ROW = re.compile(r'<li><span class="list__main"><a class="link" href="([^"]+)">(.*?)</a>.*?'
                 r'<time class="list__meta" datetime="(\d{4}-\d{2}-\d{2})">', re.S)


def essays(n=5):
    req = urllib.request.Request(BLOG, headers={"User-Agent": "profile-readme-updater"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    found = {href: (html.unescape(t), d) for href, t, d in ROW.findall(page)}
    rows = sorted(((d, t) for t, d in found.values()), reverse=True)[:n]
    if len(rows) < n:
        sys.exit(f"Found only {len(rows)} essays; the blog layout may have changed.")
    return [(t, date.fromisoformat(d)) for d, t in rows]


def width(font, s, size, tr=0.0):
    f = FONTS[font]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), cmap[63])][0] for c in s) * size / upm + tr * size * max(len(s) - 1, 0)


def text(font, s, x, y, size, fill, anchor="start", tr=0.0):
    f = FONTS[font]
    cmap, gs, hmtx, upm = f.getBestCmap(), f.getGlyphSet(), f["hmtx"], f["head"].unitsPerEm
    k = size / upm
    if anchor == "end":
        x -= width(font, s, size, tr)
    pen = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    for c in s:
        g = cmap.get(ord(c), cmap[63])
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
        x += hmtx[g][0] * k + tr * size
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'


def card(rows):
    W, row = 880, 46
    H = 84 + row * len(rows) + 16
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{C["card"]}" stroke="{C["line"]}"/>',
         text("cond", "RECENT WRITING", 28, 44, 20, C["ink"], tr=0.08),
         text("mono", "PUBLISHED", 852, 44, 11, C["muted"], "end", 0.1),
         f'<line x1="28" y1="64" x2="852" y2="64" stroke="{C["line2"]}"/>']
    for i, (title, d) in enumerate(rows):
        y = 64 + row * i
        if i:
            b.append(f'<line x1="28" y1="{y}" x2="852" y2="{y}" stroke="{C["line"]}"/>')
        size = 17
        while width("serif", title, size) > 680 and size > 12:
            size -= 0.5
        mid = y + row / 2 + 5
        b.append(text("serif", title, 28, mid, size, C["ink"]))
        b.append(text("mono", f"{d.day} {d:%b %Y}".upper(), 852, mid, 11.5, C["muted"], "end", 0.08))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Recent writing: {len(rows)} published essays on backend work.">{"".join(b)}</svg>')


if __name__ == "__main__":
    rows = essays()
    OUT.write_text(card(rows))
    for t, d in rows:
        print(d, t)
