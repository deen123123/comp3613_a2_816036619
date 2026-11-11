from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.utilities.clock import utcnow

if TYPE_CHECKING:
    from app.models.accommodation import Accommodation
    from app.models.user import User


class Review(SQLModel, table=True):
    """One review per completed booking, so every review is a verified stay."""

    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    accommodation_id: int = Field(foreign_key="accommodations.id", index=True)
    student_id: int = Field(foreign_key="users.id", index=True)
    booking_id: int = Field(foreign_key="bookings.id", unique=True)
    rating: int
    comment: str = Field(default="", max_length=1000)
    created_at: datetime = Field(default_factory=utcnow)

    accommodation: Optional["Accommodation"] = Relationship(back_populates="reviews")
    student: Optional["User"] = Relationship(back_populates="reviews")
