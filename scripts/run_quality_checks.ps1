$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Assert-LastCommandSucceeded {
    param([Parameter(Mandatory = $true)][string]$Step)

    if ($LASTEXITCODE -ne 0) {
        throw ($Step + ' failed with exit code ' + $LASTEXITCODE + '.')
    }
}

python -m pytest tests -q -p no:cacheprovider
Assert-LastCommandSucceeded 'Pytest suite'
python tests\run_processed_checks.py
Assert-LastCommandSucceeded 'Processed-data checks'
python tests\run_data_mart_checks.py
Assert-LastCommandSucceeded 'Data Mart checks'
python tests\run_cleaning_final_checks.py
Assert-LastCommandSucceeded 'Final cleaning checks'
python tests\run_statistical_checks.py
Assert-LastCommandSucceeded 'Statistical checks'
python tests\run_dashboard_download_checks.py
Assert-LastCommandSucceeded 'Dashboard download checks'
python tests\benchmark_dashboard.py
Assert-LastCommandSucceeded 'Dashboard performance checks'

Write-Host "ALL PROJECT QUALITY CHECKS PASSED" -ForegroundColor Green
