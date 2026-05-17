"""Risk Engine - Professional-grade bankroll management for recreational bettors.

Key protections:
- 1% max risk per bet (recreational safe)
- 12% max drawdown circuit breaker (prevents emotional blow-ups)
- Fractional Kelly (0.20) for conservative growth
- Minimum confidence threshold (56%)

Based on research:
- Kelly Criterion with fractional betting
- Drawdown-based risk adjustment
- Professional bankroll management adapted for fun/recreational use
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    """Risk management configuration."""
    max_risk_per_bet: float = 0.01      # 1% max per bet (recreational safe)
    max_drawdown: float = 0.12          # 12% drawdown triggers circuit breaker
    kelly_fraction: float = 0.20        # Conservative fractional Kelly
    min_confidence: float = 0.56        # Minimum probability to bet
    min_edge: float = 0.03              # 3% minimum edge
    min_bet: float = 5.0                # $5 minimum bet
    max_bet: float = 500.0              # $500 maximum bet
    daily_loss_limit: float = 0.05      # 5% daily loss limit


@dataclass
class BetSizing:
    """Result of bet sizing calculation."""
    stake: float
    kelly_pct: float
    edge: float
    approved: bool
    reason: str
    risk_level: str  # LOW, MEDIUM, HIGH


class RiskEngine:
    """
    Professional-grade risk management for recreational bettors.

    Features:
    - Kelly Criterion with fractional betting
    - Drawdown-based circuit breaker
    - Daily loss limits
    - Edge validation
    """

    # Standard juice for -110 odds
    STANDARD_JUICE = 1.91  # Decimal odds for -110

    def __init__(self, config: Optional[RiskConfig] = None, initial_bankroll: float = 10000):
        self.config = config or RiskConfig()
        self.initial_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.current_drawdown = 0.0
        self.daily_pnl = 0.0
        self.daily_bets = 0
        self.last_reset_date = datetime.now().date()
        self.circuit_breaker_active = False
        self.bet_history: List[Dict] = []

    def update_bankroll(self, new_bankroll: float):
        """Update bankroll and recalculate drawdown."""
        pnl = new_bankroll - self.current_bankroll
        self.current_bankroll = new_bankroll

        # Track daily P&L
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_bets = 0
            self.last_reset_date = today

        self.daily_pnl += pnl
        self.daily_bets += 1

        # Update peak and drawdown
        if new_bankroll > self.peak_bankroll:
            self.peak_bankroll = new_bankroll
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_bankroll - new_bankroll) / self.peak_bankroll

        # Check circuit breaker
        self._check_circuit_breaker()

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should activate."""
        # Drawdown circuit breaker
        if self.current_drawdown > self.config.max_drawdown:
            self.circuit_breaker_active = True
            logger.warning(f"CIRCUIT BREAKER: Drawdown {self.current_drawdown:.1%} exceeds limit")
            return True

        # Daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / self.current_bankroll if self.daily_pnl < 0 else 0
        if daily_loss_pct > self.config.daily_loss_limit:
            self.circuit_breaker_active = True
            logger.warning(f"CIRCUIT BREAKER: Daily loss {daily_loss_pct:.1%} exceeds limit")
            return True

        self.circuit_breaker_active = False
        return False

    def calculate_kelly(self, win_probability: float, decimal_odds: float = None) -> float:
        """
        Calculate Kelly Criterion stake percentage.

        Kelly % = (bp - q) / b
        where:
        - b = decimal odds - 1 (net odds)
        - p = probability of winning
        - q = probability of losing (1 - p)
        """
        if decimal_odds is None:
            decimal_odds = self.STANDARD_JUICE

        b = decimal_odds - 1  # Net odds
        p = win_probability
        q = 1 - p

        kelly = (b * p - q) / b if b > 0 else 0
        return max(0, kelly)

    def calculate_edge(self, win_probability: float, decimal_odds: float = None) -> float:
        """
        Calculate expected edge.

        Edge = (probability * odds) - 1
        """
        if decimal_odds is None:
            decimal_odds = self.STANDARD_JUICE

        expected_return = win_probability * decimal_odds
        edge = expected_return - 1
        return edge

    def size_bet(
        self,
        win_probability: float,
        decimal_odds: float = None,
        confidence: str = "MEDIUM",
    ) -> BetSizing:
        """
        Calculate optimal bet size with all risk checks.

        Args:
            win_probability: Model's probability of winning
            decimal_odds: Decimal odds (default: 1.91 for -110)
            confidence: Confidence level (HIGH, MEDIUM, LOW)

        Returns:
            BetSizing with stake and approval status
        """
        if decimal_odds is None:
            decimal_odds = self.STANDARD_JUICE

        # Check circuit breaker
        if self.circuit_breaker_active:
            return BetSizing(
                stake=0,
                kelly_pct=0,
                edge=0,
                approved=False,
                reason="Circuit breaker active - betting suspended",
                risk_level="HIGH"
            )

        # Check minimum confidence
        if win_probability < self.config.min_confidence:
            return BetSizing(
                stake=0,
                kelly_pct=0,
                edge=self.calculate_edge(win_probability, decimal_odds),
                approved=False,
                reason=f"Probability {win_probability:.1%} below minimum {self.config.min_confidence:.1%}",
                risk_level="LOW"
            )

        # Calculate edge
        edge = self.calculate_edge(win_probability, decimal_odds)

        if edge < self.config.min_edge:
            return BetSizing(
                stake=0,
                kelly_pct=0,
                edge=edge,
                approved=False,
                reason=f"Edge {edge:.1%} below minimum {self.config.min_edge:.1%}",
                risk_level="LOW"
            )

        # Calculate Kelly
        kelly_pct = self.calculate_kelly(win_probability, decimal_odds)

        # Apply fractional Kelly
        fractional_kelly = kelly_pct * self.config.kelly_fraction

        # Cap at max risk
        stake_pct = min(fractional_kelly, self.config.max_risk_per_bet)

        # Adjust for confidence
        confidence_multiplier = {
            "HIGH": 1.0,
            "MEDIUM": 0.75,
            "LOW": 0.5,
        }
        stake_pct *= confidence_multiplier.get(confidence, 0.75)

        # Calculate dollar amount
        stake = self.current_bankroll * stake_pct

        # Apply min/max limits
        stake = max(self.config.min_bet, min(stake, self.config.max_bet))

        # Determine risk level
        if stake_pct > 0.008:
            risk_level = "HIGH"
        elif stake_pct > 0.005:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return BetSizing(
            stake=round(stake, 2),
            kelly_pct=kelly_pct,
            edge=edge,
            approved=True,
            reason=f"Edge: {edge:.1%}, Kelly: {kelly_pct:.1%}, Fractional: {stake_pct:.2%}",
            risk_level=risk_level
        )

    def get_status(self) -> Dict:
        """Get current risk status."""
        return {
            "bankroll": round(self.current_bankroll, 2),
            "peak_bankroll": round(self.peak_bankroll, 2),
            "drawdown": f"{self.current_drawdown:.1%}",
            "drawdown_limit": f"{self.config.max_drawdown:.0%}",
            "circuit_breaker": self.circuit_breaker_active,
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_bets": self.daily_bets,
            "risk_per_bet": f"{self.config.max_risk_per_bet:.0%}",
        }

    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (use with caution)."""
        if self.current_drawdown <= self.config.max_drawdown:
            self.circuit_breaker_active = False
            logger.info("Circuit breaker reset")
        else:
            logger.warning("Cannot reset - still in drawdown")


def create_risk_engine(
    initial_bankroll: float = 10000,
    config: Optional[RiskConfig] = None,
) -> RiskEngine:
    """Factory function for risk engine."""
    return RiskEngine(config=config, initial_bankroll=initial_bankroll)
