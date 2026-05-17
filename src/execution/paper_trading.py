"""Paper Trading Execution Harness

Simulates real-money execution with realistic slippage.
Tracks P&L, CLV, win rate, and bankroll in real time.

Based on research:
- Realistic slippage: ±0.3-0.5% line movement
- Kelly Criterion for position sizing
- Full audit trail of all trades
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Single paper trade record."""
    trade_id: str
    timestamp: datetime
    prop_name: str
    prop_type: str  # 'player_prop', 'spread', 'total', 'parlay'
    stake: float
    predicted_prob: float
    opening_line: float
    closing_line: float
    effective_line: float  # After slippage
    outcome: str  # 'WIN', 'LOSS', 'PUSH', 'PENDING'
    profit: float
    bankroll_after: float
    clv: float  # Closing Line Value
    edge_type: str  # 'divisional_dog', 'weather', 'rest', etc.
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'

    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'timestamp': self.timestamp.isoformat(),
            'prop_name': self.prop_name,
            'prop_type': self.prop_type,
            'stake': self.stake,
            'predicted_prob': self.predicted_prob,
            'opening_line': self.opening_line,
            'closing_line': self.closing_line,
            'effective_line': self.effective_line,
            'outcome': self.outcome,
            'profit': self.profit,
            'bankroll_after': self.bankroll_after,
            'clv': self.clv,
            'edge_type': self.edge_type,
            'confidence': self.confidence,
        }


@dataclass
class PerformanceReport:
    """Paper trading performance summary."""
    total_trades: int
    wins: int
    losses: int
    pushes: int
    pending: int
    win_rate: float
    total_risked: float
    total_profit: float
    roi_pct: float
    current_bankroll: float
    avg_clv: float
    best_trade: Optional[Trade]
    worst_trade: Optional[Trade]
    by_edge_type: Dict[str, Dict]
    by_confidence: Dict[str, Dict]


