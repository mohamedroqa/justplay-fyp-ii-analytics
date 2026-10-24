param(
    [switch]$RebuildProcessed
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Invoke-Step {
    param([string]$Name, [string]$Script)
    Write-Host "`n[$Name]" -ForegroundColor Cyan
    python $Script
    if ($LASTEXITCODE -ne 0) {
        throw "Pipeline step failed: $Name"
    }
}

Invoke-Step "1/6 Raw data audit" "src\pipeline\audit_data.py"
Invoke-Step "2/6 Experiment scope audit" "src\pipeline\audit_experiment_scope.py"

if ($RebuildProcessed) {
    Invoke-Step "3/6 Processed layer rebuild" "src\pipeline\build_processed_data.py"
} elseif (-not (Test-Path "data\processed\user_features.parquet")) {
    throw "Processed layer is missing. Run this script with -RebuildProcessed."
} else {
    Write-Host "`n[3/6 Processed layer] Existing verified files reused" -ForegroundColor Yellow
}

Invoke-Step "4/6 Data Mart build" "src\analytics\build_data_marts.py"
Invoke-Step "5/6 Duplicate and outlier analysis" "src\pipeline\audit_duplicates_outliers.py"
Invoke-Step "6/6 Statistical analysis" "src\analytics\run_statistical_analysis.py"

Write-Host "`nRunning final quality suite..." -ForegroundColor Cyan
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_quality_checks.ps1
if ($LASTEXITCODE -ne 0) {
    throw "Final quality suite failed."
}

Write-Host "`nPIPELINE COMPLETED: outputs are ready for the dashboard." -ForegroundColor Green
