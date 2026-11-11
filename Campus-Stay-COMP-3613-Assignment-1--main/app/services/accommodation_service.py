from datetime import date
from typing import List, Optional

from sqlmodel import Session

from app.errors import ForbiddenError, NotFoundError, ServiceError
from app.models import AMENITY_LABELS, Accommodation, Availability, Role, RoomType, User, pack_amenities
from app.repositories import booking_repo, accommodation_repo, review_repo
from app.schemas.accommodation import AccommodationCard, AccommodationDetail, AccommodationFilters
from app.utilities.validators import (
    clean,
    parse_float,
    parse_int,
    parse_optional_date,
)


# ---------- Workflow 1 & 2: search and view accommodation (student) ----------

def _cards(session: Session, accommodations: List[Accommodation]) -> List[AccommodationCard]:
    stats = review_repo.rating_stats(session, [item.id for item in accommodations])
    cards = []
    for item in accommodations:
        avg, n = stats.get(item.id, (0.0, 0))
        cards.append(AccommodationCard(accommodation=item, avg_rating=avg, review_count=n))
    return cards


def search_accommodations(session: Session, filters: AccommodationFilters) -> List[AccommodationCard]:
    cards = _cards(session, accommodation_repo.search(session, filters))
    if filters.sort == "price_asc":
        cards.sort(key=lambda c: c.accommodation.rent)
    elif filters.sort == "price_desc":
        cards.sort(key=lambda c: -c.accommodation.rent)
    elif filters.sort == "distance":
        cards.sort(key=lambda c: c.accommodation.distance_km)
    elif filters.sort == "rating":
        cards.sort(key=lambda c: (-c.avg_rating, -c.review_count))
    else:  # recommended: well reviewed first, then close to campus
        cards.sort(key=lambda c: (-c.avg_rating, c.accommodation.distance_km))
    return cards


def featured(session: Session) -> List[AccommodationCard]:
    return _cards(session, accommodation_repo.featured(session))


def get_detail(session: Session, accommodation_id: int, viewer: Optional[dict]) -> AccommodationDetail:
    accommodation = accommodation_repo.get(session, accommodation_id)
    if accommodation is None:
        raise NotFoundError()
    is_owner = bool(viewer and viewer["id"] == accommodation.landlord_id)
    is_admin = bool(viewer and viewer["role"] == Role.ADMIN)
    public = accommodation.is_verified
    if not public and not (is_owner or is_admin):
        raise NotFoundError()
    stats = review_repo.rating_stats(session, [accommodation.id]).get(accommodation.id, (0.0, 0))
    blocked = [(b.start_date, b.end_date) for b in booking_repo.approved_from(session, accommodation.id, date.today())]
    return AccommodationDetail(
        accommodation=accommodation,
        avg_rating=stats[0],
        review_count=stats[1],
        reviews=review_repo.for_accommodation(session, accommodation.id),
        blocked_ranges=blocked,
        is_owner=is_owner,
        can_request=bool(viewer and viewer["role"] == Role.STUDENT and public),
    )


# ---------- Landlord: post / edit accommodations (supporting behaviour) ----------

def _apply_form(accommodation: Accommodation, form: dict) -> None:
    title = clean(form.get("title"))
    if len(title) < 5:
        raise ServiceError("Give the accommodation a title of at least 5 characters.")
    description = clean(form.get("description"))
    if len(description) < 20:
        raise ServiceError("Describe the place in at least 20 characters.")
    area = clean(form.get("area"))
    address = clean(form.get("address"))
    if not area or not address:
        raise ServiceError("Area and address are required.")
    room_type = clean(form.get("room_type"))
    if room_type not in RoomType.ALL:
        raise ServiceError("Choose a valid room type.")
    image_url = clean(form.get("image_url"))
    if image_url and not image_url.startswith(("http://", "https://")):
        raise ServiceError("Image URL must start with http:// or https://")
    chosen = [a for a in (form.get("amenities") or []) if a in AMENITY_LABELS]

    accommodation.title = title[:150]
    accommodation.description = description[:4000]
    accommodation.area = area[:80]
    accommodation.address = address[:255]
    accommodation.room_type = room_type
    accommodation.rent = parse_int(form.get("rent"), "Monthly price", 1, 100000)
    accommodation.bedrooms = parse_int(form.get("bedrooms"), "Bedrooms", 1, 10)
    accommodation.max_tenants = parse_int(form.get("max_tenants"), "Sleeps", 1, 12)
    accommodation.distance_km = parse_float(form.get("distance_km"), "Distance to campus", 0, 100)
    accommodation.available_from = parse_optional_date(form.get("available_from"), "Available from")
    accommodation.image_url = image_url[:500]
    accommodation.amenities = pack_amenities(chosen)


def create_accommodation(session: Session, landlord: User, form: dict) -> Accommodation:
    accommodation = Accommodation(landlord_id=landlord.id, title="", rent=0)
    _apply_form(accommodation, form)
    accommodation.is_verified = False  # trusted accommodations: an admin must verify first
    return accommodation_repo.add(session, accommodation)


def get_owned(session: Session, landlord: User, accommodation_id: int) -> Accommodation:
    accommodation = accommodation_repo.get(session, accommodation_id)
    if accommodation is None:
        raise NotFoundError()
    if accommodation.landlord_id != landlord.id:
        raise ForbiddenError()
    return accommodation


def update_accommodation(session: Session, landlord: User, accommodation_id: int, form: dict) -> Accommodation:
    accommodation = get_owned(session, landlord, accommodation_id)
    _apply_form(accommodation, form)
    return accommodation_repo.add(session, accommodation)


def toggle_availability(session: Session, landlord: User, accommodation_id: int) -> Accommodation:
    accommodation = get_owned(session, landlord, accommodation_id)
    accommodation.availability_status = (
        Availability.UNAVAILABLE if accommodation.is_available else Availability.AVAILABLE
    )
    return accommodation_repo.add(session, accommodation)


# ---------- Admin: verification queue ----------

def verification_queue(session: Session) -> List[Accommodation]:
    return accommodation_repo.pending_verification(session)


def verified_accommodations(session: Session) -> List[Accommodation]:
    return accommodation_repo.verified(session)


def set_verified(session: Session, accommodation_id: int, verified: bool) -> Accommodation:
    accommodation = accommodation_repo.get(session, accommodation_id)
    if accommodation is None:
        raise NotFoundError()
    accommodation.is_verified = verified
    return accommodation_repo.add(session, accommodation)
