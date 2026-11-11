from typing import Annotated, Optional

from fastapi import Depends, Request
from sqlmodel import Session

from app.database import get_session
from app.errors import ForbiddenError, LoginRequired
from app.models import Role, User
from app.repositories import user_repo

SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user_optional(request: Request, session: SessionDep) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = user_repo.get(session, user_id)
    if user is None:  # account vanished (e.g. database reset): drop the stale cookie
        request.session.clear()
    return user


OptionalUserDep = Annotated[Optional[User], Depends(get_current_user_optional)]


def _role_dependency(*roles: str):
    def dependency(request: Request, user: OptionalUserDep) -> User:
        if user is None:
            target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
            raise LoginRequired(target)
        if user.role not in roles:
            raise ForbiddenError()
        return user

    return dependency


UserDep = Annotated[User, Depends(_role_dependency(Role.STUDENT, Role.LANDLORD, Role.ADMIN))]
StudentDep = Annotated[User, Depends(_role_dependency(Role.STUDENT))]
LandlordDep = Annotated[User, Depends(_role_dependency(Role.LANDLORD))]
AdminDep = Annotated[User, Depends(_role_dependency(Role.ADMIN))]
