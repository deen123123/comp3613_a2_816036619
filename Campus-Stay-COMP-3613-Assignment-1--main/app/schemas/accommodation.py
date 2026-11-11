from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from app.models import Accommodation, Review
from app.utilities.validators import clean, to_int_or_none

SORT_OPTIONS = {
    "recommended": "Recommended",
    "price_asc": "Rent: low to high",
    "price_desc": "Rent: high to low",
    "distance": "Closest to campus",
    "rating": "Best rated",
}


@dataclass
class AccommodationFilters:
    """Search form: location first, then the filter panel (rent range, bedrooms, available now)."""

    location: str = ""
    min_rent: Optional[int] = None
    max_rent: Optional[int] = None
    bedrooms: Optional[int] = None  # minimum number of bedrooms
    available_now: bool = False
    sort: str = "recommended"

    @classmethod
    def from_params(
        cls,
        location: str = "",
        min_rent: str = "",
        max_rent: str = "",
        bedrooms: str = "",
        available_now: str = "",
        sort: str = "",
    ) -> "AccommodationFilters":
        sort = clean(sort)
        return cls(
            location=clean(location),
            min_rent=to_int_or_none(min_rent),
            max_rent=to_int_or_none(max_rent),
            bedrooms=to_int_or_none(bedrooms),
            available_now=clean(available_now).lower() in ("1", "on", "true", "yes"),
            sort=sort if sort in SORT_OPTIONS else "recommended",
        )


@dataclass
class AccommodationCard:
    accommodation: Accommodation
    avg_rating: float = 0.0
    review_count: int = 0

    @property
    def stars(self) -> int:
        return int(round(self.avg_rating))

    def to_dict(self) -> dict:
        item = self.accommodation
        return {
            "id": item.id,
            "title": item.title,
            "area": item.area,
            "address": item.address,
            "rent": item.rent,
            "bedrooms": item.bedrooms,
            "availability_status": item.availability_status,
            "is_verified": item.is_verified,
            "avg_rating": self.avg_rating,
            "review_count": self.review_count,
        }


@dataclass
class AccommodationDetail:
    accommodation: Accommodation
    avg_rating: float
    review_count: int
    reviews: List[Review]
    blocked_ranges: List[Tuple[date, date]]
    is_owner: bool
    can_request: bool

    @property
    def stars(self) -> int:
        return int(round(self.avg_rating))
