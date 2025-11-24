"""
Message Bus for Agent Communication

Handles routing and delivery of messages between agents.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from src.agents.base_agent import AgentMessage, BaseAgent

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Central message bus for agent communication.

    Features:
    - Message routing
    - Broadcast messaging
    - Message persistence
    - Timeout handling
    """

    def __init__(self):
        """Initialize message bus."""
        self.subscribers: Dict[str, List[BaseAgent]] = defaultdict(list)
        self.message_history: List[AgentMessage] = []
        self.pending_responses: Dict[str, List[Callable]] = {}
        self.running = False
        self.lock = asyncio.Lock()

        logger.info("Message bus initialized")

    def subscribe(self, agent: BaseAgent, message_types: Optional[List[str]] = None):
        """
        Subscribe agent to messages.

        Args:
            agent: Agent to subscribe
            message_types: Types to subscribe to (None = all)
        """
        if message_types is None:
            message_types = ["*"]

        for msg_type in message_types:
            self.subscribers[msg_type].append(agent)

        logger.debug(f"Agent {agent.agent_id} subscribed to {message_types}")

    def unsubscribe(self, agent: BaseAgent):
        """Unsubscribe agent from all messages."""
        for subscribers in self.subscribers.values():
            if agent in subscribers:
                subscribers.remove(agent)

        logger.debug(f"Agent {agent.agent_id} unsubscribed")

    async def send(self, message: AgentMessage):
        """
        Send a message.

        Args:
            message: Message to send
        """
        async with self.lock:
            self.message_history.append(message)

            # Route to specific receiver
            if message.receiver_id:
                receiver = self._find_agent(message.receiver_id)
                if receiver:
                    receiver.receive_message(message)
                else:
                    logger.warning(f"Receiver {message.receiver_id} not found")

            # Broadcast to subscribers
            if message.message_type in self.subscribers:
                for subscriber in self.subscribers[message.message_type]:
                    if subscriber.agent_id != message.sender_id:
                        subscriber.receive_message(message)

            # Broadcast to all subscribers
            if "*" in self.subscribers:
                for subscriber in self.subscribers["*"]:
                    if subscriber.agent_id != message.sender_id:
                        subscriber.receive_message(message)

            logger.debug(f"Message {message.message_id} routed")

    async def broadcast(self, message: AgentMessage):
        """
        Broadcast message to all agents.

        Args:
            message: Message to broadcast
        """
        message.receiver_id = "*"  # Broadcast marker
        await self.send(message)

    def _find_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Find agent by ID."""
        from src.agents.base_agent import agent_registry

        return agent_registry.get(agent_id)

    def get_message_history(self, agent_id: Optional[str] = None) -> List[AgentMessage]:
        """Get message history, optionally filtered by agent."""
        if agent_id:
            return [
                m
                for m in self.message_history
                if m.sender_id == agent_id or m.receiver_id == agent_id
            ]
        return self.message_history


# Global message bus instance
message_bus = MessageBus()
