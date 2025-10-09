"""
Pydantic schemas for the R2A2 Subsystem API.

This module defines the data structures used for request and response bodies
in the FastAPI application, ensuring type safety and clear API contracts.
This version is updated to match the TDD's /deliberate endpoint.
"""

from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field

# --- API Schemas for /deliberate endpoint ---

class ProposedAction(BaseModel):
    """The action the agent intends to execute next."""
    tool_name: str = Field(..., description="The name of the tool to be called.")
    parameters: Dict[str, Any] = Field(..., description="The parameters for the tool call.")

class AgentState(BaseModel):
    """A comprehensive snapshot of the agent's current cognitive state."""
    goal: str = Field(..., description="The original user-provided goal or instruction.")
    plan: Optional[List[str]] = Field(None, description="The agent's current multi-step plan.")
    memory_buffer: Optional[str] = Field(None, description="A transcript of the recent conversation and action history.")
    proposed_action: ProposedAction = Field(..., description="The action the agent intends to execute next.")
    tool_schemas: Optional[List[Dict[str, Any]]] = Field(None, description="The definitions of all tools available to the agent.")

class DeliberateRequest(BaseModel):
    """
    Request body for the POST /deliberate endpoint.
    This is the primary input for the synchronous deliberation process.
    """
    agent_state: AgentState
    observation: Optional[str] = Field(None, description="The output or result from the previously executed action.")
    policy_constraints: Optional[List[str]] = Field(None, description="A list of high-level, task-specific constraints.")

class DeliberateResponse(BaseModel):
    """
    Response body for the POST /deliberate endpoint.
    Contains the MCS's decision and justification.
    """
    decision: Literal["EXECUTE", "REVISE", "VETO", "ESCALATE", "TERMINATE"] = Field(..., description="The metalevel action command issued by the MCS.")
    parameters: Dict[str, Any] = Field(..., description="Arguments for the decision (e.g., sanitized action params, prompt for revision).")
    justification: str = Field(..., description="A human-readable explanation of the MCS's decision-making process.")
    risk_assessment: Dict[str, Any] = Field(..., description="A structured breakdown of the risk scores calculated by the Risk & Constraint Modeler.")

# --- Configuration Schemas (Retained for potential future use) ---

class Constraint(BaseModel):
    """
    Defines a single safety constraint for the CMDP framework.
    """
    name: str = Field(..., description="A unique identifier for the constraint (e.g., 'tool_misuse').")
    description: str = Field(..., description="A natural language description of the constraint's intent for the LLM.")
    budget: float = Field(..., description="The maximum allowed expected cumulative cost (d_k).")


class PIDGains(BaseModel):
    """
    Defines the gains for the PID controller used in the dual variable update.
    """
    kp: float = Field(..., description="Proportional gain.")
    ki: float = Field(..., description="Integral gain.")
    kd: float = Field(..., description="Derivative gain.")


class ConfigureSettingsRequest(BaseModel):
    """
    Request body for the POST /configure/settings endpoint.
    Allows for tuning the internal hyperparameters of the R2A2 subsystem.
    """
    dual_learning_rate: Optional[float] = Field(None, description="The learning rate (eta) for the Lagrange multiplier updates.")
    pid_gains: Optional[PIDGains] = Field(None, description="The P, I, and D gains for the dual variable update controller.")


class ConfigureResponse(BaseModel):
    """
    A generic success response for configuration endpoints.
    """
    status: Literal["success"] = "success"