"""FSM holatlari (aiogram)."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


class BonusFlow(StatesGroup):
    waiting_code = State()


class BookFlow(StatesGroup):
    # Foydalanuvchi kitob tanlab, kod kiritishini kutamiz (data: book_id)
    waiting_code = State()
