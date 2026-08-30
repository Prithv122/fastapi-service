"""Stock model — a ticker the user is researching or has traded."""

import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .enums import Sector
from .mixins import IDMixin, TimestampMixin


class Stock(Base, IDMixin, TimestampMixin):
    __tablename__ = "stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_stock_user_ticker"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(32))
    company_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[Sector] = mapped_column(SAEnum(Sector, name="sector"))
    sub_sector: Mapped[str] = mapped_column(String(128))
