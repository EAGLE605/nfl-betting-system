"""Training script with MLOps integration."""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from .features import FeaturePipeline, FeatureConfig
from .registry import ModelRegistry

FEATURES = [
    "epa_diff",
    "diff_rb_efficiency_roll",
    "diff_rb_stacked_box_pct_roll",
    "diff_rb_time_to_los_roll",
    "diff_rb_ypc_roll",
]


def train_and_register(
    train_seasons: list[int],
    test_seasons: list[int],
    min_week: int = 4,
    confidence_threshold: float = 0.62,
) -> str:
    """Train model and register with the registry."""

    pipeline = FeaturePipeline(FeatureConfig(min_week=min_week))

    games, team_epa = pipeline.get_epa_features()
    rb_stats = pipeline.get_ngs_features()

    roll_cols = [
        "rb_efficiency_roll", "rb_stacked_box_pct_roll",
        "rb_time_to_los_roll", "rb_ypc_roll"
    ]

    home_rb = rb_stats[["season", "week", "team"] + roll_cols].copy()
    home_rb.columns = ["season", "week", "home_team"] + [f"home_{c}" for c in roll_cols]

    away_rb = rb_stats[["season", "week", "team"] + roll_cols].copy()
    away_rb.columns = ["season", "week", "away_team"] + [f"away_{c}" for c in roll_cols]

    df = games.merge(home_rb, on=["season", "week", "home_team"], how="left")
    df = df.merge(away_rb, on=["season", "week", "away_team"], how="left")

    home_epa = team_epa[["game_id", "team", "epa_roll"]].rename(
        columns={"team": "home_team", "epa_roll": "home_epa"}
    )
    away_epa = team_epa[["game_id", "team", "epa_roll"]].rename(
        columns={"team": "away_team", "epa_roll": "away_epa"}
    )

    df = df.merge(home_epa, on=["game_id", "home_team"], how="left")
    df = df.merge(away_epa, on=["game_id", "away_team"], how="left")

    df["epa_diff"] = df["home_epa"].fillna(0) - df["away_epa"].fillna(0)
    for col in roll_cols:
        df[f"diff_{col}"] = df[f"home_{col}"].fillna(0) - df[f"away_{col}"].fillna(0)

    train = df[df["season"].isin(train_seasons) & (df["week"] >= min_week)]
    test = df[df["season"].isin(test_seasons) & (df["week"] >= min_week)]

    train = train.dropna(subset=["home_win"])
    test = test.dropna(subset=["home_win"])

    X_train = train[FEATURES].fillna(0)
    y_train = train["home_win"]
    X_test = test[FEATURES].fillna(0)
    y_test = test["home_win"]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)

    probs = model.predict_proba(X_test_scaled)[:, 1]

    high_conf_mask = (probs >= confidence_threshold) | (probs <= 1 - confidence_threshold)
    if high_conf_mask.sum() > 0:
        preds = (probs >= 0.5).astype(int)
        accuracy = (preds[high_conf_mask] == y_test.values[high_conf_mask]).mean()
        roi = (accuracy * 1.91 - 1) * 100
    else:
        accuracy = (probs >= 0.5).astype(int) == y_test.values
        accuracy = accuracy.mean()
        roi = (accuracy * 1.91 - 1) * 100

    registry = ModelRegistry()
    version = registry.register(
        model=model,
        scaler=scaler,
        accuracy=round(accuracy * 100, 1),
        roi=round(roi, 1),
        sample_size=int(high_conf_mask.sum()),
        features=FEATURES,
        test_years=test_seasons,
        notes=f"Train: {train_seasons}, Test: {test_seasons}",
    )

    print(f"Registered model: {version}")
    print(f"  Accuracy: {accuracy*100:.1f}%")
    print(f"  ROI: {roi:.1f}%")
    print(f"  Sample: {high_conf_mask.sum()} high-conf picks")

    return version


if __name__ == "__main__":
    version = train_and_register(
        train_seasons=[2021, 2022],
        test_seasons=[2023, 2024],
    )
    print(f"\nTo promote to production:")
    print(f"  registry.promote('{version}', 'production')")
