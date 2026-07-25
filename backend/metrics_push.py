"""AURA-EAGLE — Push initial metrics state over WebSocket"""
from backend.memory.fabric import memory
from backend.knowledge.graph import knowledge_graph
from backend.reasoning.decision_engine import decision_engine
from backend.agents.orion import orion
from backend.agents.nyx import nyx
from backend.agents.sol import sol
from backend.agents.kade import kade
from backend.agents.mira import mira
from backend.agents.vex import vex
from backend.core.events import manager


async def push_state(websocket=None):
    payload = {
        "memory": memory.stats(),
        "knowledge_graph": knowledge_graph.stats(),
        "decisions": decision_engine.stats(),
        "agents": [a.status() for a in [orion, nyx, sol, kade, mira, vex]],
    }
    if websocket:
        await manager.send_personal(websocket, "state_snapshot", payload)
    else:
        await manager.broadcast("state_snapshot", payload)
