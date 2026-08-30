import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ..models.enums import CallType


class BrokerageCallCreate(BaseModel):
    broker: str
    rating: str
    target_price: Decimal
    note: str | None = None
    call_date: date


class BrokerageCallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    broker: str
    rating: str
    target_price: Decimal
    note: str | None
    call_date: date


class ResearchNoteCreate(BaseModel):
    refresh_date: date
    call: CallType
    thesis: str
    catalysts: list[str] = []
    risks: list[str] = []
    target_1w: Decimal | None = None
    target_1w_note: str | None = None
    target_1_3m: Decimal | None = None
    target_1_3m_note: str | None = None
    target_1_3y: Decimal | None = None
    target_1_3y_note: str | None = None
    technical_notes: str | None = None
    brokerage_calls: list[BrokerageCallCreate] = []


class ResearchNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stock_id: uuid.UUID
    refresh_date: date
    call: CallType
    thesis: str
    catalysts: list[str]
    risks: list[str]
    target_1w: Decimal | None
    target_1w_note: str | None
    target_1_3m: Decimal | None
    target_1_3m_note: str | None
    target_1_3y: Decimal | None
    target_1_3y_note: str | None
    technical_notes: str | None
    created_at: datetime
    brokerage_calls: list[BrokerageCallRead] = []


class StockHistoryEntry(BaseModel):
    """One row of GET /stocks/{ticker}/history -- the call over time."""

    refresh_date: date
    call: CallType
    research_note_id: uuid.UUID
