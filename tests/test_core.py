"""Tests for core nfl_picks modules."""

import sys
from pathlib import Path

import pytest

# Add src to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestPickSignal:
    """Tests for PickSignal enum."""

    def test_signal_values(self):
        from nfl_picks.core import PickSignal
        assert PickSignal.STRONG.value == "STRONG"
        assert PickSignal.LEAN.value == "LEAN"
        assert PickSignal.SKIP.value == "SKIP"

    def test_signal_emoji(self):
        from nfl_picks.core import PickSignal
        assert PickSignal.STRONG.emoji == "🟢"
        assert PickSignal.LEAN.emoji == "🟡"
        assert PickSignal.SKIP.emoji == "⚫"


class TestPick:
    """Tests for Pick dataclass."""

    def test_pick_creation(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick(
            game_id="2026_01_KC_BAL",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            pick_team="KC",
            confidence=71.2,
            signal=PickSignal.STRONG,
        )
        assert pick.game_id == "2026_01_KC_BAL"
        assert pick.pick_team == "KC"
        assert pick.confidence == 71.2

    def test_pick_display(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick(
            game_id="test",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            pick_team="KC",
            pick_type="ML",
            confidence=70,
            signal=PickSignal.STRONG,
        )
        assert pick.pick_display == "KC ML"

    def test_pick_display_spread(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick(
            game_id="test",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            pick_team="KC",
            pick_type="spread",
            line=-3.5,
            confidence=70,
            signal=PickSignal.STRONG,
        )
        assert pick.pick_display == "KC -3.5"

    def test_matchup(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick(
            game_id="test",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            pick_team="KC",
            confidence=70,
            signal=PickSignal.STRONG,
        )
        assert pick.matchup == "BAL @ KC"

    def test_from_prediction_strong(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick.from_prediction(
            game_id="test",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            home_win_prob=0.72,
            features={"epa_diff": 0.15},
        )
        assert pick.signal == PickSignal.STRONG
        assert pick.pick_team == "KC"
        assert pick.confidence == 72.0

    def test_from_prediction_lean(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick.from_prediction(
            game_id="test",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            home_win_prob=0.65,
            features={},
        )
        assert pick.signal == PickSignal.LEAN
        assert pick.confidence == 65.0

    def test_from_prediction_skip(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick.from_prediction(
            game_id="test",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            home_win_prob=0.55,
            features={},
        )
        assert pick.signal == PickSignal.SKIP
        assert pick.confidence == 55.0

    def test_from_prediction_away_team(self):
        from nfl_picks.core import Pick, PickSignal
        pick = Pick.from_prediction(
            game_id="test",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            home_win_prob=0.28,  # Away team favored
            features={},
        )
        assert pick.pick_team == "BAL"
        assert pick.confidence == 72.0

    def test_to_dict_and_back(self):
        from nfl_picks.core import Pick, PickSignal
        original = Pick(
            game_id="2026_01_KC_BAL",
            season=2026,
            week=1,
            home_team="KC",
            away_team="BAL",
            pick_team="KC",
            confidence=71.2,
            signal=PickSignal.STRONG,
            reasons=["EPA advantage", "Home field"],
        )
        data = original.to_dict()
        restored = Pick.from_dict(data)
        assert restored.game_id == original.game_id
        assert restored.confidence == original.confidence
        assert restored.signal == original.signal


class TestConfig:
    """Tests for configuration."""

    def test_default_settings(self):
        from nfl_picks.config import Settings
        s = Settings()
        assert s.confidence_threshold == 0.62
        assert s.model_version == "v4-rb-ngs"

    def test_calculated_unit_size(self):
        from nfl_picks.config import Settings
        s = Settings(bankroll=10000)
        assert s.calculated_unit_size == 100  # 1% of 10000

    def test_explicit_unit_size(self):
        from nfl_picks.config import Settings
        s = Settings(bankroll=10000, unit_size=50)
        assert s.calculated_unit_size == 50  # Explicit overrides calculated
