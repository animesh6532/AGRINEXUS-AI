"""
Temporal Prediction Smoother for Live Camera Streaming.
Provides rolling buffer prediction aggregation to reduce frame-to-frame flickering.
"""

from collections import deque, Counter
from typing import List, Dict, Any, Tuple


class TemporalSmoother:
    """Sliding window prediction buffer for live camera stability."""

    def __init__(self, buffer_size: int = 5):
        self.buffer_size = buffer_size
        self.history = deque(maxlen=buffer_size)

    def add_prediction(self, predicted_class: str, confidence: float):
        """Append a frame prediction to the rolling history buffer."""
        self.history.append((predicted_class, confidence))

    def get_smoothed_prediction(self) -> Tuple[str, float]:
        """
        Compute confidence-weighted majority vote across the rolling history.
        Returns (stable_predicted_class, aggregated_confidence).
        """
        if not self.history:
            return "Unknown", 0.0

        class_weights: Dict[str, float] = {}
        class_counts: Dict[str, int] = {}

        for cls, conf in self.history:
            class_weights[cls] = class_weights.get(cls, 0.0) + conf
            class_counts[cls] = class_counts.get(cls, 0) + 1

        # Select class with highest cumulative confidence weight
        best_class = max(class_weights.items(), key=lambda x: x[1])[0]
        avg_confidence = class_weights[best_class] / class_counts[best_class]

        return best_class, round(avg_confidence, 4)

    def reset(self):
        """Clear the history buffer."""
        self.history.clear()
