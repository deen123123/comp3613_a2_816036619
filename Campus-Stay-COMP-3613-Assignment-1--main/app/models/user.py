from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.utilities.clock import utcnow

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.accommodation import Accommodation
    from app.models.review import Review


class Role:
    STUDENT = "student"
    LANDLORD = "landlord"
    ADMIN = "admin"
    SIGNUP = (STUDENT, LANDLORD)  # roles a visitor may pick when registering


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(default="", max_length=120)
    phone: str = Field(default="", max_length=30)
    password_hash: str
    role: str = Field(default=Role.STUDENT, index=True, max_length=20)
    created_at: datetime = Field(default_factory=utcnow)

    accommodations: List["Accommodation"] = Relationship(back_populates="landlord")
    bookings: List["Booking"] = Relationship(back_populates="student")
    reviews: List["Review"] = Relationship(back_populates="student")

    @property
    def display_name(self) -> str:
        return self.full_name or self.username
