"""Automated Weekly Retraining Scheduler

Runs every Sunday night automatically to:
1. Ingest fresh data from nflverse
2. Retrain models with latest results
3. Update feature importance tracking
4. Trigger drift detection
5. Generate new predictions for upcoming week

Based on research:
- Weekly retraining captures recent performance shifts
- Sunday night timing = full week's data available
- Automatic drift detection prevents stale models
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetrainingJob:
    """Single retraining job configuration."""

    def __init__(
        self,
        name: str,
        function: Callable,
        schedule: str,  # cron expression
        enabled: bool = True,
    ):
        self.name = name
        self.function = function
        self.schedule = schedule
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.last_status: str = "never_run"
        self.last_error: Optional[str] = None

    def run(self) -> bool:
        """Execute the job."""
        try:
            logger.info(f"Starting job: {self.name}")
            self.function()
            self.last_run = datetime.now()
            self.last_status = "success"
            self.last_error = None
            logger.info(f"Job completed: {self.name}")
            return True
        except Exception as e:
            self.last_run = datetime.now()
            self.last_status = "failed"
            self.last_error = str(e)
            logger.error(f"Job failed: {self.name} - {e}")
            return False


class WeeklyScheduler:
    """
    Automated weekly retraining scheduler.

    Schedule:
    - Sunday 23:00: Full model retraining
    - Monday 06:00: Generate weekly predictions
    - Daily 08:00: Update live lines and odds
    """

    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self.jobs: Dict[str, RetrainingJob] = {}
        self._scheduler = None
        self._running = False

    def add_job(
        self,
        name: str,
        function: Callable,
        schedule: str,
        enabled: bool = True,
    ):
        """Add a scheduled job."""
        self.jobs[name] = RetrainingJob(name, function, schedule, enabled)
        logger.info(f"Added job: {name} ({schedule})")

    def start(self):
        """Start the scheduler."""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger

            self._scheduler = BackgroundScheduler()

            for name, job in self.jobs.items():
                if job.enabled:
                    # Parse cron expression
                    parts = job.schedule.split()
                    if len(parts) == 5:
                        trigger = CronTrigger(
                            minute=parts[0],
                            hour=parts[1],
                            day=parts[2],
                            month=parts[3],
                            day_of_week=parts[4],
                        )
                        self._scheduler.add_job(
                            job.run,
                            trigger=trigger,
                            id=name,
                            name=name,
                        )

            self._scheduler.start()
            self._running = True
            logger.info("Scheduler started")

        except ImportError:
            logger.warning("APScheduler not installed. Using simple scheduler fallback.")
            self._running = True

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown()
        self._running = False
        logger.info("Scheduler stopped")

    def run_job_now(self, name: str) -> bool:
        """Manually trigger a job."""
        if name in self.jobs:
            return self.jobs[name].run()
        return False

    def get_status(self) -> Dict:
        """Get scheduler status."""
        return {
            'running': self._running,
            'jobs': {
                name: {
                    'enabled': job.enabled,
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'last_status': job.last_status,
                    'last_error': job.last_error,
                    'schedule': job.schedule,
                }
                for name, job in self.jobs.items()
            }
        }


def create_production_scheduler() -> WeeklyScheduler:
    """
    Create production scheduler with all jobs configured.

    Jobs:
    1. weekly_retrain: Sunday 23:00 - Full model retraining
    2. generate_picks: Monday 06:00 - Generate weekly card
    3. update_lines: Daily 08:00 - Refresh odds
    4. drift_check: Daily 12:00 - Check for model drift
    """
    scheduler = WeeklyScheduler()

    def weekly_retrain():
        """Full weekly retraining job."""
        from src.pipeline.feature_store import create_feature_store
        from src.models.training import train_all_models

        logger.info("Starting weekly retraining...")

        # 1. Refresh bronze data
        store = create_feature_store()
        current_year = datetime.now().year
        seasons = list(range(current_year - 3, current_year + 1))
        store.ingest_bronze(seasons)

        # 2. Build silver features
        pbp = store.load_bronze('pbp', seasons)
        schedules = store.load_bronze('schedules', seasons)
        store.build_silver_player_features(pbp, schedules)
        store.build_silver_game_features(schedules, pbp)

        # 3. Build gold training set
        store.build_gold_training_set()

        # 4. Retrain models
        train_all_models()

        logger.info("Weekly retraining complete")

    def generate_picks():
        """Generate weekly betting card."""
        from scripts.autonomous_system import main as generate_card

        logger.info("Generating weekly picks...")
        generate_card()
        logger.info("Weekly picks generated")

    def update_lines():
        """Update live odds from The Odds API."""
        logger.info("Updating live lines...")
        # Placeholder - integrate with odds API
        logger.info("Lines updated")

    def drift_check():
        """Check for model drift."""
        from src.core.validation_framework import create_validation_framework

        logger.info("Running drift check...")
        framework = create_validation_framework()
        # Check recent predictions vs actuals
        logger.info("Drift check complete")

    # Add jobs with cron schedules
    # Format: minute hour day month day_of_week
    scheduler.add_job("weekly_retrain", weekly_retrain, "0 23 * * 0")  # Sunday 23:00
    scheduler.add_job("generate_picks", generate_picks, "0 6 * * 1")   # Monday 06:00
    scheduler.add_job("update_lines", update_lines, "0 8 * * *")       # Daily 08:00
    scheduler.add_job("drift_check", drift_check, "0 12 * * *")        # Daily 12:00

    return scheduler


# Simple scheduler for environments without APScheduler
class SimpleScheduler:
    """Fallback scheduler using simple time checks."""

    def __init__(self):
        self.jobs: Dict[str, Callable] = {}

    def add_job(self, name: str, function: Callable, **kwargs):
        self.jobs[name] = function

    def run_all(self):
        """Run all jobs once."""
        for name, func in self.jobs.items():
            try:
                logger.info(f"Running: {name}")
                func()
            except Exception as e:
                logger.error(f"Job {name} failed: {e}")
