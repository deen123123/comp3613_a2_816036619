from fastapi import APIRouter, Request

from app.dependencies import SessionDep
from app.schemas.accommodation import SORT_OPTIONS, AccommodationFilters
from app.services import accommodation_service
from app.utilities.templating import render, session_user

router = APIRouter()


@router.get("/")
def landing(request: Request, session: SessionDep):
    return render(request, "landing.html", featured=accommodation_service.featured(session))


@router.get("/accommodations")
def search_accommodations(
    request: Request,
    session: SessionDep,
    location: str = "",
    min_rent: str = "",
    max_rent: str = "",
    bedrooms: str = "",
    available_now: str = "",
    sort: str = "",
):
    """Workflow 1 - Search Accommodation: location first, then refine with the filter panel."""
    filters = AccommodationFilters.from_params(location, min_rent, max_rent, bedrooms, available_now, sort)
    cards = accommodation_service.search_accommodations(session, filters)
    return render(request, "accommodations.html", cards=cards, filters=filters, sort_options=SORT_OPTIONS)


@router.get("/accommodations/{accommodation_id}")
def accommodation_detail(accommodation_id: int, request: Request, session: SessionDep):
    """Workflow 2 - View Accommodation and Reviews."""
    detail = accommodation_service.get_detail(session, accommodation_id, session_user(request))
    return render(request, "accommodation_detail.html", detail=detail)
