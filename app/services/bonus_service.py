"""⭐ Atomik kod tekshirish va bonus berish (TZ §8, §15, §19).

Butun mantiq BITTA Postgres transaction ichida bajariladi:
  • ruchka kodi `FOR UPDATE` bilan qulflanadi
      → bir kodni ikki user bir vaqtda ishlata olmaydi (TZ §17.20);
  • bo'sh bonus `FOR UPDATE SKIP LOCKED` bilan olinadi
      → parallel so'rovlar har xil bonus oladi (TZ §17.21, §15);
  • ikkala o'zgarish birga commit/rollback bo'ladi (atomiklik, TZ §14.14).

Sheets bu jarayonda umuman ishtirok etmaydi — Postgres haqiqat manbai.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.enums import BonusStatus, CodeStatus
from app.db.repositories import (
    BonusRepo,
    CodeRepo,
    utcnow,
    write_audit,
)


class ClaimOutcome(str, enum.Enum):
    SUCCESS = "success"                    # kod to'g'ri + bonus berildi
    CONFIRMED_NO_BONUS = "confirmed_no_bonus"  # kod to'g'ri, bonus qolmagan
    NOT_FOUND = "not_found"                # kod topilmadi
    ALREADY_USED = "already_used"          # kod avval ishlatilgan
    BLOCKED = "blocked"                    # kod bloklangan


@dataclass(slots=True)
class ClaimResult:
    outcome: ClaimOutcome
    bonus_code: str | None = None
    discount_percent: int = 10


class BonusService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def claim(self, *, user, code_str: str) -> ClaimResult:
        """Kod bo'yicha xaridni tasdiqlaydi va imkon bo'lsa bonus biriktiradi.

        `code_str` allaqachon normalizatsiya qilingan bo'lishi kerak (trim+UPPER).
        """
        codes = CodeRepo(self.session)
        bonuses = BonusRepo(self.session)

        # Eslatma: SQLAlchemy autobegin tufayli barcha so'rovlar bitta
        # transaction ichida bajariladi. Oxirida commit/rollback bilan yopamiz.
        # FOR UPDATE va SKIP LOCKED qulflari commit'gacha ushlab turiladi.
        try:
            # 1) Kodni qulflab o'qiymiz
            code = await codes.get_for_update(code_str)

            if code is None:
                await self.session.rollback()
                return ClaimResult(ClaimOutcome.NOT_FOUND)
            if code.status == CodeStatus.blocked:
                await self.session.rollback()
                return ClaimResult(ClaimOutcome.BLOCKED)
            if code.status == CodeStatus.used:
                await self.session.rollback()
                return ClaimResult(ClaimOutcome.ALREADY_USED)

            # 2) Kodni band qilamiz — xarid tasdiqlandi (bonus bo'lmasa ham)
            code.status = CodeStatus.used
            code.used_by_telegram_id = user.telegram_id
            code.used_by_name = user.full_name
            code.used_by_phone = user.phone
            code.used_by_username = user.username
            code.used_at = utcnow()

            # 3) Bo'sh bonusni qulflab olamiz (SKIP LOCKED)
            bonus = await bonuses.take_free_for_update()

            if bonus is None:
                # TZ §8.5 — kod to'g'ri, lekin bonus qolmagan
                await write_audit(
                    self.session,
                    actor_id=user.telegram_id,
                    action="code_used_no_bonus",
                    entity="code",
                    entity_id=code.id,
                )
                await self.session.commit()
                return ClaimResult(ClaimOutcome.CONFIRMED_NO_BONUS)

            # 4) Bonusni shu userga biriktiramiz
            bonus.status = BonusStatus.assigned
            bonus.assigned_to_telegram_id = user.telegram_id
            bonus.assigned_to_name = user.full_name
            bonus.assigned_to_phone = user.phone
            bonus.assigned_to_username = user.username
            bonus.source_code_id = code.id
            bonus.assigned_at = utcnow()
            if settings.bonus_expiry_days > 0:
                bonus.expires_at = utcnow() + timedelta(days=settings.bonus_expiry_days)

            await write_audit(
                self.session,
                actor_id=user.telegram_id,
                action="bonus_assigned",
                entity="bonus",
                entity_id=bonus.id,
                details=f"code={code.code}",
            )

            await self.session.commit()
            return ClaimResult(
                ClaimOutcome.SUCCESS,
                bonus_code=bonus.bonus_code,
                discount_percent=bonus.discount_percent,
            )
        except Exception:
            await self.session.rollback()
            raise
