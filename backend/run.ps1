# Start the local API server (loopback only) on Windows.
# Usage:  .\run.ps1
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
.\.venv\Scripts\Activate.ps1
python app.py
