"""BULLDOG MODE: Visualization Suite

Generate all required professional visualizations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import seaborn as sns

    sns.set_style("whitegrid")
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
plt.style.use("default")
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.size"] = 10
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3

OUTPUT_DIR = Path("reports/bulldog_mode/visualizations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class BulldogVisualizations:
    """Generate all visualizations for Bulldog Mode."""

    def __init__(self, results_path: str = None, bets_path: str = None):
        """Initialize visualization generator."""
        # Load data
        if results_path is None:
            results_path = Path(
                "reports/bulldog_mode/data/bulldog_performance_by_segment.csv"
            )
        if bets_path is None:
            bets_path = Path("reports/bulldog_mode/data/bulldog_backtest_results.csv")

        if results_path.exists():
            self.results_df = pd.read_csv(results_path)
        else:
            logger.warning(f"Results file not found: {results_path}")
            self.results_df = None

        if bets_path.exists():
            self.bets_df = pd.read_csv(bets_path)
        else:
            logger.warning(f"Bets file not found: {bets_path}")
            self.bets_df = None

    def plot_equity_curve(self):
        """1. Equity Curve - Bankroll over time"""
        logger.info("Creating equity curve...")

        if self.bets_df is None or len(self.bets_df) == 0:
            logger.warning("No bet data for equity curve")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Get main scenario (full period)
        main_bets = self.bets_df[
            self.bets_df["scenario"] == "Full Period (2020-2024)"
        ].copy()
        if len(main_bets) == 0:
            main_bets = self.bets_df.copy()

        main_bets = main_bets.sort_values("gameday").reset_index(drop=True)

        # Equity curve
        ax1.plot(main_bets.index, main_bets["bankroll"], linewidth=2, color="#2E86AB")
        ax1.axhline(
            y=main_bets["bankroll"].iloc[0],
            color="r",
            linestyle="--",
            label="Initial Bankroll",
            alpha=0.7,
        )
        ax1.set_xlabel("Bet Number", fontsize=12)
        ax1.set_ylabel("Bankroll ($)", fontsize=12)
        ax1.set_title("Equity Curve - Bulldog Backtest", fontsize=14, fontweight="bold")
        ax1.legend()
        ax1.grid(alpha=0.3)

        # Drawdown
        cumulative_max = main_bets["bankroll"].cummax()
        drawdown = (main_bets["bankroll"] - cumulative_max) / cumulative_max * 100

        ax2.fill_between(main_bets.index, drawdown, 0, color="red", alpha=0.3)
        ax2.plot(main_bets.index, drawdown, linewidth=2, color="red")
        ax2.set_xlabel("Bet Number", fontsize=12)
        ax2.set_ylabel("Drawdown (%)", fontsize=12)
        ax2.set_title("Drawdown Over Time", fontsize=14, fontweight="bold")
        ax2.grid(alpha=0.3)
        ax2.axhline(y=0, color="black", linestyle="-", alpha=0.3)

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "equity_curve.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ Equity curve saved")

    def plot_win_rate_by_month(self):
        """2. Win Rate by Month - Temporal patterns"""
        logger.info("Creating win rate by month...")

        if self.bets_df is None or len(self.bets_df) == 0:
            logger.warning("No bet data for win rate by month")
            return

        main_bets = self.bets_df.copy()
        if "gameday" in main_bets.columns:
            main_bets["gameday"] = pd.to_datetime(main_bets["gameday"])
            main_bets["month"] = main_bets["gameday"].dt.month
            main_bets["year_month"] = main_bets["gameday"].dt.to_period("M")

            monthly_stats = (
                main_bets.groupby("year_month")
                .agg({"result": lambda x: (x == "win").sum(), "bet_size": "count"})
                .rename(columns={"result": "wins", "bet_size": "total_bets"})
            )
            monthly_stats["win_rate"] = (
                monthly_stats["wins"] / monthly_stats["total_bets"] * 100
            )

            fig, ax = plt.subplots(figsize=(14, 6))
            ax.bar(
                range(len(monthly_stats)),
                monthly_stats["win_rate"],
                color="#2E86AB",
                alpha=0.7,
            )
            ax.axhline(
                y=50, color="r", linestyle="--", label="Break-even (50%)", alpha=0.7
            )
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Win Rate (%)", fontsize=12)
            ax.set_title("Win Rate by Month", fontsize=14, fontweight="bold")
            ax.set_xticks(range(len(monthly_stats)))
            ax.set_xticklabels(
                [str(x) for x in monthly_stats.index], rotation=45, ha="right"
            )
            ax.legend()
            ax.grid(alpha=0.3, axis="y")

            plt.tight_layout()
            plt.savefig(OUTPUT_DIR / "win_rate_by_month.png", bbox_inches="tight")
            plt.close()
            logger.info("✓ Win rate by month saved")

    def plot_roi_by_segment(self):
        """3. ROI by Segment - Heatmap"""
        logger.info("Creating ROI by segment heatmap...")

        if self.results_df is None or len(self.results_df) == 0:
            logger.warning("No results data for ROI heatmap")
            return

        # Filter to relevant scenarios
        relevant = self.results_df[
            (self.results_df["total_bets"] > 0) & (self.results_df["roi"].notna())
        ].copy()

        if len(relevant) == 0:
            logger.warning("No valid data for ROI heatmap")
            return

        # Create pivot table (simplified - just show top scenarios)
        top_scenarios = relevant.nlargest(20, "total_bets")

        fig, ax = plt.subplots(figsize=(12, 8))

        y_pos = np.arange(len(top_scenarios))
        colors = ["green" if x > 0 else "red" for x in top_scenarios["roi"]]

        ax.barh(y_pos, top_scenarios["roi"], color=colors, alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(top_scenarios["name"], fontsize=9)
        ax.set_xlabel("ROI (%)", fontsize=12)
        ax.set_title("ROI by Segment (Top 20)", fontsize=14, fontweight="bold")
        ax.axvline(x=0, color="black", linestyle="-", alpha=0.3)
        ax.grid(alpha=0.3, axis="x")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "roi_by_segment.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ ROI by segment saved")

    def plot_feature_importance(self):
        """4. Feature Importance - Bar chart (top 20)"""
        logger.info("Creating feature importance chart...")

        importance_path = Path(
            "reports/bulldog_mode/data/bulldog_feature_importance.csv"
        )
        if not importance_path.exists():
            logger.warning("Feature importance file not found")
            return

        importance_df = pd.read_csv(importance_path)
        top_20 = importance_df.head(20)

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.barh(
            range(len(top_20)), top_20["importance_pct"], color="#2E86AB", alpha=0.7
        )
        ax.set_yticks(range(len(top_20)))
        ax.set_yticklabels(top_20["feature"], fontsize=9)
        ax.set_xlabel("Importance (%)", fontsize=12)
        ax.set_title("Top 20 Feature Importance", fontsize=14, fontweight="bold")
        ax.invert_yaxis()
        ax.grid(alpha=0.3, axis="x")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "feature_importance.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ Feature importance saved")

    def plot_drawdown_analysis(self):
        """5. Drawdown Analysis - Underwater chart"""
        logger.info("Creating drawdown analysis...")

        if self.bets_df is None or len(self.bets_df) == 0:
            logger.warning("No bet data for drawdown analysis")
            return

        main_bets = self.bets_df.copy()
        if len(main_bets) == 0:
            return

        main_bets = main_bets.sort_values("gameday").reset_index(drop=True)

        cumulative_max = main_bets["bankroll"].cummax()
        drawdown = (main_bets["bankroll"] - cumulative_max) / cumulative_max * 100

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.fill_between(main_bets.index, drawdown, 0, color="red", alpha=0.4)
        ax.plot(main_bets.index, drawdown, linewidth=2, color="darkred")
        ax.set_xlabel("Bet Number", fontsize=12)
        ax.set_ylabel("Drawdown (%)", fontsize=12)
        ax.set_title(
            "Underwater Chart - Drawdown Analysis", fontsize=14, fontweight="bold"
        )
        ax.grid(alpha=0.3)
        ax.axhline(y=0, color="black", linestyle="-", alpha=0.3)

        # Mark max drawdown
        max_dd_idx = drawdown.idxmin()
        max_dd_val = drawdown.min()
        ax.plot(max_dd_idx, max_dd_val, "ro", markersize=10)
        ax.annotate(
            f"Max DD: {max_dd_val:.1f}%",
            xy=(max_dd_idx, max_dd_val),
            xytext=(max_dd_idx + len(main_bets) * 0.1, max_dd_val),
            fontsize=10,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="red"),
        )

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "drawdown_analysis.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ Drawdown analysis saved")

    def plot_bet_size_distribution(self):
        """6. Bet Size Distribution - Histogram"""
        logger.info("Creating bet size distribution...")

        if self.bets_df is None or len(self.bets_df) == 0:
            logger.warning("No bet data for bet size distribution")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(
            self.bets_df["bet_size"],
            bins=50,
            color="#2E86AB",
            alpha=0.7,
            edgecolor="black",
        )
        ax.set_xlabel("Bet Size ($)", fontsize=12)
        ax.set_ylabel("Frequency", fontsize=12)
        ax.set_title("Bet Size Distribution", fontsize=14, fontweight="bold")
        ax.axvline(
            self.bets_df["bet_size"].mean(),
            color="r",
            linestyle="--",
            label=f'Mean: ${self.bets_df["bet_size"].mean():.2f}',
        )
        ax.legend()
        ax.grid(alpha=0.3, axis="y")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "bet_size_distribution.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ Bet size distribution saved")

    def plot_win_loss_streaks(self):
        """7. Win/Loss Streaks - Timeline"""
        logger.info("Creating win/loss streaks...")

        if self.bets_df is None or len(self.bets_df) == 0:
            logger.warning("No bet data for streaks")
            return

        main_bets = self.bets_df.copy()
        main_bets = main_bets.sort_values("gameday").reset_index(drop=True)

        # Calculate streaks
        main_bets["is_win"] = (main_bets["result"] == "win").astype(int)
        main_bets["streak"] = (main_bets["is_win"].diff() != 0).cumsum()
        streaks = (
            main_bets.groupby("streak")
            .agg({"is_win": "first", "bet_size": "count"})
            .rename(columns={"bet_size": "length"})
        )

        fig, ax = plt.subplots(figsize=(14, 6))

        win_streaks = streaks[streaks["is_win"] == 1]["length"]
        loss_streaks = streaks[streaks["is_win"] == 0]["length"]

        ax.bar(
            range(len(win_streaks)),
            win_streaks,
            color="green",
            alpha=0.7,
            label="Win Streaks",
        )
        ax.bar(
            range(len(win_streaks), len(win_streaks) + len(loss_streaks)),
            loss_streaks,
            color="red",
            alpha=0.7,
            label="Loss Streaks",
        )

        ax.set_xlabel("Streak Number", fontsize=12)
        ax.set_ylabel("Streak Length (bets)", fontsize=12)
        ax.set_title("Win/Loss Streaks Timeline", fontsize=14, fontweight="bold")
        ax.legend()
        ax.grid(alpha=0.3, axis="y")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "win_loss_streaks.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ Win/loss streaks saved")

    def plot_confidence_calibration(self):
        """8. Confidence Calibration - Predicted vs actual"""
        logger.info("Creating confidence calibration...")

        if self.bets_df is None or len(self.bets_df) == 0:
            logger.warning("No bet data for confidence calibration")
            return

        # Bin predictions and calculate actual win rates
        bins = np.linspace(0.5, 1.0, 11)
        self.bets_df["pred_bin"] = pd.cut(self.bets_df["pred_prob"], bins=bins)

        calibration = (
            self.bets_df.groupby("pred_bin")
            .agg({"pred_prob": "mean", "result": lambda x: (x == "win").mean()})
            .dropna()
        )

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.scatter(
            calibration["pred_prob"],
            calibration["result"],
            s=100,
            alpha=0.7,
            color="#2E86AB",
        )

        # Perfect calibration line
        ax.plot([0.5, 1.0], [0.5, 1.0], "r--", label="Perfect Calibration", linewidth=2)

        ax.set_xlabel("Predicted Probability", fontsize=12)
        ax.set_ylabel("Actual Win Rate", fontsize=12)
        ax.set_title("Confidence Calibration", fontsize=14, fontweight="bold")
        ax.legend()
        ax.grid(alpha=0.3)
        ax.set_xlim(0.5, 1.0)
        ax.set_ylim(0.5, 1.0)

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "confidence_calibration.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ Confidence calibration saved")

    def plot_clv_distribution(self):
        """9. CLV Distribution - Histogram"""
        logger.info("Creating CLV distribution...")

        if self.bets_df is None or len(self.bets_df) == 0:
            logger.warning("No bet data for CLV distribution")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(
            self.bets_df["clv"] * 100,
            bins=50,
            color="#2E86AB",
            alpha=0.7,
            edgecolor="black",
        )
        ax.axvline(0, color="r", linestyle="--", linewidth=2, label="Zero CLV")
        ax.axvline(
            self.bets_df["clv"].mean() * 100,
            color="g",
            linestyle="--",
            label=f'Mean: {self.bets_df["clv"].mean()*100:.2f}%',
        )
        ax.set_xlabel("CLV (%)", fontsize=12)
        ax.set_ylabel("Frequency", fontsize=12)
        ax.set_title(
            "Closing Line Value (CLV) Distribution", fontsize=14, fontweight="bold"
        )
        ax.legend()
        ax.grid(alpha=0.3, axis="y")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "clv_distribution.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ CLV distribution saved")

    def plot_risk_return_scatter(self):
        """10. Risk-Return Scatter - Different strategies"""
        logger.info("Creating risk-return scatter...")

        if self.results_df is None or len(self.results_df) == 0:
            logger.warning("No results data for risk-return scatter")
            return

        relevant = self.results_df[
            (self.results_df["total_bets"] > 10)
            & (self.results_df["roi"].notna())
            & (self.results_df["max_drawdown"].notna())
        ].copy()

        if len(relevant) == 0:
            logger.warning("No valid data for risk-return scatter")
            return

        fig, ax = plt.subplots(figsize=(12, 8))

        scatter = ax.scatter(
            relevant["max_drawdown"],
            relevant["roi"],
            s=relevant["total_bets"] * 2,
            alpha=0.6,
            c=relevant["sharpe_ratio"],
            cmap="viridis",
        )

        ax.set_xlabel("Max Drawdown (%)", fontsize=12)
        ax.set_ylabel("ROI (%)", fontsize=12)
        ax.set_title(
            "Risk-Return Scatter (Size = # Bets, Color = Sharpe)",
            fontsize=14,
            fontweight="bold",
        )
        ax.axhline(y=0, color="black", linestyle="-", alpha=0.3)
        ax.axvline(x=0, color="black", linestyle="-", alpha=0.3)
        ax.grid(alpha=0.3)

        plt.colorbar(scatter, label="Sharpe Ratio")

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "risk_return_scatter.png", bbox_inches="tight")
        plt.close()
        logger.info("✓ Risk-return scatter saved")

    def generate_all_visualizations(self):
        """Generate all visualizations."""
        logger.info("=" * 80)
        logger.info("GENERATING ALL BULLDOG MODE VISUALIZATIONS")
        logger.info("=" * 80)

        self.plot_equity_curve()
        self.plot_win_rate_by_month()
        self.plot_roi_by_segment()
        self.plot_feature_importance()
        self.plot_drawdown_analysis()
        self.plot_bet_size_distribution()
        self.plot_win_loss_streaks()
        self.plot_confidence_calibration()
        self.plot_clv_distribution()
        self.plot_risk_return_scatter()

        logger.info("\n" + "=" * 80)
        logger.info("ALL VISUALIZATIONS COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Visualizations saved to: {OUTPUT_DIR}")


def main():
    """Main execution."""
    viz = BulldogVisualizations()
    viz.generate_all_visualizations()


if __name__ == "__main__":
    main()
