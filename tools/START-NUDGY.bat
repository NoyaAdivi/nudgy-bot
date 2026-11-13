@echo off
chcp 65001 >nul
cd /d "%~dp0.."
if not exist .env (
  copy .env.example .env >nul
  echo Created .env - open it, paste your token from @BotFather, then run this again.
  notepad .env
  pause
  exit /b
)
if not exist .venv (
  echo First run: installing...
  py -m venv .venv
  .venv\Scripts\python -m pip install -r requirements-dev.txt
)
.venv\Scripts\python -m nudgy
pause
