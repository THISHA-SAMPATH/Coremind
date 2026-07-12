# setup.ps1
# One-command setup for CoreMind on Windows.
# Usage: right-click > Run with PowerShell, or run `.\setup.ps1` in a terminal.

Write-Host "=== CoreMind Setup ===" -ForegroundColor Cyan

# 1. Python dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 2. Check Ollama is installed
Write-Host "`nChecking for Ollama..." -ForegroundColor Yellow
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "Ollama not found. Please install it from https://ollama.com/download" -ForegroundColor Red
    Write-Host "Then re-run this script." -ForegroundColor Red
    exit 1
}

# 3. Pull the model if not already present
Write-Host "`nChecking for phi3:mini model..." -ForegroundColor Yellow
$models = ollama list
if ($models -notmatch "phi3:mini") {
    Write-Host "Pulling phi3:mini (about 2.3GB, may take a few minutes)..." -ForegroundColor Yellow
    ollama pull phi3:mini
} else {
    Write-Host "phi3:mini already present." -ForegroundColor Green
}

# 4. Launch the app
Write-Host "`nSetup complete. Launching CoreMind..." -ForegroundColor Green
python -m streamlit run app.py
