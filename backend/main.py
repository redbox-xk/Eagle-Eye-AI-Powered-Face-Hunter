"""AURA-EAGLE — FastAPI Application Entry Point"""
import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import structlog

from backend.core.config import settings
from backend.core.database import init_db
from backend.core.events import manager
from backend.api.routes import agents, memory, reasoning, knowledge, metrics

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("aura_eagle.startup", version=settings.app_version)
    await init_db()
    # Warm up: run a silent boot task through the pipeline
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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────────
app.include_router(agents.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(reasoning.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")


# ── WebSocket ──────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial state
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


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "operational", "system": "AURA-EAGLE", "version": settings.app_version}


# ── Static / SPA ───────────────────────────────────────────────────────────────
_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        return FileResponse(os.path.join(_dist, "index.html"))
