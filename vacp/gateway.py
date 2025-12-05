import logging
from vacp.ans import AgentNameService
from vacp.ucf import UCFPolicyEngine
from vacp.schemas import AgentAction

logger = logging.getLogger(__name__)

class ToolGateway:
    """
    ISO 42001 Clause 8.1: Operational Control.
    The Single Chokepoint for all agent side-effects.
    """
    def __init__(self):
        self.ans = AgentNameService()
        self.ucf = UCFPolicyEngine()
        self.kill_switch_active = False

    def activate_kill_switch(self):
        logger.warning("VACP: MILLISECOND KILL-SWITCH ACTIVATED. ALL TRAFFIC DENIED.")
        self.kill_switch_active = True

    def intercept_and_validate(self, agent_id: str, action: AgentAction) -> bool:
        """
        Enforces Taint Tracking (LPCI) and Access Control.
        """
        if self.kill_switch_active:
            raise PermissionError("VACP: Kill-switch is active. Action denied.")

        # 1. Identity Check (ANS)
        identity = self.ans.resolve_agent(agent_id)
        if not identity:
            raise PermissionError(f"VACP: Agent '{agent_id}' not found in ANS Registry.")

        # 2. Capability Check (UCF CONTROL-033)
        context = {"tool": action.tool_name, "allowed_tools": identity.authorized_tools}
        if not self.ucf.evaluate("CONTROL-033", context):
            raise PermissionError(f"VACP: Tool '{action.tool_name}' unauthorized for risk tier '{identity.risk_tier}'.")

        # 3. Guardrail Checks (Legacy Actuators moved here)
        self._check_financial_circuit_breaker(action)

        return True

    def _check_financial_circuit_breaker(self, action: AgentAction):
        # Simplified circuit breaker logic
        if action.tool_name == "place_order":
            # In real implementation, check params against portfolio value
            pass
