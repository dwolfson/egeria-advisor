"""
Query processor for understanding and categorizing user queries.

This module analyzes user queries to determine intent and extract
relevant information for RAG retrieval.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from loguru import logger


class QueryType(Enum):
    """Types of queries the system can handle."""
    CODE_SEARCH = "code_search"  # Find specific code
    EXPLANATION = "explanation"  # Explain how something works
    EXAMPLE = "example"  # Show examples
    COMPARISON = "comparison"  # Compare approaches
    BEST_PRACTICE = "best_practice"  # Best practices
    DEBUGGING = "debugging"  # Help with errors
    GENERAL = "general"  # General question


class QueryProcessor:
    """Processes and analyzes user queries."""
    
    def __init__(self):
        """Initialize query processor."""
        self.query_patterns = self._build_query_patterns()
        logger.info("Initialized query processor")
    
    def _build_query_patterns(self) -> Dict[QueryType, List[str]]:
        """Build patterns for query type detection."""
        return {
            QueryType.CODE_SEARCH: [
                "find", "search", "locate", "where is", "show me",
                "get", "retrieve", "fetch"
            ],
            QueryType.EXPLANATION: [
                "how does", "how do", "explain", "what is", "what does",
                "why", "describe", "tell me about"
            ],
            QueryType.EXAMPLE: [
                "example", "sample", "demo", "show example",
                "how to use", "usage"
            ],
            QueryType.COMPARISON: [
                "compare", "difference", "versus", "vs", "better",
                "which", "choose between"
            ],
            QueryType.BEST_PRACTICE: [
                "best practice", "recommended", "should i", "proper way",
                "correct way", "standard"
            ],
            QueryType.DEBUGGING: [
                "error", "bug", "issue", "problem", "not working",
                "fix", "debug", "troubleshoot"
            ]
        }
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a user query.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with query analysis
        """
        query_lower = query.lower()
        
        # Detect query type
        query_type = self._detect_query_type(query_lower)
        
        # Extract keywords
        keywords = self._extract_keywords(query)
        
        # Determine search strategy
        search_strategy = self._determine_search_strategy(query_type)
        
        # Build result
        result = {
            "original_query": query,
            "query_type": query_type.value,
            "keywords": keywords,
            "search_strategy": search_strategy,
            "enhanced_query": self._enhance_query(query, keywords)
        }
        
        logger.info(f"Processed query: type={query_type.value}, keywords={len(keywords)}")
        
        return result
    
    def _detect_query_type(self, query_lower: str) -> QueryType:
        """Detect the type of query."""
        # Check each pattern
        for query_type, patterns in self.query_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    return query_type
        
        # Default to general
        return QueryType.GENERAL
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        # Simple keyword extraction
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "should", "could",
            "may", "might", "can", "i", "you", "he", "she", "it",
            "we", "they", "this", "that", "these", "those", "what",
            "which", "who", "when", "where", "why", "how", "me", "my"
        }
        
        # Split and filter
        words = query.lower().split()
        keywords = [
            word.strip(".,!?;:\"'()[]{}") 
            for word in words 
            if word.lower() not in stop_words and len(word) > 2
        ]
        
        return keywords
    
    def _determine_search_strategy(self, query_type: QueryType) -> Dict[str, Any]:
        """Determine search strategy based on query type."""
        strategies = {
            QueryType.CODE_SEARCH: {
                "top_k": 5,
                "min_score": 0.7,
                "format_style": "compact"
            },
            QueryType.EXPLANATION: {
                "top_k": 3,
                "min_score": 0.75,
                "format_style": "detailed"
            },
            QueryType.EXAMPLE: {
                "top_k": 5,
                "min_score": 0.7,
                "format_style": "detailed"
            },
            QueryType.COMPARISON: {
                "top_k": 6,
                "min_score": 0.65,
                "format_style": "detailed"
            },
            QueryType.BEST_PRACTICE: {
                "top_k": 4,
                "min_score": 0.75,
                "format_style": "detailed"
            },
            QueryType.DEBUGGING: {
                "top_k": 5,
                "min_score": 0.7,
                "format_style": "detailed"
            },
            QueryType.GENERAL: {
                "top_k": 3,
                "min_score": 0.7,
                "format_style": "detailed"
            }
        }
        
        return strategies.get(query_type, strategies[QueryType.GENERAL])
    
    def _enhance_query(self, query: str, keywords: List[str]) -> str:
        """Enhance query for better retrieval."""
        # For now, just return the original query
        # Could add query expansion, synonym handling, etc.
        return query
    
    def suggest_filters(self, query: str) -> Optional[Dict[str, Any]]:
        """Suggest metadata filters based on query."""
        query_lower = query.lower()
        filters = {}
        
        # Detect file type mentions
        if "test" in query_lower:
            filters["file_path"] = {"$regex": "test"}
        
        # Detect element type mentions
        if "class" in query_lower:
            filters["element_type"] = "class"
        elif "function" in query_lower or "def" in query_lower:
            filters["element_type"] = "function"
        elif "method" in query_lower:
            filters["element_type"] = "method"
        
        return filters if filters else None


# Global processor instance
_query_processor: Optional[QueryProcessor] = None


def get_query_processor() -> QueryProcessor:
    """Get or create the global query processor instance."""
    global _query_processor
    
    if _query_processor is None:
        _query_processor = QueryProcessor()
    
    return _query_processor