from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from app.config import settings
from app.routers import chat, ws, projects, files, system, tools, agent, memory, evaluation, autonomy, integrations, platform, context, models, retrieval
from app.services.session_manager import session_manager
from app.services.ollama_client import OllamaClient
from app.services.embedding_service import embedding_service
from app.tools.registry import tool_registry
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "Starting %s with model %s",
        settings.app_name,
        settings.primary_model,
    )
    logger.info("Qdrant path: %s", settings.qdrant_path)
    logger.info("SQLite path: %s", settings.sqlite_path)

    await tool_registry.discover_tools()
    logger.info("Discovered %d tools", len(tool_registry.tools))

    await embedding_service.initialize()
    await session_manager.initialize()

    yield

    logger.info("Shutting down...")
    await embedding_service.shutdown()
    await session_manager.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(ws.router, prefix="/api", tags=["websocket"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(tools.router, prefix="/api", tags=["tools"])
app.include_router(agent.router)
app.include_router(memory.router)
app.include_router(evaluation.router)
app.include_router(autonomy.router)
app.include_router(integrations.router)
app.include_router(platform.router)
app.include_router(context.router)
app.include_router(models.router)
app.include_router(retrieval.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
