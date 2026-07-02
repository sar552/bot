"""Boshlang'ich ma'lumotlar — bot ishga tushganda bir marta (idempotent)."""
from __future__ import annotations

import os

from loguru import logger

from app.config import settings
from app.db.repositories import BookRepo
from app.db.session import session_factory

# (fayl nomi, ko'rinadigan nom) — books/ papkasida mavjud bo'lsa qo'shiladi
_EXAMPLE_BOOKS = [
    ("example1.tnb", "Namuna kitob 1"),
    ("example2.tnb", "Namuna kitob 2"),
]


async def seed_example_books() -> None:
    """Books jadvali bo'sh bo'lsa va example fayllar mavjud bo'lsa — qo'shadi.

    Faqat SEED_EXAMPLE_BOOKS=true bo'lsa ishlaydi (production'da o'chiq).
    """
    if not settings.seed_example_books:
        return
    async with session_factory() as session:
        repo = BookRepo(session)
        if await repo.count() > 0:
            return  # allaqachon kitoblar bor — tegmaymiz
        added = 0
        for filename, title in _EXAMPLE_BOOKS:
            if os.path.exists(os.path.join(settings.books_dir, filename)):
                await repo.add(title, filename)
                added += 1
        if added:
            await session.commit()
            logger.info(f"{added} ta namuna kitob qo'shildi (seed)")
