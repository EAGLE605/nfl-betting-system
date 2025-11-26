"""
Health Check System

Provides health endpoints for monitoring system status.

Checks:
- Database connectivity
- API availability (ESPN, Odds)
- Model file existence
- Disk space
- Circuit breaker status

BEGINNER GUIDE:
---------------
Why health checks matter:
- Monitoring tools (like Uptime Robot) can ping these endpoints
- Get alerted when something breaks before users notice
- Helps diagnose which component is failing

How to use:
    # Start health check server (standalone)
    python -m src.health.health_check

    # Check health programmatically
    from src.health.health_check import run_health_checks
    results = run_health_checks()

Endpoints (when running as server):
    GET /health       - Overall health status
    GET /health/db    - Database health
    GET /health/api   - API health
    GET /health/model - Model health
    GET /ready        - Readiness probe (for k8s)
    GET /live         - Liveness probe (for k8s)
"""

import json
import logging
import os
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


# =============================================================================
# HEALTH CHECK MODELS
# =============================================================================


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    latency_ms: float = 0.0
    details: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SystemHealth:
    """Overall system health status."""

    status: str  # "healthy", "degraded", "unhealthy"
    checks: List[HealthCheckResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"

    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "checks": [asdict(c) for c in self.checks],
            "timestamp": self.timestamp,
            "version": self.version,
        }


# =============================================================================
# INDIVIDUAL HEALTH CHECKS
# =============================================================================


def check_database_health() -> HealthCheckResult:
    """
    Check database connectivity and integrity.
    """
    start = time.time()

    databases = [
        Path("data/adaptive_learning.db"),
        Path("data/odds_history.db"),
    ]

    issues = []
    details = {}

    for db_path in databases:
        db_name = db_path.stem

        if not db_path.exists():
            issues.append(f"{db_name}: not found")
            details[db_name] = "missing"
            continue

        try:
            conn = sqlite3.connect(str(db_path), timeout=5)
            cursor = conn.cursor()

            # Quick integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]

            if result == "ok":
                # Get size
                size = db_path.stat().st_size
                details[db_name] = {"status": "ok", "size_bytes": size}
            else:
                issues.append(f"{db_name}: integrity check failed")
                details[db_name] = {"status": "corrupted", "error": result}

            conn.close()

        except Exception as e:
            issues.append(f"{db_name}: {str(e)}")
            details[db_name] = {"status": "error", "error": str(e)}

    latency = (time.time() - start) * 1000

    if not issues:
        return HealthCheckResult(
            name="database",
            status="healthy",
            message="All databases healthy",
            latency_ms=latency,
            details=details,
        )
    else:
        return HealthCheckResult(
            name="database",
            status="unhealthy",
            message="; ".join(issues),
            latency_ms=latency,
            details=details,
        )


def check_api_health() -> HealthCheckResult:
    """
    Check external API availability.
    """
    start = time.time()
    details = {}
    issues = []

    # Check ESPN API
    try:
        import requests

        resp = requests.get(
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            timeout=5,
        )
        if resp.status_code == 200:
            details["espn"] = {
                "status": "ok",
                "response_time_ms": resp.elapsed.total_seconds() * 1000,
            }
        else:
            issues.append(f"ESPN: HTTP {resp.status_code}")
            details["espn"] = {"status": "error", "http_code": resp.status_code}
    except Exception as e:
        issues.append(f"ESPN: {str(e)}")
        details["espn"] = {"status": "error", "error": str(e)}

    # Check circuit breaker status
    try:
        from src.utils.resilience import get_circuit_status

        circuits = get_circuit_status()
        details["circuit_breakers"] = circuits

        for name, status in circuits.items():
            if status.get("is_open"):
                issues.append(f"Circuit {name} is OPEN")
    except ImportError:
        details["circuit_breakers"] = "not_available"

    latency = (time.time() - start) * 1000

    if not issues:
        return HealthCheckResult(
            name="api",
            status="healthy",
            message="All APIs reachable",
            latency_ms=latency,
            details=details,
        )
    elif len(issues) == 1 and "Circuit" in issues[0]:
        return HealthCheckResult(
            name="api",
            status="degraded",
            message="; ".join(issues),
            latency_ms=latency,
            details=details,
        )
    else:
        return HealthCheckResult(
            name="api",
            status="unhealthy",
            message="; ".join(issues),
            latency_ms=latency,
            details=details,
        )


