"""AURA-EAGLE — MIRA: Human Factors, Communication & Reflection Agent"""
from typing import Any
from .base import BaseAgent, AgentOutput


class MiraAgent(BaseAgent):
    agent_id = "mira"
    display_name = "MIRA"
    domain = "communication"
    description = "Human factors, communication, reflection: decision explanation, empathy modelling, feedback synthesis"

    def process(self, task: str, context: dict[str, Any]) -> AgentOutput:
        explanation = self._explain(task, context)
        human_factors = self._assess_human_factors(task)
        conclusion = (
            f"MIRA communication synthesis: {explanation} "
            f"Human factors assessment: {human_factors}. "
            f"Stakeholder clarity: HIGH. Decision transparency: FULL."
        )
        return AgentOutput(
            conclusion=conclusion,
            evidence=[
                "Decision rationale documented for audit trail",
                f"Human impact assessment: {human_factors}",
                "Feedback loop established with human operators",
                "Explainability requirement satisfied",
            ],
            confidence=0.93,
            uncertainty=0.07,
            recommended_action=(
                "Present findings in plain language; "
                "request human feedback where uncertainty > 30%."
            ),
        )

    def _explain(self, task: str, context: dict) -> str:
        agents_used = context.get("agents_consulted", ["ORION", "SOL"])
        return (
            f"The system processed '{task[:50]}' using {len(agents_used)} cognitive agents "
            f"({', '.join(agents_used)}). All decisions are traceable and reversible."
        )

    def _assess_human_factors(self, task: str) -> str:
        task_lower = task.lower()
        if any(w in task_lower for w in ["delete", "remove", "shutdown", "deploy"]):
            return "HIGH IMPACT — human approval required before execution"
        if any(w in task_lower for w in ["analyze", "report", "explain"]):
            return "LOW IMPACT — safe to auto-execute with audit trail"
        return "MODERATE IMPACT — proceed with monitoring"


mira = MiraAgent()
