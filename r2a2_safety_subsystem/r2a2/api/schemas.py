"""
Pydantic schemas for the R2A2 Subsystem API.

This module defines the data structures used for request and response bodies
in the FastAPI application, ensuring type safety and clear API contracts.
"""

from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field

# --- API Schemas ---

class PerceiveRequest(BaseModel):
    """
    Request body for the POST /perceive endpoint.
    This is the primary input method for the host agent to send new information.
    """
    task_instruction: str = Field(..., description="The high-level goal or task for the agent.")
    observations: Dict[str, Any] = Field(..., description="A key-value map of new observations from the environment.")
    external_reward: Optional[float] = Field(None, description="An optional scalar reward signal from the environment resulting from the previous action.")


class PerceiveResponse(BaseModel):
    """
    Response body for the POST /perceive endpoint.
    """
    transaction_id: str = Field(..., description="A unique ID for the perception-action cycle, used to retrieve the corresponding action.")


class GetActionResponse(BaseModel):
    """
    Response body for the GET /getAction endpoint.
    This is the primary output method for the R2A2 subsystem to provide a safe action.
    """
    status: Literal["ACTION_APPROVED", "DEFER_TO_HUMAN", "ERROR"] = Field(..., description="The status of the action decision.")
    action: Optional[Dict[str, Any]] = Field(None, description="The serialized action command for the host agent to execute. Present only if status is 'ACTION_APPROVED'.")
    explanation: Optional[str] = Field(None, description="A natural language explanation of the reasoning behind the action, for logging and interpretability.")


# --- Configuration Schemas ---

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