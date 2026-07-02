"""Savol-javob bo'limi (TZ §11.1)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards import callbacks as cb
from app.keyboards.inline import back_to_menu_kb

router = Router(name="faq")


@router.callback_query(F.data == cb.MENU_FAQ)
async def show_faq(call: CallbackQuery, texts) -> None:
    try:
        await call.message.edit_text(texts.FAQ, reply_markup=back_to_menu_kb(texts))
    except Exception:
        await call.message.answer(texts.FAQ, reply_markup=back_to_menu_kb(texts))
    await call.answer()
