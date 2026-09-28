$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python Launcher 'py' was not found. Install Python 3.11 or 3.12 first." }
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements-desktop.txt
Write-Host ""
Write-Host "SAI Voice OS installation complete."
Write-Host "Start with: .\start_sai.bat"
