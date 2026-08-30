"""Console entry point: runs the dev server with uvicorn."""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="fastapi-service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    # loop="none": uvicorn's own "asyncio" loop factory hardcodes ProactorEventLoop on
    # Windows, which silently overrides the SelectorEventLoop policy psycopg's async mode
    # requires (set in fastapiservice/__init__.py). "none" skips uvicorn's factory and
    # defers to that policy instead.
    uvicorn.run(
        "fastapiservice.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        loop="none",
    )
