"""
ESPN API Client - Free, No Authentication

ESPN has an unofficial but widely-used public API that doesn't require authentication.
"""

import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ESPNClient:
    """
    ESPN NFL API Client (Free, No Auth)

    Rate Limits: ~100 requests/day (undocumented, be respectful)
    """

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    def __init__(self, cache=None):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "NFLBettingSystem/1.0", "Accept": "application/json"}
        )

    def get_scoreboard(self, dates: Optional[str] = None) -> Dict:
        """
        Get current week scoreboard.

        Args:
            dates: Optional date filter (format: YYYYMMDD)

        Returns:
            Scoreboard data with all games
        """
        url = f"{self.BASE_URL}/scoreboard"
        params = {}
        if dates:
            params["dates"] = dates

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ESPN API error: {e}")
            return {}

    def get_game_summary(self, game_id: str) -> Dict:
        """
        Get detailed game summary.

        Args:
            game_id: ESPN game ID (e.g., "401547502")

        Returns:
            Detailed game data including stats, plays, etc.
        """
        url = f"{self.BASE_URL}/summary"
        params = {"event": game_id}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ESPN game summary error: {e}")
            return {}

    def get_teams(self) -> List[Dict]:
        """
        Get all NFL teams.

        Returns:
            List of team data
        """
        url = f"{self.BASE_URL}/teams"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract teams from nested structure
            teams = []
            if "sports" in data:
                for sport in data["sports"]:
                    if "leagues" in sport:
                        for league in sport["leagues"]:
                            if "teams" in league:
                                teams.extend([t["team"] for t in league["teams"]])

            return teams
        except Exception as e:
            logger.error(f"ESPN teams error: {e}")
            return []

    def get_team_roster(self, team_abbr: str) -> List[Dict]:
        """
        Get team roster.

        Args:
            team_abbr: Team abbreviation (e.g., "KC" for Chiefs)

        Returns:
            List of players
        """
        url = f"{self.BASE_URL}/teams/{team_abbr}/roster"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ESPN roster error: {e}")
            return []

    def get_team_schedule(self, team_abbr: str, season: Optional[int] = None) -> Dict:
        """
        Get team schedule.

        Args:
            team_abbr: Team abbreviation (e.g., "KC")
            season: Optional season year

        Returns:
            Schedule data
        """
        url = f"{self.BASE_URL}/teams/{team_abbr}/schedule"
        params = {}
        if season:
            params["season"] = season

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ESPN schedule error: {e}")
            return {}

    def get_standings(self) -> Dict:
        """Get NFL standings."""
        url = f"{self.BASE_URL}/standings"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ESPN standings error: {e}")
            return {}

    def get_news(self) -> List[Dict]:
        """Get NFL news."""
        url = f"{self.BASE_URL}/news"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            logger.error(f"ESPN news error: {e}")
            return []
