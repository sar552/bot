"""Test sozlamalari.

Postgres kerak (FOR UPDATE / SKIP LOCKED semantikasi shu yerda sinaladi).
Test bazasini TEST_DATABASE_URL orqali bering, masalan:

    export TEST_DATABASE_URL=postgresql+asyncpg://penbot:penbot@localhost:5432/penbot_test
    pytest
"""
from __future__ import annotations

import os

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://penbot:penbot@localhost:5432/penbot_test",
)


@pytest_asyncio.fixture
async def engine():
    """Function-scoped — har bir test o'zining event loop'ida toza sxema oladi.

    pytest-asyncio per-test loop yaratadi; engine pool ham shu loop'ga bog'lanadi.
    """
    eng = create_async_engine(TEST_DB_URL, pool_pre_ping=True)
    async with eng.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS audit_log, channel_clicks, "
                                "rate_limits, bonuses, codes, users CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS bonus_status, code_status CASCADE"))
        await conn.execute(text(
            "CREATE TYPE code_status AS ENUM ('unused','used','blocked')"
        ))
        await conn.execute(text(
            "CREATE TYPE bonus_status AS ENUM "
            "('unused','assigned','used','expired','blocked')"
        ))
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def clean_tables(engine):
    # engine fixture har test uchun sxemani qaytadan yaratadi — toza holat kafolatlangan
    yield
