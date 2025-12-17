import json
import os
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class StateManager(ABC):
    """
    Abstract Base Class for GOA State Management.
    Ensures state is durable and external to the agent's runtime memory.
    """
    @abstractmethod
    def get_kill_switch_state(self) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def set_kill_switch_state(self, active: bool, reason: str):
        pass

class FileBasedStateManager(StateManager):
    """
    File-based implementation of StateManager.
    Simulates a distributed store (like Redis) by persisting state to a JSON file.
    """
    def __init__(self, state_file_path: str = "vacp_state.json"):
        self.state_file_path = state_file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.state_file_path):
            self._write_state(False, "")

    def _write_state(self, active: bool, reason: str):
        data = {
            "kill_switch_active": active,
            "quarantine_reason": reason
        }
        try:
            with open(self.state_file_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to write GOA state to file: {e}")

    def _read_state(self) -> dict:
        try:
            with open(self.state_file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read GOA state from file: {e}")
            return {"kill_switch_active": True, "quarantine_reason": f"State Read Error: {e}"}

    def get_kill_switch_state(self) -> Tuple[bool, str]:
        data = self._read_state()
        return data.get("kill_switch_active", False), data.get("quarantine_reason", "")

    def set_kill_switch_state(self, active: bool, reason: str):
        # Read-Modify-Write (naive lock for single file)
        # In a real Redis impl, this would be atomic.
        self._write_state(active, reason)
