"""Worker Agents (Level 3) - API Manager, Database, Notification, Logging, Self-Healing."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from src.agents.base_agent import AgentCapability, BaseAgent
from src.api.request_orchestrator import Priority, RequestOrchestrator

logger = logging.getLogger(__name__)


class APIManagerAgent(BaseAgent):
    """API Manager Agent - Rate limiting, caching, retries."""

    def __init__(self, orchestrator: RequestOrchestrator):
        super().__init__(
            agent_id="api_manager_001",
            agent_name="API Manager Agent",
            capabilities=[AgentCapability.TOOLS],
        )
        self.orchestrator = orchestrator
        self.register_tool("queue_request", self._queue_request, "Queue API request")

    async def run(self):
        while self.running:
            await asyncio.sleep(60)

    async def _queue_request(
        self, endpoint: str, params: Dict, priority: Priority = Priority.NORMAL
    ):
        from src.api.request_orchestrator import PriorityRequest

        request = PriorityRequest(
            endpoint=endpoint, params=params, priority=priority, callback=lambda x: None
        )
        return self.orchestrator.enqueue(request)


class DatabaseAgent(BaseAgent):
    """Database Agent - CRUD operations, query optimization."""

    def __init__(self):
        super().__init__(
            agent_id="database_001",
            agent_name="Database Agent",
            capabilities=[AgentCapability.TOOLS, AgentCapability.MEMORY],
        )
        self.register_tool("query", self._query, "Query database")
        self.register_tool("store", self._store, "Store data")

    async def run(self):
        while self.running:
            await asyncio.sleep(60)

    async def _query(self, query: str) -> Dict[str, Any]:
        """Query database."""
        import sqlite3
        from pathlib import Path

        # Connect to odds_history.db
        db_path = Path("data/odds_history.db")
        if not db_path.exists():
            return {"results": [], "count": 0, "error": "Database not found"}

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return {"results": rows, "count": len(rows)}
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return {"results": [], "count": 0, "error": str(e)}

    async def _store(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store data in database."""
        import sqlite3
        from datetime import datetime
        from pathlib import Path

        db_path = Path("data/odds_history.db")
        if not db_path.exists():
            return {"stored": False, "error": "Database not found"}

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Simple insert (would need proper schema handling)
            if table == "odds_snapshots":
                cursor.execute(
                    """
                    INSERT INTO odds_snapshots (
                        fetch_timestamp, game_id, home_team, away_team,
                        commence_time, bookmaker, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now().isoformat(),
                        data.get("game_id", ""),
                        data.get("home_team", ""),
                        data.get("away_team", ""),
                        data.get("commence_time", ""),
                        data.get("bookmaker", ""),
                        str(data),
                    ),
                )

            conn.commit()
            row_id = cursor.lastrowid
            conn.close()
            return {"stored": True, "id": row_id}
        except Exception as e:
            logger.error(f"Database store error: {e}")
            return {"stored": False, "error": str(e)}


class NotificationAgent(BaseAgent):
    """Notification Agent - Alerts, reports, dashboards."""

    def __init__(self):
        super().__init__(
            agent_id="notification_001",
            agent_name="Notification Agent",
            capabilities=[AgentCapability.COMMUNICATION],
        )
        self.register_tool("send_alert", self._send_alert, "Send alert")
        self.register_tool("send_report", self._send_report, "Send report")

    async def run(self):
        while self.running:
            await asyncio.sleep(60)

    async def _send_alert(self, message: str, severity: str = "info"):
        logger.info(f"Alert [{severity}]: {message}")
        return {"sent": True}

    async def _send_report(self, report: Dict[str, Any]):
        logger.info(f"Report: {report.get('title', 'Untitled')}")
        return {"sent": True}


class LoggingAgent(BaseAgent):
    """Logging Agent - System health, debugging, audit trails."""

    def __init__(self):
        super().__init__(
            agent_id="logging_001",
            agent_name="Logging Agent",
            capabilities=[AgentCapability.MEMORY],
        )
        self.logs: List[Dict[str, Any]] = []
        self.register_tool("log", self._log, "Log event")
        self.register_tool("get_logs", self._get_logs, "Get logs")

    async def run(self):
        while self.running:
            await asyncio.sleep(60)

    async def _log(self, level: str, message: str, metadata: Dict = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "metadata": metadata or {},
        }
        self.logs.append(log_entry)
        logger.log(getattr(logging, level.upper(), logging.INFO), message)
        return {"logged": True}

    async def _get_logs(self, level: str = None, limit: int = 100) -> Dict[str, Any]:
        filtered = (
            self.logs if not level else [l for l in self.logs if l["level"] == level]
        )
        return {"logs": filtered[-limit:], "count": len(filtered)}


class SelfHealingAgent(BaseAgent):
    """Self-Healing Agent - Detect & fix system issues."""

    def __init__(self):
        super().__init__(
            agent_id="self_healing_001",
            agent_name="Self-Healing Agent",
            capabilities=[AgentCapability.REASONING, AgentCapability.TOOLS],
        )
        self.register_tool("detect_issues", self._detect_issues, "Detect system issues")
        self.register_tool("fix_issue", self._fix_issue, "Fix an issue")

    async def run(self):
        while self.running:
            try:
                issues = await self._detect_issues()
                for issue in issues:
                    await self._fix_issue(issue)
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Self-Healing error: {e}")
                await asyncio.sleep(10)

    async def _detect_issues(self) -> List[Dict[str, Any]]:
        return []

    async def _fix_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Fixing issue: {issue.get('type')}")
        return {"fixed": True, "issue_id": issue.get("id")}
