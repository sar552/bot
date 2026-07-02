"""Asosiy menyu navigatsiyasi (TZ §4)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.keyboards import callbacks as cb
from app.keyboards.inline import main_menu_kb

router = Router(name="menu")


@router.callback_query(F.data == cb.MENU_MAIN)
async def back_to_main(call: CallbackQuery, state: FSMContext, texts) -> None:
    await state.clear()
    try:
        await call.message.edit_text(texts.MAIN_MENU, reply_markup=main_menu_kb(texts))
    except Exception:
        await call.message.answer(texts.MAIN_MENU, reply_markup=main_menu_kb(texts))
    await call.answer()
