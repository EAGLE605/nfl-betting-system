"""Props module - Player props, SGPs, and correlation analysis.

Key components:
- CorrelationEngine: SGP correlation scoring and building
- DefenseMatchupAnalyzer: Defense-vs-position matchup edges
- HitRateTracker: Filter props by historical hit rates

Research-backed approach:
- 5-10% edges appear more in props than sides/totals
- Correlation drives SGP success
- Defense matchups are slow to price in
- 51%+ hit rate in 10+ games = actionable
"""

from .correlation_engine import (
    CorrelationEngine,
    PropType,
    CorrelationPair,
    build_correlated_sgp,
    print_correlation_analysis,
    SGP_TEMPLATES,
)
from .defense_matchups import (
    DefenseMatchupAnalyzer,
    MatchupAnalysis,
    MatchupGrade,
    Position,
    create_prop_with_matchup_adjustment,
)
from .hit_rate_tracker import (
    HitRateTracker,
    HitRateRecord,
    FilteredProp,
    create_filtered_prop,
    format_hot_props_sheet,
    generate_demo_hot_props,
)

__all__ = [
    # Correlation
    'CorrelationEngine',
    'PropType',
    'CorrelationPair',
    'build_correlated_sgp',
    'print_correlation_analysis',
    'SGP_TEMPLATES',
    # Defense matchups
    'DefenseMatchupAnalyzer',
    'MatchupAnalysis',
    'MatchupGrade',
    'Position',
    'create_prop_with_matchup_adjustment',
    # Hit rates
    'HitRateTracker',
    'HitRateRecord',
    'FilteredProp',
    'create_filtered_prop',
    'format_hot_props_sheet',
    'generate_demo_hot_props',
]
