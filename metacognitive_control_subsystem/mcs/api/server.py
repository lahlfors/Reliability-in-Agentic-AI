"""
The FastAPI server for the R2A2 subsystem.

This module exposes the API endpoints defined in the TDD, allowing a host
agent to interact with the R2A2 subsystem. It wires together all the
cognitive components to create a complete decision-making loop.
"""
from fastapi import FastAPI, HTTPException, Body

# Import the new TDD-aligned schemas
from metacognitive_control_subsystem.mcs.api.schemas import (
    DeliberateRequest, DeliberateResponse,
    Constraint, ConfigureSettingsRequest, ConfigureResponse, PIDGains
)
# Import the new DeliberationController
from metacognitive_control_subsystem.mcs.components.deliberation_controller import DeliberationController


# --- Application Setup ---

app = FastAPI(
    title="R2A2 Modular Safety Subsystem (TDD-Aligned)",
    description="An implementation of the Metacognitive Control Subsystem (MCS) architecture.",
    version="0.2.0",
)

# --- Global State & Component Initialization ---

# Instantiate the core Deliberation Controller
deliberation_controller = DeliberationController()

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


# --- Configuration Endpoints (Retained for now) ---

@app.post("/configure/constraints", response_model=ConfigureResponse)
async def configure_constraints(constraints: list[Constraint] = Body(...)):
    """
    Defines or updates the set of safety constraints the subsystem must enforce.
    (This functionality will be integrated into the new components later)
    """
    print(f"Configuring {len(constraints)} constraints.")
    # Placeholder for future implementation
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