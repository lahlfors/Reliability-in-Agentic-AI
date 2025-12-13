import hashlib
import json
import os
from typing import Optional

class C2PASigner:
    """
    Handles Content Credentials (C2PA) signing and verification.
    Currently implements a 'Soft' verification mode using SHA-256.
    """
    def __init__(self, key_path: Optional[str] = None):
        self.key_path = key_path

    def _calculate_hash(self, file_path: str) -> str:
        """Internal helper to calculate SHA-256 of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def sign_file(self, file_path: str, output_path: str) -> bool:
        """Creates a detached signature file (Mock)."""
        try:
            file_hash = self._calculate_hash(file_path)
            signature_data = {
                "algorithm": "sha256-mock",
                "hash": file_hash,
                "signer": "vacp-internal-authority",
                "timestamp": "2023-10-27T10:00:00Z"
            }
            with open(output_path, 'w') as f:
                json.dump(signature_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Signing failed: {e}")
            return False

    def verify_file(self, file_path: str, signature_path: str) -> bool:
        """Verifies the integrity of the file against the signature."""
        if not os.path.exists(file_path) or not os.path.exists(signature_path):
            return False
        try:
            with open(signature_path, 'r') as f:
                sig_data = json.load(f)
            current_hash = self._calculate_hash(file_path)
            return sig_data.get('hash') == current_hash
        except Exception as e:
            print(f"Verification error: {e}")
            return False
