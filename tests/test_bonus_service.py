"""⭐ Atomik bonus berish va race condition testlari (TZ §17.8–§17.21).

Postgres talab qiladi (conftest dagi TEST_DATABASE_URL).
"""
from __future__ import annotations

import asyncio

import pytest

from app.db.enums import BonusStatus, CodeStatus
from app.db.models import Bonus, Code, User
from app.services.bonus_service import BonusService, ClaimOutcome

pytestmark = pytest.mark.asyncio


async def _seed_user(session_factory, tg_id: int) -> User:
    async with session_factory() as s:
        user = User(telegram_id=tg_id, username=f"u{tg_id}", full_name="Test",
                    phone="+998901234567")
        s.add(user)
        await s.commit()
        return user


async def _add_code(session_factory, code: str, status=CodeStatus.unused):
    async with session_factory() as s:
        s.add(Code(code=code, status=status))
        await s.commit()


async def _add_bonus(session_factory, code: str):
    async with session_factory() as s:
        s.add(Bonus(bonus_code=code, discount_percent=10, status=BonusStatus.unused))
        await s.commit()


async def test_success(clean_tables, session_factory):
    user = await _seed_user(session_factory, 1001)
    await _add_code(session_factory, "ABC12345")
    await _add_bonus(session_factory, "BONUS10-AAAA")

    async with session_factory() as s:
        res = await BonusService(s).claim(user=user, code_str="ABC12345")

    assert res.outcome == ClaimOutcome.SUCCESS
    assert res.bonus_code == "BONUS10-AAAA"


async def test_not_found(clean_tables, session_factory):
    user = await _seed_user(session_factory, 1002)
    async with session_factory() as s:
        res = await BonusService(s).claim(user=user, code_str="NOPE")
    assert res.outcome == ClaimOutcome.NOT_FOUND


async def test_already_used(clean_tables, session_factory):
    user = await _seed_user(session_factory, 1003)
    await _add_code(session_factory, "USED1", status=CodeStatus.used)
    async with session_factory() as s:
        res = await BonusService(s).claim(user=user, code_str="USED1")
    assert res.outcome == ClaimOutcome.ALREADY_USED


async def test_blocked(clean_tables, session_factory):
    user = await _seed_user(session_factory, 1004)
    await _add_code(session_factory, "BLK1", status=CodeStatus.blocked)
    async with session_factory() as s:
        res = await BonusService(s).claim(user=user, code_str="BLK1")
    assert res.outcome == ClaimOutcome.BLOCKED


async def test_confirmed_no_bonus(clean_tables, session_factory):
    """Kod to'g'ri, lekin bonus qolmagan (TZ §8.5)."""
    user = await _seed_user(session_factory, 1005)
    await _add_code(session_factory, "OK1")  # bonus qo'shmaymiz
    async with session_factory() as s:
        res = await BonusService(s).claim(user=user, code_str="OK1")
    assert res.outcome == ClaimOutcome.CONFIRMED_NO_BONUS


async def test_concurrent_same_code(clean_tables, session_factory):
    """Bitta kodni 2 user bir vaqtda → faqat bittasi muvaffaqiyatli (TZ §17.20)."""
    u1 = await _seed_user(session_factory, 2001)
    u2 = await _seed_user(session_factory, 2002)
    await _add_code(session_factory, "RACE1")
    await _add_bonus(session_factory, "BONUS10-B1")
    await _add_bonus(session_factory, "BONUS10-B2")

    async def claim(user):
        async with session_factory() as s:
            return await BonusService(s).claim(user=user, code_str="RACE1")

    r1, r2 = await asyncio.gather(claim(u1), claim(u2))
    outcomes = {r1.outcome, r2.outcome}
    assert ClaimOutcome.SUCCESS in outcomes
    assert ClaimOutcome.ALREADY_USED in outcomes


async def test_session_reusable_after_not_found(clean_tables, session_factory):
    """Regressiya: NOT_FOUND'dagi rollback'dan keyin ham sessiya ishlatilishi mumkin.

    Ilgari handler claim'dan keyin `user.telegram_id` ga murojaat qilganda
    MissingGreenlet xatosi chiqardi (rollback obyektni expired qilgani uchun).
    """
    from app.db.repositories import UserRepo
    from app.services.rate_limit_service import RateLimitService

    await _seed_user(session_factory, 4001)

    async with session_factory() as s:
        user = await UserRepo(s).get(4001)
        tg_id = user.telegram_id  # claim'dan oldin olamiz (fix)
        res = await BonusService(s).claim(user=user, code_str="DOESNOTEXIST")
        assert res.outcome == ClaimOutcome.NOT_FOUND
        # rollback'dan keyin sessiya hali ishlaydi
        minutes = await RateLimitService(s).register_failure(tg_id)
        assert minutes == 0  # birinchi xato — hali bloklanmaydi


async def test_concurrent_distinct_bonuses(clean_tables, session_factory):
    """2 har xil kod bir vaqtda → har biriga HAR XIL bonus (TZ §17.21, §15)."""
    u1 = await _seed_user(session_factory, 3001)
    u2 = await _seed_user(session_factory, 3002)
    await _add_code(session_factory, "CODE-A")
    await _add_code(session_factory, "CODE-B")
    await _add_bonus(session_factory, "BONUS10-X1")
    await _add_bonus(session_factory, "BONUS10-X2")

    async def claim(user, code):
        async with session_factory() as s:
            return await BonusService(s).claim(user=user, code_str=code)

    r1, r2 = await asyncio.gather(claim(u1, "CODE-A"), claim(u2, "CODE-B"))
    assert r1.outcome == ClaimOutcome.SUCCESS
    assert r2.outcome == ClaimOutcome.SUCCESS
    # Eng muhimi: bitta bonus ikki userga berilmagan
    assert r1.bonus_code != r2.bonus_code
