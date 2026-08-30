import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..deps import get_current_user
from ..models import ResearchNote, User
from ..models.enums import CallType
from ..schemas.research import ResearchNoteRead

router = APIRouter(prefix="/research", tags=["research"])


@router.get("", response_model=list[ResearchNoteRead])
async def list_research_notes(
    stock_id: uuid.UUID | None = None,
    call: CallType | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResearchNote]:
    query = (
        select(ResearchNote)
        .where(ResearchNote.user_id == user.id)
        .options(selectinload(ResearchNote.brokerage_calls))
    )
    if stock_id is not None:
        query = query.where(ResearchNote.stock_id == stock_id)
    if call is not None:
        query = query.where(ResearchNote.call == call)
    return list(await db.scalars(query.order_by(ResearchNote.refresh_date.desc())))


@router.get("/{research_note_id}", response_model=ResearchNoteRead)
async def get_research_note(
    research_note_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchNote:
    query = (
        select(ResearchNote)
        .where(ResearchNote.id == research_note_id, ResearchNote.user_id == user.id)
        .options(selectinload(ResearchNote.brokerage_calls))
    )
    note = await db.scalar(query)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Research note not found")
    return note
