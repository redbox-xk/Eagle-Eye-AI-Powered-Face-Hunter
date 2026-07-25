"""AURA-EAGLE — Reasoning Pipeline

Full 11-stage pipeline:
  INPUT → Understand → Retrieve Memory → Generate Solutions →
  Evaluate → Simulate → Critic Review → Risk Analysis →
  Governance Check → Execute / Request Approval →
  Measure Outcome → Update Memory
"""
from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import structlog

from backend.agents.orion import orion
from backend.agents.nyx import nyx
from backend.agents.sol import sol
from backend.agents.kade import kade
from backend.agents.mira import mira
from backend.agents.vex import vex
from backend.agents.base import AgentOutput
from backend.memory.fabric import memory
from backend.memory.types import MemoryLayer
from backend.knowledge.graph import knowledge_graph
from backend.governance.ethics import ethics_engine
from backend.reasoning.decision_engine import decision_engine, Decision
from backend.reasoning.simulation import simulation_engine
from backend.core.config import settings

log = structlog.get_logger()

ALL_AGENTS = [orion, nyx, sol, kade, mira, vex]
SPECIALIST_AGENTS = [nyx, sol, kade, mira, vex]


@dataclass
class PipelineStage:
    name: str
    status: str = "pending"   # pending | running | complete | skipped | failed
    result: Any = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2),
            "result_summary": self._summarize(),
        }

    def _summarize(self) -> str | None:
        if self.result is None:
            return None
        if isinstance(self.result, str):
            return self.result[:200]
        if isinstance(self.result, dict):
            return str(self.result)[:200]
        return str(self.result)[:200]


@dataclass
class PipelineResult:
    task_id: str
    task: str
    stages: list[PipelineStage]
    agent_outputs: list[AgentOutput]
    decision: Decision | None
    aura_score: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task": self.task,
            "stages": [s.to_dict() for s in self.stages],
            "agent_outputs": [a.to_dict() for a in self.agent_outputs],
            "decision": self.decision.to_dict() if self.decision else None,
            "aura_score": round(self.aura_score, 4),
            "created_at": self.created_at.isoformat(),
            "duration_ms": round(self.duration_ms, 2),
        }


