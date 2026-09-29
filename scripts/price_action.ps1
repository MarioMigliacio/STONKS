# =============================================================================
# File: price_action.ps1
# Purpose: Launch the STONKS price-action CLI.
# =============================================================================

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    & ".\venv\Scripts\Activate.ps1"

    $env:PYTHONPATH = "src"

    python -m stonks.price_action_cli
}
finally {
    Pop-Location
}