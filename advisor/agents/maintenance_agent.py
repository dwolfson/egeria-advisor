"""
Maintenance Agent using BeeAI Framework.
"""

from typing import Dict, Any, Optional
from loguru import logger

from beeai_framework.agents.react.agent import ReActAgent
from beeai_framework.memory import UnconstrainedMemory
from advisor.agents.backend import BeeAIBackend
from advisor.tools.rag_tool import RAGTool


class MaintenanceAgent:
    """
    Agent specialized in maintenance and debugging using BeeAI ReAct.
    """

    def __init__(self):
        """Initialize Maintenance Agent."""
        self.name = "maintenance"
        self.model = BeeAIBackend.get_chat_model("codellama:13b")
        self.memory = UnconstrainedMemory()
        self.tools = [RAGTool()]

        self.agent = ReActAgent(
            llm=self.model,
            tools=self.tools,
            memory=self.memory
        )

    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a maintenance query.

        Args:
            query: User's request

        Returns:
            Response dictionary
        """
        logger.info(f"MaintenanceAgent (BeeAI) processing: {query}")

        error_context = context.get("error") if context else None
        prompt = query
        if error_context:
            prompt += f"\n\nError Context:\n{error_context}"

        prompt += "\n\nAnalyze this issue and suggest a fix based on Egeria best practices."

        try:
            response = await self.agent.run(prompt=prompt)
            return {
                "agent": self.name,
                "response": response.output.text,
                "confidence": 1.0
            }
        except Exception as e:
            logger.error(f"MaintenanceAgent failed: {e}")
            return {
                "agent": self.name,
                "response": "Error processing maintenance request.",
                "error": str(e)
            }
