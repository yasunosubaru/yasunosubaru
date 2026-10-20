"""Render data/profile.json into the SVG cards in assets/.

Every card is drawn twice: once for GitHub's light theme, once for dark.
Data panels stay transparent so they sit on the page; only the hero is a plate.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

from svgkit import Doc, count, num, truncate, width_of
from theme import THEMES, language_colour

ROOT = Path(__file__).resolve().parents[1]
W = 1000
M = 44
PAD = 24  # inner padding of a readout cell


def load():
    data = json.loads((ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
    return data, config


def stamp(iso_value):
    moment = datetime.strptime(iso_value, "%Y-%m-%dT%H:%M:%SZ")
    return moment.strftime("%Y-%m-%d %H:%M UTC")


def short_date(iso_value):
    return iso_value[5:]


def panel_title(doc, title, right=None):
    doc.text(M, 40, title, 20, doc.t["ink"], 600)
    if right:
        doc.text(W - M, 41, right, 12.5, doc.t["ink3"], mono=True, anchor="end")
    doc.line(M, 56, W - M, 56, doc.t["soft"])


# -- hero -------------------------------------------------------------------

def hero(theme, data, config):
    t = theme
    doc = Doc(W, 272, t, background=t["bg"], frame=True)
    doc.text(M, 66, config["kicker"], 12.5, t["ink3"], mono=True, ls="0.06em")

    moment = stamp(data["meta"]["generated_at"])
    doc.text(W - M, 66, moment, 12.5, t["ink3"], mono=True, anchor="end")
    doc.circle(W - M - width_of(moment, 12.5, True) - 13, 62, 3.5, t["accent"], cls="pulse")

    doc.text(M, 112, config["headline"], 44, t["ink"], 600, ls="-0.02em")
    doc.line(M, 128, M + 48, 128, t["accent"], 3, cls="draw", path_length=1)
    doc.text(M, 166, config["statement"], 20, t["ink2"])
    doc.line(M, 192, W - M, 192, t["soft"])

    contributions = data["contributions"]
    cells = [
        (count(data["user"]["public_repos"]), "公开仓库", False),
        (count(contributions["total"]), "近一年贡献", True),
        (count(contributions["current_streak"]), "当前连续（天）", False),
        (count(contributions["best_day"]["count"]), "单日峰值", False),
    ]
    cell_w = (W - 2 * M) / len(cells)
    for index, (value, label, accent) in enumerate(cells):
        x = M + index * cell_w
        if index:
            doc.line(x - PAD, 204, x - PAD, 254, t["soft"])
        doc.text(x, 228, value, 36, t["accent"] if accent else t["ink"], 500, mono=True)
        doc.text(x, 250, label, 12.5, t["ink3"], mono=True, ls="0.02em")
    return doc


# -- rhythm -----------------------------------------------------------------

def rhythm(theme, data, config):
    t = theme
    doc = Doc(W, 330, t)
    window = 42
    days = data["contributions"]["days"][-window:]
    panel_title(doc, f"近 {window // 7} 周", "每日贡献 / 7 日均线")

    x0, x1 = 64, W - M
    y0, y1 = 78, 198
    values = [day["count"] for day in days]
    peak = max(values) if values else 0
    top = max(30, math.ceil(peak / 30) * 30)

    pitch = (x1 - x0) / window
    bar_w = min(13, pitch - 6)

    def y_of(value):
        return y1 - value / top * (y1 - y0)

    for tick in (0, top / 2, top):
        y = y_of(tick)
        doc.line(x0, y, x1, y, t["line"] if tick == 0 else t["soft"])
        doc.text(x0 - 8, y + 4, str(int(tick)), 11.5, t["ink3"], mono=True, anchor="end")

    for index, day in enumerate(days):
        value = day["count"]
        if value <= 0:
            continue
        x = x0 + index * pitch + (pitch - bar_w) / 2
        height = y1 - y_of(value)
        if value == peak:
            doc.rect(x, y_of(value), bar_w, height, t["accent"], rx=2, opacity=0.92)
        else:
            doc.rect(x, y_of(value), bar_w, height, t["ink3"], rx=2, opacity=0.34)

    all_counts = [day["count"] for day in data["contributions"]["days"]]
    offset = len(all_counts) - window
    points = []
    for index in range(window):
        tail = all_counts[max(0, offset + index - 6): offset + index + 1]
        mean = sum(tail) / len(tail) if tail else 0
        points.append((x0 + index * pitch + pitch / 2, y_of(mean)))
    doc.path(
        "M " + " L ".join(f"{num(x)} {num(y)}" for x, y in points),
        stroke=t["accent"], sw=2.25,
    )

    peak_index = values.index(peak)
    peak_x = x0 + peak_index * pitch + pitch / 2
    doc.circle(peak_x, y_of(peak), 3.5, t["accent"])
    label = f"{short_date(days[peak_index]['date'])} / {peak} 次"
    if peak_x < x1 - width_of(label, 12, True) - 20:
        doc.text(peak_x + 11, y_of(peak) + 4, label, 12, t["ink2"], mono=True)
    else:
        doc.text(peak_x - 11, y_of(peak) + 4, label, 12, t["ink2"], mono=True, anchor="end")

    for index in range(0, window, 7):
        x = x0 + index * pitch + pitch / 2
        label = f"{int(days[index]['date'][5:7])}/{int(days[index]['date'][8:10])}"
        doc.text(x, y1 + 22, label, 11.5, t["ink3"], mono=True, anchor="middle")

    doc.line(M, 246, W - M, 246, t["soft"])
    contributions = data["contributions"]
    facts = [
        ("活跃天", contributions["active_days"]),
        ("最长连续（天）", contributions["longest_streak"]),
        ("活跃日均", contributions["avg_per_active_day"]),
    ]

    cell_w = (W - 2 * M) / len(facts)
    for index, (label, value) in enumerate(facts):
        x = M + index * cell_w
        doc.text(x, 290, count(value), 28, t["ink"], 500, mono=True)
        doc.text(x, 310, label, 12.5, t["ink3"], mono=True)
    doc.text(W - M, 310, "近一年 / 365 天", 12, t["ink3"], mono=True, anchor="end")
    return doc


# -- languages --------------------------------------------------------------

def languages(theme, data, config):
    t = theme
    doc = Doc(W, 272, t)
    entries = data.get("primary_languages") or []
    total = sum(entry["repos"] for entry in entries)
    panel_title(doc, "语言分布", "按主语言统计 · 不含 fork")

    gap = 3
    usable = (W - 2 * M) - gap * max(0, len(entries) - 1)
    x = M
    for entry in entries:
        width = usable * entry["repos"] / total if total else 0
        if width <= 0:
            continue
        doc.rect(x, 78, width, 18, language_colour(entry["color"], t), rx=3)
        x += width + gap

    columns = 2
    col_w = (W - 2 * M) / columns
    for index, entry in enumerate(entries):
        column, row = index % columns, index // columns
        x = M + column * col_w
        y = 146 + row * 34
        doc.circle(x + 5, y - 4.5, 4.5, language_colour(entry["color"], t))
        doc.text(x + 19, y, entry["name"], 15, t["ink"])
        doc.text(x + col_w - 20, y, f"{entry['pct']:g}%", 14, t["ink2"], mono=True, anchor="end")

    index = len(entries)
    column, row = index % columns, index // columns
    doc.text(M + column * col_w + 19, 146 + row * 34, f"共 {total} 个仓库", 12.5, t["ink3"], mono=True)
    return doc


# -- preview ----------------------------------------------------------------

PREVIEW = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{title}</title>
<style>
  :root {{ color-scheme: {scheme}; }}
  body {{ margin: 0; background: {bg}; color: {fg};
         font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; }}
  main {{ width: 880px; margin: 0 auto; padding: 32px 0 64px; }}
  p {{ margin: 0 0 16px; }}
  img {{ max-width: 100%; display: block; margin: 0 0 24px; }}
  h1 {{ font-size: 24px; margin: 24px 0 8px; }}
  .muted {{ color: {muted}; }}
</style></head>
<body><main>
<p>我在武汉大学地空学院，把测量、运维和安全里反复出现的问题做成工具：GNSS 信号分析、
Windows 控制台、离线维基 U 盘、会自己复现漏洞的 AI 智能体。下载就能跑。</p>
<p class="muted">这些数字每 6 小时重新算一次，不是截图。</p>
<img src="../assets/hero-{theme}.svg" width="880" alt="">
<img src="../assets/rhythm-{theme}.svg" width="880" alt="">
<img src="../assets/languages-{theme}.svg" width="880" alt="">
<h1>项目</h1>
<p>项目列表由 Actions 重写，这里只检查图片。</p>
</main></body></html>
"""


