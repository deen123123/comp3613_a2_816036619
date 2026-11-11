from sqlmodel import Session

from app.models import Booking, Accommodation, Review, User
from app.repositories.base import count


def overview(session: Session) -> dict:
    return {
        "users": count(session, User),
        "accommodations": count(session, Accommodation),
        "bookings": count(session, Booking),
        "reviews": count(session, Review),
    }
