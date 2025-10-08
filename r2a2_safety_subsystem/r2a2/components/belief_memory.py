"""
Full implementation of the Belief & Memory module.

This module is the central repository for the agent's state, providing
contextual continuity for planning and adaptation. It is a critical defense
against long-term risks like memory poisoning, using a hybrid memory system
and provenance tracking as described in the TDD.
"""
import time
import re
from collections import deque
from typing import Any, Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeliefMemory:
    """
    A full implementation of the Belief & Memory component.
    """

    def __init__(self, episodic_buffer_size: int = 100):
        """
        Initializes the Belief & Memory store.

        Args:
            episodic_buffer_size: The maximum number of recent events to store
                                  in the high-speed episodic buffer.
        """
        # The agent's current understanding of the world state.
        self._current_belief: Dict[str, Any] = {}

        # Short-term, chronological memory (like a RAM buffer).
        self._episodic_buffer: deque = deque(maxlen=episodic_buffer_size)

        # Long-term, knowledge store (simulating a vector DB).
        # In a real system, this would be a proper vector database for
        # efficient semantic search.
        self._semantic_memory: List[Dict[str, Any]] = []

        self._tick = 0
        logger.info("Belief & Memory: Initialized (Full Implementation).")

    def update_belief(self, structured_state: Dict[str, Any], source: str = "perceiver"):
        """
        Updates the internal belief state and commits the experience to memory.

        Args:
            structured_state: The structured state from the Perceiver.
            source: The origin of the information (e.g., 'perceiver', 'reflection').
        """
        logger.info("Belief & Memory: Updating belief state.")

        self._tick += 1
        timestamp = time.time()

        # Update the current, immediate belief
        self._current_belief = structured_state
        self._current_belief['tick'] = self._tick
        self._current_belief['timestamp'] = timestamp

        # Create a memory object with provenance
        memory_entry = {
            "state": structured_state,
            "source": source,
            "tick": self._tick,
            "timestamp": timestamp,
            "confidence": 1.0, # Could be adjusted by a trust mechanism
        }

        # Add to both memory stores
        self._episodic_buffer.append(memory_entry)
        self._semantic_memory.append(memory_entry) # In a real system, this would be encoded and indexed.

        # Trigger consistency audit periodically (placeholder)
        if self._tick % 50 == 0:
            self._audit_consistency()

    def get_belief_state(self) -> Dict[str, Any]:
        """
        Retrieves the current, most immediate belief state.
        """
        return self._current_belief

    def retrieve_relevant_memories(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves relevant memories based on a query.

        This is a simulation of semantic search. A real implementation would
        use vector embeddings to find the most similar memories.

        Args:
            query: The natural language query to search for.
            top_k: The number of most relevant memories to return.

        Returns:
            A list of relevant memory entries.
        """
        logger.info(f"Retrieving top {top_k} memories for query: '{query}'")
        # Simple keyword matching simulation
        query_words = set(re.split(r'\W+', query.lower()))

        scored_memories = []
        for mem in reversed(self._semantic_memory): # Prioritize recent memories
            task = mem['state'].get('task_instruction', '')

            # FIX: Properly extract text from observations dictionary
            obs = mem['state'].get('observations', {})
            obs_texts = [str(v) for v in obs.values() if isinstance(v, (str, int, float))]
            obs_str = " ".join(obs_texts)

            content = (task + ' ' + obs_str).lower()
            content_words = set(re.split(r'\W+', content))

            score = len(query_words.intersection(content_words))
            if score > 0:
                scored_memories.append((score, mem))

        # Sort by score (desc) and return the top_k
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [mem for score, mem in scored_memories[:top_k]]

    def _audit_consistency(self):
        """
        Placeholder for the consistency auditing mechanism.

        A real implementation would query the memory store to find and resolve
        contradictions, mitigating issues like value drift.
        """
        logger.info("Belief & Memory: Performing periodic consistency audit (placeholder).")
        pass