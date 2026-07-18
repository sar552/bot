"""Inline klaviaturalar (TZ §12). Har bir funksiya `t` (til moduli) qabul qiladi."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings
from app.keyboards import callbacks as cb
from app.texts import B_LANG_RU, B_LANG_UZ


def lang_kb() -> InlineKeyboardMarkup:
    """Til tanlash (ikki tilli — tildan mustaqil)."""
    b = InlineKeyboardBuilder()
    b.button(text=B_LANG_UZ, callback_data=cb.LANG_UZ)
    b.button(text=B_LANG_RU, callback_data=cb.LANG_RU)
    b.adjust(2)
    return b.as_markup()


def main_menu_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_VIDEO, callback_data=cb.MENU_VIDEO)
    b.button(text=t.B_INFO, callback_data=cb.MENU_INFO)
    b.button(text=t.B_BOOKS, callback_data=cb.MENU_BOOKS)
    b.button(text=t.B_CHANNELS, callback_data=cb.MENU_CHANNELS)
    b.button(text=t.B_BONUS, callback_data=cb.MENU_BONUS)
    b.button(text=t.B_FAQ, callback_data=cb.MENU_FAQ)
    b.button(text=t.B_OPERATOR, callback_data=cb.MENU_OPERATOR)
    b.button(text=t.B_LANG, callback_data=cb.MENU_LANG)
    b.adjust(1)
    return b.as_markup()


def _operator_button(t) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t.B_OPERATOR, url=settings.operator_link)


def _main_menu_button(t) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)


def channels_kb(t) -> InlineKeyboardMarkup:
    """Sotuv kanallari — har biri alohida link, bosilishi log qilinadi (TZ §7)."""
    b = InlineKeyboardBuilder()
    if settings.channel_telegram_url:
        b.button(text=t.B_CH_TELEGRAM, callback_data=f"{cb.CLICK_PREFIX}telegram")
    if settings.channel_instagram_url:
        b.button(text=t.B_CH_INSTAGRAM, callback_data=f"{cb.CLICK_PREFIX}instagram")
    if settings.channel_uzum_url:
        b.button(text=t.B_CH_UZUM, callback_data=f"{cb.CLICK_PREFIX}uzum")
    if settings.channel_other_url:
        b.button(text=t.B_CH_OTHER, callback_data=f"{cb.CLICK_PREFIX}other")
    b.button(text=t.B_OPERATOR, callback_data=cb.MENU_OPERATOR)
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def channel_link_kb(t, url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_GO_CHANNEL, url=url)
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def after_video_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # YouTube havolasi bo'lsa — eng tepada ko'rish tugmasi
    if settings.product_video_url:
        b.button(text=t.B_WATCH_YOUTUBE, url=settings.product_video_url)
    b.button(text=t.B_BUY, callback_data=cb.MENU_CHANNELS)
    b.button(text=t.B_BONUS, callback_data=cb.MENU_BONUS)
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def product_info_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_WATCH_VIDEO, callback_data=cb.MENU_VIDEO)
    b.button(text=t.B_BUY, callback_data=cb.MENU_CHANNELS)
    b.button(text=t.B_BONUS, callback_data=cb.MENU_BONUS)
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def books_list_kb(t, books) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for book in books:
        b.button(text=f"📖 {book.title}", callback_data=f"{cb.BOOK_PREFIX}{book.id}")
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def book_retry_kb(t, book_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_RETRY_CODE, callback_data=f"{cb.BOOK_PREFIX}{book_id}")
    b.button(text=t.B_BOOKS_LIST, callback_data=cb.MENU_BOOKS)
    b.row(_operator_button(t))
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def after_book_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_OTHER_BOOKS, callback_data=cb.MENU_BOOKS)
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def bonus_intro_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_ENTER_CODE, callback_data=cb.BONUS_ENTER_CODE)
    b.button(text=t.B_OPERATOR, callback_data=cb.MENU_OPERATOR)
    b.button(text=t.B_MAIN_MENU, callback_data=cb.MENU_MAIN)
    b.adjust(1)
    return b.as_markup()


def bonus_success_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_USE_BONUS, callback_data=cb.BONUS_USE)
    b.button(text=t.B_SALES_CHANNELS, callback_data=cb.MENU_CHANNELS)
    b.row(_operator_button(t))
    b.row(_main_menu_button(t))
    b.adjust(1)
    return b.as_markup()


def code_retry_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.B_RETRY_CODE, callback_data=cb.BONUS_ENTER_CODE)
    b.row(_operator_button(t))
    b.row(_main_menu_button(t))
    b.adjust(1)
    return b.as_markup()


def operator_only_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_operator_button(t))
    b.button(text=t.B_SALES_CHANNELS, callback_data=cb.MENU_CHANNELS)
    b.row(_main_menu_button(t))
    b.adjust(1)
    return b.as_markup()


def operator_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=t.B_OPERATOR_WRITE, url=settings.operator_link))
    b.row(_main_menu_button(t))
    return b.as_markup()


def back_to_menu_kb(t) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_main_menu_button(t))
    return b.as_markup()
