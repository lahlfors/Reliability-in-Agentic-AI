from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PolicyResult:
    allowed: bool
    risk_level: RiskLevel
    reasons: List[str]
    requirements: List[str]  # e.g., ["consensus_required", "human_approval"]

class PolicyEngine(ABC):
    """Layer 2: Policy-as-Code Interface (OPA Pattern)"""
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        pass

class Verifier(ABC):
    """Layer 3: Semantic Verifier Interface (Small LLM Pattern)"""
    @abstractmethod
    def verify(self, content: str, context: Dict[str, Any]) -> bool:
        pass

class ConsensusStrategy(ABC):
    """Layer 4: Consensus Engine Interface"""
    @abstractmethod
    def vote(self, proposal: str, context: Dict[str, Any]) -> bool:
        pass
