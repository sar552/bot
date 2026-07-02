"""Admin inline klaviaturalari (TZ §10)."""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards import callbacks as cb


def admin_menu_kb() -> InlineKeyboardMarkup:
    # Kod va bonuslar Google Sheets orqali boshqariladi, shuning uchun ular
    # uchun tugmalar olib tashlangan. Faqat Sheets'da yo'q amallar qoldirilgan.
    b = InlineKeyboardBuilder()
    b.button(text="📊 Statistika", callback_data=cb.ADMIN_STATS)
    b.button(text="📚 Kitoblar", callback_data=cb.ADMIN_BOOKS)
    b.button(text="➕ Kitob qo‘shish", callback_data=cb.ADMIN_ADD_BOOK)
    b.button(text="📣 Ommaviy xabar", callback_data=cb.ADMIN_BROADCAST)
    b.button(text="🔄 Sheets'ni yangilash", callback_data=cb.ADMIN_SHEETS_SYNC)
    b.adjust(2)
    return b.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Admin menyu", callback_data=cb.ADMIN_MENU)
    return b.as_markup()


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Yuborish", callback_data=cb.ADMIN_BROADCAST_CONFIRM)
    b.button(text="❌ Bekor qilish", callback_data=cb.ADMIN_BROADCAST_CANCEL)
    b.adjust(2)
    return b.as_markup()
