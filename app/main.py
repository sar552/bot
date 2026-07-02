"""Bot entrypoint — dispatcher, middleware'lar, routerlar va scheduler."""
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from loguru import logger
from redis.asyncio import Redis

from app.config import settings
from app.db.seed import seed_example_books
from app.handlers import build_router
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.user import LoadUserMiddleware
from app.scheduler import setup_scheduler
from app.utils.logging import setup_logging


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Boshlash / Asosiy menyu"),
        ]
    )


def build_dispatcher() -> Dispatcher:
    # FSM holatini Redis'da saqlaymiz — restart'da yo'qolmaydi (TZ §17.27)
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    # Middleware tartibi muhim: throttling → db → user
    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(LoadUserMiddleware())

    dp.include_router(build_router())
    return dp


async def main() -> None:
    setup_logging()
    logger.info("Bot ishga tushmoqda...")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    scheduler = setup_scheduler()
    scheduler.start()

    await seed_example_books()
    await set_commands(bot)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("Bot to'xtatildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot qo'lda to'xtatildi")
