"""AURA-EAGLE — Decision Engine

DecisionScore: D = (Value + Confidence + Evidence) - (Risk + Cost + Uncertainty)
Execute only when Confidence threshold is satisfied.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import structlog

from backend.core.config import settings

log = structlog.get_logger()


@dataclass
class Decision:
    task: str
    value: float        # Expected utility  [0,1]
    confidence: float   # Belief in correctness [0,1]
    evidence: float     # Strength of supporting evidence [0,1]
    risk: float         # Probability × severity of failure [0,1]
    cost: float         # Resource / effort cost [0,1]
    uncertainty: float  # Epistemic uncertainty [0,1]
    conclusion: str = ""
    evidence_items: list[str] = field(default_factory=list)
    recommended_action: str = ""
    agent_id: str = "system"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    created_at: datetime = field(default_factory=datetime.utcnow)
    ethical_score: float = 1.0
    approved: bool = False

    @property
    def score(self) -> float:
        """D = (Value + Confidence + Evidence) - (Risk + Cost + Uncertainty)"""
        return (self.value + self.confidence + self.evidence) - (self.risk + self.cost + self.uncertainty)

    @property
    def should_execute(self) -> bool:
        return self.confidence >= settings.confidence_threshold and self.score > 0

    @property
    def normalized_score(self) -> float:
        """Map score from [-3,3] to [0,1]"""
        return (self.score + 3) / 6

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "agent_id": self.agent_id,
            "score": round(self.score, 4),
            "normalized_score": round(self.normalized_score, 4),
            "value": self.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "risk": self.risk,
            "cost": self.cost,
            "uncertainty": self.uncertainty,
            "conclusion": self.conclusion,
            "evidence_items": self.evidence_items,
            "recommended_action": self.recommended_action,
            "ethical_score": self.ethical_score,
            "approved": self.approved,
            "should_execute": self.should_execute,
            "created_at": self.created_at.isoformat(),
        }


class DecisionEngine:
    """Scores and approves decisions based on the AURA-EAGLE decision formula."""

    def __init__(self):
        self._history: list[Decision] = []

    def evaluate(
        self,
        task: str,
        agent_output: dict[str, Any],
        ethical_score: float = 1.0,
        cost_estimate: float = 0.2,
    ) -> Decision:
        confidence = float(agent_output.get("confidence", 0.5))
        uncertainty = float(agent_output.get("uncertainty", 0.3))
        evidence_items = agent_output.get("evidence", [])

        # Derive value from conclusion sentiment / content
        conclusion = agent_output.get("conclusion", "")
        value = self._estimate_value(conclusion, agent_output)
        evidence_strength = min(len(evidence_items) / 5.0, 1.0) * 0.8 + 0.2
        risk = self._estimate_risk(task, agent_output)

        decision = Decision(
            task=task,
            value=value,
            confidence=confidence,
            evidence=evidence_strength,
            risk=risk,
            cost=cost_estimate,
            uncertainty=uncertainty,
            conclusion=conclusion,
            evidence_items=evidence_items,
            recommended_action=agent_output.get("recommended_action", ""),
            agent_id=agent_output.get("agent_id", "unknown"),
            ethical_score=ethical_score,
            approved=False,
        )
        decision.approved = decision.should_execute and ethical_score >= settings.ethical_threshold
        self._history.append(decision)
        log.info(
            "decision.evaluated",
            id=decision.id,
            score=round(decision.score, 3),
            approved=decision.approved,
        )
        return decision

    def _estimate_value(self, conclusion: str, agent_output: dict) -> float:
        positive_words = ["success", "optimal", "efficient", "improved", "solved", "complete", "found"]
        negative_words = ["fail", "error", "impossible", "blocked", "unknown"]
        text = (conclusion + " " + str(agent_output)).lower()
        pos = sum(1 for w in positive_words if w in text)
        neg = sum(1 for w in negative_words if w in text)
        return max(0.1, min(1.0, 0.5 + pos * 0.1 - neg * 0.15))

    def _estimate_risk(self, task: str, agent_output: dict) -> float:
        risk_words = ["delete", "modify", "external", "deploy", "critical", "production"]
        text = (task + " " + str(agent_output)).lower()
        risk = sum(0.12 for w in risk_words if w in text)
        return min(risk, 0.8)

    def history(self, limit: int = 20) -> list[dict]:
        return [d.to_dict() for d in self._history[-limit:]]

    def stats(self) -> dict:
        if not self._history:
            return {"total": 0, "approved": 0, "approval_rate": 0.0, "avg_score": 0.0}
        approved = sum(1 for d in self._history if d.approved)
        return {
            "total": len(self._history),
            "approved": approved,
            "approval_rate": approved / len(self._history),
            "avg_score": sum(d.score for d in self._history) / len(self._history),
        }


decision_engine = DecisionEngine()
