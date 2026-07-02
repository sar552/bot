"""Reply klaviaturalar (kontakt yuborish)."""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def phone_request_kb(t) -> ReplyKeyboardMarkup:
    """Telegram “Kontaktni yuborish” tugmasi (TZ §3.3)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t.B_SEND_PHONE, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
