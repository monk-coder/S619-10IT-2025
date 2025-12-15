from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

import database as db_module

if TYPE_CHECKING:
    from database import DatabaseManager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_module.AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def db_session(db_manager_class: type) -> AsyncIterator[Tuple[AsyncSession, 'DatabaseManager']]:
    if db_module.AsyncSessionLocal is None:
        await db_module.init_database()

    async with db_module.AsyncSessionLocal() as session:
        db = db_manager_class(session)
        yield session, db
