# =============================================================================
# File: format.ps1
# Purpose: Automatically format STONKS Python source files.
# =============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $ProjectRoot

try {
    ruff check . --fix
    ruff format .
}
finally {
    Pop-Location
}