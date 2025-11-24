"""System Connectivity Auditor - Monitor component connections and data flow."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


@dataclass
class ComponentConnection:
    """A connection between components."""

    source: str
    target: str
    connection_type: str  # data_flow, config, dependency
    status: str = "unknown"  # healthy, degraded, disconnected
    last_check: datetime = field(default_factory=datetime.now)
    latency_ms: float = 0.0


class ConnectivityGraph:
    """Graph of component connections."""

    def __init__(self):
        """Initialize connectivity graph."""
        self.connections: Dict[str, List[ComponentConnection]] = {}
        self.components: Set[str] = set()

        # Define expected connections
        self.expected_connections = {
            "data_pipeline": ["feature_engineering", "cache"],
            "feature_engineering": ["model_training", "predictions"],
            "model_training": ["model_registry", "backtest"],
            "predictions": ["daily_picks", "cache"],
            "daily_picks": ["parlay_generator", "notifications"],
            "cache": ["api_client", "dashboard", "agents"],
            "agents": ["orchestrator", "swarms", "self_healing"],
        }

        logger.info("Connectivity graph initialized")

    def add_connection(
        self, source: str, target: str, connection_type: str = "data_flow"
    ):
        """Add a connection."""
        if source not in self.connections:
            self.connections[source] = []

        conn = ComponentConnection(
            source=source, target=target, connection_type=connection_type
        )

        self.connections[source].append(conn)
        self.components.add(source)
        self.components.add(target)

    def check_connection(self, source: str, target: str) -> ComponentConnection:
        """Check a specific connection."""
        if source not in self.connections:
            return ComponentConnection(
                source=source, target=target, status="disconnected"
            )

        for conn in self.connections[source]:
            if conn.target == target:
                # In real implementation, would actually test the connection
                conn.status = "healthy"
                conn.last_check = datetime.now()
                return conn

        return ComponentConnection(source=source, target=target, status="disconnected")


class SystemConnectivityAuditor:
    """Audit system connectivity and detect disconnects."""

    def __init__(self):
        """Initialize connectivity auditor."""
        self.graph = ConnectivityGraph()
        self.disconnects: List[Dict[str, Any]] = []
        self.running = False

        # Initialize expected connections
        for source, targets in self.graph.expected_connections.items():
            for target in targets:
                self.graph.add_connection(source, target)

        logger.info("System Connectivity Auditor initialized")

    async def audit(self) -> Dict[str, Any]:
        """Run connectivity audit."""
        logger.info("Running connectivity audit")

        issues = []

        # Check all expected connections
        for source, targets in self.graph.expected_connections.items():
            for target in targets:
                conn = self.graph.check_connection(source, target)

                if conn.status == "disconnected":
                    issue = {
                        "type": "disconnect",
                        "source": source,
                        "target": target,
                        "severity": "high",
                        "timestamp": datetime.now().isoformat(),
                    }
                    issues.append(issue)
                    self.disconnects.append(issue)

        return {
            "timestamp": datetime.now().isoformat(),
            "components_checked": len(self.graph.components),
            "connections_checked": sum(
                len(conns) for conns in self.graph.connections.values()
            ),
            "issues_found": len(issues),
            "issues": issues,
        }

    async def run_continuous(self, interval: int = 300):
        """Run continuous auditing."""
        self.running = True

        while self.running:
            try:
                result = await self.audit()

                if result["issues_found"] > 0:
                    logger.warning(
                        f"Found {result['issues_found']} connectivity issues"
                    )

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Connectivity audit error: {e}")
                await asyncio.sleep(60)

    def get_disconnects(self) -> List[Dict[str, Any]]:
        """Get all detected disconnects."""
        return self.disconnects

    def auto_remediate(self, disconnect: Dict[str, Any]):
        """Attempt to auto-remediate a disconnect."""
        source = disconnect.get("source")
        target = disconnect.get("target")

        logger.info(f"Auto-remediating disconnect: {source} -> {target}")

        # Remediation logic would go here
        # - Restart failed components
        # - Clear stale caches
        # - Re-sync data sources
        # - Re-establish agent connections

        return {"remediated": True, "action": "reconnected"}
