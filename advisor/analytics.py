"""
Analytics module for codebase statistics and quantitative queries.

This module provides access to codebase statistics and metrics for
answering quantitative questions about the egeria-python repository.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger

from advisor.config import settings


class AnalyticsManager:
    """Manages codebase analytics and statistics."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize analytics manager.
        
        Args:
            cache_dir: Directory containing cached statistics
        """
        self.cache_dir = cache_dir or Path(settings.advisor_cache_dir)
        self.stats: Optional[Dict[str, Any]] = None
        self.directory_stats: Optional[Dict[str, Any]] = None
        self._load_statistics()
        self._load_directory_statistics()
    
    def _load_statistics(self):
        """Load statistics from cache."""
        summary_file = self.cache_dir / "pipeline_summary.json"
        
        if not summary_file.exists():
            logger.warning(f"Statistics file not found: {summary_file}")
            self.stats = {}
            return
        
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
                self.stats = data.get("statistics", {})
            logger.info(f"Loaded statistics from {summary_file}")
        except Exception as e:
            logger.error(f"Failed to load statistics: {e}")
            self.stats = {}
    
    def _load_directory_statistics(self):
        """Load per-directory statistics from cache."""
        dir_stats_file = self.cache_dir / "directory_stats.json"
        
        if not dir_stats_file.exists():
            logger.warning(f"Directory statistics file not found: {dir_stats_file}")
            logger.info("Run scripts/generate_directory_stats.py to enable scoped queries")
            self.directory_stats = {}
            return
        
        try:
            with open(dir_stats_file, 'r') as f:
                self.directory_stats = json.load(f)
            logger.info(f"Loaded directory statistics from {dir_stats_file}")
            logger.info(f"Directories available: {', '.join([d for d in self.directory_stats.keys() if d != '_total'])}")
        except Exception as e:
            logger.error(f"Failed to load directory statistics: {e}")
            self.directory_stats = {}
    
    def get_total_classes(self, path_filter: Optional[str] = None) -> int:
        """
        Get total number of classes, optionally filtered by path.
        
        Args:
            path_filter: Optional directory path to filter by (e.g., "pyegeria")
            
        Returns:
            Count of classes
        """
        if path_filter and self.directory_stats:
            # Normalize path filter
            path_filter = path_filter.lower().strip('/')
            dir_data = self.directory_stats.get(path_filter, {})
            return dir_data.get('classes', 0)
        return self.stats.get("code", {}).get("by_type", {}).get("class", 0)
    
    def get_total_functions(self, path_filter: Optional[str] = None) -> int:
        """
        Get total number of functions, optionally filtered by path.
        
        Args:
            path_filter: Optional directory path to filter by
            
        Returns:
            Count of functions
        """
        if path_filter and self.directory_stats:
            path_filter = path_filter.lower().strip('/')
            dir_data = self.directory_stats.get(path_filter, {})
            return dir_data.get('functions', 0)
        return self.stats.get("code", {}).get("by_type", {}).get("function", 0)
    
    def get_total_methods(self, path_filter: Optional[str] = None) -> int:
        """
        Get total number of methods, optionally filtered by path.
        
        Args:
            path_filter: Optional directory path to filter by
            
        Returns:
            Count of methods
        """
        if path_filter and self.directory_stats:
            path_filter = path_filter.lower().strip('/')
            dir_data = self.directory_stats.get(path_filter, {})
            return dir_data.get('methods', 0)
        return self.stats.get("code", {}).get("by_type", {}).get("method", 0)
    
    def get_total_code_elements(self) -> int:
        """Get total number of code elements (classes + functions + methods)."""
        return self.stats.get("code", {}).get("total", 0)
    
    def get_total_files(self) -> int:
        """Get total number of files."""
        return self.stats.get("metadata", {}).get("total_files", 0)
    
    def get_total_python_files(self) -> int:
        """Get total number of Python files."""
        return self.stats.get("metadata", {}).get("by_type", {}).get("python", 0)
    
    def get_total_lines_of_code(self) -> int:
        """Get total lines of code."""
        return self.stats.get("metadata", {}).get("total_lines", 0)
    
    def get_total_size_bytes(self) -> int:
        """Get total codebase size in bytes."""
        return self.stats.get("metadata", {}).get("total_size_bytes", 0)
    
    def get_files_by_category(self) -> Dict[str, int]:
        """Get file counts by category."""
        return self.stats.get("metadata", {}).get("by_category", {})
    
    def get_public_elements_count(self) -> int:
        """Get count of public code elements."""
        return self.stats.get("code", {}).get("public_elements", 0)
    
    def get_elements_with_docstrings(self) -> int:
        """Get count of elements with docstrings."""
        return self.stats.get("code", {}).get("with_docstrings", 0)
    
    def get_average_complexity(self) -> float:
        """Get average cyclomatic complexity."""
        return self.stats.get("code", {}).get("avg_complexity", 0.0)
    
    def get_total_documentation_sections(self) -> int:
        """Get total documentation sections."""
        return self.stats.get("documentation", {}).get("total", 0)
    
    def get_total_examples(self) -> int:
        """Get total number of examples."""
        return self.stats.get("examples", {}).get("total", 0)
    
    def get_examples_by_type(self) -> Dict[str, int]:
        """Get example counts by type."""
        return self.stats.get("examples", {}).get("by_type", {})
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of statistics."""
        return {
            "code": {
                "total_elements": self.get_total_code_elements(),
                "classes": self.get_total_classes(),
                "functions": self.get_total_functions(),
                "methods": self.get_total_methods(),
                "public_elements": self.get_public_elements_count(),
                "with_docstrings": self.get_elements_with_docstrings(),
                "avg_complexity": self.get_average_complexity(),
            },
            "files": {
                "total": self.get_total_files(),
                "python": self.get_total_python_files(),
                "by_category": self.get_files_by_category(),
            },
            "size": {
                "total_bytes": self.get_total_size_bytes(),
                "total_lines": self.get_total_lines_of_code(),
            },
            "documentation": {
                "sections": self.get_total_documentation_sections(),
            },
            "examples": {
                "total": self.get_total_examples(),
                "by_type": self.get_examples_by_type(),
            }
        }
    
    def answer_quantitative_query(self, query: str, path_filter: Optional[str] = None) -> str:
        """
        Answer a quantitative query about the codebase.
        
        Args:
            query: User's quantitative question
            path_filter: Optional directory path to filter by (e.g., "pyegeria")
            
        Returns:
            Formatted answer with statistics
        """
        query_lower = query.lower()
        
        # Build scope description
        if path_filter:
            scope = f"the **{path_filter}** directory"
        else:
            scope = "the egeria-python codebase"
        
        # Detect what the user is asking about
        if "how many class" in query_lower:
            count = self.get_total_classes(path_filter)
            return f"There are **{count:,} classes** in {scope}."
        
        elif "how many function" in query_lower:
            count = self.get_total_functions(path_filter)
            return f"There are **{count:,} functions** in {scope}."
        
        elif "how many method" in query_lower:
            count = self.get_total_methods(path_filter)
            return f"There are **{count:,} methods** in {scope}."
        
        elif "how many file" in query_lower or "total file" in query_lower:
            total = self.get_total_files()
            python = self.get_total_python_files()
            return f"There are **{total:,} total files** in the codebase, including **{python:,} Python files**."
        
        elif "lines of code" in query_lower or "loc" in query_lower:
            lines = self.get_total_lines_of_code()
            return f"The codebase contains **{lines:,} lines of code**."
        
        elif "how many module" in query_lower:
            # Modules are roughly equivalent to Python files
            count = self.get_total_python_files()
            return f"There are approximately **{count:,} modules** (Python files) in the codebase."
        
        elif "size" in query_lower and ("codebase" in query_lower or "repository" in query_lower):
            size_bytes = self.get_total_size_bytes()
            size_mb = size_bytes / (1024 * 1024)
            return f"The codebase is **{size_mb:.1f} MB** ({size_bytes:,} bytes)."
        
        elif "docstring" in query_lower:
            count = self.get_elements_with_docstrings()
            total = self.get_total_code_elements()
            percentage = (count / total * 100) if total > 0 else 0
            return f"**{count:,} code elements** ({percentage:.1f}%) have docstrings."
        
        elif "public" in query_lower:
            count = self.get_public_elements_count()
            total = self.get_total_code_elements()
            percentage = (count / total * 100) if total > 0 else 0
            return f"**{count:,} code elements** ({percentage:.1f}%) are public."
        
        elif "complexity" in query_lower:
            avg = self.get_average_complexity()
            return f"The average cyclomatic complexity is **{avg:.2f}**."
        
        elif "example" in query_lower:
            count = self.get_total_examples()
            by_type = self.get_examples_by_type()
            details = ", ".join([f"{count} {type_}" for type_, count in by_type.items()])
            return f"There are **{count:,} examples** in the codebase ({details})."
        
        elif "documentation" in query_lower or "doc section" in query_lower:
            count = self.get_total_documentation_sections()
            return f"There are **{count:,} documentation sections** in the codebase."
        
        elif "category" in query_lower or "breakdown" in query_lower:
            by_category = self.get_files_by_category()
            lines = ["**Files by category:**"]
            for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {category}: {count:,} files")
            return "\n".join(lines)
        
        elif "summary" in query_lower or "overview" in query_lower or "statistics" in query_lower:
            summary = self.get_summary()
            return self._format_summary(summary)
        
        else:
            # Default: provide a general summary
            return self._format_summary(self.get_summary())
    
    def _format_summary(self, summary: Dict[str, Any]) -> str:
        """Format a summary dictionary into a readable string."""
        lines = ["**Codebase Statistics:**\n"]
        
        # Code statistics
        code = summary["code"]
        lines.append(f"**Code Elements:** {code['total_elements']:,}")
        lines.append(f"  - Classes: {code['classes']:,}")
        lines.append(f"  - Functions: {code['functions']:,}")
        lines.append(f"  - Methods: {code['methods']:,}")
        lines.append(f"  - Public: {code['public_elements']:,} ({code['public_elements']/code['total_elements']*100:.1f}%)")
        lines.append(f"  - With docstrings: {code['with_docstrings']:,} ({code['with_docstrings']/code['total_elements']*100:.1f}%)")
        lines.append(f"  - Avg complexity: {code['avg_complexity']:.2f}\n")
        
        # File statistics
        files = summary["files"]
        lines.append(f"**Files:** {files['total']:,}")
        lines.append(f"  - Python files: {files['python']:,}\n")
        
        # Size statistics
        size = summary["size"]
        size_mb = size['total_bytes'] / (1024 * 1024)
        lines.append(f"**Size:**")
        lines.append(f"  - Total: {size_mb:.1f} MB")
        lines.append(f"  - Lines of code: {size['total_lines']:,}\n")
        
        # Documentation
        docs = summary["documentation"]
        lines.append(f"**Documentation:** {docs['sections']:,} sections\n")
        
        # Examples
        examples = summary["examples"]
        lines.append(f"**Examples:** {examples['total']:,}")
        
        return "\n".join(lines)


# Global analytics manager instance
_analytics_manager: Optional[AnalyticsManager] = None


def get_analytics_manager() -> AnalyticsManager:
    """Get or create the global analytics manager instance."""
    global _analytics_manager
    
    if _analytics_manager is None:
        _analytics_manager = AnalyticsManager()
    
    return _analytics_manager