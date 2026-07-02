"""Admin — foydalanuvchilarni ko'rish (TZ §10.1, §10.2)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepo
from app.keyboards import callbacks as cb
from app.keyboards.admin import admin_back_kb

router = Router(name="admin_users")


@router.callback_query(F.data == cb.ADMIN_USERS)
async def list_users(call: CallbackQuery, session: AsyncSession) -> None:
    repo = UserRepo(session)
    total = await repo.count()
    users = await repo.list_all(limit=30)

    lines = [f"👥 Foydalanuvchilar (jami: {total}, oxirgi 30 ta):\n"]
    for u in users:
        uname = f"@{u.username}" if u.username else "—"
        lines.append(f"• {u.full_name} | {u.phone or '—'} | {uname} | ID:{u.telegram_id}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n…"

    try:
        await call.message.edit_text(text, reply_markup=admin_back_kb())
    except Exception:
        await call.message.answer(text, reply_markup=admin_back_kb())
    await call.answer()
