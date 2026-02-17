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
    QUANTITATIVE = "quantitative"  # Statistics and metrics
    RELATIONSHIP = "relationship"  # Code relationships
    GENERAL = "general"  # General question


class QueryProcessor:
    """Processes and analyzes user queries."""
    
    def __init__(self):
        """Initialize query processor."""
        self.query_patterns = self._build_query_patterns()
        logger.info("Initialized query processor")
    
    def _build_query_patterns(self) -> Dict[QueryType, List[str]]:
        """
        Build patterns for query type detection with priority ordering.
        
        Patterns are checked in order of specificity (most specific first).
        Multi-word patterns are checked before single-word patterns.
        """
        return {
            # High priority - specific multi-word patterns
            QueryType.QUANTITATIVE: [
                "how many", "how much", "number of", "lines of code",
                "count", "total", "statistics", "metrics", "size",
                "summary", "overview"
            ],
            QueryType.BEST_PRACTICE: [
                "best practice", "best way", "recommended", "should i",
                "proper way", "correct way", "standard", "recommended approach"
            ],
            QueryType.COMPARISON: [
                "difference between", "compare", "versus", "vs",
                "differ from", "better", "which", "choose between"
            ],
            QueryType.DEBUGGING: [
                "not working", "isn't working", "error", "bug", "issue",
                "problem", "fix", "debug", "troubleshoot", "getting an error"
            ],
            # Medium priority - action-oriented patterns
            QueryType.CODE_SEARCH: [
                "show me how", "how do i", "how to", "find", "search",
                "locate", "where is", "show me", "get", "retrieve", "fetch",
                "give me"
            ],
            QueryType.EXAMPLE: [
                "show example", "give me example", "examples of", "example",
                "sample", "demo", "how to use", "usage", "some examples"
            ],
            QueryType.EXPLANATION: [
                "how does", "explain", "what is", "what does", "what are",
                "why", "describe", "tell me about"
            ],
            # Lower priority - relationship patterns (often overlap)
            QueryType.RELATIONSHIP: [
                "what calls", "what imports", "related to", "relationship",
                "connected", "belong to", "methods of", "inherits",
                "extends", "uses", "depends on"
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
    
    def detect_query_type(self, query: str) -> QueryType:
        """
        Detect the type of query (public method for testing).
        
        Args:
            query: User query string
            
        Returns:
            QueryType enum value
        """
        return self._detect_query_type(query.lower())
    
    def _detect_query_type(self, query_lower: str) -> QueryType:
        """
        Detect the type of query using priority-based pattern matching.
        
        Checks patterns in order of specificity:
        1. Multi-word patterns first (more specific)
        2. Single-word patterns last (less specific)
        3. Returns first match found
        """
        # Sort patterns by length (longer = more specific)
        for query_type, patterns in self.query_patterns.items():
            # Sort patterns by length descending (check longer patterns first)
            sorted_patterns = sorted(patterns, key=len, reverse=True)
            for pattern in sorted_patterns:
                if pattern in query_lower:
                    return query_type
        
        # Default to general
        return QueryType.GENERAL
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize query text (public method for testing).
        
        Args:
            query: User query string
            
        Returns:
            Normalized query string (lowercase, trimmed whitespace)
        """
        # Remove extra whitespace
        normalized = " ".join(query.split())
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        # Convert to lowercase for consistent matching
        normalized = normalized.lower()
        return normalized
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query (public method for testing).
        
        Args:
            query: User query string
            
        Returns:
            List of keywords
        """
        return self._extract_keywords(query)
    
    def extract_context(self, query: str) -> Dict[str, Any]:
        """
        Extract contextual information from query (public method for testing).
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with context information
        """
        query_lower = query.lower()
        context = {
            "has_code_reference": any(word in query_lower for word in ["class", "function", "method", "def"]),
            "has_file_reference": any(word in query_lower for word in ["file", "module", "package"]),
            "has_error_reference": any(word in query_lower for word in ["error", "exception", "bug", "issue"]),
            "has_quantitative": any(word in query_lower for word in ["how many", "count", "total", "number"]),
            "has_relationship": any(word in query_lower for word in ["calls", "uses", "imports", "inherits"]),
        }
        return context
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query and return comprehensive analysis (public method for testing).
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with complete query analysis
            
        Raises:
            ValueError: If query is empty or invalid
        """
        # Validate query
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Normalize the query
        normalized = self.normalize_query(query)
        
        # Detect query type
        query_type = self.detect_query_type(normalized)
        
        # Extract keywords
        keywords = self.extract_keywords(normalized)
        
        # Extract context
        context = self.extract_context(normalized)
        
        # Determine search strategy
        search_strategy = self._determine_search_strategy(query_type)
        
        # Build result - return enum instead of string value
        result = {
            "original_query": query,
            "normalized_query": normalized,
            "query_type": query_type,  # Return enum, not .value
            "keywords": keywords,
            "context": context,
            "search_strategy": search_strategy,
            "enhanced_query": self._enhance_query(normalized, keywords)
        }
        
        logger.info(f"Processed query: type={query_type.value}, keywords={len(keywords)}")
        
        return result
    
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
                "top_k": 10,
                "min_score": 0.3,
                "format_style": "compact"
            },
            QueryType.EXPLANATION: {
                "top_k": 10,
                "min_score": 0.3,
                "format_style": "detailed"
            },
            QueryType.EXAMPLE: {
                "top_k": 10,
                "min_score": 0.3,
                "format_style": "detailed"
            },
            QueryType.COMPARISON: {
                "top_k": 10,
                "min_score": 0.3,
                "format_style": "detailed"
            },
            QueryType.BEST_PRACTICE: {
                "top_k": 10,
                "min_score": 0.3,
                "format_style": "detailed"
            },
            QueryType.DEBUGGING: {
                "top_k": 10,
                "min_score": 0.3,
                "format_style": "detailed"
            },
            QueryType.GENERAL: {
                "top_k": 10,
                "min_score": 0.3,
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