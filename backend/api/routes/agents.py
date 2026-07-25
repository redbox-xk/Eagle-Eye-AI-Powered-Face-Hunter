"""AURA-EAGLE — Agents API"""
from fastapi import APIRouter
from backend.agents.orion import orion
from backend.agents.nyx import nyx
from backend.agents.sol import sol
from backend.agents.kade import kade
from backend.agents.mira import mira
from backend.agents.vex import vex

router = APIRouter(prefix="/agents", tags=["agents"])
ALL = [orion, nyx, sol, kade, mira, vex]


@router.get("/")
async def list_agents():
    return {"agents": [a.status() for a in ALL]}


@router.get("/{agent_id}/status")
async def agent_status(agent_id: str):
    for a in ALL:
        if a.agent_id == agent_id:
            return a.status()
    return {"error": f"Agent '{agent_id}' not found"}, 404


@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, body: dict):
    task = body.get("task", "")
    context = body.get("context", {})
    for a in ALL:
        if a.agent_id == agent_id:
            output = a.run(task, context)
            return output.to_dict()
    return {"error": f"Agent '{agent_id}' not found"}
