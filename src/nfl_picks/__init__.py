"""NFL Picks - Validated betting intelligence.

Model: V4 RB-NGS Optimized
Accuracy: 65.6% on high-confidence picks
ROI: +25.3% at -110 odds
Validated: 2023-2024 seasons (317 games, p < 0.0001)
"""

__version__ = "1.0.0"

from .core.pick import Pick, PickSignal
from .core.predictor import Predictor
from .config import Settings, settings

__all__ = [
    "Pick",
    "PickSignal",
    "Predictor",
    "Settings",
    "settings",
    "__version__",
]
