"""Admin FSM holatlari."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminAddCode(StatesGroup):
    waiting_codes = State()


class AdminAddBonus(StatesGroup):
    waiting_bonuses = State()


class AdminBlockCode(StatesGroup):
    waiting_code = State()


class AdminBonusStatus(StatesGroup):
    waiting_code = State()
    waiting_status = State()


class AdminBroadcast(StatesGroup):
    waiting_message = State()
    waiting_confirm = State()


class AdminAddBook(StatesGroup):
    waiting_file = State()
    waiting_title = State()
