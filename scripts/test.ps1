# =============================================================================
# File: test.ps1
# Purpose: Run full, focused, or profiled STONKS pytest checks.
# =============================================================================

[CmdletBinding()]
param(
    [ValidateSet('Full', 'Quick')]
    [string]$Mode = 'Full',

    [string]$Target,

    [Alias('Path')]
    [string]$TestPath,

    [switch]$FailFast,

    [switch]$Profile
)

$root = Split-Path -Parent $PSScriptRoot

if ($Target -and $TestPath) {
    throw 'Specify either -Target or -Path, not both.'
}

Push-Location $root

try {
    $pytestArgs = @('-v', '--tb=short')

    if ($Mode -eq 'Quick') {
        # Requires the "slow" marker to be registered in pyproject.toml.
        # Until tests are marked slow, Quick runs the same tests as Full.
        $pytestArgs += @('-m', 'not slow')
    }

    if ($FailFast) {
        $pytestArgs += '-x'
    }

    if ($Profile) {
        $pytestArgs += @('--durations=20', '--durations-min=0.1')
    }

    if ($Target) {
        if ($Target -notmatch '^[A-Za-z0-9_-]+$') {
            throw 'Target must be a simple test directory name under tests/.'
        }
        $targetPath = Join-Path 'tests' $Target
        if (-not (Test-Path -LiteralPath $targetPath -PathType Container)) {
            throw "Unknown test target: $Target (expected $targetPath)."
        }
        $pytestArgs += $targetPath
    }
    elseif ($TestPath) {
        if (-not (Test-Path -LiteralPath $TestPath)) {
            throw "Test path not found: $TestPath"
        }
        $pytestArgs += $TestPath
    }

    Write-Host "Running: pytest $($pytestArgs -join ' ')"
    & pytest @pytestArgs
    $testExitCode = $LASTEXITCODE
    exit $testExitCode
}
finally {
    Pop-Location
}
