"""Fetch everything the cards need and write data/profile.json.

The profile is public, so every source is public too: GraphQL for repositories
and account facts (public only), the anonymous contributions page for the
calendar. A token only raises the rate limit — it never widens what is counted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

from github_api import GitHubError, graphql, public_html, rest

ROOT = Path(__file__).resolve().parents[1]

ACCOUNT_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(privacy: PUBLIC, ownerAffiliations: [OWNER], isFork: false) { totalCount }
  }
}
"""

REPOSITORIES_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(first: 100, after: $cursor, privacy: PUBLIC,
                 ownerAffiliations: [OWNER], isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name description url stargazerCount forkCount createdAt pushedAt
        isArchived primaryLanguage { name color }
        repositoryTopics(first: 20) { nodes { topic { name } } }
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

LANGUAGE_COLOURS = {
    "Python": "#3572A5", "Rust": "#DEA584", "TypeScript": "#3178C6", "C#": "#178600",
    "Dart": "#00B4AB", "PowerShell": "#012456", "JavaScript": "#F1E05A", "C++": "#F34B7D",
    "HTML": "#E34C26", "Shell": "#89E051", "Go": "#00ADD8", "C": "#555555",
    "Java": "#B07219", "Swift": "#F05138", "Kotlin": "#A97BFF", "Vue": "#41B883",
    "CSS": "#563D7C", "Jupyter Notebook": "#DA5B0B", "Batchfile": "#C1F12E",
    "Makefile": "#427819", "CMake": "#DA3434", "Lua": "#000080", "Ruby": "#701516",
}


def iso(date):
    return date.isoformat()


def warn(message):
    print(f"warning: {message}", file=sys.stderr)


# -- contributions ----------------------------------------------------------

def contributions_from_html(login, start, end):
    page = public_html(f"/users/{login}/contributions?from={iso(start)}&to={iso(end)}")
    by_id = {}
    for tag in re.findall(r"<td[^>]*>", page):
        date = re.search(r'data-date="([^"]+)"', tag)
        ident = re.search(r'id="([^"]+)"', tag)
        if date and ident:
            by_id[ident.group(1)] = date.group(1)
    counts = {}
    for tag in re.findall(r"<tool-tip[^>]*>.*?</tool-tip>", page, re.S):
        ident = re.search(r'for="([^"]+)"', tag)
        text = re.sub(r"<[^>]+>", "", tag).strip()
        if not ident or ident.group(1) not in by_id:
            continue
        if text.lower().startswith("no contribution"):
            counts[by_id[ident.group(1)]] = 0
            continue
        hit = re.match(r"([\d,]+)\s+contribution", text)
        if hit:
            counts[by_id[ident.group(1)]] = int(hit.group(1).replace(",", ""))
    if not counts:
        raise GitHubError("could not parse the contributions page")
    return counts


def streaks(series):
    longest = run = 0
    for day in series:
        run = run + 1 if day["count"] > 0 else 0
        longest = max(longest, run)
    index = len(series) - 1
    if index >= 0 and series[index]["count"] == 0:
        index -= 1
    current = 0
    while index >= 0 and series[index]["count"] > 0:
        current += 1
        index -= 1
    return current, longest


def fetch_contributions(login, start, end):
    # The public calendar is the honest source: a token can see private
    # contributions that visitors of this profile cannot.
    counts = contributions_from_html(login, start, end)

    series = []
    cursor = start
    while cursor <= end:
        key = iso(cursor)
        series.append({"date": key, "count": counts.get(key, 0)})
        cursor += dt.timedelta(days=1)

    by_month = []
    for day in series:
        month = day["date"][:7]
        if not by_month or by_month[-1]["month"] != month:
            by_month.append({"month": month, "count": 0})
        by_month[-1]["count"] += day["count"]

    active = [day for day in series if day["count"] > 0]
    best = max(series, key=lambda day: (day["count"], day["date"])) if series else {"date": "", "count": 0}
    current, longest = streaks(series)
    total = sum(day["count"] for day in series)

    return {
        "source": "github.com public calendar",
        "window": {"from": iso(start), "to": iso(end)},
        "total": total,
        "active_days": len(active),
        "avg_per_day": round(total / len(series), 2) if series else 0,
        "avg_per_active_day": round(total / len(active), 1) if active else 0,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "days": series,
        "by_month": by_month,
    }


# -- repositories -----------------------------------------------------------

def repos_from_graphql(login):
    repos, cursor = [], None
    while True:
        data = graphql(REPOSITORIES_QUERY, {"login": login, "cursor": cursor})
        user = data.get("user")
        if not user:
            raise GitHubError(f"user {login!r} not found")
        block = user["repositories"]
        for node in block["nodes"]:
            repos.append({
                "name": node["name"],
                "description": (node.get("description") or "").strip(),
                "url": node["url"],
                "stars": node["stargazerCount"],
                "forks": node["forkCount"],
                "created_at": node["createdAt"],
                "pushed_at": node["pushedAt"],
                "archived": node["isArchived"],
                "primary_language": (node.get("primaryLanguage") or {}).get("name"),
                "primary_language_color": (node.get("primaryLanguage") or {}).get("color"),
                "topics": [edge["topic"]["name"] for edge in node["repositoryTopics"]["nodes"]],
                "languages": [
                    {"name": edge["node"]["name"], "bytes": edge["size"], "color": edge["node"]["color"]}
                    for edge in node["languages"]["edges"]
                ],
            })
        if not block["pageInfo"]["hasNextPage"]:
            break
        cursor = block["pageInfo"]["endCursor"]
    return repos


def repos_from_rest(login):
    repos = []
    page = 1
    while True:
        batch = rest(f"/users/{login}/repos?per_page=100&page={page}&type=owner&sort=pushed")
        for item in batch:
            if item["fork"]:
                continue
            languages = []
            try:
                raw = rest(f"/repos/{login}/{item['name']}/languages")
                for name, size in raw.items():
                    languages.append({
                        "name": name,
                        "bytes": size,
                        "color": LANGUAGE_COLOURS.get(name),
                    })
                languages.sort(key=lambda entry: entry["bytes"], reverse=True)
            except GitHubError as error:
                warn(f"languages for {item['name']}: {error}")
            repos.append({
                "name": item["name"],
                "description": (item.get("description") or "").strip(),
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "forks": item["forks_count"],
                "created_at": item["created_at"],
                "pushed_at": item["pushed_at"],
                "archived": item["archived"],
                "primary_language": item["language"],
                "primary_language_color": LANGUAGE_COLOURS.get(item["language"] or ""),
                "topics": item.get("topics") or [],
                "languages": languages,
            })
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_repos(login):
    try:
        return repos_from_graphql(login), "graphql"
    except Exception as error:  # noqa: BLE001
        warn(f"repositories via GraphQL failed ({error}); using REST")
        return repos_from_rest(login), "rest"


def fetch_account(login):
    try:
        data = graphql(ACCOUNT_QUERY, {"login": login})
        user = data["user"]
        return {
            "created_at": user["createdAt"],
            "followers": user["followers"]["totalCount"],
            "public_repos": user["repositories"]["totalCount"],
        }
    except Exception as error:  # noqa: BLE001
        warn(f"account via GraphQL failed ({error}); using REST")
        user = rest(f"/users/{login}")
        return {
            "created_at": user["created_at"],
            "followers": user["followers"],
            "public_repos": user["public_repos"],
        }


def aggregate(repos):
    totals = {}
    for repo in repos:
        for language in repo["languages"]:
            entry = totals.setdefault(language["name"], {"name": language["name"], "bytes": 0, "color": language["color"]})
            entry["bytes"] += language["bytes"]
            entry["color"] = entry["color"] or language["color"]
    total_bytes = sum(item["bytes"] for item in totals.values()) or 1
    languages = sorted(totals.values(), key=lambda item: item["bytes"], reverse=True)
    for item in languages:
        item["pct"] = round(item["bytes"] * 100 / total_bytes, 1)

    primary = {}
    for repo in repos:
        name = repo["primary_language"]
        if not name:
            continue
        entry = primary.setdefault(name, {"name": name, "repos": 0, "color": repo["primary_language_color"]})
        entry["repos"] += 1
        entry["color"] = entry["color"] or repo["primary_language_color"]
    primary_languages = sorted(primary.values(), key=lambda item: (-item["repos"], item["name"]))
    counted = sum(item["repos"] for item in primary_languages) or 1
    for item in primary_languages:
        item["pct"] = round(item["repos"] * 100 / counted, 1)

    topics = {}
    for repo in repos:
        for topic in repo["topics"]:
            topics[topic] = topics.get(topic, 0) + 1
    return {
        "languages": languages,
        "primary_languages": primary_languages,
        "language_total_bytes": total_bytes,
        "topics": [{"name": name, "count": n} for name, n in sorted(topics.items(), key=lambda kv: (-kv[1], kv[0]))],
        "stars": sum(repo["stars"] for repo in repos),
        "forks": sum(repo["forks"] for repo in repos),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", default=None)
    parser.add_argument("--out", default=str(ROOT / "data" / "profile.json"))
    args = parser.parse_args()

    config = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
    login = args.login or os.environ.get("PROFILE_LOGIN") or config["login"]

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    end = now.date()
    start = end - dt.timedelta(days=364)

    repos, repo_source = fetch_repos(login)
    contributions = fetch_contributions(login, start, end)
    totals = aggregate(repos)
    account = fetch_account(login)

    profile = {
        "meta": {
            "login": login,
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator": "github-profile-dashboard/1",
            "repo_source": repo_source,
            "contributions_source": contributions["source"],
        },
        "user": {
            "login": login,
            "public_repos": account["public_repos"],
            "followers": account["followers"],
            "created_at": account["created_at"],
        },
        "contributions": contributions,
        "repos": repos,
        "languages": totals["languages"],
        "primary_languages": totals["primary_languages"],
        "language_total_bytes": totals["language_total_bytes"],
        "topics": totals["topics"],
        "stars": totals["stars"],
        "forks": totals["forks"],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(profile, ensure_ascii=False, indent=2) + "\n")

    print(
        f"{login}: {len(repos)} repos, {contributions['total']} contributions "
        f"({contributions['current_streak']}d streak, {contributions['active_days']} active days), "
        f"{len(totals['languages'])} languages"
    )


if __name__ == "__main__":
    main()
