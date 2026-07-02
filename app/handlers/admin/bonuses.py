"""Admin — bonuslarni ko'rish, qo'shish, status o'zgartirish (TZ §10.8–§10.12, §10.16)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BonusStatus
from app.db.repositories import BonusRepo, write_audit
from app.keyboards import callbacks as cb
from app.keyboards.admin import admin_back_kb
from app.states.admin import AdminAddBonus, AdminBonusStatus

router = Router(name="admin_bonuses")

_VALID_STATUSES = {s.value for s in BonusStatus}


@router.callback_query(F.data == cb.ADMIN_BONUSES)
async def list_bonuses(call: CallbackQuery, session: AsyncSession) -> None:
    repo = BonusRepo(session)
    counts = await repo.count_by_status()
    recent = await repo.list_by_status(None, limit=20)

    lines = [
        "🎁 Bonuslar holati:",
        f"  unused: {counts.get('unused', 0)} | assigned: {counts.get('assigned', 0)} | "
        f"used: {counts.get('used', 0)} | expired: {counts.get('expired', 0)} | "
        f"blocked: {counts.get('blocked', 0)}",
        "\nOxirgi 20 ta:",
    ]
    for b in recent:
        who = f" → {b.assigned_to_name} ({b.assigned_to_phone})" if b.assigned_to_telegram_id else ""
        lines.append(f"• {b.bonus_code} [{b.status.value}]{who}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n…"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_kb())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_kb())
    await call.answer()


# ── Bonus qo'shish (har qatorda: "BONUS_KOD" yoki "BONUS_KOD | foiz") ──
@router.callback_query(F.data == cb.ADMIN_ADD_BONUS)
async def add_bonus_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer(
        "Yangi bonus kodlarini yuboring. Har bir qatorda bitta kod.\n"
        "Foizni o‘zgartirish uchun: `BONUS10-AB12 | 10`",
        parse_mode="Markdown",
    )
    await state.set_state(AdminAddBonus.waiting_bonuses)
    await call.answer()


@router.message(AdminAddBonus.waiting_bonuses, F.text)
async def add_bonus_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    repo = BonusRepo(session)
    added, skipped = 0, 0
    for line in message.text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        code = parts[0].strip()
        percent = 10
        if len(parts) > 1:
            try:
                percent = int(parts[1].strip())
            except ValueError:
                percent = 10
        if not code:
            skipped += 1
            continue
        new_id = await repo.add(code, percent)
        if new_id:
            added += 1
        else:
            skipped += 1
    await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Qo‘shildi: {added}, o‘tkazib yuborildi (dublikat): {skipped}",
        reply_markup=admin_back_kb(),
    )


# ── Bonus statusini qo'lda o'zgartirish ──
@router.callback_query(F.data == cb.ADMIN_BONUS_STATUS)
async def bonus_status_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer(
        "Format: `BONUS_KOD status`\n"
        "Mavjud statuslar: unused, assigned, used, expired, blocked\n"
        "Masalan: `BONUS10-AB12 used`",
        parse_mode="Markdown",
    )
    await state.set_state(AdminBonusStatus.waiting_code)
    await call.answer()


@router.message(AdminBonusStatus.waiting_code, F.text)
async def bonus_status_do(message: Message, state: FSMContext, session: AsyncSession) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2 or parts[1] not in _VALID_STATUSES:
        await message.answer(
            "Noto‘g‘ri format. Masalan: `BONUS10-AB12 used`", parse_mode="Markdown"
        )
        return
    bonus_code, status = parts[0], parts[1]
    repo = BonusRepo(session)
    ok = await repo.set_status(bonus_code, BonusStatus(status))
    if ok:
        await write_audit(
            session, actor_id=message.from_user.id, action="bonus_status_change",
            entity="bonus", details=f"{bonus_code}->{status}",
        )
    await session.commit()
    await state.clear()
    msg = f"✅ {bonus_code} → {status}" if ok else f"❌ {bonus_code} topilmadi."
    await message.answer(msg, reply_markup=admin_back_kb())
