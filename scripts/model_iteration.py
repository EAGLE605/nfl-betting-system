"""Model Iteration - Find the Edge

Start simple, add complexity only when it helps.
Test everything out-of-sample. No cheating.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/user/nfl-betting-system/data/raw")


def load_and_prepare_data():
    """Load PBP and create features using ONLY prior information."""
    print("Loading data...")
    pbp = pd.read_parquet(DATA_DIR / "pbp_4seasons.parquet")

    # Game outcomes
    games = pbp.groupby(['game_id', 'season', 'week', 'home_team', 'away_team']).agg({
        'total_home_score': 'max',
        'total_away_score': 'max',
        'roof': 'first',
        'temp': 'first',
        'wind': 'first',
    }).reset_index()
    games.columns = ['game_id', 'season', 'week', 'home_team', 'away_team',
                     'home_score', 'away_score', 'roof', 'temp', 'wind']
    games = games.dropna(subset=['home_score', 'away_score'])
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)
    games['total_points'] = games['home_score'] + games['away_score']
    games['point_diff'] = games['home_score'] - games['away_score']

    # Sort for rolling calculations
    games = games.sort_values(['season', 'week']).reset_index(drop=True)

    # Team EPA by game (for rolling)
    team_epa = pbp[pbp['play_type'].isin(['pass', 'run']) & pbp['epa'].notna()].groupby(
        ['game_id', 'posteam']
    ).agg({
        'epa': 'mean',
        'success': 'mean',
        'yards_gained': 'mean',
    }).reset_index()
    team_epa.columns = ['game_id', 'team', 'epa', 'success_rate', 'yards_per_play']

    # Defensive EPA
    def_epa = pbp[pbp['play_type'].isin(['pass', 'run']) & pbp['epa'].notna()].groupby(
        ['game_id', 'defteam']
    )['epa'].mean().reset_index()
    def_epa.columns = ['game_id', 'team', 'def_epa']

    # Merge team stats
    team_stats = team_epa.merge(def_epa, on=['game_id', 'team'], how='left')

    # Add season/week for sorting
    game_info = games[['game_id', 'season', 'week']].drop_duplicates()
    team_stats = team_stats.merge(game_info, on='game_id')
    team_stats = team_stats.sort_values(['team', 'season', 'week'])

    # Calculate rolling features (PRIOR games only - shift by 1)
    for col in ['epa', 'success_rate', 'yards_per_play', 'def_epa']:
        team_stats[f'{col}_roll3'] = team_stats.groupby('team')[col].transform(
            lambda x: x.shift(1).rolling(3, min_periods=1).mean()
        )
        team_stats[f'{col}_roll5'] = team_stats.groupby('team')[col].transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).mean()
        )

    # Merge rolling stats back to games
    home_stats = team_stats[['game_id', 'team', 'epa_roll3', 'epa_roll5',
                              'success_rate_roll5', 'def_epa_roll5']].rename(
        columns={'team': 'home_team', 'epa_roll3': 'home_epa3', 'epa_roll5': 'home_epa5',
                 'success_rate_roll5': 'home_success', 'def_epa_roll5': 'home_def_epa'}
    )
    away_stats = team_stats[['game_id', 'team', 'epa_roll3', 'epa_roll5',
                              'success_rate_roll5', 'def_epa_roll5']].rename(
        columns={'team': 'away_team', 'epa_roll3': 'away_epa3', 'epa_roll5': 'away_epa5',
                 'success_rate_roll5': 'away_success', 'def_epa_roll5': 'away_def_epa'}
    )

    games = games.merge(home_stats, on=['game_id', 'home_team'], how='left')
    games = games.merge(away_stats, on=['game_id', 'away_team'], how='left')

    return games, pbp


def engineer_features(games):
    """Create predictive features."""
    df = games.copy()

    # EPA differentials
    df['epa_diff_3'] = df['home_epa3'].fillna(0) - df['away_epa3'].fillna(0)
    df['epa_diff_5'] = df['home_epa5'].fillna(0) - df['away_epa5'].fillna(0)

    # Success rate differential
    df['success_diff'] = df['home_success'].fillna(0.45) - df['away_success'].fillna(0.45)

    # Defensive EPA differential (lower is better for defense)
    df['def_epa_diff'] = df['away_def_epa'].fillna(0) - df['home_def_epa'].fillna(0)

    # Home field
    df['home_field'] = 1

    # Division game
    divisions = {
        'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
        'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
        'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
        'AFC West': ['DEN', 'KC', 'LAC', 'LV'],
        'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
        'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
        'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
        'NFC West': ['ARI', 'LAR', 'SEA', 'SF'],
    }

    def same_div(home, away):
        for teams in divisions.values():
            if home in teams and away in teams:
                return 1
        return 0

    df['div_game'] = df.apply(lambda x: same_div(x['home_team'], x['away_team']), axis=1)

    # Week (early vs late season)
    df['week_norm'] = df['week'] / 18
    df['late_season'] = (df['week'] >= 12).astype(int)

    # Weather
    df['dome'] = (df['roof'] == 'dome').astype(int) if 'roof' in df.columns else 0
    df['cold'] = ((df['temp'] < 35) & (df['dome'] == 0)).astype(int) if 'temp' in df.columns else 0
    df['windy'] = ((df['wind'] > 15) & (df['dome'] == 0)).astype(int) if 'wind' in df.columns else 0

    # Combined efficiency score
    df['home_eff'] = df['home_epa5'].fillna(0) - df['home_def_epa'].fillna(0)
    df['away_eff'] = df['away_epa5'].fillna(0) - df['away_def_epa'].fillna(0)
    df['eff_diff'] = df['home_eff'] - df['away_eff']

    return df


def evaluate_model(y_true, y_pred_proba, name="Model"):
    """Evaluate with multiple metrics."""
    y_pred = (y_pred_proba > 0.5).astype(int)

    acc = accuracy_score(y_true, y_pred)
    brier = brier_score_loss(y_true, y_pred_proba)
    ll = log_loss(y_true, y_pred_proba)

    n = len(y_true)
    se = np.sqrt(acc * (1 - acc) / n)

    # ROI at -110 odds
    wins = (y_pred == y_true).sum()
    losses = n - wins
    roi = (wins * 0.91 - losses) / n * 100

    # High confidence
    high_conf = (y_pred_proba > 0.58) | (y_pred_proba < 0.42)
    if high_conf.sum() > 10:
        hc_acc = accuracy_score(y_true[high_conf], y_pred[high_conf])
        hc_n = high_conf.sum()
        hc_roi = ((y_pred[high_conf] == y_true[high_conf]).sum() * 0.91 -
                  (y_pred[high_conf] != y_true[high_conf]).sum()) / hc_n * 100
    else:
        hc_acc, hc_n, hc_roi = 0, 0, 0

    return {
        'name': name,
        'n': n,
        'accuracy': acc,
        'ci_low': acc - 1.96 * se,
        'ci_high': acc + 1.96 * se,
        'brier': brier,
        'log_loss': ll,
        'roi_flat': roi,
        'hc_n': hc_n,
        'hc_accuracy': hc_acc,
        'hc_roi': hc_roi,
    }


def run_iteration():
    """Main iteration loop."""
    print("=" * 70)
    print("MODEL ITERATION - FINDING THE EDGE")
    print("=" * 70)

    # Load data
    games, pbp = load_and_prepare_data()
    df = engineer_features(games)

    # Drop early season (no rolling data)
    df = df[df['week'] >= 4].copy()
    print(f"\nTotal games: {len(df)}")
    print(f"Seasons: {sorted(df['season'].unique())}")

    # Feature sets to try
    feature_sets = {
        'minimal': ['epa_diff_5', 'home_field'],
        'basic': ['epa_diff_5', 'home_field', 'div_game', 'week_norm'],
        'efficiency': ['epa_diff_5', 'success_diff', 'def_epa_diff', 'home_field', 'div_game'],
        'full': ['epa_diff_5', 'epa_diff_3', 'success_diff', 'def_epa_diff',
                 'home_field', 'div_game', 'week_norm', 'late_season',
                 'dome', 'cold', 'windy', 'eff_diff'],
    }

    # Models to try
    models = {
        'logistic': LogisticRegression(C=1.0, max_iter=1000),
        'rf': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
        'gbm': GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                          learning_rate=0.1, random_state=42),
    }

    results = []

    # Walk-forward for each combination
    for test_year in [2023, 2024]:
        print(f"\n{'='*70}")
        print(f"TEST YEAR: {test_year}")
        print(f"{'='*70}")

        train = df[df['season'] < test_year]
        test = df[df['season'] == test_year]

        if len(test) < 50:
            continue

        y_train = train['home_win']
        y_test = test['home_win']

        for feat_name, features in feature_sets.items():
            available = [f for f in features if f in df.columns]

            X_train = train[available].fillna(0)
            X_test = test[available].fillna(0)

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            for model_name, model in models.items():
                # Fresh model instance
                if model_name == 'logistic':
                    m = LogisticRegression(C=1.0, max_iter=1000)
                elif model_name == 'rf':
                    m = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
                else:
                    m = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                                   learning_rate=0.1, random_state=42)

                m.fit(X_train_scaled, y_train)
                y_pred_proba = m.predict_proba(X_test_scaled)[:, 1]

                result = evaluate_model(y_test.values, y_pred_proba,
                                        f"{model_name}_{feat_name}")
                result['year'] = test_year
                result['features'] = feat_name
                result['model'] = model_name
                results.append(result)

    # Summarize results
    results_df = pd.DataFrame(results)

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    # Best by accuracy
    print("\nBest by Accuracy:")
    best_acc = results_df.loc[results_df['accuracy'].idxmax()]
    print(f"  {best_acc['name']}: {best_acc['accuracy']:.1%} (n={best_acc['n']})")

    # Best by high-confidence accuracy
    hc_results = results_df[results_df['hc_n'] > 20]
    if len(hc_results) > 0:
        print("\nBest High-Confidence:")
        best_hc = hc_results.loc[hc_results['hc_accuracy'].idxmax()]
        print(f"  {best_hc['name']}: {best_hc['hc_accuracy']:.1%} (n={best_hc['hc_n']})")
        print(f"  ROI at -110: {best_hc['hc_roi']:.1f}%")

    # Best by ROI
    print("\nBest by ROI (flat betting all games):")
    best_roi = results_df.loc[results_df['roi_flat'].idxmax()]
    print(f"  {best_roi['name']}: {best_roi['roi_flat']:.1f}% ROI")

    # Aggregate across years
    print("\n" + "=" * 70)
    print("AGGREGATED RESULTS (2023 + 2024)")
    print("=" * 70)

    agg = results_df.groupby(['model', 'features']).agg({
        'n': 'sum',
        'accuracy': lambda x: (x * results_df.loc[x.index, 'n']).sum() / results_df.loc[x.index, 'n'].sum(),
        'hc_n': 'sum',
        'hc_accuracy': lambda x: (x * results_df.loc[x.index, 'hc_n']).sum() / max(results_df.loc[x.index, 'hc_n'].sum(), 1),
        'roi_flat': 'mean',
        'hc_roi': 'mean',
    }).reset_index()

    agg = agg.sort_values('accuracy', ascending=False)

    print(f"\n{'Model':<25} {'Acc':>8} {'HC Acc':>8} {'HC ROI':>8} {'N':>6}")
    print("-" * 60)
    for _, row in agg.head(10).iterrows():
        print(f"{row['model']}_{row['features']:<15} {row['accuracy']:>7.1%} {row['hc_accuracy']:>7.1%} {row['hc_roi']:>7.1f}% {int(row['n']):>6}")

    # Find profitable configs
    print("\n" + "=" * 70)
    print("POTENTIALLY PROFITABLE (HC ROI > 5%)")
    print("=" * 70)

    profitable = agg[agg['hc_roi'] > 5].sort_values('hc_roi', ascending=False)
    if len(profitable) > 0:
        for _, row in profitable.iterrows():
            print(f"\n{row['model']}_{row['features']}:")
            print(f"  High-Conf Accuracy: {row['hc_accuracy']:.1%}")
            print(f"  High-Conf ROI: {row['hc_roi']:.1f}%")
            print(f"  High-Conf Games: {int(row['hc_n'])}")
    else:
        print("\nNo configurations showed >5% ROI on high-confidence bets.")
        print("This is expected - NFL is efficient.")

    return results_df, agg


if __name__ == "__main__":
    results_df, agg = run_iteration()
