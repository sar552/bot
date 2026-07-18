"""Mahsulot video va ma'lumot bo'limlari (TZ §5, §6)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.config import settings
from app.keyboards import callbacks as cb
from app.keyboards.inline import after_video_kb, product_info_kb

router = Router(name="product")


@router.callback_query(F.data == cb.MENU_VIDEO)
async def show_video(call: CallbackQuery, texts) -> None:
    if settings.product_video_url:
        # YouTube havolasi — matn + "YouTube'da ko'rish" tugmasi (after_video_kb ichida)
        try:
            await call.message.edit_text(texts.VIDEO_CAPTION, reply_markup=after_video_kb(texts))
        except Exception:
            await call.message.answer(texts.VIDEO_CAPTION, reply_markup=after_video_kb(texts))
    elif settings.product_video_file_id:
        # Muqobil: Telegram videosi
        await call.message.answer_video(
            video=settings.product_video_file_id,
            caption=texts.VIDEO_CAPTION,
            reply_markup=after_video_kb(texts),
        )
    else:
        try:
            await call.message.edit_text(texts.VIDEO_MISSING, reply_markup=after_video_kb(texts))
        except Exception:
            await call.message.answer(texts.VIDEO_MISSING, reply_markup=after_video_kb(texts))
    await call.answer()


@router.callback_query(F.data == cb.MENU_INFO)
async def show_info(call: CallbackQuery, texts) -> None:
    try:
        await call.message.edit_text(texts.PRODUCT_INFO, reply_markup=product_info_kb(texts))
    except Exception:
        await call.message.answer(texts.PRODUCT_INFO, reply_markup=product_info_kb(texts))
    await call.answer()
