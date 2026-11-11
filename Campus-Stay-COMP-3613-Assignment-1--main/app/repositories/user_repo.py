from typing import List, Optional

from sqlmodel import Session, col, select

from app.models import User
from app.repositories.base import save


def get(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def get_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username.lower())).first()


def get_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email.lower())).first()


def list_all(session: Session) -> List[User]:
    return list(session.exec(select(User).order_by(col(User.id))).all())


def add(session: Session, user: User) -> User:
    user.username = user.username.lower()
    user.email = user.email.lower()
    return save(session, user)
