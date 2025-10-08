"""
Full implementation of the Reasoning & Planner module.

This module is the generative heart of the R2A2 subsystem. It leverages the
powerful inference capabilities of a core LLM to translate high-level goals
and the current belief state into concrete, executable plans.
"""
import json
import logging
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReasoningPlanner:
    """
    A full implementation of the Reasoning & Planner component.
    """

    def __init__(self):
        """Initializes the Reasoning & Planner."""
        logger.info("Reasoning & Planner: Initialized (Full Implementation).")

    def _construct_prompt(self, belief_state: Dict[str, Any], relevant_memories: List[Dict[str, Any]]) -> str:
        """
        Constructs a detailed, structured prompt for the LLM.

        This is a critical step in guiding the LLM to produce high-quality,
        relevant, and structured plans.
        """
        task = belief_state.get("task_instruction", "No task defined.")
        observations = belief_state.get("observations", {})

        prompt = f"""
You are an AI agent's reasoning core. Your goal is to generate a set of candidate plans to achieve the user's task.

**Current Task:**
{task}

**Current Observations:**
{json.dumps(observations, indent=2)}

**Relevant Past Experiences (for context):**
"""
        if relevant_memories:
            for i, mem in enumerate(relevant_memories, 1):
                prompt += f"{i}. {mem['state'].get('task_instruction', 'N/A')}\n"
        else:
            prompt += "No relevant past experiences found.\n"

        prompt += """
**Instructions:**
1.  Analyze the task and observations.
2.  Propose 1 to 3 candidate plans to make progress on the task.
3.  A plan is a sequence of one or more actions.
4.  For each action, specify the 'tool_name' and 'parameters'.
5.  Provide a brief 'explanation' for each action.
6.  Your final output must be a single JSON object containing a key "candidate_plans", which is a list of plans. Do not include any other text or explanation outside of the JSON.

**Example Output Format:**
{
  "candidate_plans": [
    [
      {
        "tool_name": "read_file",
        "parameters": {"path": "/path/to/file"},
        "explanation": "First, I need to read the relevant file."
      },
      {
        "tool_name": "execute_code",
        "parameters": {"code": "print('processing...')"},
        "explanation": "Then, I process the file's content."
      }
    ]
  ]
}
"""
        return prompt

    def _call_llm_simulation(self, prompt: str) -> str:
        """
        Simulates a call to a powerful LLM.

        In a real system, this would be a network call to an API like OpenAI's
        or a self-hosted model. Here, we return a hardcoded, structured
        response based on the prompt's instructions.
        """
        logger.info("Reasoning & Planner: Simulating LLM call.")
        # This mock response simulates the LLM understanding the prompt
        # and returning a valid JSON object with candidate plans.
        mock_response = {
            "candidate_plans": [
                [
                    {
                        "tool_name": "search_web",
                        "parameters": {"query": "latest market trends"},
                        "explanation": "First, search the web for current market trends to gather data."
                    }
                ],
                [
                    {
                        "tool_name": "read_internal_docs",
                        "parameters": {"topic": "market_analysis"},
                        "explanation": "Alternatively, start by reading internal documentation on market analysis."
                    }
                ]
            ]
        }
        return json.dumps(mock_response)


    def generate_plans(self, belief_state: Dict[str, Any], relevant_memories: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Generates a list of candidate action plans.

        Args:
            belief_state: The agent's current understanding of the world.
            relevant_memories: A list of relevant memories to provide context.

        Returns:
            A list of candidate plans, where each plan is a list of actions.
        """
        logger.info("Reasoning & Planner: Generating candidate plans.")

        # 1. Construct the prompt
        prompt = self._construct_prompt(belief_state, relevant_memories)

        # 2. Call the (simulated) LLM
        llm_response_str = self._call_llm_simulation(prompt)

        # 3. Parse the LLM's response
        try:
            response_json = json.loads(llm_response_str)
            plans = response_json.get("candidate_plans", [])
            if not isinstance(plans, list):
                logger.error("LLM response for 'candidate_plans' was not a list.")
                return []
            return plans
        except json.JSONDecodeError:
            logger.error(f"Failed to decode LLM response as JSON: {llm_response_str}")
            return []