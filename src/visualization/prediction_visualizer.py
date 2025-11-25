"""
Prediction Visualizer - ESPN-Style Charts and Graphics

Generates professional betting pick visualizations:
1. Matchup comparison charts
2. Edge/confidence gauges
3. Historical performance charts
4. Equity curves
5. Pick cards for social sharing
"""

import io
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

# NFL team colors
NFL_COLORS = {
    "Arizona Cardinals": {"primary": "#97233F", "secondary": "#000000"},
    "Atlanta Falcons": {"primary": "#A71930", "secondary": "#000000"},
    "Baltimore Ravens": {"primary": "#241773", "secondary": "#9E7C0C"},
    "Buffalo Bills": {"primary": "#00338D", "secondary": "#C60C30"},
    "Carolina Panthers": {"primary": "#0085CA", "secondary": "#101820"},
    "Chicago Bears": {"primary": "#0B162A", "secondary": "#C83803"},
    "Cincinnati Bengals": {"primary": "#FB4F14", "secondary": "#000000"},
    "Cleveland Browns": {"primary": "#311D00", "secondary": "#FF3C00"},
    "Dallas Cowboys": {"primary": "#003594", "secondary": "#869397"},
    "Denver Broncos": {"primary": "#FB4F14", "secondary": "#002244"},
    "Detroit Lions": {"primary": "#0076B6", "secondary": "#B0B7BC"},
    "Green Bay Packers": {"primary": "#203731", "secondary": "#FFB612"},
    "Houston Texans": {"primary": "#03202F", "secondary": "#A71930"},
    "Indianapolis Colts": {"primary": "#002C5F", "secondary": "#A2AAAD"},
    "Jacksonville Jaguars": {"primary": "#006778", "secondary": "#D7A22A"},
    "Kansas City Chiefs": {"primary": "#E31837", "secondary": "#FFB81C"},
    "Las Vegas Raiders": {"primary": "#000000", "secondary": "#A5ACAF"},
    "Los Angeles Chargers": {"primary": "#0080C6", "secondary": "#FFC20E"},
    "Los Angeles Rams": {"primary": "#003594", "secondary": "#FFA300"},
    "Miami Dolphins": {"primary": "#008E97", "secondary": "#FC4C02"},
    "Minnesota Vikings": {"primary": "#4F2683", "secondary": "#FFC62F"},
    "New England Patriots": {"primary": "#002244", "secondary": "#C60C30"},
    "New Orleans Saints": {"primary": "#D3BC8D", "secondary": "#101820"},
    "New York Giants": {"primary": "#0B2265", "secondary": "#A71930"},
    "New York Jets": {"primary": "#125740", "secondary": "#000000"},
    "Philadelphia Eagles": {"primary": "#004C54", "secondary": "#A5ACAF"},
    "Pittsburgh Steelers": {"primary": "#FFB612", "secondary": "#101820"},
    "San Francisco 49ers": {"primary": "#AA0000", "secondary": "#B3995D"},
    "Seattle Seahawks": {"primary": "#002244", "secondary": "#69BE28"},
    "Tampa Bay Buccaneers": {"primary": "#D50A0A", "secondary": "#FF7900"},
    "Tennessee Titans": {"primary": "#0C2340", "secondary": "#4B92DB"},
    "Washington Commanders": {"primary": "#5A1414", "secondary": "#FFB612"},
}


@dataclass
class PickVisualization:
    """Generated visualization for a pick."""
    pick_id: str
    figure: Figure
    image_bytes: bytes
    file_path: Optional[Path]
    metadata: Dict[str, Any]


