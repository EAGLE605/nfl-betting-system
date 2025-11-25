"""Database schema definitions for all tables.

Centralizes schema knowledge for schema-aware database operations.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ColumnSchema:
    """Schema for a single column."""

    name: str
    type: str  # SQLite type: TEXT, INTEGER, REAL, BLOB
    nullable: bool = True
    primary_key: bool = False
    default: Optional[any] = None


@dataclass
class TableSchema:
    """Schema for a database table."""

    name: str
    columns: List[ColumnSchema]
    indexes: List[str] = None  # List of column names to index
    description: str = ""

    def __post_init__(self):
        if self.indexes is None:
            self.indexes = []

    def get_column(self, name: str) -> Optional[ColumnSchema]:
        """Get column schema by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_column_names(self) -> List[str]:
        """Get list of all column names."""
        return [col.name for col in self.columns]

    def create_table_sql(self) -> str:
        """Generate CREATE TABLE SQL statement."""
        col_defs = []
        for col in self.columns:
            parts = [col.name, col.type]
            if col.primary_key:
                parts.append("PRIMARY KEY")
            if not col.nullable:
                parts.append("NOT NULL")
            if col.default is not None:
                parts.append(f"DEFAULT {col.default}")
            col_defs.append(" ".join(parts))

        sql = f"CREATE TABLE IF NOT EXISTS {self.name} (\n"
        sql += ",\n".join(f"  {col_def}" for col_def in col_defs)
        sql += "\n)"

        return sql

    def create_index_sql(self) -> List[str]:
        """Generate CREATE INDEX SQL statements."""
        statements = []
        for col_name in self.indexes:
            idx_name = f"idx_{self.name}_{col_name}"
            sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {self.name}({col_name})"
            statements.append(sql)
        return statements


