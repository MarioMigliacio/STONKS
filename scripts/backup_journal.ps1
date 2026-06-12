# =============================================================================
# File: backup_journal.ps1
# Purpose: Create a backup of STONKS journal data.
# =============================================================================

$root = Split-Path -Parent $PSScriptRoot

Push-Location $root

try {
    & ".\venv\Scripts\Activate.ps1"

    $env:PYTHONPATH = "src"

    python -m stonks.journal.journal_backup
}
finally {
    Pop-Location
}