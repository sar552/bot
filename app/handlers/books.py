"""Kitoblar bo'limi — ro'yxat → ruchka kodi → .tnb fayl.

Kod faqat TEKSHIRILADI (used qilinmaydi). Har kitob uchun kod qayta so'raladi.
"""
from __future__ import annotations

import os

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import User
from app.db.repositories import BookRepo, CodeRepo
from app.keyboards import callbacks as cb
from app.keyboards.inline import (
    after_book_kb,
    back_to_menu_kb,
    book_retry_kb,
    books_list_kb,
)
from app.services.rate_limit_service import RateLimitService
from app.states.user import BookFlow
from app.utils.validators import normalize_code

router = Router(name="books")


@router.callback_query(F.data == cb.MENU_BOOKS)
async def show_books(call: CallbackQuery, state: FSMContext, session: AsyncSession, texts) -> None:
    await state.clear()
    books = await BookRepo(session).list_active()
    if not books:
        try:
            await call.message.edit_text(texts.BOOKS_EMPTY, reply_markup=back_to_menu_kb(texts))
        except Exception:
            await call.message.answer(texts.BOOKS_EMPTY, reply_markup=back_to_menu_kb(texts))
        await call.answer()
        return
    try:
        await call.message.edit_text(texts.BOOKS_INTRO, reply_markup=books_list_kb(texts, books))
    except Exception:
        await call.message.answer(texts.BOOKS_INTRO, reply_markup=books_list_kb(texts, books))
    await call.answer()


@router.callback_query(F.data.startswith(cb.BOOK_PREFIX))
async def choose_book(call: CallbackQuery, state: FSMContext, session: AsyncSession, texts) -> None:
    book_id = int(call.data.removeprefix(cb.BOOK_PREFIX))
    book = await BookRepo(session).get(book_id)
    if book is None or not book.is_active:
        await call.answer(texts.BOOK_NOT_FOUND, show_alert=True)
        return
    await state.set_state(BookFlow.waiting_code)
    await state.update_data(book_id=book_id, book_title=book.title)
    await call.message.answer(texts.book_ask_code(book.title))
    await call.answer()


@router.message(BookFlow.waiting_code, F.text)
async def on_book_code(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    texts,
) -> None:
    if user is None or not user.full_name or not user.phone:
        await message.answer(texts.NEED_REGISTER)
        await state.clear()
        return

    tg_id = user.telegram_id
    data = await state.get_data()
    book_id = data.get("book_id")
    if book_id is None:
        await state.clear()
        return

    rl = RateLimitService(session)
    blocked = await rl.remaining_block_minutes(tg_id)
    if blocked > 0:
        await message.answer(texts.rate_limited(blocked), reply_markup=book_retry_kb(texts, book_id))
        return

    code_str = normalize_code(message.text or "")
    valid = False
    if code_str is not None:
        valid = await CodeRepo(session).is_valid_for_books(code_str)

    if not valid:
        minutes = await rl.register_failure(
            tg_id, settings.book_code_max_fails, settings.book_block_minutes
        )
        if minutes > 0:
            await message.answer(texts.rate_limited(minutes), reply_markup=book_retry_kb(texts, book_id))
        else:
            await message.answer(texts.BOOK_CODE_INVALID, reply_markup=book_retry_kb(texts, book_id))
        return

    # Kod to'g'ri — kitobni yuboramiz
    await rl.reset(tg_id)
    book = await BookRepo(session).get(book_id)
    if book is None:
        await message.answer(texts.BOOK_NOT_FOUND, reply_markup=back_to_menu_kb(texts))
        await state.clear()
        return

    path = os.path.join(settings.books_dir, book.filename)
    if not os.path.exists(path):
        logger.error(f"Kitob fayli yo'q: {path}")
        await message.answer(texts.BOOK_FILE_MISSING, reply_markup=back_to_menu_kb(texts))
        await state.clear()
        return

    await message.answer(texts.book_sending(book.title))
    document = FSInputFile(path, filename=book.filename)
    await message.answer_document(
        document,
        caption=f"📖 {book.title}",
        reply_markup=after_book_kb(texts),
    )
    await state.clear()
