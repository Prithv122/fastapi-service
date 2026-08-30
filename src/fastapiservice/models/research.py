"""Append-only research notes and their per-broker brokerage calls.

A ResearchNote is never updated after creation -- a refresh creates a new row, so a stock's
research can always be evaluated against what was known at the time. See NOTES.md.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ARRAY, Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import CallType
from .mixins import IDMixin, TimestampMixin


class ResearchNote(Base, IDMixin, TimestampMixin):
    __tablename__ = "research_notes"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    stock_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stocks.id"), index=True)

    refresh_date: Mapped[date] = mapped_column(Date)
    call: Mapped[CallType] = mapped_column(SAEnum(CallType, name="call_type"))
    thesis: Mapped[str] = mapped_column(Text)
    catalysts: Mapped[list[str]] = mapped_column(ARRAY(String))
    risks: Mapped[list[str]] = mapped_column(ARRAY(String))

    target_1w: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    target_1w_note: Mapped[str | None] = mapped_column(Text)
    target_1_3m: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    target_1_3m_note: Mapped[str | None] = mapped_column(Text)
    target_1_3y: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    target_1_3y_note: Mapped[str | None] = mapped_column(Text)

    technical_notes: Mapped[str | None] = mapped_column(Text)

    brokerage_calls: Mapped[list["BrokerageCall"]] = relationship(
        back_populates="research_note", cascade="all, delete-orphan"
    )


class BrokerageCall(Base, IDMixin, TimestampMixin):
    __tablename__ = "brokerage_calls"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    research_note_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_notes.id"), index=True
    )

    broker: Mapped[str] = mapped_column(String(128))
    rating: Mapped[str] = mapped_column(String(64))
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    note: Mapped[str | None] = mapped_column(Text)
    call_date: Mapped[date] = mapped_column(Date)

    research_note: Mapped[ResearchNote] = relationship(back_populates="brokerage_calls")
