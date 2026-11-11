from datetime import date
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.utilities.flash import pop_flashes

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _ttd(value) -> str:
    try:
        return f"TT${int(value):,}"
    except (TypeError, ValueError):
        return "-"


def _fmt_date(value) -> str:
    return value.strftime("%d %b %Y") if value else "-"


templates.env.filters["ttd"] = _ttd
templates.env.filters["fmt_date"] = _fmt_date
templates.env.globals["today"] = date.today


def session_user(request: Request):
    """Lightweight view of the signed-in user, kept in the session cookie."""
    data = request.session
    if not data.get("user_id"):
        return None
    return {
        "id": data["user_id"],
        "username": data.get("username", ""),
        "role": data.get("role", ""),
        "full_name": data.get("full_name", ""),
    }


def render(request: Request, name: str, status_code: int = 200, **context):
    context.setdefault("user", session_user(request))
    context["flashes"] = pop_flashes(request)
    return templates.TemplateResponse(request, name, context, status_code=status_code)
