"""Admin — kitoblarni ko'rish va qo'shish (.tnb fayllar)."""
from __future__ import annotations

import os
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.repositories import BookRepo, write_audit
from app.keyboards import callbacks as cb
from app.keyboards.admin import admin_back_kb
from app.states.admin import AdminAddBook

router = Router(name="admin_books")


def _books_admin_kb(books):
    """Har bir kitob yonida o'chirish tugmasi."""
    b = InlineKeyboardBuilder()
    for bk in books:
        mark = "🟢" if bk.is_active else "⚪️"
        b.button(text=f"{mark} {bk.title}", callback_data="noop")
        b.button(text="🗑 O‘chirish", callback_data=f"{cb.ADMIN_BOOK_DEL_PREFIX}{bk.id}")
    b.button(text="⬅️ Admin menyu", callback_data=cb.ADMIN_MENU)
    b.adjust(2)
    return b.as_markup()

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(name: str) -> str:
    base = os.path.basename(name or "").strip()
    base = _SAFE.sub("_", base)
    if not base:
        base = "book.tnb"
    if not base.lower().endswith(".tnb"):
        base += ".tnb"
    return base


@router.callback_query(F.data == cb.ADMIN_BOOKS)
async def list_books(call: CallbackQuery, session: AsyncSession) -> None:
    books = await BookRepo(session).list_all()
    if not books:
        text = "📚 Kitoblar yo‘q. «➕ Kitob qo‘shish» orqali qo‘shing."
        markup = admin_back_kb()
    else:
        text = "📚 Kitoblar. O‘chirish uchun kitob yonidagi 🗑 tugmasini bosing:"
        markup = _books_admin_kb(books)
    try:
        await call.message.edit_text(text, reply_markup=markup)
    except Exception:
        await call.message.answer(text, reply_markup=markup)
    await call.answer()


@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery) -> None:
    await call.answer()


@router.callback_query(F.data.startswith(cb.ADMIN_BOOK_DEL_PREFIX))
async def delete_book(call: CallbackQuery, session: AsyncSession) -> None:
    book_id = int(call.data.removeprefix(cb.ADMIN_BOOK_DEL_PREFIX))
    repo = BookRepo(session)
    filename = await repo.delete(book_id)
    if filename is None:
        await call.answer("Kitob topilmadi.", show_alert=True)
        return
    await write_audit(
        session, actor_id=call.from_user.id, action="book_deleted",
        entity="book", entity_id=book_id, details=filename,
    )
    await session.commit()

    # Faylni ham o'chiramiz (best-effort — boshqa kitob ishlatmayotgan bo'lsa)
    still_used = any(b.filename == filename for b in await repo.list_all())
    if not still_used:
        path = os.path.join(settings.books_dir, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as e:  # pragma: no cover
            logger.warning(f"Kitob faylini o'chirishda xato: {e}")

    await call.answer("✅ O‘chirildi")
    # Ro'yxatni yangilaymiz
    books = await repo.list_all()
    if not books:
        text = "📚 Kitoblar yo‘q. «➕ Kitob qo‘shish» orqali qo‘shing."
        markup = admin_back_kb()
    else:
        text = "📚 Kitoblar. O‘chirish uchun kitob yonidagi 🗑 tugmasini bosing:"
        markup = _books_admin_kb(books)
    try:
        await call.message.edit_text(text, reply_markup=markup)
    except Exception:
        await call.message.answer(text, reply_markup=markup)


@router.callback_query(F.data == cb.ADMIN_ADD_BOOK)
async def add_book_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer(
        "📥 Kitob faylini (.tnb yoki boshqa hujjat) shu yerga yuboring."
    )
    await state.set_state(AdminAddBook.waiting_file)
    await call.answer()


@router.message(AdminAddBook.waiting_file, F.document)
async def add_book_file(message: Message, state: FSMContext) -> None:
    doc = message.document
    filename = _safe_filename(doc.file_name or f"book_{doc.file_unique_id}.tnb")
    os.makedirs(settings.books_dir, exist_ok=True)
    dest = os.path.join(settings.books_dir, filename)

    # Dublikat nomdan saqlanish
    if os.path.exists(dest):
        stem, ext = os.path.splitext(filename)
        filename = f"{stem}_{doc.file_unique_id}{ext}"
        dest = os.path.join(settings.books_dir, filename)

    try:
        await message.bot.download(doc, destination=dest)
    except Exception as e:  # pragma: no cover
        logger.exception(f"Kitob faylini yuklab olishda xato: {e}")
        await message.answer("❌ Faylni saqlashda xatolik. Qayta urinib ko‘ring.")
        return

    await state.update_data(filename=filename)
    await state.set_state(AdminAddBook.waiting_title)
    await message.answer(
        f"✅ Fayl saqlandi: <code>{filename}</code>\n\n"
        "Endi kitob nomini yuboring (foydalanuvchilarga shu nom ko‘rinadi):"
    )


@router.message(AdminAddBook.waiting_file)
async def add_book_not_file(message: Message) -> None:
    await message.answer("Iltimos, kitob faylini hujjat (document) sifatida yuboring.")


@router.message(AdminAddBook.waiting_title, F.text)
async def add_book_title(message: Message, state: FSMContext, session: AsyncSession) -> None:
    title = message.text.strip()[:256]
    data = await state.get_data()
    filename = data.get("filename")
    if not filename:
        await state.clear()
        await message.answer("Xatolik: fayl topilmadi. Qaytadan boshlang.")
        return
    book = await BookRepo(session).add(title, filename)
    await write_audit(
        session, actor_id=message.from_user.id, action="book_added",
        entity="book", entity_id=book.id, details=title,
    )
    await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Kitob qo‘shildi: «{title}» (#{book.id})", reply_markup=admin_back_kb()
    )
