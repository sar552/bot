"""Foydalanuvchini yuklab, handler'ga `user` sifatida beradi.

Mavjud bo'lsa DB'dan oladi; yangi bo'lsa (registratsiyadan oldin) None bo'ladi.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User as TgUser

from app.db.repositories import UserRepo
from app.texts import get_texts


def _extract_tg_user(event: TelegramObject, data: dict[str, Any]) -> TgUser | None:
    """event_from_user bo'lmasa, Update obyektidan foydalanuvchini ajratadi."""
    tg_user = data.get("event_from_user")
    if tg_user is not None:
        return tg_user
    if isinstance(event, Update):
        for sub in (
            event.message,
            event.callback_query,
            event.edited_message,
            event.my_chat_member,
            event.chat_member,
        ):
            if sub is not None and getattr(sub, "from_user", None) is not None:
                return sub.from_user
    return None


class LoadUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = _extract_tg_user(event, data)
        session = data.get("session")
        user = None
        if tg_user is not None and session is not None:
            user = await UserRepo(session).get(tg_user.id)
        data["user"] = user
        # Foydalanuvchi tiliga mos matn modulini handlerlarga beramiz
        data["texts"] = get_texts(user.language if user else None)
        return await handler(event, data)
