"""Admin — ommaviy xabar yuborish (TZ §10.17)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards import callbacks as cb
from app.keyboards.admin import admin_back_kb, broadcast_confirm_kb
from app.services.broadcast_service import broadcast
from app.states.admin import AdminBroadcast

router = Router(name="admin_broadcast")


@router.callback_query(F.data == cb.ADMIN_BROADCAST)
async def broadcast_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer("Yubormoqchi bo‘lgan xabar matnini yuboring:")
    await state.set_state(AdminBroadcast.waiting_message)
    await call.answer()


@router.message(AdminBroadcast.waiting_message, F.text)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await message.answer(
        f"Quyidagi xabar barcha foydalanuvchilarga yuboriladi:\n\n{message.text}",
        reply_markup=broadcast_confirm_kb(),
    )
    await state.set_state(AdminBroadcast.waiting_confirm)


@router.callback_query(AdminBroadcast.waiting_confirm, F.data == cb.ADMIN_BROADCAST_CONFIRM)
async def broadcast_confirm(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    text = data.get("text", "")
    await state.clear()
    await call.message.edit_text("📣 Yuborilmoqda... Bu biroz vaqt olishi mumkin.")
    sent, failed = await broadcast(call.bot, text)
    await call.message.answer(
        f"✅ Yakunlandi.\nYuborildi: {sent}\nXato: {failed}",
        reply_markup=admin_back_kb(),
    )
    await call.answer()


@router.callback_query(AdminBroadcast.waiting_confirm, F.data == cb.ADMIN_BROADCAST_CANCEL)
async def broadcast_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.", reply_markup=admin_back_kb())
    await call.answer()
