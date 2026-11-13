@echo off
cd /d "%~dp0.."
if not exist .venv (
  py -m venv .venv
  .venv\Scripts\python -m pip install -r requirements-dev.txt
)
.venv\Scripts\python -m pytest -q
pause
