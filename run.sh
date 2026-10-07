#!/usr/bin/env bash
set -e
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Edite .env e coloque o DISCORD_TOKEN antes de executar novamente."
  exit 1
fi
.venv/bin/python bot.py
