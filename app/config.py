"""Loyiha konfiguratsiyasi — .env dan o'qiladi (pydantic-settings)."""
from __future__ import annotations

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str
    # Vergul bilan ajratilgan ID'lar: "11111111,22222222".
    # Xom holda str sifatida o'qiymiz; ro'yxat sifatida `admin_ids` property beradi.
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    operator_username: str = "operator"

    # Database / cache
    database_url: str
    redis_url: str = "redis://redis:6379/0"

    # Google Sheets (ixtiyoriy)
    google_sheets_credentials: str = ""
    google_spreadsheet_id: str = ""
    sheets_sync_interval_min: int = 10

    # Kontent
    product_video_file_id: str = ""

    # Sotuv kanallari
    channel_telegram_url: str = ""
    channel_instagram_url: str = ""
    channel_uzum_url: str = ""
    channel_other_url: str = ""

    # Biznes qoidalari
    rate_limit_max_fails: int = 5
    rate_limit_block_minutes: int = 10
    bonus_expiry_days: int = 30

    # Kitob yuklashda noto'g'ri kod uchun urinishlar
    book_code_max_fails: int = 10
    book_block_minutes: int = 10

    # Kitob fayllari saqlanadigan papka (konteyner ichida)
    books_dir: str = "books"

    @property
    def admin_ids(self) -> list[int]:
        return [int(x) for x in self.admin_ids_raw.replace(" ", "").split(",") if x]

    @property
    def operator_link(self) -> str:
        username = self.operator_username.lstrip("@")
        return f"https://t.me/{username}"

    @property
    def sheets_enabled(self) -> bool:
        return bool(self.google_sheets_credentials and self.google_spreadsheet_id)


settings = Settings()
