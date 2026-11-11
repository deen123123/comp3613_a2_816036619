from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.utilities.clock import utcnow

if TYPE_CHECKING:
    from app.models.accommodation import Accommodation
    from app.models.user import User


class BookingStatus:
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class Booking(SQLModel, table=True):
    """A student's request to rent a accommodation. Start is inclusive, end is the check-out day."""

    __tablename__ = "bookings"

    id: Optional[int] = Field(default=None, primary_key=True)
    accommodation_id: int = Field(foreign_key="accommodations.id", index=True)
    student_id: int = Field(foreign_key="users.id", index=True)
    start_date: date
    end_date: date
    occupants: int = Field(default=1)
    message: str = Field(default="", max_length=500)
    landlord_note: str = Field(default="", max_length=300)
    status: str = Field(default=BookingStatus.PENDING, index=True, max_length=20)
    created_at: datetime = Field(default_factory=utcnow)
    decided_at: Optional[datetime] = Field(default=None)

    accommodation: Optional["Accommodation"] = Relationship(back_populates="bookings")
    student: Optional["User"] = Relationship(back_populates="bookings")

    @property
    def reference(self) -> str:
        return f"CS-{10000 + (self.id or 0)}"

    @property
    def stay_ended(self) -> bool:
        return self.status == BookingStatus.APPROVED and self.end_date <= date.today()

    @property
    def display_status(self) -> str:
        if self.status == BookingStatus.APPROVED:
            today = date.today()
            if self.end_date <= today:
                return "completed"
            if self.start_date <= today:
                return "active"
        return self.status

    @property
    def nights(self) -> int:
        return (self.end_date - self.start_date).days
