from typing import Dict, Any
from dataclasses import dataclass
from .interfaces import PolicyResult, RiskLevel

@dataclass
class ReviewPacket:
    summary: str
    risk_score: int
    recommended_action: str
    raw_context: Dict[str, Any]

class ReviewerAgent:
    """
    Pre-computes context for the human operator to minimize latency.
    """
    def pre_compute_context(self, violation: PolicyResult, context: Dict[str, Any]) -> ReviewPacket:
        # In a real system, this would call an LLM to summarize the logs
        summary = f"Agent attempted {context.get('action')} which triggered {violation.risk_level.value} risk policies."

        recommendation = "REJECT"
        if violation.risk_level == RiskLevel.HIGH and "consensus_required" in violation.requirements:
             recommendation = "APPROVE_WITH_AUDIT"

        return ReviewPacket(
            summary=summary,
            risk_score=90 if violation.risk_level == RiskLevel.CRITICAL else 50,
            recommended_action=recommendation,
            raw_context=context
        )
