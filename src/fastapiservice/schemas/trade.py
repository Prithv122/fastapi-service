import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field

from ..models.enums import BrokerName, TradeSide


class TradeCreate(BaseModel):
    stock_id: uuid.UUID
    setup_id: uuid.UUID | None = None
    broker: BrokerName
    side: TradeSide
    quantity: int
    entry_price: Decimal
    entry_date: date
    notes: str | None = None


class TradeExitUpdate(BaseModel):
    exit_price: Decimal
    exit_date: date


class TradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stock_id: uuid.UUID
    setup_id: uuid.UUID | None
    broker: BrokerName
    side: TradeSide
    quantity: int
    entry_price: Decimal
    entry_date: date
    exit_price: Decimal | None
    exit_date: date | None
    notes: str | None
    created_at: datetime

    @computed_field
    @property
    def realized_pnl(self) -> Decimal | None:
        if self.exit_price is None:
            return None
        direction = 1 if self.side == TradeSide.BUY else -1
        return (self.exit_price - self.entry_price) * self.quantity * direction

    @computed_field
    @property
    def realized_pnl_pct(self) -> Decimal | None:
        pnl = self.realized_pnl
        if pnl is None:
            return None
        cost_basis = self.entry_price * self.quantity
        if cost_basis == 0:
            return None
        return (pnl / cost_basis) * 100
