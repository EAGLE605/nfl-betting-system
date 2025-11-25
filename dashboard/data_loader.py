"""
Dashboard Data Loader

Loads real data from files, APIs, and models for the dashboard.
No more hardcoded fake data!
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"


def load_backtest_metrics() -> Dict[str, Any]:
    """
    Load backtest metrics from JSON file.

    Returns:
        Dict with backtest metrics or empty dict on error
    """
    metrics_file = REPORTS_DIR / "backtest_metrics.json"
    try:
        if metrics_file.exists():
            with open(metrics_file, "r") as f:
                metrics = json.load(f)
                logger.debug(f"Loaded backtest metrics: {metrics}")
                return metrics
    except Exception as e:
        logger.error(f"Error loading backtest metrics: {e}")

    return {
        "total_bets": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "roi": 0.0,
        "total_profit": 0.0,
        "max_drawdown": 0.0,
        "sharpe_ratio": 0.0,
        "final_bankroll": 500.0,
    }


def load_bet_history() -> pd.DataFrame:
    """
    Load bet history from CSV file.

    Returns:
        DataFrame with bet history or empty DataFrame on error
    """
    history_file = REPORTS_DIR / "bet_history.csv"
    try:
        if history_file.exists():
            df = pd.read_csv(history_file)
            df["gameday"] = pd.to_datetime(df["gameday"])
            logger.debug(f"Loaded {len(df)} historical bets")
            return df
    except Exception as e:
        logger.error(f"Error loading bet history: {e}")

    return pd.DataFrame()


def load_daily_picks() -> List[Dict[str, Any]]:
    """
    Load the most recent daily picks.

    Returns:
        List of pick dictionaries
    """
    try:
        # Find most recent picks file
        picks_files = list(REPORTS_DIR.glob("daily_picks_*.json"))
        if picks_files:
            # Sort by modification time, newest first
            picks_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_file = picks_files[0]

            with open(latest_file, "r") as f:
                data = json.load(f)
                picks = data.get("picks", [])
                logger.debug(f"Loaded {len(picks)} daily picks from {latest_file.name}")
                return picks
    except Exception as e:
        logger.error(f"Error loading daily picks: {e}")

    return []


def get_live_odds() -> List[Dict[str, Any]]:
    """
    Fetch live odds from The Odds API.

    Returns:
        List of games with odds from multiple sportsbooks
    """
    try:
        import sys

        sys.path.insert(0, str(PROJECT_ROOT))
        from agents.api_integrations import TheOddsAPI

        api = TheOddsAPI()
        if api.api_key:
            odds = api.get_nfl_odds()
            logger.info(f"Fetched {len(odds)} games with live odds")
            return odds
    except Exception as e:
        logger.warning(f"Could not fetch live odds: {e}")

    return []


def get_espn_scoreboard() -> Dict[str, Any]:
    """
    Fetch current scoreboard from ESPN.

    Returns:
        Dict with scoreboard data
    """
    try:
        import sys

        sys.path.insert(0, str(PROJECT_ROOT))
        from agents.api_integrations import ESPNAPI

        api = ESPNAPI()
        scoreboard = api.get_scoreboard(2024)
        if scoreboard and "events" in scoreboard:
            logger.info(f"Fetched {len(scoreboard['events'])} games from ESPN")
            return scoreboard
    except Exception as e:
        logger.warning(f"Could not fetch ESPN scoreboard: {e}")

    return {}


def calculate_season_record(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate season record from bet history.

    Args:
        df: Bet history DataFrame

    Returns:
        Dict with season statistics
    """
    if df.empty:
        return {"wins": 0, "losses": 0, "units": 0.0, "roi": 0.0}

    # Filter to current season (2024)
    current_year = datetime.now().year
    season_df = df[df["gameday"].dt.year >= current_year - 1]

    wins = len(season_df[season_df["result"] == "win"])
    losses = len(season_df[season_df["result"] == "loss"])

    # Calculate units (assuming $100 per unit)
    if not season_df.empty:
        total_profit = season_df["profit"].sum()
        total_wagered = season_df["bet_size"].sum()
        units = total_profit / 10  # Normalize to units
        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0.0
    else:
        units = 0.0
        roi = 0.0

    return {
        "wins": wins,
        "losses": losses,
        "units": round(units, 1),
        "roi": round(roi, 1),
    }