class PredictionVisualizer:
    """
    Creates professional betting visualizations.
    
    Generates:
    - Matchup cards
    - Confidence gauges
    - Edge comparison charts
    - Historical trend lines
    - Social media-ready pick graphics
    """
    
    def __init__(self, output_dir: str = "reports/visuals"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Style settings
        plt.style.use('dark_background')
        self.font_family = 'sans-serif'
        self.accent_color = '#00D4AA'  # Cyan/teal accent
        self.background_color = '#0A0A0A'
        self.card_color = '#1A1A2E'
        
        logger.info("PredictionVisualizer initialized")
    
    def get_team_colors(self, team_name: str) -> Tuple[str, str]:
        """Get team colors, with fallback."""
        colors = NFL_COLORS.get(team_name, {"primary": "#333333", "secondary": "#666666"})
        return colors["primary"], colors["secondary"]
    
    def create_matchup_card(
        self,
        home_team: str,
        away_team: str,
        pick: str,
        confidence: float,
        edge: float,
        odds: float,
        tier: str,
        game_time: str,
        reasoning: List[str],
        save_path: Optional[str] = None
    ) -> PickVisualization:
        """
        Create a professional matchup card.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            pick: "home" or "away"
            confidence: 0-1 confidence score
            edge: Expected edge (e.g., 0.05 for 5%)
            odds: American odds
            tier: Betting tier ("S_tier", "A_tier", etc.)
            game_time: Game time string
            reasoning: List of reasons for the pick
        
        Returns:
            PickVisualization with the generated card
        """
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.background_color)
        ax.set_facecolor(self.card_color)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis('off')
        
        # Get team colors
        home_primary, home_secondary = self.get_team_colors(home_team)
        away_primary, away_secondary = self.get_team_colors(away_team)
        
        # Header bar
        header_rect = mpatches.FancyBboxPatch(
            (0, 5.2), 10, 0.8,
            boxstyle="round,pad=0.05",
            facecolor=self.accent_color,
            edgecolor='none'
        )
        ax.add_patch(header_rect)
        
        # Header text
        ax.text(0.3, 5.6, "NFL EDGE FINDER", fontsize=12, color='black', 
                fontweight='bold', family=self.font_family)
        ax.text(9.7, 5.6, tier.replace("_", " ").upper(), fontsize=12, color='black',
                fontweight='bold', ha='right', family=self.font_family)
        
        # Team blocks
        # Away team (left)
        away_rect = mpatches.FancyBboxPatch(
            (0.3, 3.2), 4.2, 1.8,
            boxstyle="round,pad=0.1",
            facecolor=away_primary,
            edgecolor=away_secondary,
            linewidth=3
        )
        ax.add_patch(away_rect)
        ax.text(2.4, 4.3, away_team.split()[-1].upper(), fontsize=16, color='white',
                fontweight='bold', ha='center', family=self.font_family)
        ax.text(2.4, 3.7, "AWAY", fontsize=10, color='white', alpha=0.7,
                ha='center', family=self.font_family)
        
        # VS text
        ax.text(5, 4.1, "@", fontsize=24, color='white', alpha=0.5,
                ha='center', family=self.font_family)
        
        # Home team (right)
        home_rect = mpatches.FancyBboxPatch(
            (5.5, 3.2), 4.2, 1.8,
            boxstyle="round,pad=0.1",
            facecolor=home_primary,
            edgecolor=home_secondary,
            linewidth=3
        )
        ax.add_patch(home_rect)
        ax.text(7.6, 4.3, home_team.split()[-1].upper(), fontsize=16, color='white',
                fontweight='bold', ha='center', family=self.font_family)
        ax.text(7.6, 3.7, "HOME", fontsize=10, color='white', alpha=0.7,
                ha='center', family=self.font_family)
        
        # Pick indicator (arrow or highlight)
        pick_team = home_team if pick == "home" else away_team
        pick_x = 7.6 if pick == "home" else 2.4
        ax.annotate('', xy=(pick_x, 3.0), xytext=(pick_x, 2.6),
                    arrowprops=dict(arrowstyle='->', color=self.accent_color, lw=3))
        ax.text(pick_x, 2.4, "OUR PICK", fontsize=10, color=self.accent_color,
                fontweight='bold', ha='center', family=self.font_family)
        
        # Metrics row
        metrics_y = 1.5
        
        # Confidence gauge
        self._draw_gauge(ax, 1.5, metrics_y, confidence, "CONFIDENCE", 1.0)
        
        # Edge indicator
        self._draw_metric_box(ax, 5.0, metrics_y, f"+{edge*100:.1f}%", "EDGE")
        
        # Odds
        odds_str = f"+{int(odds)}" if odds > 0 else str(int(odds))
        self._draw_metric_box(ax, 8.5, metrics_y, odds_str, "ODDS")
        
        # Reasoning footer
        if reasoning:
            reason_text = reasoning[0][:50] + "..." if len(reasoning[0]) > 50 else reasoning[0]
            ax.text(5, 0.4, reason_text, fontsize=9, color='white', alpha=0.7,
                    ha='center', family=self.font_family, style='italic')
        
        # Game time
        ax.text(5, 0.1, game_time, fontsize=8, color='white', alpha=0.5,
                ha='center', family=self.font_family)
        
        plt.tight_layout()
        
        # Save to bytes
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=self.background_color, edgecolor='none')
        buf.seek(0)
        image_bytes = buf.getvalue()
        
        # Save to file if requested
        file_path = None
        if save_path:
            file_path = Path(save_path)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.output_dir / f"pick_{away_team}_{home_team}_{timestamp}.png"
        
        fig.savefig(file_path, dpi=150, bbox_inches='tight',
                    facecolor=self.background_color, edgecolor='none')
        
        plt.close(fig)
        
        return PickVisualization(
            pick_id=f"{away_team}_{home_team}_{datetime.now().strftime('%Y%m%d')}",
            figure=fig,
            image_bytes=image_bytes,
            file_path=file_path,
            metadata={
                "home_team": home_team,
                "away_team": away_team,
                "pick": pick,
                "confidence": confidence,
                "edge": edge,
                "tier": tier
            }
        )
    
    def _draw_gauge(self, ax, x: float, y: float, value: float, label: str, max_val: float):
        """Draw a confidence gauge."""
        # Background arc
        theta1, theta2 = 180, 0
        arc_bg = mpatches.Arc((x, y), 1.5, 1.5, angle=0, theta1=theta1, theta2=theta2,
                              color='#333333', linewidth=10)
        ax.add_patch(arc_bg)
        
        # Value arc
        fill_angle = 180 - (value / max_val * 180)
        arc_fg = mpatches.Arc((x, y), 1.5, 1.5, angle=0, theta1=fill_angle, theta2=theta2,
                              color=self.accent_color, linewidth=10)
        ax.add_patch(arc_fg)
        
        # Value text
        ax.text(x, y - 0.1, f"{value*100:.0f}%", fontsize=14, color='white',
                fontweight='bold', ha='center', family=self.font_family)
        
        # Label
        ax.text(x, y - 0.5, label, fontsize=8, color='white', alpha=0.7,
                ha='center', family=self.font_family)
    
    def _draw_metric_box(self, ax, x: float, y: float, value: str, label: str):
        """Draw a metric box."""
        box = mpatches.FancyBboxPatch(
            (x - 0.7, y - 0.4), 1.4, 0.8,
            boxstyle="round,pad=0.05",
            facecolor='#222233',
            edgecolor=self.accent_color,
            linewidth=1
        )
        ax.add_patch(box)
        
        ax.text(x, y + 0.1, value, fontsize=14, color=self.accent_color,
                fontweight='bold', ha='center', family=self.font_family)
        ax.text(x, y - 0.25, label, fontsize=8, color='white', alpha=0.7,
                ha='center', family=self.font_family)
    
    def create_equity_curve(
        self,
        bankroll_history: List[float],
        dates: List[datetime],
        title: str = "Bankroll Performance",
        save_path: Optional[str] = None
    ) -> PickVisualization:
        """
        Create an equity curve chart.
        
        Args:
            bankroll_history: List of bankroll values
            dates: Corresponding dates
            title: Chart title
        
        Returns:
            PickVisualization with the chart
        """
        fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.background_color)
        ax.set_facecolor(self.card_color)
        
        # Plot equity curve
        ax.plot(dates, bankroll_history, color=self.accent_color, linewidth=2, label='Bankroll')
        
        # Fill under curve
        ax.fill_between(dates, bankroll_history, bankroll_history[0],
                        alpha=0.3, color=self.accent_color)
        
        # Add starting line
        ax.axhline(y=bankroll_history[0], color='white', linestyle='--', alpha=0.3, label='Starting')
        
        # Calculate metrics
        roi = (bankroll_history[-1] - bankroll_history[0]) / bankroll_history[0] * 100
        max_val = max(bankroll_history)
        min_val = min(bankroll_history)
        max_dd = (max_val - min_val) / max_val * 100
        
        # Title with metrics
        ax.set_title(f"{title}\nROI: {roi:+.1f}% | Max Drawdown: {max_dd:.1f}%",
                     color='white', fontsize=14, fontweight='bold', pad=20)
        
        # Styling
        ax.set_xlabel('Date', color='white', fontsize=10)
        ax.set_ylabel('Bankroll ($)', color='white', fontsize=10)
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#333333')
        ax.spines['left'].set_color('#333333')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2)
        
        plt.tight_layout()
        
        # Save
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=self.background_color)
        buf.seek(0)
        image_bytes = buf.getvalue()
        
        file_path = None
        if save_path:
            file_path = Path(save_path)
        else:
            file_path = self.output_dir / f"equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        fig.savefig(file_path, dpi=150, bbox_inches='tight', facecolor=self.background_color)
        plt.close(fig)
        
        return PickVisualization(
            pick_id=f"equity_{datetime.now().strftime('%Y%m%d')}",
            figure=fig,
            image_bytes=image_bytes,
            file_path=file_path,
            metadata={"roi": roi, "max_drawdown": max_dd}
        )
    
    def create_daily_picks_summary(
        self,
        picks: List[Dict[str, Any]],
        date: str,
        save_path: Optional[str] = None
    ) -> PickVisualization:
        """
        Create a summary graphic for all daily picks.
        
        Args:
            picks: List of pick dictionaries
            date: Date string
        
        Returns:
            PickVisualization with the summary
        """
        n_picks = len(picks)
        if n_picks == 0:
            # No picks graphic
            fig, ax = plt.subplots(figsize=(10, 4), facecolor=self.background_color)
            ax.set_facecolor(self.card_color)
            ax.axis('off')
            ax.text(0.5, 0.5, "NO PICKS TODAY", transform=ax.transAxes,
                    fontsize=24, color='white', alpha=0.5, ha='center', va='center')
        else:
            # Calculate rows needed
            cols = 3
            rows = (n_picks + cols - 1) // cols
            fig_height = 2 + rows * 1.5
            
            fig, ax = plt.subplots(figsize=(12, fig_height), facecolor=self.background_color)
            ax.set_facecolor(self.card_color)
            ax.set_xlim(0, 12)
            ax.set_ylim(0, fig_height)
            ax.axis('off')
            
            # Header
            ax.text(6, fig_height - 0.5, f"NFL PICKS - {date}", fontsize=16, color='white',
                    fontweight='bold', ha='center', family=self.font_family)
            ax.text(6, fig_height - 0.9, f"{n_picks} RECOMMENDED BETS", fontsize=10,
                    color=self.accent_color, ha='center', family=self.font_family)
            
            # Draw each pick
            for i, pick in enumerate(picks):
                col = i % cols
                row = i // cols
                
                x = 0.5 + col * 4
                y = fig_height - 2 - row * 1.5
                
                # Pick box
                tier_color = {
                    "S_tier": "#FFD700",
                    "A_tier": "#00FF00",
                    "B_tier": "#00BFFF"
                }.get(pick.get("tier", "B_tier"), self.accent_color)
                
                box = mpatches.FancyBboxPatch(
                    (x, y - 0.5), 3.5, 1.2,
                    boxstyle="round,pad=0.1",
                    facecolor='#1a1a2e',
                    edgecolor=tier_color,
                    linewidth=2
                )
                ax.add_patch(box)
                
                # Team matchup
                game = pick.get("game", "TBD @ TBD")
                ax.text(x + 0.1, y + 0.4, game[:20], fontsize=9, color='white',
                        fontweight='bold', family=self.font_family)
                
                # Pick and odds
                pick_text = f"{pick.get('pick', 'TBD')} ({pick.get('odds', 'N/A')})"
                ax.text(x + 0.1, y + 0.1, pick_text, fontsize=8, color=tier_color,
                        family=self.font_family)
                
                # Confidence
                conf = pick.get("confidence", 0)
                ax.text(x + 3.3, y + 0.2, f"{conf*100:.0f}%", fontsize=10,
                        color=tier_color, fontweight='bold', ha='right',
                        family=self.font_family)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=self.background_color)
        buf.seek(0)
        image_bytes = buf.getvalue()
        
        file_path = Path(save_path) if save_path else \
            self.output_dir / f"daily_summary_{datetime.now().strftime('%Y%m%d')}.png"
        
        fig.savefig(file_path, dpi=150, bbox_inches='tight', facecolor=self.background_color)
        plt.close(fig)
        
        return PickVisualization(
            pick_id=f"summary_{date}",
            figure=fig,
            image_bytes=image_bytes,
            file_path=file_path,
            metadata={"date": date, "picks_count": n_picks}
        )
    
    def create_performance_dashboard(
        self,
        metrics: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> PickVisualization:
        """
        Create a comprehensive performance dashboard.
        
        Args:
            metrics: Dict with performance metrics
        
        Returns:
            PickVisualization with the dashboard
        """
        fig = plt.figure(figsize=(14, 8), facecolor=self.background_color)
        
        # Create grid
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        # Main metrics cards (top row)
        metrics_data = [
            ("WIN RATE", f"{metrics.get('win_rate', 0)*100:.1f}%", metrics.get('win_rate', 0) > 0.55),
            ("ROI", f"{metrics.get('roi', 0)*100:.1f}%", metrics.get('roi', 0) > 0.05),
            ("TOTAL BETS", str(metrics.get('total_bets', 0)), True),
            ("PROFIT", f"${metrics.get('total_profit', 0):.0f}", metrics.get('total_profit', 0) > 0),
        ]
        
        for i, (label, value, is_good) in enumerate(metrics_data):
            ax = fig.add_subplot(gs[0, i])
            ax.set_facecolor(self.card_color)
            ax.axis('off')
            
            color = '#00FF00' if is_good else '#FF4444'
            ax.text(0.5, 0.7, value, transform=ax.transAxes, fontsize=24,
                    color=color, fontweight='bold', ha='center')
            ax.text(0.5, 0.3, label, transform=ax.transAxes, fontsize=10,
                    color='white', alpha=0.7, ha='center')
        
        # Record breakdown (middle left)
        ax_record = fig.add_subplot(gs[1, :2])
        ax_record.set_facecolor(self.card_color)
        
        wins = metrics.get('wins', 0)
        losses = metrics.get('losses', 0)
        pushes = metrics.get('pushes', 0)
        
        bars = ax_record.bar(['Wins', 'Losses', 'Pushes'], [wins, losses, pushes],
                             color=['#00FF00', '#FF4444', '#888888'])
        ax_record.set_title('RECORD', color='white', fontsize=12)
        ax_record.tick_params(colors='white')
        ax_record.spines['bottom'].set_color('#333333')
        ax_record.spines['left'].set_color('#333333')
        ax_record.spines['top'].set_visible(False)
        ax_record.spines['right'].set_visible(False)
        
        # Tier breakdown (middle right)
        ax_tier = fig.add_subplot(gs[1, 2:])
        ax_tier.set_facecolor(self.card_color)
        
        tier_data = metrics.get('tier_breakdown', {})
        if tier_data:
            tiers = list(tier_data.keys())
            values = list(tier_data.values())
            colors = ['#FFD700', '#00FF00', '#00BFFF', '#888888'][:len(tiers)]
            ax_tier.pie(values, labels=tiers, colors=colors, autopct='%1.0f%%',
                       textprops={'color': 'white'})
        ax_tier.set_title('BY TIER', color='white', fontsize=12)
        
        # Recent performance (bottom)
        ax_recent = fig.add_subplot(gs[2, :])
        ax_recent.set_facecolor(self.card_color)
        
        recent = metrics.get('recent_results', [])
        if recent:
            x = range(len(recent))
            colors = ['#00FF00' if r == 'W' else '#FF4444' if r == 'L' else '#888888' for r in recent]
            ax_recent.bar(x, [1]*len(recent), color=colors, edgecolor='none')
            ax_recent.set_ylim(0, 1.5)
            ax_recent.set_xlim(-0.5, len(recent) - 0.5)
            ax_recent.axis('off')
        ax_recent.set_title('LAST 20 RESULTS', color='white', fontsize=12, pad=20)
        
        plt.suptitle('PERFORMANCE DASHBOARD', color='white', fontsize=16, fontweight='bold')
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=self.background_color)
        buf.seek(0)
        image_bytes = buf.getvalue()
        
        file_path = Path(save_path) if save_path else \
            self.output_dir / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        fig.savefig(file_path, dpi=150, bbox_inches='tight', facecolor=self.background_color)
        plt.close(fig)
        
        return PickVisualization(
            pick_id=f"dashboard_{datetime.now().strftime('%Y%m%d')}",
            figure=fig,
            image_bytes=image_bytes,
            file_path=file_path,
            metadata=metrics
        )


