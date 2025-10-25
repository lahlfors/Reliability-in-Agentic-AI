# Reinforcement Learning Training Data Generation

## Introduction

This document explains how training data for the Metacognitive Control Subsystem's (MCS) reinforcement learning model is generated. The MCS uses a Constrained Markov Decision Process (CMDP) to learn a safe and effective decision-making policy. The training data is generated dynamically through simulated interactions between the RL agent and a custom environment.

## Agent-Environment Interaction Loop

The training process takes place within a simulated environment defined in `metacognitive_control_subsystem/mcs/formal/cmdp_env.py`. The core of the data generation process is the interaction between the reinforcement learning agent (a PPO model from `stable-baselines3`) and the `CMDP_Environment`. This interaction loop can be summarized as follows:

1.  **Environment Reset**: At the beginning of each training episode, the environment is reset. In this step, a new, randomized `AgentState` is created. This `AgentState` represents a snapshot of a hypothetical host agent's state, including its goals, plans, and the action it proposes to take next. These synthetic states are designed to cover a wide range of scenarios, from safe and aligned to risky and misaligned.

2.  **Observation**: The `StateMonitor` component processes the `AgentState` and constructs a 4-dimensional "belief state" vector. This vector serves as the observation for the RL agent, providing a condensed summary of the agent's current situation.

3.  **Action**: The RL agent receives the observation and, based on its current policy, selects one of four possible metacognitive actions: `EXECUTE`, `REVISE`, `VETO`, or `ESCALATE`.

4.  **Step and Evaluation**: The environment's `step` function takes the agent's action and evaluates it. This is where the core data for learning is generated:
    *   **Cost**: The `RiskConstraintModeler` assesses the risk of the `proposed_action` in the `AgentState` and calculates a `cost`.
    *   **Reward**: A `reward` is calculated based on a set of predefined rules that incentivize the agent to make safe and effective decisions. For example, vetoing a high-cost action yields a high reward, while executing it results in a penalty.

5.  **Learning**: The generated data—the observation (belief state), the action taken, the resulting reward, and the cost—are used by the PPO algorithm to update the agent's policy. The episode then terminates, and a new one begins.

## Description of the Generated Data

The training data is generated on-the-fly and is not stored in a static dataset. The key pieces of data generated in each step are:

*   **State (Observation)**: The 4-dimensional belief state vector from the `StateMonitor`.
*   **Action**: The integer representing the metacognitive action chosen by the agent (0-3).
*   **Reward**: The scalar reward value that guides the agent toward its primary objective.
*   **Cost**: The scalar cost value that the CMDP framework uses to enforce safety constraints.

## Running the Training Script

To initiate the training process and begin generating data, run the following command from the root of the repository:

```bash
PYTHONPATH=/app poetry -C financial-advisor run python3 metacognitive_control_subsystem/train.py
```

This script will instantiate the environment and the PPO agent and start the training loop. As the agent interacts with the environment, it will continuously generate new training data to learn from.

## The Role of the CMDP Framework

The use of a CMDP is crucial to the data generation and learning process. The CMDP framework extends the standard reinforcement learning paradigm by introducing the concept of a "cost." This cost represents the violation of a safety constraint.

During training, a custom `LagrangianCallback` adjusts the reward signal based on the cost. This mechanism encourages the agent to not only maximize the reward but also to keep the cost below a predefined budget, effectively learning to satisfy the safety constraints.
