"""BULLDOG MODE: Advanced Analytics

Feature importance, CLV analysis, variance analysis, drawdown analysis, etc.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import joblib
import json
import logging
from typing import Dict, List, Tuple
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available - feature importance analysis will be limited")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("reports/bulldog_mode")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class BulldogAnalysis:
    """Advanced analytics for Bulldog Mode."""
    
    def __init__(self, model_path: str = "models/xgboost_improved.pkl",
                 data_path: str = "data/processed/features_2016_2024_improved.parquet",
                 results_path: str = None):
        """Initialize analysis engine."""
        self.model_path = model_path
        self.data_path = data_path
        
        # Load model
        logger.info(f"Loading model from {model_path}...")
        self.model = joblib.load(model_path)
        
        # Load data
        logger.info(f"Loading data from {data_path}...")
        self.df = pd.read_parquet(data_path)
        self.df_test = self.df[self.df['season'] >= 2020].copy()
        
        # Load backtest results if available
        if results_path:
            self.results_df = pd.read_csv(results_path)
        else:
            results_path = OUTPUT_DIR / "data" / "bulldog_backtest_results.csv"
            if results_path.exists():
                self.results_df = pd.read_csv(results_path)
            else:
                logger.warning("Backtest results not found - some analyses will be skipped")
                self.results_df = None
        
        # Get feature columns
        self.feature_cols = self._get_feature_columns()
        
        # Analysis results
        self.analysis_results = {}
    
    def _get_feature_columns(self) -> List[str]:
        """Get feature columns."""
        exclude = [
            "game_id", "gameday", "home_team", "away_team", "season", "week",
            "home_score", "away_score", "result", "target", "total", "game_type",
            "weekday", "gametime", "location", "overtime", "old_game_id", "gsis",
            "nfl_detail_id", "pfr", "pff", "espn", "ftn", "away_qb_id", "home_qb_id",
            "away_qb_name", "home_qb_name", "away_coach", "home_coach", "referee",
            "stadium_id", "stadium", "roof", "surface",
            "home_moneyline", "away_moneyline", "spread_line", "home_spread_odds",
            "away_spread_odds", "total_line", "over_odds", "under_odds",
            "line_movement", "total_movement", "home_favorite", "spread_home"
        ]
        
        feature_cols = [col for col in self.df.columns if col not in exclude]
        feature_cols = [col for col in feature_cols 
                       if self.df[col].dtype in ["float64", "int64"]]
        
        return feature_cols
    
    def analyze_feature_importance(self) -> pd.DataFrame:
        """A. Feature Importance Deep Dive"""
        logger.info("\n" + "="*80)
        logger.info("A. FEATURE IMPORTANCE DEEP DIVE")
        logger.info("="*80)
        
        # Get feature importance from model
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_names = self.feature_cols[:len(importances)]
        elif hasattr(self.model, 'get_feature_importance'):
            importance_dict = self.model.get_feature_importance()
            feature_names = list(importance_dict.keys())
            importances = list(importance_dict.values())
        elif hasattr(self.model, 'get_booster'):
            # XGBoost model
            booster = self.model.get_booster()
            feature_names = booster.feature_names
            importances = booster.get_score(importance_type='gain')
            # Convert to list in correct order
            importances = [importances.get(f, 0) for f in feature_names]
        else:
            logger.warning("Cannot extract feature importance from model")
            return pd.DataFrame()
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        # Calculate percentage
        importance_df['importance_pct'] = (importance_df['importance'] / 
                                          importance_df['importance'].sum() * 100)
        
        # Cumulative importance
        importance_df['cumulative_pct'] = importance_df['importance_pct'].cumsum()
        
        logger.info(f"\nTop 20 Features:")
        logger.info(importance_df.head(20).to_string(index=False))
        
        # Save
        importance_df.to_csv(OUTPUT_DIR / "data" / "bulldog_feature_importance.csv", index=False)
        
        self.analysis_results['feature_importance'] = importance_df
        
        # SHAP analysis if available
        if SHAP_AVAILABLE and len(self.df_test) > 0:
            logger.info("\nRunning SHAP analysis...")
            try:
                # Sample for SHAP (can be slow)
                sample_size = min(100, len(self.df_test))
                X_sample = self.df_test[self.feature_cols].fillna(0).iloc[:sample_size]
                
                # Create explainer
                explainer = shap.TreeExplainer(self.model)
                shap_values = explainer.shap_values(X_sample)
                
                # Calculate mean absolute SHAP values
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # Use positive class
                
                shap_importance = pd.DataFrame({
                    'feature': self.feature_cols[:shap_values.shape[1]],
                    'shap_importance': np.abs(shap_values).mean(axis=0)
                }).sort_values('shap_importance', ascending=False)
                
                logger.info(f"\nTop 10 Features by SHAP:")
                logger.info(shap_importance.head(10).to_string(index=False))
                
                shap_importance.to_csv(OUTPUT_DIR / "data" / "bulldog_shap_importance.csv", index=False)
                
            except Exception as e:
                logger.warning(f"SHAP analysis failed: {e}")
        
        return importance_df
    
    def analyze_clv(self) -> Dict:
        """B. Closing Line Value (CLV) Analysis"""
        logger.info("\n" + "="*80)
        logger.info("B. CLOSING LINE VALUE (CLV) ANALYSIS")
        logger.info("="*80)
        
        if self.results_df is None or len(self.results_df) == 0:
            logger.warning("No backtest results available for CLV analysis")
            return {}
        
        # Calculate CLV metrics
        clv_stats = {
            'avg_clv': self.results_df['clv'].mean() * 100,
            'median_clv': self.results_df['clv'].median() * 100,
            'std_clv': self.results_df['clv'].std() * 100,
            'positive_clv_pct': (self.results_df['clv'] > 0).sum() / len(self.results_df) * 100,
            'negative_clv_pct': (self.results_df['clv'] < 0).sum() / len(self.results_df) * 100,
            'clv_percentile_25': self.results_df['clv'].quantile(0.25) * 100,
            'clv_percentile_75': self.results_df['clv'].quantile(0.75) * 100,
        }
        
        # CLV by win/loss
        clv_by_result = self.results_df.groupby('result')['clv'].agg(['mean', 'std', 'count'])
        
        # CLV correlation with profitability
        if 'profit' in self.results_df.columns:
            clv_profit_corr = self.results_df['clv'].corr(self.results_df['profit'])
            clv_stats['clv_profit_correlation'] = clv_profit_corr
        
        logger.info(f"\nCLV Statistics:")
        logger.info(f"  Average CLV: {clv_stats['avg_clv']:.2f}%")
        logger.info(f"  Positive CLV: {clv_stats['positive_clv_pct']:.1f}% of bets")
        logger.info(f"  CLV-Profit Correlation: {clv_stats.get('clv_profit_correlation', 0):.3f}")
        
        self.analysis_results['clv'] = clv_stats
        return clv_stats
    
    def analyze_variance(self) -> Dict:
        """D. Variance Analysis (Monte Carlo)"""
        logger.info("\n" + "="*80)
        logger.info("D. VARIANCE ANALYSIS (MONTE CARLO)")
        logger.info("="*80)
        
        if self.results_df is None or len(self.results_df) == 0:
            logger.warning("No backtest results available for variance analysis")
            return {}
        
        # Get bet outcomes
        wins = (self.results_df['result'] == 'win').sum()
        losses = (self.results_df['result'] == 'loss').sum()
        total_bets = len(self.results_df)
        win_rate = wins / total_bets
        
        # Calculate actual profit
        actual_profit = self.results_df['profit'].sum()
        
        # Monte Carlo simulation
        n_simulations = 1000
        simulated_profits = []
        
        logger.info(f"Running {n_simulations} Monte Carlo simulations...")
        
        for _ in range(n_simulations):
            # Simulate random outcomes with same win rate
            simulated_results = np.random.binomial(1, win_rate, total_bets)
            
            # Calculate profit (simplified - use average bet size and odds)
            avg_bet_size = self.results_df['bet_size'].mean()
            avg_odds = self.results_df['odds'].mean()
            
            simulated_profit = 0
            for result in simulated_results:
                if result == 1:  # Win
                    simulated_profit += avg_bet_size * (avg_odds - 1)
                else:  # Loss
                    simulated_profit -= avg_bet_size
            
            simulated_profits.append(simulated_profit)
        
        simulated_profits = np.array(simulated_profits)
        
        # Calculate statistics
        variance_stats = {
            'actual_profit': actual_profit,
            'simulated_mean_profit': simulated_profits.mean(),
            'simulated_std_profit': simulated_profits.std(),
            'simulated_median_profit': np.median(simulated_profits),
            'p_value': stats.ttest_1samp(simulated_profits, actual_profit)[1],
            'percentile_5': np.percentile(simulated_profits, 5),
            'percentile_95': np.percentile(simulated_profits, 95),
            'probability_positive': (simulated_profits > 0).mean(),
            'z_score': (actual_profit - simulated_profits.mean()) / simulated_profits.std() if simulated_profits.std() > 0 else 0
        }
        
        logger.info(f"\nVariance Analysis:")
        logger.info(f"  Actual Profit: ${variance_stats['actual_profit']:,.2f}")
        logger.info(f"  Simulated Mean: ${variance_stats['simulated_mean_profit']:,.2f}")
        logger.info(f"  Z-Score: {variance_stats['z_score']:.2f}")
        logger.info(f"  P-Value: {variance_stats['p_value']:.4f}")
        logger.info(f"  Probability of Positive: {variance_stats['probability_positive']:.1%}")
        
        self.analysis_results['variance'] = variance_stats
        return variance_stats
    
    def analyze_drawdown(self) -> Dict:
        """E. Drawdown Analysis"""
        logger.info("\n" + "="*80)
        logger.info("E. DRAWDOWN ANALYSIS")
        logger.info("="*80)
        
        if self.results_df is None or len(self.results_df) == 0:
            logger.warning("No backtest results available for drawdown analysis")
            return {}
        
        # Calculate cumulative bankroll
        bankrolls = self.results_df['bankroll'].values
        cumulative_max = np.maximum.accumulate(bankrolls)
        drawdowns = (bankrolls - cumulative_max) / cumulative_max
        
        # Find drawdown periods
        in_drawdown = drawdowns < 0
        drawdown_periods = []
        start_idx = None
        
        for i, is_dd in enumerate(in_drawdown):
            if is_dd and start_idx is None:
                start_idx = i
            elif not is_dd and start_idx is not None:
                drawdown_periods.append({
                    'start': start_idx,
                    'end': i - 1,
                    'duration': i - start_idx,
                    'max_drawdown': drawdowns[start_idx:i].min()
                })
                start_idx = None
        
        # Calculate statistics
        drawdown_stats = {
            'max_drawdown': drawdowns.min() * 100,
            'avg_drawdown': drawdowns[drawdowns < 0].mean() * 100 if (drawdowns < 0).any() else 0,
            'num_drawdown_periods': len(drawdown_periods),
            'avg_drawdown_duration': np.mean([p['duration'] for p in drawdown_periods]) if drawdown_periods else 0,
            'max_drawdown_duration': max([p['duration'] for p in drawdown_periods]) if drawdown_periods else 0,
            'worst_drawdown': min([p['max_drawdown'] for p in drawdown_periods]) * 100 if drawdown_periods else 0
        }
        
        logger.info(f"\nDrawdown Statistics:")
        logger.info(f"  Max Drawdown: {drawdown_stats['max_drawdown']:.2f}%")
        logger.info(f"  Number of Drawdown Periods: {drawdown_stats['num_drawdown_periods']}")
        logger.info(f"  Average Duration: {drawdown_stats['avg_drawdown_duration']:.1f} bets")
        logger.info(f"  Worst Drawdown: {drawdown_stats['worst_drawdown']:.2f}%")
        
        self.analysis_results['drawdown'] = drawdown_stats
        return drawdown_stats
    
    def analyze_statistical_significance(self) -> Dict:
        """Statistical validation - prove results are not luck"""
        logger.info("\n" + "="*80)
        logger.info("STATISTICAL SIGNIFICANCE ANALYSIS")
        logger.info("="*80)
        
        if self.results_df is None or len(self.results_df) == 0:
            logger.warning("No backtest results available for statistical analysis")
            return {}
        
        # Get outcomes
        wins = (self.results_df['result'] == 'win').sum()
        total_bets = len(self.results_df)
        win_rate = wins / total_bets
        
        # Hypothesis test: H0: win_rate = 0.5 (random)
        # H1: win_rate > 0.5 (skill)
        z_score = (win_rate - 0.5) / np.sqrt(0.5 * 0.5 / total_bets)
        p_value = 1 - stats.norm.cdf(z_score)
        
        # Confidence intervals using normal approximation
        se = np.sqrt(win_rate * (1 - win_rate) / total_bets)
        z_95 = stats.norm.ppf(0.975)  # 95% CI
        z_99 = stats.norm.ppf(0.995)  # 99% CI
        ci_95 = (win_rate - z_95 * se, win_rate + z_95 * se)
        ci_99 = (win_rate - z_99 * se, win_rate + z_99 * se)
        
        stats_results = {
            'win_rate': win_rate * 100,
            'total_bets': total_bets,
            'wins': wins,
            'z_score': z_score,
            'p_value': p_value,
            'significant_95': p_value < 0.05,
            'significant_99': p_value < 0.01,
            'ci_95_lower': ci_95[0] * 100,
            'ci_95_upper': ci_95[1] * 100,
            'ci_99_lower': ci_99[0] * 100,
            'ci_99_upper': ci_99[1] * 100
        }
        
        logger.info(f"\nStatistical Significance:")
        logger.info(f"  Win Rate: {stats_results['win_rate']:.2f}%")
        logger.info(f"  Z-Score: {stats_results['z_score']:.2f}")
        logger.info(f"  P-Value: {stats_results['p_value']:.6f}")
        logger.info(f"  Significant at 95%: {stats_results['significant_95']}")
        logger.info(f"  Significant at 99%: {stats_results['significant_99']}")
        logger.info(f"  95% CI: [{stats_results['ci_95_lower']:.2f}%, {stats_results['ci_95_upper']:.2f}%]")
        
        self.analysis_results['statistical_significance'] = stats_results
        return stats_results
    
    def run_all_analyses(self):
        """Run all analyses."""
        logger.info("="*80)
        logger.info("RUNNING ALL BULLDOG MODE ANALYSES")
        logger.info("="*80)
        
        self.analyze_feature_importance()
        self.analyze_clv()
        self.analyze_variance()
        self.analyze_drawdown()
        self.analyze_statistical_significance()
        
        # Save all analysis results
        with open(OUTPUT_DIR / "data" / "bulldog_analysis_results.json", 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        logger.info("\n" + "="*80)
        logger.info("ALL ANALYSES COMPLETE")
        logger.info("="*80)


def main():
    """Main execution."""
    analyzer = BulldogAnalysis()
    analyzer.run_all_analyses()


if __name__ == "__main__":
    main()

