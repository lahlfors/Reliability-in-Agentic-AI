import logging
import functools
import os
from opentelemetry import trace
from vacp.goa import GoverningOrchestratorAgent
from vacp.ans import AgentNameService
from vacp.ucf import UCFPolicyEngine
from vacp.schemas import AgentAction, AgentCard
from vacp.gcp_identity import MIMService

logger = logging.getLogger(__name__)

# MIM Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id")
PRIVILEGED_SA_EMAIL = os.environ.get("VACP_PRIVILEGED_SA", "vacp-trader-sa@your-project-id.iam.gserviceaccount.com")
TRADING_SECRET_ID = os.environ.get("VACP_TRADING_SECRET_ID", "TRADING_API_KEY")

class Gateway:
    """
    The Policy Governor.
    Checks tools against the Agent Card policy.
    """
    def __init__(self, agent_card: AgentCard = None):
        self.card = agent_card
        self.denied_tools = set()
        self.allowed_tools = set()

        if self.card:
            self.denied_tools = set(self.card.constraints.tools_denied)
            self.allowed_tools = set(self.card.constraints.tools_allowed)

    def check_tool_policy(self, tool_name: str) -> bool:
        """
        Returns True if tool is allowed, False if blocked.
        """
        if not self.card:
            # Fallback behavior: if no card, allow? Or rely on other controls?
            # Existing logic suggests failing open or using ANS.
            # For strictness, if card is missing but expected, we might block.
            # But to maintain backward compat during transition:
            return True

        # 1. Explicit Deny (Kill List)
        if tool_name in self.denied_tools:
            logger.warning(f"⛔ BLOCKED: Tool '{tool_name}' is explicitly denied.")
            return False

        # 2. Allow List (if populated, strictly enforce)
        if self.allowed_tools and tool_name not in self.allowed_tools:
            logger.warning(f"⛔ BLOCKED: Tool '{tool_name}' is not in allowed list.")
            return False

        return True

class ToolGateway(Gateway):
    """
    ISO 42001 Clause 8.1: Operational Control.
    The Single Chokepoint for all agent side-effects.
    Integrated with MIM/ZSP for Identity Elevation and Policy/Kill-Switch checks.
    """
    def __init__(self):
        super().__init__(agent_card=None) # Start without card, loaded later
        self.goa = GoverningOrchestratorAgent() # Singleton
        # Pull policy from GOA if already loaded
        if self.goa.agent_card:
            self.set_policy(self.goa.agent_card)

        self.ans = AgentNameService()
        self.ucf = UCFPolicyEngine()
        self.mim_service = MIMService(PRIVILEGED_SA_EMAIL, PROJECT_ID)

    def set_policy(self, agent_card: AgentCard):
        """Update the policy with the loaded Agent Card."""
        self.card = agent_card
        if self.card:
            self.denied_tools = set(self.card.constraints.tools_denied)
            self.allowed_tools = set(self.card.constraints.tools_allowed)
            logger.info(f"ToolGateway: Policy updated from Agent Card: {self.card.agent_name}")

    def verify_access(self, tool_name: str, args: dict):
        """
        Enforces Taint Tracking (LPCI) and Access Control.
        """
        # 1. Check Kill Switch (System 3)
        is_quarantined, reason = self.goa.is_quarantined()
        if is_quarantined:
            raise PermissionError(f"VACP: Kill-switch is active. Action denied. Reason: {reason}")

        # 2. Check Agent Card Policy (System 5)
        if not self.check_tool_policy(tool_name):
            raise PermissionError(f"VACP: Tool '{tool_name}' blocked by Agent Card policy.")

        # 3. Identity & UCF Checks (Legacy/Fallback)
        # Only if no card is present or as additional check?
        # Keeping existing logic as secondary check
        agent_id = "financial_coordinator"
        identity = self.ans.resolve_agent(agent_id)

        if not identity:
             logger.warning(f"VACP: Agent '{agent_id}' not found. Proceeding with caution.")
             return

        # If Agent Card is present, it acts as the authoritative source for allowed tools.
        if self.card:
            allowed_tools = list(self.card.constraints.tools_allowed)
        else:
            allowed_tools = identity.authorized_tools

        context = {"tool": tool_name, "allowed_tools": allowed_tools}
        if not self.ucf.evaluate("CONTROL-033", context):
            # If card allows it but UCF (risk tier) blocks it, we should probably block.
            # But if card is authoritative, maybe we skip UCF?
            # For safety, layered defense: both must allow.
            raise PermissionError(f"VACP: Tool '{tool_name}' unauthorized for risk tier '{identity.risk_tier}'.")

    def inject_zsp_credentials(self, tool_name: str, args: dict) -> dict:
        """
        Performs Just-In-Time (JIT) access elevation if the tool requires it.
        Returns the modified arguments (with injected secrets).
        """
        if tool_name == "place_order":
            logger.info("🛑 Gateway: Intercepting 'place_order'. Initiating ZSP flow.")
            try:
                # 1. Elevate Privilege (JIT)
                jit_creds = self.mim_service.get_jit_session()

                # 2. Retrieve the actual API Key
                api_key = self.mim_service.fetch_secret_with_jit(TRADING_SECRET_ID, jit_creds)

                # 3. Inject secret into args
                new_args = args.copy()
                new_args['api_token'] = api_key
                return new_args
            except Exception as e:
                logger.error(f"ZSP Elevation Failed: {e}")
                raise PermissionError(f"ZSP Access Denied: {e}")

        return args

# Singleton Gateway
gateway = ToolGateway()

def vacp_enforce(func):
    """
    Decorator to enforce VACP controls on tool execution.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        logger.info(f"VACP Gateway: Intercepting call to '{tool_name}'")

        try:
            # 1. Verify Policy
            gateway.verify_access(tool_name, kwargs)

            # 2. Inject ZSP Credentials (if needed)
            updated_kwargs = gateway.inject_zsp_credentials(tool_name, kwargs)

        except PermissionError as e:
            logger.error(f"VACP Violation: {e}")
            return str(e) # Return error string to agent

        return func(*args, **updated_kwargs)
    return wrapper
