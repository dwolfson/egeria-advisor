"""
Output Formatters for Egeria Advisor CLI

This module provides various formatters for displaying query results.
"""

import json
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


class ResponseFormatter:
    """Format and display query responses."""
    
    def __init__(
        self,
        format_type: str = 'text',
        show_citations: bool = True,
        verbose: bool = False
    ):
        """
        Initialize formatter.
        
        Parameters
        ----------
        format_type : str
            Output format: 'text', 'json', or 'markdown'
        show_citations : bool
            Whether to show source citations
        verbose : bool
            Whether to show verbose output
        """
        self.format_type = format_type.lower()
        self.show_citations = show_citations
        self.verbose = verbose
    
    def display(self, result: Dict[str, Any], console: Console):
        """
        Display formatted result.
        
        Parameters
        ----------
        result : dict
            Query result from RAG system
        console : Console
            Rich console for output
        """
        if self.format_type == 'json':
            self._display_json(result, console)
        elif self.format_type == 'markdown':
            self._display_markdown(result, console)
        else:
            self._display_text(result, console)
    
    def _display_text(self, result: Dict[str, Any], console: Console):
        """Display as rich formatted text."""
        
        # Query panel
        query = result.get('query', '')
        console.print(Panel(
            f"[bold]Query:[/bold] {query}",
            border_style="blue",
            padding=(0, 1)
        ))
        console.print()
        
        # Response
        response = result.get('response', '')
        console.print("[bold cyan]Answer:[/bold cyan]")
        console.print(response)
        console.print()
        
        # Code examples if present
        if 'code_examples' in result and result['code_examples']:
            console.print("[bold cyan]Code Example:[/bold cyan]")
            for i, code in enumerate(result['code_examples'], 1):
                syntax = Syntax(
                    code,
                    "python",
                    theme="monokai",
                    line_numbers=True,
                    padding=1
                )
                console.print(syntax)
                if i < len(result['code_examples']):
                    console.print()
        
        # Sources/Citations
        if self.show_citations and 'sources' in result:
            sources = result['sources']
            if sources:
                console.print("[bold cyan]Sources:[/bold cyan]")
                for source in sources[:5]:  # Show top 5 sources
                    file_path = source.get('file_path', 'Unknown')
                    name = source.get('name', 'Unknown')
                    score = source.get('score', 0.0)
                    
                    # Format source line
                    source_text = Text()
                    source_text.append("  • ", style="dim")
                    source_text.append(f"{file_path}", style="blue")
                    if name != 'Unknown':
                        source_text.append(f": {name}", style="white")
                    if self.verbose:
                        source_text.append(f" (score: {score:.3f})", style="dim")
                    
                    console.print(source_text)
                console.print()
        
        # Metadata footer
        if self.verbose:
            self._display_metadata(result, console)
    
    def _display_json(self, result: Dict[str, Any], console: Console):
        """Display as JSON."""
        # Clean up result for JSON output
        output = {
            'query': result.get('query', ''),
            'response': result.get('response', ''),
            'code_examples': result.get('code_examples', []),
            'sources': [
                {
                    'file_path': s.get('file_path', ''),
                    'name': s.get('name', ''),
                    'score': s.get('score', 0.0)
                }
                for s in result.get('sources', [])
            ] if self.show_citations else [],
            'metadata': {
                'response_time': result.get('response_time', 0.0),
                'num_sources': len(result.get('sources', [])),
            }
        }
        
        console.print_json(data=output)
    
    def _display_markdown(self, result: Dict[str, Any], console: Console):
        """Display as markdown."""
        md_lines = []
        
        # Query
        query = result.get('query', '')
        md_lines.append(f"# Query: {query}\n")
        
        # Response
        response = result.get('response', '')
        md_lines.append("## Answer\n")
        md_lines.append(f"{response}\n")
        
        # Code examples
        if 'code_examples' in result and result['code_examples']:
            md_lines.append("## Code Example\n")
            for code in result['code_examples']:
                md_lines.append("```python")
                md_lines.append(code)
                md_lines.append("```\n")
        
        # Sources
        if self.show_citations and 'sources' in result:
            sources = result['sources']
            if sources:
                md_lines.append("## Sources\n")
                for source in sources[:5]:
                    file_path = source.get('file_path', 'Unknown')
                    name = source.get('name', 'Unknown')
                    md_lines.append(f"- `{file_path}`: {name}")
                md_lines.append("")
        
        # Render markdown
        md_content = "\n".join(md_lines)
        md = Markdown(md_content)
        console.print(md)
    
    def _display_metadata(self, result: Dict[str, Any], console: Console):
        """Display metadata footer."""
        response_time = result.get('response_time', 0.0)
        num_sources = len(result.get('sources', []))
        confidence = result.get('confidence', 0.0)
        
        # Create metadata table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="dim")
        table.add_column(style="cyan")
        
        table.add_row("Response time:", f"{response_time:.2f}s")
        table.add_row("Sources found:", str(num_sources))
        if confidence > 0:
            table.add_row("Confidence:", f"{confidence:.2f}")
        
        console.print("─" * console.width)
        console.print(table)


class CodeFormatter:
    """Format code with syntax highlighting."""
    
    @staticmethod
    def format(code: str, language: str = "python", theme: str = "monokai") -> Syntax:
        """
        Format code with syntax highlighting.
        
        Parameters
        ----------
        code : str
            Code to format
        language : str
            Programming language
        theme : str
            Color theme
        
        Returns
        -------
        Syntax
            Rich Syntax object
        """
        return Syntax(
            code,
            language,
            theme=theme,
            line_numbers=True,
            padding=1
        )


class CitationFormatter:
    """Format source citations."""
    
    @staticmethod
    def format_citations(sources: List[Dict[str, Any]], max_sources: int = 5) -> Table:
        """
        Format citations as a table.
        
        Parameters
        ----------
        sources : list
            List of source dictionaries
        max_sources : int
            Maximum number of sources to display
        
        Returns
        -------
        Table
            Rich Table object
        """
        table = Table(title="Sources", show_header=True, header_style="bold cyan")
        table.add_column("File", style="blue")
        table.add_column("Element", style="white")
        table.add_column("Score", justify="right", style="dim")
        
        for source in sources[:max_sources]:
            file_path = source.get('file_path', 'Unknown')
            name = source.get('name', 'Unknown')
            score = source.get('score', 0.0)
            
            # Shorten file path if too long
            if len(file_path) > 50:
                file_path = "..." + file_path[-47:]
            
            table.add_row(file_path, name, f"{score:.3f}")
        
        return table


class ProgressFormatter:
    """Format progress indicators."""
    
    @staticmethod
    def create_spinner(message: str) -> tuple:
        """
        Create a spinner progress indicator.
        
        Parameters
        ----------
        message : str
            Progress message
        
        Returns
        -------
        tuple
            (Progress, task_id)
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        )
        task_id = progress.add_task(message, total=None)
        
        return progress, task_id


class ErrorFormatter:
    """Format error messages."""
    
    @staticmethod
    def format_error(error: Exception, verbose: bool = False, console: Console = None) -> None:
        """
        Format and display error message.
        
        Parameters
        ----------
        error : Exception
            The error to format
        verbose : bool
            Whether to show full traceback
        console : Console
            Rich console for output
        """
        if console is None:
            console = Console()
        
        console.print(f"\n[red]✗ Error:[/red] {str(error)}")
        
        if verbose:
            console.print("\n[dim]Full traceback:[/dim]")
            console.print_exception()
        else:
            console.print("[dim]Use --verbose for more details[/dim]")