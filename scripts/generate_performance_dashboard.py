#!/usr/bin/env python3
"""Generate performance dashboard with visualizations."""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_dashboard():
    """Generate comprehensive performance dashboard."""
    logger.info("Generating performance dashboard...")
    
    # Load bet history
    bet_history_path = Path("reports/bet_history.csv")
    if not bet_history_path.exists():
        logger.error("No bet history found. Run backtest first.")
        return
    
    df = pd.read_csv(bet_history_path)
    
    # Ensure result is numeric (1 for win, 0 for loss)
    if 'result' in df.columns:
        if df['result'].dtype == 'object':
            df['result'] = (df['result'] == 'win').astype(int)
        else:
            df['result'] = df['result'].astype(int)
    
    # Create dashboard
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Equity Curve
    ax1 = fig.add_subplot(gs[0, :])
    df['cumulative_profit'] = df['profit'].cumsum()
    df['bankroll'] = df['cumulative_profit'] + 10000  # Starting bankroll
    ax1.plot(df.index, df['bankroll'], linewidth=2, label='Bankroll')
    ax1.axhline(y=10000, color='r', linestyle='--', alpha=0.7, label='Starting Bankroll')
    ax1.set_xlabel('Bet Number')
    ax1.set_ylabel('Bankroll ($)')
    ax1.set_title('Equity Curve')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 2. Win Rate by Tier
    ax2 = fig.add_subplot(gs[1, 0])
    if 'tier' in df.columns:
        tier_stats = df.groupby('tier').agg({
            'result': ['count', 'sum']
        }).reset_index()
        tier_stats['win_rate'] = tier_stats[('result', 'sum')] / tier_stats[('result', 'count')] * 100
        ax2.bar(tier_stats['tier'], tier_stats['win_rate'], color=['gold', 'green', 'blue', 'gray'])
        ax2.set_ylabel('Win Rate (%)')
        ax2.set_title('Win Rate by Tier')
        ax2.set_ylim(0, 100)
    
    # 3. ROI by Sportsbook (if available)
    ax3 = fig.add_subplot(gs[1, 1])
    if 'sportsbook' in df.columns:
        book_stats = df.groupby('sportsbook').agg({
            'profit': 'sum',
            'bet_size': 'sum'
        }).reset_index()
        book_stats['roi'] = (book_stats['profit'] / book_stats['bet_size']) * 100
        book_stats = book_stats.sort_values('roi', ascending=False).head(10)
        ax3.barh(book_stats['sportsbook'], book_stats['roi'])
        ax3.set_xlabel('ROI (%)')
        ax3.set_title('ROI by Sportsbook (Top 10)')
    else:
        ax3.text(0.5, 0.5, 'Sportsbook data\nnot available', 
                ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('ROI by Sportsbook')
    
    # 4. Recent Form (Last 10 Bets)
    ax4 = fig.add_subplot(gs[1, 2])
    recent = df.tail(10)
    ax4.plot(range(len(recent)), recent['result'].cumsum(), marker='o', linewidth=2)
    ax4.axhline(y=5, color='r', linestyle='--', alpha=0.7, label='Break Even')
    ax4.set_xlabel('Last 10 Bets')
    ax4.set_ylabel('Cumulative Wins')
    ax4.set_title('Recent Form')
    ax4.legend()
    ax4.grid(alpha=0.3)
    
    # 5. Profit Distribution
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.hist(df['profit'], bins=30, edgecolor='black', alpha=0.7)
    ax5.axvline(x=0, color='r', linestyle='--', linewidth=2)
    ax5.set_xlabel('Profit per Bet ($)')
    ax5.set_ylabel('Frequency')
    ax5.set_title('Profit Distribution')
    
    # 6. Win Rate Over Time
    ax6 = fig.add_subplot(gs[2, 1])
    df['rolling_win_rate'] = df['result'].rolling(window=20).mean() * 100
    ax6.plot(df.index, df['rolling_win_rate'], linewidth=2)
    ax6.axhline(y=55, color='g', linestyle='--', alpha=0.7, label='Target (55%)')
    ax6.set_xlabel('Bet Number')
    ax6.set_ylabel('Rolling Win Rate (%)')
    ax6.set_title('20-Bet Rolling Win Rate')
    ax6.legend()
    ax6.grid(alpha=0.3)
    
    # 7. Summary Stats
    ax7 = fig.add_subplot(gs[2, 2])
    ax7.axis('off')
    
    total_bets = len(df)
    wins = df['result'].sum()
    win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0
    total_profit = df['profit'].sum()
    bet_size_col = 'bet_size' if 'bet_size' in df.columns else 'bet_amount'
    roi = (total_profit / df[bet_size_col].sum()) * 100 if df[bet_size_col].sum() > 0 else 0
    
    stats_text = f"""
    PERFORMANCE SUMMARY
    
    Total Bets: {total_bets:,}
    Wins: {wins}
    Win Rate: {win_rate:.2f}%
    
    Total Profit: ${total_profit:,.2f}
    ROI: {roi:.2f}%
    
    Avg Bet: ${df[bet_size_col].mean():.2f}
    Max Win: ${df['profit'].max():.2f}
    Max Loss: ${df['profit'].min():.2f}
    
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    ax7.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Save dashboard
    output_path = Path("reports/img/performance_dashboard.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"Dashboard saved to: {output_path}")
    
    plt.close()


if __name__ == "__main__":
    generate_dashboard()

