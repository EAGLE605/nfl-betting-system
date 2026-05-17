#!/usr/bin/env python3
"""NFL Betting System CLI - Main Entry Point

Usage:
    python cli.py refresh     # Download fresh data
    python cli.py train       # Train models
    python cli.py predict     # Generate predictions
    python cli.py serve       # Start API server
    python cli.py card        # Generate betting card
    python cli.py run         # Full pipeline: refresh -> train -> predict -> serve
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("nfl_betting.log"),
    ]
)
logger = logging.getLogger(__name__)


def cmd_refresh(args):
    """Download fresh data from all sources."""
    from src.services import create_data_service

    logger.info("Refreshing data from nflverse and odds APIs...")
    service = create_data_service()
    counts = service.refresh_all_data()

    print("\n" + "=" * 50)
    print("DATA REFRESH COMPLETE")
    print("=" * 50)
    for source, count in counts.items():
        print(f"  {source}: {count:,} records")
    print("=" * 50)

    return 0


def cmd_train(args):
    """Train prediction models."""
    from src.services import create_data_service, create_model_service

    logger.info("Training models on real data...")

    data_service = create_data_service()
    model_service = create_model_service()

    # Load training data
    path = Path("data/raw/schedules.parquet")
    if not path.exists():
        logger.error("No training data. Run 'python cli.py refresh' first.")
        return 1

    import pandas as pd
    schedules = pd.read_parquet(path)

    # Get team stats for features
    try:
        team_stats = data_service.get_team_stats()
    except Exception:
        team_stats = None

    # Prepare features
    from src.data.nfl_data import prepare_features
    train_df = prepare_features(schedules, team_stats)

    if len(train_df) == 0:
        logger.error("No training data after feature preparation")
        return 1

    # Train game outcome model
    model, metrics = model_service.train_game_model(train_df)

    print("\n" + "=" * 50)
    print("MODEL TRAINING COMPLETE")
    print("=" * 50)
    print(f"  Samples: {len(train_df):,}")
    print(f"  Brier Score: {metrics['brier_score']:.4f}")
    print(f"  Log Loss: {metrics['log_loss']:.4f}")
    print(f"  AUC-ROC: {metrics['auc_roc']:.4f}")
    print(f"  Accuracy: {metrics['accuracy']:.1%}")
    print("=" * 50)

    return 0


def cmd_predict(args):
    """Generate predictions for current week."""
    from src.services import create_prediction_service

    logger.info("Generating predictions...")
    service = create_prediction_service()
    card = service.generate_weekly_card()

    # Print summary
    print("\n" + "=" * 60)
    print(f"NFL BETTING CARD - WEEK {card.week}, {card.season}")
    print("=" * 60)

    print(f"\nTOP PICKS ({len(card.top_picks)}):")
    print("-" * 40)
    for pick in card.top_picks[:5]:
        print(f"  [{pick.confidence}] {pick.pick}")
        print(f"      {pick.matchup} | {pick.edge_type}")

    print(f"\nPLAYER PROPS ({len(card.player_props)}):")
    print("-" * 40)
    for prop in card.player_props[:5]:
        print(f"  [{prop.confidence}] {prop.player_name} {prop.prediction} {prop.line} {prop.prop_type}")
        print(f"      vs {prop.opponent} | Matchup: {prop.matchup_grade}")

    print(f"\nPARLAYS ({len(card.parlays)}):")
    print("-" * 40)
    for parlay in card.parlays:
        print(f"  {parlay.name} ({len(parlay.legs)} legs)")
        print(f"      Odds: +{parlay.total_odds} | EV: {parlay.expected_value:.1f}%")

    print("\n" + "=" * 60)

    # Save to file
    output = service.to_json(card)
    output_path = f"data/predictions/card_week{card.week}_{card.season}.json"
    Path("data/predictions").mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved to: {output_path}")

    return 0


def cmd_serve(args):
    """Start the API server."""
    import subprocess

    port = args.port or 8000
    logger.info(f"Starting API server on port {port}...")

    # Check if backend exists
    backend_path = Path("backend/main.py")
    if not backend_path.exists():
        logger.warning("Backend not found. Using built-in server.")
        _serve_builtin(port)
    else:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ])

    return 0


def _serve_builtin(port: int):
    """Built-in minimal server."""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
    except ImportError:
        logger.error("FastAPI not installed. Run: pip install fastapi uvicorn")
        return

    app = FastAPI(title="NFL Betting API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health():
        return {"status": "ok", "timestamp": datetime.now().isoformat()}

    @app.get("/api/card")
    def get_card():
        from src.services import create_prediction_service
        service = create_prediction_service()
        card = service.generate_weekly_card()
        return service.to_json(card)

    @app.get("/api/picks")
    def get_picks():
        from src.services import create_prediction_service
        service = create_prediction_service()
        card = service.generate_weekly_card()
        return {"picks": [p.__dict__ for p in card.top_picks]}

    @app.get("/api/props")
    def get_props():
        from src.services import create_prediction_service
        service = create_prediction_service()
        card = service.generate_weekly_card()
        return {"props": [p.__dict__ for p in card.player_props]}

    @app.get("/api/parlays")
    def get_parlays():
        from src.services import create_prediction_service
        service = create_prediction_service()
        card = service.generate_weekly_card()
        return {"parlays": [p.__dict__ for p in card.parlays]}

    uvicorn.run(app, host="0.0.0.0", port=port)


def cmd_card(args):
    """Generate and display betting card."""
    return cmd_predict(args)


def cmd_run(args):
    """Run full pipeline: refresh -> train -> predict."""
    print("\n" + "=" * 60)
    print("NFL BETTING SYSTEM - FULL PIPELINE")
    print("=" * 60 + "\n")

    # Step 1: Refresh data
    print("Step 1/3: Refreshing data...")
    if cmd_refresh(args) != 0:
        logger.error("Data refresh failed")
        return 1

    # Step 2: Train models
    print("\nStep 2/3: Training models...")
    if cmd_train(args) != 0:
        logger.error("Model training failed")
        return 1

    # Step 3: Generate predictions
    print("\nStep 3/3: Generating predictions...")
    if cmd_predict(args) != 0:
        logger.error("Prediction generation failed")
        return 1

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print("\nTo start the API server, run:")
    print("  python cli.py serve")
    print("\nTo start the frontend, run:")
    print("  cd frontend && npm run dev")

    return 0


def cmd_install(args):
    """Install dependencies."""
    import subprocess

    print("Installing Python dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    print("\nInstalling frontend dependencies...")
    subprocess.run(["npm", "install"], cwd="frontend")

    print("\nInstallation complete!")
    return 0


def cmd_status(args):
    """Show system status."""
    from pathlib import Path

    print("\n" + "=" * 50)
    print("NFL BETTING SYSTEM STATUS")
    print("=" * 50)

    # Check data
    data_files = [
        ("Schedules", "data/raw/schedules.parquet"),
        ("Play-by-play", "data/raw/pbp.parquet"),
        ("Models", "models/game_outcome_latest.pkl"),
    ]

    print("\nData Status:")
    for name, path in data_files:
        exists = Path(path).exists()
        status = "OK" if exists else "MISSING"
        print(f"  {name}: {status}")

    # Check environment
    print("\nEnvironment:")
    odds_key = os.environ.get("ODDS_API_KEY")
    print(f"  ODDS_API_KEY: {'Set' if odds_key else 'Not set (optional)'}")

    # Check recent predictions
    pred_dir = Path("data/predictions")
    if pred_dir.exists():
        preds = list(pred_dir.glob("*.json"))
        if preds:
            latest = max(preds, key=lambda p: p.stat().st_mtime)
            print(f"\nLatest prediction: {latest.name}")

    print("=" * 50)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="NFL Betting System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  refresh   Download fresh data from nflverse and odds APIs
  train     Train prediction models on historical data
  predict   Generate predictions for current week
  serve     Start the API server
  card      Generate and display betting card
  run       Full pipeline: refresh -> train -> predict
  install   Install all dependencies
  status    Show system status

Examples:
  python cli.py run           # Run full pipeline
  python cli.py serve --port 8000  # Start API server
  python cli.py card          # Quick betting card
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Refresh command
    subparsers.add_parser("refresh", help="Download fresh data")

    # Train command
    subparsers.add_parser("train", help="Train models")

    # Predict command
    subparsers.add_parser("predict", help="Generate predictions")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--port", type=int, default=8000, help="Server port")

    # Card command
    subparsers.add_parser("card", help="Generate betting card")

    # Run command
    subparsers.add_parser("run", help="Run full pipeline")

    # Install command
    subparsers.add_parser("install", help="Install dependencies")

    # Status command
    subparsers.add_parser("status", help="Show system status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "refresh": cmd_refresh,
        "train": cmd_train,
        "predict": cmd_predict,
        "serve": cmd_serve,
        "card": cmd_card,
        "run": cmd_run,
        "install": cmd_install,
        "status": cmd_status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
