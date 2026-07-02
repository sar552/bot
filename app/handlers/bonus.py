"""10% bonus olish oqimi (TZ §8)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.keyboards import callbacks as cb
from app.keyboards.inline import (
    back_to_menu_kb,
    bonus_intro_kb,
    bonus_success_kb,
    code_retry_kb,
    operator_only_kb,
)
from app.services.bonus_service import BonusService, ClaimOutcome
from app.services.rate_limit_service import RateLimitService
from app.states.user import BonusFlow
from app.utils.validators import normalize_code

router = Router(name="bonus")


@router.callback_query(F.data == cb.MENU_BONUS)
async def bonus_intro(call: CallbackQuery, state: FSMContext, texts) -> None:
    await state.clear()
    try:
        await call.message.edit_text(texts.ASK_CODE, reply_markup=bonus_intro_kb(texts))
    except Exception:
        await call.message.answer(texts.ASK_CODE, reply_markup=bonus_intro_kb(texts))
    await state.set_state(BonusFlow.waiting_code)
    await call.answer()


@router.callback_query(F.data == cb.BONUS_ENTER_CODE)
async def bonus_enter(call: CallbackQuery, state: FSMContext, texts) -> None:
    await call.message.answer(texts.ASK_CODE)
    await state.set_state(BonusFlow.waiting_code)
    await call.answer()


@router.callback_query(F.data == cb.BONUS_USE)
async def bonus_use(call: CallbackQuery, texts) -> None:
    await call.message.answer(texts.BONUS_USAGE, reply_markup=back_to_menu_kb(texts))
    await call.answer()


@router.message(BonusFlow.waiting_code, F.text)
async def on_code(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User | None,
    texts,
) -> None:
    # Registratsiya tugaganini tekshiramiz
    if user is None or not user.full_name or not user.phone:
        await message.answer(texts.NEED_REGISTER)
        await state.clear()
        return

    # telegram_id ni oldindan lokal o'zgaruvchiga olamiz (rollback expired qiladi)
    tg_id = user.telegram_id

    rl = RateLimitService(session)

    blocked = await rl.remaining_block_minutes(tg_id)
    if blocked > 0:
        await message.answer(texts.rate_limited(blocked), reply_markup=operator_only_kb(texts))
        return

    code_str = normalize_code(message.text or "")
    if code_str is None:
        await message.answer(texts.CODE_NOT_FOUND, reply_markup=code_retry_kb(texts))
        await rl.register_failure(tg_id)
        return

    # ⭐ Atomik kod tekshirish + bonus berish
    service = BonusService(session)
    try:
        result = await service.claim(user=user, code_str=code_str)
    except Exception as e:  # pragma: no cover
        logger.exception(f"Bonus claim xatosi: {e}")
        await message.answer(texts.CODE_NOT_FOUND, reply_markup=operator_only_kb(texts))
        return

    if result.outcome == ClaimOutcome.SUCCESS:
        await rl.reset(tg_id)
        await state.clear()
        await message.answer(
            texts.bonus_success(result.bonus_code, result.discount_percent),
            reply_markup=bonus_success_kb(texts),
        )

    elif result.outcome == ClaimOutcome.CONFIRMED_NO_BONUS:
        await rl.reset(tg_id)
        await state.clear()
        await message.answer(texts.CONFIRMED_NO_BONUS, reply_markup=operator_only_kb(texts))

    elif result.outcome == ClaimOutcome.ALREADY_USED:
        await message.answer(texts.CODE_ALREADY_USED, reply_markup=operator_only_kb(texts))

    elif result.outcome == ClaimOutcome.BLOCKED:
        await message.answer(texts.CODE_BLOCKED, reply_markup=operator_only_kb(texts))

    else:  # NOT_FOUND
        minutes = await rl.register_failure(tg_id)
        if minutes > 0:
            await message.answer(texts.rate_limited(minutes), reply_markup=operator_only_kb(texts))
        else:
            await message.answer(texts.CODE_NOT_FOUND, reply_markup=code_retry_kb(texts))
