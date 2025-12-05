import logging
import time
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace import ReadableSpan
from vacp.agent_guard import AgentGuard
from vacp.janus import JanusMonitor
from vacp.ucf import UCFPolicyEngine
from vacp.goa import GoverningOrchestratorAgent
from vacp.schemas import AgentAction

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
        # For demo, we might need to parse the proposed tool from the text if possible
        # Or we rely on the fact that this reasoning leads to a tool call.
        # We verify the *reasoning* itself.

        # 2. AgentGuard (Clause 6.1.2)
        # We construct a pseudo-action for the check if we can infer it,
        # or we just check the state transition.
        # For the refactor, let's assume we can infer the intended tool from the plan text attributes
        # if the agent logic put it there.
        # If not, we just check the plan text for keywords.

        inferred_tool = "place_order" if "buy" in plan_text.lower() or "order" in plan_text.lower() else "unknown"
        if "python" in plan_text.lower() or "code" in plan_text.lower():
            inferred_tool = "execute_python_code"

        action = AgentAction(tool_name=inferred_tool, parameters={"context": plan_text})

        self.agent_guard.update_model(action)
        p_failure = self.agent_guard.calculate_failure_probability(action, risk_tier="High")

        # 3. Janus (Clause 9.2)
        vulnerability = self.janus.run_red_team_simulation(action, plan_text)

        # 4. UCF & Decision Logic
        decision = "TRACK"
        if vulnerability != "None" or p_failure > 0.05:
            decision = "QUARANTINE"
            justification = f"P(fail)={p_failure}, Janus={vulnerability}"
            self.goa.activate_kill_switch(justification)

        logger.info(f"VACP Processor: Decision={decision} for intent '{inferred_tool}'")
