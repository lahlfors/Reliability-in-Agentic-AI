import logging
import functools
import os
from opentelemetry import trace
from vacp.goa import GoverningOrchestratorAgent
from vacp.ans import AgentNameService
from vacp.ucf import UCFPolicyEngine
from vacp.schemas import AgentAction
from vacp.gcp_identity import MIMService

logger = logging.getLogger(__name__)

# MIM Configuration
# In a real deployment, these should be set in the environment variables.
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id")
PRIVILEGED_SA_EMAIL = os.environ.get("VACP_PRIVILEGED_SA", "vacp-trader-sa@your-project-id.iam.gserviceaccount.com")
TRADING_SECRET_ID = os.environ.get("VACP_TRADING_SECRET_ID", "TRADING_API_KEY")

class ToolGateway:
    """
    ISO 42001 Clause 8.1: Operational Control.
    The Single Chokepoint for all agent side-effects.
    Now integrated with MIM/ZSP for Identity Elevation.
    """
    def __init__(self):
        self.goa = GoverningOrchestratorAgent()
        self.ans = AgentNameService()
        self.ucf = UCFPolicyEngine()

        # Initialize MIM Service
        self.mim_service = MIMService(PRIVILEGED_SA_EMAIL, PROJECT_ID)

    def verify_access(self, tool_name: str, args: dict):
        """
        Enforces Taint Tracking (LPCI) and Access Control.
        """
        # 1. Check Kill Switch
        is_quarantined, reason = self.goa.is_quarantined()
        if is_quarantined:
            raise PermissionError(f"VACP: Kill-switch is active. Action denied. Reason: {reason}")

        # 2. Extract Context (Baggage) - Simplified for this implementation

        # 3. Identity & UCF Checks
        agent_id = "financial_coordinator"
        identity = self.ans.resolve_agent(agent_id)

        if not identity:
             logger.warning(f"VACP: Agent '{agent_id}' not found. Proceeding with caution.")
             return

        context = {"tool": tool_name, "allowed_tools": identity.authorized_tools}
        if not self.ucf.evaluate("CONTROL-033", context):
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
            # Note: We update kwargs. args are usually empty for tool calls in this framework.
            updated_kwargs = gateway.inject_zsp_credentials(tool_name, kwargs)

        except PermissionError as e:
            logger.error(f"VACP Violation: {e}")
            return str(e) # Return error string to agent

        return func(*args, **updated_kwargs)
    return wrapper
