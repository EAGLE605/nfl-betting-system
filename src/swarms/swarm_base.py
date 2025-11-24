"""Swarm Base Framework - Agent coordination within swarms."""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from src.agents.base_agent import AgentMessage, BaseAgent

logger = logging.getLogger(__name__)


class ConsensusRule(Enum):
    """Consensus decision rules."""

    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    QUORUM = "quorum"
    WEIGHTED = "weighted"


@dataclass
class SwarmDecision:
    """A decision made by a swarm."""

    decision_id: str
    swarm_id: str
    decision: Any
    confidence: float
    votes: Dict[str, Any]
    timestamp: datetime
    rule_used: ConsensusRule


class SwarmBase:
    """
    Base class for swarms.

    A swarm is a group of agents working together to make decisions.
    """

    def __init__(
        self,
        swarm_id: str,
        swarm_name: str,
        agents: List[BaseAgent],
        consensus_rule: ConsensusRule,
    ):
        """
        Initialize swarm.

        Args:
            swarm_id: Unique swarm identifier
            swarm_name: Human-readable name
            agents: List of agents in the swarm
            consensus_rule: Decision rule for consensus
        """
        self.swarm_id = swarm_id
        self.swarm_name = swarm_name
        self.agents = agents
        self.consensus_rule = consensus_rule

        self.decisions: List[SwarmDecision] = []
        self.votes: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"Initialized swarm: {swarm_name} ({swarm_id}) with {len(agents)} agents"
        )

    async def make_decision(
        self, task: Dict[str, Any], timeout: int = 300
    ) -> SwarmDecision:
        """
        Make a decision through swarm consensus.

        Args:
            task: Task description
            timeout: Timeout in seconds

        Returns:
            SwarmDecision
        """
        logger.info(
            f"Swarm {self.swarm_name} making decision on: {task.get('type', 'unknown')}"
        )

        # Phase 1: Individual analysis
        votes = await self._collect_votes(task, timeout)

        # Phase 2: Consensus
        decision = await self._reach_consensus(votes, task)

        # Store decision
        self.decisions.append(decision)

        return decision

    async def _collect_votes(
        self, task: Dict[str, Any], timeout: int
    ) -> Dict[str, Any]:
        """Collect votes from all agents."""
        votes = {}

        # Send task to all agents
        for agent in self.agents:
            message = AgentMessage(
                sender_id=self.swarm_id,
                receiver_id=agent.agent_id,
                message_type="request",
                content={"task": task, "request_vote": True},
            )
            # In real implementation, would send via message bus

        # Collect responses (simplified)
        for agent in self.agents:
            votes[agent.agent_id] = {
                "vote": "approve",  # Simplified
                "confidence": 0.8,
                "reasoning": "Default reasoning",
            }

        return votes

    async def _reach_consensus(
        self, votes: Dict[str, Any], task: Dict[str, Any]
    ) -> SwarmDecision:
        """Reach consensus based on votes."""
        if self.consensus_rule == ConsensusRule.MAJORITY:
            approve_count = sum(1 for v in votes.values() if v.get("vote") == "approve")
            decision = approve_count > len(votes) / 2

        elif self.consensus_rule == ConsensusRule.UNANIMOUS:
            decision = all(v.get("vote") == "approve" for v in votes.values())

        elif self.consensus_rule == ConsensusRule.QUORUM:
            approve_count = sum(1 for v in votes.values() if v.get("vote") == "approve")
            decision = approve_count >= len(votes) * 0.6  # 60% quorum

        else:  # WEIGHTED
            total_confidence = sum(v.get("confidence", 0) for v in votes.values())
            decision = total_confidence / len(votes) > 0.7

        avg_confidence = (
            sum(v.get("confidence", 0) for v in votes.values()) / len(votes)
            if votes
            else 0
        )

        return SwarmDecision(
            decision_id=f"decision_{int(datetime.now().timestamp())}",
            swarm_id=self.swarm_id,
            decision=decision,
            confidence=avg_confidence,
            votes=votes,
            timestamp=datetime.now(),
            rule_used=self.consensus_rule,
        )