# Singleton instance
_visualizer: Optional[PredictionVisualizer] = None


def get_visualizer() -> PredictionVisualizer:
    """Get or create singleton PredictionVisualizer instance."""
    global _visualizer
    if _visualizer is None:
        _visualizer = PredictionVisualizer()
    return _visualizer


if __name__ == "__main__":
    # Test visualizations
    viz = get_visualizer()
    
    # Test matchup card
    print("Creating matchup card...")
    card = viz.create_matchup_card(
        home_team="Buffalo Bills",
        away_team="Kansas City Chiefs",
        pick="home",
        confidence=0.72,
        edge=0.08,
        odds=-145,
        tier="A_tier",
        game_time="Sun Nov 24, 4:25 PM ET",
        reasoning=["Bills 5-0 at home", "Chiefs 3-2 on road"]
    )
    print(f"Saved to: {card.file_path}")
    
    # Test equity curve
    print("Creating equity curve...")
    import random
    bankroll = [10000]
    for _ in range(50):
        change = random.uniform(-200, 300)
        bankroll.append(bankroll[-1] + change)
    
    dates = [datetime(2024, 9, 1) + timedelta(days=i) for i in range(51)]
    
    curve = viz.create_equity_curve(bankroll, dates, "2024 Season Performance")
    print(f"Saved to: {curve.file_path}")
    
    # Test daily summary
    print("Creating daily summary...")
    picks = [
        {"game": "KC @ BUF", "pick": "Bills", "odds": -145, "confidence": 0.72, "tier": "A_tier"},
        {"game": "SF @ GB", "pick": "49ers", "odds": -130, "confidence": 0.68, "tier": "A_tier"},
        {"game": "DAL @ NYG", "pick": "Cowboys", "odds": -180, "confidence": 0.75, "tier": "S_tier"},
    ]
    summary = viz.create_daily_picks_summary(picks, "Week 12 - Nov 24, 2024")
    print(f"Saved to: {summary.file_path}")
    
    # Test dashboard
    print("Creating performance dashboard...")
    metrics = {
        "win_rate": 0.68,
        "roi": 0.12,
        "total_bets": 52,
        "total_profit": 1200,
        "wins": 35,
        "losses": 16,
        "pushes": 1,
        "tier_breakdown": {"S_tier": 10, "A_tier": 25, "B_tier": 17},
        "recent_results": ['W', 'W', 'L', 'W', 'W', 'W', 'L', 'W', 'W', 'L',
                          'W', 'W', 'W', 'L', 'W', 'W', 'W', 'W', 'L', 'W']
    }
    dashboard = viz.create_performance_dashboard(metrics)
    print(f"Saved to: {dashboard.file_path}")
    
    print("\nAll visualizations created successfully!")

