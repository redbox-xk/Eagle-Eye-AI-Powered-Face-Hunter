"""AURA-EAGLE — Reasoning API"""
from fastapi import APIRouter
from backend.reasoning.pipeline import pipeline
from backend.reasoning.decision_engine import decision_engine
from backend.reasoning.simulation import simulation_engine
from backend.governance.ethics import ethics_engine

router = APIRouter(prefix="/reasoning", tags=["reasoning"])


@router.post("/run")
async def run_pipeline(body: dict):
    task = body.get("task", "")
    context = body.get("context", {})
    if not task.strip():
        return {"error": "task is required"}
    result = await pipeline.run(task, context)
    return result.to_dict()


@router.get("/history")
async def pipeline_history(limit: int = 10):
    return {"history": pipeline.history(limit=limit)}


@router.post("/simulate")
async def simulate(body: dict):
    task = body.get("task", "")
    depth = int(body.get("depth", 5))
    result = simulation_engine.simulate(task, depth=depth)
    return result.to_dict()


@router.post("/decide")
async def decide(body: dict):
    task = body.get("task", "")
    agent_output = body.get("agent_output", {})
    ethical_score = float(body.get("ethical_score", 1.0))
    decision = decision_engine.evaluate(task, agent_output, ethical_score=ethical_score)
    return decision.to_dict()


@router.get("/decisions")
async def decisions(limit: int = 20):
    return {"decisions": decision_engine.history(limit), "stats": decision_engine.stats()}


@router.post("/ethics/evaluate")
async def evaluate_ethics(body: dict):
    action = body.get("action", "")
    context = body.get("context", {})
    assessment = ethics_engine.evaluate(action, context)
    return assessment.to_dict()
