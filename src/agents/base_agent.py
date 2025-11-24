"""
Base Agent Framework

Foundation for all agents in the autonomous system.
"""

import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status states."""

    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentCapability(Enum):
    """Agent capabilities."""

    REASONING = "reasoning"
    MEMORY = "memory"
    TOOLS = "tools"
    COMMUNICATION = "communication"
    LEARNING = "learning"


@dataclass
class AgentMessage:
    """Message between agents."""

    message_id: str = field(default_factory=lambda: str(uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: str = (
        "request"  # request, response, alert, command, proposal, vote, heartbeat
    )
    content: Dict[str, Any] = field(default_factory=dict)
    priority: int = 3  # 1=critical, 2=high, 3=normal, 4=low
    timestamp: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None  # For threading conversations
    requires_response: bool = False


class BaseAgent(ABC):
    """
    Base class for all agents.

    Provides:
    - Lifecycle management (init, run, shutdown)
    - Message passing
    - Tool registry
    - Memory/state management
    - Status tracking
    """

    def __init__(
        self, agent_id: str, agent_name: str, capabilities: List[AgentCapability]
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable name
            capabilities: List of agent capabilities
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.capabilities = capabilities

        self.status = AgentStatus.INITIALIZING
        self.created_at = datetime.now()
        self.last_heartbeat = datetime.now()

        # Message queue
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: List[AgentMessage] = []

        # Tools registry
        self.tools: Dict[str, Callable] = {}

        # Memory/state
        self.memory: Dict[str, Any] = {}

        # Control
        self.running = False
        self.lock = threading.Lock()

        logger.info(f"Initialized agent: {agent_name} ({agent_id})")

    def register_tool(self, name: str, tool: Callable, description: str = ""):
        """
        Register a tool for the agent.

        Args:
            name: Tool name
            tool: Tool function
            description: Tool description
        """
        self.tools[name] = tool
        self.memory[f"tool_{name}_description"] = description
        logger.debug(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self.tools.get(name)

    def send_message(self, message: AgentMessage):
        """
        Send message to another agent (via message bus).

        Args:
            message: Message to send
        """
        message.sender_id = self.agent_id
        # In real implementation, this would go through message bus
        logger.debug(
            f"Agent {self.agent_id} sending message {message.message_id} to {message.receiver_id}"
        )

    def receive_message(self, message: AgentMessage):
        """
        Receive a message.

        Args:
            message: Received message
        """
        self.message_queue.put_nowait(message)
        self.message_history.append(message)
        logger.debug(
            f"Agent {self.agent_id} received message {message.message_id} from {message.sender_id}"
        )

    async def process_messages(self):
        """Process messages from queue."""
        while self.running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def handle_message(self, message: AgentMessage):
        """
        Handle a received message (override in subclasses).

        Args:
            message: Message to handle
        """
        logger.debug(f"Agent {self.agent_id} handling message {message.message_id}")

        # Default: send heartbeat response
        if message.message_type == "heartbeat":
            response = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type="response",
                content={
                    "status": self.status.value,
                    "heartbeat": datetime.now().isoformat(),
                },
                parent_id=message.message_id,
            )
            self.send_message(response)

    def update_memory(self, key: str, value: Any):
        """Update agent memory."""
        with self.lock:
            self.memory[key] = value

    def get_memory(self, key: str, default: Any = None) -> Any:
        """Get value from memory."""
        with self.lock:
            return self.memory.get(key, default)

    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        with self.lock:
            self.last_heartbeat = datetime.now()

    @abstractmethod
    async def run(self):
        """
        Main agent loop (override in subclasses).

        This is where the agent's primary logic runs.
        """
        pass

    async def start(self):
        """Start the agent."""
        if self.running:
            return

        self.status = AgentStatus.READY
        self.running = True

        logger.info(f"Starting agent: {self.agent_name}")

        # Start message processing
        asyncio.create_task(self.process_messages())

        # Start main loop
        self.status = AgentStatus.RUNNING
        await self.run()

    async def stop(self):
        """Stop the agent."""
        if not self.running:
            return

        logger.info(f"Stopping agent: {self.agent_name}")
        self.running = False
        self.status = AgentStatus.SHUTDOWN

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        with self.lock:
            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "status": self.status.value,
                "capabilities": [c.value for c in self.capabilities],
                "created_at": self.created_at.isoformat(),
                "last_heartbeat": self.last_heartbeat.isoformat(),
                "tools_count": len(self.tools),
                "memory_keys": list(self.memory.keys()),
                "messages_received": len(self.message_history),
            }


class AgentRegistry:
    """Registry for all agents."""

    def __init__(self):
        """Initialize agent registry."""
        self.agents: Dict[str, BaseAgent] = {}
        self.lock = threading.Lock()

    def register(self, agent: BaseAgent):
        """Register an agent."""
        with self.lock:
            self.agents[agent.agent_id] = agent
            logger.info(f"Registered agent: {agent.agent_name} ({agent.agent_id})")

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        with self.lock:
            return self.agents.get(agent_id)

    def get_all(self) -> List[BaseAgent]:
        """Get all registered agents."""
        with self.lock:
            return list(self.agents.values())

    def get_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        with self.lock:
            for agent in self.agents.values():
                if agent.agent_name == name:
                    return agent
            return None


# Global registry
agent_registry = AgentRegistry()