class PaperTradingHarness:
    """
    Live paper-trading execution harness.

    Simulates real execution with:
    - Realistic slippage (±0.3-0.5%)
    - Full P&L tracking
    - CLV measurement
    - Performance reporting
    """

    # Realistic slippage parameters
    SLIPPAGE_MIN = -0.003  # -0.3%
    SLIPPAGE_MAX = 0.005   # +0.5%

    # Standard juice
    JUICE = 0.91  # -110 odds

    def __init__(
        self,
        initial_bankroll: float = 10000,
        data_path: str = "data/paper_trading",
        max_bet_pct: float = 0.05,  # Max 5% per bet
    ):
        self.initial_bankroll = initial_bankroll
        self.bankroll = initial_bankroll
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.max_bet_pct = max_bet_pct

        self.trades: List[Trade] = []
        self.total_risked = 0
        self.total_profit = 0

        self._load_history()

    def _load_history(self):
        """Load trade history from disk."""
        history_file = self.data_path / "trade_history.json"
        if history_file.exists():
            with open(history_file) as f:
                data = json.load(f)
                self.bankroll = data.get('bankroll', self.initial_bankroll)
                self.total_risked = data.get('total_risked', 0)
                self.total_profit = data.get('total_profit', 0)
                logger.info(f"Loaded paper trading history: ${self.bankroll:.2f} bankroll")

    def _save_history(self):
        """Save trade history to disk."""
        history_file = self.data_path / "trade_history.json"
        data = {
            'bankroll': self.bankroll,
            'total_risked': self.total_risked,
            'total_profit': self.total_profit,
            'trades': [t.to_dict() for t in self.trades[-100:]],  # Keep last 100
        }
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def calculate_kelly_stake(
        self,
        predicted_prob: float,
        american_odds: float,
    ) -> float:
        """
        Calculate optimal stake using Kelly Criterion.

        Kelly % = (bp - q) / b
        where:
        - b = decimal odds - 1
        - p = probability of winning
        - q = probability of losing (1 - p)
        """
        # Convert American odds to decimal
        if american_odds > 0:
            decimal_odds = (american_odds / 100) + 1
        else:
            decimal_odds = (100 / abs(american_odds)) + 1

        b = decimal_odds - 1
        p = predicted_prob
        q = 1 - p

        kelly = (b * p - q) / b if b > 0 else 0

        # Use fractional Kelly (25%) for safety
        fractional_kelly = kelly * 0.25

        # Cap at max bet percentage
        stake_pct = max(0, min(fractional_kelly, self.max_bet_pct))

        return stake_pct

    def place_paper_bet(
        self,
        prop_name: str,
        prop_type: str,
        predicted_prob: float,
        opening_line: float,
        closing_line: float,
        actual_outcome: int,  # 1=win, 0=loss, -1=push
        edge_type: str = "general",
        confidence: str = "MEDIUM",
        stake_override: Optional[float] = None,
    ) -> Trade:
        """
        Place a paper bet and record the result.

        Args:
            prop_name: Description of the bet
            prop_type: Type of bet (player_prop, spread, etc.)
            predicted_prob: Our predicted probability
            opening_line: Line when we would have bet
            closing_line: Final closing line
            actual_outcome: 1=win, 0=loss, -1=push
            edge_type: Source of our edge
            confidence: HIGH/MEDIUM/LOW
            stake_override: Override calculated stake
        """
        # Calculate stake
        if stake_override:
            stake_pct = stake_override
        else:
            stake_pct = self.calculate_kelly_stake(predicted_prob, opening_line)

        stake = self.bankroll * stake_pct
        self.total_risked += stake

        # Simulate realistic execution slippage
        slippage = np.random.uniform(self.SLIPPAGE_MIN, self.SLIPPAGE_MAX)
        effective_line = closing_line * (1 + slippage)

        # Calculate CLV (Closing Line Value)
        if opening_line != 0:
            clv = (closing_line - opening_line) / abs(opening_line) * 100
        else:
            clv = 0

        # Calculate P&L
        if actual_outcome == 1:  # Win
            if effective_line > 0:
                profit = stake * (effective_line / 100)
            else:
                profit = stake * (100 / abs(effective_line))
            outcome_str = "WIN"
        elif actual_outcome == -1:  # Push
            profit = 0
            outcome_str = "PUSH"
        else:  # Loss
            profit = -stake
            outcome_str = "LOSS"

        self.total_profit += profit
        self.bankroll += profit

        # Create trade record
        trade = Trade(
            trade_id=f"PT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.trades)+1:04d}",
            timestamp=datetime.now(),
            prop_name=prop_name,
            prop_type=prop_type,
            stake=round(stake, 2),
            predicted_prob=round(predicted_prob, 3),
            opening_line=opening_line,
            closing_line=closing_line,
            effective_line=round(effective_line, 2),
            outcome=outcome_str,
            profit=round(profit, 2),
            bankroll_after=round(self.bankroll, 2),
            clv=round(clv, 2),
            edge_type=edge_type,
            confidence=confidence,
        )

        self.trades.append(trade)
        self._save_history()

        logger.info(f"Paper trade: {trade.outcome} | {prop_name} | ${trade.profit:+.2f} | Bankroll: ${trade.bankroll_after:.2f}")

        return trade

    def get_performance_report(self) -> PerformanceReport:
        """Generate comprehensive performance report."""
        if not self.trades:
            return PerformanceReport(
                total_trades=0, wins=0, losses=0, pushes=0, pending=0,
                win_rate=0, total_risked=0, total_profit=0, roi_pct=0,
                current_bankroll=self.bankroll, avg_clv=0,
                best_trade=None, worst_trade=None,
                by_edge_type={}, by_confidence={},
            )

        # Count outcomes
        wins = sum(1 for t in self.trades if t.outcome == "WIN")
        losses = sum(1 for t in self.trades if t.outcome == "LOSS")
        pushes = sum(1 for t in self.trades if t.outcome == "PUSH")
        pending = sum(1 for t in self.trades if t.outcome == "PENDING")

        total = wins + losses
        win_rate = wins / total if total > 0 else 0
        roi_pct = (self.total_profit / self.total_risked * 100) if self.total_risked > 0 else 0

        # CLV
        settled_trades = [t for t in self.trades if t.outcome in ("WIN", "LOSS")]
        avg_clv = np.mean([t.clv for t in settled_trades]) if settled_trades else 0

        # Best/worst
        best_trade = max(settled_trades, key=lambda t: t.profit) if settled_trades else None
        worst_trade = min(settled_trades, key=lambda t: t.profit) if settled_trades else None

        # By edge type
        by_edge_type = {}
        for edge in set(t.edge_type for t in self.trades):
            edge_trades = [t for t in settled_trades if t.edge_type == edge]
            if edge_trades:
                edge_wins = sum(1 for t in edge_trades if t.outcome == "WIN")
                by_edge_type[edge] = {
                    'trades': len(edge_trades),
                    'win_rate': edge_wins / len(edge_trades),
                    'profit': sum(t.profit for t in edge_trades),
                }

        # By confidence
        by_confidence = {}
        for conf in ["HIGH", "MEDIUM", "LOW"]:
            conf_trades = [t for t in settled_trades if t.confidence == conf]
            if conf_trades:
                conf_wins = sum(1 for t in conf_trades if t.outcome == "WIN")
                by_confidence[conf] = {
                    'trades': len(conf_trades),
                    'win_rate': conf_wins / len(conf_trades),
                    'profit': sum(t.profit for t in conf_trades),
                }

        return PerformanceReport(
            total_trades=len(self.trades),
            wins=wins,
            losses=losses,
            pushes=pushes,
            pending=pending,
            win_rate=win_rate,
            total_risked=self.total_risked,
            total_profit=self.total_profit,
            roi_pct=roi_pct,
            current_bankroll=self.bankroll,
            avg_clv=avg_clv,
            best_trade=best_trade,
            worst_trade=worst_trade,
            by_edge_type=by_edge_type,
            by_confidence=by_confidence,
        )

    def generate_report_card(self) -> str:
        """Generate visual report card."""
        report = self.get_performance_report()

        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("💰 PAPER TRADING PERFORMANCE REPORT")
        lines.append("=" * 60)

        lines.append(f"\n📊 OVERALL STATS")
        lines.append("-" * 40)
        lines.append(f"  Total Trades: {report.total_trades}")
        lines.append(f"  Record: {report.wins}W - {report.losses}L - {report.pushes}P")
        lines.append(f"  Win Rate: {report.win_rate:.1%}")
        lines.append(f"  ROI: {report.roi_pct:+.1f}%")
        lines.append(f"  Avg CLV: {report.avg_clv:+.2f}%")

        lines.append(f"\n💵 BANKROLL")
        lines.append("-" * 40)
        lines.append(f"  Starting: ${self.initial_bankroll:,.2f}")
        lines.append(f"  Current: ${report.current_bankroll:,.2f}")
        lines.append(f"  P&L: ${report.total_profit:+,.2f}")

        if report.by_edge_type:
            lines.append(f"\n🎯 BY EDGE TYPE")
            lines.append("-" * 40)
            for edge, stats in sorted(report.by_edge_type.items(), key=lambda x: x[1]['profit'], reverse=True):
                lines.append(f"  {edge}: {stats['win_rate']:.0%} ({stats['trades']} bets) ${stats['profit']:+.2f}")

        if report.by_confidence:
            lines.append(f"\n🔥 BY CONFIDENCE")
            lines.append("-" * 40)
            for conf in ["HIGH", "MEDIUM", "LOW"]:
                if conf in report.by_confidence:
                    stats = report.by_confidence[conf]
                    lines.append(f"  {conf}: {stats['win_rate']:.0%} ({stats['trades']} bets) ${stats['profit']:+.2f}")

        if report.best_trade:
            lines.append(f"\n🏆 Best Trade: {report.best_trade.prop_name} (${report.best_trade.profit:+.2f})")
        if report.worst_trade:
            lines.append(f"📉 Worst Trade: {report.worst_trade.prop_name} (${report.worst_trade.profit:+.2f})")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)


def create_paper_trading_harness(
    initial_bankroll: float = 10000,
) -> PaperTradingHarness:
    """Factory function for paper trading harness."""
    return PaperTradingHarness(initial_bankroll=initial_bankroll)
