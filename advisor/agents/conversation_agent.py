"""
Conversation Agent (Orchestrator) using BeeAI Framework.
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from advisor.agents.base import BaseAgent
from advisor.agents.query_agent import QueryAgent
from advisor.agents.code_example_agent import CodeExampleAgent
from advisor.agents.maintenance_agent import MaintenanceAgent
from advisor.query_processor import get_query_processor, QueryType


class ConversationAgent:
    """
    Orchestrator agent that routes queries to specialized BeeAI agents.
    """

    def __init__(self):
        """Initialize Conversation Agent."""
        self.name = "conversation"
        self.query_processor = get_query_processor()

        # Initialize specialized BeeAI agents
        self.agents = {
            "query": QueryAgent(),
            "code": CodeExampleAgent(),
            "maintenance": MaintenanceAgent()
        }

        self.history: List[Dict[str, str]] = []

    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query by routing to the appropriate BeeAI agent.

        Args:
            query: User's input
            context: Session context

        Returns:
            Response from the selected agent
        """
        logger.info(f"ConversationAgent processing: {query}")

        self.history.append({"role": "user", "content": query})

        # Analyze query intent
        analysis = self.query_processor.process(query)
        query_type_str = analysis.get("query_type", "general")

        # Route logic
        if query_type_str in [QueryType.CODE_SEARCH.value, QueryType.EXAMPLE.value]:
            target_agent = self.agents["code"]
        elif query_type_str in [QueryType.DEBUGGING.value, QueryType.BEST_PRACTICE.value]:
            target_agent = self.agents["maintenance"]
        else:
            target_agent = self.agents["query"]

        logger.info(f"Routing query type '{query_type_str}' to agent: {target_agent.name}")

        # Execute BeeAI agent
        # Note: BeeAI agents are async, so we await
        try:
            result = await target_agent.process(query, context)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            result = {
                "agent": target_agent.name,
                "response": "An error occurred while processing your request.",
                "error": str(e)
            }

        # Update history
        response_text = result.get("response", "")
        self.history.append({"role": "assistant", "content": response_text})

        result["routed_to"] = target_agent.name
        result["query_type"] = query_type_str

        return result

    def clear_history(self):
        """Clear conversation history."""
        self.history = []
