# =============================================================================
# File: run.ps1
# Purpose: Activate the STONKS environment standalone script.
# =============================================================================

Write-Host "Activating STONKS virtual environment..."

$root = Split-Path -Parent $PSScriptRoot

Set-Location $root

& ".\venv\Scripts\Activate.ps1"

$env:PYTHONPATH = "src"

Write-Host ""
Write-Host "STONKS environment ready."
Write-Host "PYTHONPATH=src"