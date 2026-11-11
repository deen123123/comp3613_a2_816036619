from datetime import date
from typing import List, Tuple

from sqlmodel import Session

from app.errors import ForbiddenError, NotFoundError, ServiceError
from app.models import Booking, BookingStatus, User
from app.repositories import booking_repo, accommodation_repo, review_repo
from app.schemas.booking import BookingRow, LandlordDashboard
from app.schemas.accommodation import AccommodationCard
from app.utilities.clock import utcnow
from app.utilities.validators import clean, parse_date, parse_int

MIN_STAY_DAYS = 28
MAX_STAY_DAYS = 366


# ---------- Workflow 2a: student requests a booking ----------

def get_bookable(session: Session, accommodation_id: int):
    accommodation = accommodation_repo.get(session, accommodation_id)
    if accommodation is None or not accommodation.is_verified:
        raise NotFoundError()
    if not accommodation.is_available:
        raise ServiceError("This place is currently unavailable.")
    return accommodation


def get_confirmation(session: Session, student: User, booking_id: int) -> Booking:
    booking = booking_repo.get(session, booking_id)
    if booking is None:
        raise NotFoundError()
    if booking.student_id != student.id:
        raise ForbiddenError()
    return booking


def request_booking(
    session: Session, student: User, accommodation_id: int, start_raw: str, end_raw: str,
    message: str, occupants_raw: str = "1",
) -> Booking:
    accommodation = get_bookable(session, accommodation_id)
    occupants = parse_int(occupants_raw, "Occupants", 1, max(accommodation.max_tenants, 1))

    start = parse_date(start_raw, "Move-in date")
    end = parse_date(end_raw, "Move-out date")
    if start < date.today():
        raise ServiceError("Move-in date cannot be in the past.")
    if end <= start:
        raise ServiceError("Move-out must be after move-in.")
    length = (end - start).days
    if length < MIN_STAY_DAYS:
        raise ServiceError(f"Stays are monthly: please request at least {MIN_STAY_DAYS} days.")
    if length > MAX_STAY_DAYS:
        raise ServiceError(f"Stays are limited to {MAX_STAY_DAYS} days per request.")
    if accommodation.available_from and start < accommodation.available_from:
        raise ServiceError(f"This place is available from {accommodation.available_from:%d %b %Y}.")

    if booking_repo.overlapping(session, accommodation.id, start, end, [BookingStatus.APPROVED]):
        raise ServiceError("Sorry, that place is already booked for part of those dates.")
    if booking_repo.overlapping(
        session, accommodation.id, start, end,
        [BookingStatus.PENDING, BookingStatus.APPROVED], student_id=student.id,
    ):
        raise ServiceError("You already have a request for this place on overlapping dates.")

    booking = Booking(
        accommodation_id=accommodation.id,
        student_id=student.id,
        start_date=start,
        end_date=end,
        occupants=occupants,
        message=clean(message)[:500],
    )
    return booking_repo.add(session, booking)


def _can_cancel(booking: Booking) -> bool:
    if booking.status == BookingStatus.PENDING:
        return True
    return booking.status == BookingStatus.APPROVED and booking.start_date > date.today()


def student_rows(session: Session, student: User) -> List[BookingRow]:
    bookings = booking_repo.for_student(session, student.id)
    reviewed = review_repo.reviewed_booking_ids(session, [b.id for b in bookings])
    return [
        BookingRow(
            booking=b,
            reviewed=b.id in reviewed,
            can_cancel=_can_cancel(b),
            can_review=b.stay_ended and b.id not in reviewed,
        )
        for b in bookings
    ]


def cancel(session: Session, student: User, booking_id: int) -> Booking:
    booking = booking_repo.get(session, booking_id)
    if booking is None:
        raise NotFoundError()
    if booking.student_id != student.id:
        raise ForbiddenError()
    if not _can_cancel(booking):
        raise ServiceError("This booking can no longer be cancelled.")
    booking.status = BookingStatus.CANCELLED
    booking.decided_at = utcnow()
    return booking_repo.add(session, booking)


# ---------- Workflow 2b: landlord manages requests ----------

def landlord_dashboard(session: Session, landlord: User) -> LandlordDashboard:
    accommodations = accommodation_repo.list_for_landlord(session, landlord.id)
    stats = review_repo.rating_stats(session, [item.id for item in accommodations])
    dashboard = LandlordDashboard(
        accommodations=[
            AccommodationCard(item, *stats.get(item.id, (0.0, 0))) for item in accommodations
        ]
    )
    for booking in booking_repo.for_landlord(session, landlord.id):
        if booking.status == BookingStatus.PENDING:
            dashboard.pending.append(booking)
        elif booking.status == BookingStatus.APPROVED and not booking.stay_ended:
            dashboard.upcoming.append(booking)
        else:
            dashboard.history.append(booking)
    dashboard.upcoming.sort(key=lambda b: b.start_date)
    return dashboard


def decide(
    session: Session, landlord: User, booking_id: int, decision: str, note: str
) -> Tuple[Booking, int]:
    """Approve or decline a pending request. Returns (booking, auto-declined count)."""
    booking = booking_repo.get(session, booking_id)
    if booking is None:
        raise NotFoundError()
    if booking.accommodation.landlord_id != landlord.id:
        raise ForbiddenError()
    if booking.status != BookingStatus.PENDING:
        raise ServiceError("This request has already been handled.")

    now = utcnow()
    booking.landlord_note = clean(note)[:300]
    booking.decided_at = now
    changed = [booking]
    auto_declined = 0

    if decision == "approve":
        clash = booking_repo.overlapping(
            session, booking.accommodation_id, booking.start_date, booking.end_date,
            [BookingStatus.APPROVED], exclude_id=booking.id,
        )
        if clash:
            raise ServiceError("Cannot approve: it overlaps an approved booking.")
        booking.status = BookingStatus.APPROVED
        # The room is now taken: close competing requests for the same nights.
        for other in booking_repo.overlapping(
            session, booking.accommodation_id, booking.start_date, booking.end_date,
            [BookingStatus.PENDING], exclude_id=booking.id,
        ):
            other.status = BookingStatus.DECLINED
            other.landlord_note = "Another student was approved for overlapping dates."
            other.decided_at = now
            changed.append(other)
            auto_declined += 1
    elif decision == "decline":
        booking.status = BookingStatus.DECLINED
    else:
        raise ServiceError("Unknown decision.")

    booking_repo.save_all(session, *changed)
    return booking, auto_declined
