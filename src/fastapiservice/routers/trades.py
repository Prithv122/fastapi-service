import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import Trade, User
from ..schemas.trade import TradeCreate, TradeExitUpdate, TradeRead

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
async def create_trade(
    payload: TradeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Trade:
    trade = Trade(user_id=user.id, **payload.model_dump())
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


@router.get("", response_model=list[TradeRead])
async def list_trades(
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Trade]:
    query = select(Trade).where(Trade.user_id == user.id)
    if date_from is not None:
        query = query.where(Trade.entry_date >= date_from)
    if date_to is not None:
        query = query.where(Trade.entry_date <= date_to)
    return list(await db.scalars(query.order_by(Trade.entry_date.desc())))


async def get_owned_trade(trade_id: uuid.UUID, user: User, db: AsyncSession) -> Trade:
    trade = await db.scalar(select(Trade).where(Trade.id == trade_id, Trade.user_id == user.id))
    if trade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trade not found")
    return trade


@router.get("/{trade_id}", response_model=TradeRead)
async def get_trade(
    trade_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Trade:
    return await get_owned_trade(trade_id, user, db)


@router.patch("/{trade_id}/exit", response_model=TradeRead)
async def close_trade(
    trade_id: uuid.UUID,
    payload: TradeExitUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Trade:
    trade = await get_owned_trade(trade_id, user, db)
    trade.exit_price = payload.exit_price
    trade.exit_date = payload.exit_date
    await db.commit()
    await db.refresh(trade)
    return trade
