"""Admin moduli (TZ §10). Barcha handlerlar IsAdmin filtri bilan himoyalangan."""
from __future__ import annotations

from aiogram import Router

from app.handlers.admin import bonuses, books, broadcast, codes, menu, tools, users
from app.middlewares.admin import IsAdmin

router = Router(name="admin")

# Faqat adminlar — message va callback ikkalasiga
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

router.include_router(menu.router)
router.include_router(users.router)
router.include_router(codes.router)
router.include_router(bonuses.router)
router.include_router(broadcast.router)
router.include_router(books.router)
router.include_router(tools.router)
