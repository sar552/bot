"""Noto'g'ri kod kiritish cheklovi (TZ §8.11.13)."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.repositories import RateLimitRepo, utcnow


class RateLimitService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = RateLimitRepo(session)
        self.session = session

    async def remaining_block_minutes(self, telegram_id: int) -> int:
        """Agar bloklangan bo'lsa, qolgan daqiqalarni qaytaradi; aks holda 0."""
        rl = await self.repo.get(telegram_id)
        if rl is None or rl.blocked_until is None:
            return 0
        delta = rl.blocked_until - utcnow()
        secs = delta.total_seconds()
        return max(0, int(secs // 60) + 1) if secs > 0 else 0

    async def register_failure(
        self,
        telegram_id: int,
        max_fails: int | None = None,
        block_minutes: int | None = None,
    ) -> int:
        """Bitta xato urinishni qayd qiladi. Blok boshlansa qolgan daqiqani qaytaradi.

        max_fails/block_minutes berilmasa, bonus uchun standart (.env) qiymatlar.
        Kitob oqimi o'zining qiymatlarini (10 urinish) uzatadi.
        Autobegin transaction'da ishlaydi (oldindan ochiq bo'lsa ham mos keladi).
        """
        await self.repo.register_failure(
            telegram_id,
            max_fails if max_fails is not None else settings.rate_limit_max_fails,
            block_minutes if block_minutes is not None else settings.rate_limit_block_minutes,
        )
        await self.session.commit()
        return await self.remaining_block_minutes(telegram_id)

    async def reset(self, telegram_id: int) -> None:
        await self.repo.reset(telegram_id)
        await self.session.commit()
