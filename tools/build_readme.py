"""Rewrite the generated block in README.md from data/profile.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- projects:start -->"
END = "<!-- projects:end -->"


def md_escape(text):
    for char in ("[", "]", "|", "*", "_", "`"):
        text = text.replace(char, "\\" + char)
    return text


def units(text):
    return sum(2 if ord(char) > 0x2E7F else 1 for char in text)


def blurb(text, limit=124):
    text = " ".join(text.split()).replace("公开脱敏仓库", "").strip()
    if units(text) <= limit:
        return text
    cut = 0
    for mark in ("。", ". "):
        position = text.find(mark)
        if position > 0 and units(text[:position + 1]) <= limit:
            cut = position + 1
            break
    if cut:
        return text[:cut].strip()
    out = ""
    for char in text:
        if units(out + char) > limit - 1:
            break
        out += char
    if " " in out and ord(out[-1]) < 0x2E7F:
        out = out.rsplit(" ", 1)[0]
    out = out.rstrip("，、；： ,.;")
    return out + "…"


def entry(repo):
    language = repo.get("primary_language")
    suffix = f" `{language}`" if language else ""
    description = blurb(repo["description"])
    return (
        f"- **[{md_escape(repo['name'])}]({repo['url']})**{suffix}\n"
        f"  {md_escape(description)}"
    )


def main():
    data = json.loads((ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
    block = "\n".join(entry(repo) for repo in data["featured"])

    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    replacement = f"{START}\n{block}\n{END}"
    if not pattern.search(text):
        raise SystemExit(f"README.md is missing the {START} / {END} block")
    updated = pattern.sub(lambda _: replacement, text)
    if updated != text:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(updated)
        print(f"README.md: {len(data['featured'])} projects")
    else:
        print("README.md: unchanged")


if __name__ == "__main__":
    main()
