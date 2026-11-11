from sqlmodel import Session

from app.errors import ForbiddenError, NotFoundError, ServiceError
from app.models import Booking, Review, User
from app.repositories import booking_repo, review_repo
from app.utilities.validators import clean, parse_int


def get_reviewable(session: Session, student: User, booking_id: int) -> Booking:
    booking = booking_repo.get(session, booking_id)
    if booking is None:
        raise NotFoundError()
    if booking.student_id != student.id:
        raise ForbiddenError()
    if not booking.stay_ended:
        raise ServiceError("You can review a place once your stay has ended.")
    if review_repo.get_by_booking(session, booking.id):
        raise ServiceError("You have already reviewed this stay.")
    return booking


def create_review(session: Session, student: User, booking_id: int, rating_raw: str, comment: str) -> Review:
    booking = get_reviewable(session, student, booking_id)
    rating = parse_int(rating_raw, "Rating", 1, 5)
    comment = clean(comment)
    if len(comment) < 10:
        raise ServiceError("Tell future tenants a little more (at least 10 characters).")
    review = Review(
        accommodation_id=booking.accommodation_id,
        student_id=student.id,
        booking_id=booking.id,
        rating=rating,
        comment=comment[:1000],
    )
    return review_repo.add(session, review)
