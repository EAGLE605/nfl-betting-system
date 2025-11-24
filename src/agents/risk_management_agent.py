"""Risk Management Agent - Bankroll optimization, Kelly criterion, exposure limits."""

import asyncio
import logging
from typing import Any, Dict

from src.agents.base_agent import AgentCapability, BaseAgent
from src.betting.kelly import KellyCriterion

logger = logging.getLogger(__name__)


class RiskManagementAgent(BaseAgent):
    """Risk Management Agent - Level 2"""

    def __init__(self):
        super().__init__(
            agent_id="risk_mgmt_001",
            agent_name="Risk Management Agent",
            capabilities=[AgentCapability.REASONING, AgentCapability.TOOLS],
        )
        self.kelly = KellyCriterion()
        self.register_tool(
            "calculate_bet_size", self._calculate_bet_size, "Calculate optimal bet size"
        )
        self.register_tool(
            "check_exposure", self._check_exposure, "Check exposure limits"
        )

    async def run(self):
        while self.running:
            try:
                await self._monitor_risk()
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Risk Management error: {e}")
                await asyncio.sleep(10)

    async def _calculate_bet_size(
        self, bankroll: float, edge: float, prob: float
    ) -> Dict[str, Any]:
        bet_size = self.kelly.calculate_bet_size(bankroll, edge, prob)
        return {"bet_size": bet_size, "kelly_fraction": self.kelly.kelly_fraction}

    async def _check_exposure(self, current_bets: list) -> Dict[str, Any]:
        total_exposure = sum(b.get("amount", 0) for b in current_bets)
        return {
            "total_exposure": total_exposure,
            "within_limits": total_exposure < 1000,
        }

    async def _monitor_risk(self):
        logger.debug("Monitoring risk")
