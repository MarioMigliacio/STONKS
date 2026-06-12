# =============================================================================
# File: journal.ps1
# Purpose: Launch the STONKS journal CLI.
# =============================================================================

Write-Host ""
Write-Host "====================================="
Write-Host "Launching STONKS Journal..."
Write-Host "====================================="
Write-Host ""

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    & ".\venv\Scripts\Activate.ps1"

    $env:PYTHONPATH = "src"

    python -m stonks.journal.journal_cli
}
finally {
    Pop-Location
}