import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import TradeSetup, User
from ..models.enums import SetupStatus, TimeFrame
from ..schemas.setup import TradeSetupCreate, TradeSetupRead, TradeSetupUpdate

router = APIRouter(prefix="/setups", tags=["setups"])


@router.post("", response_model=TradeSetupRead, status_code=status.HTTP_201_CREATED)
async def create_setup(
    payload: TradeSetupCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TradeSetup:
    setup = TradeSetup(user_id=user.id, **payload.model_dump())
    db.add(setup)
    await db.commit()
    await db.refresh(setup)
    return setup


@router.get("", response_model=list[TradeSetupRead])
async def list_setups(
    status_filter: SetupStatus | None = None,
    timeframe: TimeFrame | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TradeSetup]:
    query = select(TradeSetup).where(TradeSetup.user_id == user.id)
    if status_filter is not None:
        query = query.where(TradeSetup.status == status_filter)
    if timeframe is not None:
        query = query.where(TradeSetup.timeframe == timeframe)
    return list(await db.scalars(query.order_by(TradeSetup.created_at.desc())))


async def get_owned_setup(setup_id: uuid.UUID, user: User, db: AsyncSession) -> TradeSetup:
    setup = await db.scalar(
        select(TradeSetup).where(TradeSetup.id == setup_id, TradeSetup.user_id == user.id)
    )
    if setup is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trade setup not found")
    return setup


@router.patch("/{setup_id}", response_model=TradeSetupRead)
async def update_setup_status(
    setup_id: uuid.UUID,
    payload: TradeSetupUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TradeSetup:
    setup = await get_owned_setup(setup_id, user, db)
    setup.status = payload.status
    await db.commit()
    await db.refresh(setup)
    return setup
