"""AURA-EAGLE — FastAPI Application Entry Point"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import structlog

from backend.core.config import settings
from backend.core.database import init_db
from backend.core.events import manager
from backend.api.routes import agents, memory, reasoning, knowledge, metrics

log = structlog.get_logger()

# Resolve frontend dist relative to repo root
_REPO = Path(__file__).parent.parent
_DIST = _REPO / "frontend" / "dist"
_DIST_ASSETS = _DIST / "assets"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("aura_eagle.startup", version=settings.app_version)
    await init_db()
    # Boot task: warm up the cognitive baseline
    from backend.reasoning.pipeline import pipeline
    asyncio.create_task(
        pipeline.run("system boot — initialize cognitive baseline", {"silent": True})
    )
    yield
    log.info("aura_eagle.shutdown")


app = FastAPI(
    title="PROJECT AURA-EAGLE",
    description="Autonomous Unified Reasoning Architecture — Enhanced Adaptive Graph Learning Engine",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────────
app.include_router(agents.router,    prefix="/api")
app.include_router(memory.router,    prefix="/api")
app.include_router(reasoning.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(metrics.router,   prefix="/api")


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "operational", "system": "AURA-EAGLE", "version": settings.app_version}


# ── WebSocket ──────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    from backend.metrics_push import push_state
    await push_state(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "run_pipeline":
                    from backend.reasoning.pipeline import pipeline
                    task = msg.get("task", "")
                    if task:
                        await manager.send_personal(websocket, "pipeline_started", {"task": task})
                        result = await pipeline.run(task)
                        await manager.broadcast("pipeline_result", result.to_dict())
            except Exception as e:
                await manager.send_personal(websocket, "error", {"message": str(e)})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Static / SPA ───────────────────────────────────────────────────────────────
if _DIST_ASSETS.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_DIST_ASSETS)), name="assets")
    log.info("static.serving", path=str(_DIST))
else:
    log.warning("static.not_found", path=str(_DIST), hint="Run: cd frontend && npm run build")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    # Serve index.html for any non-API route (SPA client-side routing)
    index = _DIST / "index.html"
    if index.is_file():
        return FileResponse(str(index))
    return JSONResponse(
        {"error": "Frontend not built. Run: cd frontend && npm run build"},
        status_code=503,
    )
