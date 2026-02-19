"""
Simple Egeria Advisor Agent using BeeAI components.

This implementation uses BeeAI's stable components (TokenMemory, SlidingCache, OllamaChatModel)
without inheriting from base classes to avoid abstract method complexity.
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

from advisor.rag_retrieval import RAGRetriever
from advisor.config import get_full_config


class SimpleEgeriaAgent:
    """
    Simple intelligent agent for Egeria development assistance.
    
    Uses BeeAI components (memory, cache, LLM) with direct RAG integration.
    No inheritance from BeeAI base classes to avoid API complexity.
    
    Features:
    - Token-aware memory management
    - Response caching
    - Direct RAG retrieval integration
    - Simple, maintainable implementation
    """
    
    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
        max_tokens: int = 8000,
        cache_size: int = 100,
        temperature: float = 0.7
    ):
        """
        Initialize the agent.
        
        Parameters
        ----------
        model : str
            Ollama model name
        base_url : str
            Ollama server URL
        max_tokens : int
            Maximum context tokens
        cache_size : int
            Cache size for responses
        temperature : float
            LLM temperature
        """
        # BeeAI components
        self.memory = TokenMemory(max_tokens=max_tokens)
        self.cache = SlidingCache(size=cache_size)
        self.llm = OllamaChatModel(model=model, base_url=base_url)
        self.temperature = temperature
        
        # Direct RAG integration
        self.rag = RAGRetriever(use_multi_collection=True, enable_cache=True)
        
        # System prompt
        self.system_prompt = """You are an expert Egeria developer assistant with deep knowledge of:
- Egeria Python library (pyegeria)
- Egeria Java implementation
- Egeria architecture and concepts
- Metadata management and governance

Your role is to help developers find relevant code examples, understand concepts, and solve problems.

When answering:
- Use search results to provide accurate information
- Include code examples when relevant
- Cite sources
- Be concise but thorough
"""
        
        # Initialize conversation
        self._messages = [SystemMessage(content=self.system_prompt)]
    
    async def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Process a query and generate a response.
        
        Parameters
        ----------
        query : str
            User's question
        top_k : int
            Number of RAG results to retrieve
            
        Returns
        -------
        dict
            Response with content and metadata
        """
        # Check cache (async)
        cache_key = f"query:{query}"
        cached = await self.cache.get(cache_key)
        if cached:
            return {
                "content": cached,
                "metadata": {"cache_hit": True, "rag_used": False}
            }
        
        # Retrieve relevant context from RAG
        rag_results = self.rag.retrieve(query=query, top_k=top_k)
        
        # Format RAG context
        context = self._format_rag_results(rag_results)
        
        # Create prompt with context
        prompt = f"""Question: {query}

Relevant information from Egeria codebase:
{context}

Please provide a clear, accurate answer based on the information above."""
        
        # Add to conversation
        self._messages.append(UserMessage(content=prompt))
        
        # Generate response
        response = await self.llm.generate(
            messages=self._messages,
            parameters=ChatModelParameters(
                max_tokens=1500,
                temperature=self.temperature
            )
        )
        
        # Add assistant response to history
        self._messages.append(AssistantMessage(content=response.content))
        
        # Cache response (async)
        await self.cache.set(cache_key, response.content)
        
        return {
            "content": response.content,
            "metadata": {
                "cache_hit": False,
                "rag_used": True,
                "rag_results": len(rag_results)
            }
        }
    
    def _format_rag_results(self, results: List[Any]) -> str:
        """Format RAG results for prompt."""
        if not results:
            return "No relevant information found."
        
        formatted = []
        for i, result in enumerate(results[:3], 1):  # Top 3
            file_path = result.metadata.get('file_path', 'Unknown')
            collection = result.metadata.get('collection', 'Unknown')
            score = result.score
            # SearchResult uses 'text' not 'content'
            content = result.text[:400] if hasattr(result, 'text') else str(result)[:400]
            
            formatted.append(f"\n{i}. [{collection}] {file_path} (relevance: {score:.3f})")
            formatted.append(f"   {content}...")
        
        return "\n".join(formatted)
    
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
            "model": self.llm.model
        }


def create_simple_agent(**kwargs) -> SimpleEgeriaAgent:
    """
    Factory function to create an agent with default configuration.
    
    Parameters
    ----------
    **kwargs
        Override default configuration
        
    Returns
    -------
    SimpleEgeriaAgent
        Configured agent instance
    """
    # Load configuration
    config = get_full_config()
    llm_config = config["llm"]
    
    # Merge with kwargs
    agent_config = {
        "model": llm_config.models.conversation,
        "base_url": llm_config.base_url,
        "temperature": llm_config.parameters.temperature,
        "max_tokens": 8000,
        "cache_size": 100
    }
    agent_config.update(kwargs)
    
    return SimpleEgeriaAgent(**agent_config)