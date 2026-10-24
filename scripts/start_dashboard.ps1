$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path "data\marts\overall_kpis.parquet")) {
    throw "Dashboard Data Marts are missing. Build the analysis outputs first."
}

python -c "import streamlit, pandas, pyarrow" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Required Python packages are missing. Run: python -m pip install -r requirements.txt"
}

Write-Host "Starting JustPlay Analytics at http://localhost:8501" -ForegroundColor Cyan
python -m streamlit run app\streamlit_app.py --server.port 8501
