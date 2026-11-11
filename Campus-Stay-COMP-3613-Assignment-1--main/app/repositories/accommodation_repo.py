from typing import List, Optional

from sqlalchemy import or_
from sqlmodel import Session, col, select

from app.models import Accommodation, Availability
from app.repositories.base import save
from app.schemas.accommodation import AccommodationFilters


def get(session: Session, accommodation_id: int) -> Optional[Accommodation]:
    return session.get(Accommodation, accommodation_id)


def get_many(session: Session, ids: List[int]) -> List[Accommodation]:
    if not ids:
        return []
    return list(session.exec(select(Accommodation).where(col(Accommodation.id).in_(ids))).all())


def search(session: Session, filters: AccommodationFilters) -> List[Accommodation]:
    """Public search: only admin-verified accommodation is shown to students."""
    stmt = select(Accommodation).where(col(Accommodation.is_verified) == True)  # noqa: E712
    if filters.location:
        term = f"%{filters.location}%"
        stmt = stmt.where(
            or_(
                col(Accommodation.area).ilike(term),
                col(Accommodation.address).ilike(term),
                col(Accommodation.title).ilike(term),
                col(Accommodation.description).ilike(term),
            )
        )
    if filters.min_rent is not None:
        stmt = stmt.where(col(Accommodation.rent) >= filters.min_rent)
    if filters.max_rent is not None:
        stmt = stmt.where(col(Accommodation.rent) <= filters.max_rent)
    if filters.bedrooms is not None:
        stmt = stmt.where(col(Accommodation.bedrooms) >= filters.bedrooms)
    if filters.available_now:
        stmt = stmt.where(Accommodation.availability_status == Availability.AVAILABLE)
    return list(session.exec(stmt.order_by(col(Accommodation.rent))).all())


def featured(session: Session, limit: int = 3) -> List[Accommodation]:
    stmt = (
        select(Accommodation)
        .where(
            col(Accommodation.is_verified) == True,  # noqa: E712
            Accommodation.availability_status == Availability.AVAILABLE,
        )
        .order_by(col(Accommodation.distance_km))
        .limit(limit)
    )
    return list(session.exec(stmt).all())


def list_for_landlord(session: Session, landlord_id: int) -> List[Accommodation]:
    stmt = select(Accommodation).where(Accommodation.landlord_id == landlord_id).order_by(col(Accommodation.id).desc())
    return list(session.exec(stmt).all())


def pending_verification(session: Session) -> List[Accommodation]:
    stmt = (
        select(Accommodation)
        .where(col(Accommodation.is_verified) == False)  # noqa: E712
        .order_by(col(Accommodation.created_at))
    )
    return list(session.exec(stmt).all())


def verified(session: Session) -> List[Accommodation]:
    stmt = select(Accommodation).where(col(Accommodation.is_verified) == True).order_by(col(Accommodation.id))  # noqa: E712
    return list(session.exec(stmt).all())


def add(session: Session, accommodation: Accommodation) -> Accommodation:
    return save(session, accommodation)
