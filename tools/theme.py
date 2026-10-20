"""Design tokens for the profile cards.

Every card is a self-contained SVG. Colours are CSS custom properties defined
inside the file, with a dark-mode override in a `prefers-color-scheme` media
query — so one file serves both GitHub themes, works inside a table cell, and
needs no <picture> juggling.

The palette follows the violet -> cyan scheme that dominates 2026 profile
READMEs: #7C3AED -> #4E7FD4 -> #06B6D4.
"""

SANS = (
    'ui-sans-serif, -apple-system, "Segoe UI", "Microsoft YaHei", '
    '"PingFang SC", "Noto Sans SC", Roboto, Helvetica, Arial, sans-serif'
)
MONO = (
    'ui-monospace, "Cascadia Mono", "SF Mono", SFMono-Regular, Menlo, '
    'Consolas, "Liberation Mono", monospace'
)

LIGHT = {
    "--card": "#ffffff",
    "--card-2": "#f6f8fa",
    "--border": "#d0d7de",
    "--ink": "#1f2328",
    "--ink-2": "#424a53",
    "--muted": "#59636e",
    "--faint": "#8c959f",
    "--heat-0": "#ebedf0",
    "--heat-1": "#ded1f9",
    "--heat-2": "#bda4f6",
    "--heat-3": "#8b5cf6",
    "--heat-4": "#06b6d4",
}

DARK = {
    "--card": "#161b22",
    "--card-2": "#0d1117",
    "--border": "#30363d",
    "--ink": "#e6edf3",
    "--ink-2": "#c9d1d9",
    "--muted": "#9198a1",
    "--faint": "#6e7681",
    "--heat-0": "#171b21",
    "--heat-1": "#2a1b4d",
    "--heat-2": "#4c2a9e",
    "--heat-3": "#7c3aed",
    "--heat-4": "#06b6d4",
}

GRADIENT = {
    "--grad-a": "#7c3aed",
    "--grad-b": "#4e7fd4",
    "--grad-c": "#06b6d4",
}

# Semantic names used by the drawing code.
TOKENS = {
    "card": "var(--card)",
    "card2": "var(--card-2)",
    "border": "var(--border)",
    "ink": "var(--ink)",
    "ink2": "var(--ink-2)",
    "muted": "var(--muted)",
    "faint": "var(--faint)",
    "grad_a": "var(--grad-a)",
    "grad_b": "var(--grad-b)",
    "grad_c": "var(--grad-c)",
}

# Accent dots for the four headline numbers.
ACCENTS = ["var(--grad-c)", "var(--grad-b)", "var(--grad-a)", "#f59e0b"]


def style_block():
    def block(variables):
        return "".join(f"{name}:{value};" for name, value in variables.items())

    return (
        "<style>"
        ":root{" + block(LIGHT) + block(GRADIENT) + "}"
        "@media (prefers-color-scheme:dark){:root{"
        + block(DARK)
        + "}}"
        "</style>"
    )


def language_colour(github_colour):
    """GitHub's linguist colour, desaturated a little so the cards stay calm.

    No mixing towards the page background: the card can be shown in either
    theme, so the swatch has to work on both.
    """
    if not github_colour or not github_colour.startswith("#") or len(github_colour) != 7:
        return "var(--faint)"
    import colorsys

    r, g, b = (int(github_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    calm = colorsys.hls_to_rgb(hue, lightness, saturation * 0.75)
    return "#%02X%02X%02X" % tuple(round(channel * 255) for channel in calm)
