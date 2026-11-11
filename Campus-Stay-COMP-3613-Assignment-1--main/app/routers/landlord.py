from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.dependencies import LandlordDep, SessionDep
from app.errors import ServiceError
from app.models import AMENITY_LABELS, RoomType
from app.services import booking_service, accommodation_service
from app.utilities.flash import flash
from app.utilities.templating import render

router = APIRouter(prefix="/landlord")


@router.get("")
def dashboard(request: Request, session: SessionDep, landlord: LandlordDep):
    return render(request, "landlord_dashboard.html", data=booking_service.landlord_dashboard(session, landlord))


@router.post("/bookings/{booking_id}/decide")
def decide(
    booking_id: int,
    request: Request,
    session: SessionDep,
    landlord: LandlordDep,
    decision: str = Form(""),
    note: str = Form(""),
):
    try:
        _, auto = booking_service.decide(session, landlord, booking_id, decision, note)
        word = "approved" if decision == "approve" else "declined"
        message = f"Request {word}."
        if auto:
            message += f" {auto} overlapping request(s) were closed automatically."
        flash(request, message, "success")
    except ServiceError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse("/landlord", status_code=303)


def _form_context(**extra):
    return {"room_types": RoomType.LABELS, "amenity_labels": AMENITY_LABELS, **extra}


@router.get("/accommodations/new")
def new_accommodation_page(request: Request, landlord: LandlordDep):
    return render(request, "accommodation_form.html", **_form_context(accommodation=None, form={"amenities": []}))


async def _read_form(request: Request) -> dict:
    data = await request.form()
    form = {key: data.get(key, "") for key in data.keys()}
    form["amenities"] = data.getlist("amenities")
    return form


@router.post("/accommodations/new")
async def create_accommodation(request: Request, session: SessionDep, landlord: LandlordDep):
    form = await _read_form(request)
    try:
        accommodation = accommodation_service.create_accommodation(session, landlord, form)
    except ServiceError as exc:
        flash(request, str(exc), "error")
        return render(request, "accommodation_form.html", status_code=400, **_form_context(accommodation=None, form=form))
    flash(request, f"“{accommodation.title}” saved. It goes live once an admin verifies it.", "success")
    return RedirectResponse("/landlord", status_code=303)


@router.get("/accommodations/{accommodation_id}/edit")
def edit_accommodation_page(accommodation_id: int, request: Request, session: SessionDep, landlord: LandlordDep):
    accommodation = accommodation_service.get_owned(session, landlord, accommodation_id)
    form = {
        "title": accommodation.title, "description": accommodation.description, "area": accommodation.area,
        "address": accommodation.address, "room_type": accommodation.room_type,
        "rent": accommodation.rent, "bedrooms": accommodation.bedrooms,
        "max_tenants": accommodation.max_tenants, "distance_km": accommodation.distance_km,
        "available_from": accommodation.available_from.isoformat() if accommodation.available_from else "",
        "image_url": accommodation.image_url, "amenities": accommodation.amenity_keys,
    }
    return render(request, "accommodation_form.html", **_form_context(accommodation=accommodation, form=form))


@router.post("/accommodations/{accommodation_id}/edit")
async def update_accommodation(accommodation_id: int, request: Request, session: SessionDep, landlord: LandlordDep):
    form = await _read_form(request)
    try:
        accommodation = accommodation_service.update_accommodation(session, landlord, accommodation_id, form)
    except ServiceError as exc:
        flash(request, str(exc), "error")
        accommodation = accommodation_service.get_owned(session, landlord, accommodation_id)
        return render(request, "accommodation_form.html", status_code=400, **_form_context(accommodation=accommodation, form=form))
    flash(request, "Accommodation updated.", "success")
    return RedirectResponse("/landlord", status_code=303)


@router.post("/accommodations/{accommodation_id}/availability")
def toggle_accommodation(accommodation_id: int, request: Request, session: SessionDep, landlord: LandlordDep):
    accommodation = accommodation_service.toggle_availability(session, landlord, accommodation_id)
    flash(request, f"Marked {accommodation.availability_status.lower()}.", "success")
    return RedirectResponse("/landlord", status_code=303)
