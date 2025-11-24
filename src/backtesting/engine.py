"""Walk-forward backtesting engine.

Simulates betting on historical games with realistic constraints.
"""

import logging
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from src.betting.kelly import KellyCriterion

logger = logging.getLogger(__name__)


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
        """Calculate performance metrics."""
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

        # CLV
        avg_clv = history_df["clv"].mean() * 100
        positive_clv_pct = (history_df["clv"] > 0).sum() / len(history_df) * 100

        metrics = {
            "total_bets": self.bet_count,
            "wins": self.win_count,
            "losses": self.bet_count - self.win_count,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "roi": roi,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe,
            "final_bankroll": self.bankroll,
            "avg_clv": avg_clv,
            "positive_clv_pct": positive_clv_pct,
        }

        return metrics, history_df
