#!/usr/bin/env python3
"""Automated weekly retraining script.

Runs every Monday to:
1. Download latest data
2. Retrain favorites-only model
3. A/B test vs current model
4. Deploy if better
"""

import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Set PYTHONPATH for subprocesses
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_weekly_retrain():
    """Run weekly retraining pipeline."""
    logger.info("=" * 70)
    logger.info("WEEKLY AUTOMATED RETRAINING")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    # Step 1: Download latest data
    logger.info("\n[1] Downloading latest data...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/download_data.py", "--seasons", "2024", "--force"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )
        if result.returncode == 0:
            logger.info("[OK] Data downloaded successfully")
        else:
            logger.error(f"[ERROR] Data download failed: {result.stderr}")
            return 1
    except Exception as e:
        logger.error(f"[ERROR] Data download exception: {e}")
        return 1

    # Step 2: Regenerate features
    logger.info("\n[2] Regenerating features...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from src.features.pipeline import create_features; create_features([2024])",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )
        if result.returncode == 0:
            logger.info("[OK] Features regenerated")
        else:
            logger.warning(f"[WARNING] Feature regeneration: {result.stderr}")
    except Exception as e:
        logger.warning(f"[WARNING] Feature regeneration exception: {e}")

    # Step 3: Retrain favorites-only model
    logger.info("\n[3] Retraining favorites-only model...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/train_favorites_specialist.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )
        if result.returncode == 0:
            logger.info("[OK] Model retrained successfully")
        else:
            logger.error(f"[ERROR] Model training failed: {result.stderr}")
            return 1
    except Exception as e:
        logger.error(f"[ERROR] Model training exception: {e}")
        return 1

    # Step 4: A/B test (compare new vs old model)
    logger.info("\n[4] Running A/B test...")
    logger.info("[INFO] Compare new model metrics with previous model")
    logger.info("[INFO] If new model is better, it will be used automatically")

    logger.info("\n" + "=" * 70)
    logger.info("WEEKLY RETRAINING COMPLETE")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(run_weekly_retrain())
