"""
BeeAI-based Egeria Advisor Agent.

This agent uses BeeAI Framework components to provide intelligent assistance
for Egeria development, leveraging our optimized RAG retrieval system.
"""

from typing import List, Optional, Dict, Any
from beeai_framework.memory import TokenMemory
from beeai_framework.cache import SlidingCache
from beeai_framework.adapters.ollama import OllamaChatModel
from beeai_framework.backend import (
    UserMessage,
    SystemMessage,
    AssistantMessage,
    ChatModelParameters
)
from beeai_framework.tools import Tool

from advisor.tools.beeai_tools import get_egeria_tools
from advisor.config import get_full_config


class EgeriaAgent:
    """
    Intelligent agent for Egeria development assistance.
    
    Uses BeeAI Framework components without inheriting from BaseAgent
    to avoid abstract method complexity.
    
    Features:
    - Token-aware memory management (8K context)
    - Query result caching
    - Multi-collection RAG search
    - Code analysis capabilities
    - Documentation lookup
    """
    
    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
        max_tokens: int = 8000,
        cache_size: int = 100,
        temperature: float = 0.7,
        tools: Optional[List[Tool]] = None
    ):
        """
        Initialize the Egeria agent.
        
        Parameters
        ----------
        model : str, optional
            Ollama model name (default: llama3.1:8b)
        base_url : str, optional
            Ollama server URL (default: http://localhost:11434)
        max_tokens : int, optional
            Maximum context tokens (default: 8000)
        cache_size : int, optional
            Cache size for repeated queries (default: 100)
        temperature : float, optional
            LLM temperature (default: 0.7)
        tools : list[Tool], optional
            Custom tools (default: Egeria RAG tools)
        """
        # Initialize memory with token limit
        self.memory = TokenMemory(max_tokens=max_tokens)
        
        # Initialize cache for repeated queries
        self.cache = SlidingCache(size=cache_size)
        
        # Initialize Ollama chat model
        self.llm = OllamaChatModel(
            model=model,
            base_url=base_url
        )
        self.temperature = temperature
        
        # Get tools (use provided or default Egeria tools)
        self.tools = tools if tools is not None else get_egeria_tools()
        
        # System prompt for Egeria expertise
        self.system_prompt = """You are an expert Egeria developer assistant with deep knowledge of:
- Egeria Python library (pyegeria)
- Egeria Java implementation
- Egeria architecture and concepts
- Metadata management and governance
- Open metadata standards

Your role is to help developers:
1. Find relevant code examples and documentation
2. Understand Egeria concepts and APIs
3. Troubleshoot issues
4. Follow best practices

When answering questions:
- Use the search tools to find accurate, up-to-date information
- Provide code examples when relevant
- Cite sources from the search results
- Be concise but thorough
- If you're unsure, say so and suggest where to look

Available tools:
- search_egeria_code: Search across all Egeria code and documentation
- analyze_egeria_code: Analyze specific code elements (classes, functions, etc.)
- lookup_egeria_docs: Find official documentation and guides
"""
        
        # Initialize conversation with system message
        self._messages = [SystemMessage(content=self.system_prompt)]
    
    async def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query and generate a response.
        
        Parameters
        ----------
        query : str
            User's question or request
        context : dict, optional
            Additional context for the query
            
        Returns
        -------
        dict
            Response with content and metadata
        """
        # Check cache first
        cache_key = f"query:{query}"
        cached_response = self.cache.get(cache_key)
        if cached_response:
            return {
                "content": cached_response,
                "metadata": {"cache_hit": True, "tools_used": []}
            }
        
        # Add user message
        self._messages.append(UserMessage(content=query))
        
        # Generate response with tool usage
        response = await self._generate_with_tools(query, context)
        
        # Add assistant message to history
        self._messages.append(AssistantMessage(content=response["content"]))
        
        # Cache the response
        self.cache.set(cache_key, response["content"])
        
        return response
    
    async def _generate_with_tools(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate response using available tools.
        
        This implements a simple ReAct-style loop:
        1. Decide which tool to use (if any)
        2. Execute the tool
        3. Generate final response
        """
        # Determine if we need to use tools
        tool_decision = self._decide_tool_usage(query)
        
        tool_results = []
        if tool_decision["use_tools"]:
            # Execute relevant tools
            for tool_name in tool_decision["tools"]:
                tool = self._get_tool_by_name(tool_name)
                if tool:
                    result = self._execute_tool(tool, query, context)
                    tool_results.append({
                        "tool": tool_name,
                        "result": result
                    })
        
        # Generate final response incorporating tool results
        final_response = await self._generate_final_response(
            query=query,
            tool_results=tool_results,
            context=context
        )
        
        return {
            "content": final_response,
            "metadata": {
                "tools_used": [r["tool"] for r in tool_results],
                "cache_hit": False
            }
        }
    
    def _decide_tool_usage(self, query: str) -> Dict[str, Any]:
        """
        Decide which tools (if any) to use for the query.
        
        Simple heuristic-based approach:
        - Code/implementation questions -> search_egeria_code
        - Class/function analysis -> analyze_egeria_code
        - Documentation/concepts -> lookup_egeria_docs
        """
        query_lower = query.lower()
        
        tools_to_use = []
        
        # Check for code search keywords
        code_keywords = ["how to", "example", "implement", "use", "code", "function", "class", "method"]
        if any(kw in query_lower for kw in code_keywords):
            tools_to_use.append("search_egeria_code")
        
        # Check for analysis keywords
        analysis_keywords = ["analyze", "find all", "list", "classes", "functions", "methods"]
        if any(kw in query_lower for kw in analysis_keywords):
            tools_to_use.append("analyze_egeria_code")
        
        # Check for documentation keywords
        doc_keywords = ["documentation", "guide", "tutorial", "concept", "architecture", "what is"]
        if any(kw in query_lower for kw in doc_keywords):
            tools_to_use.append("lookup_egeria_docs")
        
        # Default to search if no specific tool identified
        if not tools_to_use:
            tools_to_use.append("search_egeria_code")
        
        return {
            "use_tools": len(tools_to_use) > 0,
            "tools": tools_to_use
        }
    
    def _execute_tool(
        self,
        tool: Tool,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a tool with the given query."""
        try:
            # Extract parameters from context if available
            top_k = context.get("top_k", 5) if context else 5
            
            # Execute tool
            result = tool.run(query=query, top_k=top_k)
            return result.data if hasattr(result, 'data') else result
        except Exception as e:
            return {"error": str(e)}
    
    async def _generate_final_response(
        self,
        query: str,
        tool_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate final response incorporating tool results.
        
        This uses the LLM to synthesize tool results into a coherent answer.
        """
        if not tool_results:
            # No tools used, generate direct response
            response = await self.llm.generate(
                messages=self._messages,
                parameters=ChatModelParameters(
                    max_tokens=1000,
                    temperature=self.temperature
                )
            )
            return response.content
        
        # Format tool results for the LLM
        tool_context = self._format_tool_results(tool_results)
        
        # Create synthesis prompt
        synthesis_prompt = f"""Based on the following search results, answer the user's question: "{query}"

{tool_context}

Provide a clear, accurate answer that:
1. Directly addresses the question
2. Cites specific sources from the results
3. Includes relevant code examples if available
4. Is concise but complete

Answer:"""
        
        # Generate response
        messages = self._messages + [UserMessage(content=synthesis_prompt)]
        response = await self.llm.generate(
            messages=messages,
            parameters=ChatModelParameters(
                max_tokens=1500,
                temperature=self.temperature
            )
        )
        
        return response.content
    
    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results for inclusion in prompt."""
        formatted = []
        
        for result in tool_results:
            tool_name = result["tool"]
            data = result["result"]
            
            formatted.append(f"\n=== {tool_name} Results ===")
            
            if isinstance(data, dict):
                if "results" in data:
                    for i, item in enumerate(data["results"][:3], 1):  # Top 3 results
                        formatted.append(f"\nResult {i}:")
                        formatted.append(f"  File: {item.get('file_path', 'Unknown')}")
                        formatted.append(f"  Score: {item.get('relevance_score', 0)}")
                        formatted.append(f"  Content: {item.get('content', '')[:300]}...")
                elif "results_by_type" in data:
                    for elem_type, items in data["results_by_type"].items():
                        formatted.append(f"\n{elem_type}:")
                        for item in items[:2]:  # Top 2 per type
                            formatted.append(f"  - {item.get('name', 'unnamed')}")
                            formatted.append(f"    {item.get('code_snippet', '')[:200]}...")
        
        return "\n".join(formatted)
    
    def _get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get a tool by its name."""
        for tool in self.tools:
            tool_options = tool.options if hasattr(tool, 'options') else {}
            if tool_options.get("name") == name:
                return tool
        return None
    
    def clear_memory(self):
        """Clear conversation memory."""
        self._messages = [SystemMessage(content=self.system_prompt)]
    
    def clear_cache(self):
        """Clear response cache."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "memory_size": len(self._messages),
            "cache_size": len(self.cache._cache) if hasattr(self.cache, '_cache') else 0,
            "tools_available": len(self.tools),
            "model": self.llm.model
        }


def create_egeria_agent(**kwargs) -> EgeriaAgent:
    """
    Factory function to create an Egeria agent with default configuration.
    
    Parameters
    ----------
    **kwargs
        Override default configuration
        
    Returns
    -------
    EgeriaAgent
        Configured Egeria agent instance
    """
    # Load configuration
    config = get_full_config()
    llm_config = config["llm"]  # Dict access, value is LLMConfig Pydantic model
    
    # Merge with kwargs
    agent_config = {
        "model": llm_config.models.conversation,  # Use conversation model
        "base_url": llm_config.base_url,
        "temperature": llm_config.parameters.temperature,
        "max_tokens": 8000,
        "cache_size": 100
    }
    agent_config.update(kwargs)
    
    return EgeriaAgent(**agent_config)