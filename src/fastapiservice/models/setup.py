"""Trade setup -- a planned entry scenario for a stock, e.g. "dip entry" or "breakout add"."""

import uuid
from decimal import Decimal

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .enums import SetupStatus, TimeFrame
from .mixins import IDMixin, TimestampMixin


class TradeSetup(Base, IDMixin, TimestampMixin):
    __tablename__ = "trade_setups"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    stock_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stocks.id"), index=True)
    research_note_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("research_notes.id"), index=True
    )

    scenario: Mapped[str] = mapped_column(String(64))
    entry_zone_low: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    entry_zone_high: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    timeframe: Mapped[TimeFrame] = mapped_column(SAEnum(TimeFrame, name="timeframe"))
    status: Mapped[SetupStatus] = mapped_column(
        SAEnum(SetupStatus, name="setup_status"), default=SetupStatus.OPEN
    )

    @property
    def risk_per_share(self) -> Decimal:
        return self.entry_zone_low - self.stop_loss

    @property
    def reward_per_share(self) -> Decimal:
        return self.target_price - self.entry_zone_low

    @property
    def risk_reward_ratio(self) -> Decimal:
        risk = self.risk_per_share
        if risk <= 0:
            raise ValueError("risk_per_share must be positive to compute risk/reward")
        return self.reward_per_share / risk
