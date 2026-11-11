from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import create_db
from app.errors import ForbiddenError, LoginRequired, NotFoundError
from app.routers import admin, api, auth, bookings, landlord, accommodations, ops
from app.utilities.templating import render

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db(drop=False)  # safe: only creates missing tables
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    max_age=60 * 60 * 24 * 7,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

for module in (api, auth, accommodations, bookings, landlord, admin, ops):
    app.include_router(module.router)


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(f"/login?next={quote(exc.next_url, safe='')}", status_code=303)


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError):
    return render(
        request, "error.html", status_code=403,
        code=403, heading="Not allowed", detail="Your account type cannot open this page.",
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return render(
        request, "error.html", status_code=404,
        code=404, heading="Not found", detail="We couldn't find what you were looking for.",
    )
