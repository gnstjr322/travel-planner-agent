"""
Base class for all agents in the travel planner system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain.schema import BaseMessage
from pydantic import BaseModel


class BaseAgent(ABC):
    """Base class for all travel planner agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.conversation_history: List[BaseMessage] = []

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result."""
        pass

    @abstractmethod
    def get_tools(self) -> List[Any]:
        """Return list of tools this agent can use."""
        pass

    def add_to_history(self, message: BaseMessage):
        """Add message to conversation history."""
        self.conversation_history.append(message)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()


class AgentResponse(BaseModel):
    """Standard response format for all agents."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    error: Optional[str] = None
    agent_name: str = ""
