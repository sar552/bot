"""SQLAlchemy 2.0 modellari (TZ §9.2 — Database varianti)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.enums import BonusStatus, CodeStatus


class Base(DeclarativeBase):
    pass


# Barcha vaqt ustunlari timezone-aware (timestamptz) — utcnow() aware qiymat beradi
TZDateTime = DateTime(timezone=True)


# Postgres ENUM tiplari (Alembic create_type=False — migrationda qo'lda yaratamiz)
code_status_enum = PgEnum(CodeStatus, name="code_status", create_type=False)
bonus_status_enum = PgEnum(BonusStatus, name="bonus_status", create_type=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(128))
    full_name: Mapped[str] = mapped_column(String(256))
    phone: Mapped[str | None] = mapped_column(String(32))
    language: Mapped[str] = mapped_column(String(8), default="uz")
    registered_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())


class Code(Base):
    """Ruchka orqasidagi maxsus kodlar (TZ §9.2.2)."""

    __tablename__ = "codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[CodeStatus] = mapped_column(
        code_status_enum, default=CodeStatus.unused, index=True
    )
    used_by_telegram_id: Mapped[int | None] = mapped_column(BigInteger)
    used_by_name: Mapped[str | None] = mapped_column(String(256))
    used_by_phone: Mapped[str | None] = mapped_column(String(32))
    used_by_username: Mapped[str | None] = mapped_column(String(128))
    used_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    note: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())


class Bonus(Base):
    """Oldindan yuklangan 10% bonuslar (TZ §9.2.3)."""

    __tablename__ = "bonuses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bonus_code: Mapped[str] = mapped_column(String(64), unique=True)
    discount_percent: Mapped[int] = mapped_column(default=10)
    status: Mapped[BonusStatus] = mapped_column(
        bonus_status_enum, default=BonusStatus.unused, index=True
    )
    assigned_to_telegram_id: Mapped[int | None] = mapped_column(BigInteger)
    assigned_to_name: Mapped[str | None] = mapped_column(String(256))
    assigned_to_phone: Mapped[str | None] = mapped_column(String(32))
    assigned_to_username: Mapped[str | None] = mapped_column(String(128))
    source_code_id: Mapped[int | None] = mapped_column(ForeignKey("codes.id"))
    assigned_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    used_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    expires_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    note: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())


class Book(Base):
    """Kitoblar — .tnb fayllar ro'yxati (ruchka kodi bilan yuklab olinadi)."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    filename: Mapped[str] = mapped_column(String(256))  # books/ papkasidagi fayl nomi
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())


class RateLimit(Base):
    """Noto'g'ri kod kiritish cheklovi (TZ §8.11.13)."""

    __tablename__ = "rate_limits"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    failed_attempts: Mapped[int] = mapped_column(default=0)
    blocked_until: Mapped[datetime | None] = mapped_column(TZDateTime)
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), onupdate=func.now()
    )


class ChannelClick(Base):
    """Sotuv kanaliga o'tishlar logi (TZ §7)."""

    __tablename__ = "channel_clicks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    channel: Mapped[str] = mapped_column(String(32))
    clicked_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())


class AuditLog(Base):
    """Admin amallari va muhim hodisalar (TZ §14.10)."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str | None] = mapped_column(String(32))
    entity_id: Mapped[int | None] = mapped_column(BigInteger)
    details: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())


Index("idx_channel_clicks_tg", ChannelClick.telegram_id)
