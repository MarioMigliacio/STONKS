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

# Move to project root.
Set-Location $root

# Activate Python virtual environment.
& ".\venv\Scripts\Activate.ps1"

# Configure Python package root.
$env:PYTHONPATH = "src"

# Run the application.
python -m stonks
