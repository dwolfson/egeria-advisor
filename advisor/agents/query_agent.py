"""
Query Agent using BeeAI Framework.
"""

from typing import Dict, Any, Optional
from loguru import logger

from beeai_framework.agents.react.agent import ReActAgent
from beeai_framework.memory import UnconstrainedMemory
from advisor.agents.backend import BeeAIBackend
from advisor.tools.rag_tool import RAGTool


class QueryAgent:
    """
    Agent specialized in answering general queries using BeeAI ReAct.
    """

    def __init__(self):
        """Initialize Query Agent."""
        self.name = "query"
        self.model = BeeAIBackend.get_chat_model("llama3.1:8b")
        self.memory = UnconstrainedMemory()
        self.tools = [RAGTool()]

        self.agent = ReActAgent(
            llm=self.model,
            tools=self.tools,
            memory=self.memory
        )

    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query using the BeeAI agent.

        Args:
            query: User's question

        Returns:
            Response dictionary
        """
        logger.info(f"QueryAgent (BeeAI) processing: {query}")

        try:
            response = await self.agent.run(prompt=query)
            return {
                "agent": self.name,
                "response": response.output.text,
                "confidence": 1.0 # Placeholder
            }
        except Exception as e:
            logger.error(f"QueryAgent failed: {e}")
            return {
                "agent": self.name,
                "response": "I encountered an error processing your request.",
                "error": str(e)
            }
