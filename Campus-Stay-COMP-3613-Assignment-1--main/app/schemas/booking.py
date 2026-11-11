from dataclasses import dataclass, field
from typing import List

from app.models import Booking


@dataclass
class BookingRow:
    booking: Booking
    reviewed: bool = False
    can_cancel: bool = False
    can_review: bool = False


@dataclass
class LandlordDashboard:
    accommodations: list = field(default_factory=list)
    pending: List[Booking] = field(default_factory=list)
    upcoming: List[Booking] = field(default_factory=list)
    history: List[Booking] = field(default_factory=list)
