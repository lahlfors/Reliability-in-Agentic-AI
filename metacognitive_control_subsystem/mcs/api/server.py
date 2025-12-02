"""
The FastAPI server for the MCS subsystem.

This module exposes the API endpoints defined in the TDD, allowing a host
agent to interact with the MCS subsystem. It wires together all the
cognitive components to create a complete decision-making loop.
"""
from fastapi import FastAPI, HTTPException, Body
from typing import List

# Import the new TDD-aligned schemas
from metacognitive_control_subsystem.mcs.api.schemas import (
    DeliberateRequest, DeliberateResponse,
    Constraint, ConfigureSettingsRequest, ConfigureResponse, PIDGains
)
# Import the new DeliberationController
from metacognitive_control_subsystem.mcs.components.deliberation_controller import DeliberationController


# --- Application Setup ---

app = FastAPI(
    title="MCS Modular Safety Subsystem (TDD-Aligned)",
    description="An implementation of the Metacognitive Control Subsystem (MCS) architecture.",
    version="0.2.0",
)

# --- Global State & Component Initialization ---

# AgentGuard: Initialize with default formal constraints to demonstrate verification
default_constraints = [
    Constraint(
        name="Compliance Constraint",
        description="Must include disclaimer",
        budget=0.01,
        unsafe_state_definition={"disclaimer": "missing"},
        max_probability_threshold=0.01
    ),
    Constraint(
        name="NO_FILE_DELETION",
        description="No file deletion allowed",
        budget=0.0,
        unsafe_state_definition={"file": "delete"},
        max_probability_threshold=0.0
    )
]

# Instantiate the core Deliberation Controller with no initial constraints
deliberation_controller = DeliberationController(constraints=default_constraints)

# --- API Endpoints ---

@app.post("/deliberate", response_model=DeliberateResponse)
async def deliberate(request: DeliberateRequest):
    """
    Accepts the agent's full state and proposed action for a metacognitive decision.
    This is the core endpoint of the MCS.
    """
    # Pass the request to the Deliberation Controller to get a decision
    decision_response = deliberation_controller.decide(request)
    return decision_response


# --- Configuration Endpoints ---

@app.post("/configure/constraints", response_model=ConfigureResponse)
async def configure_constraints(constraints: List[Constraint] = Body(...)):
    """
    Defines or updates the set of safety constraints the subsystem must enforce.
    """
    global deliberation_controller
    # Note: In a production system, we would just update the constraints of the existing controller
    # to preserve learned state (AgentGuard model). For now, re-instantiation resets the model.
    # To fix this, we should add a method to DeliberationController to update constraints.
    deliberation_controller = DeliberationController(constraints=constraints)
    return ConfigureResponse()

@app.post("/configure/settings", response_model=ConfigureResponse)
async def configure_settings(settings: ConfigureSettingsRequest):
    """
    Tunes the internal hyperparameters of the learning and control algorithms.
    (This functionality will be integrated into the new components later)
    """
    print(f"Applying new configuration settings.")
    # Placeholder for future implementation
    return ConfigureResponse()
