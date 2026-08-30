from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import BrokerageCall, ResearchNote, Stock, User
from ..schemas.research import ResearchNoteCreate, ResearchNoteRead, StockHistoryEntry
from ..schemas.stock import StockCreate, StockRead

router = APIRouter(prefix="/stocks", tags=["stocks"])


async def get_owned_stock(ticker: str, user: User, db: AsyncSession) -> Stock:
    stock = await db.scalar(
        select(Stock).where(Stock.user_id == user.id, Stock.ticker == ticker.upper())
    )
    if stock is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stock not found")
    return stock


@router.post("", response_model=StockRead, status_code=status.HTTP_201_CREATED)
async def create_stock(
    payload: StockCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Stock:
    stock = Stock(user_id=user.id, **payload.model_dump() | {"ticker": payload.ticker.upper()})
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return stock


@router.get("", response_model=list[StockRead])
async def list_stocks(
    sector: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Stock]:
    query = select(Stock).where(Stock.user_id == user.id)
    if sector is not None:
        query = query.where(Stock.sector == sector)
    return list(await db.scalars(query.order_by(Stock.ticker)))


@router.get("/{ticker}", response_model=StockRead)
async def get_stock(
    ticker: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Stock:
    return await get_owned_stock(ticker, user, db)


@router.get("/{ticker}/history", response_model=list[StockHistoryEntry])
async def get_stock_history(
    ticker: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[StockHistoryEntry]:
    stock = await get_owned_stock(ticker, user, db)
    query = (
        select(ResearchNote)
        .where(ResearchNote.stock_id == stock.id)
        .order_by(ResearchNote.refresh_date)
    )
    notes = await db.scalars(query)
    return [
        StockHistoryEntry(refresh_date=n.refresh_date, call=n.call, research_note_id=n.id)
        for n in notes
    ]


@router.post(
    "/{ticker}/research", response_model=ResearchNoteRead, status_code=status.HTTP_201_CREATED
)
async def create_research_note(
    ticker: str,
    payload: ResearchNoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchNote:
    """Append a new research refresh for this stock. Never edits a prior note."""
    stock = await get_owned_stock(ticker, user, db)

    note = ResearchNote(
        user_id=user.id,
        stock_id=stock.id,
        **payload.model_dump(exclude={"brokerage_calls"}),
    )
    note.brokerage_calls = [
        BrokerageCall(user_id=user.id, **call.model_dump()) for call in payload.brokerage_calls
    ]
    db.add(note)
    await db.commit()
    await db.refresh(note, attribute_names=["brokerage_calls"])
    return note
