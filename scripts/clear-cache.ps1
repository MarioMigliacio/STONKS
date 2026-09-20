# =============================================================================
# File: clear-cache.ps1
# Purpose: Removes cached JSON data while preserving cache directories.
# =============================================================================

$cacheDirectory = "data/cache"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $ProjectRoot

try {
    if (-not (Test-Path $cacheDirectory)) {
        Write-Host "Cache directory does not exist."
        exit 0
    }

    $cacheFiles = Get-ChildItem `
        -Path $cacheDirectory `
        -Filter "*.json" `
        -File `
        -Recurse

    if (-not $cacheFiles) {
        Write-Host "No cached JSON files found."
        exit 0
    }

    $fileCount = $cacheFiles.Count

    $cacheFiles | Remove-Item

    Write-Host "Removed $fileCount cached JSON file(s)."
    Write-Host "Cache directories preserved."
}
finally {
    Pop-Location
}