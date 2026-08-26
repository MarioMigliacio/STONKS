# =============================================================================
# File: lint.ps1
# Purpose: Run STONKS linting and formatting checks.
# =============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $ProjectRoot

try {
    ruff check .
    ruff format --check .
}
finally {
    Pop-Location
}