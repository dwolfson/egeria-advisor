"""
Complete RAG system integrating retrieval, query processing, and LLM generation.

This module provides the main interface for the RAG-based code advisor.
"""

from typing import Dict, Any, Optional, List
from loguru import logger
import time

from advisor.llm_client import get_ollama_client
from advisor.rag_retrieval import get_rag_retriever
from advisor.query_processor import get_query_processor
from advisor.mlflow_tracking import get_mlflow_tracker
from advisor.config import get_full_config


class RAGSystem:
    """Complete RAG system for code advisory."""

    def __init__(self):
        """Initialize RAG system."""
        self.llm_client = get_ollama_client()
        self.retriever = get_rag_retriever()
        self.query_processor = get_query_processor()
        self.mlflow_tracker = get_mlflow_tracker()

        config = get_full_config()
        self.rag_config = config.get("rag")

        logger.info("Initialized RAG system")

    def query(
        self,
        user_query: str,
        include_context: bool = True,
        track_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query and generate a response.

        Args:
            user_query: User's question or request
            include_context: Whether to include retrieved context
            track_metrics: Whether to track with MLflow

        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Processing query: {user_query[:100]}...")

        # Track with MLflow if enabled
        if track_metrics:
            with self.mlflow_tracker.track_operation(
                operation_name="rag_query",
                params={
                    "query_length": len(user_query),
                    "include_context": include_context
                }
            ) as tracker:
                result = self._process_query(user_query, include_context)
                tracker.log_metrics({
                    "response_length": len(result["response"]),
                    "num_sources": result.get("num_sources", 0),
                    "retrieval_time": result.get("retrieval_time", 0.0),
                    "generation_time": result.get("generation_time", 0.0),
                    "avg_relevance_score": result.get("avg_relevance_score", 0.0),
                    "context_length": result.get("context_length", 0)
                })
                return result
        else:
            return self._process_query(user_query, include_context)

    def _process_query(
        self,
        user_query: str,
        include_context: bool
    ) -> Dict[str, Any]:
        """Internal query processing."""
        # Process query to understand intent
        query_analysis = self.query_processor.process(user_query)
        logger.info(f"Query type: {query_analysis['query_type']}")

        # Get search strategy
        search_strategy = query_analysis["search_strategy"]

        # Retrieve relevant context with timing
        retrieval_start = time.time()
        if include_context:
            context, sources = self.retriever.retrieve_and_build_context(
                query=query_analysis["enhanced_query"],
                top_k=search_strategy["top_k"],
                min_score=search_strategy["min_score"],
                format_style=search_strategy["format_style"]
            )
        else:
            context = ""
            sources = []
        retrieval_time = time.time() - retrieval_start

        # Build prompt
        prompt = self._build_prompt(
            user_query=user_query,
            context=context,
            query_type=query_analysis["query_type"]
        )

        # Generate response with timing
        generation_start = time.time()
        response = self.llm_client.generate(
            prompt=prompt,
            system=self._get_system_prompt(),
            temperature=self.rag_config.generation.temperature,
            max_tokens=self.rag_config.generation.max_tokens
        )
        generation_time = time.time() - generation_start

        # Calculate average relevance score
        avg_relevance_score = 0.0
        if sources:
            avg_relevance_score = sum(s.get("score", 0.0) for s in sources) / len(sources)

        # Build result with enhanced metrics
        result = {
            "query": user_query,
            "response": response,
            "query_type": query_analysis["query_type"],
            "sources": sources,
            "num_sources": len(sources),
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "avg_relevance_score": avg_relevance_score,
            "context_length": len(context)
        }

        logger.info(f"Generated response: {len(response)} chars from {len(sources)} sources")

        return result

    def _get_system_prompt(self) -> str:
        """Get system prompt for the LLM."""
        return """You are an expert code advisor for the Egeria project. Your role is to:

1. Provide accurate, helpful information about the codebase
2. Explain code functionality clearly and concisely
3. Suggest best practices and improvements
4. Help debug issues and understand error messages
5. Reference specific code examples when relevant

Guidelines:
- Be precise and technical when needed
- Provide code examples to illustrate points
- Cite specific files/functions when referencing code
- If you're unsure, say so rather than guessing
- Keep responses focused and relevant to the question

When code context is provided, use it to give specific, accurate answers.
When no context is available, provide general guidance based on best practices."""

    def _build_prompt(
        self,
        user_query: str,
        context: str,
        query_type: str
    ) -> str:
        """Build the complete prompt for the LLM."""
        if context:
            prompt = f"""Based on the following code from the Egeria project, please answer the user's question.

# Relevant Code Context

{context}

# User Question

{user_query}

# Instructions

Please provide a helpful, accurate response based on the code context above. Reference specific code elements when relevant."""
        else:
            prompt = f"""# User Question

{user_query}

# Instructions

Please provide a helpful response based on your knowledge of software development best practices. Note that no specific code context is available for this query."""

        return prompt

    def chat(
        self,
        messages: List[Dict[str, str]],
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Multi-turn chat interface.

        Args:
            messages: List of message dicts with 'role' and 'content'
            include_context: Whether to retrieve context for last message

        Returns:
            Dictionary with response and metadata
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        # Get last user message
        last_message = messages[-1]["content"]

        # Process like a regular query
        result = self.query(last_message, include_context=include_context)

        return result

    def explain_code(
        self,
        code_snippet: str,
        context: Optional[str] = None,
        track_metrics: bool = True
    ) -> str:
        """
        Explain a code snippet.

        Args:
            code_snippet: Code to explain
            context: Optional additional context
            track_metrics: Whether to track with MLflow

        Returns:
            Explanation text
        """
        if track_metrics:
            with self.mlflow_tracker.track_operation(
                operation_name="explain_code",
                params={
                    "code_length": len(code_snippet),
                    "has_context": context is not None
                }
            ) as tracker:
                generation_start = time.time()

                prompt = f"""Please explain the following code:

```python
{code_snippet}
```
"""

                if context:
                    prompt += f"\n\nAdditional context: {context}"

                response = self.llm_client.generate(
                    prompt=prompt,
                    system=self._get_system_prompt(),
                    temperature=0.3  # Lower temperature for explanations
                )

                generation_time = time.time() - generation_start

                tracker.log_metrics({
                    "response_length": len(response),
                    "generation_time": generation_time
                })

                return response
        else:
            prompt = f"""Please explain the following code:

```python
{code_snippet}
```
"""

            if context:
                prompt += f"\n\nAdditional context: {context}"

            response = self.llm_client.generate(
                prompt=prompt,
                system=self._get_system_prompt(),
                temperature=0.3  # Lower temperature for explanations
            )

            return response

    def find_similar_code(
        self,
        code_snippet: str,
        top_k: int = 5,
        track_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find code similar to a given snippet.

        Args:
            code_snippet: Code to find similar examples for
            top_k: Number of results
            track_metrics: Whether to track with MLflow

        Returns:
            List of similar code snippets
        """
        if track_metrics:
            with self.mlflow_tracker.track_operation(
                operation_name="find_similar_code",
                params={
                    "code_length": len(code_snippet),
                    "top_k": top_k
                }
            ) as tracker:
                results = self.retriever.get_similar_code(
                    code_snippet=code_snippet,
                    top_k=top_k
                )

                # Calculate average similarity score
                avg_similarity_score = 0.0
                if results:
                    avg_similarity_score = sum(r.get("score", 0.0) for r in results) / len(results)

                tracker.log_metrics({
                    "num_results": len(results),
                    "avg_similarity_score": avg_similarity_score
                })

                return results
        else:
            return self.retriever.get_similar_code(
                code_snippet=code_snippet,
                top_k=top_k
            )

    def get_file_summary(
        self,
        file_path: str,
        track_metrics: bool = True
    ) -> str:
        """
        Get a summary of a file's contents.

        Args:
            file_path: Path to file
            track_metrics: Whether to track with MLflow

        Returns:
            Summary text
        """
        if track_metrics:
            with self.mlflow_tracker.track_operation(
                operation_name="get_file_summary",
                params={
                    "file_path": file_path
                }
            ) as tracker:
                generation_start = time.time()

                # Get file context
                context = self.retriever.get_file_context(file_path)

                # Generate summary
                prompt = f"""Please provide a concise summary of this file's purpose and main components:

{context}

Focus on:
1. Main purpose of the file
2. Key classes/functions
3. Important functionality"""

                response = self.llm_client.generate(
                    prompt=prompt,
                    system=self._get_system_prompt(),
                    temperature=0.3,
                    max_tokens=500
                )

                generation_time = time.time() - generation_start

                # Count code elements (classes, functions, etc.)
                num_code_elements = context.count("class ") + context.count("def ")

                tracker.log_metrics({
                    "response_length": len(response),
                    "num_code_elements": num_code_elements,
                    "generation_time": generation_time
                })

                return response
        else:
            # Get file context
            context = self.retriever.get_file_context(file_path)

            # Generate summary
            prompt = f"""Please provide a concise summary of this file's purpose and main components:

{context}

Focus on:
1. Main purpose of the file
2. Key classes/functions
3. Important functionality"""

            response = self.llm_client.generate(
                prompt=prompt,
                system=self._get_system_prompt(),
                temperature=0.3,
                max_tokens=500
            )

            return response

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all system components.

        Returns:
            Dictionary with component health status
        """
        # Ensure vector store is connected
        if not self.retriever.vector_store.is_connected():
            try:
                self.retriever.vector_store.connect()
            except Exception as e:
                logger.warning(f"Failed to connect to vector store during health check: {e}")

        health = {
            "llm_available": self.llm_client.is_available(),
            "vector_store_connected": self.retriever.vector_store.is_connected(),
            "embedding_model_loaded": self.retriever.embedding_gen.model is not None
        }

        logger.info(f"Health check: {health}")

        return health


# Global RAG system instance
_rag_system: Optional[RAGSystem] = None


def get_rag_system() -> RAGSystem:
    """Get or create the global RAG system instance."""
    global _rag_system

    if _rag_system is None:
        _rag_system = RAGSystem()

    return _rag_system
