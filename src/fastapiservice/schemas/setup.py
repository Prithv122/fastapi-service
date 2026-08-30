import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from ..config import get_settings
from ..models.enums import SetupStatus, TimeFrame


class TradeSetupCreate(BaseModel):
    stock_id: uuid.UUID
    research_note_id: uuid.UUID | None = None
    scenario: str
    entry_zone_low: Decimal
    entry_zone_high: Decimal
    stop_loss: Decimal
    target_price: Decimal
    timeframe: TimeFrame

    @model_validator(mode="after")
    def check_price_ordering_and_risk_reward(self) -> "TradeSetupCreate":
        if not (self.stop_loss < self.entry_zone_low <= self.entry_zone_high < self.target_price):
            raise ValueError(
                "prices must satisfy stop_loss < entry_zone_low <= entry_zone_high < target_price"
            )

        risk = self.entry_zone_low - self.stop_loss
        reward = self.target_price - self.entry_zone_low
        min_rr = get_settings().min_risk_reward_ratio
        if reward / risk < Decimal(str(min_rr)):
            raise ValueError(f"reward/risk ratio must be at least {min_rr}")

        return self


class TradeSetupUpdate(BaseModel):
    status: SetupStatus


class TradeSetupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stock_id: uuid.UUID
    research_note_id: uuid.UUID | None
    scenario: str
    entry_zone_low: Decimal
    entry_zone_high: Decimal
    stop_loss: Decimal
    target_price: Decimal
    timeframe: TimeFrame
    status: SetupStatus
    created_at: datetime

    @computed_field
    @property
    def risk_reward_ratio(self) -> Decimal:
        risk = self.entry_zone_low - self.stop_loss
        reward = self.target_price - self.entry_zone_low
        return reward / risk
