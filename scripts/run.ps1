# =============================================================================
# File: run.ps1
# Purpose: Activate the STONKS environment and run the application.
# =============================================================================

Write-Host ""
Write-Host "====================================="
Write-Host "Launching STONKS..."
Write-Host "====================================="
Write-Host ""

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    & ".\venv\Scripts\Activate.ps1"

    $env:PYTHONPATH = "src"

    python -m stonks
}
finally {
    Pop-Location
}