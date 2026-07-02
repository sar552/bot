"""Repository qatlami — barcha DB so'rovlari shu yerda jamlangan.

Atomiklik uchun muhim: lock'li (FOR UPDATE) so'rovlar faqat ochiq
transaction ichida (session.begin) chaqirilishi kerak.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BonusStatus, CodeStatus
from app.db.models import (
    AuditLog,
    Bonus,
    Book,
    ChannelClick,
    Code,
    RateLimit,
    User,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ───────────────────────── Users ─────────────────────────
class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, telegram_id: int) -> User | None:
        return await self.session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

    async def upsert_basic(self, telegram_id: int, username: str | None) -> User:
        """Foydalanuvchini topadi yoki bo'sh holatda yaratadi (registratsiya boshlanishi)."""
        user = await self.get(telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id, username=username, full_name="")
            self.session.add(user)
            await self.session.flush()
        elif username and user.username != username:
            user.username = username
        return user

    async def set_name(self, telegram_id: int, full_name: str) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(full_name=full_name)
        )

    async def set_phone(self, telegram_id: int, phone: str) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(phone=phone)
        )

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[User]:
        res = await self.session.scalars(
            select(User).order_by(User.registered_at.desc()).limit(limit).offset(offset)
        )
        return list(res)

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(User)) or 0

    async def all_telegram_ids(self) -> list[int]:
        res = await self.session.scalars(select(User.telegram_id))
        return list(res)


# ───────────────────────── Codes ─────────────────────────
class CodeRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, code: str) -> Code | None:
        """Kodni lock'siz o'qiydi (kitob uchun tekshirishda ishlatiladi)."""
        return await self.session.scalar(select(Code).where(Code.code == code))

    async def is_valid_for_books(self, code: str) -> bool:
        """Kitob yuklash uchun kod yaroqlimi: mavjud va bloklanmagan.

        Kodni ISHLATMAYDI (used qilmaydi) — ruchka egasi kitoblarni qayta oladi.
        """
        c = await self.get(code)
        return c is not None and c.status != CodeStatus.blocked

    async def get_for_update(self, code: str) -> Code | None:
        """Kodni qatorni qulflagan holda o'qiydi (FOR UPDATE).

        Faqat ochiq transaction ichida ishlatilsin.
        """
        return await self.session.scalar(
            select(Code).where(Code.code == code).with_for_update()
        )

    async def add(self, code: str, note: str | None = None) -> int | None:
        """Yangi kod qo'shadi. Dublikat bo'lsa None qaytaradi."""
        stmt = (
            pg_insert(Code)
            .values(code=code, note=note, status=CodeStatus.unused)
            .on_conflict_do_nothing(index_elements=[Code.code])
            .returning(Code.id)
        )
        return await self.session.scalar(stmt)

    async def block(self, code: str) -> bool:
        res = await self.session.execute(
            update(Code)
            .where(Code.code == code)
            .values(status=CodeStatus.blocked)
        )
        return res.rowcount > 0

    async def list_by_status(self, status: CodeStatus | None, limit: int = 50) -> list[Code]:
        q = select(Code).order_by(Code.id.desc()).limit(limit)
        if status is not None:
            q = q.where(Code.status == status)
        res = await self.session.scalars(q)
        return list(res)

    async def count_by_status(self) -> dict[str, int]:
        res = await self.session.execute(
            select(Code.status, func.count()).group_by(Code.status)
        )
        return {row[0].value: row[1] for row in res}


