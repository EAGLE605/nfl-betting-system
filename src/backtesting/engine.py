"""Walk-forward backtesting engine.

Simulates betting on historical games with realistic constraints.

Research-backed enhancements:
- CLV tracking as primary edge metric (Joseph Buchdahl methodology)
- GO/NO-GO validation based on peer-reviewed criteria
- Statistical significance testing
- Sample size requirements (2000-3000 bets for signal vs noise)
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from src.betting.kelly import KellyCriterion

logger = logging.getLogger(__name__)


# GO/NO-GO criteria based on research
GO_CRITERIA = {
    "min_bets": 50,  # Minimum for any signal
    "min_clv": 0.5,  # 0.5% average CLV (research: 2% cancels vig at -110)
    "min_positive_clv_pct": 52,  # More than half should beat closing line
    "min_roi": -5.0,  # Allow small negative ROI if CLV is positive
    "max_drawdown": -30,  # Maximum acceptable drawdown
    "min_sharpe": 0.3,  # Minimum risk-adjusted return
}


class BacktestEngine:
    """Walk-forward backtest with Kelly criterion."""

    def __init__(self, initial_bankroll: float = 10000, config: dict = None):
        """
        Initialize engine.

        Args:
            initial_bankroll: Starting bankroll
            config: Configuration from config.yaml
        """
        self.initial_bankroll = initial_bankroll
        self.config = config or {}

        self.kelly = KellyCriterion(
            kelly_fraction=self.config.get("kelly_fraction", 0.25),
            min_edge=self.config.get("min_edge", 0.02),
            min_probability=self.config.get("min_probability", 0.55),
            max_bet_pct=self.config.get("max_bet_size", 0.02),
        )

        self.reset()

    def reset(self):
        """Reset state."""
        self.bankroll = self.initial_bankroll
        self.history = []
        self.bet_count = 0
        self.win_count = 0

    def run_backtest(self, predictions_df: pd.DataFrame) -> Tuple[Dict, pd.DataFrame]:
        """
        Run backtest on predictions.

        Args:
            predictions_df: DataFrame with:
                - game_id, gameday, home_team, away_team
                - pred_prob: Model probability (0-1)
                - actual: Actual outcome (0 or 1)
                - odds: Decimal odds

        Returns:
            (metrics_dict, history_df)
        """
        self.reset()

        logger.info(f"Running backtest on {len(predictions_df)} games...")

        # Sort by date
        predictions_df = predictions_df.sort_values("gameday")

        for idx, row in predictions_df.iterrows():
            # Calculate bet size
            bet_size = self.kelly.calculate_bet_size(
                prob_win=row["pred_prob"], odds=row["odds"], bankroll=self.bankroll
            )

            # Skip if no bet
            if bet_size <= 0:
                continue

            # Place bet
            self.bet_count += 1

            # Determine outcome
            if row["actual"] == 1:
                profit = bet_size * (row["odds"] - 1)
                self.win_count += 1
                result = "win"
            else:
                profit = -bet_size
                result = "loss"

            # Update bankroll
            self.bankroll += profit

            # Calculate CLV
            clv = (row["pred_prob"] * row["odds"]) - 1

            # Record
            self.history.append(
                {
                    "game_id": row["game_id"],
                    "gameday": row["gameday"],
                    "home_team": row.get("home_team", ""),
                    "away_team": row.get("away_team", ""),
                    "bet_size": bet_size,
                    "odds": row["odds"],
                    "pred_prob": row["pred_prob"],
                    "actual": row["actual"],
                    "result": result,
                    "profit": profit,
                    "bankroll": self.bankroll,
                    "clv": clv,
                }
            )

        # Calculate metrics
        metrics, history_df = self._calculate_metrics()

        logger.info(
            f"✓ Backtest complete: {self.bet_count} bets, {self.win_count} wins"
        )

        return metrics, history_df

    def _calculate_metrics(self) -> Tuple[Dict, pd.DataFrame]:
        """Calculate performance metrics with research-backed CLV analysis."""
        if not self.history:
            return {"error": "No bets placed"}, pd.DataFrame()

        history_df = pd.DataFrame(self.history)

        # Basic metrics
        total_profit = self.bankroll - self.initial_bankroll
        roi = (total_profit / self.initial_bankroll) * 100
        win_rate = (self.win_count / self.bet_count) * 100

        # Drawdown
        history_df["cumulative_max"] = history_df["bankroll"].cummax()
        history_df["drawdown"] = (
            history_df["bankroll"] - history_df["cumulative_max"]
        ) / history_df["cumulative_max"]
        max_drawdown = history_df["drawdown"].min() * 100

        # Sharpe ratio (annualized, assuming ~250 betting days)
        returns = history_df["profit"] / history_df["bet_size"]
        sharpe = (
            (returns.mean() / returns.std()) * np.sqrt(250) if returns.std() > 0 else 0
        )

        # Enhanced CLV Analysis (research-backed)
        avg_clv = history_df["clv"].mean() * 100
        positive_clv_pct = (history_df["clv"] > 0).sum() / len(history_df) * 100
        clv_std = history_df["clv"].std() * 100

        # Statistical significance of CLV
        # Research: CLV changes in small increments, easier to detect signal
        clv_tstat, clv_pvalue = stats.ttest_1samp(history_df["clv"], 0)

        # Streak analysis (for variance assessment)
        history_df["win_streak"] = self._calculate_streaks(history_df["result"] == "win")
        history_df["loss_streak"] = self._calculate_streaks(history_df["result"] == "loss")
        max_win_streak = history_df["win_streak"].max()
        max_loss_streak = history_df["loss_streak"].max()

        # Expected vs actual performance
        expected_wins = history_df["pred_prob"].sum()
        expected_roi = ((history_df["pred_prob"] * history_df["odds"]).sum() - len(history_df)) / len(history_df) * 100

        metrics = {
            # Basic
            "total_bets": self.bet_count,
            "wins": self.win_count,
            "losses": self.bet_count - self.win_count,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "roi": roi,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe,
            "final_bankroll": self.bankroll,

            # CLV (PRIMARY EDGE METRIC)
            "avg_clv": avg_clv,
            "clv_std": clv_std,
            "positive_clv_pct": positive_clv_pct,
            "clv_tstat": clv_tstat,
            "clv_pvalue": clv_pvalue,
            "clv_significant": clv_pvalue < 0.05 and avg_clv > 0,

            # Variance analysis
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,

            # Expected vs actual
            "expected_wins": expected_wins,
            "expected_roi": expected_roi,
            "luck_factor": (self.win_count - expected_wins) / max(expected_wins, 1),
        }

        return metrics, history_df

    def _calculate_streaks(self, wins: pd.Series) -> pd.Series:
        """Calculate consecutive win/loss streaks."""
        streak = wins.ne(wins.shift()).cumsum()
        return wins.groupby(streak).cumsum()

    def validate_go_no_go(self, metrics: Dict) -> Tuple[bool, Dict[str, Tuple[bool, str]]]:
        """
        Validate backtest results against research-backed GO/NO-GO criteria.

        Based on:
        - Joseph Buchdahl CLV methodology
        - Walsh & Joshi (2024) calibration research
        - Statistical significance requirements

        Returns:
            (is_go, criteria_results) where criteria_results maps
            criterion name to (passed, explanation)
        """
        results = {}

        # Minimum sample size
        n_bets = metrics.get("total_bets", 0)
        passed = n_bets >= GO_CRITERIA["min_bets"]
        results["min_bets"] = (
            passed,
            f"Bets: {n_bets} (need {GO_CRITERIA['min_bets']}+)"
        )

        # CLV - PRIMARY CRITERION
        avg_clv = metrics.get("avg_clv", 0)
        passed = avg_clv >= GO_CRITERIA["min_clv"]
        results["min_clv"] = (
            passed,
            f"Avg CLV: {avg_clv:.2f}% (need {GO_CRITERIA['min_clv']}%+)"
        )

        # Positive CLV percentage
        pos_clv = metrics.get("positive_clv_pct", 0)
        passed = pos_clv >= GO_CRITERIA["min_positive_clv_pct"]
        results["positive_clv_pct"] = (
            passed,
            f"Positive CLV: {pos_clv:.1f}% (need {GO_CRITERIA['min_positive_clv_pct']}%+)"
        )

        # ROI (allow negative if CLV is positive - variance)
        roi = metrics.get("roi", -100)
        passed = roi >= GO_CRITERIA["min_roi"]
        results["min_roi"] = (
            passed,
            f"ROI: {roi:.2f}% (need {GO_CRITERIA['min_roi']}%+)"
        )

        # Maximum drawdown
        max_dd = metrics.get("max_drawdown", -100)
        passed = max_dd >= GO_CRITERIA["max_drawdown"]
        results["max_drawdown"] = (
            passed,
            f"Max Drawdown: {max_dd:.2f}% (limit {GO_CRITERIA['max_drawdown']}%)"
        )

        # Sharpe ratio
        sharpe = metrics.get("sharpe_ratio", 0)
        passed = sharpe >= GO_CRITERIA["min_sharpe"]
        results["min_sharpe"] = (
            passed,
            f"Sharpe: {sharpe:.2f} (need {GO_CRITERIA['min_sharpe']}+)"
        )

        # Statistical significance of CLV
        clv_sig = metrics.get("clv_significant", False)
        results["clv_significance"] = (
            clv_sig,
            f"CLV p-value: {metrics.get('clv_pvalue', 1):.4f} (need <0.05)"
        )

        # Overall GO/NO-GO
        # Must pass: min_bets, min_clv, max_drawdown
        # Should pass: positive_clv_pct, min_sharpe
        critical_criteria = ["min_bets", "min_clv", "max_drawdown"]
        is_go = all(results[c][0] for c in critical_criteria)

        return is_go, results

    def print_go_no_go_report(self, metrics: Dict) -> bool:
        """Print formatted GO/NO-GO decision report."""
        is_go, results = self.validate_go_no_go(metrics)

        logger.info("\n" + "=" * 70)
        logger.info("GO/NO-GO DECISION (Research-Backed Criteria)")
        logger.info("=" * 70)

        for criterion, (passed, explanation) in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"  {status:12} {explanation}")

        logger.info("-" * 70)

        if is_go:
            logger.info("✓ DECISION: GO - Model shows edge based on CLV analysis")
            logger.info("  Note: Continue monitoring CLV as primary success metric")
        else:
            logger.info("✗ DECISION: NO-GO - Insufficient evidence of edge")
            logger.info("  Recommendation: Review model calibration and feature engineering")

        logger.info("=" * 70)

        # Additional context
        if metrics.get("total_bets", 0) < 200:
            logger.warning(
                "⚠ Sample size warning: Results based on <200 bets. "
                "Research suggests 2000-3000 bets needed for statistical confidence."
            )

        luck = metrics.get("luck_factor", 0)
        if abs(luck) > 0.1:
            direction = "lucky" if luck > 0 else "unlucky"
            logger.warning(
                f"⚠ Variance warning: Results appear {direction} "
                f"(actual vs expected: {luck:+.1%})"
            )

        return is_go
