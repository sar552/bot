"""Google Sheets bilan bir tomonlama sync (TZ §8.1, §10).

Postgres — haqiqat manbai. Sheets faqat:
  • EKSPORT: Postgres → Sheets (admin ko'rishi uchun "oyna");
  • IMPORT: Sheets'dagi yangi kod/bonus qatorlarini Postgres'ga qo'shish.

Sheets sozlanmagan bo'lsa (credentials yo'q) — barcha metodlar jim o'tadi.
Bonus berish logikasi bu modulga BOG'LIQ EMAS — Sheets uzilsa ham bot ishlaydi.
"""
from __future__ import annotations

import asyncio

from loguru import logger

from app.config import settings
from app.db.enums import BonusStatus, CodeStatus
from app.db.repositories import BonusRepo, CodeRepo, UserRepo
from app.db.session import session_factory
from app.utils.validators import normalize_code

try:  # gspread ixtiyoriy — o'rnatilmagan bo'lsa ham bot ishga tushadi
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:  # pragma: no cover
    gspread = None
    Credentials = None

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsService:
    def __init__(self) -> None:
        self._client = None

    @property
    def enabled(self) -> bool:
        return settings.sheets_enabled and gspread is not None

    def _get_client(self):
        if self._client is None:
            creds = Credentials.from_service_account_file(
                settings.google_sheets_credentials, scopes=_SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client

    def _worksheet(self, title: str):
        sh = self._get_client().open_by_key(settings.google_spreadsheet_id)
        try:
            return sh.worksheet(title)
        except Exception:
            return sh.add_worksheet(title=title, rows=1000, cols=20)

    # ── EKSPORT (Postgres → Sheets) ──
    async def export_all(self) -> None:
        if not self.enabled:
            return
        try:
            # Ma'lumotni event loop'da (async) o'qiymiz, yozishni thread'da bajaramiz
            await self._export_all_inner()
            logger.info("Sheets eksport yakunlandi")
        except Exception as e:  # pragma: no cover
            logger.error(f"Sheets eksport xatosi: {e}")

    async def _export_all_inner(self) -> None:
        async with session_factory() as session:
            users = await UserRepo(session).list_all(limit=10000)
            codes = await CodeRepo(session).list_by_status(None, limit=10000)
            bonuses = await BonusRepo(session).list_by_status(None, limit=10000)

        def write():
            ws = self._worksheet("Users")
            ws.clear()
            ws.update(
                [["telegram_id", "username", "name", "phone", "registered_at"]]
                + [
                    [u.telegram_id, u.username or "", u.full_name, u.phone or "",
                     str(u.registered_at)]
                    for u in users
                ]
            )
            ws = self._worksheet("Codes")
            ws.clear()
            ws.update(
                [["code", "status", "used_by_telegram_id", "name", "phone",
                  "username", "used_at", "note"]]
                + [
                    [c.code, c.status.value, c.used_by_telegram_id or "",
                     c.used_by_name or "", c.used_by_phone or "",
                     c.used_by_username or "", str(c.used_at or ""), c.note or ""]
                    for c in codes
                ]
            )
            ws = self._worksheet("Bonuses")
            ws.clear()
            ws.update(
                [["bonus_code", "discount_percent", "status",
                  "assigned_to_telegram_id", "assigned_to_name",
                  "assigned_to_phone", "assigned_to_username",
                  "assigned_at", "used_at", "expires_at", "note"]]
                + [
                    [b.bonus_code, b.discount_percent, b.status.value,
                     b.assigned_to_telegram_id or "", b.assigned_to_name or "",
                     b.assigned_to_phone or "", b.assigned_to_username or "",
                     str(b.assigned_at or ""), str(b.used_at or ""),
                     str(b.expires_at or ""), b.note or ""]
                    for b in bonuses
                ]
            )

        await asyncio.to_thread(write)

    # ── IMPORT (Sheets → Postgres): yangi kod/bonus + status (block/used) ──
    async def import_new(self) -> tuple[int, int]:
        """Sheets'dan import qiladi:
          • yangi ruchka kod va bonuslarni qo'shadi (dublikatlar o'tkaziladi);
          • Sheets'dagi status orqali ADMIN amallarini qo'llaydi:
              - kod status = blocked  -> kodni bloklaydi;
              - bonus status = blocked/used/expired -> shu holatga o'tkazadi.

        Xavfsiz: bot belgilaydigan holatlar (unused/assigned) Sheets'dan
        QAYTA YOZILMAYDI — faqat admin tomonidagi terminal holatlar qo'llanadi.
        """
        if not self.enabled:
            return (0, 0)
        try:
            codes, bonuses = await asyncio.to_thread(self._read_new)
        except Exception as e:  # pragma: no cover
            logger.error(f"Sheets import o'qish xatosi: {e}")
            return (0, 0)

        added_codes = added_bonuses = 0
        async with session_factory() as session:
            crepo = CodeRepo(session)
            brepo = BonusRepo(session)

            for code, status in codes:
                if await crepo.add(code):
                    added_codes += 1
                if status == CodeStatus.blocked.value:
                    await crepo.block(code)  # admin Sheets'da bloklagan

            for bonus_code, percent, status in bonuses:
                if await brepo.add(bonus_code, percent):
                    added_bonuses += 1
                # admin Sheets orqali terminal holatga o'tkazsa
                if status in (
                    BonusStatus.blocked.value,
                    BonusStatus.used.value,
                    BonusStatus.expired.value,
                ):
                    await brepo.set_status(bonus_code, BonusStatus(status))

            await session.commit()

        if added_codes or added_bonuses:
            logger.info(
                f"Sheets import: {added_codes} kod, {added_bonuses} bonus qo'shildi"
            )
        return (added_codes, added_bonuses)

    def _read_new(self):
        sh = self._get_client().open_by_key(settings.google_spreadsheet_id)

        # codes: (code, status) — status B ustun
        codes: list[tuple[str, str]] = []
        try:
            rows = sh.worksheet("Codes").get_all_values()
            for row in rows[1:]:  # sarlavhani o'tkazamiz
                if row and row[0].strip():
                    c = normalize_code(row[0])
                    if c:
                        status = row[1].strip().lower() if len(row) > 1 else ""
                        codes.append((c, status))
        except Exception:
            pass

        # bonuses: (bonus_code, percent, status) — status C ustun
        bonuses: list[tuple[str, int, str]] = []
        try:
            rows = sh.worksheet("Bonuses").get_all_values()
            for row in rows[1:]:
                if row and row[0].strip():
                    code = row[0].strip()
                    percent = 10
                    if len(row) > 1 and str(row[1]).strip().isdigit():
                        percent = int(str(row[1]).strip())
                    status = row[2].strip().lower() if len(row) > 2 else ""
                    bonuses.append((code, percent, status))
        except Exception:
            pass

        return codes, bonuses

    # ── To'liq sinxron: avval import (qo'lda qo'shilganlar), keyin eksport ──
    async def sync(self) -> None:
        """Bir tsikl: Sheets'dagi yangi kodlarni import qilib, keyin DB holatini
        Sheets'ga qaytaradi (UI har doim yangilanib turadi)."""
        if not self.enabled:
            return
        await self.import_new()   # avval: qo'lda qo'shilganlarni o'qib olamiz
        await self.export_all()   # keyin: to'liq holatni qaytaramiz


sheets_service = SheetsService()
