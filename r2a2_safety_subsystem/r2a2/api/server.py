"""
The FastAPI server for the R2A2 subsystem.

This module exposes the API endpoints defined in the TDD, allowing a host
agent to interact with the R2A2 subsystem. It wires together all the
cognitive components to create a complete decision-making loop.
"""

import uuid
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Body

# Import schemas and components
from r2a2.api.schemas import (
    PerceiveRequest, PerceiveResponse, GetActionResponse,
    Constraint, ConfigureSettingsRequest, ConfigureResponse, PIDGains
)
from r2a2.components.perceiver import Perceiver
from r2a2.components.belief_memory import BeliefMemory
from r2a2.components.reasoning_planner import ReasoningPlanner
from r2a2.components.risk_aware_world_model import RiskAwareWorldModel
from r2a2.components.constraint_filter import ConstraintFilter
from r2a2.components.actuator import Actuator
from r2a2.formal.cmdp import CMDP_Model

# --- Application Setup ---

app = FastAPI(
    title="R2A2 Modular Safety Subsystem",
    description="An implementation of the Reflective Risk-Aware Agent Architecture.",
    version="0.1.0",
)

# --- Global State & Component Initialization ---

# In a production system, this state would be managed more robustly.
TRANSACTION_STORE: Dict[str, GetActionResponse] = {}

# Instantiate all the core components (now using full implementations)
perceiver = Perceiver()
belief_memory = BeliefMemory()
planner = ReasoningPlanner()
world_model = RiskAwareWorldModel()
constraint_filter = ConstraintFilter()
actuator = Actuator()
cmdp_model = CMDP_Model()

# Default settings
DEFAULT_PID_GAINS = PIDGains(kp=0.1, ki=0.01, kd=0.05)
DEFAULT_LEARNING_RATE = 0.01

# --- API Endpoints ---

@app.post("/configure/constraints", response_model=ConfigureResponse)
async def configure_constraints(constraints: List[Constraint] = Body(...)):
    """
    Defines or updates the set of safety constraints the subsystem must enforce.
    """
    try:
        pid_gains = getattr(app.state, "pid_gains", DEFAULT_PID_GAINS)
        learning_rate = getattr(app.state, "learning_rate", DEFAULT_LEARNING_RATE)
        cmdp_model.configure_constraints(constraints, pid_gains, learning_rate)
        return ConfigureResponse()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/configure/settings", response_model=ConfigureResponse)
async def configure_settings(settings: ConfigureSettingsRequest):
    """
    Tunes the internal hyperparameters of the learning and control algorithms.
    """
    if settings.pid_gains:
        app.state.pid_gains = settings.pid_gains
    if settings.dual_learning_rate:
        app.state.learning_rate = settings.dual_learning_rate
    if cmdp_model.get_all_constraints():
        current_defs = [Constraint(name=c.name, description=c.description, budget=c.budget) for c in cmdp_model.get_all_constraints()]
        pid_gains = getattr(app.state, "pid_gains", DEFAULT_PID_GAINS)
        learning_rate = getattr(app.state, "learning_rate", DEFAULT_LEARNING_RATE)
        cmdp_model.configure_constraints(current_defs, pid_gains, learning_rate)
    return ConfigureResponse()


@app.post("/perceive", response_model=PerceiveResponse)
async def perceive(request: PerceiveRequest):
    """
    Submits new perceptual data, initiating a full decision-making cycle.
    """
    transaction_id = str(uuid.uuid4())

    # 1. Perception
    structured_state = perceiver.process_input(request.observations, request.task_instruction)

    # 2. Belief Update
    belief_memory.update_belief(structured_state)
    current_belief = belief_memory.get_belief_state()

    # Retrieve relevant memories to aid in planning
    relevant_memories = belief_memory.retrieve_relevant_memories(request.task_instruction)

    # 3. Plan Generation
    candidate_plans = planner.generate_plans(current_belief, relevant_memories)

    # 4. Risk-Aware Simulation & 5. Plan Refinement
    if not candidate_plans:
        action_response = GetActionResponse(status="DEFER_TO_HUMAN", explanation="Planner failed to generate any plans.")
        TRANSACTION_STORE[transaction_id] = action_response
        return PerceiveResponse(transaction_id=transaction_id)

    # This is a simplification. A real implementation would evaluate all plans
    # and select the best one based on the primal-dual objective.
    best_plan = candidate_plans[0]
    reward, costs = world_model.evaluate_plan(best_plan, current_belief)

    # Dual variable update (learning)
    for name, cost in costs.items():
        constraint = cmdp_model.get_constraint(name)
        if constraint:
            constraint.update_lambda(cost)

    # 6. Constraint Verification
    action_to_verify = best_plan[0]
    is_safe = constraint_filter.verify_action(action_to_verify, costs, cmdp_model)

    # 7. Action Dispatch or Deferral
    if is_safe:
        formatted_action = actuator.format_action(action_to_verify)
        action_response = GetActionResponse(
            status="ACTION_APPROVED",
            action=formatted_action,
            explanation=formatted_action.get("explanation", "Action approved by R2A2 subsystem.")
        )
    else:
        action_response = GetActionResponse(
            status="DEFER_TO_HUMAN",
            explanation="Proposed action was rejected by the Constraint Filter."
        )

    TRANSACTION_STORE[transaction_id] = action_response
    return PerceiveResponse(transaction_id=transaction_id)


@app.get("/getAction", response_model=GetActionResponse)
async def get_action(transaction_id: str):
    """
    Retrieves the result of a decision-making cycle.
    """
    if transaction_id not in TRANSACTION_STORE:
        raise HTTPException(status_code=404, detail="Transaction ID not found.")

    return TRANSACTION_STORE.pop(transaction_id)