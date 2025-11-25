"""
Lab Runner - Unified interface for backtesting and training operations.

Provides async and sync methods for running backtests and training models,
designed to be called from the Streamlit dashboard.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from src.backtesting.data_loader import BacktestDataLoader
from src.backtesting.engine import BacktestEngine
from src.backtesting.prediction_generator import PredictionGenerator
from src.swarms.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class LabRunner:
    """
    Unified interface for The Lab operations.
    
    Supports:
    - Single model backtesting
    - Multi-model comparison backtesting
    - Walk-forward validation
    - Real-time progress callbacks
    """
    
    def __init__(self, data_dir: str = "data", models_dir: str = "models"):
        """
        Initialize Lab Runner.
        
        Args:
            data_dir: Path to data directory
            models_dir: Path to models directory
        """
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        
        self.data_loader = BacktestDataLoader(data_dir)
        self.model_loader = ModelLoader()
        self.pred_generator = PredictionGenerator()
        
        logger.info("LabRunner initialized")
    
    def get_available_models(self) -> List[str]:
        """Get list of available trained models."""
        return self.model_loader.list_available_models()
    
    def get_available_seasons(self) -> List[int]:
        """Get list of available seasons for backtesting."""
        return self.data_loader.get_available_seasons()
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get metadata about a model."""
        meta = self.model_loader.get_model_metadata(model_name)
        
        # Try to determine model type
        if "xgboost" in model_name.lower():
            meta["model_type"] = "XGBoost"
        elif "lightgbm" in model_name.lower():
            meta["model_type"] = "LightGBM"
        elif "ensemble" in model_name.lower():
            meta["model_type"] = "Ensemble"
        elif "calibrated" in model_name.lower():
            meta["model_type"] = "Calibrated"
        else:
            meta["model_type"] = "Unknown"
        
        return meta
    
    def run_backtest(
        self,
        model_name: str,
        start_year: int,
        end_year: int,
        initial_bankroll: float = 10000,
        kelly_fraction: float = 0.25,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Run a full backtest for a single model.
        
        Args:
            model_name: Name of model to backtest
            start_year: Start year for backtest period
            end_year: End year for backtest period
            initial_bankroll: Starting bankroll
            kelly_fraction: Kelly criterion fraction for bet sizing
            progress_callback: Optional callback(message, progress_pct)
        
        Returns:
            Dict with backtest results:
                - metrics: Performance metrics
                - history: Bet-by-bet history
                - model_name: Model used
                - period: Date range
        """
        def log_progress(msg: str, pct: float = 0):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, pct)
        
        log_progress(f"Starting backtest for {model_name}", 0)
        
        try:
            # Step 1: Load data
            log_progress("Loading historical data...", 10)
            schedules_df, pbp_df = self.data_loader.get_backtest_data({
                "start_year": start_year,
                "end_year": end_year,
                "focus": "full"
            })
            
            if schedules_df is None or len(schedules_df) == 0:
                return {"error": "No historical data found for the specified period"}
            
            log_progress(f"Loaded {len(schedules_df)} games", 25)
            
            # Step 2: Generate predictions
            log_progress("Generating model predictions...", 30)
            predictions_df = self.pred_generator.generate_predictions(
                schedules_df,
                {"model_name": model_name},
                pbp_df
            )
            
            if len(predictions_df) == 0:
                return {"error": "No predictions could be generated"}
            
            log_progress(f"Generated {len(predictions_df)} predictions", 60)
            
            # Step 3: Run backtest engine
            log_progress("Running walk-forward backtest...", 70)
            engine = BacktestEngine(
                initial_bankroll=initial_bankroll,
                config={
                    "kelly_fraction": kelly_fraction,
                    "min_edge": 0.02,
                    "min_probability": 0.55,
                    "max_bet_size": 0.02
                }
            )
            
            metrics, history_df = engine.run_backtest(predictions_df)
            
            log_progress("Calculating final metrics...", 90)
            
            # Build result
            result = {
                "metrics": metrics,
                "history": history_df.to_dict('records') if len(history_df) > 0 else [],
                "model_name": model_name,
                "start_year": start_year,
                "end_year": end_year,
                "predictions_count": len(predictions_df),
                "timestamp": datetime.now().isoformat()
            }
            
            log_progress(f"Backtest complete! ROI: {metrics.get('roi', 0):.2f}%", 100)
            
            return result
            
        except FileNotFoundError as e:
            logger.error(f"Model not found: {e}")
            return {"error": f"Model not found: {model_name}"}
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {"error": str(e)}
    
    def run_comparison_backtest(
        self,
        model_names: List[str],
        start_year: int,
        end_year: int,
        initial_bankroll: float = 10000,
        kelly_fraction: float = 0.25,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run backtest for multiple models and return comparison results.
        
        Args:
            model_names: List of model names to compare
            start_year: Start year for backtest period
            end_year: End year for backtest period
            initial_bankroll: Starting bankroll (same for all)
            kelly_fraction: Kelly criterion fraction
            progress_callback: Optional callback(message, progress_pct)
        
        Returns:
            Dict mapping model_name to backtest results
        """
        results = {}
        total_models = len(model_names)
        
        for i, model_name in enumerate(model_names):
            base_progress = (i / total_models) * 100
            
            def model_progress(msg: str, pct: float):
                overall_pct = base_progress + (pct / total_models)
                if progress_callback:
                    progress_callback(f"[{model_name}] {msg}", overall_pct)
            
            results[model_name] = self.run_backtest(
                model_name=model_name,
                start_year=start_year,
                end_year=end_year,
                initial_bankroll=initial_bankroll,
                kelly_fraction=kelly_fraction,
                progress_callback=model_progress
            )
        
        return results
    
    def run_walk_forward(
        self,
        model_name: str,
        start_year: int,
        end_year: int,
        test_weeks: int = 4,
        initial_bankroll: float = 10000,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Run walk-forward validation with rolling windows.
        
        Args:
            model_name: Model to validate
            start_year: Start year
            end_year: End year
            test_weeks: Number of weeks in each test window
            initial_bankroll: Starting bankroll
            progress_callback: Optional progress callback
        
        Returns:
            Dict with walk-forward validation results
        """
        def log_progress(msg: str, pct: float = 0):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, pct)
        
        log_progress(f"Starting walk-forward validation for {model_name}", 0)
        
        try:
            # Load full dataset
            schedules_df, pbp_df = self.data_loader.get_backtest_data({
                "start_year": start_year,
                "end_year": end_year,
                "focus": "full"
            })
            
            if schedules_df is None or len(schedules_df) == 0:
                return {"error": "No data found"}
            
            # Sort by date and create windows
            schedules_df = schedules_df.sort_values('gameday')
            schedules_df['week_num'] = pd.to_datetime(schedules_df['gameday']).dt.isocalendar().week
            
            # Get unique week boundaries
            unique_weeks = schedules_df['week_num'].unique()
            
            window_results = []
            total_windows = max(1, len(unique_weeks) // test_weeks - 1)
            
            for i, window_start in enumerate(range(0, len(unique_weeks) - test_weeks, test_weeks)):
                pct = (i / total_windows) * 100
                log_progress(f"Processing window {i+1}/{total_windows}", pct)
                
                # Define train/test split for this window
                train_weeks = unique_weeks[:window_start + test_weeks]
                test_weeks_list = unique_weeks[window_start:window_start + test_weeks]
                
                # Get test data for this window
                test_mask = schedules_df['week_num'].isin(test_weeks_list)
                test_df = schedules_df[test_mask]
                
                if len(test_df) == 0:
                    continue
                
                # Generate predictions and backtest
                predictions_df = self.pred_generator.generate_predictions(
                    test_df,
                    {"model_name": model_name},
                    pbp_df
                )
                
                if len(predictions_df) > 0:
                    engine = BacktestEngine(initial_bankroll=initial_bankroll)
                    metrics, _ = engine.run_backtest(predictions_df)
                    
                    window_results.append({
                        "window": i + 1,
                        "games": len(test_df),
                        "bets": metrics.get("total_bets", 0),
                        "roi": metrics.get("roi", 0),
                        "win_rate": metrics.get("win_rate", 0)
                    })
            
            # Aggregate results
            if window_results:
                avg_roi = sum(w["roi"] for w in window_results) / len(window_results)
                avg_win_rate = sum(w["win_rate"] for w in window_results) / len(window_results)
                consistency = sum(1 for w in window_results if w["roi"] > 0) / len(window_results)
            else:
                avg_roi = 0
                avg_win_rate = 0
                consistency = 0
            
            log_progress("Walk-forward validation complete!", 100)
            
            return {
                "model_name": model_name,
                "windows": window_results,
                "summary": {
                    "avg_roi": avg_roi,
                    "avg_win_rate": avg_win_rate,
                    "consistency": consistency * 100,  # % of windows profitable
                    "total_windows": len(window_results)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Walk-forward failed: {e}")
            return {"error": str(e)}
    
    def validate_data_availability(
        self,
        start_year: int,
        end_year: int
    ) -> Dict[str, Any]:
        """Check if data is available for the requested period."""
        return self.data_loader.validate_data_availability(start_year, end_year)


# Async wrapper for use with async frameworks
class AsyncLabRunner:
    """Async wrapper for LabRunner."""
    
    def __init__(self, *args, **kwargs):
        self._runner = LabRunner(*args, **kwargs)
    
    async def run_backtest(self, *args, **kwargs) -> Dict[str, Any]:
        """Run backtest asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._runner.run_backtest(*args, **kwargs)
        )
    
    async def run_comparison_backtest(self, *args, **kwargs) -> Dict[str, Dict[str, Any]]:
        """Run comparison backtest asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._runner.run_comparison_backtest(*args, **kwargs)
        )


# Convenience function for quick backtests
def quick_backtest(
    model_name: str,
    seasons: List[int] = None,
    bankroll: float = 10000
) -> Dict[str, Any]:
    """
    Quick backtest function for scripts and notebooks.
    
    Args:
        model_name: Model to backtest
        seasons: List of seasons (default: 2022-2024)
        bankroll: Initial bankroll
    
    Returns:
        Backtest results dict
    """
    if seasons is None:
        seasons = [2022, 2023, 2024]
    
    runner = LabRunner()
    return runner.run_backtest(
        model_name=model_name,
        start_year=min(seasons),
        end_year=max(seasons),
        initial_bankroll=bankroll
    )


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    runner = LabRunner()
    
    print("Available models:", runner.get_available_models())
    print("Available seasons:", runner.get_available_seasons())
    
    # Run a backtest
    if runner.get_available_models():
        result = runner.run_backtest(
            model_name=runner.get_available_models()[0],
            start_year=2022,
            end_year=2023,
            initial_bankroll=10000
        )
        print("\nBacktest result:")
        print(f"  Model: {result.get('model_name')}")
        print(f"  ROI: {result.get('metrics', {}).get('roi', 0):.2f}%")
        print(f"  Win Rate: {result.get('metrics', {}).get('win_rate', 0):.1f}%")

