"""Test Spread Predictions (ATS - Against The Spread)

Does the model predict if the favorite covers?
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import nfl_data_py as nfl
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/user/nfl-betting-system/data/raw")


def load_data_with_spreads():
    """Load games with spread lines."""
    # Load schedules with spreads
    schedules = nfl.import_schedules([2021, 2022, 2023, 2024])
    schedules = schedules[
        (schedules['game_type'] == 'REG') &
        (schedules['home_score'].notna())
    ].copy()
    
    # Calculate if home team covered
    schedules['home_margin'] = schedules['home_score'] - schedules['away_score']
    # spread_line is negative when home is favored
    # Home covers if: home_margin > -spread_line (or home_margin + spread_line > 0)
    schedules['home_covered'] = (schedules['home_margin'] + schedules['spread_line']) > 0
    schedules['home_covered'] = schedules['home_covered'].astype(int)
    
    # Load PBP for EPA
    pbp = pd.read_parquet(DATA_DIR / "pbp_4seasons.parquet")
    
    # Team EPA
    team_epa = pbp[pbp['play_type'].isin(['pass', 'run']) & pbp['epa'].notna()].groupby(
        ['game_id', 'posteam']
    )['epa'].mean().reset_index()
    team_epa.columns = ['game_id', 'team', 'epa']
    
    game_info = schedules[['game_id', 'season', 'week']].drop_duplicates()
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
    }).reset_index()
    rb_stats.columns = ['season', 'week', 'team', 'rb_efficiency', 'rb_stacked_box_pct']
    rb_stats = rb_stats.sort_values(['team', 'season', 'week'])
    for col in ['rb_efficiency', 'rb_stacked_box_pct']:
        rb_stats[f'{col}_roll'] = rb_stats.groupby('team')[col].transform(
            lambda x: x.shift(1).rolling(3, min_periods=1).mean()
        )
    
    # Merge features
    home_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'home_team', 'epa_roll': 'home_epa'})
    away_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'away_team', 'epa_roll': 'away_epa'})
    
    df = schedules.merge(home_epa, on=['game_id', 'home_team'], how='left')
    df = df.merge(away_epa, on=['game_id', 'away_team'], how='left')
    
    home_rb = rb_stats[['season', 'week', 'team', 'rb_efficiency_roll', 'rb_stacked_box_pct_roll']].rename(
        columns={'team': 'home_team', 'rb_efficiency_roll': 'home_rb_eff', 'rb_stacked_box_pct_roll': 'home_rb_stacked'})
    away_rb = rb_stats[['season', 'week', 'team', 'rb_efficiency_roll', 'rb_stacked_box_pct_roll']].rename(
        columns={'team': 'away_team', 'rb_efficiency_roll': 'away_rb_eff', 'rb_stacked_box_pct_roll': 'away_rb_stacked'})
    
    df = df.merge(home_rb, on=['season', 'week', 'home_team'], how='left')
    df = df.merge(away_rb, on=['season', 'week', 'away_team'], how='left')
    
    # Create features
    df['epa_diff'] = df['home_epa'].fillna(0) - df['away_epa'].fillna(0)
    df['rb_eff_diff'] = df['home_rb_eff'].fillna(0) - df['away_rb_eff'].fillna(0)
    df['rb_stacked_diff'] = df['home_rb_stacked'].fillna(0) - df['away_rb_stacked'].fillna(0)
    df['spread_abs'] = df['spread_line'].abs()
    df['home_favored'] = (df['spread_line'] < 0).astype(int)
    
    return df


def test_spread_model():
    """Test spread prediction model."""
    print("=" * 70)
    print("SPREAD PREDICTION TEST (ATS)")
    print("=" * 70)
    
    df = load_data_with_spreads()
    df = df[df['week'] >= 4].copy()
    df = df[df['spread_line'].notna()].copy()
    
    print(f"\nTotal games with spreads: {len(df)}")
    print(f"Home cover rate: {df['home_covered'].mean():.1%}")
    
    features = ['epa_diff', 'rb_eff_diff', 'rb_stacked_diff', 'spread_abs', 'home_favored']
    
    results = []
    
    for test_year in [2023, 2024]:
        train = df[df['season'] < test_year].dropna(subset=['home_covered'])
        test = df[df['season'] == test_year].dropna(subset=['home_covered'])
        
        if len(train) < 50 or len(test) < 50:
            continue
        
        X_train = train[features].fillna(0)
        X_test = test[features].fillna(0)
        y_train = train['home_covered']
        y_test = test['home_covered']
        
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        
        model = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
        model.fit(X_train_s, y_train)
        
        y_prob = model.predict_proba(X_test_s)[:, 1]
        y_pred = (y_prob > 0.5).astype(int)
        
        acc = accuracy_score(y_test, y_pred)
        
        # High confidence
        hc_mask = (y_prob > 0.58) | (y_prob < 0.42)
        if hc_mask.sum() > 10:
            hc_acc = accuracy_score(y_test[hc_mask], y_pred[hc_mask])
            hc_n = hc_mask.sum()
            hc_roi = ((y_pred[hc_mask] == y_test.values[hc_mask]).sum() * 0.91 -
                      (y_pred[hc_mask] != y_test.values[hc_mask]).sum()) / hc_n * 100
        else:
            hc_acc, hc_n, hc_roi = 0, 0, 0
        
        results.append({
            'year': test_year, 'accuracy': acc, 'hc_accuracy': hc_acc, 
            'hc_n': hc_n, 'hc_roi': hc_roi
        })
        
        print(f"\n{test_year}:")
        print(f"  Overall: {acc:.1%} ({len(test)} games)")
        print(f"  High-Conf: {hc_acc:.1%} ({hc_n} games), ROI={hc_roi:+.1f}%")
    
    # Summary
    results_df = pd.DataFrame(results)
    total_hc = results_df['hc_n'].sum()
    avg_hc_acc = (results_df['hc_accuracy'] * results_df['hc_n']).sum() / total_hc if total_hc > 0 else 0
    avg_hc_roi = results_df['hc_roi'].mean()
    
    print("\n" + "=" * 70)
    print("SPREAD PREDICTION SUMMARY")
    print("=" * 70)
    print(f"High-Confidence Accuracy: {avg_hc_acc:.1%}")
    print(f"High-Confidence ROI: {avg_hc_roi:+.1f}%")
    print(f"High-Confidence Games: {int(total_hc)}")
    
    return results_df


if __name__ == "__main__":
    results = test_spread_model()
