"""i18n — foydalanuvchi tiliga qarab matn modulini tanlash (TZ §11.2)."""
from __future__ import annotations

from types import ModuleType

from app.texts import ru, uz

SUPPORTED = ("uz", "ru")
DEFAULT_LANG = "uz"

_MODULES: dict[str, ModuleType] = {"uz": uz, "ru": ru}


def get_texts(lang: str | None) -> ModuleType:
    """Til kodiga mos matn modulini qaytaradi (noma'lum bo'lsa — uz)."""
    return _MODULES.get(lang or DEFAULT_LANG, uz)


# Til tanlash — ikki tilli (til hali tanlanmaganda ko'rsatiladi)
CHOOSE_LANG = "Tilni tanlang / Выберите язык 👇"
B_LANG_UZ = "🇺🇿 O‘zbekcha"
B_LANG_RU = "🇷🇺 Русский"
