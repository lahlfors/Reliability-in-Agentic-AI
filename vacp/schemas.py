from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
import time

class AgentIdentity(BaseModel):
    """Corresponds to the DID and Risk Tier in ANS."""
    agent_id: str
    did: str
    risk_tier: Literal["Low", "Medium", "High"]
    authorized_tools: List[str]
    training_hash: str  # For Data Provenance (Annex A.7)

class AgentAction(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class SafetyAssessment(BaseModel):
    """Output from AgentGuard and Janus."""
    p_failure: float
    unsafe_control_action_detected: bool
    red_team_vulnerability: Optional[str] = None

class GOADecision(BaseModel):
    """Output of the Governing-Orchestrator Agent (SSVC)."""
    decision: Literal["TRACK", "MONITOR", "QUARANTINE"]
    justification: str
    latency_ms: float

class AuditLog(BaseModel):
    """Zero-Knowledge Audit Trail Entry."""
    timestamp: float = Field(default_factory=time.time)
    agent_id: str
    action_hash: str
    decision: str
    zk_proof: str  # Mock Groth16 proof string
