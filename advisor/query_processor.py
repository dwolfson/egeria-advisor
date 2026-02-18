"""
Query processor for understanding and categorizing user queries.

This module analyzes user queries to determine intent and extract
relevant information for RAG retrieval.
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from loguru import logger
import re


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
        
        # Indicator lists for context-aware detection
        self.quantitative_indicators = [
            "how many", "how much", "count", "number of", "total",
            "average", "mean", "sum", "size", "amount"
        ]
        self.relationship_indicators = [
            "import", "depend", "use", "call", "inherit",
            "extend", "implement", "reference"
        ]
        self.debugging_indicators = [
            "error", "exception", "fail", "broken", "not working",
            "doesn't work", "isn't working", "bug", "issue"
        ]
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
        
        # Extract path filter (for scoped queries)
        path_filter = self.extract_path(query)
        
        # Determine search strategy
        search_strategy = self._determine_search_strategy(query_type)
        
        # Build result
        result = {
            "original_query": query,
            "query_type": query_type.value,
            "keywords": keywords,
            "path_filter": path_filter,  # NEW: for scoped queries
            "search_strategy": search_strategy,
            "enhanced_query": self._enhance_query(query, keywords)
        }
        
        log_msg = f"Processed query: type={query_type.value}, keywords={len(keywords)}"
        if path_filter:
            log_msg += f", path_filter={path_filter}"
        logger.info(log_msg)
        
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
    
    def detect_query_type_with_confidence(self, query: str) -> Tuple[QueryType, float]:
        """
        Detect query type with confidence score.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (QueryType, confidence_score)
            confidence_score is between 0.0 and 1.0
        """
        query_lower = query.lower()
        
        # Check for context-aware indicators first
        has_quantitative = any(ind in query_lower for ind in self.quantitative_indicators)
        has_relationship = any(ind in query_lower for ind in self.relationship_indicators)
        has_debugging = any(ind in query_lower for ind in self.debugging_indicators)
        
        # Detect base query type
        query_type = self._detect_query_type(query_lower)
        
        # Calculate confidence based on context
        confidence = self._calculate_confidence(
            query_lower, 
            query_type,
            has_quantitative,
            has_relationship,
            has_debugging
        )
        
        # Override if strong indicators present
        if has_quantitative and query_type == QueryType.EXPLANATION:
            query_type = QueryType.QUANTITATIVE
            confidence = 0.85
        elif has_relationship and query_type == QueryType.EXPLANATION:
            query_type = QueryType.RELATIONSHIP
            confidence = 0.85
        elif has_debugging and query_type == QueryType.EXPLANATION:
            query_type = QueryType.DEBUGGING
            confidence = 0.85
        
        return query_type, confidence
    
    def _calculate_confidence(
        self,
        query_lower: str,
        query_type: QueryType,
        has_quantitative: bool,
        has_relationship: bool,
        has_debugging: bool
    ) -> float:
        """
        Calculate confidence score for query type detection.
        
        Args:
            query_lower: Normalized query string
            query_type: Detected query type
            has_quantitative: Whether query has quantitative indicators
            has_relationship: Whether query has relationship indicators
            has_debugging: Whether query has debugging indicators
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence from pattern matching
        patterns = self.query_patterns.get(query_type, [])
        
        # Find the longest matching pattern
        max_pattern_length = 0
        for pattern in patterns:
            if pattern in query_lower:
                max_pattern_length = max(max_pattern_length, len(pattern))
        
        # Longer patterns = higher confidence
        if max_pattern_length == 0:
            base_confidence = 0.3  # Default for GENERAL
        elif max_pattern_length > 15:
            base_confidence = 0.95  # Very specific pattern
        elif max_pattern_length > 10:
            base_confidence = 0.85  # Specific pattern
        elif max_pattern_length > 5:
            base_confidence = 0.75  # Moderate pattern
        else:
            base_confidence = 0.65  # Short pattern
        
        # Adjust confidence based on context indicators
        if query_type == QueryType.QUANTITATIVE and has_quantitative:
            base_confidence = min(1.0, base_confidence + 0.1)
        elif query_type == QueryType.RELATIONSHIP and has_relationship:
            base_confidence = min(1.0, base_confidence + 0.1)
        elif query_type == QueryType.DEBUGGING and has_debugging:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        # Penalize conflicting indicators
        if query_type == QueryType.EXPLANATION:
            if has_quantitative or has_relationship or has_debugging:
                base_confidence = max(0.4, base_confidence - 0.2)
        
        return base_confidence
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
    
    def extract_path(self, query: str) -> Optional[str]:
        """
        Extract path/directory reference from query.
        
        Supports patterns like:
        - "in the pyegeria folder"
        - "under src/utils"
        - "within the tests directory"
        - "from pyegeria/admin"
        
        Args:
            query: User query string
            
        Returns:
            Extracted path string or None if no path found
        """
        query_lower = query.lower()
        
        # Pattern 1: "in [the] X folder/directory/package/module"
        match = re.search(r'in (?:the )?([a-z0-9_/.-]+) (?:folder|directory|package|module)', query_lower)
        if match:
            return match.group(1)
        
        # Pattern 2: "under X" or "within X"
        match = re.search(r'(?:under|within) (?:the )?([a-z0-9_/.-]+)', query_lower)
        if match:
            return match.group(1)
        
        # Pattern 3: "from X" (when X looks like a path)
        match = re.search(r'from (?:the )?([a-z0-9_/.-]+)', query_lower)
        if match:
            path = match.group(1)
            # Only return if it looks like a path (has / or common directory names)
            if '/' in path or path in ['src', 'tests', 'pyegeria', 'admin', 'utils', 'core']:
                return path
        
        # Pattern 4: Direct path reference (contains /)
        match = re.search(r'\b([a-z0-9_]+/[a-z0-9_/.-]+)\b', query_lower)
        if match:
            return match.group(1)
        
        return None
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
        
        # Extract path filter (for scoped queries)
        path_filter = self.extract_path(query)
        
        # Determine search strategy
        search_strategy = self._determine_search_strategy(query_type)
        
        # Build result - return enum instead of string value
        result = {
            "original_query": query,
            "normalized_query": normalized,
            "query_type": query_type,  # Return enum, not .value
            "keywords": keywords,
            "context": context,
            "path_filter": path_filter,  # NEW: for scoped queries
            "search_strategy": search_strategy,
            "enhanced_query": self._enhance_query(normalized, keywords)
        }
        
        log_msg = f"Processed query: type={query_type.value}, keywords={len(keywords)}"
        if path_filter:
            log_msg += f", path_filter={path_filter}"
        logger.info(log_msg)
        
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