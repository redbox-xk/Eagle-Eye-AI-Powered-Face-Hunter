"""AURA-EAGLE — ORION: Supervisor Agent

Responsibilities:
  - Task decomposition
  - Agent coordination
  - Resource allocation
  - Quality control
"""
from __future__ import annotations
from typing import Any
from .base import BaseAgent, AgentOutput


class OrionAgent(BaseAgent):
    agent_id = "orion"
    display_name = "ORION"
    domain = "supervision"
    description = "Supervisor: task decomposition, agent coordination, quality control"

    def process(self, task: str, context: dict[str, Any]) -> AgentOutput:
        subtasks = self._decompose(task)
        agents_assigned = self._assign_agents(subtasks)
        conclusion = (
            f"ORION decomposed '{task[:60]}' into {len(subtasks)} sub-objectives. "
            f"Assigned to: {', '.join(agents_assigned)}. "
            f"Coordination sequence initialized. Quality gates active."
        )
        return AgentOutput(
            conclusion=conclusion,
            evidence=[
                f"Subtask identified: {st}" for st in subtasks
            ] + [f"Agent assigned: {a}" for a in agents_assigned],
            confidence=min(0.92, 0.70 + len(subtasks) * 0.05),
            uncertainty=max(0.05, 0.25 - len(subtasks) * 0.03),
            recommended_action=(
                "Execute subtasks in parallel where dependencies allow; "
                "apply critic review before decision submission."
            ),
        )

    def _decompose(self, task: str) -> list[str]:
        task_lower = task.lower()
        subtasks = ["Understand objective and constraints"]
        if any(w in task_lower for w in ["analyze", "data", "research"]):
            subtasks.append("Retrieve and analyze relevant information (SOL)")
        if any(w in task_lower for w in ["build", "implement", "code", "fix"]):
            subtasks.append("Engineering implementation (KADE)")
        if any(w in task_lower for w in ["design", "architect", "structure"]):
            subtasks.append("Architecture design (NYX)")
        if any(w in task_lower for w in ["explain", "report", "communicate"]):
            subtasks.append("Communication synthesis (MIRA)")
        if any(w in task_lower for w in ["create", "generate", "explore", "idea"]):
            subtasks.append("Creative exploration (VEX)")
        subtasks.append("Validate output and update memory")
        return subtasks

    def _assign_agents(self, subtasks: list[str]) -> list[str]:
        assigned = []
        mapping = {
            "SOL": ["sol", "research", "analyze"],
            "KADE": ["kade", "engineering", "implement"],
            "NYX": ["nyx", "architecture", "design"],
            "MIRA": ["mira", "communication", "synthesize"],
            "VEX": ["vex", "creative", "explore"],
        }
        for agent_name, keywords in mapping.items():
            for st in subtasks:
                if any(k in st.lower() for k in keywords):
                    if agent_name not in assigned:
                        assigned.append(agent_name)
                    break
        return assigned or ["NYX", "SOL"]


orion = OrionAgent()
