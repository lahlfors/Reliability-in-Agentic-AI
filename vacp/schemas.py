from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import time

# --- Existing schemas (Preserved for compatibility) ---

class AgentAction(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    financial_context: Optional[Any] = None

class SafetyAssessment(BaseModel):
    p_failure: float
    unsafe_control_action_detected: bool
    red_team_vulnerability: Optional[str] = None

class GOADecision(BaseModel):
    decision: Literal["TRACK", "MONITOR", "QUARANTINE"]
    justification: str
    latency_ms: float

class AuditLog(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    agent_id: str
    action_hash: str
    decision: str
    zk_proof: str

class AgentIdentity(BaseModel):
    agent_id: str
    did: str
    risk_tier: Literal["Low", "Medium", "High"]
    authorized_tools: List[str]
    training_hash: str


# --- New ISO 42001 / EU AI Act Schemas ---

class HighRiskCategory(str, Enum):
    """EU AI Act Annex III High-Risk Categories (relevant subsets)"""
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    EDUCATION_VOCATIONAL = "education_vocational"
    EMPLOYMENT_HR = "employment_hr"
    ESSENTIAL_SERVICES_FINANCIAL = "essential_services_financial"
    LAW_ENFORCEMENT = "law_enforcement"
    NONE = "none"

class ProviderDetails(BaseModel):
    """Annex IV: Information about the provider"""
    name: str = Field(..., description="Legal name of the provider")
    address: str = Field(..., description="Registered trade address")
    lei_code: Optional[str] = Field(None, description="Legal Entity Identifier (ISO 17442)")
    contact_email: str

class RegulatoryCompliance(BaseModel):
    """Annex IV: Intended Purpose and Classification"""
    intended_purpose: str = Field(..., description="Specific purpose required by Annex IV")
    high_risk_category: HighRiskCategory = Field(default=HighRiskCategory.NONE)
    human_oversight_measures: List[str] = Field(default_factory=list)

class OperationalConstraints(BaseModel):
    """System 5 Policy: Constraints for the Governor"""
    max_autonomy_level: int = Field(..., ge=1, le=5)
    tools_allowed: List[str] = Field(default_factory=list)
    tools_denied: List[str] = Field(default_factory=list, description="Explicit kill-list for tools")
    risk_limits: Dict[str, Any] = Field(default_factory=dict, description="Parametric limits")

class AgentCard(BaseModel):
    """The Master Configuration Artifact (Agent Card)"""
    card_version: str = "1.0"
    agent_name: str
    agent_version: str
    model_hash: Optional[str] = Field(None, description="Integrity hash of the model weights/code")

    provider: ProviderDetails
    regulatory: RegulatoryCompliance
    constraints: OperationalConstraints
