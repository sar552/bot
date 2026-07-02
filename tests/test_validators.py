"""Validatorlar uchun testlar (Postgres talab qilmaydi)."""
from __future__ import annotations

from app.utils.validators import clean_name, normalize_code, normalize_phone


def test_clean_name():
    assert clean_name("  Ali   Valiyev ") == "Ali Valiyev"
    assert clean_name("A") is None
    assert clean_name("12345") is None
    assert clean_name("Ali") == "Ali"


def test_normalize_phone():
    assert normalize_phone("+998901234567") == "+998901234567"
    assert normalize_phone("998901234567") == "+998901234567"
    assert normalize_phone("901234567") == "+998901234567"
    assert normalize_phone("abc") is None
    assert normalize_phone("123") is None


def test_normalize_code():
    assert normalize_code("  abc12345 ") == "ABC12345"
    assert normalize_code("ABC-12345") == "ABC-12345"
    assert normalize_code("") is None
    assert normalize_code("!!") is None
