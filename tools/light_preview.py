"""Render the light palette only, for visual QA of the light theme.

Usage: python tools/light_preview.py  -> .preview/bento-light-preview.html
Then restore the normal assets with `python tools/render.py`.
"""

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import svgkit  # noqa: E402
import theme  # noqa: E402


def light_only():
    body = "".join(f"{k}:{v};" for k, v in theme.LIGHT.items())
    body += "".join(f"{k}:{v};" for k, v in theme.GRADIENT.items())
    return "<style>:root{" + body + "}</style>"


def main():
    svgkit.style_block = light_only
    import render

    written, _ = render.render_all()
    light_dir = ROOT / ".preview" / "light-assets"
    light_dir.mkdir(parents=True, exist_ok=True)
    for path in written:
        (light_dir / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme = readme.replace('src="assets/', 'src="light-assets/')
    page = render.PREVIEW.format(body=readme)
    out = ROOT / ".preview" / "bento-light-preview.html"
    out.write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
