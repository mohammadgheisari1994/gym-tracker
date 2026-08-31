"""User account model."""

from enum import StrEnum

from sqlalchemy import Enum, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

MIN_REST_SECONDS = 15
MAX_REST_SECONDS = 600
DEFAULT_REST_SECONDS = 120


class WeightUnit(StrEnum):
    KG = "kg"
    LB = "lb"


_WEIGHT_UNIT = Enum(
    WeightUnit,
    native_enum=False,
    create_constraint=False,
    length=4,
    values_callable=lambda enum: [member.value for member in enum],
)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(80))
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    weight_unit: Mapped[WeightUnit] = mapped_column(_WEIGHT_UNIT, server_default=text("'kg'"))
    default_rest_seconds: Mapped[int] = mapped_column(Integer, server_default=text("120"))
