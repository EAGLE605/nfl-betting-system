"""
Aggressive Kelly Criterion Calculator

PHILOSOPHY: Push when confident, pull back when uncertain!
"""

import numpy as np
import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class AggressiveKellyCalculator:
    """
    Dynamic bet sizing based on confidence, edge, and performance.
    
    PUSH THROTTLE when:
    - High model confidence (>70%)
    - Proven situational edge (>5%)
    - Recent hot streak (>58% last 20 bets)
    - Multiple confirming factors
    
    PULL BACK when:
    - Low confidence (<62%)
    - Recent struggles (<52%)
    - High drawdown (>20%)
    """
    
    def __init__(self, bankroll: float, max_bet_pct: float = 0.10):
        self.bankroll = bankroll
        self.max_bet_pct = max_bet_pct  # Never bet more than 10% on single game
        self.recent_bets = []
    
    def calculate_bet_size(self,
                          edge: float,
                          confidence: float,
                          situational_edge: float = 0.0,
                          weather_confidence: str = 'MEDIUM',
                          recent_performance: Dict = None) -> Dict:
        """
        Calculate aggressive bet size.
        
        Args:
            edge: Model edge (prob - implied_prob)
            confidence: Model confidence (0-1)
            situational_edge: Historical edge for this situation (0-1)
            weather_confidence: NOAA confidence (LOW/MEDIUM/HIGH/VERY HIGH)
            recent_performance: Recent win rate, sharpe, drawdown
            
        Returns:
            Dict with bet_size, tier, reasoning
        """
        
        # Default Kelly (edge / variance)
        # Assume variance ~0.25 for NFL betting
        optimal_kelly = edge / 0.25
        
        # Start with base (1/4 Kelly)
        kelly_fraction = 0.25
        multiplier = 1.0
        
        # ===== CONFIDENCE MULTIPLIER =====
        if confidence >= 0.80:
            multiplier *= 3.0  # SUPER CONFIDENT!
            tier = 'S'
        elif confidence >= 0.75:
            multiplier *= 2.5
            tier = 'S'
        elif confidence >= 0.70:
            multiplier *= 2.0  # Very confident
            tier = 'A'
        elif confidence >= 0.65:
            multiplier *= 1.0  # Standard
            tier = 'B'
        elif confidence >= 0.60:
            multiplier *= 0.5  # Uncertain
            tier = 'C'
        else:
            multiplier *= 0.0  # SKIP
            tier = 'D'
        
        # ===== EDGE MULTIPLIER =====
        if edge >= 0.15:
            multiplier *= 1.8  # HUGE edge!
        elif edge >= 0.10:
            multiplier *= 1.5
        elif edge >= 0.05:
            multiplier *= 1.2
        elif edge < 0.02:
            multiplier *= 0.3  # Too small
        
        # ===== SITUATIONAL MULTIPLIER =====
        if situational_edge >= 0.10:
            multiplier *= 1.6  # Proven 10%+ edge!
            logger.info(f"🎯 SITUATIONAL EDGE: {situational_edge:.1%}")
        elif situational_edge >= 0.05:
            multiplier *= 1.3
        
        # ===== WEATHER CONFIDENCE =====
        if weather_confidence == 'VERY HIGH':
            multiplier *= 1.4  # Satellite confirms forecast!
        elif weather_confidence == 'HIGH':
            multiplier *= 1.2
        elif weather_confidence == 'LOW':
            multiplier *= 0.8  # Uncertain weather
        
        # ===== PERFORMANCE GOVERNOR =====
        if recent_performance:
            recent_wr = recent_performance.get('win_rate', 0.54)
            recent_sharpe = recent_performance.get('sharpe', 1.0)
            max_dd = recent_performance.get('max_drawdown', 0.0)
            
            # HOT STREAK = ACCELERATE! 🔥
            if recent_wr >= 0.60:
                multiplier *= 1.5
                logger.info("🔥 HOT STREAK - ACCELERATING!")
            elif recent_wr >= 0.58:
                multiplier *= 1.3
            
            # COLD STREAK = BRAKE! 🛑
            elif recent_wr <= 0.50:
                multiplier *= 0.3
                logger.warning("🐌 COLD STREAK - PULLING BACK")
            elif recent_wr <= 0.52:
                multiplier *= 0.6
            
            # SEVERE DRAWDOWN = EMERGENCY STOP! 🚨
            if abs(max_dd) >= 0.25:
                multiplier = 0.0
                tier = 'X'
                logger.error("🚨 EMERGENCY STOP - Max drawdown exceeded!")
            elif abs(max_dd) >= 0.20:
                multiplier *= 0.3
                logger.warning("⚠️ High drawdown - reducing aggression")
        
        # ===== CALCULATE FINAL BET SIZE =====
        final_kelly_fraction = kelly_fraction * multiplier
        
        # Safety caps
        final_kelly_fraction = np.clip(final_kelly_fraction, 0, 0.75)  # Never more than 3/4 Kelly
        
        bet_size_kelly = self.bankroll * optimal_kelly * final_kelly_fraction
        bet_size_pct = bet_size_kelly / self.bankroll
        
        # Absolute safety: Never more than 10% of bankroll
        if bet_size_pct > self.max_bet_pct:
            bet_size_pct = self.max_bet_pct
            bet_size_kelly = self.bankroll * self.max_bet_pct
            logger.info(f"⚠️ Capping bet at {self.max_bet_pct:.1%} of bankroll")
        
        # Classify tier
        if bet_size_pct >= 0.08:
            tier = 'S - SLAM DUNK'
            emoji = '🚀'
        elif bet_size_pct >= 0.04:
            tier = 'A - HIGH CONFIDENCE'
            emoji = '🔥'
        elif bet_size_pct >= 0.015:
            tier = 'B - STANDARD'
            emoji = '⚙️'
        elif bet_size_pct >= 0.005:
            tier = 'C - EXPLORATORY'
            emoji = '🐌'
        else:
            tier = 'D - SKIP'
            emoji = '🛑'
        
        return {
            'bet_size': round(bet_size_kelly, 2),
            'bet_pct': bet_size_pct,
            'kelly_fraction': final_kelly_fraction,
            'multiplier': multiplier,
            'tier': tier,
            'emoji': emoji,
            'optimal_kelly': optimal_kelly,
            'reasoning': self._explain_sizing(
                confidence, edge, situational_edge, multiplier, recent_performance
            )
        }
    
    def _explain_sizing(self, confidence, edge, situational_edge, multiplier, recent_perf):
        """Explain why we sized this way."""
        reasons = []
        
        if confidence >= 0.75:
            reasons.append(f"Very high confidence ({confidence:.1%})")
        if edge >= 0.10:
            reasons.append(f"Large edge ({edge:.1%})")
        if situational_edge >= 0.05:
            reasons.append(f"Proven situation (+{situational_edge:.1%})")
        
        if recent_perf and recent_perf.get('win_rate', 0.54) >= 0.58:
            reasons.append("Hot streak")
        elif recent_perf and recent_perf.get('win_rate', 0.54) <= 0.52:
            reasons.append("Recent struggles (reduced)")
        
        if multiplier >= 2.0:
            reasons.append("AGGRESSIVE SIZING 🚀")
        elif multiplier <= 0.5:
            reasons.append("Conservative (low confidence)")
        
        return " | ".join(reasons) if reasons else "Standard bet"
    
    def get_tier_stats(self) -> pd.DataFrame:
        """Get performance by tier."""
        if not self.recent_bets:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.recent_bets)
        
        tier_stats = df.groupby('tier').agg({
            'bet_size': ['count', 'mean', 'sum'],
            'profit': 'sum',
            'won': lambda x: (x == True).sum()
        })
        
        tier_stats['win_rate'] = tier_stats['won'] / tier_stats['count']
        tier_stats['roi'] = tier_stats['profit_sum'] / tier_stats['bet_size_sum']
        
        return tier_stats


