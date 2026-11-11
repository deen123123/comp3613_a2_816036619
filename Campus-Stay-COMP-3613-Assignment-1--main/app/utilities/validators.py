from datetime import date
from typing import Optional

from app.errors import ServiceError


def clean(value: Optional[str]) -> str:
    return (value or "").strip()


def parse_date(value: Optional[str], label: str) -> date:
    try:
        return date.fromisoformat(clean(value))
    except ValueError:
        raise ServiceError(f"{label} must be a valid date (YYYY-MM-DD).") from None


def parse_optional_date(value: Optional[str], label: str) -> Optional[date]:
    return parse_date(value, label) if clean(value) else None


def parse_int(value, label: str, minimum: int = None, maximum: int = None) -> int:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ServiceError(f"{label} must be a whole number.") from None
    if minimum is not None and number < minimum:
        raise ServiceError(f"{label} must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ServiceError(f"{label} must be at most {maximum}.")
    return number


def parse_float(value, label: str, minimum: float = None, maximum: float = None) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        raise ServiceError(f"{label} must be a number.") from None
    if minimum is not None and number < minimum:
        raise ServiceError(f"{label} must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ServiceError(f"{label} must be at most {maximum}.")
    return number


def to_int_or_none(value) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def to_float_or_none(value) -> Optional[float]:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None
