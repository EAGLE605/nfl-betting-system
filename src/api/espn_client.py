"""
ESPN API Client - Free, No Authentication

ESPN has an unofficial but widely-used public API that doesn't require authentication.

RESILIENCE PATTERNS:
- Circuit Breaker: Trips after 5 consecutive failures, resets after 60s
- Exponential Backoff: Retries with 1s, 2s, 4s... delays
- Fallback: Returns cached/empty data when API fails
"""

import logging
import time
from typing import Dict, List, Optional

import requests

# Import resilience utilities
try:
    from src.utils.resilience import (
        espn_breaker,
        espn_limiter,
        with_resilience,
        metrics as resilience_metrics,
    )

    RESILIENCE_AVAILABLE = True
except ImportError:
    RESILIENCE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ESPNClient:
    """
    ESPN NFL API Client (Free, No Auth)

    Rate Limits: ~100 requests/day (undocumented, be respectful)

    Resilience Features:
    - Circuit breaker: Fails fast after 5 consecutive errors
    - Exponential backoff: Retries with increasing delays
    - Rate limiting: Respects API limits
    - Fallback: Returns cached data when API unavailable
    """

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # seconds

    def __init__(self, cache=None):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "NFLBettingSystem/1.0", "Accept": "application/json"}
        )
        self._last_request_time = 0
        self._min_request_interval = 0.5  # 500ms between requests

    def _make_request(
        self, url: str, params: Optional[Dict] = None, cache_key: Optional[str] = None
    ) -> Dict:
        """
        Make an HTTP request with resilience patterns.

        Features:
        - Rate limiting (500ms between requests)
        - Circuit breaker (fails fast if API is down)
        - Exponential backoff retries
        - Fallback to cache

        Args:
            url: API endpoint URL
            params: Query parameters
            cache_key: Optional cache key for fallback

        Returns:
            JSON response or empty dict on failure
        """
        # Rate limiting - wait if too fast
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)

        # Check circuit breaker state
        if RESILIENCE_AVAILABLE:
            try:
                from pybreaker import STATE_OPEN

                if espn_breaker.current_state == STATE_OPEN:
                    logger.warning("ESPN circuit breaker OPEN - using fallback")
                    return self._get_fallback(cache_key)
            except Exception:
                pass

        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                self._last_request_time = time.time()

                # Make the actual request
                if RESILIENCE_AVAILABLE:
                    # Use circuit breaker
                    response = espn_breaker.call(
                        self.session.get, url, params=params, timeout=10
                    )
                else:
                    response = self.session.get(url, params=params, timeout=10)

                response.raise_for_status()

                # Success - cache the result
                result = response.json()
                if cache_key and self.cache:
                    self.cache[cache_key] = result

                return result

            except requests.exceptions.Timeout as e:
                last_error = e
                wait_time = self.RETRY_BACKOFF_BASE**attempt
                logger.warning(
                    f"ESPN timeout (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {wait_time}s"
                )
                time.sleep(wait_time)

            except requests.exceptions.ConnectionError as e:
                last_error = e
                wait_time = self.RETRY_BACKOFF_BASE**attempt
                logger.warning(
                    f"ESPN connection error (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {wait_time}s"
                )
                time.sleep(wait_time)

            except requests.exceptions.HTTPError as e:
                last_error = e
                if e.response and e.response.status_code >= 500:
                    # Server error - retry
                    wait_time = self.RETRY_BACKOFF_BASE**attempt
                    logger.warning(
                        f"ESPN server error {e.response.status_code} (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(wait_time)
                else:
                    # Client error - don't retry
                    logger.error(f"ESPN client error: {e}")
                    break

            except Exception as e:
                last_error = e
                logger.error(f"ESPN unexpected error: {e}")
                break

        # All retries exhausted - use fallback
        logger.error(f"ESPN API failed after {self.MAX_RETRIES} attempts: {last_error}")
        return self._get_fallback(cache_key)

    def _get_fallback(self, cache_key: Optional[str]) -> Dict:
        """
        Get fallback data from cache.

        Args:
            cache_key: Cache key to look up

        Returns:
            Cached data or empty dict
        """
        if cache_key and self.cache and cache_key in self.cache:
            logger.info(f"Using cached fallback for {cache_key}")
            return self.cache[cache_key]
        return {}

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

        cache_key = f"scoreboard_{dates or 'current'}"
        return self._make_request(url, params, cache_key)

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
        cache_key = f"game_summary_{game_id}"
        return self._make_request(url, params, cache_key)

    def get_teams(self) -> List[Dict]:
        """
        Get all NFL teams.

        Returns:
            List of team data
        """
        url = f"{self.BASE_URL}/teams"
        data = self._make_request(url, cache_key="teams")

        # Extract teams from nested structure
        teams = []
        if "sports" in data:
            for sport in data["sports"]:
                if "leagues" in sport:
                    for league in sport["leagues"]:
                        if "teams" in league:
                            teams.extend([t["team"] for t in league["teams"]])

        return teams

    def get_team_roster(self, team_abbr: str) -> List[Dict]:
        """
        Get team roster.

        Args:
            team_abbr: Team abbreviation (e.g., "KC" for Chiefs)

        Returns:
            List of players
        """
        url = f"{self.BASE_URL}/teams/{team_abbr}/roster"
        cache_key = f"roster_{team_abbr}"
        result = self._make_request(url, cache_key=cache_key)
        return result if isinstance(result, list) else []

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

        cache_key = f"schedule_{team_abbr}_{season or 'current'}"
        return self._make_request(url, params, cache_key)

    def get_standings(self) -> Dict:
        """Get NFL standings."""
        url = f"{self.BASE_URL}/standings"
        return self._make_request(url, cache_key="standings")

    def get_news(self) -> List[Dict]:
        """Get NFL news."""
        url = f"{self.BASE_URL}/news"
        data = self._make_request(url, cache_key="news")
        return data.get("articles", [])

    def get_circuit_status(self) -> Dict:
        """
        Get the current circuit breaker status.

        Returns:
            Dict with circuit state and failure count
        """
        if RESILIENCE_AVAILABLE:
            return {
                "state": espn_breaker.current_state.name,
                "fail_count": espn_breaker.fail_counter,
                "is_open": espn_breaker.current_state.name == "open",
            }
        return {"state": "unknown", "fail_count": 0, "is_open": False}
