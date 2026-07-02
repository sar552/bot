"""Ommaviy xabar yuborish (TZ §10.17). Telegram limitlariga rioya — sekin oqim."""
from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from loguru import logger

from app.db.repositories import UserRepo
from app.db.session import session_factory


async def broadcast(bot: Bot, text: str) -> tuple[int, int]:
    """Barcha foydalanuvchilarga xabar yuboradi.

    Qaytaradi: (muvaffaqiyatli, muvaffaqiyatsiz) sonlari.
    """
    async with session_factory() as session:
        ids = await UserRepo(session).all_telegram_ids()

    sent, failed = 0, 0
    for tg_id in ids:
        try:
            await bot.send_message(tg_id, text)
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(tg_id, text)
                sent += 1
            except Exception:
                failed += 1
        except TelegramForbiddenError:
            failed += 1  # user botni bloklagan
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast xato {tg_id}: {e}")
        await asyncio.sleep(0.05)  # ~20 msg/sek — Telegram limiti ostida

    logger.info(f"Broadcast yakunlandi: {sent} yuborildi, {failed} xato")
    return sent, failed
