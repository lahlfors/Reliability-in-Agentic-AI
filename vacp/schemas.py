from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
import time
import re

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

# --- Capstone "Glass Wall" Schemas ---

class TradeAction(BaseModel):
    """
    Layer 1: Syntax Trapdoor.
    Strict schema for trade execution to prevent injection and type errors.
    """
    symbol: str
    action: Literal["BUY", "SELL"]
    amount: float
    reason: Optional[str] = None

    @validator('amount', pre=True)
    def validate_amount_type(cls, v):
        """Disallow string representations of numbers that might contain suffixes or be malformed."""
        if isinstance(v, str):
            # Fail hard on strings like "10k" or "1,000,000" if we want strict float
            # Pydantic default coercion might allow "1000", but we want to fail "1,000,000" or "10k"
            # Capstone Req: "Fail hard on invalid ones"
            if "," in v or "k" in v.lower() or "m" in v.lower():
                raise ValueError("Amount must be a pure number, not a string with formatters.")
        return v

    @validator('reason', 'symbol')
    def prevent_sql_injection(cls, v):
        """
        Layer 1 Defense: Sanitization against SQL Injection.
        """
        if v is None:
            return v

        # Common SQL Injection patterns
        sql_patterns = [
            r"DROP\s+TABLE",
            r"DELETE\s+FROM",
            r"INSERT\s+INTO",
            r"SELECT\s+.*FROM",
            r";--",
            r"' OR '1'='1"
        ]

        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Security Alert: Potential SQL Injection detected in field: {v}")

        return v
