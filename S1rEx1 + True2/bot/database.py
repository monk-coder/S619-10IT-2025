from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Sequence

import aiosqlite


class Database:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._conn is not None:
            return
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._create_schema()

    async def close(self) -> None:
        if self._conn is None:
            return
        await self._conn.close()
        self._conn = None

    async def _create_schema(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                prompt_template TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                template TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, name)
            );
            """
        )
        await self._conn.commit()

    async def add_note(
        self,
        *,
        user_id: int,
        title: str,
        content: str,
        source: str = "manual",
    ) -> int:
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            INSERT INTO notes (user_id, title, content, source, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, title, content, source, dt.datetime.utcnow().isoformat()),
        )
        await self._conn.commit()
        return int(cursor.lastrowid)

    async def list_notes(self, user_id: int) -> list[dict[str, Any]]:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT id, title, source, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_note(self, note_id: int, user_id: int) -> dict[str, Any] | None:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT id, title, content, source, created_at FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def delete_note(self, note_id: int, user_id: int) -> bool:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "DELETE FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def set_prompt_template(self, user_id: int, template: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO user_settings (user_id, prompt_template, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                prompt_template = excluded.prompt_template,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, template),
        )
        await self._conn.commit()

    async def get_prompt_template(self, user_id: int) -> str | None:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT prompt_template FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return str(row["prompt_template"]) if row["prompt_template"] else None

    async def list_custom_prompts(self, user_id: int) -> list[dict[str, Any]]:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT id, name, template FROM user_prompts WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def upsert_custom_prompt(self, user_id: int, name: str, template: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO user_prompts (user_id, name, template, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, name) DO UPDATE SET template = excluded.template
            """,
            (user_id, name, template),
        )
        await self._conn.commit()

    async def delete_custom_prompt(self, user_id: int, prompt_id: int) -> bool:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "DELETE FROM user_prompts WHERE user_id = ? AND id = ?",
            (user_id, prompt_id),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def get_custom_prompt(self, user_id: int, prompt_id: int) -> dict[str, Any] | None:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT id, name, template FROM user_prompts WHERE user_id = ? AND id = ?",
            (user_id, prompt_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def execute(self, query: str, parameters: Sequence[Any] | None = None) -> None:
        assert self._conn is not None
        await self._conn.execute(query, parameters or [])
        await self._conn.commit()
