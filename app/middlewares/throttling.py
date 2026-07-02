"""Oddiy flood himoyasi — bir foydalanuvchidan juda tez kelgan update'larni cheklaydi."""
from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.4) -> None:
        self.rate_limit = rate_limit
        self._last: dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is not None:
            now = time.monotonic()
            if now - self._last[tg_user.id] < self.rate_limit:
                return None  # juda tez — tashlab yuboramiz
            self._last[tg_user.id] = now
        return await handler(event, data)
