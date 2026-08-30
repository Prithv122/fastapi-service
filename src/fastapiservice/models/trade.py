"""Trade -- an actual fill, optionally closed out with an exit."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .enums import BrokerName, TradeSide
from .mixins import IDMixin, TimestampMixin


class Trade(Base, IDMixin, TimestampMixin):
    __tablename__ = "trades"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    stock_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stocks.id"), index=True)
    setup_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trade_setups.id"), index=True)

    broker: Mapped[BrokerName] = mapped_column(SAEnum(BrokerName, name="broker_name"))
    side: Mapped[TradeSide] = mapped_column(SAEnum(TradeSide, name="trade_side"))
    quantity: Mapped[int]
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    entry_date: Mapped[date] = mapped_column(Date)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    exit_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    @property
    def is_closed(self) -> bool:
        return self.exit_price is not None

    @property
    def realized_pnl(self) -> Decimal | None:
        if self.exit_price is None:
            return None
        direction = 1 if self.side == TradeSide.BUY else -1
        return (self.exit_price - self.entry_price) * self.quantity * direction

    @property
    def realized_pnl_pct(self) -> Decimal | None:
        pnl = self.realized_pnl
        if pnl is None:
            return None
        cost_basis = self.entry_price * self.quantity
        if cost_basis == 0:
            return None
        return (pnl / cost_basis) * 100
