"""V2: Next Gen Stats Model

Novel approach using NFL Next Gen Stats metrics:
- QB: time_to_throw, aggressiveness, air_yards
- RB: efficiency, stacked_box_rate, time_to_los
- WR: separation, cushion

Version: 2.0
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, brier_score_loss
import nfl_data_py as nfl
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/user/nfl-betting-system/data/raw")
VERSION = "2.0-nextgen"


def load_nextgen_stats():
    """Load Next Gen Stats for all available seasons."""
    print("Loading Next Gen Stats...")

    seasons = [2021, 2022, 2023, 2024]

    try:
        ngs_passing = nfl.import_ngs_data('passing', seasons)
        ngs_rushing = nfl.import_ngs_data('rushing', seasons)
        ngs_receiving = nfl.import_ngs_data('receiving', seasons)

        print(f"  Passing: {len(ngs_passing)} rows")
        print(f"  Rushing: {len(ngs_rushing)} rows")
        print(f"  Receiving: {len(ngs_receiving)} rows")

        return ngs_passing, ngs_rushing, ngs_receiving
    except Exception as e:
        print(f"Error loading NGS: {e}")
        return None, None, None


def aggregate_team_ngs(ngs_passing, ngs_rushing, ngs_receiving):
    """Aggregate NGS to team-week level."""
    print("Aggregating to team level...")

    # QB metrics (top QB per team per week)
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

    # WR metrics (aggregate all receivers)
    wr_stats = ngs_receiving.groupby(['season', 'week', 'team_abbr']).agg({
        'avg_cushion': 'mean',
        'avg_separation': 'mean',
        'catch_percentage': 'mean',
    }).reset_index()
    wr_stats.columns = ['season', 'week', 'team', 'wr_cushion',
                        'wr_separation', 'wr_catch_pct']

    # Merge all
    team_ngs = qb_stats.merge(rb_stats, on=['season', 'week', 'team'], how='outer')
    team_ngs = team_ngs.merge(wr_stats, on=['season', 'week', 'team'], how='outer')

    # Create rolling averages (prior 3 weeks)
    team_ngs = team_ngs.sort_values(['team', 'season', 'week'])

    ngs_cols = ['qb_time_to_throw', 'qb_aggressiveness', 'qb_air_yards', 'qb_air_diff',
                'qb_comp_pct', 'rb_efficiency', 'rb_stacked_box_pct', 'rb_time_to_los',
                'rb_ypc', 'wr_cushion', 'wr_separation', 'wr_catch_pct']

    for col in ngs_cols:
        if col in team_ngs.columns:
            team_ngs[f'{col}_roll'] = team_ngs.groupby('team')[col].transform(
                lambda x: x.shift(1).rolling(3, min_periods=1).mean()
            )

    return team_ngs


def load_game_outcomes():
    """Load game outcomes from PBP."""
    pbp = pd.read_parquet(DATA_DIR / "pbp_4seasons.parquet")

    games = pbp.groupby(['game_id', 'season', 'week', 'home_team', 'away_team']).agg({
        'total_home_score': 'max',
        'total_away_score': 'max',
    }).reset_index()
    games.columns = ['game_id', 'season', 'week', 'home_team', 'away_team',
                     'home_score', 'away_score']
    games = games.dropna()
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)

    return games


def build_features(games, team_ngs):
    """Build feature matrix with NGS metrics."""
    print("Building features...")

    # Get rolling columns
    roll_cols = [c for c in team_ngs.columns if c.endswith('_roll')]

    # Merge home team NGS
    home_ngs = team_ngs[['season', 'week', 'team'] + roll_cols].copy()
    home_ngs.columns = ['season', 'week', 'home_team'] + [f'home_{c}' for c in roll_cols]

    # Merge away team NGS
    away_ngs = team_ngs[['season', 'week', 'team'] + roll_cols].copy()
    away_ngs.columns = ['season', 'week', 'away_team'] + [f'away_{c}' for c in roll_cols]

    df = games.merge(home_ngs, on=['season', 'week', 'home_team'], how='left')
    df = df.merge(away_ngs, on=['season', 'week', 'away_team'], how='left')

    # Create differentials for key metrics
    for col in roll_cols:
        home_col = f'home_{col}'
        away_col = f'away_{col}'
        if home_col in df.columns and away_col in df.columns:
            df[f'diff_{col}'] = df[home_col].fillna(0) - df[away_col].fillna(0)

    return df


def run_v2_model():
    """Run the V2 Next Gen Stats model."""
    print("=" * 70)
    print(f"NFL BETTING MODEL V{VERSION}")
    print("=" * 70)

    # Load data
    ngs_pass, ngs_rush, ngs_rec = load_nextgen_stats()

    if ngs_pass is None:
        print("Failed to load NGS data")
        return

    team_ngs = aggregate_team_ngs(ngs_pass, ngs_rush, ngs_rec)
    games = load_game_outcomes()

    print(f"\nGames: {len(games)}")
    print(f"NGS team-weeks: {len(team_ngs)}")

    # Build features
    df = build_features(games, team_ngs)

    # Also add EPA from PBP for comparison
    pbp = pd.read_parquet(DATA_DIR / "pbp_4seasons.parquet")
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

    home_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'home_team', 'epa_roll': 'home_epa'})
    away_epa = team_epa[['game_id', 'team', 'epa_roll']].rename(
        columns={'team': 'away_team', 'epa_roll': 'away_epa'})

    df = df.merge(home_epa, on=['game_id', 'home_team'], how='left')
    df = df.merge(away_epa, on=['game_id', 'away_team'], how='left')
    df['epa_diff'] = df['home_epa'].fillna(0) - df['away_epa'].fillna(0)

    # Filter to weeks with data
    df = df[df['week'] >= 4].copy()

    # Define feature sets
    diff_cols = [c for c in df.columns if c.startswith('diff_')]

    feature_sets = {
        'epa_only': ['epa_diff'],
        'ngs_only': diff_cols,
        'combined': ['epa_diff'] + diff_cols,
    }

    print(f"\nFeature sets:")
    for name, cols in feature_sets.items():
        available = [c for c in cols if c in df.columns]
        print(f"  {name}: {len(available)} features")

    # Walk-forward test
    print("\n" + "=" * 70)
    print("WALK-FORWARD VALIDATION")
    print("=" * 70)

    results = []

    for test_year in [2023, 2024]:
        train = df[df['season'] < test_year].dropna(subset=['home_win'])
        test = df[df['season'] == test_year].dropna(subset=['home_win'])

        if len(train) < 50 or len(test) < 50:
            continue

        y_train = train['home_win']
        y_test = test['home_win']

        print(f"\n--- {test_year} (train: {len(train)}, test: {len(test)}) ---")

        for feat_name, feat_cols in feature_sets.items():
            available = [c for c in feat_cols if c in df.columns]
            if len(available) == 0:
                continue

            X_train = train[available].fillna(0)
            X_test = test[available].fillna(0)

            # Scale
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)

            # Train GBM
            model = GradientBoostingClassifier(
                n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
            )
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
                'year': test_year,
                'features': feat_name,
                'n_features': len(available),
                'accuracy': acc,
                'hc_accuracy': hc_acc,
                'hc_n': hc_n,
                'hc_roi': hc_roi,
            })

            print(f"  {feat_name}: Acc={acc:.1%}, HC={hc_acc:.1%} (n={hc_n}), ROI={hc_roi:+.1f}%")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    results_df = pd.DataFrame(results)

    # Aggregate by feature set
    agg = results_df.groupby('features').agg({
        'accuracy': 'mean',
        'hc_accuracy': 'mean',
        'hc_roi': 'mean',
        'hc_n': 'sum',
    }).reset_index()

    print("\nBy Feature Set:")
    for _, row in agg.sort_values('hc_roi', ascending=False).iterrows():
        print(f"  {row['features']}: HC Acc={row['hc_accuracy']:.1%}, ROI={row['hc_roi']:+.1f}%, N={int(row['hc_n'])}")

    # Best result
    best = results_df.loc[results_df['hc_roi'].idxmax()]
    print(f"\nBest: {best['features']} in {best['year']}")
    print(f"  HC Accuracy: {best['hc_accuracy']:.1%}")
    print(f"  HC ROI: {best['hc_roi']:+.1f}%")
    print(f"  HC Games: {int(best['hc_n'])}")

    return results_df


if __name__ == "__main__":
    results = run_v2_model()
