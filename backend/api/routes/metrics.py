"""AURA-EAGLE — System Metrics & Observability API"""
import psutil
import time
from fastapi import APIRouter
from backend.memory.fabric import memory
from backend.knowledge.graph import knowledge_graph
from backend.reasoning.decision_engine import decision_engine
from backend.reasoning.pipeline import pipeline
from backend.agents.orion import orion
from backend.agents.nyx import nyx
from backend.agents.sol import sol
from backend.agents.kade import kade
from backend.agents.mira import mira
from backend.agents.vex import vex

router = APIRouter(prefix="/metrics", tags=["metrics"])
_start_time = time.time()


@router.get("/system")
async def system_metrics():
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    return {
        "uptime_seconds": round(time.time() - _start_time, 1),
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / 1024 / 1024, 1),
        "memory_total_mb": round(mem.total / 1024 / 1024, 1),
    }


@router.get("/aura")
async def aura_score():
    """Compute live AURA score: (Intelligence × Adaptation × Reliability) / (Cost × Risk × Uncertainty)"""
    all_agents = [orion, nyx, sol, kade, mira, vex]
    invocations = sum(a._invocations for a in all_agents)
    errors = sum(a._errors for a in all_agents)
    
    reliability = 1.0 - (errors / max(invocations, 1))
    decision_stats = decision_engine.stats()
    approval_rate = decision_stats.get("approval_rate", 0.5)
    intelligence = approval_rate * 0.7 + reliability * 0.3
    adaptation = min(1.0, invocations / 20)  # improves with use
    cost = 0.2
    risk = 1.0 - approval_rate
    uncertainty = 1.0 - intelligence

    numerator = intelligence * max(adaptation, 0.1) * reliability
    denominator = max(0.001, cost * max(risk, 0.01) * max(uncertainty, 0.01))
    aura = min(1.0, numerator / (denominator * 2))

    return {
        "aura_score": round(aura, 4),
        "components": {
            "intelligence": round(intelligence, 4),
            "adaptation": round(adaptation, 4),
            "reliability": round(reliability, 4),
            "cost": round(cost, 4),
            "risk": round(risk, 4),
            "uncertainty": round(uncertainty, 4),
        },
        "formula": "AURA = (Intelligence × Adaptation × Reliability) / (Cost × Risk × Uncertainty)",
        "invocations": invocations,
        "decision_stats": decision_stats,
    }


@router.get("/overview")
async def overview():
    mem_stats = memory.stats()
    kg_stats = knowledge_graph.stats()
    decision_stats = decision_engine.stats()
    all_agents = [orion, nyx, sol, kade, mira, vex]
    return {
        "memory": mem_stats,
        "knowledge_graph": kg_stats,
        "decisions": decision_stats,
        "pipeline_runs": len(pipeline._history),
        "agents": {
            "total": len(all_agents),
            "total_invocations": sum(a._invocations for a in all_agents),
            "total_errors": sum(a._errors for a in all_agents),
        },
    }
