from typing import Dict, Optional
from vacp.schemas import AgentIdentity

class AgentNameService:
    """
    ISO 42001 Clause 4.1: Source of Truth for AIMS Scope.
    Maintains the registry of authorized agents and their risk profiles.
    """
    def __init__(self):
        # In-memory registry simulating the Cryptographic Registry
        self._registry: Dict[str, AgentIdentity] = {
            "financial_coordinator": AgentIdentity(
                agent_id="financial_coordinator",
                did="did:vacp:fin:001",
                risk_tier="High", # Financial advice is high risk
                authorized_tools=["data_analyst", "trading_analyst", "execution_analyst", "place_order", "execute_python_code"],
                training_hash="sha256:deadbeef1234..."
            )
        }

    def resolve_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        return self._registry.get(agent_id)

    def verify_provenance(self, agent_id: str, current_hash: str) -> bool:
        """Annex A.7: Verifies data provenance against the registry."""
        identity = self.resolve_agent(agent_id)
        if not identity:
            return False
        return identity.training_hash == current_hash
