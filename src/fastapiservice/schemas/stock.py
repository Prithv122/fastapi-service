import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..models.enums import Sector


class StockCreate(BaseModel):
    ticker: str
    company_name: str
    sector: Sector
    sub_sector: str


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticker: str
    company_name: str
    sector: Sector
    sub_sector: str
    created_at: datetime
