"""Test Parlay Performance by Type and Leg Count

Using validated moneyline model (65.6% HC accuracy), simulate parlay outcomes.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from itertools import combinations
import nfl_data_py as nfl
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/user/nfl-betting-system/data/raw")


def load_model_predictions():
    """Load data and generate model predictions for all games."""
    # Load PBP
    pbp = pd.read_parquet(DATA_DIR / "pbp_4seasons.parquet")
    
    # Games
    games = pbp.groupby(['game_id', 'season', 'week', 'home_team', 'away_team']).agg({
        'total_home_score': 'max',
        'total_away_score': 'max',
    }).reset_index()
    games.columns = ['game_id', 'season', 'week', 'home_team', 'away_team', 'home_score', 'away_score']
    games = games.dropna()
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)
    
    # EPA
    team_epa = pbp[pbp['play_type'].isin(['pass', 'run']) & pbp['epa'].notna()].groupby(
        ['game_id', 'posteam']
    )['epa'].mean().reset_index()
    team_epa.columns = ['game_id', 'team', 'epa']
    
    game_info = games[['game_id', 'season', 'week']].drop_duplicates()
    team_epa = team_epa.merge(game_info, on='game_id')
    team_epa = team_epa.sort_values(['team', 'season', 'week'])
    team_epa['epa_roll'] = team_epa.groupby('team')['epa'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).mean()
    )
    
    # NGS rushing
    ngs_rushing = nfl.import_ngs_data('rushing', [2021, 2022, 2023, 2024])
    rb_stats = ngs_rushing.groupby(['season', 'week', 'team_abbr']).agg({
        'efficiency': 'mean',
        'percent_attempts_gte_eight_defenders': 'mean',
        'avg_time_to_los': 'mean',
        'avg_rush_yards': 'mean',
    }).reset_index()
    rb_stats.columns = ['season', 'week', 'team', 'rb_efficiency', 'rb_stacked_box_pct', 'rb_time_to_los', 'rb_ypc']
    rb_stats = rb_stats.sort_values(['team', 'season', 'week'])
    for col in ['rb_efficiency', 'rb_stacked_box_pct', 'rb_time_to_los', 'rb_ypc']:
        rb_stats[f'{col}_roll'] = rb_stats.groupby('team')[col].transform(
            lambda x: x.shift(1).rolling(3, min_periods=1).mean()
        )
    
    # Build features
    roll_cols = ['rb_efficiency_roll', 'rb_stacked_box_pct_roll', 'rb_time_to_los_roll', 'rb_ypc_roll']
    
    home_rb = rb_stats[['season', 'week', 'team'] + roll_cols].copy()
    home_rb.columns = ['season', 'week', 'home_team'] + [f'home_{c}' for c in roll_cols]
    
    away_rb = rb_stats[['season', 'week', 'team'] + roll_cols].copy()
    away_rb.columns = ['season', 'week', 'away_team'] + [f'away_{c}' for c in roll_cols]
    
    df = games.merge(home_rb, on=['season', 'week', 'home_team'], how='left')
    df = df.merge(away_rb, on=['season', 'week', 'away_team'], how='left')
    
    home_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'home_team', 'epa_roll': 'home_epa'})
    away_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'away_team', 'epa_roll': 'away_epa'})
    
    df = df.merge(home_epa, on=['game_id', 'home_team'], how='left')
    df = df.merge(away_epa, on=['game_id', 'away_team'], how='left')
    
    # Differentials
    df['epa_diff'] = df['home_epa'].fillna(0) - df['away_epa'].fillna(0)
    for col in roll_cols:
        df[f'diff_{col}'] = df[f'home_{col}'].fillna(0) - df[f'away_{col}'].fillna(0)
    
    df = df[df['week'] >= 4].copy()
    
    return df


def generate_predictions(df):
    """Generate walk-forward predictions."""
    features = ['epa_diff', 'diff_rb_efficiency_roll', 'diff_rb_stacked_box_pct_roll',
                'diff_rb_time_to_los_roll', 'diff_rb_ypc_roll']
    
    all_preds = []
    
    for test_year in [2023, 2024]:
        train = df[df['season'] < test_year].dropna(subset=['home_win'])
        test = df[df['season'] == test_year].dropna(subset=['home_win'])
        
        X_train = train[features].fillna(0)
        X_test = test[features].fillna(0)
        y_train = train['home_win']
        
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        
        model = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
        model.fit(X_train_s, y_train)
        
        y_prob = model.predict_proba(X_test_s)[:, 1]
        
        preds = test[['game_id', 'season', 'week', 'home_team', 'away_team', 'home_win']].copy()
        preds['prob'] = y_prob
        preds['confidence'] = np.maximum(y_prob, 1 - y_prob)
        preds['pick_home'] = (y_prob > 0.5).astype(int)
        preds['correct'] = (preds['pick_home'] == preds['home_win']).astype(int)
        
        all_preds.append(preds)
    
    return pd.concat(all_preds, ignore_index=True)


def simulate_parlays(preds, n_legs, n_simulations=10000, conf_threshold=0.62):
    """Simulate parlay performance."""
    # Filter to high-confidence picks
    hc_preds = preds[preds['confidence'] >= conf_threshold].copy()
    
    if len(hc_preds) < n_legs:
        return None
    
    # Group by week
    weeks = hc_preds.groupby(['season', 'week'])
    
    parlay_results = []
    
    for (season, week), week_games in weeks:
        if len(week_games) < n_legs:
            continue
        
        # All possible parlays of n_legs from this week
        game_indices = week_games.index.tolist()
        
        if len(game_indices) > 10:
            # Sample combinations if too many
            sampled_combos = []
            for _ in range(min(50, len(list(combinations(game_indices, n_legs))))):
                combo = tuple(sorted(np.random.choice(game_indices, n_legs, replace=False)))
                if combo not in sampled_combos:
                    sampled_combos.append(combo)
        else:
            sampled_combos = list(combinations(game_indices, n_legs))
        
        for combo in sampled_combos:
            legs = week_games.loc[list(combo)]
            all_correct = legs['correct'].all()
            avg_conf = legs['confidence'].mean()
            
            # Calculate parlay odds (simplified: multiply individual odds)
            # At -110, fair prob is 52.4%, so odds are ~1.91
            # For favorites at our confidence levels, assume -150 avg = 1.67 payout
            # For underdogs, assume +130 avg = 2.30 payout
            
            # Simplified: assume each leg pays 1.91 (standard -110)
            payout_multiplier = 1.91 ** n_legs
            
            parlay_results.append({
                'season': season,
                'week': week,
                'n_legs': n_legs,
                'won': int(all_correct),
                'avg_confidence': avg_conf,
                'payout': payout_multiplier if all_correct else 0,
            })
    
    return pd.DataFrame(parlay_results)


def test_all_parlays():
    """Test parlays of different sizes."""
    print("=" * 70)
    print("PARLAY PERFORMANCE TEST")
    print("=" * 70)
    
    print("\nLoading data and generating predictions...")
    df = load_model_predictions()
    preds = generate_predictions(df)
    
    hc_preds = preds[preds['confidence'] >= 0.62]
    print(f"\nHigh-confidence picks: {len(hc_preds)}")
    print(f"HC accuracy: {hc_preds['correct'].mean():.1%}")
    
    print("\n" + "=" * 70)
    print("PARLAY RESULTS BY LEG COUNT")
    print("=" * 70)
    
    results_summary = []
    
    for n_legs in [2, 3, 4, 5, 6]:
        print(f"\n--- {n_legs}-LEG PARLAYS ---")
        
        parlay_results = simulate_parlays(preds, n_legs, conf_threshold=0.62)
        
        if parlay_results is None or len(parlay_results) == 0:
            print(f"  Not enough games for {n_legs}-leg parlays")
            continue
        
        n_parlays = len(parlay_results)
        win_rate = parlay_results['won'].mean()
        avg_payout = parlay_results['payout'].mean()
        
        # ROI: (avg_payout - 1) * 100 (since we bet 1 unit)
        roi = (avg_payout - 1) * 100
        
        # Expected win rate at 65.6% per leg
        expected_win = 0.656 ** n_legs
        
        # Breakeven win rate for this payout
        payout_mult = 1.91 ** n_legs
        breakeven = 1 / payout_mult
        
        print(f"  Parlays tested: {n_parlays}")
        print(f"  Win rate: {win_rate:.1%}")
        print(f"  Expected (at 65.6%/leg): {expected_win:.1%}")
        print(f"  Breakeven needed: {breakeven:.1%}")
        print(f"  Payout multiplier: {payout_mult:.1f}x")
        print(f"  ROI: {roi:+.1f}%")
        
        if win_rate > breakeven:
            print(f"  *** PROFITABLE ***")
        
        results_summary.append({
            'legs': n_legs,
            'n_parlays': n_parlays,
            'win_rate': win_rate,
            'expected_win': expected_win,
            'breakeven': breakeven,
            'payout': payout_mult,
            'roi': roi,
            'profitable': win_rate > breakeven,
        })
    
    # Summary table
    print("\n" + "=" * 70)
    print("PARLAY SUMMARY")
    print("=" * 70)
    
    summary_df = pd.DataFrame(results_summary)
    print(f"\n{'Legs':<6} {'Win%':<8} {'Expected':<10} {'Breakeven':<10} {'Payout':<8} {'ROI':<10} {'Profitable'}")
    print("-" * 70)
    for _, row in summary_df.iterrows():
        status = "YES" if row['profitable'] else "NO"
        print(f"{int(row['legs']):<6} {row['win_rate']:.1%}    {row['expected_win']:.1%}      {row['breakeven']:.1%}      {row['payout']:.1f}x     {row['roi']:+.1f}%     {status}")
    
    # By confidence level
    print("\n" + "=" * 70)
    print("2-LEG PARLAYS BY CONFIDENCE THRESHOLD")
    print("=" * 70)
    
    for conf in [0.55, 0.60, 0.62, 0.65, 0.70]:
        parlay_results = simulate_parlays(preds, 2, conf_threshold=conf)
        if parlay_results is None or len(parlay_results) == 0:
            continue
        
        win_rate = parlay_results['won'].mean()
        roi = (parlay_results['payout'].mean() - 1) * 100
        n = len(parlay_results)
        
        print(f"  Conf >= {conf:.0%}: Win={win_rate:.1%}, ROI={roi:+.1f}%, N={n}")
    
    return summary_df


if __name__ == "__main__":
    results = test_all_parlays()
