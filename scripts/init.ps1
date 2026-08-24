# =============================================================================
# File: init.ps1
# Purpose: Initialize the STONKS environment and show next steps.
# =============================================================================

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    Write-Host "Initializing STONKS..."

    if (!(Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example"
    }
    else {
        Write-Host ".env already exists. Skipping."
    }

    if (!(Test-Path "venv")) {
        python -m venv venv
        Write-Host "Created virtual environment."
    }
    else {
        Write-Host "venv already exists. Skipping."
    }

    Write-Host "Installing project dependencies..."

    & ".\venv\Scripts\python.exe" -m pip install -r requirements.txt

    Write-Host "Dependencies installed."

    Write-Host ""
    Write-Host "STONKS initialization complete."
    Write-Host ""
    Write-Host "Run venv\Scripts\activate to begin development."
    Write-Host "Add your STONKS_API_KEY to .env if it has not been configured."
}
finally {
    Pop-Location
}