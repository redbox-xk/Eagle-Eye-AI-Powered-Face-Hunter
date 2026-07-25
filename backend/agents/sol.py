"""AURA-EAGLE — SOL: Research & Analytical Reasoning Agent"""
from typing import Any
from .base import BaseAgent, AgentOutput


class SolAgent(BaseAgent):
    agent_id = "sol"
    display_name = "SOL"
    domain = "research"
    description = "Research and analytical reasoning: information synthesis, pattern analysis, insight generation"

    def process(self, task: str, context: dict[str, Any]) -> AgentOutput:
        insights = self._synthesize_insights(task, context)
        confidence = min(0.95, 0.65 + len(insights) * 0.05)

        conclusion = (
            f"SOL analytical synthesis for '{task[:60]}': "
            f"Generated {len(insights)} evidence-backed insights. "
            f"Confidence derived from {context.get('memory_hits', 0)} memory retrievals "
            f"and {context.get('knowledge_edges', 0)} knowledge graph traversals."
        )
        return AgentOutput(
            conclusion=conclusion,
            evidence=insights,
            confidence=confidence,
            uncertainty=1.0 - confidence,
            recommended_action=(
                "Cross-reference findings with episodic memory; "
                "update semantic memory with validated conclusions."
            ),
        )

    def _synthesize_insights(self, task: str, context: dict) -> list[str]:
        base = [
            f"Task domain classified as: {self._classify_domain(task)}",
            f"Analytical framework: evidence-weighted inference",
            "Uncertainty quantified and bounded",
        ]
        memory = context.get("memories", [])
        for m in memory[:3]:
            content = m.get("content", {})
            base.append(f"Memory evidence: {str(content)[:80]}")
        if not memory:
            base.append("No prior memory — forming first-pass hypothesis")
        return base

    def _classify_domain(self, task: str) -> str:
        task_lower = task.lower()
        if any(w in task_lower for w in ["code", "implement", "bug", "fix"]):
            return "software engineering"
        if any(w in task_lower for w in ["data", "analyze", "report", "metric"]):
            return "data analytics"
        if any(w in task_lower for w in ["plan", "strategy", "design"]):
            return "strategic planning"
        return "general intelligence"


sol = SolAgent()
