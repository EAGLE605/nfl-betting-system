"""Model training, calibration, ensemble, and correlation modules.

Research-backed implementations:
- XGBoostNFLModel: Base model with proper evaluation metrics
- ModelCalibrator: Platt scaling with ECE/MCE metrics (Guo et al. 2017)
- StackedEnsembleModel: Heterogeneous ensemble (Nature Scientific Reports 2025)
- MCDropoutPredictor: Uncertainty quantification (Gal & Ghahramani 2016)
- ConformalPredictor: Distribution-free prediction intervals (Shafer & Vovk 2008)
- GaussianCopula: Professional SGP correlation modeling (sportsbook standard)
- EmpiricalCorrelationEngine: Data-validated correlations from 4 seasons nflverse
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

try:
    from .conformal import ConformalPredictor, AdaptiveConformalPredictor, should_bet_with_conformal
except ImportError:
    ConformalPredictor = None
    AdaptiveConformalPredictor = None
    should_bet_with_conformal = None

try:
    from .probability_stacking import (
        ProbabilityStacker, StackedProbability, stack_for_week,
        odds_to_probability, spread_to_probability
    )
except ImportError:
    ProbabilityStacker = None
    StackedProbability = None
    stack_for_week = None
    odds_to_probability = None
    spread_to_probability = None

try:
    from .advanced_copula import (
        GaussianCopula, MultivariateGaussianCopula, VineCopulaSimplified,
        CorrelationDiscovery
    )
except ImportError:
    GaussianCopula = None
    MultivariateGaussianCopula = None
    VineCopulaSimplified = None
    CorrelationDiscovery = None

try:
    from .empirical_correlations import (
        EmpiricalCorrelationEngine, EmpiricalCorrelation,
        VALIDATED_CORRELATIONS, get_recommended_sgp_combinations
    )
except ImportError:
    EmpiricalCorrelationEngine = None
    EmpiricalCorrelation = None
    VALIDATED_CORRELATIONS = None
    get_recommended_sgp_combinations = None

__all__ = [
    "XGBoostNFLModel",
    "ModelCalibrator",
    "StackedEnsembleModel",
    "MCDropoutPredictor",
    "calculate_confidence_score",
    "ConformalPredictor",
    "AdaptiveConformalPredictor",
    "should_bet_with_conformal",
    "ProbabilityStacker",
    "StackedProbability",
    "stack_for_week",
    "odds_to_probability",
    "spread_to_probability",
    # Copula and correlation models
    "GaussianCopula",
    "MultivariateGaussianCopula",
    "VineCopulaSimplified",
    "CorrelationDiscovery",
    "EmpiricalCorrelationEngine",
    "EmpiricalCorrelation",
    "VALIDATED_CORRELATIONS",
    "get_recommended_sgp_combinations",
]
