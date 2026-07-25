"""AURA-EAGLE — WebSocket broadcast bus"""
import asyncio
import json
from typing import Any
from fastapi import WebSocket
import structlog

log = structlog.get_logger()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        log.info("ws.connected", total=len(self.active))

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        log.info("ws.disconnected", total=len(self.active))

    async def broadcast(self, event_type: str, data: Any):
        payload = json.dumps({"type": event_type, "data": data})
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_personal(self, ws: WebSocket, event_type: str, data: Any):
        try:
            await ws.send_text(json.dumps({"type": event_type, "data": data}))
        except Exception as e:
            log.warning("ws.send_failed", error=str(e))


manager = ConnectionManager()