# ───────────────────────── Bonuses ─────────────────────────
class BonusRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def take_free_for_update(self) -> Bonus | None:
        """Bo'sh (unused) bonusni qulflab oladi.

        SKIP LOCKED — parallel tranzaksiyalar bir xil bonusni olmaydi,
        har biri keyingi bo'sh bonusga o'tadi (TZ §15, race condition himoyasi).
        """
        return await self.session.scalar(
            select(Bonus)
            .where(Bonus.status == BonusStatus.unused)
            .order_by(Bonus.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )

    async def add(self, bonus_code: str, discount_percent: int = 10) -> int | None:
        stmt = (
            pg_insert(Bonus)
            .values(
                bonus_code=bonus_code,
                discount_percent=discount_percent,
                status=BonusStatus.unused,
            )
            .on_conflict_do_nothing(index_elements=[Bonus.bonus_code])
            .returning(Bonus.id)
        )
        return await self.session.scalar(stmt)

    async def set_status(self, bonus_code: str, status: BonusStatus) -> bool:
        values: dict = {"status": status}
        if status == BonusStatus.used:
            values["used_at"] = utcnow()
        res = await self.session.execute(
            update(Bonus).where(Bonus.bonus_code == bonus_code).values(**values)
        )
        return res.rowcount > 0

    async def expire_overdue(self) -> int:
        """Muddati tugagan assigned bonuslarni expired qiladi (TZ §8.10)."""
        res = await self.session.execute(
            update(Bonus)
            .where(
                Bonus.status == BonusStatus.assigned,
                Bonus.expires_at.is_not(None),
                Bonus.expires_at < utcnow(),
            )
            .values(status=BonusStatus.expired)
        )
        return res.rowcount

    async def list_by_status(self, status: BonusStatus | None, limit: int = 50) -> list[Bonus]:
        q = select(Bonus).order_by(Bonus.id.desc()).limit(limit)
        if status is not None:
            q = q.where(Bonus.status == status)
        res = await self.session.scalars(q)
        return list(res)

    async def count_by_status(self) -> dict[str, int]:
        res = await self.session.execute(
            select(Bonus.status, func.count()).group_by(Bonus.status)
        )
        return {row[0].value: row[1] for row in res}


# ───────────────────────── Books ─────────────────────────
class BookRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[Book]:
        res = await self.session.scalars(
            select(Book).where(Book.is_active.is_(True)).order_by(Book.id)
        )
        return list(res)

    async def list_all(self) -> list[Book]:
        res = await self.session.scalars(select(Book).order_by(Book.id))
        return list(res)

    async def get(self, book_id: int) -> Book | None:
        return await self.session.get(Book, book_id)

    async def add(self, title: str, filename: str) -> Book:
        book = Book(title=title, filename=filename)
        self.session.add(book)
        await self.session.flush()
        return book

    async def set_active(self, book_id: int, active: bool) -> bool:
        book = await self.get(book_id)
        if book is None:
            return False
        book.is_active = active
        return True

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(Book)) or 0


# ───────────────────────── Rate limit ─────────────────────────
class RateLimitRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, telegram_id: int) -> RateLimit | None:
        return await self.session.get(RateLimit, telegram_id)

    async def register_failure(self, telegram_id: int, max_fails: int, block_minutes: int):
        from datetime import timedelta

        rl = await self.get(telegram_id)
        if rl is None:
            rl = RateLimit(telegram_id=telegram_id, failed_attempts=0)
            self.session.add(rl)
        rl.failed_attempts += 1
        if rl.failed_attempts >= max_fails:
            rl.blocked_until = utcnow() + timedelta(minutes=block_minutes)
            rl.failed_attempts = 0
        return rl

    async def reset(self, telegram_id: int) -> None:
        rl = await self.get(telegram_id)
        if rl is not None:
            rl.failed_attempts = 0
            rl.blocked_until = None


# ───────────────────────── Channel clicks ─────────────────────────
class ChannelRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_click(self, telegram_id: int, channel: str) -> None:
        self.session.add(ChannelClick(telegram_id=telegram_id, channel=channel))


# ───────────────────────── Hisobot (join) ─────────────────────────
async def purchase_report(session: AsyncSession, limit: int = 100_000):
    """Tasdiqlangan xaridlar: mijoz → ishlatgan kod → olgan bonus.

    Codes (used) LEFT JOIN Bonuses (source_code_id bo'yicha) — bonus
    olmaganlar ham ko'rinadi (bonus ustunlari bo'sh bo'ladi).
    """
    stmt = (
        select(
            Code.used_by_name,
            Code.used_by_phone,
            Code.used_by_username,
            Code.used_by_telegram_id,
            Code.code,
            Code.used_at,
            Bonus.bonus_code,
            Bonus.status,
            Bonus.assigned_at,
            Bonus.expires_at,
        )
        .select_from(Code)
        .outerjoin(Bonus, Bonus.source_code_id == Code.id)
        .where(Code.status == CodeStatus.used)
        .order_by(Code.used_at.desc())
        .limit(limit)
    )
    res = await session.execute(stmt)
    return res.all()


# ───────────────────────── Audit ─────────────────────────
async def write_audit(
    session: AsyncSession,
    *,
    actor_id: int | None,
    action: str,
    entity: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details,
        )
    )
