"""The user's current daily motivational line."""

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MotivationalQuote(TimestampMixin, Base):
    __tablename__ = "motivational_quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    body: Mapped[str] = mapped_column(Text)
    for_date: Mapped[date] = mapped_column(Date)
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
