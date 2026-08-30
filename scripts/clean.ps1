# =============================================================================
# File: clean.ps1
# Purpose: Removes generated STONKS development artifacts.
# =============================================================================

Write-Host "====================================="
Write-Host "Cleaning STONKS..."
Write-Host "====================================="

$pathsToRemove = @(
    ".pytest_cache",
    ".ruff_cache",
    "logs"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $ProjectRoot

try {
    foreach ($path in $pathsToRemove) {
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path
            Write-Host "Removed $path"
        }
        else {
            Write-Host "Skipping $path - not found"
        }
    }

    $pythonCacheDirectories = Get-ChildItem `
        -Path "src", "tests" `
        -Directory `
        -Recurse `
        -Filter "__pycache__"

    foreach ($directory in $pythonCacheDirectories) {
        Remove-Item -Recurse -Force $directory.FullName
        Write-Host "Removed $($directory.FullName)"
    }

    Write-Host ""
    Write-Host "STONKS clean complete."
}
finally {
    Pop-Location
}