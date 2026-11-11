"""Ops console at /config. Disabled unless CONFIG_PASSWORD is set."""

import hmac

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.dependencies import SessionDep
from app.errors import NotFoundError
from app.services import admin_service
from app.utilities.flash import flash
from app.utilities.templating import render

router = APIRouter()


def _require_enabled() -> None:
    if not settings.config_password:
        raise NotFoundError()


@router.get("/config")
def config_page(request: Request, session: SessionDep):
    _require_enabled()
    if not request.session.get("config_ok"):
        return render(request, "config.html", authed=False)
    info = {
        "ENV": settings.env,
        "Database": settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
        "Port": settings.port,
    }
    return render(request, "config.html", authed=True, info=info, stats=admin_service.overview(session))


@router.post("/config")
def config_login(request: Request, password: str = Form("")):
    _require_enabled()
    if hmac.compare_digest(password.encode(), settings.config_password.encode()):
        request.session["config_ok"] = True
    else:
        flash(request, "Wrong password.", "error")
    return RedirectResponse("/config", status_code=303)
