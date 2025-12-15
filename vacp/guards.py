import random
from typing import Dict, Any
from .interfaces import Verifier, ConsensusStrategy

class ShieldGemmaMock(Verifier):
    """
    Layer 3: Simulates a fine-tuned Safety LLM (e.g., ShieldGemma 8B).
    Checks for semantic hazards like 'jailbreak' patterns or 'toxic' content.
    """
    def verify(self, content: str, context: Dict[str, Any]) -> bool:
        # Heuristic simulation of a neural classifier
        unsafe_patterns = [
            "ignore previous instructions",
            "system_override",
            "drop table",
            "read_internal_logs",
            "read_file",
            "/etc/secrets.txt",
            "debug_system_check" # "Social engineered" tool name
        ]

        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content)

        content_lower = content.lower()

        # Check action name specifically for "The Insider" / Disguise
        action = context.get("action", "").lower()
        if action == "debug_system_check":
             print(f"[ShieldGemma] Blocked deceptive tool usage: {action}")
             return False

        for pattern in unsafe_patterns:
            if pattern in content_lower:
                print(f"[ShieldGemma] Blocked unsafe content: {pattern}")
                return False

        # Additional check: If tool is "read_file" or "read_internal_logs", usually blocked by Policy,
        # but Sentinel acts as second line.
        # Note: The Agent might try to call "read_file" which is NOT in the allowed tool list.
        # But if it were, Sentinel guards the *arguments* too.

        return True

class EnsembleConsensus(ConsensusStrategy):
    """
    Layer 4: Simulates querying 3 frontier models (GPT-4, Claude 3.5, Gemini 1.5).
    """
    def vote(self, proposal: str, context: Dict[str, Any]) -> bool:
        print(f"[Consensus] Initiating voting on: {proposal[:50]}...")

        # Mocking model responses
        votes = {
            "gpt-4": self._mock_model_vote("gpt-4", proposal),
            "claude-3-opus": self._mock_model_vote("claude-3-opus", proposal),
            "gemini-1.5-pro": self._mock_model_vote("gemini-1.5-pro", proposal)
        }

        yeas = sum(1 for v in votes.values() if v)
        nays = sum(1 for v in votes.values() if not v)

        print(f"[Consensus] Result: {yeas} Allow / {nays} Block. Votes: {votes}")
        return yeas > nays

    def _mock_model_vote(self, model_name: str, proposal: str) -> bool:
        # Simulate probabilistic disagreement on edge cases
        if "borderline" in proposal:
            return random.choice([True, False])
        return True
