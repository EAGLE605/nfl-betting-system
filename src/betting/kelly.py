"""Kelly Criterion for optimal bet sizing.

Formula: f = (p*b - q) / b
where:
  f = fraction of bankroll to bet
  p = probability of winning
  b = odds - 1 (e.g., 0.91 for 1.91 decimal odds)
  q = 1 - p (probability of losing)

We use 1/4 Kelly to reduce variance.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


class KellyCriterion:
    """Kelly criterion calculator."""
    
    def __init__(
        self,
        kelly_fraction: float = 0.25,
        min_edge: float = 0.02,
        min_probability: float = 0.55,
        max_bet_pct: float = 0.02
    ):
        """
        Initialize Kelly calculator.
        
        Args:
            kelly_fraction: Fraction of Kelly to use (0.25 = 1/4 Kelly)
            min_edge: Minimum edge required (2%)
            min_probability: Minimum probability to bet (55%)
            max_bet_pct: Maximum bet as % of bankroll (2%)
        """
        self.kelly_fraction = kelly_fraction
        self.min_edge = min_edge
        self.min_probability = min_probability
        self.max_bet_pct = max_bet_pct
    
    def calculate_bet_size(
        self,
        prob_win: float,
        odds: float,
        bankroll: float
    ) -> float:
        """
        Calculate optimal bet size.
        
        Args:
            prob_win: Model probability of winning (0-1)
            odds: Decimal odds (e.g., 1.91)
            bankroll: Current bankroll
            
        Returns:
            Bet size in dollars (0 if no edge)
        """
        # Check minimum probability
        if prob_win < self.min_probability:
            return 0.0
        
        # Calculate edge
        implied_prob = 1 / odds
        edge = prob_win - implied_prob
        
        # Check minimum edge
        if edge < self.min_edge:
            return 0.0
        
        # Kelly formula
        b = odds - 1  # Net odds
        kelly_full = (prob_win * b - (1 - prob_win)) / b
        
        # Apply fractional Kelly
        kelly_bet = kelly_full * self.kelly_fraction
        
        # Cap at maximum
        kelly_bet = min(kelly_bet, self.max_bet_pct)
        
        # Ensure non-negative
        kelly_bet = max(kelly_bet, 0.0)
        
        # Convert to dollars
        bet_size = bankroll * kelly_bet
        
        return bet_size

