# One-time setup on Windows: create an isolated venv and install backend deps.
# Run from PowerShell in the backend folder:  .\setup.ps1
# If script execution is blocked, first run:  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Prefer the Windows Python launcher (py); fall back to python.
$py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }

& $py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "Backend deps installed. Next steps (Windows):" -ForegroundColor Green
Write-Host "  1. Install Ollama:  download from https://ollama.com/download (OllamaSetup.exe) or: winget install Ollama.Ollama"
Write-Host "  2. Ollama runs automatically in the background at http://127.0.0.1:11434"
Write-Host "  3. Pull a small model:   ollama pull llama3.2:3b"
Write-Host "  4. Run the API:          .\run.ps1"
