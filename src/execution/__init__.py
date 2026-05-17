"""Execution module - Paper trading and scheduling.

Components:
- PaperTradingHarness: Simulates real-money execution
- WeeklyScheduler: Automated retraining and prediction generation
"""

from .paper_trading import (
    PaperTradingHarness,
    Trade,
    PerformanceReport,
    create_paper_trading_harness,
)
from .scheduler import (
    WeeklyScheduler,
    RetrainingJob,
    create_production_scheduler,
    SimpleScheduler,
)

__all__ = [
    'PaperTradingHarness',
    'Trade',
    'PerformanceReport',
    'create_paper_trading_harness',
    'WeeklyScheduler',
    'RetrainingJob',
    'create_production_scheduler',
    'SimpleScheduler',
]
