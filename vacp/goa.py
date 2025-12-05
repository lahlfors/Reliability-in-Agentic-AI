import logging
import time
from vacp.schemas import AgentAction, GOADecision
from vacp.agent_guard import AgentGuard
from vacp.janus import JanusMonitor
from vacp.gateway import ToolGateway
from vacp.audit import ZKProver
from vacp.ucf import UCFPolicyEngine

logger = logging.getLogger(__name__)

class GoverningOrchestratorAgent:
    """
    The 'Act' phase of ISO 42001.
    Orchestrates the verification loop and makes the final SSVC decision.
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.agent_guard = AgentGuard()
        self.janus = JanusMonitor()
        self.gateway = ToolGateway()
        self.audit = ZKProver()
        self.ucf = UCFPolicyEngine()

    def process_request(self, action: AgentAction, plan_context: str) -> GOADecision:
        start_time = time.time()
        logger.info(f"GOA: Assessing action '{action.tool_name}' for agent '{self.agent_id}'")

        # 1. Plan (Risk Assessment) - AgentGuard
        self.agent_guard.update_model(action)
        # Assuming High risk for demo purposes, usually fetched from ANS
        p_failure = self.agent_guard.calculate_failure_probability(action, risk_tier="High")

        # 2. Check (Evaluation) - Janus
        vulnerability = self.janus.run_red_team_simulation(action, plan_context)

        # 3. Act (SSVC Decision Tree)
        # Decision Logic:
        # If P_failure > Threshold OR Vulnerability Critical -> QUARANTINE
        # If P_failure Moderate -> MONITOR
        # Else -> TRACK

        decision = "TRACK"

        # UCF Control Check (CONTROL-013)
        ucf_context = {"p_failure": p_failure, "risk_tier": "High"}
        is_safe_prob = self.ucf.evaluate("CONTROL-013", ucf_context)

        if not is_safe_prob or "Vulnerability" in vulnerability and vulnerability != "None":
            decision = "QUARANTINE"
        elif p_failure > 0.05:
            decision = "MONITOR"

        # 4. Enforce Decision
        if decision == "QUARANTINE":
            self.gateway.activate_kill_switch()
            justification = f"High Risk: P(fail)={p_failure}, Janas={vulnerability}"
        else:
            # If not quarantined, try to validate through Gateway
            try:
                self.gateway.intercept_and_validate(self.agent_id, action)
                justification = "Action authorized by VACP."
            except PermissionError as e:
                decision = "QUARANTINE"
                justification = str(e)

        # 5. Audit Trail
        self.audit.log_event(self.agent_id, decision, f"{action.tool_name}:{justification}")

        return GOADecision(
            decision=decision,
            justification=justification,
            latency_ms=(time.time() - start_time) * 1000
        )
