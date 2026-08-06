# =============================================================================
# File: news.ps1
# Purpose: Launch the STONKS news-provider CLI.
# =============================================================================

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    & ".\venv\Scripts\Activate.ps1"

    $env:PYTHONPATH = "src"

    python -m stonks.news.news_cli
}
finally {
    Pop-Location
}