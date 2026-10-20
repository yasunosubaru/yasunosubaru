"""A very small SVG builder: enough for hand-placed dashboard panels."""

from __future__ import annotations

import html

from theme import MONO, SANS


def esc(value):
    return html.escape(str(value), quote=True)


def num(value):
    if isinstance(value, float):
        return ("%.2f" % value).rstrip("0").rstrip(".")
    return str(value)


def count(value):
    return f"{value:,}"


def human_bytes(value):
    value = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return ("%d %s" % (value, unit)) if unit == "B" else ("%.1f %s" % (value, unit))
        value /= 1024
    return "%.1f GB" % value


def pct(value):
    return ("%.1f" % value).rstrip("0").rstrip(".") + "%"


def width_of(text, size, mono=False):
    """Rough rendered width; good enough to place one label beside another."""
    if mono:
        units = 0.0
        for ch in text:
            units += 1.0 if ord(ch) > 0x2E7F else 0.6
        return units * size
    units = 0.0
    for ch in text:
        o = ord(ch)
        if o > 0x2E7F:
            units += 1.0
        elif ch in " .,:;'|!il1":
            units += 0.32
        elif ch in "MW@%":
            units += 0.92
        elif ch.isupper() or ch.isdigit():
            units += 0.62
        else:
            units += 0.55
    return units * size


def truncate(text, size, max_width, mono=False):
    if width_of(text, size, mono) <= max_width:
        return text
    ellipsis = "…"
    limit = max_width - width_of(ellipsis, size, mono)
    out = ""
    for ch in text:
        if width_of(out + ch, size, mono) > limit:
            break
        out += ch
    return out.rstrip(" ,，、;；") + ellipsis


class Doc:
    def __init__(self, width, height, theme, *, background=None, frame=False):
        self.w = width
        self.h = height
        self.t = theme
        self.parts = []
        if background:
            self.rect(0, 0, width, height, background)
        if frame:
            self.rect(0.5, 0.5, width - 1, height - 1, "none",
                      stroke=theme["line"], sw=1, rx=4)

    # -- primitives ---------------------------------------------------------
    def add(self, markup):
        self.parts.append(markup)

    def rect(self, x, y, w, h, fill, rx=0, stroke=None, sw=1, opacity=None, cls=None):
        bits = [
            f'x="{num(x)}"', f'y="{num(y)}"', f'width="{num(w)}"', f'height="{num(h)}"',
            f'fill="{fill}"',
        ]
        if rx:
            bits.append(f'rx="{num(rx)}"')
        if stroke:
            bits.append(f'stroke="{stroke}" stroke-width="{num(sw)}"')
        if opacity is not None:
            bits.append(f'opacity="{num(opacity)}"')
        if cls:
            bits.append(f'class="{cls}"')
        self.add(f"<rect {' '.join(bits)}/>")

    def line(self, x1, y1, x2, y2, stroke, sw=1, opacity=None, dash=None, cls=None, path_length=None):
        bits = [
            f'x1="{num(x1)}"', f'y1="{num(y1)}"', f'x2="{num(x2)}"', f'y2="{num(y2)}"',
            f'stroke="{stroke}" stroke-width="{num(sw)}"',
        ]
        if opacity is not None:
            bits.append(f'opacity="{num(opacity)}"')
        if dash:
            bits.append(f'stroke-dasharray="{dash}"')
        if cls:
            bits.append(f'class="{cls}"')
        if path_length:
            bits.append(f'pathLength="{path_length}"')
        self.add(f"<line {' '.join(bits)}/>")

    def circle(self, cx, cy, r, fill, opacity=None, cls=None):
        bits = [f'cx="{num(cx)}"', f'cy="{num(cy)}"', f'r="{num(r)}"', f'fill="{fill}"']
        if opacity is not None:
            bits.append(f'opacity="{num(opacity)}"')
        if cls:
            bits.append(f'class="{cls}"')
        self.add(f"<circle {' '.join(bits)}/>")

    def path(self, d, fill="none", stroke=None, sw=1, opacity=None, cls=None, path_length=None):
        bits = [f'd="{d}"', f'fill="{fill}"']
        if stroke:
            bits.append(f'stroke="{stroke}" stroke-width="{num(sw)}"')
            bits.append('stroke-linejoin="round" stroke-linecap="round"')
        if opacity is not None:
            bits.append(f'opacity="{num(opacity)}"')
        if cls:
            bits.append(f'class="{cls}"')
        if path_length:
            bits.append(f'pathLength="{path_length}"')
        self.add(f"<path {' '.join(bits)}/>")

    def text(self, x, y, value, size=15, fill=None, weight=400, mono=False,
             anchor="start", ls=None, opacity=None, cls=None):
        bits = [
            f'x="{num(x)}"', f'y="{num(y)}"',
            f'font-family="{esc(MONO if mono else SANS)}"',
            f'font-size="{num(size)}"',
            f'fill="{fill or self.t["ink"]}"',
        ]
        if weight != 400:
            bits.append(f'font-weight="{weight}"')
        if anchor != "start":
            bits.append(f'text-anchor="{anchor}"')
        if ls:
            bits.append(f'letter-spacing="{ls}"')
        if opacity is not None:
            bits.append(f'opacity="{num(opacity)}"')
        if cls:
            bits.append(f'class="{cls}"')
        self.add(f"<text {' '.join(bits)}>{esc(value)}</text>")

    # -- output -------------------------------------------------------------
    def render(self, title, desc):
        style = (
            "<style>"
            "@media (prefers-reduced-motion: no-preference){"
            ".draw{stroke-dasharray:1;stroke-dashoffset:1;animation:draw .9s .3s ease-out forwards}"
            ".pulse{animation:pulse 3.8s ease-in-out infinite}"
            "}"
            "@keyframes draw{to{stroke-dashoffset:0}}"
            "@keyframes pulse{0%,100%{opacity:.25}50%{opacity:1}}"
            "</style>"
        )
        body = "\n  ".join(self.parts)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t d">\n'
            f"  <title id=\"t\">{esc(title)}</title>\n"
            f"  <desc id=\"d\">{esc(desc)}</desc>\n"
            f"  {style}\n"
            f"  {body}\n"
            "</svg>\n"
        )
