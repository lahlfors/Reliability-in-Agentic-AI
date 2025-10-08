"""
Unit tests for the full implementation of the BeliefMemory module.
"""

import pytest
from r2a2.components.belief_memory import BeliefMemory

@pytest.fixture
def belief_memory():
    """Provides a BeliefMemory instance with a small buffer for testing."""
    return BeliefMemory(episodic_buffer_size=3)

def test_initialization(belief_memory):
    """
    Tests that the memory module initializes in a clean state.
    """
    assert belief_memory.get_belief_state() == {}
    assert belief_memory.retrieve_relevant_memories("any query") == []
    assert belief_memory._tick == 0

def test_update_belief_and_get_state(belief_memory):
    """
    Tests that updating the belief also updates the current state and creates
    a memory entry with correct provenance.
    """
    structured_state = {
        "task_instruction": "Test task",
        "observations": {"data": "value"},
    }
    belief_memory.update_belief(structured_state)

    current_belief = belief_memory.get_belief_state()
    assert current_belief["task_instruction"] == "Test task"
    assert current_belief["tick"] == 1
    assert "timestamp" in current_belief

    # Check that the memory was recorded
    memories = belief_memory.retrieve_relevant_memories("Test task")
    assert len(memories) == 1
    assert memories[0]["state"] == structured_state
    assert memories[0]["source"] == "perceiver"
    assert memories[0]["confidence"] == 1.0

def test_semantic_retrieval_simulation(belief_memory):
    """
    Tests the simulated semantic search functionality.
    """
    state1 = {"task_instruction": "analyze stock market", "observations": {"ticker": "AI"}}
    state2 = {"task_instruction": "write a report on AI", "observations": {"source": "web"}}
    state3 = {"task_instruction": "summarize news about finance", "observations": {}}

    belief_memory.update_belief(state1)
    belief_memory.update_belief(state2)
    belief_memory.update_belief(state3)

    # Query for "AI" should return state2 and state1
    retrieved = belief_memory.retrieve_relevant_memories("AI safety report")
    assert len(retrieved) == 2
    assert retrieved[0]["state"]["task_instruction"] == "write a report on AI"
    assert retrieved[1]["state"]["task_instruction"] == "analyze stock market"

    # Query for "finance" should return state3
    retrieved = belief_memory.retrieve_relevant_memories("finance")
    assert len(retrieved) == 1
    assert retrieved[0]["state"]["task_instruction"] == "summarize news about finance"

def test_episodic_buffer_size_limit(belief_memory):
    """
    Tests that the episodic buffer correctly discards the oldest memories
    when it exceeds its configured size.
    """
    # The buffer size is 3
    belief_memory.update_belief({"task_instruction": "task 1"})
    belief_memory.update_belief({"task_instruction": "task 2"})
    belief_memory.update_belief({"task_instruction": "task 3"})

    assert len(belief_memory._episodic_buffer) == 3
    assert belief_memory._episodic_buffer[0]["state"]["task_instruction"] == "task 1"

    # Add a fourth item, which should push out the first one
    belief_memory.update_belief({"task_instruction": "task 4"})

    assert len(belief_memory._episodic_buffer) == 3
    assert belief_memory._episodic_buffer[0]["state"]["task_instruction"] == "task 2"
    assert belief_memory._episodic_buffer[2]["state"]["task_instruction"] == "task 4"

def test_semantic_memory_retains_all(belief_memory):
    """
    Tests that the semantic memory does not discard items like the episodic buffer.
    """
    # The buffer size is 3
    belief_memory.update_belief({"task_instruction": "task 1"})
    belief_memory.update_belief({"task_instruction": "task 2"})
    belief_memory.update_belief({"task_instruction": "task 3"})
    belief_memory.update_belief({"task_instruction": "task 4"})

    assert len(belief_memory._semantic_memory) == 4
    assert belief_memory._semantic_memory[0]["state"]["task_instruction"] == "task 1"