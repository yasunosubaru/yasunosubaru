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
HALF = (600, 236)
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

    doc.line(300, 30, 300, h - 30, TOKENS["border"], 1)
    doc.line(32, 126, w - 32, 126, TOKENS["border"], 1)

    for index, (value, label) in enumerate(tiles):
        column, row = index % 2, index // 2
        x = 32 + column * 268
        y = 88 + row * 98
        doc.circle(x + 5, y - 30, 5.5, ACCENTS[index])
        doc.text(x, y, count(value), 40, TOKENS["ink"], 500, mono=True)
        doc.text(x, y + 24, label, 14, TOKENS["muted"])
    return doc


# -- languages --------------------------------------------------------------

def languages(data):
    w, h = HALF
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    entries = (data.get("primary_languages") or [])[:6]
    total = sum(entry["repos"] for entry in entries)
    doc.text(32, 48, "语言分布", 20, TOKENS["ink"], 600)
    doc.text(w - 32, 48, f"共 {total} 个仓库", 14, TOKENS["muted"], mono=True, anchor="end")

    left, right = 32, w - 32
    bar_y, bar_h, gap = 78, 15, 3
    usable = right - left - gap * max(0, len(entries) - 1)
    x = left
    for entry in entries:
        width = usable * entry["repos"] / total if total else 0
        if width <= 0:
            continue
        doc.rect(x, bar_y, width, bar_h, language_colour(entry["color"]), rx=7.5)
        x += width + gap

    for index, entry in enumerate(entries):
        column, row = index % 2, index // 2
        x = 32 + column * 268
        y = 134 + row * 34
        doc.circle(x + 5, y - 5, 5.5, language_colour(entry["color"]))
        doc.text(x + 19, y, entry["name"], 16, TOKENS["ink"])
        doc.text(x + 268 - 34, y, f"{entry['pct']:g}%", 15, TOKENS["muted"], mono=True, anchor="end")
    return doc


# -- heatmap ----------------------------------------------------------------

def heatmap(data):
    w, h = WIDE
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    days = data["contributions"]["days"]
    contributions = data["contributions"]

    doc.text(40, 48, "近一年贡献", 20, TOKENS["ink"], 600)

    # legend
    legend_x = w - 40 - 5 * 16 - 78
    doc.text(legend_x, 48, "少", 13, TOKENS["faint"], mono=True)
    for index in range(5):
        doc.rect(legend_x + 28 + index * 16, 37, 12, 12, f"var(--heat-{index})", rx=3)
    doc.text(legend_x + 28 + 5 * 16 + 7, 48, "多", 13, TOKENS["faint"], mono=True)

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
        doc.rect(
            grid_x + column * pitch,
            grid_y + row * pitch,
            square, square,
            f"var(--heat-{level(day['count'])})",
            rx=4,
        )
        if date.day <= 7 and (not month_marks or column - month_marks[-1][0] >= 4):
            month_marks.append((column, date.month))

    for column, month in month_marks:
        doc.text(grid_x + column * pitch, grid_y - 10, f"{month}月", 13, TOKENS["faint"], mono=True)

    for row, name in ((1, "周一"), (3, "周三"), (5, "周五")):
        doc.text(40, grid_y + row * pitch + 14, name, 13, TOKENS["faint"], mono=True)

    doc.text(
        40, h - 24,
        f"{contributions['total']} 次贡献 · {contributions['active_days']} 天有活动 · "
        f"最长连续 {contributions['longest_streak']} 天",
        14, TOKENS["muted"], mono=True,
    )
    return doc


# -- repos ------------------------------------------------------------------

def repos(data):
    w, h = TALL
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    doc.text(32, 48, "仓库", 20, TOKENS["ink"], 600)
    doc.text(w - 32, 48, "最近更新", 14, TOKENS["muted"], mono=True, anchor="end")

    entries = data.get("showcase") or []
    for index, repo in enumerate(entries):
        y = 96 + index * 40
        doc.circle(38, y - 5, 5.5, language_colour(repo.get("language_color")))
        doc.text(53, y, repo["name"], 16, TOKENS["ink"], 600, mono=True)
        stars = repo.get("stars", 0)
        doc.text(w - 32, y, f"★ {stars}", 14, TOKENS["muted"], mono=True, anchor="end")
        description = truncate(repo.get("description", ""), 13.5, 455)
        if description:
            doc.text(53, y + 18, description, 13.5, TOKENS["muted"])
    return doc


# -- monthly ----------------------------------------------------------------

def monthly(data):
    w, h = TALL
    doc = Doc(w, h)
    card(doc, 0, 0, w, h)

    doc.text(32, 48, "月度活跃", 20, TOKENS["ink"], 600)
    doc.text(w - 32, 48, "自注册以来", 14, TOKENS["muted"], mono=True, anchor="end")

    months = (data.get("contributions", {}).get("by_month") or [])
    created = (data.get("user", {}).get("created_at") or "")[:7]
    if created:
        months = [month for month in months if month["month"] >= created]
    months = months[-12:]
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
        height = max(4, value / peak * (baseline - top))
        colour = TOKENS["grad_a"] if value else TOKENS["border"]
        doc.rect(centre - bar_w / 2, baseline - height, bar_w, height, colour, rx=6)
        if value:
            doc.text(centre, baseline - height - 10, count(value), 13, TOKENS["muted"], mono=True, anchor="middle")
        label = f"{int(month['month'][5:7])}月"
        doc.text(centre, baseline + 26, label, 13, TOKENS["faint"], mono=True, anchor="middle")
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


PREVIEW = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>bento preview</title>
<style>
  body {{ margin: 0; background: #0d1117; padding: 24px 0; }}
  .wrap {{ width: 880px; margin: 0 auto; }}
  img {{ max-width: 100%; display: block; }}
  table {{ width: 100%; border-collapse: collapse; border-spacing: 0; }}
  td {{ padding: 0; vertical-align: top; }}
</style></head><body><div class="wrap">
{body}
</div></body></html>
"""


def preview():
    folder = ROOT / ".preview"
    folder.mkdir(exist_ok=True)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    body = readme.replace('src="assets/', 'src="../assets/')
    (folder / "bento.html").write_text(PREVIEW.format(body=body), encoding="utf-8")
    return folder


def main():
    written, data = render_all()
    preview()
    print(f"rendered {len(written)} cards for {data['meta']['login']}")


if __name__ == "__main__":
    main()
