"""V4: RB-Optimized Model

Best performer: RB metrics + EPA
- 65.3% HC accuracy
- +24.7% ROI

Validate across seasons and optimize confidence threshold.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, brier_score_loss
import nfl_data_py as nfl
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/user/nfl-betting-system/data/raw")
VERSION = "4.0-rb-optimized"


def load_data():
    """Load and prepare all data."""
    seasons = [2021, 2022, 2023, 2024]
    
    # NGS rushing
    ngs_rushing = nfl.import_ngs_data('rushing', seasons)
    
    rb_stats = ngs_rushing.groupby(['season', 'week', 'team_abbr']).agg({
        'efficiency': 'mean',
        'percent_attempts_gte_eight_defenders': 'mean',
        'avg_time_to_los': 'mean',
        'avg_rush_yards': 'mean',
    }).reset_index()
    rb_stats.columns = ['season', 'week', 'team', 'rb_efficiency',
                        'rb_stacked_box_pct', 'rb_time_to_los', 'rb_ypc']
    
    rb_stats = rb_stats.sort_values(['team', 'season', 'week'])
    
    for col in ['rb_efficiency', 'rb_stacked_box_pct', 'rb_time_to_los', 'rb_ypc']:
        rb_stats[f'{col}_roll'] = rb_stats.groupby('team')[col].transform(
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
    games['point_diff'] = games['home_score'] - games['away_score']
    
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
    
    # Create differentials
    df['epa_diff'] = df['home_epa'].fillna(0) - df['away_epa'].fillna(0)
    for col in roll_cols:
        df[f'diff_{col}'] = df[f'home_{col}'].fillna(0) - df[f'away_{col}'].fillna(0)
    
    return df


def run_validation():
    """Run full validation with confidence threshold optimization."""
    print("=" * 70)
    print(f"NFL BETTING MODEL V{VERSION}")
    print("=" * 70)
    
    df = load_data()
    df = df[df['week'] >= 4].copy()
    
    features = ['epa_diff', 'diff_rb_efficiency_roll', 'diff_rb_stacked_box_pct_roll',
                'diff_rb_time_to_los_roll', 'diff_rb_ypc_roll']
    
    print(f"\nFeatures: {features}")
    print(f"Total games: {len(df)}")
    
    # Walk-forward validation
    print("\n" + "=" * 70)
    print("WALK-FORWARD VALIDATION")
    print("=" * 70)
    
    all_predictions = []
    
    for test_year in [2023, 2024]:
        train = df[df['season'] < test_year].dropna(subset=['home_win'])
        test = df[df['season'] == test_year].dropna(subset=['home_win'])
        
        if len(train) < 50 or len(test) < 50:
            continue
        
        X_train = train[features].fillna(0)
        X_test = test[features].fillna(0)
        y_train = train['home_win']
        y_test = test['home_win']
        
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        
        model = GradientBoostingClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
        )
        model.fit(X_train_s, y_train)
        
        y_prob = model.predict_proba(X_test_s)[:, 1]
        
        # Store predictions
        preds = test[['game_id', 'season', 'week', 'home_team', 'away_team', 
                      'home_win', 'point_diff']].copy()
        preds['prob'] = y_prob
        all_predictions.append(preds)
        
        # Basic metrics
        y_pred = (y_prob > 0.5).astype(int)
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n--- {test_year} ---")
        print(f"  Overall Accuracy: {acc:.1%}")
        print(f"  N Games: {len(test)}")
    
    # Combine predictions
    all_preds = pd.concat(all_predictions, ignore_index=True)
    
    # Optimize confidence threshold
    print("\n" + "=" * 70)
    print("CONFIDENCE THRESHOLD OPTIMIZATION")
    print("=" * 70)
    
    best_roi = -100
    best_threshold = 0.58
    
    for threshold in [0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.62, 0.65]:
        hc_mask = (all_preds['prob'] > threshold) | (all_preds['prob'] < (1 - threshold))
        hc = all_preds[hc_mask]
        
        if len(hc) < 20:
            continue
        
        y_pred = (hc['prob'] > 0.5).astype(int)
        y_true = hc['home_win']
        
        correct = (y_pred == y_true)
        acc = correct.mean()
        roi = (correct.sum() * 0.91 - (~correct).sum()) / len(hc) * 100
        
        print(f"\nThreshold {threshold:.2f} (bet when prob > {threshold:.2f} or < {1-threshold:.2f}):")
        print(f"  HC Games: {len(hc)}")
        print(f"  HC Accuracy: {acc:.1%}")
        print(f"  HC ROI: {roi:+.1f}%")
        
        if roi > best_roi:
            best_roi = roi
            best_threshold = threshold
    
    # Best threshold results
    print("\n" + "=" * 70)
    print("OPTIMAL CONFIGURATION")
    print("=" * 70)
    
    hc_mask = (all_preds['prob'] > best_threshold) | (all_preds['prob'] < (1 - best_threshold))
    hc = all_preds[hc_mask]
    
    y_pred = (hc['prob'] > 0.5).astype(int)
    y_true = hc['home_win']
    
    correct = (y_pred == y_true)
    acc = correct.mean()
    roi = (correct.sum() * 0.91 - (~correct).sum()) / len(hc) * 100
    
    print(f"\nBest Threshold: {best_threshold}")
    print(f"High-Confidence Games: {len(hc)}")
    print(f"High-Confidence Accuracy: {acc:.1%}")
    print(f"High-Confidence ROI: {roi:+.1f}%")
    
    # By season
    print("\n--- By Season ---")
    for year in [2023, 2024]:
        year_preds = hc[hc['season'] == year]
        if len(year_preds) > 10:
            y_pred_year = (year_preds['prob'] > 0.5).astype(int)
            y_true_year = year_preds['home_win']
            correct_year = (y_pred_year == y_true_year)
            acc_year = correct_year.mean()
            roi_year = (correct_year.sum() * 0.91 - (~correct_year).sum()) / len(year_preds) * 100
            print(f"  {year}: {acc_year:.1%} ({len(year_preds)} games), ROI={roi_year:+.1f}%")
    
    # By margin of victory
    print("\n--- By Game Closeness ---")
    close_mask = hc['point_diff'].abs() <= 7
    close = hc[close_mask]
    blowout = hc[~close_mask]
    
    if len(close) > 10:
        y_pred_close = (close['prob'] > 0.5).astype(int)
        y_true_close = close['home_win']
        acc_close = (y_pred_close == y_true_close).mean()
        print(f"  Close games (<=7 pts): {acc_close:.1%} ({len(close)} games)")
    
    if len(blowout) > 10:
        y_pred_blowout = (blowout['prob'] > 0.5).astype(int)
        y_true_blowout = blowout['home_win']
        acc_blowout = (y_pred_blowout == y_true_blowout).mean()
        print(f"  Blowouts (>7 pts): {acc_blowout:.1%} ({len(blowout)} games)")
    
    # Statistical significance
    print("\n--- Statistical Significance ---")
    n = len(hc)
    se = np.sqrt(acc * (1 - acc) / n)
    ci_low = acc - 1.96 * se
    ci_high = acc + 1.96 * se
    
    print(f"  95% CI: [{ci_low:.1%}, {ci_high:.1%}]")
    
    # Is it significantly better than 52.4% (break-even at -110)?
    breakeven = 0.524
    z_score = (acc - breakeven) / se
    from scipy import stats
    p_value = 1 - stats.norm.cdf(z_score)
    
    print(f"  vs Break-even (52.4%): z={z_score:.2f}, p={p_value:.4f}")
    
    if ci_low > breakeven:
        print("  *** STATISTICALLY SIGNIFICANT EDGE ***")
    else:
        print("  Edge not statistically significant (need more games)")
    
    return all_preds, best_threshold


if __name__ == "__main__":
    preds, threshold = run_validation()
