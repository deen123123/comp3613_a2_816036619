from datetime import date, datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp (stored the same way on SQLite and Postgres)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def today() -> date:
    return date.today()
