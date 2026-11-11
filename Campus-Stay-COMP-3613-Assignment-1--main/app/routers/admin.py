from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.dependencies import AdminDep, SessionDep
from app.services import admin_service, accommodation_service
from app.utilities.flash import flash
from app.utilities.templating import render

router = APIRouter(prefix="/admin")


@router.get("")
def admin_home(request: Request, session: SessionDep, admin: AdminDep):
    return render(
        request,
        "admin.html",
        queue=accommodation_service.verification_queue(session),
        verified=accommodation_service.verified_accommodations(session),
        stats=admin_service.overview(session),
    )


@router.post("/accommodations/{accommodation_id}/verify")
def verify_accommodation(
    accommodation_id: int, request: Request, session: SessionDep, admin: AdminDep, verified: str = Form("1")
):
    accommodation = accommodation_service.set_verified(session, accommodation_id, verified == "1")
    state = "verified and now searchable" if accommodation.is_verified else "unverified and hidden from search"
    flash(request, f"“{accommodation.title}” is {state}.", "success")
    return RedirectResponse("/admin", status_code=303)
