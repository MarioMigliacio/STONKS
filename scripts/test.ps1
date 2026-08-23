# =============================================================================
# File: test.ps1
# Purpose: Run the STONKS automated test suite.
# =============================================================================

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    pytest -v
}
finally {
    Pop-Location
}