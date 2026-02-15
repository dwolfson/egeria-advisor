"""
Code Example Agent using BeeAI Framework.
"""

from typing import Dict, Any, Optional
from loguru import logger

from beeai_framework.agents.react.agent import ReActAgent
from beeai_framework.memory import UnconstrainedMemory
from advisor.agents.backend import BeeAIBackend
from advisor.tools.rag_tool import RAGTool


class CodeExampleAgent:
    """
    Agent specialized in code examples using BeeAI ReAct.
    """

    def __init__(self):
        """Initialize Code Example Agent."""
        self.name = "code"
        # Use code-specialized model if configured
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
        Process a code query.

        Args:
            query: User's request

        Returns:
            Response dictionary
        """
        logger.info(f"CodeExampleAgent (BeeAI) processing: {query}")

        # prompt engineering for code
        enhanced_prompt = (
            f"You are an expert Egeria developer. Provide a complete, runnable code example "
            f"for the following request. Use the available tools to search for existing examples "
            f"or documentation. \n\nRequest: {query}"
        )

        try:
            response = await self.agent.run(prompt=enhanced_prompt)
            return {
                "agent": self.name,
                "response": response.output.text,
                "confidence": 1.0
            }
        except Exception as e:
            logger.error(f"CodeExampleAgent failed: {e}")
            return {
                "agent": self.name,
                "response": "Error generating code example.",
                "error": str(e)
            }
