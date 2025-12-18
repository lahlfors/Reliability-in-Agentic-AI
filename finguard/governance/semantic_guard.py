import os
import numpy as np
from typing import List, Optional
from dataclasses import dataclass

try:
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

@dataclass
class DriftResult:
    is_drift: bool
    similarity_score: float
    message: str

class SemanticGuard:
    """
    Prevents 'Vaporwork' (Semantic Drift/Looping) by comparing the semantic meaning
    of the current thought against a history of recent thoughts using Embeddings.
    """

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1", model_name: str = "text-embedding-004", mock_mode: bool = False):
        self.history_buffer: List[List[float]] = []
        self.buffer_size = 3
        self.threshold = 0.92
        self.mock_mode = mock_mode
        self.model = None

        if not self.mock_mode and VERTEX_AI_AVAILABLE:
            try:
                # Initialize Vertex AI
                # Note: In a real environment, project_id might be inferred from environment
                project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
                if project:
                    vertexai.init(project=project, location=location)
                    self.model = TextEmbeddingModel.from_pretrained(model_name)
                else:
                    print("Warning: GOOGLE_CLOUD_PROJECT not set. SemanticGuard falling back to Mock Mode.")
                    self.mock_mode = True
            except Exception as e:
                print(f"Warning: Failed to initialize Vertex AI: {e}. SemanticGuard falling back to Mock Mode.")
                self.mock_mode = True
        else:
            self.mock_mode = True

    def _get_embedding(self, text: str) -> List[float]:
        if self.mock_mode:
            # Deterministic mock embedding based on hash for testing loops
            # This allows "identical" strings to have identical embeddings
            # and "similar" strings (not easily mocked by hash) -> we assume hash is good for exact match drift
            # For semantic similarity mock, we can't easily do it without a real model.
            # So we will just use random noise seeded by text length + hash?
            # Better: use a simple bag-of-words or just 1-hot for testing.
            # Let's use a dummy vector.
            import random
            random.seed(text)
            return [random.random() for _ in range(10)]

        try:
            embeddings = self.model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0.0] * 768 # Fallback

    def check_drift(self, current_thought: str) -> DriftResult:
        """
        Checks if the current thought is semantically identical (or very similar)
        to the recent history.
        """
        if not current_thought:
             return DriftResult(False, 0.0, "Empty thought")

        current_vec = self._get_embedding(current_thought)

        if not self.history_buffer:
            self._update_buffer(current_vec)
            return DriftResult(False, 0.0, "First thought")

        # Calculate max similarity with history
        max_sim = 0.0
        for past_vec in self.history_buffer:
            sim = self._cosine_similarity(current_vec, past_vec)
            if sim > max_sim:
                max_sim = sim

        # Check threshold
        is_drift = max_sim > self.threshold

        # Update buffer
        self._update_buffer(current_vec)

        msg = f"Similarity: {max_sim:.4f}"
        if is_drift:
            msg += " [DRIFT DETECTED]"

        return DriftResult(is_drift, max_sim, msg)

    def _update_buffer(self, vec: List[float]):
        self.history_buffer.append(vec)
        if len(self.history_buffer) > self.buffer_size:
            self.history_buffer.pop(0)

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        a = np.array(vec_a)
        b = np.array(vec_b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)

if __name__ == "__main__":
    # Test script
    guard = SemanticGuard(mock_mode=True)

    thoughts = [
        "I will research AAPL stock.",
        "I need to look up Apple's ticker.", # Semantically similar? In mock mode, only if hash matches.
        "I will research AAPL stock.", # Exact repeat -> drift
        "I am executing the trade."
    ]

    print("Testing SemanticGuard (Mock Mode)...")
    for t in thoughts:
        res = guard.check_drift(t)
        print(f"Thought: '{t}' -> {res.message}")
