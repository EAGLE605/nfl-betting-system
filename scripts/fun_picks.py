#!/usr/bin/env python3
"""
🏈 NFL FUN PICKS - High Accuracy + Entertainment

Priority: HIT RATE > ROI > FUN > CLV

This is for BEER MONEY entertainment betting.
Uses documented 60%+ win rate angles + exciting parlays.

Usage:
    python scripts/fun_picks.py           # This week's picks
    python scripts/fun_picks.py --train   # Train model first

Features:
- 🎯 High accuracy angles (71% divisional dogs, etc.)
- 🎰 Smart parlays (2-3 legs with edge)
- 🏈 TD props for SGPs
- 📊 Clean visual output

GAMBLE RESPONSIBLY. This is for fun.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="NFL Fun Picks - High Accuracy + Entertainment")
    parser.add_argument('--train', action='store_true', help="Train model first")
    parser.add_argument('--download', action='store_true', help="Download fresh data")
    args = parser.parse_args()

    print_banner()

    # Setup
    from src.data.nfl_data import setup_data_directory
    setup_data_directory()

    # Get data and model
    if args.download or args.train:
        games, model, feature_cols = setup_with_fresh_data(args.train)
    else:
        games, model, feature_cols = setup_from_cache()

    if games is None or len(games) == 0:
        print("\n❌ No games found. Try --download to get fresh data.")
        return 1

    # Generate all content
    print("\n🔄 Analyzing games...")

    # 1. High accuracy angle picks
    accuracy_picks = generate_accuracy_picks(games)

    # 2. Model-based picks with edges
    if model is not None:
        model_picks = generate_model_picks(games, model, feature_cols)
    else:
        model_picks = games

    # 3. Parlays
    parlays = generate_fun_parlays(model_picks)

    # 4. Print everything
    print_full_card(accuracy_picks, model_picks, parlays)

    # 5. Save outputs
    save_all_outputs(accuracy_picks, model_picks, parlays)

    return 0


def print_banner():
    """Print the fun banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║  🏈  NFL FUN PICKS  🏈                                            ║
║  High Accuracy Angles + Smart Parlays + Entertainment             ║
║  ─────────────────────────────────────────────────────────────    ║
║  Priority: HIT RATE > ROI > FUN                                   ║
║  For beer money bets. Gamble responsibly!                         ║
╚═══════════════════════════════════════════════════════════════════╝
    """)


def setup_with_fresh_data(train: bool):
    """Download data and optionally train model."""
    from src.data.nfl_data import (
        download_schedules, download_pbp, calculate_team_stats,
        prepare_features, get_current_week_games
    )

    current_year = datetime.now().year
    current_month = datetime.now().month
    if current_month >= 9:
        seasons = list(range(2022, current_year + 1))
    else:
        seasons = list(range(2022, current_year))

    logger.info(f"📥 Downloading data for {seasons}...")

    try:
        schedules = download_schedules(seasons)
        logger.info(f"✅ Got {len(schedules)} games")
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        return None, None, None

    games = get_current_week_games()

    if train:
        # Quick train
        try:
            pbp = download_pbp(seasons[-2:])
            team_stats = calculate_team_stats(pbp)
            features = prepare_features(schedules, team_stats)
            model, feature_cols = quick_train(features)
            return games, model, feature_cols
        except Exception as e:
            logger.warning(f"Training skipped: {e}")
            return games, None, None

    return games, None, None


def setup_from_cache():
    """Load from cache if available."""
    from src.data.nfl_data import get_current_week_games

    try:
        games = get_current_week_games()
    except Exception as e:
        logger.warning(f"Could not get games: {e}")
        games = pd.DataFrame()

    # Try to load model
    model, feature_cols = None, None
    if Path("models/nfl_model.json").exists():
        try:
            from src.models.xgboost_model import XGBoostNFLModel
            model = XGBoostNFLModel.load("models/nfl_model.json")
            with open("models/feature_cols.json") as f:
                feature_cols = json.load(f)
            logger.info("✅ Loaded trained model")
        except Exception as e:
            logger.warning(f"Could not load model: {e}")

    return games, model, feature_cols


def quick_train(features_df):
    """Quick model training."""
    from src.models.xgboost_model import XGBoostNFLModel

    max_season = features_df['season'].max()
    train_df = features_df[features_df['season'] < max_season]
    val_df = features_df[features_df['season'] == max_season]

    exclude = ['game_id', 'gameday', 'home_team', 'away_team', 'season', 'week',
               'home_score', 'away_score', 'target', 'result', 'total', 'game_type',
               'spread_line', 'total_line']

    feature_cols = [c for c in train_df.columns
                    if c not in exclude and train_df[c].dtype in ['int64', 'float64']]

    X_train = train_df[feature_cols].fillna(0)
    y_train = train_df['target']
    X_val = val_df[feature_cols].fillna(0)
    y_val = val_df['target']

    model = XGBoostNFLModel({'params': {'n_estimators': 100, 'max_depth': 4}})
    model.train(X_train, y_train, X_val, y_val)
    model.save("models/nfl_model.json")

    with open("models/feature_cols.json", "w") as f:
        json.dump(feature_cols, f)

    return model, feature_cols


def generate_accuracy_picks(games_df):
    """Generate picks from high-accuracy angles."""
    from src.picks.high_accuracy_picks import HighAccuracyEngine

    engine = HighAccuracyEngine()

    for idx, row in games_df.iterrows():
        engine.analyze_game(
            game_id=row.get('game_id', f'game_{idx}'),
            home_team=row['home_team'],
            away_team=row['away_team'],
            spread=row.get('spread_line', 0),
            total=row.get('total_line', 45),
            week=row.get('week', 1),
        )

    return engine.get_best_picks()


def generate_model_picks(games_df, model, feature_cols):
    """Generate model-based picks."""
    games = games_df.copy()

    # Add features
    games['home_field'] = 1
    games['week_normalized'] = games['week'] / 18

    for col in feature_cols:
        if col not in games.columns:
            games[col] = 0

    X = games[feature_cols].fillna(0)
    probs = model.predict_proba(X)

    games['model_home_prob'] = probs
    games['model_away_prob'] = 1 - probs

    # Market implied
    if 'spread_line' in games.columns:
        games['market_prob'] = 0.5 - (games['spread_line'] * 0.03)
        games['edge'] = games['model_home_prob'] - games['market_prob']
    else:
        games['edge'] = 0

    # Confidence
    games['confidence_score'] = games.apply(
        lambda r: min(100, 50 + abs(r['edge']) * 300 + (10 if abs(r.get('spread_line', 0)) > 7 else 0)),
        axis=1
    )

    return games


def generate_fun_parlays(picks_df):
    """Generate fun parlays."""
    from src.picks.parlay_builder import ParlayBuilder

    builder = ParlayBuilder(min_edge=0.02, max_legs=3)
    parlays = {}

    # Best 2-leg (safest)
    safe = builder.build_conservative_parlay(picks_df)
    if safe:
        parlays['safe_2leg'] = safe

    # Standard 3-leg
    std = builder.build_best_parlay(picks_df, num_legs=3)
    if std:
        parlays['standard_3leg'] = std

    # Underdog parlay (fun longshot)
    dog = builder.build_underdog_parlay(picks_df)
    if dog:
        parlays['underdog_fun'] = dog

    return parlays


def print_full_card(accuracy_picks, model_picks, parlays):
    """Print the complete card."""
    print("\n")
    print("=" * 70)
    print("🎯 TODAY'S CARD")
    print("=" * 70)

    # Section 1: High Accuracy Picks
    if accuracy_picks:
        print("\n" + "─" * 70)
        print("🔥 HIGH ACCURACY ANGLES (60%+ documented win rates)")
        print("─" * 70)

        for pick in accuracy_picks:
            rate_bar = "█" * int(pick.historical_rate * 10)
            print(f"""
