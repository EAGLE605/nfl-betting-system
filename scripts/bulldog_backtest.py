"""BULLDOG MODE: Exhaustive Backtest System

This script runs the most comprehensive backtest ever conducted on the NFL betting system.
Tests ALL scenarios, dimensions, and edge cases to find EVERY exploitable edge.

NO COMPROMISES. NO SHORTCUTS. FIND THE EDGE.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import joblib
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from src.backtesting.engine import BacktestEngine
from src.betting.kelly import KellyCriterion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
np.random.seed(42)

# Create output directories
OUTPUT_DIR = Path("reports/bulldog_mode")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "visualizations").mkdir(exist_ok=True)
(OUTPUT_DIR / "data").mkdir(exist_ok=True)


class BulldogBacktest:
    """Comprehensive backtest engine for Bulldog Mode."""
    
    def __init__(self, model_path: str = "models/xgboost_improved.pkl", 
                 data_path: str = "data/processed/features_2016_2024_improved.parquet",
                 initial_bankroll: float = 10000):
        """Initialize backtest engine."""
        self.model_path = model_path
        self.data_path = data_path
        self.initial_bankroll = initial_bankroll
        
        # Load model
        logger.info(f"Loading model from {model_path}...")
        self.model = joblib.load(model_path)
        
        # Load data
        logger.info(f"Loading data from {data_path}...")
        self.df = pd.read_parquet(data_path)
        logger.info(f"Loaded {len(self.df)} games")
        logger.info(f"Date range: {self.df['gameday'].min()} to {self.df['gameday'].max()}")
        
        # Get feature columns
        self.feature_cols = self._get_feature_columns()
        logger.info(f"Using {len(self.feature_cols)} features")
        
        # Prepare predictions
        self._prepare_predictions()
        
        # Results storage
        self.results = {}
        self.all_bets = []
        
    def _get_feature_columns(self) -> List[str]:
        """Get feature columns, excluding metadata and betting lines."""
        exclude = [
            "game_id", "gameday", "home_team", "away_team", "season", "week",
            "home_score", "away_score", "result", "target", "total", "game_type",
            "weekday", "gametime", "location", "overtime", "old_game_id", "gsis",
            "nfl_detail_id", "pfr", "pff", "espn", "ftn", "away_qb_id", "home_qb_id",
            "away_qb_name", "home_qb_name", "away_coach", "home_coach", "referee",
            "stadium_id", "stadium", "roof", "surface",
            # CRITICAL: Exclude betting line features (data leakage)
            "home_moneyline", "away_moneyline", "spread_line", "home_spread_odds",
            "away_spread_odds", "total_line", "over_odds", "under_odds",
            "line_movement", "total_movement", "home_favorite", "spread_home"
        ]
        
        feature_cols = [col for col in self.df.columns if col not in exclude]
        feature_cols = [col for col in feature_cols 
                       if self.df[col].dtype in ["float64", "int64"]]
        
        return feature_cols
    
    def _prepare_predictions(self):
        """Generate predictions for all games."""
        logger.info("Generating predictions...")
        
        # Filter to test period (2020-2024)
        self.df_test = self.df[self.df['season'] >= 2020].copy()
        logger.info(f"Test period (2020-2024): {len(self.df_test)} games")
        
        # Get model's expected features
        model_features = None
        if hasattr(self.model, 'get_booster'):
            # XGBoost model
            booster = self.model.get_booster()
            model_features = booster.feature_names
        elif hasattr(self.model, 'feature_names_in_'):
            model_features = self.model.feature_names_in_
        elif hasattr(self.model, 'get_feature_importance'):
            # Try to get from feature importance
            importance_dict = self.model.get_feature_importance()
            model_features = list(importance_dict.keys())
        
        # Align features with model expectations
        if model_features:
            # Use model's expected features
            available_features = [f for f in model_features if f in self.df_test.columns]
            missing_features = [f for f in model_features if f not in self.df_test.columns]
            
            if missing_features:
                logger.warning(f"Model expects {len(missing_features)} features not in data, filling with 0: {missing_features[:5]}...")
                for feat in missing_features:
                    self.df_test[feat] = 0
            
            # Use model's feature order
            X = self.df_test[model_features].fillna(0)
        else:
            # Fallback to our feature columns
            X = self.df_test[self.feature_cols].fillna(0)
        
        # Generate predictions
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X)
            if proba.ndim == 1:
                self.df_test['pred_prob'] = proba
            else:
                self.df_test['pred_prob'] = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
        else:
            # Calibrator interface
            self.df_test['pred_prob'] = self.model.predict_proba(X)
        
        # Actual outcomes
        self.df_test['actual'] = (self.df_test['home_score'] > self.df_test['away_score']).astype(int)
        
        # Calculate confidence (distance from 0.5)
        self.df_test['confidence'] = (self.df_test['pred_prob'] - 0.5).abs() * 2
        
        # Convert moneyline to decimal odds
        def american_to_decimal(american_odds):
            if pd.isna(american_odds):
                return 1.91  # Default -110
            if american_odds > 0:
                return (american_odds / 100) + 1
            else:
                return (100 / abs(american_odds)) + 1
        
        if "home_moneyline" in self.df_test.columns:
            self.df_test['odds'] = self.df_test['home_moneyline'].apply(american_to_decimal)
        else:
            logger.warning("home_moneyline not found, using default 1.91 odds")
            self.df_test['odds'] = 1.91
        
        # Calculate implied probability
        self.df_test['implied_prob'] = 1 / self.df_test['odds']
        
        # Calculate edge
        self.df_test['edge'] = self.df_test['pred_prob'] - self.df_test['implied_prob']
        
        # Calculate CLV (Closing Line Value)
        # For now, use opening line as proxy (we'll enhance this later)
        if "spread_home" in self.df_test.columns:
            # Use spread to estimate closing line
            self.df_test['clv'] = self.df_test['edge']  # Simplified
        else:
            self.df_test['clv'] = self.df_test['edge']
        
        logger.info(f"✓ Predictions generated for {len(self.df_test)} games")
        logger.info(f"  Average confidence: {self.df_test['confidence'].mean():.2%}")
        logger.info(f"  Average edge: {self.df_test['edge'].mean():.2%}")
    
    def run_backtest(self, df_subset: pd.DataFrame, 
                    kelly_fraction: float = 0.25,
                    min_confidence: float = 0.0,
                    name: str = "default") -> Dict:
        """Run backtest on a subset of games."""
        # Filter by confidence if specified
        if min_confidence > 0:
            df_subset = df_subset[df_subset['confidence'] >= min_confidence].copy()
        
        if len(df_subset) == 0:
            return {
                'name': name,
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_profit': 0,
                'roi': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'avg_clv': 0,
                'positive_clv_pct': 0,
                'final_bankroll': self.initial_bankroll
            }
        
        # Create custom config for this backtest
        config = {
            'kelly_fraction': kelly_fraction,
            'min_edge': 0.02,
            'min_probability': 0.55,
            'max_bet_size': 0.02
        }
        
        # Initialize engine
        engine = BacktestEngine(
            initial_bankroll=self.initial_bankroll,
            config=config
        )
        
        # Run backtest
        metrics, history_df = engine.run_backtest(df_subset)
        
        # Add metadata
        metrics['name'] = name
        metrics['kelly_fraction'] = kelly_fraction
        metrics['min_confidence'] = min_confidence
        metrics['games_available'] = len(df_subset)
        
        # Store bets for analysis
        if len(history_df) > 0:
            history_df['scenario'] = name
            self.all_bets.append(history_df)
        
        return metrics
    
    def test_dimension_time_periods(self) -> Dict:
        """Test Dimension 1: Time Periods"""
        logger.info("\n" + "="*80)
        logger.info("TEST DIMENSION 1: TIME PERIODS")
        logger.info("="*80)
        
        results = {}
        
        # Full period (2020-2024)
        logger.info("\n1. Full Period (2020-2024)...")
        results['full_period'] = self.run_backtest(
            self.df_test.copy(),
            name="Full Period (2020-2024)"
        )
        logger.info(f"  ✓ Complete: {results['full_period'].get('bet_count', 0)} bets, ROI: {results['full_period'].get('roi', 0):.2%}")
        
        # By season
        for season in [2020, 2021, 2022, 2023, 2024]:
            logger.info(f"\n2. Season {season}...")
            df_season = self.df_test[self.df_test['season'] == season].copy()
            results[f'season_{season}'] = self.run_backtest(
                df_season,
                name=f"Season {season}"
            )
            logger.info(f"  ✓ Complete: {results[f'season_{season}'].get('bet_count', 0)} bets, ROI: {results[f'season_{season}'].get('roi', 0):.2%}")
        
        # By quarter (Q1/Q2 vs Q3/Q4)
        logger.info("\n3. Early Season (Weeks 1-9) vs Late Season (Weeks 10-18)...")
        df_early = self.df_test[self.df_test['week'].between(1, 9)].copy()
        df_late = self.df_test[self.df_test['week'].between(10, 18)].copy()
        
        results['early_season'] = self.run_backtest(df_early, name="Early Season (Weeks 1-9)")
        results['late_season'] = self.run_backtest(df_late, name="Late Season (Weeks 10-18)")
        
        # Regular season vs playoffs
        logger.info("\n4. Regular Season vs Playoffs...")
        df_regular = self.df_test[self.df_test['game_type'] == 'REG'].copy()
        df_playoffs = self.df_test[self.df_test['game_type'] != 'REG'].copy()
        
        results['regular_season'] = self.run_backtest(df_regular, name="Regular Season")
        results['playoffs'] = self.run_backtest(df_playoffs, name="Playoffs")
        
        self.results['time_periods'] = results
        return results
    
    def test_dimension_game_characteristics(self) -> Dict:
        """Test Dimension 2: Game Characteristics"""
        logger.info("\n" + "="*80)
        logger.info("TEST DIMENSION 2: GAME CHARACTERISTICS")
        logger.info("="*80)
        
        results = {}
        
        # Spread size
        logger.info("\n1. Spread Size Segments...")
        if 'spread_home' in self.df_test.columns:
            results['heavy_favorites'] = self.run_backtest(
                self.df_test[self.df_test['spread_home'] < -7].copy(),
                name="Heavy Favorites (Spread < -7)"
            )
            results['moderate_favorites'] = self.run_backtest(
                self.df_test[self.df_test['spread_home'].between(-7, -3)].copy(),
                name="Moderate Favorites (Spread -7 to -3)"
            )
            results['slight_favorites'] = self.run_backtest(
                self.df_test[self.df_test['spread_home'].between(-3, -1)].copy(),
                name="Slight Favorites (Spread -3 to -1)"
            )
            results['tossups'] = self.run_backtest(
                self.df_test[self.df_test['spread_home'].between(-1, 1)].copy(),
                name="Toss-ups (Spread -1 to +1)"
            )
            results['underdogs'] = self.run_backtest(
                self.df_test[self.df_test['spread_home'] > 3].copy(),
                name="Underdogs (Spread > +3)"
            )
        
        # Total points
        logger.info("\n2. Total Points Segments...")
        if 'total_line' in self.df_test.columns:
            results['high_scoring'] = self.run_backtest(
                self.df_test[self.df_test['total_line'] > 50].copy(),
                name="High Scoring (O/U > 50)"
            )
            results['normal_scoring'] = self.run_backtest(
                self.df_test[self.df_test['total_line'].between(42, 50)].copy(),
                name="Normal Scoring (O/U 42-50)"
            )
            results['low_scoring'] = self.run_backtest(
                self.df_test[self.df_test['total_line'] < 42].copy(),
                name="Low Scoring (O/U < 42)"
            )
        
        # Division games
        logger.info("\n3. Division Games...")
        if 'div_game' in self.df_test.columns:
            results['divisional'] = self.run_backtest(
                self.df_test[self.df_test['div_game'] == 1].copy(),
                name="Divisional Games"
            )
            results['non_divisional'] = self.run_backtest(
                self.df_test[self.df_test['div_game'] == 0].copy(),
                name="Non-Divisional Games"
            )
        
        # Weather conditions
        logger.info("\n4. Weather Conditions...")
        if 'is_dome' in self.df_test.columns:
            results['dome'] = self.run_backtest(
                self.df_test[self.df_test['is_dome'] == 1].copy(),
                name="Dome Games"
            )
        
        if 'temp' in self.df_test.columns and 'wind' in self.df_test.columns:
            df_good_weather = self.df_test[
                (self.df_test['temp'] > 50) & 
                (self.df_test['wind'] < 10)
            ].copy()
            results['good_weather'] = self.run_backtest(
                df_good_weather,
                name="Good Weather (>50°F, wind <10 mph)"
            )
            
            df_bad_weather = self.df_test[
                (self.df_test['temp'] < 32) | 
                (self.df_test['wind'] > 15)
            ].copy()
            results['bad_weather'] = self.run_backtest(
                df_bad_weather,
                name="Bad Weather (<32°F or wind >15 mph)"
            )
        
        self.results['game_characteristics'] = results
        return results
    
    def test_dimension_confidence_levels(self) -> Dict:
        """Test Dimension 4: Model Confidence Levels"""
        logger.info("\n" + "="*80)
        logger.info("TEST DIMENSION 4: MODEL CONFIDENCE LEVELS")
        logger.info("="*80)
        
        results = {}
        
        confidence_thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        for threshold in confidence_thresholds:
            logger.info(f"\nTesting confidence threshold: {threshold:.1%}...")
            results[f'conf_{threshold:.1f}'] = self.run_backtest(
                self.df_test.copy(),
                min_confidence=threshold,
                name=f"Confidence > {threshold:.0%}"
            )
        
        self.results['confidence_levels'] = results
        return results
    
    def test_dimension_bet_sizing(self) -> Dict:
        """Test Dimension 6: Bet Sizing Strategies"""
        logger.info("\n" + "="*80)
        logger.info("TEST DIMENSION 6: BET SIZING STRATEGIES")
        logger.info("="*80)
        
        results = {}
        
        # Test different Kelly fractions
        kelly_fractions = [0.125, 0.25, 0.5, 0.75, 1.0]
        
        for kf in kelly_fractions:
            logger.info(f"\nTesting Kelly fraction: {kf}...")
            results[f'kelly_{kf}'] = self.run_backtest(
                self.df_test.copy(),
                kelly_fraction=kf,
                name=f"Kelly Fraction {kf}"
            )
        
        self.results['bet_sizing'] = results
        return results
    
    def test_scenario_favorites_destroyer(self) -> Dict:
        """Scenario 1: THE FAVORITES DESTROYER"""
        logger.info("\n" + "="*80)
        logger.info("SCENARIO 1: THE FAVORITES DESTROYER")
        logger.info("="*80)
        
        # Only bet heavy favorites with high confidence
        if 'spread_home' in self.df_test.columns:
            df_fav = self.df_test[
                (self.df_test['spread_home'] < -7) &
                (self.df_test['confidence'] > 0.65)
            ].copy()
        else:
            # Use odds instead
            df_fav = self.df_test[
                (self.df_test['odds'] < 1.7) &
                (self.df_test['confidence'] > 0.65)
            ].copy()
        
        result = self.run_backtest(df_fav, name="Favorites Destroyer")
        self.results['scenario_favorites_destroyer'] = result
        return result
    
    def test_scenario_primetime_crusher(self) -> Dict:
        """Scenario 2: THE PRIMETIME CRUSHER"""
        logger.info("\n" + "="*80)
        logger.info("SCENARIO 2: THE PRIMETIME CRUSHER")
        logger.info("="*80)
        
        # Primetime games (SNF, MNF, TNF)
        # Check if we have game time info
        if 'gametime' in self.df_test.columns:
            # Assume primetime is evening games
            df_primetime = self.df_test[
                self.df_test['gametime'].str.contains('20:00|21:00|22:00', na=False)
            ].copy()
        else:
            # Fallback: use weekdays
            df_primetime = self.df_test[
                self.df_test['weekday'].isin(['Sunday', 'Monday', 'Thursday'])
            ].copy()
        
        result = self.run_backtest(df_primetime, name="Primetime Crusher")
        self.results['scenario_primetime_crusher'] = result
        return result
    
    def test_scenario_weather_wizard(self) -> Dict:
        """Scenario 3: THE WEATHER WIZARD"""
        logger.info("\n" + "="*80)
        logger.info("SCENARIO 3: THE WEATHER WIZARD")
        logger.info("="*80)
        
        if 'wind' in self.df_test.columns and 'temp' in self.df_test.columns:
            df_bad_weather = self.df_test[
                (self.df_test['wind'] > 15) | 
                (self.df_test['temp'] < 32)
            ].copy()
            
            result = self.run_backtest(df_bad_weather, name="Weather Wizard")
            self.results['scenario_weather_wizard'] = result
            return result
        
        logger.warning("Weather data not available for Weather Wizard scenario")
        return {}
    
    def test_all_scenarios(self):
        """Run all test scenarios."""
        logger.info("\n" + "="*80)
        logger.info("RUNNING ALL BULLDOG MODE SCENARIOS")
        logger.info("="*80)
        
        # Test all dimensions
        self.test_dimension_time_periods()
        self.test_dimension_game_characteristics()
        self.test_dimension_confidence_levels()
        self.test_dimension_bet_sizing()
        
        # Test specific scenarios
        self.test_scenario_favorites_destroyer()
        self.test_scenario_primetime_crusher()
        self.test_scenario_weather_wizard()
        
        logger.info("\n" + "="*80)
        logger.info("ALL SCENARIOS COMPLETE")
        logger.info("="*80)
    
    def save_results(self):
        """Save all results to files."""
        logger.info("\nSaving results...")
        
        # Save all bets
        if self.all_bets:
            all_bets_df = pd.concat(self.all_bets, ignore_index=True)
            all_bets_df.to_csv(OUTPUT_DIR / "data" / "bulldog_backtest_results.csv", index=False)
            logger.info(f"✓ Saved {len(all_bets_df)} bets to CSV")
        
        # Save results summary
        results_summary = []
        for category, results in self.results.items():
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, dict) and 'name' in value:
                        results_summary.append(value)
        
        if results_summary:
            results_df = pd.DataFrame(results_summary)
            results_df.to_csv(OUTPUT_DIR / "data" / "bulldog_performance_by_segment.csv", index=False)
            logger.info(f"✓ Saved {len(results_df)} scenario results to CSV")
        
        # Save raw results JSON
        with open(OUTPUT_DIR / "data" / "bulldog_results_raw.json", 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info("✓ Results saved")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulldog Mode Backtest')
    parser.add_argument('--model', type=str, default='models/xgboost_improved.pkl',
                       help='Path to model file')
    parser.add_argument('--test-season', type=int, default=None,
                       help='Test on specific season only (e.g., 2024)')
    parser.add_argument('--data', type=str, default='data/processed/features_2016_2024_improved.parquet',
                       help='Path to data file')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("🐕 BULLDOG MODE BACKTEST - NO COMPROMISES")
    logger.info("="*80)
    logger.info(f"Started at: {datetime.now()}")
    logger.info(f"Model: {args.model}")
    if args.test_season:
        logger.info(f"Test Season: {args.test_season} ONLY")
    
    # Initialize backtest
    backtest = BulldogBacktest(
        model_path=args.model,
        data_path=args.data
    )
    
    # Filter to specific season if requested
    if args.test_season:
        logger.info(f"\nFiltering to season {args.test_season} only...")
        backtest.df_test = backtest.df_test[backtest.df_test['season'] == args.test_season].copy()
        logger.info(f"Filtered to {len(backtest.df_test)} games")
        # Regenerate predictions for filtered data
        backtest._prepare_predictions()
    
    # Run all scenarios
    backtest.test_all_scenarios()
    
    # Save results
    backtest.save_results()
    
    logger.info("\n" + "="*80)
    logger.info("BULLDOG MODE BACKTEST COMPLETE")
    logger.info("="*80)
    logger.info(f"Completed at: {datetime.now()}")
    logger.info(f"Results saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