class DatabaseSchema:
    """Central registry of all database schemas."""

    # Table: odds_snapshots - Historical odds data
    ODDS_SNAPSHOTS = TableSchema(
        name="odds_snapshots",
        description="Historical betting odds snapshots for line movement analysis",
        columns=[
            ColumnSchema("id", "INTEGER", primary_key=True, nullable=False),
            ColumnSchema("game_id", "TEXT", nullable=False),
            ColumnSchema("commence_time", "TEXT", nullable=False),
            ColumnSchema("home_team", "TEXT", nullable=False),
            ColumnSchema("away_team", "TEXT", nullable=False),
            ColumnSchema("sport_key", "TEXT", default="'americanfootball_nfl'"),
            ColumnSchema("bookmaker", "TEXT"),
            ColumnSchema("market_key", "TEXT"),  # h2h, spreads, totals
            ColumnSchema("home_odds", "REAL"),  # Decimal odds for home
            ColumnSchema("away_odds", "REAL"),  # Decimal odds for away
            ColumnSchema("home_point", "REAL"),  # Spread for home
            ColumnSchema("away_point", "REAL"),  # Spread for away
            ColumnSchema("over_under", "REAL"),  # Total points line
            ColumnSchema("timestamp", "TEXT", nullable=False),  # When snapshot taken
        ],
        indexes=["game_id", "commence_time", "timestamp"],
    )

    # Table: predictions - Model predictions
    PREDICTIONS = TableSchema(
        name="predictions",
        description="Model predictions for games",
        columns=[
            ColumnSchema("id", "INTEGER", primary_key=True, nullable=False),
            ColumnSchema("game_id", "TEXT", nullable=False),
            ColumnSchema("model_name", "TEXT", nullable=False),
            ColumnSchema("model_version", "TEXT"),
            ColumnSchema("gameday", "TEXT", nullable=False),
            ColumnSchema("home_team", "TEXT", nullable=False),
            ColumnSchema("away_team", "TEXT", nullable=False),
            ColumnSchema("pred_prob", "REAL", nullable=False),  # Probability home wins
            ColumnSchema("pick", "TEXT"),  # "home" or "away"
            ColumnSchema("confidence", "REAL"),  # Confidence score (0-1)
            ColumnSchema("features_used", "TEXT"),  # JSON of feature names/values
            ColumnSchema("created_at", "TEXT", nullable=False),
        ],
        indexes=["game_id", "model_name", "gameday"],
    )

    # Table: bet_history - Actual bets placed
    BET_HISTORY = TableSchema(
        name="bet_history",
        description="Record of bets placed",
        columns=[
            ColumnSchema("bet_id", "INTEGER", primary_key=True, nullable=False),
            ColumnSchema("game_id", "TEXT", nullable=False),
            ColumnSchema("gameday", "TEXT", nullable=False),
            ColumnSchema("team", "TEXT", nullable=False),  # Team bet on
            ColumnSchema("bet_type", "TEXT", nullable=False),  # moneyline, spread, total
            ColumnSchema("amount", "REAL", nullable=False),  # Bet amount
            ColumnSchema("odds", "REAL", nullable=False),  # Decimal odds
            ColumnSchema("bookmaker", "TEXT"),
            ColumnSchema("result", "TEXT"),  # "win", "loss", "push", "pending"
            ColumnSchema("profit", "REAL"),  # Actual profit/loss
            ColumnSchema("placed_at", "TEXT", nullable=False),
            ColumnSchema("settled_at", "TEXT"),
        ],
        indexes=["game_id", "gameday", "result"],
    )

    # Table: performance_metrics - Daily/weekly performance tracking
    PERFORMANCE = TableSchema(
        name="performance_metrics",
        description="System performance metrics over time",
        columns=[
            ColumnSchema("id", "INTEGER", primary_key=True, nullable=False),
            ColumnSchema("date", "TEXT", nullable=False),  # YYYY-MM-DD
            ColumnSchema("period_type", "TEXT"),  # "daily", "weekly", "monthly"
            ColumnSchema("roi", "REAL"),  # Return on investment
            ColumnSchema("win_rate", "REAL"),  # Win rate (0-1)
            ColumnSchema("total_bets", "INTEGER"),
            ColumnSchema("wins", "INTEGER"),
            ColumnSchema("losses", "INTEGER"),
            ColumnSchema("pushes", "INTEGER"),
            ColumnSchema("bankroll", "REAL"),
            ColumnSchema("profit", "REAL"),
            ColumnSchema("sharpe_ratio", "REAL"),
            ColumnSchema("max_drawdown", "REAL"),
            ColumnSchema("avg_odds", "REAL"),
            ColumnSchema("clv", "REAL"),  # Closing line value
        ],
        indexes=["date", "period_type"],
    )

    # Table: agent_performance - Per-agent performance tracking
    AGENT_PERFORMANCE = TableSchema(
        name="agent_performance",
        description="Track individual agent prediction performance",
        columns=[
            ColumnSchema("id", "INTEGER", primary_key=True, nullable=False),
            ColumnSchema("agent_id", "TEXT", nullable=False),
            ColumnSchema("model_name", "TEXT"),
            ColumnSchema("date", "TEXT", nullable=False),
            ColumnSchema("predictions_made", "INTEGER"),
            ColumnSchema("accuracy", "REAL"),  # Prediction accuracy
            ColumnSchema("avg_confidence", "REAL"),
            ColumnSchema("roi", "REAL"),
            ColumnSchema("brier_score", "REAL"),  # Calibration metric
        ],
        indexes=["agent_id", "date"],
    )

    @classmethod
    def get_all_schemas(cls) -> Dict[str, TableSchema]:
        """Get all defined table schemas."""
        return {
            "odds_snapshots": cls.ODDS_SNAPSHOTS,
            "predictions": cls.PREDICTIONS,
            "bet_history": cls.BET_HISTORY,
            "performance_metrics": cls.PERFORMANCE,
            "agent_performance": cls.AGENT_PERFORMANCE,
        }

    @classmethod
    def get_schema(cls, table_name: str) -> Optional[TableSchema]:
        """Get schema for a specific table."""
        return cls.get_all_schemas().get(table_name)

    @classmethod
    def initialize_database(cls, conn) -> None:
        """
        Initialize database with all tables and indexes.

        Args:
            conn: SQLite connection
        """
        cursor = conn.cursor()

        for table_name, schema in cls.get_all_schemas().items():
            # Create table
            cursor.execute(schema.create_table_sql())

            # Create indexes
            for idx_sql in schema.create_index_sql():
                cursor.execute(idx_sql)

        conn.commit()
