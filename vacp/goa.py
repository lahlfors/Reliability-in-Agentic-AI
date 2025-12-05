import logging
import time
from typing import Optional
from vacp.schemas import GOADecision
from vacp.audit import ZKProver

logger = logging.getLogger(__name__)

class GoverningOrchestratorAgent:
    """
    The 'Act' phase of ISO 42001.
    Central Manager of the Kill Switch.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GoverningOrchestratorAgent, cls).__new__(cls)
        return cls._instance

    def __init__(self, agent_id: str = "financial_coordinator"):
        if hasattr(self, "initialized"):
            return
        self.agent_id = agent_id
        self.audit = ZKProver()
        self._kill_switch_active = False
        self._quarantine_reason = ""
        self.initialized = True

    def activate_kill_switch(self, reason: str):
        """Activates the millisecond kill-switch."""
        if not self._kill_switch_active:
            logger.critical(f"GOA: ACTIVATING KILL-SWITCH. Reason: {reason}")
            self._kill_switch_active = True
            self._quarantine_reason = reason
            self._audit_decision("QUARANTINE", reason)

    def is_quarantined(self) -> (bool, str):
        """Returns True if the agent is quarantined, plus the reason."""
        return self._kill_switch_active, self._quarantine_reason

    def reset(self):
        """Resets the kill switch (Manual override)."""
        logger.info("GOA: Resetting Kill-Switch.")
        self._kill_switch_active = False
        self._quarantine_reason = ""
        self._audit_decision("TRACK", "Manual Reset")

    def _audit_decision(self, decision: str, justification: str):
        self.audit.log_event(self.agent_id, decision, justification)
