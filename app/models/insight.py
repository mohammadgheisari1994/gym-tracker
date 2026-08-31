"""Cached LLM-written analytical summaries of a user's training."""

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Insight(TimestampMixin, Base):
    __tablename__ = "insights"
    __table_args__ = (UniqueConstraint("user_id", "scope", name="uq_insights_user_scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # "overall" or "exercise:{id}"
    scope: Mapped[str] = mapped_column(String(40))
    body: Mapped[str] = mapped_column(Text)
    data_signature: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
