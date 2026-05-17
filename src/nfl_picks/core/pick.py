"""Pick domain model - the core output of the system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PickSignal(Enum):
    """Signal strength for a pick."""
    STRONG = "STRONG"  # >= 68% confidence
    LEAN = "LEAN"      # 62-68% confidence
    SKIP = "SKIP"      # < 62% confidence

    @property
    def emoji(self) -> str:
        return {"STRONG": "🟢", "LEAN": "🟡", "SKIP": "⚫"}[self.value]

    @property
    def action(self) -> str:
        return {
            "STRONG": "Bet this",
            "LEAN": "Consider",
            "SKIP": "Skip",
        }[self.value]


@dataclass
class Pick:
    """A single game pick with full context."""

    # Identity
    game_id: str
    season: int
    week: int

    # Teams
    home_team: str
    away_team: str
    game_time: Optional[datetime] = None

    # The pick
    pick_team: str
    pick_type: str = "ML"  # ML, spread, total
    line: Optional[float] = None  # e.g., -3.5 for spread

    # Confidence
    confidence: float = 0.0  # 0-100
    signal: PickSignal = PickSignal.SKIP

    # Reasoning (human-readable bullets)
    reasons: list[str] = field(default_factory=list)

    # Feature values that drove this pick
    features: dict[str, float] = field(default_factory=dict)

    # Metadata
    model_version: str = "v4-rb-ngs"
    created_at: datetime = field(default_factory=datetime.now)

    # Outcome (filled after game settles)
    outcome: Optional[str] = None  # "W", "L", "P" (push)
    actual_score: Optional[str] = None  # "KC 27 - LV 20"
    settled_at: Optional[datetime] = None
    profit: Optional[float] = None  # in units

    @property
    def pick_display(self) -> str:
        """Human-readable pick string."""
        if self.pick_type == "ML":
            return f"{self.pick_team} ML"
        elif self.pick_type == "spread":
            sign = "+" if self.line and self.line > 0 else ""
            return f"{self.pick_team} {sign}{self.line}"
        else:
            return f"{self.pick_team} {self.pick_type}"

    @property
    def matchup(self) -> str:
        """Matchup string."""
        return f"{self.away_team} @ {self.home_team}"

    @classmethod
    def from_prediction(
        cls,
        game_id: str,
        season: int,
        week: int,
        home_team: str,
        away_team: str,
        home_win_prob: float,
        features: dict[str, float],
        model_version: str = "v4-rb-ngs",
    ) -> "Pick":
        """Create a Pick from model prediction."""
        confidence = max(home_win_prob, 1 - home_win_prob) * 100
        pick_team = home_team if home_win_prob > 0.5 else away_team

        if confidence >= 68:
            signal = PickSignal.STRONG
        elif confidence >= 62:
            signal = PickSignal.LEAN
        else:
            signal = PickSignal.SKIP

        reasons = cls._generate_reasons(features, home_win_prob, home_team, away_team)

        return cls(
            game_id=game_id,
            season=season,
            week=week,
            home_team=home_team,
            away_team=away_team,
            pick_team=pick_team,
            confidence=round(confidence, 1),
            signal=signal,
            reasons=reasons,
            features=features,
            model_version=model_version,
        )

    @staticmethod
    def _generate_reasons(
        features: dict[str, float],
        prob: float,
        home: str,
        away: str,
    ) -> list[str]:
        """Generate human-readable reasoning."""
        reasons = []
        better = home if prob > 0.5 else away
        worse = away if prob > 0.5 else home

        epa = features.get("epa_diff", 0)
        if abs(epa) > 0.05:
            reasons.append(f"{better} EPA {epa:+.2f} advantage")

        rb_eff = features.get("diff_rb_efficiency_roll", 0)
        if abs(rb_eff) > 0.3:
            reasons.append(f"{better} superior rushing efficiency")

        conf = max(prob, 1 - prob) * 100
        if conf > 70:
            reasons.append(f"Model highly confident ({conf:.0f}%)")
        elif conf > 65:
            reasons.append(f"Model confident ({conf:.0f}%)")

        if prob > 0.5:
            reasons.append("Home field advantage")

        return reasons or ["Multiple small edges combine"]

    def to_dict(self) -> dict:
        """Serialize for JSON storage."""
        return {
            "game_id": self.game_id,
            "season": self.season,
            "week": self.week,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "pick_team": self.pick_team,
            "pick_type": self.pick_type,
            "line": self.line,
            "confidence": self.confidence,
            "signal": self.signal.value,
            "reasons": self.reasons,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat(),
            "outcome": self.outcome,
            "settled_at": self.settled_at.isoformat() if self.settled_at else None,
            "profit": self.profit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pick":
        """Deserialize from JSON."""
        return cls(
            game_id=data["game_id"],
            season=data["season"],
            week=data["week"],
            home_team=data["home_team"],
            away_team=data["away_team"],
            pick_team=data["pick_team"],
            pick_type=data.get("pick_type", "ML"),
            line=data.get("line"),
            confidence=data["confidence"],
            signal=PickSignal(data["signal"]),
            reasons=data.get("reasons", []),
            model_version=data.get("model_version", "unknown"),
            created_at=datetime.fromisoformat(data["created_at"]),
            outcome=data.get("outcome"),
            settled_at=datetime.fromisoformat(data["settled_at"]) if data.get("settled_at") else None,
            profit=data.get("profit"),
        )
