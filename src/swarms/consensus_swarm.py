"""Consensus Swarm - Daily picks through agent consensus."""

import logging
from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent
from src.swarms.swarm_base import ConsensusRule, SwarmBase

logger = logging.getLogger(__name__)


class ConsensusSwarm(SwarmBase):
    """
    Consensus Swarm (Daily Picks)

    Size: 7-12 agents (odd number, mixed providers)
    Decision rule: Majority vote with confidence scaling
    """

    def __init__(self, agents: List[BaseAgent]):
        """Initialize consensus swarm."""
        super().__init__(
            swarm_id="consensus_swarm_001",
            swarm_name="Consensus Swarm",
            agents=agents,
            consensus_rule=ConsensusRule.WEIGHTED,
        )
        logger.info("Consensus Swarm initialized")

    async def generate_daily_picks(self, games: List[Dict]) -> List[Dict]:
        """
        Generate daily picks through swarm consensus.

        Args:
            games: List of games to analyze

        Returns:
            List of picks with confidence tiers
        """
        picks = []

        for game in games:
            # Phase 1: Individual analysis (each agent evaluates game)
            individual_picks = await self._individual_analysis(game)

            # Phase 2: Deliberation (share picks, debate disagreements)
            deliberated = await self._deliberation_phase(individual_picks)

            # Phase 3: Voting (weighted by recent_performance × confidence)
            vote_result = await self._voting_phase(deliberated)

            # Phase 4: Quality check (Risk Management Agent review)
            if vote_result.get("consensus_pct", 0) >= 0.60:
                pick = {
                    "game": game,
                    "pick": vote_result.get("pick"),
                    "confidence": vote_result.get("confidence", 0),
                    "consensus_pct": vote_result.get("consensus_pct", 0),
                    "tier": self._assign_tier(vote_result),
                }
                picks.append(pick)

        return picks

    async def _individual_analysis(self, game: Dict) -> List[Dict]:
        """Each agent analyzes the game."""
        picks = []
        for agent in self.agents:
            pick = {
                "agent": agent.agent_id,
                "pick": "home",  # Simplified
                "confidence": 0.7,
            }
            picks.append(pick)
        return picks

    async def _deliberation_phase(self, picks: List[Dict]) -> List[Dict]:
        """Agents deliberate and refine picks."""
        return picks

    async def _voting_phase(self, picks: List[Dict]) -> Dict[str, Any]:
        """Weighted voting."""
        # Count votes by pick
        vote_counts = {}
        total_confidence = {}

        for pick in picks:
            pick_value = pick.get("pick")
            confidence = pick.get("confidence", 0)

            if pick_value not in vote_counts:
                vote_counts[pick_value] = 0
                total_confidence[pick_value] = 0

            vote_counts[pick_value] += 1
            total_confidence[pick_value] += confidence

        # Find winner
        winner = max(vote_counts.items(), key=lambda x: x[1])
        consensus_pct = winner[1] / len(picks)
        avg_confidence = total_confidence[winner[0]] / winner[1]

        return {
            "pick": winner[0],
            "confidence": avg_confidence,
            "consensus_pct": consensus_pct,
            "votes": vote_counts,
        }

    def _assign_tier(self, vote_result: Dict[str, Any]) -> str:
        """Assign confidence tier."""
        consensus = vote_result.get("consensus_pct", 0)
        confidence = vote_result.get("confidence", 0)

        if consensus >= 0.90 and confidence > 0.10:
            return "S_tier"  # ≥90% consensus, 5% bankroll, >10% ROI
        elif consensus >= 0.75:
            return "A_tier"  # 75-89% consensus, 3% bankroll, 5-10% ROI
        elif consensus >= 0.60:
            return "B_tier"  # 60-74% consensus, 1.5% bankroll, 3-5% ROI
        else:
            return "no_bet"  # <60% consensus, skip
