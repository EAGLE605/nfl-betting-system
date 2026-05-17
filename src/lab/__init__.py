"""Model Laboratory - Novelty Testing & Evolution System

A transparent, auditable system for developing and graduating betting models.

Stages:
1. EXPLORATION - Research novel data sources, wild ideas, no constraints
2. CANDIDATE - Initial validation shows promise, worth deeper testing
3. VALIDATION - Rigorous walk-forward testing, statistical significance
4. STAGED - Passed all tests, awaiting human review for production
5. PRODUCTION - Human-approved, deployed for real recommendations

Each model carries full audit trail: data sources, methodology, results, limitations.
"""

from .model_registry import (
    ModelRegistry,
    ModelStage,
    ModelCandidate,
    register_model,
    promote_model,
    get_production_models,
)

from .novelty_sources import (
    NoveltySource,
    NoveltyTester,
    REGISTERED_SOURCES,
)

from .validation_harness import (
    ValidationHarness,
    ValidationResult,
    run_walk_forward_validation,
)

from .metrics import (
    REAL_WORLD_CONSTRAINTS,
    calculate_roi,
    calculate_breakeven,
    is_statistically_significant,
    format_metrics_report,
)

__all__ = [
    "ModelRegistry",
    "ModelStage",
    "ModelCandidate",
    "register_model",
    "promote_model",
    "get_production_models",
    "NoveltySource",
    "NoveltyTester",
    "REGISTERED_SOURCES",
    "ValidationHarness",
    "ValidationResult",
    "run_walk_forward_validation",
    "REAL_WORLD_CONSTRAINTS",
    "calculate_roi",
    "calculate_breakeven",
    "is_statistically_significant",
    "format_metrics_report",
]
