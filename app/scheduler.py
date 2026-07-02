"""Fon vazifalar: bonus muddati tekshiruvi va Sheets eksporti (TZ §8.10, §10)."""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.config import settings
from app.db.repositories import BonusRepo
from app.db.session import session_factory
from app.services.sheets_service import sheets_service


async def expire_bonuses_job() -> None:
    """Muddati o'tgan assigned bonuslarni expired qiladi."""
    async with session_factory() as session:
        async with session.begin():
            n = await BonusRepo(session).expire_overdue()
    if n:
        logger.info(f"{n} ta bonus expired holatiga o'tkazildi")


async def sheets_sync_job() -> None:
    # Avval Sheets'dagi yangi kod/bonuslarni import, keyin DB holatini eksport
    await sheets_service.sync()


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    # Har kuni 03:00 da muddati o'tgan bonuslarni tekshirish
    scheduler.add_job(expire_bonuses_job, "cron", hour=3, minute=0, id="expire_bonuses")

    if settings.sheets_enabled:
        scheduler.add_job(
            sheets_sync_job,
            "interval",
            minutes=settings.sheets_sync_interval_min,
            id="sheets_sync",
        )
        logger.info("Sheets ikki tomonlama sync jadvali yoqildi")

    return scheduler