def check_model_health() -> HealthCheckResult:
    """
    Check model file availability.
    """
    start = time.time()

    # Check for any of these models (at least one should exist)
    model_files = [
        Path("models/ensemble_model.pkl"),
        Path("models/xgboost_improved.pkl"),
        Path("models/xgboost_favorites_only.pkl"),
        Path("models/calibrated_model.pkl"),
    ]

    details = {}
    issues = []

    for model_path in model_files:
        model_name = model_path.stem

        if model_path.exists():
            size = model_path.stat().st_size
            mtime = datetime.fromtimestamp(model_path.stat().st_mtime).isoformat()
            details[model_name] = {
                "status": "ok",
                "size_bytes": size,
                "last_modified": mtime,
            }
        else:
            issues.append(f"{model_name}: not found")
            details[model_name] = {"status": "missing"}

    latency = (time.time() - start) * 1000

    if not issues:
        return HealthCheckResult(
            name="model",
            status="healthy",
            message="All models available",
            latency_ms=latency,
            details=details,
        )
    else:
        return HealthCheckResult(
            name="model",
            status="unhealthy",
            message="; ".join(issues),
            latency_ms=latency,
            details=details,
        )


def check_disk_health() -> HealthCheckResult:
    """
    Check disk space availability.
    """
    start = time.time()

    try:
        import shutil

        total, used, free = shutil.disk_usage(".")

        free_gb = free / (1024**3)
        used_pct = (used / total) * 100

        details = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free_gb, 2),
            "used_percent": round(used_pct, 1),
        }

        latency = (time.time() - start) * 1000

        if free_gb < 1:
            return HealthCheckResult(
                name="disk",
                status="unhealthy",
                message=f"Low disk space: {free_gb:.1f} GB free",
                latency_ms=latency,
                details=details,
            )
        elif free_gb < 5:
            return HealthCheckResult(
                name="disk",
                status="degraded",
                message=f"Disk space getting low: {free_gb:.1f} GB free",
                latency_ms=latency,
                details=details,
            )
        else:
            return HealthCheckResult(
                name="disk",
                status="healthy",
                message=f"Disk space OK: {free_gb:.1f} GB free",
                latency_ms=latency,
                details=details,
            )

    except Exception as e:
        return HealthCheckResult(
            name="disk",
            status="unhealthy",
            message=f"Failed to check disk: {str(e)}",
            latency_ms=(time.time() - start) * 1000,
        )


def check_config_health() -> HealthCheckResult:
    """
    Check configuration file availability.
    """
    start = time.time()

    config_files = [
        Path("config/config.yaml"),
    ]

    details = {}
    issues = []

    for config_path in config_files:
        if config_path.exists():
            details[config_path.name] = "ok"
        else:
            issues.append(f"{config_path.name}: not found")
            details[config_path.name] = "missing"

    # Check API keys via settings module (handles .env, env vars, and Streamlit secrets)
    try:
        from src.config import settings

        # Required: ODDS_API_KEY
        if settings.api.odds_api_key:
            details["ODDS_API_KEY"] = "set"
        else:
            issues.append("ODDS_API_KEY: not set")
            details["ODDS_API_KEY"] = "missing"

        # Optional: LLM API keys
        llm_keys = {
            "OPENAI_API_KEY": settings.api.openai_api_key,
            "ANTHROPIC_API_KEY": settings.api.anthropic_api_key,
            "XAI_API_KEY": settings.api.xai_api_key,
            "GOOGLE_API_KEY": settings.api.google_api_key,
        }
        for key_name, key_value in llm_keys.items():
            if key_value:
                details[key_name] = "set"
            else:
                details[key_name] = "not set (optional)"

    except ImportError:
        # Fallback to os.getenv if settings not available
        if os.getenv("ODDS_API_KEY"):
            details["ODDS_API_KEY"] = "set"
        else:
            issues.append("ODDS_API_KEY: not set")
            details["ODDS_API_KEY"] = "missing"

    latency = (time.time() - start) * 1000

    if not issues:
        return HealthCheckResult(
            name="config",
            status="healthy",
            message="Configuration OK",
            latency_ms=latency,
            details=details,
        )
    else:
        return HealthCheckResult(
            name="config",
            status="degraded",
            message="; ".join(issues),
            latency_ms=latency,
            details=details,
        )


