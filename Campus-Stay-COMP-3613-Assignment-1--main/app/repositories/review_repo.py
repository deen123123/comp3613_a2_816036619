from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.models import Review
from app.repositories.base import save


def add(session: Session, review: Review) -> Review:
    return save(session, review)


def get_by_booking(session: Session, booking_id: int) -> Optional[Review]:
    return session.exec(select(Review).where(Review.booking_id == booking_id)).first()


def for_accommodation(session: Session, accommodation_id: int) -> List[Review]:
    stmt = select(Review).where(Review.accommodation_id == accommodation_id).order_by(col(Review.created_at).desc())
    return list(session.exec(stmt).all())


def reviewed_booking_ids(session: Session, booking_ids: List[int]) -> Set[int]:
    if not booking_ids:
        return set()
    rows = session.exec(select(Review.booking_id).where(col(Review.booking_id).in_(booking_ids))).all()
    return set(rows)


def rating_stats(session: Session, accommodation_ids: List[int]) -> Dict[int, Tuple[float, int]]:
    """{accommodation_id: (average rating rounded to 1 dp, number of reviews)}"""
    if not accommodation_ids:
        return {}
    stmt = (
        select(Review.accommodation_id, func.avg(Review.rating), func.count(Review.id))
        .where(col(Review.accommodation_id).in_(accommodation_ids))
        .group_by(Review.accommodation_id)
    )
    return {lid: (round(float(avg), 1), int(n)) for lid, avg, n in session.exec(stmt).all()}
