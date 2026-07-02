"""Barcha routerlarni bitta joyda yig'ish."""
from __future__ import annotations

from aiogram import Router

from app.handlers import (
    bonus,
    books,
    channels,
    faq,
    menu,
    operator,
    product,
    registration,
    start,
)
from app.handlers.admin import router as admin_router


def build_router() -> Router:
    root = Router()
    # Admin birinchi — admin filtri orqali ajraladi
    root.include_router(admin_router)
    root.include_router(start.router)
    root.include_router(registration.router)
    root.include_router(menu.router)
    root.include_router(product.router)
    root.include_router(channels.router)
    root.include_router(bonus.router)
    root.include_router(books.router)
    root.include_router(faq.router)
    root.include_router(operator.router)
    return root
