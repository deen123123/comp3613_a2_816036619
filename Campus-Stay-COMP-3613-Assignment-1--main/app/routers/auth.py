from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.dependencies import OptionalUserDep, SessionDep
from app.errors import ServiceError
from app.models import Role
from app.services import auth_service
from app.utilities.flash import flash
from app.utilities.templating import render

router = APIRouter()


def _safe_next(target: str, fallback: str) -> str:
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


def _sign_in(request: Request, user) -> None:
    request.session.clear()
    request.session.update(
        user_id=user.id, username=user.username, role=user.role, full_name=user.display_name
    )


@router.get("/login")
def login_page(request: Request, user: OptionalUserDep, next: str = ""):
    if user:
        return RedirectResponse(auth_service.home_path(user.role), status_code=303)
    return render(request, "login.html", next=next)


@router.post("/login")
def login(
    request: Request,
    session: SessionDep,
    username: str = Form(""),
    password: str = Form(""),
    next: str = Form(""),
):
    try:
        user = auth_service.authenticate(session, username, password)
    except ServiceError as exc:
        flash(request, str(exc), "error")
        return render(request, "login.html", status_code=400, next=next, username=username)
    _sign_in(request, user)
    flash(request, f"Welcome back, {user.display_name}.", "success")
    return RedirectResponse(_safe_next(next, auth_service.home_path(user.role)), status_code=303)


@router.get("/register")
def register_page(request: Request, user: OptionalUserDep):
    if user:
        return RedirectResponse(auth_service.home_path(user.role), status_code=303)
    return render(request, "register.html", form={"role": Role.STUDENT})


@router.post("/register")
def register(
    request: Request,
    session: SessionDep,
    username: str = Form(""),
    email: str = Form(""),
    full_name: str = Form(""),
    phone: str = Form(""),
    password: str = Form(""),
    role: str = Form(Role.STUDENT),
):
    form = {"username": username, "email": email, "full_name": full_name, "phone": phone, "role": role}
    try:
        user = auth_service.register(session, username, email, password, full_name, role, phone)
    except ServiceError as exc:
        flash(request, str(exc), "error")
        return render(request, "register.html", status_code=400, form=form)
    _sign_in(request, user)
    flash(request, "Account created. Welcome to Campus Stay!", "success")
    return RedirectResponse(auth_service.home_path(user.role), status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "You have been signed out.", "info")
    return RedirectResponse("/", status_code=303)


@router.get("/dashboard")
def dashboard(user: OptionalUserDep):
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse(auth_service.home_path(user.role), status_code=303)
