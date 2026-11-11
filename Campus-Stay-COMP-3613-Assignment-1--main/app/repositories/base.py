from typing import Any

from sqlalchemy import func
from sqlmodel import Session, select


def count(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


def save(session: Session, *items) -> Any:
    """Add and commit one or more rows; returns the first so callers can chain."""
    for item in items:
        session.add(item)
    session.commit()
    for item in items:
        session.refresh(item)
    return items[0] if items else None
