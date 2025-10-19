"""Database session utilities."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Tuple, Type

from sqlalchemy.ext.asyncio import AsyncSession

import database as db_module

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from database import DatabaseManager


@asynccontextmanager
async def db_session(
    db_manager_class: Type["DatabaseManager"] = db_module.DatabaseManager,
) -> AsyncIterator[Tuple[AsyncSession, "DatabaseManager"]]:
    if db_module.AsyncSessionLocal is None:
        await db_module.init_database()

    assert db_module.AsyncSessionLocal is not None  # for type checkers

    async with db_module.AsyncSessionLocal() as session:
        yield session, db_manager_class(session)
