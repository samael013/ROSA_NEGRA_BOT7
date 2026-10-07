"""Configurações centralizadas do bot ROSA NEGRA."""

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GUILD_ID = os.getenv("GUILD_ID", "").strip()
PRIVACY_URL = os.getenv("PRIVACY_URL", "").strip()
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))
STATUS_URLS = [u.strip() for u in os.getenv("STATUS_URLS", "").split(",") if u.strip()]
DB_PATH = os.getenv("DB_PATH", "data/rosa_negra.sqlite3")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN não foi definido no arquivo .env")