def get_weekly_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate weekly performance from bet history.

    Args:
        df: Bet history DataFrame

    Returns:
        DataFrame with weekly stats
    """
    if df.empty:
        return pd.DataFrame()

    # Group by week
    df["week"] = df["gameday"].dt.isocalendar().week
    df["year"] = df["gameday"].dt.year

    weekly = (
        df.groupby(["year", "week"])
        .agg(
            {
                "result": lambda x: (x == "win").sum(),  # wins
                "game_id": "count",  # total bets
                "profit": "sum",
                "bet_size": "sum",
            }
        )
        .reset_index()
    )

    weekly.columns = ["Year", "Week", "Wins", "Total", "Profit", "Wagered"]
    weekly["Losses"] = weekly["Total"] - weekly["Wins"]
    weekly["ROI"] = (weekly["Profit"] / weekly["Wagered"] * 100).round(1)
    weekly["Units"] = (weekly["Profit"] / 10).round(1)

    return weekly.sort_values(["Year", "Week"], ascending=[True, True])


def get_current_week() -> int:
    """Get current NFL week number (approximate)."""
    today = datetime.now()
    # NFL season starts around September 5th
    season_start = datetime(today.year, 9, 5)
    if today < season_start:
        # Off-season
        return 18

    days_since_start = (today - season_start).days
    week = min(18, max(1, (days_since_start // 7) + 1))
    return week


def format_picks_for_display(
    picks: List[Dict], bet_history: pd.DataFrame
) -> List[Dict]:
    """
    Format picks for dashboard display, enriching with historical data.

    Args:
        picks: Raw picks from daily picks file
        bet_history: Historical bet data

    Returns:
        List of formatted pick dictionaries
    """
    formatted = []

    for pick in picks:
        if not pick.get("pick"):
            continue  # Skip picks without a selection

        # Extract game info
        game = pick.get("game", "Unknown")

        # Determine teams
        if "@" in game:
            away, home = game.split(" @ ")
        elif "vs" in game.lower():
            away, home = game.lower().split(" vs ")
            away = away.strip().title()
            home = home.strip().title()
        else:
            away, home = "Away", "Home"

        # Get odds in American format
        line = pick.get("line", 0)
        if isinstance(line, int) or isinstance(line, float):
            if line > 0:
                odds_str = f"+{int(line)}"
            else:
                odds_str = str(int(line))
        else:
            odds_str = str(line)

        # Parse edge
        edge_str = pick.get("edge", "0%")
        if isinstance(edge_str, str):
            edge = float(edge_str.replace("%", "").replace("+", ""))
        else:
            edge = float(edge_str)

        # Parse confidence
        conf_str = pick.get("confidence", "0%")
        if isinstance(conf_str, str):
            conf = float(conf_str.replace("%", ""))
        else:
            conf = float(conf_str)

        # Parse win probability - this is the REAL confidence
        win_prob_str = pick.get("win_probability", "50%")
        if isinstance(win_prob_str, str):
            win_prob = float(win_prob_str.replace("%", ""))
        else:
            win_prob = float(win_prob_str) * 100

        # CRITICAL: If win_prob is exactly 50%, model failed to predict - mark as invalid
        if abs(win_prob - 50.0) < 0.1:
            # Model didn't actually predict, skip this pick
            continue

        # Use actual model probability as confidence base
        conf = win_prob if conf == 0 else conf

        formatted.append(
            {
                "Game": game,
                "Away": away.strip(),
                "Home": home.strip(),
                "Pick": pick.get("pick", ""),
                "Type": pick.get("bet_type", "ML"),
                "Line": "",  # For spread bets
                "Odds": odds_str,
                "Confidence": round(conf, 1),
                "EV": round(edge, 1),
                "Result": "P",  # Pending
                "Book": pick.get("best_book", ""),
                "Reasoning": pick.get("reasoning", []),
            }
        )

    return formatted


def get_model_info() -> Dict[str, Any]:
    """
    Get information about available models.

    Returns:
        Dict with model information
    """
    models = {}

    model_files = [
        ("xgboost_favorites_only.pkl", "Favorites Specialist", True),
        ("xgboost_improved.pkl", "XGBoost Improved", False),
        ("xgboost_evolved_75pct.pkl", "XGBoost Evolved", False),
        ("calibrated_model.pkl", "Calibrated Ensemble", False),
        ("lightgbm_improved.pkl", "LightGBM", False),
    ]

    for filename, display_name, is_primary in model_files:
        filepath = MODELS_DIR / filename
        if filepath.exists():
            stat = filepath.stat()
            models[filename] = {
                "name": display_name,
                "file": filename,
                "exists": True,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "is_primary": is_primary,
            }

    return models


def run_backtest() -> Dict[str, Any]:
    """
    Run the backtest script and return results.

    Returns:
        Dict with backtest results and any error messages
    """
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "backtest.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=120,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(PROJECT_ROOT)},
        )

        if result.returncode == 0:
            # Reload metrics
            metrics = load_backtest_metrics()
            return {
                "success": True,
                "metrics": metrics,
                "output": result.stdout,
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Unknown error",
                "output": result.stdout,
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Backtest timed out after 120 seconds",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def generate_predictions() -> Dict[str, Any]:
    """
    Generate new predictions using the prediction engine.

    Returns:
        Dict with prediction results
    """
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_daily_picks.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=180,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(PROJECT_ROOT)},
        )

        if result.returncode == 0:
            picks = load_daily_picks()
            return {
                "success": True,
                "picks": picks,
                "output": result.stdout,
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Unknown error",
                "output": result.stdout,
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Prediction generation timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
