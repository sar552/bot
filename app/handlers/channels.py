"""Sotuv kanallari + click tracking (TZ §7)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.repositories import ChannelRepo
from app.keyboards import callbacks as cb
from app.keyboards.inline import channel_link_kb, channels_kb

router = Router(name="channels")

_CHANNEL_URLS = {
    "telegram": lambda: settings.channel_telegram_url,
    "instagram": lambda: settings.channel_instagram_url,
    "uzum": lambda: settings.channel_uzum_url,
    "other": lambda: settings.channel_other_url,
}


@router.callback_query(F.data == cb.MENU_CHANNELS)
async def show_channels(call: CallbackQuery, texts) -> None:
    try:
        await call.message.edit_text(texts.CHANNELS, reply_markup=channels_kb(texts))
    except Exception:
        await call.message.answer(texts.CHANNELS, reply_markup=channels_kb(texts))
    await call.answer()


@router.callback_query(F.data.startswith(cb.CLICK_PREFIX))
async def on_channel_click(call: CallbackQuery, session: AsyncSession, texts) -> None:
    channel = call.data.removeprefix(cb.CLICK_PREFIX)
    url_getter = _CHANNEL_URLS.get(channel)
    url = url_getter() if url_getter else None

    if not url:
        await call.answer("—", show_alert=True)
        return

    repo = ChannelRepo(session)
    await repo.log_click(call.from_user.id, channel)
    await session.commit()

    await call.message.answer(
        texts.CHANNEL_PICK,
        reply_markup=channel_link_kb(texts, url),
    )
    await call.answer()