# =============================================================================
# AGGREGATE HEALTH CHECK
# =============================================================================


def run_health_checks() -> SystemHealth:
    """
    Run all health checks and return overall status.

    Returns:
        SystemHealth object with all check results
    """
    checks = [
        check_database_health(),
        check_api_health(),
        check_model_health(),
        check_disk_health(),
        check_config_health(),
    ]

    # Determine overall status
    statuses = [c.status for c in checks]

    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "unhealthy"
    else:
        overall = "degraded"

    return SystemHealth(
        status=overall,
        checks=checks,
    )


def get_health_summary() -> Dict:
    """
    Get a simple health summary (for quick checks).
    """
    health = run_health_checks()
    return {
        "status": health.status,
        "timestamp": health.timestamp,
        "checks": {c.name: c.status for c in health.checks},
    }


# =============================================================================
# HTTP SERVER (Optional)
# =============================================================================


def create_health_app():
    """
    Create Flask app for health endpoints.

    Returns:
        Flask app
    """
    try:
        from flask import Flask, jsonify
    except ImportError:
        logger.error("Flask not installed. Run: pip install flask")
        return None

    app = Flask(__name__)

    @app.route("/health")
    def health():
        """Full health check."""
        health = run_health_checks()
        status_code = 200 if health.status == "healthy" else 503
        return jsonify(health.to_dict()), status_code

    @app.route("/health/summary")
    def health_summary():
        """Quick health summary."""
        summary = get_health_summary()
        status_code = 200 if summary["status"] == "healthy" else 503
        return jsonify(summary), status_code

    @app.route("/health/db")
    def health_db():
        """Database health only."""
        result = check_database_health()
        status_code = 200 if result.status == "healthy" else 503
        return jsonify(asdict(result)), status_code

    @app.route("/health/api")
    def health_api():
        """API health only."""
        result = check_api_health()
        status_code = 200 if result.status == "healthy" else 503
        return jsonify(asdict(result)), status_code

    @app.route("/health/model")
    def health_model():
        """Model health only."""
        result = check_model_health()
        status_code = 200 if result.status == "healthy" else 503
        return jsonify(asdict(result)), status_code

    @app.route("/ready")
    def ready():
        """Readiness probe (Kubernetes)."""
        health = run_health_checks()
        if health.status != "unhealthy":
            return jsonify({"ready": True}), 200
        return jsonify({"ready": False}), 503

    @app.route("/live")
    def live():
        """Liveness probe (Kubernetes)."""
        return jsonify({"alive": True}), 200

    return app


# =============================================================================
# CLI
# =============================================================================


def print_health_report():
    """Print a formatted health report to console."""
    print("\n" + "=" * 60)
    print("SYSTEM HEALTH CHECK")
    print("=" * 60 + "\n")

    health = run_health_checks()

    # Status emoji
    status_icons = {
        "healthy": "[OK]",
        "degraded": "[WARN]",
        "unhealthy": "[FAIL]",
    }

    print(
        f"Overall Status: {status_icons.get(health.status, '?')} {health.status.upper()}\n"
    )

    for check in health.checks:
        icon = status_icons.get(check.status, "?")
        print(f"  {icon} {check.name}: {check.message}")
        print(f"      Latency: {check.latency_ms:.1f}ms")

        if check.details:
            for key, value in check.details.items():
                if isinstance(value, dict):
                    print(f"      {key}: {value.get('status', value)}")
                else:
                    print(f"      {key}: {value}")
        print()

    print("=" * 60)
    print(f"Timestamp: {health.timestamp}")
    print("=" * 60 + "\n")

    return health.status == "healthy"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Health Check System")
    parser.add_argument(
        "--server",
        action="store_true",
        help="Start health check HTTP server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Server port (default: 8080)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if args.server:
        app = create_health_app()
        if app:
            print(f"Starting health check server on port {args.port}")
            print(f"Endpoints: /health, /health/summary, /ready, /live")
            app.run(host="0.0.0.0", port=args.port)
    elif args.json:
        health = run_health_checks()
        print(json.dumps(health.to_dict(), indent=2))
    else:
        success = print_health_report()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
