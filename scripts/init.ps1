# =============================================================================
# File: init.ps1
# Purpose: Initialize the STONKS environment and show next steps.
# =============================================================================

Write-Host "Initializing STONKS..."

if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
    Write-Host "Edit .env and add your STONKS_API_KEY."
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

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Run: venv\Scripts\activate"
Write-Host "2. Run: pip install -r requirements.txt"
Write-Host "3. Edit .env and add your API key"