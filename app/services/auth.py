"""Account registration, authentication, and profile management."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.i18n import normalize_language
from app.models import User, WeightUnit
from app.security import hash_password, verify_password
from app.services.errors import EmailAlreadyRegistered, InvalidCredentials


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _get_by_email(session: Session, email: str) -> User | None:
    stmt = select(User).where(func.lower(User.email) == _normalize_email(email))
    return session.scalar(stmt)


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def register_user(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    preferred_language: str,
) -> User:
    if _get_by_email(session, email) is not None:
        raise EmailAlreadyRegistered

    user = User(
        email=_normalize_email(email),
        password_hash=hash_password(password),
        display_name=display_name.strip(),
        preferred_language=normalize_language(preferred_language),
    )
    session.add(user)
    session.flush()
    return user


def authenticate_user(session: Session, *, email: str, password: str) -> User:
    user = _get_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials
    return user


def update_profile(
    session: Session,
    user: User,
    *,
    display_name: str,
    preferred_language: str,
    weight_unit: WeightUnit,
    default_rest_seconds: int,
) -> User:
    user.display_name = display_name.strip()
    user.preferred_language = normalize_language(preferred_language)
    user.weight_unit = weight_unit
    user.default_rest_seconds = default_rest_seconds
    session.add(user)
    return user


def change_password(
    session: Session,
    user: User,
    *,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentials
    user.password_hash = hash_password(new_password)
    session.add(user)