⭐ {pick.game}
   PICK: {pick.pick}
   ANGLE: {pick.angle_name.replace('_', ' ').title()}
   RATE: {pick.historical_rate:.0%} {rate_bar}
   DATA: {pick.sample_info}
   UNITS: {pick.recommended_units}
""")

    # Section 2: Model Picks with Edge
    if 'edge' in model_picks.columns:
        edge_picks = model_picks[model_picks['edge'].abs() > 0.05].sort_values('edge', key=abs, ascending=False)

        if len(edge_picks) > 0:
            print("\n" + "─" * 70)
            print("📊 MODEL EDGE PICKS")
            print("─" * 70)

            for _, row in edge_picks.head(5).iterrows():
                home_prob = row['model_home_prob']
                pick_team = row['home_team'] if home_prob > 0.5 else row['away_team']
                spread = row.get('spread_line', 0)
                pick_spread = spread if home_prob > 0.5 else -spread

                edge_emoji = "🟢" if row['edge'] > 0 else "🔴"

                print(f"""
{edge_emoji} {row['away_team']} @ {row['home_team']}
   PICK: {pick_team} {pick_spread:+.1f}
   MODEL: {home_prob:.0%} home win
   EDGE: {row['edge']:+.1%} vs market
""")

    # Section 3: Parlays
    if parlays:
        print("\n" + "─" * 70)
        print("🎰 PARLAYS")
        print("─" * 70)

        for name, parlay in parlays.items():
            name_clean = name.replace('_', ' ').title()
            print(f"\n📋 {name_clean}")
            print(f"   Odds: {parlay.combined_odds:+d}")
            print(f"   Legs:")
            for i, leg in enumerate(parlay.legs, 1):
                print(f"      {i}. {leg.pick} ({leg.game})")
            print(f"   Risk: {parlay.risk_level} | Units: {parlay.recommended_units}")

    # Footer
    print("\n" + "=" * 70)
    print("📌 REMEMBER:")
    print("   • High accuracy angles are historically proven (not guaranteed)")
    print("   • Parlays are for fun - high variance")
    print("   • Track your results to see what works for YOU")
    print("   • This is entertainment. Gamble responsibly!")
    print("=" * 70)


def save_all_outputs(accuracy_picks, model_picks, parlays):
    """Save outputs to files."""
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime('%Y%m%d')

    # Save accuracy picks
    if accuracy_picks:
        picks_data = [{
            'game': p.game,
            'pick': p.pick,
            'angle': p.angle_name,
            'rate': p.historical_rate,
            'units': p.recommended_units,
        } for p in accuracy_picks]
        pd.DataFrame(picks_data).to_csv(output_dir / f"accuracy_picks_{date_str}.csv", index=False)

    # Save model picks
    if len(model_picks) > 0:
        cols = ['home_team', 'away_team', 'spread_line', 'model_home_prob', 'edge']
        save_cols = [c for c in cols if c in model_picks.columns]
        model_picks[save_cols].to_csv(output_dir / f"model_picks_{date_str}.csv", index=False)

    logger.info(f"✅ Saved outputs to {output_dir}")


if __name__ == "__main__":
    sys.exit(main())
