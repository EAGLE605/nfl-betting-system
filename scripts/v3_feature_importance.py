"""V3: Feature Importance Analysis

Identify which Next Gen Stats features contribute most to predictions.
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


def load_and_build_features():
    """Load all data and build feature matrix."""
    # Load NGS
    seasons = [2021, 2022, 2023, 2024]
    ngs_passing = nfl.import_ngs_data('passing', seasons)
    ngs_rushing = nfl.import_ngs_data('rushing', seasons)
    ngs_receiving = nfl.import_ngs_data('receiving', seasons)
    
    # QB metrics
    qb_stats = ngs_passing.groupby(['season', 'week', 'team_abbr']).agg({
        'avg_time_to_throw': 'mean',
        'aggressiveness': 'mean',
        'avg_completed_air_yards': 'mean',
        'avg_air_yards_differential': 'mean',
        'completion_percentage': 'mean',
    }).reset_index()
    qb_stats.columns = ['season', 'week', 'team', 'qb_time_to_throw',
                        'qb_aggressiveness', 'qb_air_yards', 'qb_air_diff', 'qb_comp_pct']
    
    # RB metrics
    rb_stats = ngs_rushing.groupby(['season', 'week', 'team_abbr']).agg({
        'efficiency': 'mean',
        'percent_attempts_gte_eight_defenders': 'mean',
        'avg_time_to_los': 'mean',
        'avg_rush_yards': 'mean',
    }).reset_index()
    rb_stats.columns = ['season', 'week', 'team', 'rb_efficiency',
                        'rb_stacked_box_pct', 'rb_time_to_los', 'rb_ypc']
    
    # WR metrics
    wr_stats = ngs_receiving.groupby(['season', 'week', 'team_abbr']).agg({
        'avg_cushion': 'mean',
        'avg_separation': 'mean',
        'catch_percentage': 'mean',
    }).reset_index()
    wr_stats.columns = ['season', 'week', 'team', 'wr_cushion',
                        'wr_separation', 'wr_catch_pct']
    
    # Merge all NGS
    team_ngs = qb_stats.merge(rb_stats, on=['season', 'week', 'team'], how='outer')
    team_ngs = team_ngs.merge(wr_stats, on=['season', 'week', 'team'], how='outer')
    team_ngs = team_ngs.sort_values(['team', 'season', 'week'])
    
    # Create rolling averages
    ngs_cols = ['qb_time_to_throw', 'qb_aggressiveness', 'qb_air_yards', 'qb_air_diff',
                'qb_comp_pct', 'rb_efficiency', 'rb_stacked_box_pct', 'rb_time_to_los',
                'rb_ypc', 'wr_cushion', 'wr_separation', 'wr_catch_pct']
    
    for col in ngs_cols:
        if col in team_ngs.columns:
            team_ngs[f'{col}_roll'] = team_ngs.groupby('team')[col].transform(
                lambda x: x.shift(1).rolling(3, min_periods=1).mean()
            )
    
    # Load games
    pbp = pd.read_parquet(DATA_DIR / "pbp_4seasons.parquet")
    games = pbp.groupby(['game_id', 'season', 'week', 'home_team', 'away_team']).agg({
        'total_home_score': 'max',
        'total_away_score': 'max',
    }).reset_index()
    games.columns = ['game_id', 'season', 'week', 'home_team', 'away_team',
                     'home_score', 'away_score']
    games = games.dropna()
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)
    
    # Load EPA
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
    
    # Build feature matrix
    roll_cols = [c for c in team_ngs.columns if c.endswith('_roll')]
    
    home_ngs = team_ngs[['season', 'week', 'team'] + roll_cols].copy()
    home_ngs.columns = ['season', 'week', 'home_team'] + [f'home_{c}' for c in roll_cols]
    
    away_ngs = team_ngs[['season', 'week', 'team'] + roll_cols].copy()
    away_ngs.columns = ['season', 'week', 'away_team'] + [f'away_{c}' for c in roll_cols]
    
    df = games.merge(home_ngs, on=['season', 'week', 'home_team'], how='left')
    df = df.merge(away_ngs, on=['season', 'week', 'away_team'], how='left')
    
    # EPA
    home_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'home_team', 'epa_roll': 'home_epa'})
    away_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'away_team', 'epa_roll': 'away_epa'})
    
    df = df.merge(home_epa, on=['game_id', 'home_team'], how='left')
    df = df.merge(away_epa, on=['game_id', 'away_team'], how='left')
    
    # Create differentials
    df['epa_diff'] = df['home_epa'].fillna(0) - df['away_epa'].fillna(0)
    
    for col in roll_cols:
        home_col = f'home_{col}'
        away_col = f'away_{col}'
        if home_col in df.columns and away_col in df.columns:
            df[f'diff_{col}'] = df[home_col].fillna(0) - df[away_col].fillna(0)
    
    return df


def analyze_feature_importance():
    """Analyze which features matter most."""
    print("=" * 70)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("=" * 70)
    
    df = load_and_build_features()
    df = df[df['week'] >= 4].copy()
    
    # All differential features
    diff_cols = [c for c in df.columns if c.startswith('diff_')]
    all_features = ['epa_diff'] + diff_cols
    available = [f for f in all_features if f in df.columns]
    
    print(f"\nFeatures to analyze: {len(available)}")
    for f in available:
        print(f"  - {f}")
    
    # Train on 2021-2023, test on 2024
    train = df[df['season'] < 2024].dropna(subset=['home_win'])
    test = df[df['season'] == 2024].dropna(subset=['home_win'])
    
    X_train = train[available].fillna(0)
    X_test = test[available].fillna(0)
    y_train = train['home_win']
    y_test = test['home_win']
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    
    # Train model
    model = GradientBoostingClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
    )
    model.fit(X_train_s, y_train)
    
    # Feature importance
    print("\n" + "=" * 70)
    print("FEATURE IMPORTANCE (GBM)")
    print("=" * 70)
    
    importance = pd.DataFrame({
        'feature': available,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for _, row in importance.iterrows():
        bar = '█' * int(row['importance'] * 50)
        print(f"{row['feature']:<30} {row['importance']:.3f} {bar}")
    
    # Try different feature combinations
    print("\n" + "=" * 70)
    print("FEATURE COMBINATION TESTS")
    print("=" * 70)
    
    # Top 5 features
    top_5 = importance.head(5)['feature'].tolist()
    # Top 3 features
    top_3 = importance.head(3)['feature'].tolist()
    
    combinations = {
        'all_features': available,
        'top_5': top_5,
        'top_3': top_3,
        'epa_only': ['epa_diff'],
        'qb_metrics': [f for f in available if 'qb_' in f] + ['epa_diff'],
        'wr_metrics': [f for f in available if 'wr_' in f] + ['epa_diff'],
        'rb_metrics': [f for f in available if 'rb_' in f] + ['epa_diff'],
    }
    
    results = []
    
    for name, features in combinations.items():
        avail = [f for f in features if f in df.columns]
        if len(avail) == 0:
            continue
            
        X_train_sub = train[avail].fillna(0)
        X_test_sub = test[avail].fillna(0)
        
        scaler = StandardScaler()
        X_train_sub_s = scaler.fit_transform(X_train_sub)
        X_test_sub_s = scaler.transform(X_test_sub)
        
        model = GradientBoostingClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
        )
        model.fit(X_train_sub_s, y_train)
        
        y_prob = model.predict_proba(X_test_sub_s)[:, 1]
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
            'name': name,
            'n_features': len(avail),
            'accuracy': acc,
            'hc_accuracy': hc_acc,
            'hc_n': hc_n,
            'hc_roi': hc_roi,
        })
        
        print(f"\n{name} ({len(avail)} features):")
        print(f"  Overall: {acc:.1%}")
        print(f"  High-Conf: {hc_acc:.1%} (n={hc_n}), ROI={hc_roi:+.1f}%")
    
    # Summary
    print("\n" + "=" * 70)
    print("BEST CONFIGURATIONS")
    print("=" * 70)
    
    results_df = pd.DataFrame(results).sort_values('hc_roi', ascending=False)
    
    for _, row in results_df.head(5).iterrows():
        print(f"\n{row['name']}:")
        print(f"  HC Accuracy: {row['hc_accuracy']:.1%}")
        print(f"  HC ROI: {row['hc_roi']:+.1f}%")
        print(f"  HC Games: {int(row['hc_n'])}")
    
    return importance, results_df


if __name__ == "__main__":
    importance, results = analyze_feature_importance()
