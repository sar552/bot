"""Kirish ma'lumotlarini tekshirish va normalizatsiya (TZ §3.2, §3.3, §8.2)."""
from __future__ import annotations

import re

_PHONE_DIGITS = re.compile(r"\d+")
_CODE_ALLOWED = re.compile(r"^[A-Z0-9\-]{4,32}$")


def clean_name(raw: str) -> str | None:
    """Ismni tozalaydi. Yaroqsiz bo'lsa None qaytaradi (qayta so'rash kerak)."""
    name = " ".join(raw.split())
    if len(name) < 2 or name.isdigit():
        return None
    return name[:256]


def normalize_phone(raw: str) -> str | None:
    """Telefon raqamini +998XXXXXXXXX ko'rinishiga keltiradi.

    O'zbekiston raqamlarini qo'llab-quvvatlaydi (TZ §3.3). Yaroqsiz bo'lsa None.
    """
    digits = "".join(_PHONE_DIGITS.findall(raw))
    if not digits:
        return None
    # 998901234567 / 901234567 / 0901234567 variantlarini qamrab olamiz
    if digits.startswith("998") and len(digits) == 12:
        return "+" + digits
    if len(digits) == 9:  # 901234567
        return "+998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    # Boshqa xalqaro raqam: kamida 10 ta raqam bo'lsa qabul qilamiz
    if 10 <= len(digits) <= 15:
        return "+" + digits
    return None


def normalize_code(raw: str) -> str | None:
    """Ruchka kodini tozalaydi: trim + UPPER (TZ §8.2).

    Format yaroqsiz bo'lsa None qaytaradi.
    """
    code = raw.strip().upper()
    if not code:
        return None
    if not _CODE_ALLOWED.match(code):
        return None
    return code
