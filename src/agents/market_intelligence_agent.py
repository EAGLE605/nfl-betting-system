"""Market Intelligence Agent - Real-time odds, line movement, public sentiment."""

import asyncio
import logging
from typing import Any, Dict

from src.agents.base_agent import AgentCapability, BaseAgent

# TheOddsAPI will be imported at runtime or passed as dependency

logger = logging.getLogger(__name__)


class MarketIntelligenceAgent(BaseAgent):
    """Market Intelligence Agent - Level 2"""

    def __init__(self, odds_api=None):
        super().__init__(
            agent_id="market_intel_001",
            agent_name="Market Intelligence Agent",
            capabilities=[AgentCapability.REASONING, AgentCapability.TOOLS],
        )
        # Odds API will be injected or created lazily
        self._odds_api = odds_api
        self.register_tool("get_odds", self._get_odds, "Get current NFL odds")
        self.register_tool(
            "track_line_movement", self._track_line_movement, "Track line movement"
        )

    async def run(self):
        while self.running:
            try:
                odds = await self._get_odds()
                await self._analyze_market(odds)
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Market Intelligence error: {e}")
                await asyncio.sleep(10)

    async def _get_odds(self) -> Dict[str, Any]:
        if self._odds_api:
            return self._odds_api.get_nfl_odds()
        return {}

    async def _track_line_movement(self, game_id: str) -> Dict[str, Any]:
        if not self._odds_api:
            return {}
        cache = self._odds_api.cache
        if cache:
            return cache.get_line_movement(game_id)
        return {}

    async def _analyze_market(self, odds: Dict[str, Any]):
        logger.debug("Analyzing market conditions")
