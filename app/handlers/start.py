"""/start — til tanlash → registratsiya yoki menyu (TZ §3.1, §11.2)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app import texts as i18n
from app.db.models import User
from app.db.repositories import UserRepo
from app.keyboards import callbacks as cb
from app.keyboards.inline import lang_kb, main_menu_kb
from app.states.user import Registration
from app.texts import get_texts

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
) -> None:
    await state.clear()

    # Ro'yxatdan o'tgan foydalanuvchi — to'g'ridan menyuga (o'z tilida)
    if user is not None and user.full_name and user.phone:
        t = get_texts(user.language)
        await message.answer(t.MAIN_MENU, reply_markup=main_menu_kb(t))
        return

    # Yangi foydalanuvchi — avval til tanlaydi
    await message.answer(i18n.CHOOSE_LANG, reply_markup=lang_kb())


@router.callback_query(F.data.in_({cb.LANG_UZ, cb.LANG_RU}))
async def on_lang_chosen(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    lang = "uz" if call.data == cb.LANG_UZ else "ru"
    t = get_texts(lang)

    repo = UserRepo(session)
    user = await repo.upsert_basic(call.from_user.id, call.from_user.username)
    user.language = lang
    await session.commit()

    if user.full_name and user.phone:
        # Ro'yxatdan o'tgan — til o'zgartirdi, menyuga qaytamiz
        try:
            await call.message.edit_text(t.MAIN_MENU, reply_markup=main_menu_kb(t))
        except Exception:
            await call.message.answer(t.MAIN_MENU, reply_markup=main_menu_kb(t))
    else:
        # Yangi — registratsiyani boshlaymiz
        try:
            await call.message.edit_text(t.START)
        except Exception:
            await call.message.answer(t.START)
        await state.set_state(Registration.waiting_name)
    await call.answer()


@router.callback_query(F.data == cb.MENU_LANG)
async def change_lang(call: CallbackQuery) -> None:
    """Asosiy menyudagi 🌐 Til tugmasi — tilni qayta tanlash."""
    try:
        await call.message.edit_text(i18n.CHOOSE_LANG, reply_markup=lang_kb())
    except Exception:
        await call.message.answer(i18n.CHOOSE_LANG, reply_markup=lang_kb())
    await call.answer()
