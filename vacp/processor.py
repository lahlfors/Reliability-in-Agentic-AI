import logging
import time
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace import ReadableSpan
from vacp.agent_guard import AgentGuard
from vacp.janus import JanusMonitor
from vacp.ucf import UCFPolicyEngine
from vacp.goa import GoverningOrchestratorAgent
from vacp.schemas import AgentAction, FinancialContext

logger = logging.getLogger(__name__)

class VACPSpanProcessor(SpanProcessor):
    """
    ISO 42001 Nervous System.
    Synchronously processes spans to trigger the Kill Switch BEFORE the agent can act.
    """
    def __init__(self):
        self.agent_guard = AgentGuard()
        self.janus = JanusMonitor()
        self.ucf = UCFPolicyEngine()
        self.goa = GoverningOrchestratorAgent() # Singleton

    def on_end(self, span: ReadableSpan) -> None:
        """
        Called synchronously when a span ends.
        """
        # 1. Identify "Reasoning" Spans
        attributes = span.attributes or {}
        span_type = attributes.get("gen_ai.span.type")

        if span_type == "reasoning":
            self._process_reasoning_span(span, attributes)

    def _process_reasoning_span(self, span: ReadableSpan, attributes: dict):
        logger.info(f"VACP Processor: Analyzing Reasoning Span {span.name}")

        # Extract Plan/Context
        plan_text = attributes.get("gen_ai.content.completion", "")

        # 2. Infer Tool Intent
        inferred_tool = "place_order" if "buy" in plan_text.lower() or "order" in plan_text.lower() else "unknown"
        if "python" in plan_text.lower() or "code" in plan_text.lower():
            inferred_tool = "execute_python_code"

        # 3. Construct Simulated Context
        # In a real system, we'd fetch the actual Portfolio State from a database here.
        # For the Thesis Demo, we inject the specific "Risk Exposure" context.
        # We can simulate a "Bad State" if the plan text contains certain keywords for testing,
        # otherwise default to a safe state.

        # Simulation Logic for Testing:
        # If text contains "huge trade", we simulate a high trade value.
        estimated_value = 50000.0 if "huge" in plan_text.lower() else 5000.0

        financial_ctx = FinancialContext(
            portfolio_value=100000.0,
            current_risk_exposure=2000.0, # Safe baseline
            daily_drawdown=0.01
        )

        action = AgentAction(
            tool_name=inferred_tool,
            parameters={"context": plan_text, "estimated_value": estimated_value},
            financial_context=financial_ctx
        )

        # 4. AgentGuard (CMDP Check)
        self.agent_guard.update_model(action)
        # Assuming Risk Tier is High for this demo agent
        p_failure = self.agent_guard.calculate_failure_probability(action, risk_tier="High")

        # 5. Janus (Red Team / STPA Check)
        vulnerability = self.janus.run_red_team_simulation(action, plan_text)

        # 6. UCF & Decision Logic
        # We pass the calculated metrics to UCF
        context_data = {
            "p_failure": p_failure,
            "vulnerability": vulnerability,
            "risk_tier": "High",
            "tool": inferred_tool
        }

        # Check CONTROL-013 (Runtime Failure / Safety)
        is_safe = self.ucf.evaluate("CONTROL-013", context_data)

        decision = "TRACK"
        if not is_safe:
            decision = "QUARANTINE"
            justification = f"Blocked by UCF: P(fail)={p_failure:.2f}, Janus={vulnerability}"
            self.goa.activate_kill_switch(justification)

        logger.info(f"VACP Processor: Decision={decision} for intent '{inferred_tool}'")