class ReasoningPipeline:
    """
    Executes the full AURA-EAGLE reasoning pipeline for any task.
    """

    def __init__(self):
        self._history: list[PipelineResult] = []

    async def run(self, task: str, context: dict[str, Any] | None = None) -> PipelineResult:
        task_id = str(uuid.uuid4())[:12]
        context = context or {}
        t_start = time.perf_counter()
        stages: list[PipelineStage] = []
        agent_outputs: list[AgentOutput] = []
        decision: Decision | None = None

        log.info("pipeline.start", task_id=task_id, task=task[:80])

        # ── Stage 1: Understand ───────────────────────────────────────────────
        s1 = PipelineStage("Understand Objective")
        s1.status = "running"
        s1.result = f"Objective parsed: '{task[:80]}'"
        s1.status = "complete"
        stages.append(s1)

        # ── Stage 2: Retrieve Memory ──────────────────────────────────────────
        s2 = PipelineStage("Retrieve Memory")
        s2.status = "running"
        t = time.perf_counter()
        tags = task.lower().split()[:8]
        memories = memory.retrieve(tags, top_k=5)
        context["memories"] = [m.to_dict() for m in memories]
        context["memory_hits"] = len(memories)
        s2.duration_ms = (time.perf_counter() - t) * 1000
        s2.result = f"Retrieved {len(memories)} relevant memory entries"
        s2.status = "complete"
        stages.append(s2)

        # ── Stage 3: Knowledge Graph Query ────────────────────────────────────
        s3 = PipelineStage("Knowledge Graph Query")
        s3.status = "running"
        t = time.perf_counter()
        first_word = task.split()[0] if task.split() else "system"
        kg_result = knowledge_graph.subgraph_for_entity(first_word, depth=1)
        context["knowledge_edges"] = len(kg_result.get("edges", []))
        s3.duration_ms = (time.perf_counter() - t) * 1000
        s3.result = f"KG query: {len(kg_result.get('nodes', []))} nodes, {context['knowledge_edges']} edges"
        s3.status = "complete"
        stages.append(s3)

        # ── Stage 4: ORION Decomposition ──────────────────────────────────────
        s4 = PipelineStage("ORION: Task Decomposition")
        s4.status = "running"
        t = time.perf_counter()
        orion_out = orion.run(task, context)
        agent_outputs.append(orion_out)
        context["agents_consulted"] = ["ORION"]
        s4.duration_ms = (time.perf_counter() - t) * 1000
        s4.result = orion_out.conclusion[:200]
        s4.status = "complete"
        stages.append(s4)

        # ── Stage 5: Specialist Agent Ensemble ───────────────────────────────
        s5 = PipelineStage("Specialist Agent Ensemble")
        s5.status = "running"
        t = time.perf_counter()
        selected = self._select_agents(task)
        for agent in selected:
            out = agent.run(task, context)
            agent_outputs.append(out)
            context["agents_consulted"].append(agent.display_name)
        s5.duration_ms = (time.perf_counter() - t) * 1000
        s5.result = f"Consulted: {', '.join(a.display_name for a in selected)}"
        s5.status = "complete"
        stages.append(s5)

        # ── Stage 6: Simulation ───────────────────────────────────────────────
        s6 = PipelineStage("Simulation Engine")
        s6.status = "running"
        t = time.perf_counter()
        sim = simulation_engine.simulate(task, context, depth=settings.simulation_depth)
        context["simulation"] = sim.to_dict()
        s6.duration_ms = (time.perf_counter() - t) * 1000
        s6.result = f"Optimal: {sim.optimal.name} (EV={sim.optimal.expected_value:.2f})" if sim.optimal else "No optimal found"
        s6.status = "complete"
        stages.append(s6)

        # ── Stage 7: Critic Review ────────────────────────────────────────────
        s7 = PipelineStage("Critic Review")
        s7.status = "running"
        t = time.perf_counter()
        avg_confidence = sum(o.confidence for o in agent_outputs) / len(agent_outputs)
        conflicts = self._detect_conflicts(agent_outputs)
        s7.duration_ms = (time.perf_counter() - t) * 1000
        s7.result = f"Ensemble confidence: {avg_confidence:.2f}. Conflicts: {len(conflicts)}"
        s7.status = "complete"
        stages.append(s7)

        # ── Stage 8: Risk Analysis ────────────────────────────────────────────
        s8 = PipelineStage("Risk Analysis")
        s8.status = "running"
        t = time.perf_counter()
        risk_level = self._assess_risk(task, agent_outputs)
        s8.duration_ms = (time.perf_counter() - t) * 1000
        s8.result = f"Risk level: {risk_level}"
        s8.status = "complete"
        stages.append(s8)

        # ── Stage 9: Governance Check ─────────────────────────────────────────
        s9 = PipelineStage("Governance Check")
        s9.status = "running"
        t = time.perf_counter()
        ethics = ethics_engine.evaluate(task, context)
        context["ethical_score"] = ethics.score
        s9.duration_ms = (time.perf_counter() - t) * 1000
        if ethics.hard_blocked:
            s9.result = f"BLOCKED — ethical hard constraint violated (score={ethics.score:.2f})"
            s9.status = "failed"
        else:
            s9.result = f"Governance PASS (score={ethics.score:.2f}, review_required={ethics.requires_review})"
            s9.status = "complete"
        stages.append(s9)

        # ── Stage 10: Decision ────────────────────────────────────────────────
        s10 = PipelineStage("Decision Engine")
        s10.status = "running"
        t = time.perf_counter()
        # Synthesize best agent output
        best_out = max(agent_outputs, key=lambda o: o.confidence)
        decision = decision_engine.evaluate(task, best_out.to_dict(), ethical_score=ethics.score)
        s10.duration_ms = (time.perf_counter() - t) * 1000
        s10.result = f"Score={decision.score:.3f}, Approved={decision.approved}"
        s10.status = "complete"
        stages.append(s10)

        # ── Stage 11: Update Memory ───────────────────────────────────────────
        s11 = PipelineStage("Update Memory")
        s11.status = "running"
        t = time.perf_counter()
        memory.store(
            content={
                "task": task,
                "conclusion": best_out.conclusion,
                "confidence": best_out.confidence,
                "decision_score": decision.score,
                "approved": decision.approved,
            },
            layer=MemoryLayer.EPISODIC,
            tags=task.lower().split()[:6],
            confidence=best_out.confidence,
        )
        s11.duration_ms = (time.perf_counter() - t) * 1000
        s11.result = "Episodic memory updated with task outcome"
        s11.status = "complete"
        stages.append(s11)

        total_ms = (time.perf_counter() - t_start) * 1000
        aura_score = self._compute_aura(agent_outputs, decision, ethics.score)
        result = PipelineResult(
            task_id=task_id,
            task=task,
            stages=stages,
            agent_outputs=agent_outputs,
            decision=decision,
            aura_score=aura_score,
            duration_ms=total_ms,
        )
        self._history.append(result)
        log.info("pipeline.complete", task_id=task_id, aura=round(aura_score, 3), ms=round(total_ms, 1))
        return result

    def _select_agents(self, task: str) -> list:
        task_lower = task.lower()
        selected = []
        if any(w in task_lower for w in ["analyze", "data", "research", "what", "why", "how"]):
            selected.append(sol)
        if any(w in task_lower for w in ["build", "code", "implement", "fix", "debug", "optimize"]):
            selected.append(kade)
        if any(w in task_lower for w in ["design", "architect", "structure", "system"]):
            selected.append(nyx)
        if any(w in task_lower for w in ["explain", "report", "communicate", "understand"]):
            selected.append(mira)
        if any(w in task_lower for w in ["create", "generate", "explore", "idea", "novel"]):
            selected.append(vex)
        if not selected:
            selected = [sol, nyx]
        return selected[:3]

    def _detect_conflicts(self, outputs: list[AgentOutput]) -> list[str]:
        conflicts = []
        confidences = [o.confidence for o in outputs]
        if max(confidences) - min(confidences) > 0.4:
            conflicts.append("High confidence variance across agents")
        return conflicts

    def _assess_risk(self, task: str, outputs: list[AgentOutput]) -> str:
        avg_uncertainty = sum(o.uncertainty for o in outputs) / len(outputs)
        if avg_uncertainty > 0.5:
            return "HIGH"
        if avg_uncertainty > 0.25:
            return "MEDIUM"
        return "LOW"

    def _compute_aura(self, outputs: list[AgentOutput], decision: Decision, ethical_score: float) -> float:
        """AURA = (Intelligence × Adaptation × Reliability) / (Cost × Risk × Uncertainty)"""
        intelligence = sum(o.confidence for o in outputs) / len(outputs)
        adaptation = 0.85  # static for now; would track over time
        reliability = 1.0 - sum(o.uncertainty for o in outputs) / len(outputs)
        cost = 0.2
        risk = max(0.01, 1.0 - (decision.score + 3) / 6) if decision else 0.5
        uncertainty = sum(o.uncertainty for o in outputs) / len(outputs)
        numerator = intelligence * adaptation * reliability
        denominator = max(0.001, cost * risk * uncertainty)
        return min(1.0, numerator / (denominator * 3))

    def history(self, limit: int = 10) -> list[dict]:
        return [r.to_dict() for r in self._history[-limit:]]


pipeline = ReasoningPipeline()
