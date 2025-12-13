import json
import os
from vacp.schemas import AgentCard
from vacp.c2pa import C2PASigner

class CardLoader:
    def __init__(self, enforce_signature: bool = True):
        self.enforce_signature = enforce_signature
        self.signer = C2PASigner()

    def load_card(self, json_path: str) -> AgentCard:
        """Loads, verifies, and validates the Agent Card."""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Agent Card not found at {json_path}")

        # 1. Verify Integrity
        if self.enforce_signature:
            signature_path = json_path + ".sig"
            if not self.signer.verify_file(json_path, signature_path):
                # We can choose to raise an error or just log depending on strictness
                # For this implementation, we raise as per user requirement "System should fail to start"
                raise ValueError(f"CRITICAL: Signature verification failed for {json_path}")
            print(f"✅ Identity Verified: {json_path}")

        # 2. Load and Validate Schema
        try:
            with open(json_path, 'r') as f:
                raw_data = json.load(f)
            card = AgentCard(**raw_data)
            print(f"✅ Schema Validated: {card.agent_name}")
            return card
        except Exception as e:
            raise ValueError(f"Card Validation Failed: {e}")
