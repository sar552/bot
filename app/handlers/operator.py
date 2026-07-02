"""Operator bilan bog'lanish (TZ §11.4)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.config import settings
from app.keyboards import callbacks as cb
from app.keyboards.inline import operator_kb

router = Router(name="operator")


@router.callback_query(F.data == cb.MENU_OPERATOR)
async def show_operator(call: CallbackQuery, texts) -> None:
    text = texts.operator_text(settings.operator_username)
    try:
        await call.message.edit_text(text, reply_markup=operator_kb(texts))
    except Exception:
        await call.message.answer(text, reply_markup=operator_kb(texts))
    await call.answer()
