"""
This module trains the Deliberation Controller's policy using the PPO algorithm
from Stable Baselines3 on the custom Gymnasium CMDP environment.
"""
import os
import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback

from metacognitive_control_subsystem.mcs.formal.cmdp_env import CMDP_Environment
from metacognitive_control_subsystem.mcs.api.schemas import Constraint

# --- Lagrangian Callback for SB3 ---
class LagrangianCallback(BaseCallback):
    """
    A custom callback for Stable Baselines3 to implement a simple Lagrangian
    penalty. It adjusts the reward based on the cost received from the environment.
    """
    def __init__(self, cost_threshold=0.1, lambda_initial=1.0, lambda_lr=0.01, verbose=0):
        super().__init__(verbose)
        self.cost_threshold = cost_threshold
        self.lambda_val = lambda_initial
        self.lambda_lr = lambda_lr

    def _on_step(self) -> bool:
        # `infos` is a list of dictionaries, one for each environment.
        # Since we use DummyVecEnv, there's only one.
        cost = self.training_env.get_attr('last_cost', 0)[0]

        # Primal update is implicitly handled by modifying the reward
        # This is a simplified version of R' = R - lambda * C
        if self.model.ep_info_buffer:
            self.model.ep_info_buffer[-1]['r'] -= self.lambda_val * cost
            self.model.ep_info_buffer[-1]['c'] = cost # Store cost for averaging

        # Dual update: Adjust lambda based on constraint violation
        if self.model.ep_info_buffer:
            avg_cost = np.mean([ep_info.get('c', 0) for ep_info in self.model.ep_info_buffer])
            self.lambda_val = max(0, self.lambda_val + self.lambda_lr * (avg_cost - self.cost_threshold))

        return True

def train():
    """
    Trains a PPO agent on the CMDP_Environment and saves the trained model.
    """
    print("--- Starting Training ---")

    # --- 1. Environment Setup ---
    constraints = [
        Constraint(name="Fiduciary Duty Constraint", description="", budget=0.01),
        Constraint(name="Compliance Constraint", description="", budget=0.0),
        Constraint(name="NO_FILE_DELETION", description="", budget=0.0),
    ]

    # Stable Baselines3 works with vectorized environments
    vec_env = DummyVecEnv([lambda: CMDP_Environment(constraints)])

    # --- 2. Model and Training Setup ---
    # PPO is a good choice for this discrete action space
    model = PPO("MlpPolicy", vec_env, verbose=1)

    # Use the custom callback to handle the Lagrangian penalty
    callback = LagrangianCallback()

    # --- 3. Training ---
    print("Training PPO model with Lagrangian penalty...")
    model.learn(total_timesteps=10000, callback=callback)
    print("\n--- Training Finished ---")

    # --- 4. Saving the Model ---
    model_path = os.path.join(os.path.dirname(__file__), "ppo_mcs_policy.zip")
    model.save(model_path)

    print(f"\nTrained PPO policy saved to: {model_path}")

if __name__ == "__main__":
    # Add a guard to avoid issues with multiprocessing in SB3
    train()
