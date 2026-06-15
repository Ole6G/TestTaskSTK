from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.persistence.migrations import run_migrations
from app.presentation.api.routes import router as news_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    run_migrations()
    yield


app = FastAPI(
    title="RU News Analysis PoC",
    description="Prototype service for clustering and sentiment ranking of .ru news flow.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(news_router, prefix="/api")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
