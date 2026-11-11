from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.utilities.clock import utcnow

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.review import Review
    from app.models.user import User


class Availability:
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"


class RoomType:
    ROOM = "room"
    SHARED = "shared"
    STUDIO = "studio"
    APARTMENT = "apartment"
    ALL = (ROOM, SHARED, STUDIO, APARTMENT)
    LABELS = {
        ROOM: "Private room",
        SHARED: "Shared house",
        STUDIO: "Studio",
        APARTMENT: "Apartment",
    }


AMENITY_LABELS = {
    "wifi": "Wi-Fi",
    "water": "Water included",
    "electricity": "Electricity included",
    "air_conditioning": "Air conditioning",
    "furnished": "Furnished",
    "kitchen": "Kitchen access",
    "laundry": "Laundry",
    "parking": "Parking",
    "security": "Security / gated",
    "study_desk": "Study desk",
}


def pack_amenities(keys) -> str:
    """Store as ',wifi,water,' so a LIKE '%,wifi,%' match is exact."""
    valid = [k for k in AMENITY_LABELS if k in set(keys or [])]
    return "," + ",".join(valid) + "," if valid else ","


class Accommodation(SQLModel, table=True):
    __tablename__ = "accommodations"

    id: Optional[int] = Field(default=None, primary_key=True)
    landlord_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=150)
    description: str = Field(default="", max_length=4000)
    address: str = Field(default="", max_length=255)
    area: str = Field(default="", index=True, max_length=80)
    room_type: str = Field(default=RoomType.ROOM, index=True, max_length=20)
    rent: int = Field(index=True)
    bedrooms: int = Field(default=1)
    max_tenants: int = Field(default=1)
    distance_km: float = Field(default=1.0)
    amenities: str = Field(default=",", max_length=500)
    image_url: str = Field(default="", max_length=500)
    available_from: Optional[date] = Field(default=None)
    is_verified: bool = Field(default=False, index=True)
    availability_status: str = Field(default=Availability.AVAILABLE, index=True, max_length=20)
    created_at: datetime = Field(default_factory=utcnow)

    landlord: Optional["User"] = Relationship(back_populates="accommodations")
    bookings: List["Booking"] = Relationship(back_populates="accommodation")
    reviews: List["Review"] = Relationship(back_populates="accommodation")

    @property
    def is_available(self) -> bool:
        return self.availability_status == Availability.AVAILABLE

    @property
    def amenity_keys(self) -> List[str]:
        return [a for a in (self.amenities or "").split(",") if a]

    @property
    def amenity_list(self) -> List[str]:
        return [AMENITY_LABELS.get(a, a) for a in self.amenity_keys]

    @property
    def room_type_label(self) -> str:
        return RoomType.LABELS.get(self.room_type, self.room_type)

