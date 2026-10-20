"""Design tokens for the profile cards.

Two hand-tuned themes. Panels are painted transparent so they sit on GitHub's
own page colour; only the hero plate paints a surface.
"""

SANS = (
    'ui-sans-serif, -apple-system, "Segoe UI", "Microsoft YaHei", '
    '"PingFang SC", "Noto Sans SC", Roboto, Helvetica, Arial, sans-serif'
)
MONO = (
    'ui-monospace, "Cascadia Mono", "SF Mono", SFMono-Regular, Menlo, '
    'Consolas, "Liberation Mono", monospace'
)

THEMES = {
    "dark": {
        "bg": "#0C1218",
        "line": "#22303B",
        "soft": "#1A2732",
        "ink": "#E8EFF4",
        "ink2": "#A6B6C2",
        "ink3": "#8093A0",
        "accent": "#E3A93F",
        "accent_soft": "#F0C97B",
        "heat": ["#16212A", "#45361D", "#75571F", "#A87E2B", "#E8B558"],
        "series": ["#E3A93F", "#5FA8A0", "#7E9BC4", "#C8796F", "#B9A88A", "#8FA36A"],
        "grid": "#1B2832",
    },
    "light": {
        "bg": "#F6F8F9",
        "line": "#D7E0E5",
        "soft": "#E6EDF0",
        "ink": "#101A21",
        "ink2": "#465862",
        "ink3": "#66787F",
        "accent": "#A96D12",
        "accent_soft": "#C08A2A",
        "heat": ["#E7EDF0", "#F1DDB7", "#E2C07C", "#C79A45", "#9A6A1C"],
        "series": ["#A96D12", "#2F7F77", "#4E6E96", "#A65A50", "#8A7A5E", "#6E8446"],
        "grid": "#E9EFF2",
    },
}


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Blend colour a toward b by t (0 = a, 1 = b)."""
    ra, rb = rgb(a), rgb(b)
    return "#%02X%02X%02X" % tuple(round(ra[i] * (1 - t) + rb[i] * t) for i in range(3))


def language_colour(github_colour, theme, weight=0.14):
    """GitHub's linguist colour, desaturated a little so the cards stay calm."""
    if not github_colour or not github_colour.startswith("#") or len(github_colour) != 7:
        return theme["ink3"]
    import colorsys

    r, g, b = (value / 255 for value in rgb(github_colour))
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    calm = colorsys.hls_to_rgb(hue, lightness, saturation * 0.55)
    base = "#%02X%02X%02X" % tuple(round(channel * 255) for channel in calm)
    return mix(base, theme["bg"], weight)
