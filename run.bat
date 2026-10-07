@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  py -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)
if not exist .env (
  copy .env.example .env >nul
  echo.
  echo Edite o arquivo .env e coloque o DISCORD_TOKEN antes de executar novamente.
  pause
  exit /b 1
)
.venv\Scripts\python.exe bot.py
pause
