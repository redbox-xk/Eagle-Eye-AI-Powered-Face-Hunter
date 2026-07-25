"""AURA-EAGLE — Ethical Governance Engine

Every action must evaluate:
  1. Authorization
  2. Legality
  3. Safety
  4. Human Impact
  5. Reversibility
  6. Transparency

Ethical Score: E = Benefit - PotentialHarm + Transparency + Accountability
"""
from dataclasses import dataclass
from typing import Any
import structlog

log = structlog.get_logger()

ETHICAL_THRESHOLD = 0.5  # Actions below this require human review


@dataclass
class EthicalAssessment:
    authorized: bool
    legal: bool
    safe: bool
    human_impact: float      # -1 (harmful) → +1 (beneficial)
    reversible: bool
    transparent: bool

    benefit: float = 0.0
    potential_harm: float = 0.0
    accountability: float = 1.0

    @property
    def score(self) -> float:
        """E = Benefit - PotentialHarm + Transparency + Accountability"""
        transparency = 1.0 if self.transparent else 0.0
        return (
            self.benefit
            - self.potential_harm
            + transparency
            + self.accountability
        ) / 3.0  # Normalize to ~[0,1]

    @property
    def requires_review(self) -> bool:
        return self.score < ETHICAL_THRESHOLD

    @property
    def hard_blocked(self) -> bool:
        return not self.authorized or not self.legal or not self.safe

    def to_dict(self) -> dict:
        return {
            "authorized": self.authorized,
            "legal": self.legal,
            "safe": self.safe,
            "human_impact": self.human_impact,
            "reversible": self.reversible,
            "transparent": self.transparent,
            "benefit": self.benefit,
            "potential_harm": self.potential_harm,
            "accountability": self.accountability,
            "score": self.score,
            "requires_review": self.requires_review,
            "hard_blocked": self.hard_blocked,
        }


class EthicsEngine:
    """
    Evaluates actions against the AURA-EAGLE ethical governance framework.
    """

    # Risk keywords that elevate harm scores
    HARM_SIGNALS = [
        "delete", "destroy", "expose", "leak", "bypass", "override",
        "disable", "kill", "harm", "attack", "exploit", "unauthorized",
    ]
    BENEFIT_SIGNALS = [
        "improve", "optimize", "assist", "analyze", "report", "learn",
        "collaborate", "explain", "automate", "monitor", "detect",
    ]

    def evaluate(
        self,
        action: str,
        context: dict[str, Any],
        requester: str = "system",
        high_impact: bool = False,
    ) -> EthicalAssessment:
        action_lower = action.lower()

        harm_score = sum(0.15 for sig in self.HARM_SIGNALS if sig in action_lower)
        harm_score = min(harm_score, 1.0)

        benefit_score = sum(0.15 for sig in self.BENEFIT_SIGNALS if sig in action_lower)
        benefit_score = min(benefit_score + 0.3, 1.0)  # baseline benefit

        assessment = EthicalAssessment(
            authorized=self._check_authorization(requester, context),
            legal=self._check_legal(action, context),
            safe=harm_score < 0.6,
            human_impact=benefit_score - harm_score,
            reversible=not high_impact,
            transparent=True,
            benefit=benefit_score,
            potential_harm=harm_score,
            accountability=1.0,
        )
        log.info(
            "ethics.evaluated",
            action=action[:80],
            score=round(assessment.score, 3),
            blocked=assessment.hard_blocked,
        )
        return assessment

    def _check_authorization(self, requester: str, context: dict) -> bool:
        return requester in ("system", "orion", "operator", "human")

    def _check_legal(self, action: str, context: dict) -> bool:
        illegal_signals = ["circumvent law", "illegal", "violate privacy"]
        action_lower = action.lower()
        return not any(sig in action_lower for sig in illegal_signals)


ethics_engine = EthicsEngine()
