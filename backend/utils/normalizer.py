"""Input normalisation and sanitisation helpers."""
from __future__ import annotations
import re
from urllib.parse import urlparse


def normalize_value(type_: str, value: str) -> str:
    """Normalise an entity value based on its type."""
    value = value.strip()
    if type_ == "phone":
        # Keep only digits and leading +
        digits = re.sub(r"[^\d+]", "", value)
        return digits[:20]
    if type_ == "url":
        # Lowercase scheme + host; preserve path
        try:
            p = urlparse(value.lower() if "://" in value else "https://" + value.lower())
            return p.geturl()[:2048]
        except Exception:
            return value.lower()[:2048]
    # message: collapse whitespace
    return re.sub(r"\s+", " ", value)[:2048]


def sanitize_text(text: str, max_len: int = 4000) -> str:
    """Strip dangerous characters and limit length."""
    # Remove null bytes and control chars (except newline/tab)
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    return text.strip()[:max_len]


def validate_url(value: str) -> bool:
    """Return True if value looks like a valid URL."""
    try:
        p = urlparse(value if "://" in value else "https://" + value)
        return bool(p.netloc)
    except Exception:
        return False