if __name__ == '__main__':
    # Test aggressive sizing
    calc = AggressiveKellyCalculator(bankroll=10000)
    
    print("="*70)
    print("AGGRESSIVE KELLY SIZING EXAMPLES")
    print("="*70)
    
    # Example 1: SLAM DUNK
    print("\n1. SLAM DUNK (Weather game, high confidence)")
    result = calc.calculate_bet_size(
        edge=0.18,  # 18% edge!
        confidence=0.87,
        situational_edge=0.11,  # Proven 11% weather edge
        weather_confidence='VERY HIGH',
        recent_performance={'win_rate': 0.60, 'sharpe': 2.5, 'max_drawdown': -0.10}
    )
    print(f"  Bet size: ${result['bet_size']} ({result['bet_pct']:.1%} of bankroll)")
    print(f"  Tier: {result['tier']} {result['emoji']}")
    print(f"  Kelly multiplier: {result['multiplier']:.2f}×")
    print(f"  Reasoning: {result['reasoning']}")
    
    # Example 2: Standard
    print("\n2. STANDARD BET")
    result = calc.calculate_bet_size(
        edge=0.04,
        confidence=0.66,
        situational_edge=0.0,
        weather_confidence='MEDIUM',
        recent_performance={'win_rate': 0.54, 'sharpe': 1.2, 'max_drawdown': -0.15}
    )
    print(f"  Bet size: ${result['bet_size']} ({result['bet_pct']:.1%} of bankroll)")
    print(f"  Tier: {result['tier']} {result['emoji']}")
    print(f"  Reasoning: {result['reasoning']}")
    
    # Example 3: SKIP
    print("\n3. LOW CONFIDENCE (SKIP)")
    result = calc.calculate_bet_size(
        edge=0.02,
        confidence=0.59,
        situational_edge=0.0,
        weather_confidence='LOW',
        recent_performance={'win_rate': 0.51, 'sharpe': 0.5, 'max_drawdown': -0.22}
    )
    print(f"  Bet size: ${result['bet_size']} ({result['bet_pct']:.1%} of bankroll)")
    print(f"  Tier: {result['tier']} {result['emoji']}")
    print(f"  Reasoning: {result['reasoning']}")
    
    print("\n" + "="*70)

