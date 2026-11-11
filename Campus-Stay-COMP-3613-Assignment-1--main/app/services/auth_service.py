import re

from sqlmodel import Session

from app.errors import ServiceError
from app.models import Role, User
from app.repositories import user_repo
from app.utilities.security import hash_password, verify_password
from app.utilities.validators import clean

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register(
    session: Session,
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str = Role.STUDENT,
    phone: str = "",
) -> User:
    username = clean(username).lower()
    email = clean(email).lower()
    if not USERNAME_RE.match(username):
        raise ServiceError("Username must be 3-30 characters: letters, numbers or underscore.")
    if not EMAIL_RE.match(email):
        raise ServiceError("Enter a valid email address.")
    if len(password or "") < 6:
        raise ServiceError("Password must be at least 6 characters.")
    if role not in Role.SIGNUP:
        raise ServiceError("Choose whether you are a student or a landlord.")
    if user_repo.get_by_username(session, username):
        raise ServiceError("That username is taken.")
    if user_repo.get_by_email(session, email):
        raise ServiceError("An account with that email already exists.")
    user = User(
        username=username,
        email=email,
        full_name=clean(full_name)[:120],
        phone=clean(phone)[:30],
        password_hash=hash_password(password),
        role=role,
    )
    return user_repo.add(session, user)


def authenticate(session: Session, username: str, password: str) -> User:
    user = user_repo.get_by_username(session, clean(username))
    if user is None or not verify_password(password or "", user.password_hash):
        raise ServiceError("Incorrect username or password.")
    return user


def home_path(role: str) -> str:
    return {Role.LANDLORD: "/landlord", Role.ADMIN: "/admin"}.get(role, "/accommodations")
