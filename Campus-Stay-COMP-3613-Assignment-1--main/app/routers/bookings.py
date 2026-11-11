from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.dependencies import SessionDep, StudentDep
from app.errors import ServiceError
from app.services import booking_service, review_service
from app.utilities.flash import flash
from app.utilities.templating import render

router = APIRouter()


@router.get("/accommodations/{accommodation_id}/book")
def booking_form(accommodation_id: int, request: Request, session: SessionDep, student: StudentDep):
    """Workflow 3 - Request Accommodation Booking: the request form."""
    try:
        accommodation = booking_service.get_bookable(session, accommodation_id)
    except ServiceError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse(f"/accommodations/{accommodation_id}", status_code=303)
    return render(request, "booking_form.html", accommodation=accommodation, form={})


@router.post("/accommodations/{accommodation_id}/book")
def request_booking(
    accommodation_id: int,
    request: Request,
    session: SessionDep,
    student: StudentDep,
    start_date: str = Form(""),
    end_date: str = Form(""),
    occupants: str = Form("1"),
    message: str = Form(""),
):
    try:
        booking = booking_service.request_booking(
            session, student, accommodation_id, start_date, end_date, message, occupants
        )
    except ServiceError as exc:
        flash(request, str(exc), "error")
        try:
            accommodation = booking_service.get_bookable(session, accommodation_id)
        except ServiceError:
            return RedirectResponse(f"/accommodations/{accommodation_id}", status_code=303)
        form = {"start_date": start_date, "end_date": end_date, "occupants": occupants, "message": message}
        return render(request, "booking_form.html", status_code=400, accommodation=accommodation, form=form)
    return RedirectResponse(f"/bookings/{booking.id}/confirmation", status_code=303)


@router.get("/bookings/{booking_id}/confirmation")
def booking_confirmation(booking_id: int, request: Request, session: SessionDep, student: StudentDep):
    booking = booking_service.get_confirmation(session, student, booking_id)
    return render(request, "booking_confirmation.html", booking=booking)


@router.get("/my/bookings")
def my_bookings(request: Request, session: SessionDep, student: StudentDep):
    return render(request, "my_bookings.html", rows=booking_service.student_rows(session, student))


@router.post("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, request: Request, session: SessionDep, student: StudentDep):
    try:
        booking_service.cancel(session, student, booking_id)
        flash(request, "Booking cancelled.", "success")
    except ServiceError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse("/my/bookings", status_code=303)


@router.get("/bookings/{booking_id}/review")
def review_page(booking_id: int, request: Request, session: SessionDep, student: StudentDep):
    try:
        booking = review_service.get_reviewable(session, student, booking_id)
    except ServiceError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/my/bookings", status_code=303)
    return render(request, "review_form.html", booking=booking, form={})


@router.post("/bookings/{booking_id}/review")
def submit_review(
    booking_id: int,
    request: Request,
    session: SessionDep,
    student: StudentDep,
    rating: str = Form(""),
    comment: str = Form(""),
):
    try:
        review = review_service.create_review(session, student, booking_id, rating, comment)
    except ServiceError as exc:
        flash(request, str(exc), "error")
        try:
            booking = review_service.get_reviewable(session, student, booking_id)
        except ServiceError:
            return RedirectResponse("/my/bookings", status_code=303)
        return render(
            request, "review_form.html", status_code=400, booking=booking,
            form={"rating": rating, "comment": comment},
        )
    flash(request, "Thanks! Your review is live.", "success")
    return RedirectResponse(f"/accommodations/{review.accommodation_id}#reviews", status_code=303)
