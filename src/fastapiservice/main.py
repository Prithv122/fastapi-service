"""FastAPI application factory."""

from fastapi import FastAPI

from .routers import auth, research, setups, stocks, trades


def create_app() -> FastAPI:
    app = FastAPI(
        title="fastapi-service",
        summary="Personal Indian Equity Research & Swing-Trade Journal API",
    )
    app.include_router(auth.router)
    app.include_router(stocks.router)
    app.include_router(research.router)
    app.include_router(setups.router)
    app.include_router(trades.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
