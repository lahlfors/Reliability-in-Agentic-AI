"""
This module trains the Deliberation Controller's policy using a Q-learning
algorithm on the custom CMDP environment.
"""
import json
import os
import numpy as np
import random
from collections import defaultdict

from metacognitive_control_subsystem.mcs.formal.cmdp_env import CMDP_Environment
from metacognitive_control_subsystem.mcs.api.schemas import Constraint

def train():
    """
    Trains a Q-learning agent on the CMDP_Environment and saves the resulting
    policy as a set of rules in a JSON file.
    """
    # --- 1. Environment and Hyperparameter Setup ---
    # Define the constraints the environment should model
    constraints = [
        Constraint(name="Fiduciary Duty Constraint", description="", budget=0.01),
        Constraint(name="Compliance Constraint", description="", budget=0.0),
        Constraint(name="NO_FILE_DELETION", description="", budget=0.0),
    ]
    env = CMDP_Environment(constraints)

    # Q-learning hyperparameters
    alpha = 0.1  # Learning rate
    gamma = 0.6  # Discount factor
    epsilon = 0.1  # Exploration rate
    num_episodes = 10000

    # Initialize the Q-table as a nested dictionary
    # The state is discretized for simplicity.
    q_table = defaultdict(lambda: np.zeros(len(env.action_space)))

    # --- 2. Training Loop ---
    for i in range(num_episodes):
        state = env.reset()
        # Discretize the continuous state into a tuple to be used as a dict key
        state_discrete = tuple((state * 10).astype(int))

        done = False
        while not done:
            # Epsilon-greedy action selection
            if random.uniform(0, 1) < epsilon:
                action_index = random.choice(range(len(env.action_space)))
            else:
                action_index = np.argmax(q_table[state_discrete])

            # Take the action
            next_state, reward, cost, done, _ = env.step(action_index)
            next_state_discrete = tuple((next_state * 10).astype(int))

            # --- Q-learning update rule (with a simple penalty for cost) ---
            # A true Lagrangian approach would have a separate update for the multiplier.
            # Here, we directly incorporate a penalty into the reward.
            lagrangian_reward = reward - (10 * cost) # Using a fixed lambda of 10 for simplicity

            old_value = q_table[state_discrete][action_index]
            next_max = np.max(q_table[next_state_discrete])

            new_value = (1 - alpha) * old_value + alpha * (lagrangian_reward + gamma * next_max)
            q_table[state_discrete][action_index] = new_value

            state_discrete = next_state_discrete

    print("Training finished.\n")

    # --- 3. Policy Extraction and Saving ---
    # Convert the learned Q-table into a more interpretable set of rules.
    policy = {
        "policy_type": "q_learning_table",
        "rules": []
    }

    # For each learned state, find the best action and save it as a rule.
    for state, actions in q_table.items():
        best_action_index = np.argmax(actions)
        best_action = env.action_space[best_action_index]
        # The condition is a simplified representation of the belief state
        condition = {
            "goal_alignment": state[0] / 10.0,
            "plan_soundness": state[1] / 10.0,
            "environment_trustworthiness": state[2] / 10.0,
            "security_posture": state[3] / 10.0,
        }
        policy["rules"].append({"condition": condition, "action": best_action})

    # Save the policy to a file
    policy_path = os.path.join(os.path.dirname(__file__), "policy.json")
    with open(policy_path, "w") as f:
        json.dump(policy, f, indent=4)

    print(f"Policy extracted and saved to {policy_path} with {len(policy['rules'])} rules.")


if __name__ == "__main__":
    train()
