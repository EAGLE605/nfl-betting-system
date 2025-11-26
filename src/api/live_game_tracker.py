"""
Live Game Tracker - Real-time NFL game status updates

Uses ESPN's free public API to track live game data.
Automatically refreshes during NFL game windows.

BEGINNER-FRIENDLY EXPLANATION:
- This module fetches live scores from ESPN (like checking ESPN.com)
- It converts UTC timestamps to your local timezone
- It caches data to avoid hammering ESPN's servers
- It knows when to refresh (game days) and when to pause (off days)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pytz

from .espn_client import ESPNClient

logger = logging.getLogger(__name__)


class GameStatus(Enum):
    """
    Game status types.

    BEGINNER NOTE: Enums are like labeled constants.
    Instead of checking if status == 1, we check if status == GameStatus.PREGAME
    Much more readable!
    """
    SCHEDULED = "scheduled"  # Game hasn't started yet
    PREGAME = "pregame"      # Pregame show, about to start
    IN_PROGRESS = "in"       # Game is live right now!
    HALFTIME = "halftime"    # At halftime
    FINAL = "final"          # Game over
    POSTPONED = "postponed"  # Weather/other delay
    CANCELED = "canceled"    # Game canceled


class LiveGameTracker:
    """
    Track live NFL games with automatic refresh logic.

    BEGINNER NOTE: This class manages all the complexity of:
    - When to fetch new data (only during games)
    - How to convert timezones
    - What to cache and what to refresh
    """

    def __init__(self, timezone_str: str = "America/New_York"):
        """
        Initialize the tracker.

        Args:
            timezone_str: Your local timezone (e.g., "America/New_York", "America/Los_Angeles")
                         Full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

        BEGINNER NOTE: Timezones are HARD! ESPN gives us UTC times.
        We convert them to YOUR timezone so you see correct local times.
        """
        self.espn = ESPNClient()
        self.user_timezone = pytz.timezone(timezone_str)

        # Cache settings
        self._cache = {}
        self._cache_timestamp = None
        self._cache_ttl_live = timedelta(minutes=5)      # Refresh every 5 min during live games
        self._cache_ttl_pregame = timedelta(minutes=30)   # Refresh every 30 min before games
        self._cache_ttl_offday = timedelta(hours=24)      # Refresh once a day when no games

    def get_current_games(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all games for the current week with live status.

        Args:
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            List of games with status, scores, and times

        BEGINNER NOTE: This is the main function you'll call.
        It returns a list of dicts, each dict is one game.
        """
        # Check cache first (unless force refresh)
        if not force_refresh and self._is_cache_valid():
            logger.info("Using cached game data")
            return self._cache.get("games", [])

        logger.info("Fetching fresh game data from ESPN")

        # Fetch from ESPN
        scoreboard = self.espn.get_scoreboard()

        if not scoreboard or "events" not in scoreboard:
            logger.warning("No games found in ESPN response")
            return []

        # Parse games
        games = []
        for event in scoreboard["events"]:
            try:
                game = self._parse_game(event)
                games.append(game)
            except Exception as e:
                logger.error(f"Error parsing game: {e}")
                continue

        # Update cache
        self._cache = {"games": games}
        self._cache_timestamp = datetime.now()

        logger.info(f"Fetched {len(games)} games")
        return games

    def _parse_game(self, event: Dict) -> Dict:
        """
        Parse a single game from ESPN's data structure.

        BEGINNER NOTE: ESPN returns complex nested JSON.
        This function extracts the useful parts into a simple dict.

        Args:
            event: Raw ESPN event data

        Returns:
            Clean game dict with status, teams, scores, time
        """
        # Extract basic info
        game_id = event.get("id", "")
        name = event.get("name", "")  # "Team A at Team B"

        # Get competition (ESPN wraps game data in "competitions")
        competition = event.get("competitions", [{}])[0]

        # Get teams (home/away)
        competitors = competition.get("competitors", [])
        home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})

        # Get status
        status_data = competition.get("status", {})
        status_type = status_data.get("type", {}).get("state", "").lower()
        status_detail = status_data.get("type", {}).get("detail", "")

        # Parse status into our enum
        game_status = self._parse_status(status_type, status_detail)

        # Get scores (if game started)
        home_score = int(home_team.get("score", 0))
        away_score = int(away_team.get("score", 0))

        # Get game time
        game_time_utc = self._parse_datetime(event.get("date"))
        game_time_local = self._convert_to_local(game_time_utc)

        # Get live details (quarter, clock)
        period = status_data.get("period", 0)
        clock = status_data.get("displayClock", "0:00")

        return {
            "game_id": game_id,
            "name": name,
            "home_team": home_team.get("team", {}).get("abbreviation", ""),
            "home_team_full": home_team.get("team", {}).get("displayName", ""),
            "home_score": home_score,
            "away_team": away_team.get("team", {}).get("abbreviation", ""),
            "away_team_full": away_team.get("team", {}).get("displayName", ""),
            "away_score": away_score,
            "status": game_status.value,
            "status_detail": status_detail,
            "period": period,
            "clock": clock,
            "game_time_utc": game_time_utc,
            "game_time_local": game_time_local,
            "is_live": game_status == GameStatus.IN_PROGRESS,
            "is_final": game_status == GameStatus.FINAL,
            "is_upcoming": game_status in [GameStatus.SCHEDULED, GameStatus.PREGAME],
        }

    def _parse_status(self, status_type: str, status_detail: str) -> GameStatus:
        """
        Convert ESPN status to our GameStatus enum.

        BEGINNER NOTE: ESPN uses different status strings.
        We standardize them into our clean enum.
        """
        status_type = status_type.lower()

        if "pre" in status_type or "scheduled" in status_type:
            return GameStatus.SCHEDULED
        elif "in" in status_type or "live" in status_type:
            if "halftime" in status_detail.lower():
                return GameStatus.HALFTIME
            return GameStatus.IN_PROGRESS
        elif "final" in status_type or "post" in status_type:
            return GameStatus.FINAL
        elif "postponed" in status_type or "delayed" in status_type:
            return GameStatus.POSTPONED
        elif "canceled" in status_type or "cancelled" in status_type:
            return GameStatus.CANCELED
        else:
            return GameStatus.SCHEDULED

    def _parse_datetime(self, date_str: str) -> datetime:
        """
        Parse ESPN's datetime string.

        BEGINNER NOTE: ESPN gives us ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
        Python's datetime can parse this directly.
        """
        try:
            # ESPN uses ISO 8601: "2025-11-25T20:15:00Z"
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception as e:
            logger.warning(f"Could not parse datetime '{date_str}': {e}")
            return datetime.now(timezone.utc)

    def _convert_to_local(self, dt: datetime) -> datetime:
        """
        Convert UTC datetime to user's local timezone.

        BEGINNER NOTE: All times from ESPN are in UTC (Universal Time).
        This converts to YOUR timezone (e.g., Eastern, Pacific, etc.)
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(self.user_timezone)

    def _is_cache_valid(self) -> bool:
        """
        Check if cached data is still valid.

        BEGINNER NOTE: We don't want to hit ESPN's API every second!
        - Live games: refresh every 5 minutes
        - Pre-game: refresh every 30 minutes
        - Off days: refresh once a day

        Returns:
            True if cache is still fresh, False if we need new data
        """
        if self._cache_timestamp is None:
            return False

        age = datetime.now() - self._cache_timestamp

        # Check if any games are live (need frequent updates)
        games = self._cache.get("games", [])
        has_live_games = any(g.get("is_live", False) for g in games)

        if has_live_games:
            return age < self._cache_ttl_live  # 5 minutes

        # Check if any games are upcoming today
        has_upcoming_today = any(
            g.get("is_upcoming", False) and
            g.get("game_time_local", datetime.now()).date() == datetime.now().date()
            for g in games
        )

        if has_upcoming_today:
            return age < self._cache_ttl_pregame  # 30 minutes

        # Off day - cache for 24 hours
        return age < self._cache_ttl_offday

    def should_auto_refresh(self) -> bool:
        """
        Determine if we should auto-refresh the dashboard.

        BEGINNER NOTE: We only auto-refresh during NFL game windows:
        - Thursday: 8-11pm ET (Thursday Night Football)
        - Sunday: 1-11pm ET (early + afternoon + night games)
        - Monday: 8-11pm ET (Monday Night Football)

        Returns:
            True if we should auto-refresh, False otherwise
        """
        now = datetime.now(self.user_timezone)

        # Convert to Eastern Time (NFL schedule is in ET)
        et_tz = pytz.timezone("America/New_York")
        now_et = now.astimezone(et_tz)

        weekday = now_et.weekday()  # 0=Monday, 6=Sunday
        hour = now_et.hour

        # Thursday Night Football (8pm-11pm ET)
        if weekday == 3 and 20 <= hour < 23:  # 3 = Thursday
            return True

        # Sunday games (1pm-11pm ET)
        if weekday == 6 and 13 <= hour < 23:  # 6 = Sunday
            return True

        # Monday Night Football (8pm-11pm ET)
        if weekday == 0 and 20 <= hour < 23:  # 0 = Monday
            return True

        return False

    def get_live_games(self) -> List[Dict]:
        """Get only games currently in progress."""
        games = self.get_current_games()
        return [g for g in games if g.get("is_live", False)]

    def get_upcoming_games(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get upcoming games within the next X days.

        Args:
            days_ahead: How many days to look ahead (default: 7)
        """
        games = self.get_current_games()
        cutoff = datetime.now(self.user_timezone) + timedelta(days=days_ahead)

        return [
            g for g in games
            if g.get("is_upcoming", False) and
            g.get("game_time_local", datetime.max) < cutoff
        ]

    def get_completed_games(self, days_back: int = 7) -> List[Dict]:
        """
        Get completed games from the last X days.

        Args:
            days_back: How many days to look back (default: 7)
        """
        games = self.get_current_games()
        cutoff = datetime.now(self.user_timezone) - timedelta(days=days_back)

        return [
            g for g in games
            if g.get("is_final", False) and
            g.get("game_time_local", datetime.min) > cutoff
        ]

    def format_game_time(self, game: Dict) -> str:
        """
        Format game time for display.

        BEGINNER NOTE: Makes times human-readable.
        Examples:
        - "Today 8:15 PM"
        - "Tomorrow 1:00 PM"
        - "Mon Nov 25, 8:20 PM"

        Args:
            game: Game dict

        Returns:
            Formatted time string
        """
        game_time = game.get("game_time_local")
        if not game_time:
            return "TBD"

        now = datetime.now(self.user_timezone)

        # Today
        if game_time.date() == now.date():
            return f"Today {game_time.strftime('%-I:%M %p')}"

        # Tomorrow
        if game_time.date() == (now + timedelta(days=1)).date():
            return f"Tomorrow {game_time.strftime('%-I:%M %p')}"

        # This week
        if game_time.date() < (now + timedelta(days=7)).date():
            return game_time.strftime("%a %-I:%M %p")

        # Future
        return game_time.strftime("%a %b %-d, %-I:%M %p")

    def get_game_display_status(self, game: Dict) -> str:
        """
        Get human-readable game status.

        Examples:
        - "LIVE - Q3 8:42"
        - "FINAL"
        - "8:15 PM ET"
        - "Halftime"

        Args:
            game: Game dict

        Returns:
            Display status string
        """
        status = game.get("status", "")

        if status == GameStatus.IN_PROGRESS.value:
            period = game.get("period", 1)
            clock = game.get("clock", "0:00")

            # Convert period to quarter
            if period <= 4:
                quarter = f"Q{period}"
            elif period == 5:
                quarter = "OT"
            else:
                quarter = f"OT{period - 4}"

            return f"🔴 LIVE - {quarter} {clock}"

        elif status == GameStatus.HALFTIME.value:
            return "⏸️ Halftime"

        elif status == GameStatus.FINAL.value:
            return "✅ FINAL"

        elif status in [GameStatus.SCHEDULED.value, GameStatus.PREGAME.value]:
            return self.format_game_time(game)

        else:
            return status.upper()
