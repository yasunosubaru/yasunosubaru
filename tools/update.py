"""One command for a full refresh: fetch, then render."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def step(script):
    print(f"→ {script}")
    subprocess.run([sys.executable, str(ROOT / "tools" / script)], cwd=ROOT, check=True)


def main():
    step("fetch_data.py")
    step("render.py")


if __name__ == "__main__":
    main()
