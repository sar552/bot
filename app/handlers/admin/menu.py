"""Admin menyu va statistika."""
from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import BonusRepo, CodeRepo, UserRepo
from app.keyboards import callbacks as cb
from app.keyboards.admin import admin_back_kb, admin_menu_kb
from app.config import settings
from app.services.excel_service import build_export
from app.services.sheets_service import sheets_service
from app.texts import uz

router = Router(name="admin_menu")


@router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(uz.ADMIN_MENU, reply_markup=admin_menu_kb())


@router.callback_query(F.data == cb.ADMIN_MENU)
async def admin_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await call.message.edit_text(uz.ADMIN_MENU, reply_markup=admin_menu_kb())
    except Exception:
        await call.message.answer(uz.ADMIN_MENU, reply_markup=admin_menu_kb())
    await call.answer()


@router.callback_query(F.data == cb.ADMIN_STATS)
async def admin_stats(call: CallbackQuery, session: AsyncSession) -> None:
    users = await UserRepo(session).count()
    codes = await CodeRepo(session).count_by_status()
    bonuses = await BonusRepo(session).count_by_status()

    text = (
        "📊 Statistika\n\n"
        f"👥 Foydalanuvchilar: {users}\n\n"
        "🔑 Kodlar:\n"
        f"  • unused: {codes.get('unused', 0)}\n"
        f"  • used: {codes.get('used', 0)}\n"
        f"  • blocked: {codes.get('blocked', 0)}\n\n"
        "🎁 Bonuslar:\n"
        f"  • unused: {bonuses.get('unused', 0)}\n"
        f"  • assigned: {bonuses.get('assigned', 0)}\n"
        f"  • used: {bonuses.get('used', 0)}\n"
        f"  • expired: {bonuses.get('expired', 0)}\n"
        f"  • blocked: {bonuses.get('blocked', 0)}"
    )
    try:
        await call.message.edit_text(text, reply_markup=admin_back_kb())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_kb())
    await call.answer()


@router.callback_query(F.data == cb.ADMIN_EXPORT)
async def admin_export(call: CallbackQuery) -> None:
    """Joriy holatni Excel (.xlsx) fayl sifatida yuboradi."""
    await call.answer("Excel fayl tayyorlanmoqda...")
    try:
        data = await build_export()
    except Exception as e:  # pragma: no cover
        logger.exception(f"Excel eksport xatosi: {e}")
        await call.message.answer(
            "❌ Eksport vaqtida xatolik yuz berdi.", reply_markup=admin_back_kb()
        )
        return

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    file = BufferedInputFile(data, filename=f"penbot_export_{stamp}.xlsx")
    await call.message.answer_document(
        file,
        caption=f"📥 Joriy holat — {stamp}\nVaraqlar: Hisobot, Users, Codes, Bonuses",
        reply_markup=admin_back_kb(),
    )


@router.callback_query(F.data == cb.ADMIN_SHEETS_SYNC)
async def admin_sheets_sync(call: CallbackQuery) -> None:
    """Google Sheets bilan qo'lda sinxron (import + eksport)."""
    if not settings.sheets_enabled:
        await call.answer(
            "Google Sheets sozlanmagan (.env da credentials yo'q).", show_alert=True
        )
        return
    await call.answer("Sheets bilan sinxronlanmoqda...")
    try:
        added_codes, added_bonuses = await sheets_service.import_new()
        await sheets_service.export_all()
    except Exception as e:  # pragma: no cover
        logger.exception(f"Sheets sync xatosi: {e}")
        await call.message.answer(
            "❌ Sheets sinxronida xatolik. Loglarni tekshiring.",
            reply_markup=admin_back_kb(),
        )
        return
    await call.message.answer(
        f"✅ Sheets yangilandi.\nSheets'dan qo'shildi: {added_codes} kod, "
        f"{added_bonuses} bonus.",
        reply_markup=admin_back_kb(),
    )
