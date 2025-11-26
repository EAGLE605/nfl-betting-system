"""Anomaly Detection - Detect system anomalies using statistical and ML methods."""

import logging
from typing import Any, Dict, List

import numpy as np

from src.self_healing.monitoring import MonitoringLayer

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Anomaly detection using statistical baselines and ML models."""

    def __init__(self, monitoring: MonitoringLayer):
        """Initialize anomaly detector."""
        self.monitoring = monitoring
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.anomalies: List[Dict[str, Any]] = []

        logger.info("Anomaly detector initialized")

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies across all metrics."""
        anomalies = []

        # System metrics anomalies
        if self.monitoring.system_metrics:
            sys_anomalies = self._detect_system_anomalies()
            anomalies.extend(sys_anomalies)

        # Application metrics anomalies
        if self.monitoring.application_metrics:
            app_anomalies = self._detect_application_anomalies()
            anomalies.extend(app_anomalies)

        self.anomalies.extend(anomalies)
        return anomalies

    def _detect_system_anomalies(self) -> List[Dict[str, Any]]:
        """Detect system metric anomalies."""
        anomalies = []

        if len(self.monitoring.system_metrics) < 10:
            return anomalies  # Need enough data

        # Calculate baseline
        cpu_values = [m.cpu_percent for m in self.monitoring.system_metrics[-100:]]
        cpu_mean = np.mean(cpu_values)
        cpu_std = np.std(cpu_values)

        latest = self.monitoring.system_metrics[-1]

        # Detect anomalies (3 sigma rule)
        if latest.cpu_percent > cpu_mean + 3 * cpu_std:
            anomalies.append(
                {
                    "type": "high_cpu",
                    "value": latest.cpu_percent,
                    "threshold": cpu_mean + 3 * cpu_std,
                    "severity": "high",
                    "timestamp": latest.timestamp.isoformat(),
                }
            )

        if latest.memory_percent > 90:
            anomalies.append(
                {
                    "type": "high_memory",
                    "value": latest.memory_percent,
                    "threshold": 90,
                    "severity": "critical",
                    "timestamp": latest.timestamp.isoformat(),
                }
            )

        return anomalies

    def _detect_application_anomalies(self) -> List[Dict[str, Any]]:
        """Detect application metric anomalies."""
        anomalies = []

        if len(self.monitoring.application_metrics) < 10:
            return anomalies

        latest = self.monitoring.application_metrics[-1]

        # High error rate
        if latest.error_rate > 0.1:
            anomalies.append(
                {
                    "type": "high_error_rate",
                    "value": latest.error_rate,
                    "threshold": 0.1,
                    "severity": "high",
                    "timestamp": latest.timestamp.isoformat(),
                }
            )

        # Low cache hit rate
        if latest.cache_hit_rate < 0.5:
            anomalies.append(
                {
                    "type": "low_cache_hit_rate",
                    "value": latest.cache_hit_rate,
                    "threshold": 0.5,
                    "severity": "medium",
                    "timestamp": latest.timestamp.isoformat(),
                }
            )

        return anomalies
