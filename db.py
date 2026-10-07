"""Camada SQLite do ROSA NEGRA.

O banco guarda somente dados que o próprio usuário cadastrou voluntariamente.
Não existe tabela de pessoas externas nem mecanismo de busca por terceiros.
"""

import aiosqlite
from config import DB_PATH


async def init_db() -> None:
    """Cria as tabelas necessárias."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                nome TEXT,
                email TEXT,
                observacao TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_user(discord_id: int, nome: str, email: str, observacao: str) -> None:
    """Insere ou atualiza o cadastro voluntário do próprio usuário."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (discord_id, nome, email, observacao)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET
                nome=excluded.nome,
                email=excluded.email,
                observacao=excluded.observacao,
                updated_at=CURRENT_TIMESTAMP
        """, (discord_id, nome, email, observacao))
        await db.commit()


async def get_user(discord_id: int):
    """Retorna apenas o cadastro pertencente ao Discord ID informado."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        return await cur.fetchone()


async def delete_user(discord_id: int) -> bool:
    """Exclui o cadastro voluntário do próprio usuário."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))
        await db.commit()
        return cur.rowcount > 0
