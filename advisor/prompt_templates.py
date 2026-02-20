"""
Prompt templates for different query types and collections.

This module provides specialized prompts that adapt based on:
- Query type (explanation, code_search, example, etc.)
- Collection type (documentation, code, examples)
- Content language (Python, Java, Markdown)
"""

from typing import Dict, Optional, List
from advisor.query_patterns import QueryType
from advisor.collection_config import ContentType, Language


class PromptTemplateManager:
    """Manages prompt templates for different query scenarios."""
    
    def __init__(self):
        """Initialize prompt template manager."""
        self.system_prompts = self._build_system_prompts()
        self.query_type_instructions = self._build_query_type_instructions()
        self.collection_context = self._build_collection_context()
    
    def _build_system_prompts(self) -> Dict[str, str]:
        """Build system prompts for different collection types."""
        return {
            "documentation": """You are an expert Egeria documentation assistant.

CRITICAL RULES:
1. ONLY use information from the provided documentation context
2. Focus on conceptual explanations and architectural understanding
3. Explain WHY things work the way they do, not just HOW
4. Reference specific documentation sections and guides
5. If the documentation doesn't cover it, say so explicitly
6. Use clear, educational language suitable for learning
7. Provide links to related documentation when relevant

RESPONSE STYLE:
- Start with a clear conceptual explanation
- Use analogies and examples to clarify concepts
- Break down complex topics into digestible parts
- Cite documentation sources: "According to [guide/section]..."
- Suggest related topics for deeper understanding""",

            "python_code": """You are an expert Python developer specializing in the Egeria pyegeria library.

CRITICAL RULES:
1. ONLY use code from the provided context
2. Provide complete, runnable Python code examples
3. Include all necessary imports and setup
4. Show best practices and common patterns
5. Explain what each code section does
6. Include error handling where appropriate
7. Cite specific files, classes, and methods

RESPONSE STYLE:
- Start with a brief explanation of the approach
- Provide complete code with imports
- Add inline comments for clarity
- Show example usage and expected output
- Cite sources: "From pyegeria/[module].py: [Class.method]"
- Mention any prerequisites or dependencies""",

            "java_code": """You are an expert Java developer specializing in Egeria's Java implementation.

CRITICAL RULES:
1. ONLY use code from the provided context
2. Provide complete Java code examples with proper imports
3. Show OMAS, OMAG, and OMRS patterns correctly
4. Include proper exception handling
5. Reference specific packages and classes
6. Explain Spring Boot configuration when relevant
7. Show REST API endpoints and connectors

RESPONSE STYLE:
- Explain the Java architecture context first
- Provide complete code with package declarations
- Show configuration and setup requirements
- Include REST API examples when relevant
- Cite sources: "From [package].[Class]"
- Mention Maven/Gradle dependencies if needed""",

            "examples": """You are an expert at demonstrating Egeria through practical examples.

CRITICAL RULES:
1. ONLY use examples from the provided context
2. Show complete, working demonstrations
3. Include setup steps and prerequisites
4. Explain the use case and scenario
5. Provide step-by-step instructions
6. Show expected outputs and results
7. Reference specific notebooks or demo files

RESPONSE STYLE:
- Start with the use case and scenario
- Provide complete setup instructions
- Show step-by-step execution
- Include screenshots or output examples when available
- Cite sources: "From [workspace]/[notebook]"
- Suggest variations or extensions""",

            "cli": """You are an expert at using Egeria command-line tools.

CRITICAL RULES:
1. ONLY use commands from the provided context
2. Show complete command syntax with all options
3. Explain what each command does
4. Include setup and configuration steps
5. Show example outputs
6. Mention common errors and solutions
7. Reference specific CLI modules

RESPONSE STYLE:
- Start with what the command accomplishes
- Show complete command syntax
- Explain each parameter and option
- Provide example usage scenarios
- Show expected output
- Cite sources: "From hey_egeria [command]"
- Mention prerequisites and environment setup"""
        }
    
    def _build_query_type_instructions(self) -> Dict[QueryType, str]:
        """Build specific instructions for each query type."""
        return {
            QueryType.EXPLANATION: """
EXPLANATION QUERY - Focus on conceptual understanding:
- Start with a clear, high-level explanation
- Break down complex concepts into simple parts
- Use analogies and examples to clarify
- Explain the "why" behind design decisions
- Connect to broader Egeria architecture
- Avoid diving into code unless specifically asked""",

            QueryType.CODE_SEARCH: """
CODE SEARCH QUERY - Provide practical implementation:
- Show complete, runnable code immediately
- Include all necessary imports and setup
- Add inline comments explaining key parts
- Demonstrate best practices
- Show error handling
- Provide usage examples with expected output""",

            QueryType.EXAMPLE: """
EXAMPLE QUERY - Demonstrate practical usage:
- Provide multiple examples if available
- Show complete, working code
- Include setup and prerequisites
- Explain what each example demonstrates
- Show expected outputs
- Suggest variations or extensions""",

            QueryType.COMPARISON: """
COMPARISON QUERY - Highlight differences and similarities:
- Create a clear comparison structure
- List key differences first
- Explain when to use each option
- Provide examples of both approaches
- Mention trade-offs and considerations
- Recommend based on use case""",

            QueryType.BEST_PRACTICE: """
BEST PRACTICE QUERY - Provide authoritative guidance:
- State the recommended approach clearly
- Explain why it's considered best practice
- Show correct implementation
- Mention common mistakes to avoid
- Provide real-world examples
- Reference official guidelines""",

            QueryType.DEBUGGING: """
DEBUGGING QUERY - Help solve problems:
- Identify the likely cause first
- Provide step-by-step troubleshooting
- Show how to fix the issue
- Explain why the error occurs
- Mention common related issues
- Provide prevention tips""",

            QueryType.QUANTITATIVE: """
QUANTITATIVE QUERY - Provide specific metrics:
- Answer with specific numbers/counts
- Show how the metric was calculated
- Provide context for the numbers
- Mention any caveats or limitations
- Suggest related metrics if relevant""",

            QueryType.RELATIONSHIP: """
RELATIONSHIP QUERY - Explain connections:
- Map out the relationships clearly
- Show dependency graphs if relevant
- Explain how components interact
- Mention data flow and communication
- Provide architectural context""",

            QueryType.GENERAL: """
GENERAL QUERY - Provide comprehensive overview:
- Start with a broad introduction
- Cover key aspects systematically
- Provide examples where helpful
- Link to related topics
- Suggest next steps for learning"""
        }
    
    def _build_collection_context(self) -> Dict[str, str]:
        """Build context descriptions for different collections."""
        return {
            "egeria_docs": "official Egeria documentation, guides, and architectural references",
            "pyegeria": "Python client library code (pyegeria)",
            "pyegeria_cli": "command-line interface tools (hey_egeria)",
            "pyegeria_drE": "Dr. Egeria markdown-to-Python translator",
            "egeria_java": "Java implementation code (OMAS, OMAG, OMRS)",
            "egeria_workspaces": "example workspaces, Jupyter notebooks, and demonstrations"
        }
    
    def get_system_prompt(
        self,
        primary_collection: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        language: Optional[Language] = None
    ) -> str:
        """
        Get appropriate system prompt based on collection characteristics.
        
        Args:
            primary_collection: Name of primary collection being searched
            content_type: Type of content (code, documentation, examples)
            language: Primary language (python, java, markdown)
            
        Returns:
            Tailored system prompt
        """
        # Determine prompt type based on collection or content type
        if primary_collection:
            if "docs" in primary_collection:
                return self.system_prompts["documentation"]
            elif "cli" in primary_collection:
                return self.system_prompts["cli"]
            elif "workspace" in primary_collection or "example" in primary_collection:
                return self.system_prompts["examples"]
            elif "java" in primary_collection:
                return self.system_prompts["java_code"]
            else:
                return self.system_prompts["python_code"]
        
        # Fall back to content type
        if content_type == ContentType.DOCUMENTATION:
            return self.system_prompts["documentation"]
        elif content_type == ContentType.EXAMPLES:
            return self.system_prompts["examples"]
        elif language == Language.JAVA:
            return self.system_prompts["java_code"]
        else:
            return self.system_prompts["python_code"]
    
    def build_prompt(
        self,
        user_query: str,
        context: str,
        query_type: QueryType,
        collections_searched: Optional[list] = None,
        offer_examples: bool = False
    ) -> str:
        """
        Build complete prompt with query-type-specific instructions.
        
        Args:
            user_query: User's question
            context: Retrieved code/documentation context
            query_type: Type of query detected
            collections_searched: List of collections that were searched
            offer_examples: Whether to offer follow-up examples
            
        Returns:
            Complete prompt for LLM
        """
        if not context:
            return self._build_no_context_prompt(user_query)
        
        # Get query-type-specific instructions
        type_instructions = self.query_type_instructions.get(
            query_type,
            self.query_type_instructions[QueryType.GENERAL]
        )
        
        # Build collection context
        collection_info = ""
        if collections_searched:
            # Filter and get collection names, ensuring all are strings
            collection_names: List[str] = []
            for c in collections_searched[:3]:
                if c is not None:
                    name = self.collection_context.get(c, c)
                    if name is not None:
                        collection_names.append(name)
            
            if collection_names:
                collection_info = f"\n\nContext sources: {', '.join(collection_names)}"
        
        # Build follow-up suggestion
        followup = ""
        if offer_examples:
            followup = """

---

After answering, offer to show:
- A Python code example using pyegeria
- A Java implementation example  
- A REST API call example
- Related documentation or guides

Format: "Would you like to see an example? I can show you: [options]"
"""
        
        prompt = f"""# CONTEXT FROM EGERIA{collection_info}

{context}

# USER QUESTION

{user_query}

# QUERY TYPE: {query_type.value.upper()}
{type_instructions}

# YOUR TASK

Answer the question using ONLY the context above. Follow these rules:

1. Use ONLY information from the context - do not add external knowledge
2. Cite specific sources (files, classes, methods, documentation sections)
3. Be specific and technical - include details from the context
4. If the context doesn't fully answer the question, say so explicitly
5. Follow the query-type-specific instructions above{followup}

Now provide your answer:"""
        
        return prompt
    
    def _build_no_context_prompt(self, user_query: str) -> str:
        """Build prompt when no context is available."""
        return f"""# USER QUESTION

{user_query}

# IMPORTANT

No relevant context was found in the Egeria codebase for this question.

Please respond with:
"I don't have enough information in the Egeria codebase to answer that question accurately. 

Could you:
1. Rephrase your question with more specific terms?
2. Specify which part of Egeria you're asking about (Python client, Java implementation, documentation)?
3. Provide more context about what you're trying to accomplish?"

Then suggest related topics that might be helpful based on common Egeria concepts."""


# Singleton instance
_prompt_manager: Optional[PromptTemplateManager] = None


def get_prompt_manager() -> PromptTemplateManager:
    """Get singleton prompt template manager."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptTemplateManager()
    return _prompt_manager