from datetime import date
from typing import List, Optional

from sqlmodel import Session, col, select

from app.models import Booking, BookingStatus, Accommodation
from app.repositories.base import save


def get(session: Session, booking_id: int) -> Optional[Booking]:
    return session.get(Booking, booking_id)


def add(session: Session, booking: Booking) -> Booking:
    return save(session, booking)


def save_all(session: Session, *bookings: Booking) -> None:
    save(session, *bookings)


def overlapping(
    session: Session,
    accommodation_id: int,
    start: date,
    end: date,
    statuses: List[str],
    exclude_id: Optional[int] = None,
    student_id: Optional[int] = None,
) -> List[Booking]:
    """Bookings on a accommodation that share at least one night with [start, end)."""
    stmt = select(Booking).where(
        Booking.accommodation_id == accommodation_id,
        col(Booking.status).in_(statuses),
        col(Booking.start_date) < end,
        col(Booking.end_date) > start,
    )
    if exclude_id is not None:
        stmt = stmt.where(Booking.id != exclude_id)
    if student_id is not None:
        stmt = stmt.where(Booking.student_id == student_id)
    return list(session.exec(stmt).all())


def approved_from(session: Session, accommodation_id: int, since: date) -> List[Booking]:
    stmt = (
        select(Booking)
        .where(
            Booking.accommodation_id == accommodation_id,
            Booking.status == BookingStatus.APPROVED,
            col(Booking.end_date) > since,
        )
        .order_by(col(Booking.start_date))
    )
    return list(session.exec(stmt).all())


def for_student(session: Session, student_id: int) -> List[Booking]:
    stmt = select(Booking).where(Booking.student_id == student_id).order_by(col(Booking.start_date).desc())
    return list(session.exec(stmt).all())


def for_landlord(session: Session, landlord_id: int) -> List[Booking]:
    stmt = (
        select(Booking)
        .join(Accommodation, Booking.accommodation_id == Accommodation.id)
        .where(Accommodation.landlord_id == landlord_id)
        .order_by(col(Booking.created_at).desc())
    )
    return list(session.exec(stmt).all())
