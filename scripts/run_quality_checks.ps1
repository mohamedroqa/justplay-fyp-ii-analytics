$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

python -m pytest -q -p no:cacheprovider
python tests\run_processed_checks.py
python tests\run_data_mart_checks.py
python tests\run_cleaning_final_checks.py
python tests\run_statistical_checks.py
python tests\run_dashboard_download_checks.py
python tests\benchmark_dashboard.py

Write-Host "ALL PROJECT QUALITY CHECKS PASSED" -ForegroundColor Green
