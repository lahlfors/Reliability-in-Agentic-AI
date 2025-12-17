import logging
import time
import os
from typing import Optional
from vacp.schemas import GOADecision, AgentCard
from vacp.audit import ZKProver
from vacp.card_loader import CardLoader
from vacp.state_manager import StateManager, FileBasedStateManager

logger = logging.getLogger(__name__)

class GoverningOrchestratorAgent:
    """
    The 'Act' phase of ISO 42001.
    Central Manager of the Kill Switch.
    Refactored to use persistent StateManager instead of in-memory singleton state.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GoverningOrchestratorAgent, cls).__new__(cls)
        return cls._instance

    def __init__(self, agent_card_path: str = "financial-advisor/agent.json", state_manager: StateManager = None):
        if hasattr(self, "initialized"):
            return

        self.agent_id = "unknown" # Will be updated from card
        self.audit = ZKProver()

        # State Persistence
        self.state_manager = state_manager or FileBasedStateManager()

        self.agent_card: Optional[AgentCard] = None
        self.gateway = None # Will link to global gateway

        # 1. Load the Identity/Policy Card
        try:
             if os.path.exists(agent_card_path):
                loader = CardLoader(enforce_signature=True)
                self.agent_card = loader.load_card(agent_card_path)
                self.agent_id = self.agent_card.agent_name
                logger.info(f"GOA: Successfully loaded Agent Card for {self.agent_id}")

             else:
                logger.warning(f"GOA: Agent Card not found at {agent_card_path}. Starting without specific policy.")

        except Exception as e:
            msg = f"GOA: Startup Error - Failed to load Agent Card: {e}"
            logger.critical(msg)
            # Activate kill switch immediately via State Manager
            self.activate_kill_switch(msg)

        self.initialized = True

    def execute_tool(self, tool_name: str, args: dict):
        """
        Orchestrator entry point for tool execution (if used directly).
        Delegates to Gateway.
        """
        return True

    def activate_kill_switch(self, reason: str):
        """Activates the millisecond kill-switch."""
        is_active, _ = self.state_manager.get_kill_switch_state()
        if not is_active:
            logger.critical(f"GOA: ACTIVATING KILL-SWITCH. Reason: {reason}")
            self.state_manager.set_kill_switch_state(True, reason)
            self._audit_decision("QUARANTINE", reason)

    def is_quarantined(self) -> (bool, str):
        """Returns True if the agent is quarantined, plus the reason."""
        return self.state_manager.get_kill_switch_state()

    def reset(self):
        """Resets the kill switch (Manual override)."""
        logger.info("GOA: Resetting Kill-Switch.")
        self.state_manager.set_kill_switch_state(False, "")
        self._audit_decision("TRACK", "Manual Reset")

    def _audit_decision(self, decision: str, justification: str):
        self.audit.log_event(self.agent_id, decision, justification)
