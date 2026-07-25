"""AURA-EAGLE — Base Agent Contract"""
from __future__ import annotations
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import structlog

log = structlog.get_logger()


@dataclass
class AgentOutput:
    conclusion: str
    evidence: list[str]
    confidence: float       # [0,1]
    uncertainty: float      # [0,1]
    recommended_action: str
    agent_id: str = ""
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "conclusion": self.conclusion,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "recommended_action": self.recommended_action,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """
    Abstract base for all AURA-EAGLE cognitive agents.
    Every agent wraps process() with timing, logging, and error handling.
    """

    agent_id: str = "base"
    display_name: str = "Base Agent"
    domain: str = "general"
    description: str = ""

    def __init__(self):
        self._invocations: int = 0
        self._total_ms: float = 0.0
        self._errors: int = 0
        self._last_output: AgentOutput | None = None

    def run(self, task: str, context: dict[str, Any] | None = None) -> AgentOutput:
        context = context or {}
        t0 = time.perf_counter()
        self._invocations += 1
        try:
            output = self.process(task, context)
            output.agent_id = self.agent_id
            output.duration_ms = (time.perf_counter() - t0) * 1000
            self._total_ms += output.duration_ms
            self._last_output = output
            log.info(
                "agent.run",
                agent=self.agent_id,
                confidence=round(output.confidence, 3),
                ms=round(output.duration_ms, 1),
            )
            return output
        except Exception as exc:
            self._errors += 1
            log.error("agent.error", agent=self.agent_id, error=str(exc))
            return AgentOutput(
                conclusion=f"Agent {self.agent_id} encountered an error: {exc}",
                evidence=[],
                confidence=0.0,
                uncertainty=1.0,
                recommended_action="Investigate agent failure",
                agent_id=self.agent_id,
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

    @abstractmethod
    def process(self, task: str, context: dict[str, Any]) -> AgentOutput:
        ...

    def status(self) -> dict:
        avg_ms = self._total_ms / self._invocations if self._invocations else 0
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "domain": self.domain,
            "description": self.description,
            "invocations": self._invocations,
            "errors": self._errors,
            "avg_latency_ms": round(avg_ms, 2),
            "last_confidence": round(self._last_output.confidence, 4) if self._last_output else None,
            "last_conclusion": self._last_output.conclusion[:120] if self._last_output else None,
        }
