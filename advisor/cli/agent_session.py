"""
Agent Interactive Session for Egeria Advisor

This module provides an interactive session using the ConversationAgent.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.table import Table

from advisor.agents.conversation_agent import create_agent


class AgentInteractiveSession:
    """Interactive REPL session using ConversationAgent."""
    
    # Special commands
    COMMANDS = {
        '/help': 'Show help message',
        '/clear': 'Clear conversation history',
        '/history': 'Show conversation history',
        '/stats': 'Show agent statistics',
        '/exit': 'Exit interactive mode',
        '/quit': 'Exit interactive mode',
        '/verbose': 'Toggle verbose mode',
        '/citations': 'Toggle citation display',
    }
    
    def __init__(self, options: Dict[str, Any], console: Console):
        """
        Initialize agent interactive session.
        
        Parameters
        ----------
        options : dict
            CLI options
        console : Console
            Rich console for output
        """
        self.options = options
        self.console = console
        
        # Session state
        self.running = True
        
        # Options
        self.verbose = options.get('verbose', False)
        self.show_citations = options.get('show_citations', True)
        
        # Initialize agent
        self.agent = None
        
        # Set up prompt session
        history_file = Path.home() / '.egeria_advisor_agent_history'
        self.prompt_session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self._create_completer(),
        )
    
    def _create_completer(self) -> WordCompleter:
        """Create command completer."""
        words = list(self.COMMANDS.keys()) + [
            'glossary', 'collection', 'asset', 'term', 'category',
            'create', 'find', 'update', 'delete', 'search',
            'how', 'what', 'why', 'when', 'where', 'show', 'example'
        ]
        return WordCompleter(words, ignore_case=True)
    
    def run(self):
        """Run the interactive REPL loop."""
        # Initialize agent
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                progress.add_task("Initializing agent...", total=None)
                self.agent = create_agent(max_history=10, cache_size=100, rag_top_k=5)
        except Exception as e:
            self.console.print(f"[red]✗ Failed to initialize agent:[/red] {e}")
            if self.verbose:
                self.console.print_exception()
            sys.exit(1)
        
        self.console.print("[green]✓[/green] Agent ready\n")
        
        try:
            while self.running:
                try:
                    # Get user input
                    user_input = self.prompt_session.prompt('agent> ')
                    
                    # Skip empty input
                    if not user_input.strip():
                        continue
                    
                    # Handle commands
                    if user_input.startswith('/'):
                        self._handle_command(user_input.strip())
                    else:
                        # Handle query
                        self._handle_query(user_input.strip())
                    
                    self.console.print()  # Add spacing
                
                except KeyboardInterrupt:
                    self.console.print("\n[dim]Use /exit or Ctrl+D to quit[/dim]")
                    continue
                except EOFError:
                    # Ctrl+D pressed
                    self.console.print("\n[cyan]Goodbye![/cyan]")
                    break
        
        finally:
            self._cleanup()
    
    def _handle_command(self, command: str):
        """
        Handle special commands.
        
        Parameters
        ----------
        command : str
            Command string starting with /
        """
        cmd = command.lower().split()[0]
        
        if cmd in ['/exit', '/quit']:
            self.console.print("[cyan]Goodbye![/cyan]")
            self.running = False
        
        elif cmd == '/help':
            self._show_help()
        
        elif cmd == '/clear':
            self.agent.clear_history()
            self.agent.clear_cache()
            self.console.print("[green]✓[/green] Conversation history and cache cleared")
        
        elif cmd == '/history':
            self._show_history()
        
        elif cmd == '/stats':
            self._show_stats()
        
        elif cmd == '/verbose':
            self.verbose = not self.verbose
            status = "enabled" if self.verbose else "disabled"
            self.console.print(f"[green]✓[/green] Verbose mode {status}")
        
        elif cmd == '/citations':
            self.show_citations = not self.show_citations
            status = "enabled" if self.show_citations else "disabled"
            self.console.print(f"[green]✓[/green] Citations {status}")
        
        else:
            self.console.print(f"[yellow]Unknown command:[/yellow] {cmd}")
            self.console.print("[dim]Type /help for available commands[/dim]")
    
    def _handle_query(self, query: str):
        """
        Handle user query.
        
        Parameters
        ----------
        query : str
            User's query
        """
        # Show processing indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task("Processing...", total=None)
            
            try:
                # Execute query with agent
                result = self.agent.run(query, use_rag=True)
                
                # Display response
                self.console.print(Panel(
                    Markdown(result["content"]),
                    title="[bold cyan]Agent Response[/bold cyan]",
                    border_style="cyan"
                ))
                
                # Show sources if enabled
                if self.show_citations and result.get("sources"):
                    self.console.print("\n[bold]Sources:[/bold]")
                    for i, source in enumerate(result["sources"][:5], 1):
                        file_path = source.get("file_path", "Unknown")
                        collection = source.get("collection", "Unknown")
                        score = source.get("score", 0.0)
                        self.console.print(
                            f"  [cyan]{i}.[/cyan] {file_path} "
                            f"[dim]({collection}, score: {score:.3f})[/dim]"
                        )
                
                # Show metadata if verbose
                if self.verbose:
                    self.console.print(f"\n[dim]RAG used: {result.get('rag_used', False)}, "
                                     f"Cache hit: {result.get('cache_hit', False)}[/dim]")
            
            except Exception as e:
                self.console.print(f"[red]✗ Error:[/red] {e}")
                if self.verbose:
                    self.console.print_exception()
    
    def _show_help(self):
        """Show help message."""
        help_text = "[bold cyan]Available Commands:[/bold cyan]\n\n"
        
        for cmd, desc in self.COMMANDS.items():
            help_text += f"  [cyan]{cmd:12}[/cyan] - {desc}\n"
        
        help_text += "\n[bold cyan]Agent Features:[/bold cyan]\n"
        help_text += "  • Conversational AI with memory\n"
        help_text += "  • RAG-enhanced responses with source citation\n"
        help_text += "  • Response caching for repeated queries\n"
        help_text += "  • Conversation history tracking\n"
        
        help_text += "\n[bold cyan]Tips:[/bold cyan]\n"
        help_text += "  • Ask follow-up questions - context is preserved\n"
        help_text += "  • Request code examples: 'Show me how to create a glossary'\n"
        help_text += "  • Use arrow keys to navigate history\n"
        
        self.console.print(Panel(help_text, border_style="cyan", padding=(1, 2)))
    
    def _show_history(self):
        """Show conversation history."""
        history = self.agent.get_history()
        
        if not history:
            self.console.print("[dim]No conversation history[/dim]")
            return
        
        self.console.print("[bold cyan]Conversation History:[/bold cyan]\n")
        
        for i, entry in enumerate(history, 1):
            query = entry['query']
            num_sources = entry.get('sources', 0)
            
            self.console.print(f"  [cyan]{i}.[/cyan] {query}")
            if self.verbose:
                response_preview = entry['response'][:100] + "..." if len(entry['response']) > 100 else entry['response']
                self.console.print(f"     [dim]{response_preview}[/dim]")
                self.console.print(f"     [dim]({num_sources} sources)[/dim]")
    
    def _show_stats(self):
        """Show agent statistics."""
        stats = self.agent.get_stats()
        
        table = Table(title="Agent Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Conversation Turns", str(stats['conversation_turns']))
        table.add_row("Cache Hits", str(stats['cache_hits']))
        table.add_row("Cache Misses", str(stats['cache_misses']))
        table.add_row("Cache Size", f"{stats['cache_size']}/{stats['cache_max_size']}")
        table.add_row("Cache Hit Rate", f"{stats['cache_hit_rate']:.1%}")
        
        self.console.print(table)
    
    def _cleanup(self):
        """Clean up session resources."""
        pass