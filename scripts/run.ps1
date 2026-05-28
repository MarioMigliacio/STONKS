# =============================================================================
# File: run.ps1
# Purpose: Activate the STONKS environment and run the application.
# =============================================================================

Write-Host ""
Write-Host "====================================="
Write-Host "Launching STONKS..."
Write-Host "====================================="
Write-Host ""

# Resolve project root from script location.
$root = Split-Path -Parent $PSScriptRoot

# Preserve caller directory.
Push-Location $root

try {
    # Activate Python virtual environment.
    & ".\venv\Scripts\Activate.ps1"

    # Configure Python package root.
    $env:PYTHONPATH = "src"

    # Run the application.
    python -m stonks
}
finally {
    # Restore original caller directory.
    Pop-Location
}