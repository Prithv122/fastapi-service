"""Seed the database with realistic-but-synthetic demo data.

Invented NSE-style tickers only -- no real portfolio or research data. Run with:
    uv run python scripts/seed.py
"""

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select

import fastapiservice  # noqa: F401  (applies the Windows event-loop fix on import)
from fastapiservice.database import async_session_factory, engine
from fastapiservice.models import BrokerageCall, ResearchNote, Stock, Trade, TradeSetup, User
from fastapiservice.models.enums import (
    BrokerName,
    CallType,
    Sector,
    SetupStatus,
    TimeFrame,
    TradeSide,
)
from fastapiservice.security import hash_password

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password-1234"


async def seed() -> None:
    async with async_session_factory() as session:
        existing = await session.scalar(select(User).where(User.email == DEMO_EMAIL))
        if existing is not None:
            print(f"Demo user {DEMO_EMAIL} already exists (id={existing.id}); skipping seed.")
            return

        user = User(email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD))
        session.add(user)
        await session.flush()

        arvindtech = Stock(
            user_id=user.id,
            ticker="ARVINDTECH",
            company_name="Arvind Technologies Ltd",
            sector=Sector.IT,
            sub_sector="IT Services & Consulting",
        )
        bharatgreen = Stock(
            user_id=user.id,
            ticker="BHARATGREEN",
            company_name="Bharat Green Energy Ltd",
            sector=Sector.RENEWABLES,
            sub_sector="Solar EPC & Manufacturing",
        )
        nexusfin = Stock(
            user_id=user.id,
            ticker="NEXUSFIN",
            company_name="Nexus Financial Services Ltd",
            sector=Sector.FINANCIALS,
            sub_sector="NBFC - Diversified Retail Lending",
        )
        orbitdef = Stock(
            user_id=user.id,
            ticker="ORBITDEF",
            company_name="Orbit Defence Systems Ltd",
            sector=Sector.DEFENCE,
            sub_sector="Defence Electronics & Systems",
        )
        session.add_all([arvindtech, bharatgreen, nexusfin, orbitdef])
        await session.flush()

        # NEXUSFIN: three-refresh research history, call evolving BUY -> ACCUMULATE -> HOLD.
        note1 = ResearchNote(
            user_id=user.id,
            stock_id=nexusfin.id,
            refresh_date=date(2026, 6, 10),
            call=CallType.BUY,
            thesis=(
                "Diversified NBFC gaining share in underserved retail lending, trading at a "
                "discount to peers with a cleaner asset-quality trend."
            ),
            catalysts=["Q1 FY27 results", "RBI rate-cut transmission", "new gold-loan branches"],
            risks=["vehicle-finance delinquencies", "rural credit stress", "NIM compression"],
            target_1w=Decimal("152.00"),
            target_1w_note="Consolidating 142-148; breakout above 148 targets 152",
            target_1_3m=Decimal("165.00"),
            target_1_3m_note="Confirmed breakout opens 165 on volume",
            target_1_3y=Decimal("210.00"),
            target_1_3y_note="FY28 earnings-driven re-rating if AUM growth holds 20%+",
            technical_notes="Support 138/142, resistance 148/152. RSI ~47, neutral.",
        )
        session.add(note1)
        await session.flush()
        session.add(
            BrokerageCall(
                user_id=user.id,
                research_note_id=note1.id,
                broker="Nomura",
                rating="Buy",
                target_price=Decimal("160.00"),
                note="AUM growth ahead of guidance; asset quality watch-item, not a red flag yet.",
                call_date=date(2026, 6, 10),
            )
        )

        note2 = ResearchNote(
            user_id=user.id,
            stock_id=nexusfin.id,
            refresh_date=date(2026, 6, 15),
            call=CallType.ACCUMULATE,
            thesis="Thesis intact after a sharp 2-day rally; less margin of safety at this price.",
            catalysts=["Q1 FY27 results due July/Aug"],
            risks=["stock ran 13% in 2 sessions, short-term overbought"],
            target_1w=Decimal("158.00"),
            target_1w_note="Extended after the surge; expect consolidation before next leg",
            target_1_3m=Decimal("168.00"),
            target_1_3m_note="Prior resistance zone now the target on a pullback-and-hold",
            target_1_3y=Decimal("210.00"),
            target_1_3y_note="Unchanged long-term target",
            technical_notes="RSI ~68, approaching overbought. Trail stop, don't chase.",
        )
        session.add(note2)

        note3 = ResearchNote(
            user_id=user.id,
            stock_id=nexusfin.id,
            refresh_date=date(2026, 8, 25),
            call=CallType.HOLD,
            thesis="Q1 beat on profit but asset quality softened; valuation has already re-rated.",
            catalysts=["Q2 FY27 results"],
            risks=["Gross Stage 3 rose QoQ", "P/B re-rated from 4.2x to 5.17x in 10 weeks"],
            target_1w=Decimal("192.00"),
            target_1w_note="Consolidating 184-190",
            target_1_3m=Decimal("194.00"),
            target_1_3m_note="Most brokerage-implied upside already captured",
            target_1_3y=Decimal("214.00"),
            target_1_3y_note="Bull case requires continued execution, not just a Q1 repeat",
            technical_notes="Coiled under resistance 190; RSI ~46, neutral.",
        )
        session.add(note3)
        await session.flush()
        session.add(
            BrokerageCall(
                user_id=user.id,
                research_note_id=note3.id,
                broker="Jefferies",
                rating="Buy",
                target_price=Decimal("186.00"),
                note="Top pick on EPS/BVPS upgrades, not multiple expansion.",
                call_date=date(2026, 8, 25),
            )
        )
        session.add(
            BrokerageCall(
                user_id=user.id,
                research_note_id=note3.id,
                broker="Morgan Stanley",
                rating="Equal-weight",
                target_price=Decimal("182.00"),
                note="Cautious on rising vehicle-finance delinquencies.",
                call_date=date(2026, 8, 25),
            )
        )

        # ARVINDTECH: single BUY note, one open setup.
        arvind_note = ResearchNote(
            user_id=user.id,
            stock_id=arvindtech.id,
            refresh_date=date(2026, 7, 5),
            call=CallType.BUY,
            thesis="Mid-cap IT services name winning deals in BFSI vertical, margin expansion.",
            catalysts=["deal wins", "margin guidance upgrade"],
            risks=["client concentration", "US IT budget slowdown"],
            target_1w=Decimal("1180.00"),
            target_1w_note="Range 1120-1160",
            target_1_3m=Decimal("1280.00"),
            target_1_3m_note=None,
            target_1_3y=Decimal("1600.00"),
            target_1_3y_note="Margin story plays out over FY28",
            technical_notes="Support 1080, resistance 1180.",
        )
        session.add(arvind_note)

        # BHARATGREEN: WAIT_AND_BUY call, no setup yet.
        bharat_note = ResearchNote(
            user_id=user.id,
            stock_id=bharatgreen.id,
            refresh_date=date(2026, 7, 20),
            call=CallType.WAIT_AND_BUY,
            thesis="Strong order book but valuation has run ahead of near-term execution.",
            catalysts=["order-book conversion", "module manufacturing capacity ramp"],
            risks=["module price deflation", "working-capital intensity"],
            target_1w=None,
            target_1w_note=None,
            target_1_3m=Decimal("640.00"),
            target_1_3m_note="Wait for a pullback toward 560-580 before adding",
            target_1_3y=Decimal("900.00"),
            target_1_3y_note=None,
            technical_notes="Resistance 620; wait for retest of 560 support.",
        )
        session.add(bharat_note)

        # ORBITDEF: SELL call after a run-up.
        orbit_note = ResearchNote(
            user_id=user.id,
            stock_id=orbitdef.id,
            refresh_date=date(2026, 5, 12),
            call=CallType.SELL,
            thesis="Order pipeline strong, but stock priced for perfection after a 90% rally.",
            catalysts=["export order announcements"],
            risks=["valuation", "budget allocation delays"],
            target_1w=None,
            target_1w_note=None,
            target_1_3m=None,
            target_1_3m_note=None,
            target_1_3y=None,
            target_1_3y_note=None,
            technical_notes="Parabolic move, RSI > 80. High reversal risk.",
        )
        session.add(orbit_note)
        await session.flush()

        # Trade setups: one OPEN, one TRIGGERED, one INVALIDATED, one CLOSED.
        setup_open = TradeSetup(
            user_id=user.id,
            stock_id=arvindtech.id,
            research_note_id=arvind_note.id,
            scenario="Dip entry",
            entry_zone_low=Decimal("1080.00"),
            entry_zone_high=Decimal("1110.00"),
            stop_loss=Decimal("1020.00"),
            target_price=Decimal("1280.00"),
            timeframe=TimeFrame.SWING,
            status=SetupStatus.OPEN,
        )
        setup_triggered = TradeSetup(
            user_id=user.id,
            stock_id=nexusfin.id,
            research_note_id=note1.id,
            scenario="Breakout add",
            entry_zone_low=Decimal("148.00"),
            entry_zone_high=Decimal("152.00"),
            stop_loss=Decimal("140.00"),
            target_price=Decimal("175.00"),
            timeframe=TimeFrame.SWING,
            status=SetupStatus.TRIGGERED,
        )
        setup_invalidated = TradeSetup(
            user_id=user.id,
            stock_id=bharatgreen.id,
            research_note_id=bharat_note.id,
            scenario="Pullback entry",
            entry_zone_low=Decimal("560.00"),
            entry_zone_high=Decimal("580.00"),
            stop_loss=Decimal("520.00"),
            target_price=Decimal("680.00"),
            timeframe=TimeFrame.POSITIONAL,
            status=SetupStatus.INVALIDATED,
        )
        setup_closed = TradeSetup(
            user_id=user.id,
            stock_id=orbitdef.id,
            research_note_id=orbit_note.id,
            scenario="Short into resistance",
            entry_zone_low=Decimal("2400.00"),
            entry_zone_high=Decimal("2450.00"),
            stop_loss=Decimal("2550.00"),
            target_price=Decimal("2100.00"),
            timeframe=TimeFrame.SWING,
            status=SetupStatus.CLOSED,
        )
        session.add_all([setup_open, setup_triggered, setup_invalidated, setup_closed])
        await session.flush()

        # Trades: a winning long, a losing long, a winning short, and one still open.
        session.add_all(
            [
                Trade(
                    user_id=user.id,
                    stock_id=nexusfin.id,
                    setup_id=setup_triggered.id,
                    broker=BrokerName.ZERODHA,
                    side=TradeSide.BUY,
                    quantity=10,
                    entry_price=Decimal("150.00"),
                    entry_date=date(2026, 6, 16),
                    exit_price=Decimal("172.00"),
                    exit_date=date(2026, 7, 20),
                    notes="Booked at first target after breakout confirmed.",
                ),
                Trade(
                    user_id=user.id,
                    stock_id=bharatgreen.id,
                    setup_id=setup_invalidated.id,
                    broker=BrokerName.GROWW,
                    side=TradeSide.BUY,
                    quantity=15,
                    entry_price=Decimal("600.00"),
                    entry_date=date(2026, 7, 22),
                    exit_price=Decimal("545.00"),
                    exit_date=date(2026, 8, 5),
                    notes="Stopped out; setup invalidated on the way down.",
                ),
                Trade(
                    user_id=user.id,
                    stock_id=orbitdef.id,
                    setup_id=setup_closed.id,
                    broker=BrokerName.ZERODHA,
                    side=TradeSide.SELL,
                    quantity=5,
                    entry_price=Decimal("2430.00"),
                    entry_date=date(2026, 5, 13),
                    exit_price=Decimal("2180.00"),
                    exit_date=date(2026, 6, 2),
                    notes="Covered near target after the parabolic move faded.",
                ),
                Trade(
                    user_id=user.id,
                    stock_id=arvindtech.id,
                    setup_id=setup_open.id,
                    broker=BrokerName.GROWW,
                    side=TradeSide.BUY,
                    quantity=8,
                    entry_price=Decimal("1095.00"),
                    entry_date=date(2026, 8, 20),
                    notes="Still open, riding toward target.",
                ),
            ]
        )

        await session.commit()

    print(f"Seeded demo user {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print("Stocks: ARVINDTECH, BHARATGREEN, NEXUSFIN, ORBITDEF")


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
