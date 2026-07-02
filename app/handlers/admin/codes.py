"""Admin — kodlarni ko'rish, qo'shish, bloklash (TZ §10.3–§10.6, §10.13, §10.15)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import CodeStatus
from app.db.repositories import CodeRepo, write_audit
from app.keyboards import callbacks as cb
from app.keyboards.admin import admin_back_kb
from app.states.admin import AdminAddCode, AdminBlockCode
from app.utils.validators import normalize_code

router = Router(name="admin_codes")


@router.callback_query(F.data == cb.ADMIN_CODES)
async def list_codes(call: CallbackQuery, session: AsyncSession) -> None:
    repo = CodeRepo(session)
    counts = await repo.count_by_status()
    recent = await repo.list_by_status(None, limit=20)

    lines = [
        "🔑 Kodlar holati:",
        f"  unused: {counts.get('unused', 0)} | used: {counts.get('used', 0)} | "
        f"blocked: {counts.get('blocked', 0)}",
        "\nOxirgi 20 ta:",
    ]
    for c in recent:
        who = f" → {c.used_by_name} ({c.used_by_phone})" if c.used_by_telegram_id else ""
        lines.append(f"• {c.code} [{c.status.value}]{who}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n…"
    try:
        await call.message.edit_text(text, reply_markup=admin_back_kb())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_kb())
    await call.answer()


# ── Kod qo'shish (har qatorda bitta kod; "kod | izoh" ko'rinishi ham mumkin) ──
@router.callback_query(F.data == cb.ADMIN_ADD_CODE)
async def add_code_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer(
        "Yangi kodlarni yuboring. Har bir qatorda bitta kod.\n"
        "Izoh qo‘shmoqchi bo‘lsangiz: `KOD | izoh`",
        parse_mode="Markdown",
    )
    await state.set_state(AdminAddCode.waiting_codes)
    await call.answer()


@router.message(AdminAddCode.waiting_codes, F.text)
async def add_code_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    repo = CodeRepo(session)
    added, skipped = 0, 0
    for line in message.text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        code = normalize_code(parts[0])
        note = parts[1].strip() if len(parts) > 1 else None
        if code is None:
            skipped += 1
            continue
        new_id = await repo.add(code, note)
        if new_id:
            added += 1
        else:
            skipped += 1
    await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Qo‘shildi: {added}, o‘tkazib yuborildi (dublikat/yaroqsiz): {skipped}",
        reply_markup=admin_back_kb(),
    )


# ── Kodni bloklash ──
@router.callback_query(F.data == cb.ADMIN_BLOCK_CODE)
async def block_code_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer("Bloklamoqchi bo‘lgan kodni yuboring:")
    await state.set_state(AdminBlockCode.waiting_code)
    await call.answer()


@router.message(AdminBlockCode.waiting_code, F.text)
async def block_code_do(message: Message, state: FSMContext, session: AsyncSession) -> None:
    code = normalize_code(message.text or "")
    if code is None:
        await message.answer("Kod formati yaroqsiz. Qayta yuboring.")
        return
    repo = CodeRepo(session)
    ok = await repo.block(code)
    if ok:
        await write_audit(
            session, actor_id=message.from_user.id, action="code_blocked",
            entity="code", details=code,
        )
    await session.commit()
    await state.clear()
    msg = f"✅ {code} bloklandi." if ok else f"❌ {code} topilmadi."
    await message.answer(msg, reply_markup=admin_back_kb())
