# =============================================================================
# File: cache.ps1
# Purpose: Launch STONKS cache tools.
# =============================================================================

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    & ".\venv\Scripts\Activate.ps1"

    $env:PYTHONPATH = "src"

    python -m stonks.cache.cache_cli
}
finally {
    Pop-Location
}