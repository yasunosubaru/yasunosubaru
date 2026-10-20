"""Render data/profile.json into the SVG cards in assets/.

Six cards, each a self-contained SVG. Colours come from CSS custom properties
defined inside the file (see theme.py), so a single file works in both GitHub
themes and inside a table cell.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

from svgkit import Doc, count, truncate, width_of
from theme import ACCENTS, TOKENS, language_colour

ROOT = Path(__file__).resolve().parents[1]

# card sizes
BANNER = (1200, 220)
HALF = (600, 212)
WIDE = (1200, 250)
TALL = (600, 330)


def load():
    data = json.loads((ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
    return data, config


def stamp(iso_value):
    moment = dt.datetime.strptime(iso_value, "%Y-%m-%dT%H:%M:%SZ")
    return moment.strftime("%Y-%m-%d %H:%M UTC")


def card(doc, x, y, w, h, radius=18):
    doc.rect(x, y, w, h, TOKENS["card"], rx=radius, stroke=TOKENS["border"], sw=1, filt="shadow")


# -- banner -----------------------------------------------------------------

def banner(data, config):
    w, h = BANNER
    doc = Doc(w, h)
    doc.gradient("grad", [(0, TOKENS["grad_a"]), (0.5, TOKENS["grad_b"]), (1, TOKENS["grad_c"])])
    doc.radial("glow", [(0, "rgba(255,255,255,0.22)"), (1, "rgba(255,255,255,0)")], 0.72, 0.18, 0.55)
    doc.pattern("dots", '<circle cx="2" cy="2" r="1.7" fill="#ffffff" opacity="0.16"/>', 30, 30)

    doc.rect(0, 0, w, h, "url(#grad)", rx=22)
    doc.rect(0, 0, w, h, "url(#glow)", rx=22)
    doc.rect(0, 0, w, h, "url(#dots)", rx=22)

    doc.text(64, 128, config["headline"], 56, "#ffffff", 700, ls="-0.03em")
    doc.rect(64, 150, 58, 5, "#ffffff", rx=2.5, opacity=0.92)

    moment = stamp(data["meta"]["generated_at"])
    doc.text(w - 56, 72, moment, 14, "#ffffff", mono=True, anchor="end", opacity=0.82)
    doc.circle(w - 56 - width_of(moment, 14, True) - 14, 67, 4, "#ffffff", opacity=0.9, cls="pulse")
    return doc


# -- stats ------------------------------------------------------------------

def stats(data):
    w, h = HALF
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    counts = data.get("counts", {})
    contributions = data["contributions"]
    tiles = [
        (data["user"]["public_repos"], "公开仓库"),
        (contributions["total"], "近一年贡献"),
        (counts.get("pull_requests", 0), "Pull Request"),
        (counts.get("issues", 0), "Issue"),
    ]

    doc.line(300, 34, 300, h - 34, TOKENS["border"], 1)
    doc.line(32, 116, w - 32, 116, TOKENS["border"], 1)

    for index, (value, label) in enumerate(tiles):
        column, row = index % 2, index // 2
        x = 32 + column * 268
        y = 92 + row * 104
        doc.circle(x + 5, y - 30, 5, ACCENTS[index])
        doc.text(x, y, count(value), 38, TOKENS["ink"], 500, mono=True)
        doc.text(x, y + 24, label, 13, TOKENS["muted"])
    return doc


# -- languages --------------------------------------------------------------

def languages(data):
    w, h = HALF
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    entries = (data.get("primary_languages") or [])[:6]
    total = sum(entry["repos"] for entry in entries)
    doc.text(32, 46, "语言分布", 19, TOKENS["ink"], 600)
    doc.text(w - 32, 46, f"共 {total} 个仓库", 13, TOKENS["muted"], mono=True, anchor="end")

    left, right = 32, w - 32
    bar_y, bar_h, gap = 74, 14, 3
    usable = right - left - gap * max(0, len(entries) - 1)
    x = left
    for entry in entries:
        width = usable * entry["repos"] / total if total else 0
        if width <= 0:
            continue
        doc.rect(x, bar_y, width, bar_h, language_colour(entry["color"]), rx=7)
        x += width + gap

    for index, entry in enumerate(entries):
        column, row = index % 2, index // 2
        x = 32 + column * 268
        y = 128 + row * 32
        doc.circle(x + 5, y - 5, 5, language_colour(entry["color"]))
        doc.text(x + 18, y, entry["name"], 15, TOKENS["ink"])
        doc.text(x + 268 - 34, y, f"{entry['pct']:g}%", 14, TOKENS["muted"], mono=True, anchor="end")
    return doc


# -- heatmap ----------------------------------------------------------------

def heatmap(data):
    w, h = WIDE
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    days = data["contributions"]["days"]
    contributions = data["contributions"]

    doc.text(40, 46, "近一年贡献", 19, TOKENS["ink"], 600)

    # legend
    legend_x = w - 40 - 5 * 14 - 76
    doc.text(legend_x, 46, "少", 12, TOKENS["faint"], mono=True)
    for index in range(5):
        doc.rect(legend_x + 26 + index * 14, 36, 11, 11, f"var(--heat-{index})", rx=3)
    doc.text(legend_x + 26 + 5 * 14 + 6, 46, "多", 12, TOKENS["faint"], mono=True)

    values = sorted(day["count"] for day in days if day["count"] > 0)
    if values:
        def quantile(fraction):
            return values[min(len(values) - 1, int(fraction * (len(values) - 1)))]

        first, second, third = quantile(0.25), quantile(0.5), quantile(0.75)
    else:
        first = second = third = 0

    def level(value):
        if value <= 0:
            return 0
        if value <= first:
            return 1
        if value <= second:
            return 2
        if value <= third:
            return 3
        return 4

    pitch, square = 20, 16
    grid_x, grid_y = 76, 88
    first_day = dt.date.fromisoformat(days[0]["date"])
    grid_start = first_day - dt.timedelta(days=(first_day.weekday() + 1) % 7)

    month_marks = []
    for index, day in enumerate(days):
        date = dt.date.fromisoformat(day["date"])
        column = (date - grid_start).days // 7
        row = (date.weekday() + 1) % 7
        if day["count"] > 0:
            doc.rect(
                grid_x + column * pitch,
                grid_y + row * pitch,
                square, square,
                f"var(--heat-{level(day['count'])})",
                rx=4,
            )
        if date.day <= 7:
            month_marks.append((column, date.month))

    for column, month in month_marks:
        doc.text(grid_x + column * pitch, grid_y - 10, f"{month}月", 12, TOKENS["faint"], mono=True)

    for row, name in ((1, "周一"), (3, "周三"), (5, "周五")):
        doc.text(40, grid_y + row * pitch + 13, name, 12, TOKENS["faint"], mono=True)

    doc.text(
        40, h - 22,
        f"{contributions['total']} 次贡献 · {contributions['active_days']} 天有活动 · "
        f"最长连续 {contributions['longest_streak']} 天",
        13, TOKENS["muted"], mono=True,
    )
    return doc


# -- repos ------------------------------------------------------------------

def repos(data):
    w, h = TALL
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    doc.text(32, 46, "仓库", 19, TOKENS["ink"], 600)
    doc.text(w - 32, 46, "最近更新", 13, TOKENS["muted"], mono=True, anchor="end")

    entries = data.get("showcase") or []
    for index, repo in enumerate(entries):
        y = 92 + index * 40
        doc.circle(38, y - 5, 5, language_colour(repo.get("primary_language_color")))
        doc.text(52, y, repo["name"], 15, TOKENS["ink"], 600, mono=True)
        stars = repo.get("stars", 0)
        doc.text(w - 32, y, f"★ {stars}", 13, TOKENS["muted"], mono=True, anchor="end")
        description = truncate(repo.get("description", ""), 12.5, 470)
        if description:
            doc.text(52, y + 17, description, 12.5, TOKENS["muted"])
    return doc


# -- monthly ----------------------------------------------------------------

def monthly(data):
    w, h = TALL
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    doc.text(32, 46, "月度活跃", 19, TOKENS["ink"], 600)
    doc.text(w - 32, 46, "近 12 个月", 13, TOKENS["muted"], mono=True, anchor="end")

    months = (data.get("contributions", {}).get("by_month") or [])[-12:]
    if not months:
        return doc

    peak = max(month["count"] for month in months) or 1
    left, right = 44, w - 36
    baseline, top = 268, 92
    slot = (right - left) / len(months)
    bar_w = min(26, slot * 0.62)

    for index, month in enumerate(months):
        centre = left + slot * (index + 0.5)
        value = month["count"]
        height = max(3, value / peak * (baseline - top))
        colour = TOKENS["grad_a"] if value else TOKENS["border"]
        doc.rect(centre - bar_w / 2, baseline - height, bar_w, height, colour, rx=6)
        if value:
            doc.text(centre, baseline - height - 9, count(value), 12, TOKENS["muted"], mono=True, anchor="middle")
        label = f"{int(month['month'][5:7])}月"
        doc.text(centre, baseline + 24, label, 12, TOKENS["faint"], mono=True, anchor="middle")
    return doc


# -- output -----------------------------------------------------------------

CARDS = {
    "banner": (banner, "yasunosubaru — 公开数据概览"),
    "stats": (stats, "公开仓库 / 贡献 / PR / Issue"),
    "languages": (languages, "按主语言统计的仓库分布"),
    "heatmap": (heatmap, "近一年的每日贡献热力图"),
    "repos": (repos, "最近更新的仓库"),
    "monthly": (monthly, "近 12 个月的活跃度"),
}


def render_all():
    data, config = load()
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    written = []
    for name, (builder, description) in CARDS.items():
        doc = builder(data, config) if name == "banner" else builder(data)
        path = assets / f"{name}.svg"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(doc.render(name, description))
        written.append(path)
    return written, data


def main():
    written, data = render_all()
    print(f"rendered {len(written)} cards for {data['meta']['login']}")


if __name__ == "__main__":
    main()
