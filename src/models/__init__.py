"""Model training, calibration, and ensemble modules.

Research-backed implementations:
- XGBoostNFLModel: Base model with proper evaluation metrics
- ModelCalibrator: Platt scaling with ECE/MCE metrics (Guo et al. 2017)
- StackedEnsembleModel: Heterogeneous ensemble (Nature Scientific Reports 2025)
- MCDropoutPredictor: Uncertainty quantification (Gal & Ghahramani 2016)
"""

from .calibration import ModelCalibrator
from .xgboost_model import XGBoostNFLModel

# Optional imports for advanced features
try:
    from .ensemble import StackedEnsembleModel
except ImportError:
    StackedEnsembleModel = None

try:
    from .uncertainty import MCDropoutPredictor, calculate_confidence_score
except ImportError:
    MCDropoutPredictor = None
    calculate_confidence_score = None

__all__ = [
    "XGBoostNFLModel",
    "ModelCalibrator",
    "StackedEnsembleModel",
    "MCDropoutPredictor",
    "calculate_confidence_score",
]
