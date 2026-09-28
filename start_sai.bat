@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo SAI Voice OS is not installed yet.
  echo Run: py -3.11 -m venv .venv
  echo Then: .venv\Scripts\pip install -r requirements-desktop.txt
  pause
  exit /b 1
)
".venv\Scripts\python.exe" main.py
pause
