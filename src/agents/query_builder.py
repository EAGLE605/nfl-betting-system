"""Schema-aware query builder for database operations.

Provides type-safe, validated database queries using schema definitions.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.agents.database_schemas import DatabaseSchema

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Build schema-aware queries for database operations."""

    def __init__(self, conn):
        """
        Initialize query builder.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn
        self.cursor = conn.cursor()

    def get_odds_for_game(
        self, game_id: str, market_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get latest odds for a game.

        Args:
            game_id: Game identifier
            market_key: Optional market type filter (h2h, spreads, totals)

        Returns:
            List of odds dictionaries
        """
        schema = DatabaseSchema.ODDS_SNAPSHOTS

        # Build query
        query = f"""
            SELECT * FROM {schema.name}
            WHERE game_id = ?
        """
        params = [game_id]

        if market_key:
            query += " AND market_key = ?"
            params.append(market_key)

        query += " ORDER BY timestamp DESC"

        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            # Convert to dictionaries
            columns = schema.get_column_names()
            results = []
            for row in rows:
                result = dict(zip(columns, row))
                results.append(result)

            logger.debug(f"Found {len(results)} odds records for game {game_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to get odds for game {game_id}: {e}")
            return []

    def get_line_movement(
        self, game_id: str, hours: int = 24, bookmaker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical line movement for a game.

        Args:
            game_id: Game identifier
            hours: Look back period in hours
            bookmaker: Optional bookmaker filter

        Returns:
            List of odds snapshots ordered by time
        """
        schema = DatabaseSchema.ODDS_SNAPSHOTS

        # Calculate cutoff time
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        query = f"""
            SELECT * FROM {schema.name}
            WHERE game_id = ?
            AND timestamp >= ?
        """
        params = [game_id, cutoff_str]

        if bookmaker:
            query += " AND bookmaker = ?"
            params.append(bookmaker)

        query += " ORDER BY timestamp ASC"

        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            columns = schema.get_column_names()
            results = [dict(zip(columns, row)) for row in rows]

            logger.debug(
                f"Found {len(results)} line movements for game {game_id} "
                f"in last {hours} hours"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to get line movement for game {game_id}: {e}")
            return []

    def store_prediction(self, prediction: Dict[str, Any]) -> bool:
        """
        Store a model prediction.

        Args:
            prediction: Dict with required fields:
                - game_id, model_name, gameday, home_team, away_team
                - pred_prob, pick (optional), confidence (optional)

        Returns:
            True if successful
        """
        schema = DatabaseSchema.PREDICTIONS

        # Validate required fields
        required = [
            "game_id",
            "model_name",
            "gameday",
            "home_team",
            "away_team",
            "pred_prob",
        ]
        missing = [f for f in required if f not in prediction]
        if missing:
            logger.error(f"Missing required fields for prediction: {missing}")
            return False

        # Build insert query
        columns = [
            "game_id",
            "model_name",
            "model_version",
            "gameday",
            "home_team",
            "away_team",
            "pred_prob",
            "pick",
            "confidence",
            "features_used",
            "created_at",
        ]

        # Prepare values
        values = [
            prediction.get("game_id"),
            prediction.get("model_name"),
            prediction.get("model_version"),
            prediction.get("gameday"),
            prediction.get("home_team"),
            prediction.get("away_team"),
            prediction.get("pred_prob"),
            prediction.get("pick"),
            prediction.get("confidence"),
            prediction.get("features_used"),
            prediction.get("created_at", datetime.now().isoformat()),
        ]

        placeholders = ",".join(["?"] * len(columns))
        query = f"""
            INSERT INTO {schema.name} ({','.join(columns)})
            VALUES ({placeholders})
        """

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.debug(f"Stored prediction for game {prediction['game_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
            self.conn.rollback()
            return False

    def store_bet(self, bet: Dict[str, Any]) -> bool:
        """
        Store a bet record.

        Args:
            bet: Dict with required fields:
                - game_id, gameday, team, bet_type, amount, odds

        Returns:
            True if successful
        """
        schema = DatabaseSchema.BET_HISTORY

        # Validate required fields
        required = ["game_id", "gameday", "team", "bet_type", "amount", "odds"]
        missing = [f for f in required if f not in bet]
        if missing:
            logger.error(f"Missing required fields for bet: {missing}")
            return False

        columns = [
            "game_id",
            "gameday",
            "team",
            "bet_type",
            "amount",
            "odds",
            "bookmaker",
            "result",
            "profit",
            "placed_at",
            "settled_at",
        ]

        values = [
            bet.get("game_id"),
            bet.get("gameday"),
            bet.get("team"),
            bet.get("bet_type"),
            bet.get("amount"),
            bet.get("odds"),
            bet.get("bookmaker"),
            bet.get("result", "pending"),
            bet.get("profit"),
            bet.get("placed_at", datetime.now().isoformat()),
            bet.get("settled_at"),
        ]

        placeholders = ",".join(["?"] * len(columns))
        query = f"""
            INSERT INTO {schema.name} ({','.join(columns)})
            VALUES ({placeholders})
        """

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.info(
                f"Stored bet: {bet['team']} {bet['bet_type']} "
                f"${bet['amount']:.2f} @ {bet['odds']}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store bet: {e}")
            self.conn.rollback()
            return False

    def get_recent_performance(
        self, days: int = 7, period_type: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Get recent performance metrics.

        Args:
            days: Number of days to look back
            period_type: Type of metrics (daily, weekly, monthly)

        Returns:
            List of performance metric dictionaries
        """
        schema = DatabaseSchema.PERFORMANCE

        # Calculate cutoff date
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        query = f"""
            SELECT * FROM {schema.name}
            WHERE date >= ?
            AND period_type = ?
            ORDER BY date DESC
        """

        try:
            self.cursor.execute(query, [cutoff_str, period_type])
            rows = self.cursor.fetchall()

            columns = schema.get_column_names()
            results = [dict(zip(columns, row)) for row in rows]

            logger.debug(
                f"Found {len(results)} {period_type} performance records "
                f"from last {days} days"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to get recent performance: {e}")
            return []

    def store_performance_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Store performance metrics.

        Args:
            metrics: Dict with performance data

        Returns:
            True if successful
        """
        schema = DatabaseSchema.PERFORMANCE

        columns = [
            "date",
            "period_type",
            "roi",
            "win_rate",
            "total_bets",
            "wins",
            "losses",
            "pushes",
            "bankroll",
            "profit",
            "sharpe_ratio",
            "max_drawdown",
            "avg_odds",
            "clv",
        ]

        values = [metrics.get(col) for col in columns]

        placeholders = ",".join(["?"] * len(columns))
        query = f"""
            INSERT INTO {schema.name} ({','.join(columns)})
            VALUES ({placeholders})
        """

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.debug(f"Stored performance metrics for {metrics.get('date')}")
            return True

        except Exception as e:
            logger.error(f"Failed to store performance metrics: {e}")
            self.conn.rollback()
            return False

    def get_agent_performance(
        self, agent_id: str, days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for a specific agent.

        Args:
            agent_id: Agent identifier
            days: Optional number of days to look back

        Returns:
            List of agent performance records
        """
        schema = DatabaseSchema.AGENT_PERFORMANCE

        query = f"""
            SELECT * FROM {schema.name}
            WHERE agent_id = ?
        """
        params = [agent_id]

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff.strftime("%Y-%m-%d")
            query += " AND date >= ?"
            params.append(cutoff_str)

        query += " ORDER BY date DESC"

        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            columns = schema.get_column_names()
            results = [dict(zip(columns, row)) for row in rows]

            logger.debug(f"Found {len(results)} performance records for {agent_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to get agent performance for {agent_id}: {e}")
            return []

    def store_agent_performance(self, performance: Dict[str, Any]) -> bool:
        """
        Store agent performance metrics.

        Args:
            performance: Dict with agent performance data

        Returns:
            True if successful
        """
        schema = DatabaseSchema.AGENT_PERFORMANCE

        required = ["agent_id", "date"]
        missing = [f for f in required if f not in performance]
        if missing:
            logger.error(f"Missing required fields for agent performance: {missing}")
            return False

        columns = [
            "agent_id",
            "model_name",
            "date",
            "predictions_made",
            "accuracy",
            "avg_confidence",
            "roi",
            "brier_score",
        ]

        values = [performance.get(col) for col in columns]

        placeholders = ",".join(["?"] * len(columns))
        query = f"""
            INSERT INTO {schema.name} ({','.join(columns)})
            VALUES ({placeholders})
        """

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.debug(
                f"Stored agent performance for {performance['agent_id']} "
                f"on {performance['date']}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store agent performance: {e}")
            self.conn.rollback()
            return False

    def get_pending_bets(self) -> List[Dict[str, Any]]:
        """
        Get all pending (unsettled) bets.

        Returns:
            List of pending bet records
        """
        schema = DatabaseSchema.BET_HISTORY

        query = f"""
            SELECT * FROM {schema.name}
            WHERE result = 'pending'
            ORDER BY placed_at DESC
        """

        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            columns = schema.get_column_names()
            results = [dict(zip(columns, row)) for row in rows]

            logger.debug(f"Found {len(results)} pending bets")
            return results

        except Exception as e:
            logger.error(f"Failed to get pending bets: {e}")
            return []

    def update_bet_result(
        self, bet_id: int, result: str, profit: float, settled_at: Optional[str] = None
    ) -> bool:
        """
        Update bet result after settlement.

        Args:
            bet_id: Bet identifier
            result: Result (win, loss, push)
            profit: Actual profit/loss
            settled_at: Settlement timestamp

        Returns:
            True if successful
        """
        schema = DatabaseSchema.BET_HISTORY

        if settled_at is None:
            settled_at = datetime.now().isoformat()

        query = f"""
            UPDATE {schema.name}
            SET result = ?, profit = ?, settled_at = ?
            WHERE bet_id = ?
        """

        try:
            self.cursor.execute(query, [result, profit, settled_at, bet_id])
            self.conn.commit()
            logger.info(f"Updated bet {bet_id}: {result}, profit=${profit:.2f}")
            return True

        except Exception as e:
            logger.error(f"Failed to update bet result for bet {bet_id}: {e}")
            self.conn.rollback()
            return False

    def store_odds_snapshot(self, odds: Dict[str, Any]) -> bool:
        """
        Store an odds snapshot for line movement tracking.

        Args:
            odds: Dict with odds data

        Returns:
            True if successful
        """
        schema = DatabaseSchema.ODDS_SNAPSHOTS

        required = ["game_id", "commence_time", "home_team", "away_team", "timestamp"]
        missing = [f for f in required if f not in odds]
        if missing:
            logger.error(f"Missing required fields for odds snapshot: {missing}")
            return False

        columns = [
            "game_id",
            "commence_time",
            "home_team",
            "away_team",
            "sport_key",
            "bookmaker",
            "market_key",
            "home_odds",
            "away_odds",
            "home_point",
            "away_point",
            "over_under",
            "timestamp",
        ]

        values = [odds.get(col) for col in columns]

        placeholders = ",".join(["?"] * len(columns))
        query = f"""
            INSERT INTO {schema.name} ({','.join(columns)})
            VALUES ({placeholders})
        """

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.debug(f"Stored odds snapshot for game {odds['game_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to store odds snapshot: {e}")
            self.conn.rollback()
            return False
