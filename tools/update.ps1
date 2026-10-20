# Refresh every card and the generated README block, then look at .preview/.
# The token is only needed to raise GitHub's rate limit; the proxy fallback
# reuses whatever `git config http.proxy` already says.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not $env:GITHUB_TOKEN) {
    $token = gh auth token 2>$null
    if ($token) { $env:GITHUB_TOKEN = $token }
}

if (-not $env:HTTPS_PROXY -and -not $env:HTTP_PROXY) {
    $proxy = git config --get http.proxy
    if ($proxy) {
        $env:HTTPS_PROXY = $proxy
        $env:HTTP_PROXY = $proxy
    }
}

python "$root\tools\update.py"
