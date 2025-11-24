"""
Performance Tracking System
Track all bets, results, and calculate real-time performance metrics
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, List
import os


class PerformanceTracker:
    """
    Track betting performance and generate reports.
    
    Metrics:
    - Win rate
    - ROI (Return on Investment)
    - Profit/Loss
    - Kelly accuracy
    - Tier performance
    - Book performance
    - Weather edge validation
    """
    
    def __init__(self, tracking_file: str = 'reports/performance_tracking.csv'):
        """Initialize performance tracker."""
        self.tracking_file = tracking_file
        
        # Create directory if needed
        os.makedirs(os.path.dirname(tracking_file), exist_ok=True)
        
        # Load existing data or create new
        if os.path.exists(tracking_file):
            self.df = pd.read_csv(tracking_file)
        else:
            self.df = pd.DataFrame(columns=[
                'date', 'game', 'pick', 'bet_type', 'line', 'book',
                'bet_size', 'bet_size_pct', 'tier', 'win_prob', 'edge',
                'confidence', 'kelly_fraction', 'weather_impact',
                'result', 'actual_win', 'profit_loss', 'roi'
            ])
    
    def add_bet(self, bet: Dict):
        """
        Add a new bet to tracking.
        
        Args:
            bet: Bet details dict from daily picks
        """
        new_row = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'game': bet['game'],
            'pick': bet['pick'],
            'bet_type': bet['bet_type'],
            'line': bet['line'],
            'book': bet['best_book'],
            'bet_size': float(bet['bet_size'].replace('$', '')),
            'bet_size_pct': float(bet['bet_size_pct'].replace('%', '')),
            'tier': bet['tier'],
            'win_prob': bet['win_probability'],
            'edge': bet['edge'],
            'confidence': bet['confidence'],
            'kelly_fraction': bet['kelly_fraction'],
            'weather_impact': bet.get('weather_impact', 'N/A'),
            'result': 'PENDING',
            'actual_win': None,
            'profit_loss': None,
            'roi': None
        }
        
        # Use concat instead of deprecated append
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.save()
    
    def update_result(self, game: str, won: bool):
        """
        Update bet result after game completes.
        
        Args:
            game: Game description (e.g., "Bills @ Chiefs")
            won: True if bet won, False if lost
        """
        mask = (self.df['game'] == game) & (self.df['result'] == 'PENDING')
        
        if not mask.any():
            print(f"No pending bets found for: {game}")
            return
        
        # Calculate profit/loss
        for idx in self.df[mask].index:
            bet_size = self.df.loc[idx, 'bet_size']
            line = self.df.loc[idx, 'line']
            
            if won:
                # Calculate payout based on American odds
                if line > 0:
                    profit = bet_size * (line / 100)
                else:
                    profit = bet_size * (100 / abs(line))
            else:
                profit = -bet_size
            
            roi = (profit / bet_size) * 100
            
            self.df.loc[idx, 'result'] = 'WON' if won else 'LOST'
            self.df.loc[idx, 'actual_win'] = won
            self.df.loc[idx, 'profit_loss'] = profit
            self.df.loc[idx, 'roi'] = roi
        
        self.save()
        print(f"Updated: {game} - {'WON' if won else 'LOST'}")
    
    def save(self):
        """Save tracking data to CSV."""
        self.df.to_csv(self.tracking_file, index=False)
    
    def get_overall_stats(self) -> Dict:
        """Calculate overall performance statistics."""
        completed = self.df[self.df['result'] != 'PENDING']
        
        if len(completed) == 0:
            return {'error': 'No completed bets yet'}
        
        stats = {
            'total_bets': len(completed),
            'wins': len(completed[completed['actual_win'] == True]),
            'losses': len(completed[completed['actual_win'] == False]),
            'win_rate': (completed['actual_win'].sum() / len(completed)) * 100,
            'total_wagered': completed['bet_size'].sum(),
            'total_profit': completed['profit_loss'].sum(),
            'roi': (completed['profit_loss'].sum() / completed['bet_size'].sum()) * 100,
            'avg_bet_size': completed['bet_size'].mean(),
            'largest_win': completed['profit_loss'].max(),
            'largest_loss': completed['profit_loss'].min(),
        }
        
        return stats
    
    def get_tier_performance(self) -> pd.DataFrame:
        """Analyze performance by bet tier."""
        completed = self.df[self.df['result'] != 'PENDING']
        
        if len(completed) == 0:
            return pd.DataFrame()
        
        tier_stats = completed.groupby('tier').agg({
            'actual_win': ['count', 'sum', 'mean'],
            'profit_loss': 'sum',
            'bet_size': 'sum'
        }).reset_index()
        
        tier_stats.columns = ['tier', 'bets', 'wins', 'win_rate', 'profit', 'wagered']
        tier_stats['roi'] = (tier_stats['profit'] / tier_stats['wagered']) * 100
        tier_stats['win_rate'] = tier_stats['win_rate'] * 100
        
        return tier_stats.sort_values('tier')
    
    def get_book_performance(self) -> pd.DataFrame:
        """Analyze performance by sportsbook."""
        completed = self.df[self.df['result'] != 'PENDING']
        
        if len(completed) == 0:
            return pd.DataFrame()
        
        book_stats = completed.groupby('book').agg({
            'actual_win': ['count', 'sum', 'mean'],
            'profit_loss': 'sum',
            'bet_size': 'sum'
        }).reset_index()
        
        book_stats.columns = ['book', 'bets', 'wins', 'win_rate', 'profit', 'wagered']
        book_stats['roi'] = (book_stats['profit'] / book_stats['wagered']) * 100
        book_stats['win_rate'] = book_stats['win_rate'] * 100
        
        return book_stats.sort_values('roi', ascending=False)
    
    def get_recent_form(self, last_n: int = 10) -> Dict:
        """Get recent betting form (last N bets)."""
        completed = self.df[self.df['result'] != 'PENDING'].tail(last_n)
        
        if len(completed) == 0:
            return {'error': f'No completed bets in last {last_n}'}
        
        return {
            'last_n': len(completed),
            'wins': completed['actual_win'].sum(),
            'win_rate': (completed['actual_win'].sum() / len(completed)) * 100,
            'profit': completed['profit_loss'].sum(),
            'roi': (completed['profit_loss'].sum() / completed['bet_size'].sum()) * 100
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive performance report."""
        report = []
        report.append("="*80)
        report.append("BETTING PERFORMANCE REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)
        
        # Overall stats
        overall = self.get_overall_stats()
        
        if 'error' in overall:
            report.append(f"\n{overall['error']}")
            return "\n".join(report)
        
        report.append("\nOVERALL PERFORMANCE")
        report.append("-"*80)
        report.append(f"Total Bets:      {overall['total_bets']}")
        report.append(f"Record:          {overall['wins']}-{overall['losses']}")
        report.append(f"Win Rate:        {overall['win_rate']:.2f}%")
        report.append(f"Total Wagered:   ${overall['total_wagered']:,.0f}")
        report.append(f"Total Profit:    ${overall['total_profit']:+,.0f}")
        report.append(f"ROI:             {overall['roi']:+.2f}%")
        report.append(f"Avg Bet Size:    ${overall['avg_bet_size']:,.0f}")
        report.append(f"Largest Win:     ${overall['largest_win']:+,.0f}")
        report.append(f"Largest Loss:    ${overall['largest_loss']:+,.0f}")
        
        # Recent form
        recent = self.get_recent_form(10)
        if 'error' not in recent:
            report.append("\nRECENT FORM (Last 10 Bets)")
            report.append("-"*80)
            report.append(f"Record:          {recent['wins']}-{recent['last_n']-recent['wins']}")
            report.append(f"Win Rate:        {recent['win_rate']:.2f}%")
            report.append(f"Profit:          ${recent['profit']:+,.0f}")
            report.append(f"ROI:             {recent['roi']:+.2f}%")
        
        # Tier performance
        tier_perf = self.get_tier_performance()
        if not tier_perf.empty:
            report.append("\nPERFORMANCE BY TIER")
            report.append("-"*80)
            report.append(f"{'Tier':<6} {'Bets':<6} {'Wins':<6} {'Win%':<8} {'Profit':<12} {'ROI%':<8}")
            report.append("-"*80)
            
            for _, row in tier_perf.iterrows():
                report.append(
                    f"{row['tier']:<6} "
                    f"{row['bets']:<6.0f} "
                    f"{row['wins']:<6.0f} "
                    f"{row['win_rate']:<8.1f} "
                    f"${row['profit']:>10,.0f} "
                    f"{row['roi']:>7.2f}%"
                )
        
        # Book performance
        book_perf = self.get_book_performance()
        if not book_perf.empty:
            report.append("\nPERFORMANCE BY SPORTSBOOK")
            report.append("-"*80)
            report.append(f"{'Book':<20} {'Bets':<6} {'Win%':<8} {'ROI%':<8}")
            report.append("-"*80)
            
            for _, row in book_perf.head(10).iterrows():
                report.append(
                    f"{row['book']:<20} "
                    f"{row['bets']:<6.0f} "
                    f"{row['win_rate']:<8.1f} "
                    f"{row['roi']:>7.2f}%"
                )
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)
    
    def export_to_excel(self, filename: str = 'reports/betting_performance.xlsx'):
        """Export performance data to Excel for deeper analysis."""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # All bets
            self.df.to_excel(writer, sheet_name='All Bets', index=False)
            
            # Summary stats
            overall = self.get_overall_stats()
            if 'error' not in overall:
                summary_df = pd.DataFrame([overall])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Tier performance
            tier_perf = self.get_tier_performance()
            if not tier_perf.empty:
                tier_perf.to_excel(writer, sheet_name='By Tier', index=False)
            
            # Book performance
            book_perf = self.get_book_performance()
            if not book_perf.empty:
                book_perf.to_excel(writer, sheet_name='By Book', index=False)
        
        print(f"Exported to: {filename}")


def main():
    """Demo performance tracking."""
    tracker = PerformanceTracker()
    
    # Example: Load picks from today and add to tracking
    import glob
    pick_files = sorted(glob.glob('reports/daily_picks_*.json'))
    
    if pick_files:
        with open(pick_files[-1]) as f:
            picks_data = json.load(f)
        
        print(f"Loading {len(picks_data['picks'])} picks...")
        for pick in picks_data['picks']:
            tracker.add_bet(pick)
        
        print(f"Added {len(picks_data['picks'])} picks to tracking")
    
    # Generate report
    print("\n" + tracker.generate_report())
    
    # Export to Excel
    tracker.export_to_excel()


if __name__ == '__main__':
    main()

