"""Thin GitHub API client: REST + GraphQL, no third-party dependencies.

Reads HTTPS_PROXY / HTTP_PROXY from the environment (urllib does this for us),
so it works both on a proxied desktop and on a plain Actions runner.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.github.com"
UA = "yasunosubaru-profile-dashboard (+https://github.com/yasunosubaru/yasunosubaru)"


class GitHubError(RuntimeError):
    pass


def token():
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def _request(url, payload=None, *, api=True, auth=True, timeout=45):
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if api and auth:
        tok = token()
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _retry(call, attempts=3, base=4):
    last = None
    for index in range(attempts):
        try:
            return call()
        except urllib.error.HTTPError as error:
            last = error
            exhausted = error.headers.get("X-RateLimit-Remaining") == "0"
            if error.code in (429, 500, 502, 503, 504) or (error.code == 403 and exhausted):
                time.sleep(base * (index + 1))
                continue
            body = error.read().decode("utf-8", "replace")[:300]
            raise GitHubError(f"HTTP {error.code} {url_of(error)}: {body}") from None
        except (urllib.error.URLError, TimeoutError) as error:
            last = error
            time.sleep(base * (index + 1))
    raise GitHubError(f"request failed: {last}")


def url_of(error):
    return getattr(error, "url", "?")


def graphql(query, variables):
    payload = {"query": query, "variables": variables}
    raw = _retry(lambda: _request(API + "/graphql", payload))
    body = json.loads(raw.decode("utf-8"))
    if body.get("errors"):
        message = "; ".join(item.get("message", "?") for item in body["errors"])
        raise GitHubError(f"GraphQL: {message}")
    return body["data"]


def rest(path):
    raw = _retry(lambda: _request(API + path))
    return json.loads(raw.decode("utf-8"))


def public_rest(path):
    """REST without a token: only public resources are visible, which is
    exactly what a visitor of the profile sees."""
    raw = _retry(lambda: _request(API + path, auth=False))
    return json.loads(raw.decode("utf-8"))


def public_html(path, *, timeout=45):
    return _retry(lambda: _request("https://github.com" + path, api=False, timeout=timeout)).decode("utf-8", "replace")
