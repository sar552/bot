"""Kod va bonus statuslari (TZ §8.3, §8.9)."""
from __future__ import annotations

import enum


class CodeStatus(str, enum.Enum):
    unused = "unused"    # Kod hali ishlatilmagan
    used = "used"        # Kod allaqachon aktivlashtirilgan
    blocked = "blocked"  # Kod bloklangan yoki bekor qilingan


class BonusStatus(str, enum.Enum):
    unused = "unused"      # Bonus hali hech kimga berilmagan
    assigned = "assigned"  # Bonus berilgan, lekin hali ishlatilmagan
    used = "used"          # Bonus xaridda ishlatilgan
    expired = "expired"    # Bonus muddati tugagan
    blocked = "blocked"    # Bonus bekor qilingan
