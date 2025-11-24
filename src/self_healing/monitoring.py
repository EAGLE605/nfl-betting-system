"""Monitoring Layer - System metrics, application metrics, business metrics."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

import psutil

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System-level metrics."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    network_sent: int = 0
    network_recv: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ApplicationMetrics:
    """Application-level metrics."""

    api_latency_ms: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    requests_per_second: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BusinessMetrics:
    """Business-level metrics."""

    picks_generated: int = 0
    bets_placed: int = 0
    win_rate: float = 0.0
    roi: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class MonitoringLayer:
    """Monitoring layer for system health."""

    def __init__(self):
        """Initialize monitoring layer."""
        self.system_metrics: List[SystemMetrics] = []
        self.application_metrics: List[ApplicationMetrics] = []
        self.business_metrics: List[BusinessMetrics] = []

        logger.info("Monitoring layer initialized")

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system metrics."""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        net_io = psutil.net_io_counters()

        metrics = SystemMetrics(
            cpu_percent=cpu,
            memory_percent=memory,
            disk_percent=disk,
            network_sent=net_io.bytes_sent,
            network_recv=net_io.bytes_recv,
        )

        self.system_metrics.append(metrics)
        if len(self.system_metrics) > 1000:
            self.system_metrics = self.system_metrics[-1000:]

        return metrics

    def collect_application_metrics(
        self,
        api_latency: float = 0.0,
        error_rate: float = 0.0,
        cache_hit_rate: float = 0.0,
        requests_per_second: float = 0.0,
    ) -> ApplicationMetrics:
        """Collect application metrics."""
        metrics = ApplicationMetrics(
            api_latency_ms=api_latency,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate,
            requests_per_second=requests_per_second,
        )

        self.application_metrics.append(metrics)
        if len(self.application_metrics) > 1000:
            self.application_metrics = self.application_metrics[-1000:]

        return metrics

    def collect_business_metrics(
        self,
        picks_generated: int = 0,
        bets_placed: int = 0,
        win_rate: float = 0.0,
        roi: float = 0.0,
    ) -> BusinessMetrics:
        """Collect business metrics."""
        metrics = BusinessMetrics(
            picks_generated=picks_generated,
            bets_placed=bets_placed,
            win_rate=win_rate,
            roi=roi,
        )

        self.business_metrics.append(metrics)
        if len(self.business_metrics) > 1000:
            self.business_metrics = self.business_metrics[-1000:]

        return metrics

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get latest metrics."""
        return {
            "system": self.system_metrics[-1].__dict__ if self.system_metrics else {},
            "application": (
                self.application_metrics[-1].__dict__
                if self.application_metrics
                else {}
            ),
            "business": (
                self.business_metrics[-1].__dict__ if self.business_metrics else {}
            ),
        }
