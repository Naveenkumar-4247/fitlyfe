Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[FitLyfe] Creating virtual environment..."
    python -m venv .venv
}

& ".venv\Scripts\Activate.ps1"

Write-Host "[FitLyfe] Installing/updating dependencies..."
python -m pip install -r requirements.txt

Write-Host ""
Write-Host "[FitLyfe] Starting server..."
Write-Host "Open http://127.0.0.1:5000"
Write-Host "Press CTRL+C to stop."
Write-Host ""

python app.py
