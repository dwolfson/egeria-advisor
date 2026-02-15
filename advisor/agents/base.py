"""
Base agent class for Egeria Advisor agents.

This module defines the abstract base class that all specialized agents
must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger

from advisor.rag_system import get_rag_system
from advisor.config import get_full_config


class BaseAgent(ABC):
    """Abstract base class for all advisor agents."""

    def __init__(self, name: str):
        """
        Initialize the agent.

        Args:
            name: Name of the agent
        """
        self.name = name
        self.rag_system = get_rag_system()

        # Load config
        full_config = get_full_config()
        agents_config = full_config.get("agents")

        # Access specific agent config by name (e.g., query -> query_agent)
        # Handle both dict and Pydantic model for robustness
        agent_attr = f"{name}_agent"
        if hasattr(agents_config, agent_attr):
             self.agent_config = getattr(agents_config, agent_attr)
        elif isinstance(agents_config, dict):
             self.agent_config = agents_config.get(agent_attr, {})
        else:
             self.agent_config = {}

        # Convert to dict if it's a Pydantic model
        if hasattr(self.agent_config, "model_dump"):
            self.agent_config = self.agent_config.model_dump()
        elif hasattr(self.agent_config, "dict"):
            self.agent_config = self.agent_config.dict()

        logger.info(f"Initialized agent: {name}")

    @abstractmethod
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query.

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            Dictionary with response and metadata
        """
        pass

    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.agent_config

    def _format_response(
        self,
        response: str,
        sources: List[Dict[str, Any]] = None,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """
        Format the standard response structure.

        Args:
            response: Text response
            sources: List of sources used
            confidence: Confidence score (0.0 - 1.0)

        Returns:
            Formatted response dictionary
        """
        return {
            "agent": self.name,
            "response": response,
            "sources": sources or [],
            "confidence": confidence
        }
