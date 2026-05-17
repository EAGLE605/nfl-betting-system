"""Embedded knowledge - no doc loading required.

This file IS the documentation. Reading it to work on the code
automatically loads all validated findings into context.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Final


# =============================================================================
# MODEL PERFORMANCE (Validated May 2026, n=317, p<0.0001)
# =============================================================================

ACCURACY: Final[float] = 65.6  # High-confidence picks
ROI: Final[float] = 25.3  # At -110 odds
SAMPLE_SIZE: Final[int] = 317
P_VALUE: Final[float] = 0.0001
Z_SCORE: Final[float] = 4.95


# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

class Signal(Enum):
    """Pick signal based on model confidence."""
    STRONG = 0.68  # Bet this
    LEAN = 0.62    # Consider, smaller
    SKIP = 0.0     # Pass


# =============================================================================
# VALIDATED CORRELATIONS (from 198,513 plays)
# =============================================================================

@dataclass(frozen=True)
class Correlation:
    name: str
    theoretical: float
    empirical: float
    n: int
    valid: bool


CORRELATIONS: tuple[Correlation, ...] = (
    Correlation("qb_wr1_yards", 0.72, 0.68, 2278, True),
    Correlation("wr_receptions_yards", 0.75, 0.80, 16327, True),
    Correlation("wr1_wr2_yards", 0.15, 0.49, 2278, False),  # Theory wrong
    Correlation("rb_rush_rec_same", 0.40, -0.13, 4581, False),  # BUSTED
    Correlation("team_yards_tds", 0.55, 0.61, 2278, True),
)


# =============================================================================
# VALIDATED EDGES (Use these)
# =============================================================================

@dataclass(frozen=True)
class Edge:
    name: str
    effect: str
    confidence: str


EDGES: tuple[Edge, ...] = (
    Edge("target_share_22pct", "+62 yards vs <15%", "high"),
    Edge("qb_wr_stack", "+21% correlation", "high"),
    Edge("1h_full_game", "+37.5% correlation", "high"),
    Edge("rb_leading_script", "+12 yards", "high"),
    Edge("red_zone_3plus", "56% TD rate", "high"),
)


# =============================================================================
# BUSTED MYTHS (Avoid these)
# =============================================================================

@dataclass(frozen=True)
class Myth:
    claim: str
    reality: str


MYTHS: tuple[Myth, ...] = (
    Myth("Rest after bye helps", "-0.8 yards (none)"),
    Myth("RB dual threat correlates", "-0.13 (negative)"),
    Myth("Rising usage momentum", "Only +3 yards"),
    Myth("Matchups predict alone", "r=0.02 (zero)"),
    Myth("QB breaks out Year 2", "-6% (worse)"),
)


# =============================================================================
# YEAR 2 LEAPS (Position-specific)
# =============================================================================

YEAR2_LEAP: dict[str, float] = {
    "RB": 0.93,   # +93% - TARGET THESE
    "WR": 0.19,   # +19%
    "TE": 0.41,   # +41% (survivor bias)
    "QB": -0.06,  # -6% - AVOID "breakout" narratives
}


# =============================================================================
# WEATHER THRESHOLDS
# =============================================================================

WIND_THRESHOLD_MPH: Final[int] = 15  # Above this: -20 pass yards/team
RAIN_PASSING_REDUCTION: Final[float] = 0.12  # -12%
SNOW_FG_CONVERSION: Final[float] = 0.76  # vs 0.83 normal
HEAVY_SNOW_POINTS_REDUCTION: Final[float] = 0.25  # -25%


# =============================================================================
# REFEREE EDGE (Tuesday → Thursday window)
# =============================================================================

REFEREE_EXAMPLES: dict[str, str] = {
    "Alex Kemp": "Under 11/16, favorites 30-3 SU",
    "Shawn Smith": "23 DPI calls 2025, favors passing",
}


# =============================================================================
# SHARP MONEY SIGNAL
# =============================================================================

SHARP_MONEY_THRESHOLD: Final[float] = 0.30  # 30% bets getting 60% money = RLM


# =============================================================================
# RULES (Immutable principles)
# =============================================================================

RULES: tuple[str, ...] = (
    "NO GUESSING - only state what data shows",
    "VALIDATE EVERYTHING - check against empirical data",
    "WALK-FORWARD ONLY - train past, test future",
    "CITE SOURCES - include n=, CI, source",
    "ADMIT UNCERTAINTY - don't hide limitations",
    "NO DATA LEAKAGE - never use same-game data",
)


# =============================================================================
# NOVEL EDGES (Future implementation)
# =============================================================================

@dataclass(frozen=True)
class FutureEdge:
    id: str
    priority: int
    data_available: bool
    effort: str


FUTURE_EDGES: tuple[FutureEdge, ...] = (
    FutureEdge("referee_tendencies", 1, True, "medium"),
    FutureEdge("year2_rb_props", 2, True, "low"),
    FutureEdge("sharp_money_rlm", 3, False, "medium"),
    FutureEdge("wind_alerts", 4, True, "low"),
    FutureEdge("triage_agent", 5, True, "medium"),
    FutureEdge("sentiment", 6, False, "high"),
)
