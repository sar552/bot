"""Ism va telefon olish (TZ §3.2, §3.3)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepo
from app.keyboards.inline import main_menu_kb
from app.keyboards.reply import phone_request_kb, remove_kb
from app.states.user import Registration
from app.utils.validators import clean_name, normalize_phone

router = Router(name="registration")


@router.message(Registration.waiting_name, F.text)
async def on_name(message: Message, state: FSMContext, session: AsyncSession, texts) -> None:
    name = clean_name(message.text or "")
    if name is None:
        await message.answer(texts.ASK_NAME_AGAIN)
        return

    repo = UserRepo(session)
    await repo.set_name(message.from_user.id, name)
    await session.commit()

    await message.answer(texts.ASK_PHONE, reply_markup=phone_request_kb(texts))
    await state.set_state(Registration.waiting_phone)


@router.message(Registration.waiting_name)
async def on_name_invalid(message: Message, texts) -> None:
    await message.answer(texts.ASK_NAME_AGAIN)


@router.message(Registration.waiting_phone, F.contact)
async def on_contact(message: Message, state: FSMContext, session: AsyncSession, texts) -> None:
    phone = normalize_phone(message.contact.phone_number)
    await _finish(message, state, session, texts, phone)


@router.message(Registration.waiting_phone, F.text)
async def on_phone_text(message: Message, state: FSMContext, session: AsyncSession, texts) -> None:
    phone = normalize_phone(message.text or "")
    await _finish(message, state, session, texts, phone)


async def _finish(message: Message, state: FSMContext, session: AsyncSession, texts, phone) -> None:
    if phone is None:
        await message.answer(texts.ASK_PHONE_AGAIN, reply_markup=phone_request_kb(texts))
        return

    repo = UserRepo(session)
    await repo.set_phone(message.from_user.id, phone)
    await session.commit()

    await state.clear()
    await message.answer(texts.REGISTERED, reply_markup=remove_kb())
    await message.answer(texts.MAIN_MENU, reply_markup=main_menu_kb(texts))
