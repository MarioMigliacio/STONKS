# =============================================================================
# File: validation_report_journal.ps1
# Purpose: Launch the STONKS journal_validation_report.
# =============================================================================

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    & ".\venv\Scripts\Activate.ps1"

    $env:PYTHONPATH = "src"

    python -m stonks.journal.journal_validation_report
}
finally {
    Pop-Location
}