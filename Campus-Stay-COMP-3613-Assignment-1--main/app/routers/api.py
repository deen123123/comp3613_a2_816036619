from fastapi import APIRouter
from sqlalchemy import text

from app.dependencies import SessionDep
from app.schemas.accommodation import AccommodationFilters
from app.services import accommodation_service

router = APIRouter()


@router.get("/health")
def health(session: SessionDep):
    session.connection().execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/api/accommodations")
def api_accommodations(
    session: SessionDep,
    location: str = "",
    min_rent: str = "",
    max_rent: str = "",
    bedrooms: str = "",
    available_now: str = "",
    sort: str = "",
):
    filters = AccommodationFilters.from_params(location, min_rent, max_rent, bedrooms, available_now, sort)
    return [c.to_dict() for c in accommodation_service.search_accommodations(session, filters)]