GALLERY = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>gallery {theme}</title>
<style>
  html {{ background: {bg}; }}
  body {{ margin: 0; background: {bg}; }}
  img {{ display: block; width: 1000px; margin: 0 0 18px; }}
</style></head>
<body>
<img src="../assets/hero-{theme}.svg" width="1000" alt="">
<img src="../assets/rhythm-{theme}.svg" width="1000" alt="">
<img src="../assets/languages-{theme}.svg" width="1000" alt="">
</body></html>
"""


def render_all():
    data, config = load()
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    written = []
    for name, theme in THEMES.items():
        cards = {
            "hero": (hero(theme, data, config), "yasunosubaru — 仪器、桌面工具、AI 智能体"),
            "rhythm": (rhythm(theme, data, config), "近 6 周每日贡献与 7 日均线"),
            "languages": (languages(theme, data, config), "按主语言统计的仓库分布"),
        }
        for key, (doc, title) in cards.items():
            path = assets / f"{key}-{name}.svg"
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(doc.render(title, title))
            written.append(path)
    return written, data


def preview():
    folder = ROOT / ".preview"
    folder.mkdir(exist_ok=True)
    settings = {
        "light": ("#ffffff", "#1f2328", "#59636e", "light"),
        "dark": ("#0d1117", "#e6edf3", "#9198a1", "dark"),
    }
    for theme, (bg, fg, muted, scheme) in settings.items():
        page = PREVIEW.format(title=f"profile {theme}", bg=bg, fg=fg, muted=muted, scheme=scheme, theme=theme)
        (folder / f"preview-{theme}.html").write_text(page, encoding="utf-8")
        gallery = GALLERY.format(theme=theme, bg=bg)
        (folder / f"gallery-{theme}.html").write_text(gallery, encoding="utf-8")
    return folder


def main():
    written, data = render_all()
    preview()
    print(f"rendered {len(written)} cards for {data['meta']['login']}")


if __name__ == "__main__":
    main()

