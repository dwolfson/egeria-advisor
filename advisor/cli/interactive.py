"""
Interactive REPL Mode for Egeria Advisor

This module provides an interactive session with command history and context preservation.
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

from advisor.cli.formatters import ResponseFormatter


class InteractiveSession:
    """Interactive REPL session for the Egeria Advisor."""
    
    # Special commands
    COMMANDS = {
        '/help': 'Show help message',
        '/clear': 'Clear conversation context',
        '/history': 'Show query history',
        '/exit': 'Exit interactive mode',
        '/quit': 'Exit interactive mode',
        '/verbose': 'Toggle verbose mode',
        '/citations': 'Toggle citation display',
    }
    
    def __init__(self, rag_system, options: Dict[str, Any], console: Console):
        """
        Initialize interactive session.
        
        Parameters
        ----------
        rag_system
            RAG system instance
        options : dict
            CLI options
        console : Console
            Rich console for output
        """
        self.rag = rag_system
        self.options = options
        self.console = console
        
        # Session state
        self.context: List[Dict[str, str]] = []
        self.history: List[Dict[str, Any]] = []
        self.running = True
        
        # Options
        self.verbose = options.get('verbose', False)
        self.show_citations = options.get('show_citations', True)
        self.track_metrics = options.get('track_metrics', True)
        
        # Set up prompt session
        history_file = Path.home() / '.egeria_advisor_history'
        self.prompt_session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self._create_completer(),
        )
        
        # Formatter
        self.formatter = ResponseFormatter(
            format_type='text',
            show_citations=self.show_citations,
            verbose=self.verbose
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
        try:
            while self.running:
                try:
                    # Get user input
                    user_input = self.prompt_session.prompt('egeria> ')
                    
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
            self.context.clear()
            self.console.print("[green]✓[/green] Conversation context cleared")
        
        elif cmd == '/history':
            self._show_history()
        
        elif cmd == '/verbose':
            self.verbose = not self.verbose
            self.formatter.verbose = self.verbose
            status = "enabled" if self.verbose else "disabled"
            self.console.print(f"[green]✓[/green] Verbose mode {status}")
        
        elif cmd == '/citations':
            self.show_citations = not self.show_citations
            self.formatter.show_citations = self.show_citations
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
                # Build context from recent history
                context_str = self._build_context()
                
                # Execute query
                result = self.rag.query(
                    user_query=query,
                    include_context=True,
                    track_metrics=self.track_metrics
                )
                
                # Add to history
                self.history.append({
                    'query': query,
                    'response': result.get('response', ''),
                    'sources': result.get('sources', [])
                })
                
                # Update context
                self.context.append({
                    'query': query,
                    'response': result.get('response', '')
                })
                
                # Keep only last 5 exchanges
                if len(self.context) > 5:
                    self.context = self.context[-5:]
                
                # Display result
                self.formatter.display(result, self.console)
            
            except Exception as e:
                self.console.print(f"[red]✗ Error:[/red] {e}")
                if self.verbose:
                    self.console.print_exception()
    
    def _build_context(self) -> Optional[str]:
        """
        Build context string from recent conversation.
        
        Returns
        -------
        str or None
            Context string or None if no context
        """
        if not self.context:
            return None
        
        context_parts = []
        for exchange in self.context[-3:]:  # Last 3 exchanges
            context_parts.append(f"Q: {exchange['query']}")
            context_parts.append(f"A: {exchange['response'][:200]}...")  # Truncate
        
        return "\n".join(context_parts)
    
    def _show_help(self):
        """Show help message."""
        help_text = "[bold cyan]Available Commands:[/bold cyan]\n\n"
        
        for cmd, desc in self.COMMANDS.items():
            help_text += f"  [cyan]{cmd:12}[/cyan] - {desc}\n"
        
        help_text += "\n[bold cyan]Tips:[/bold cyan]\n"
        help_text += "  • Ask questions in natural language\n"
        help_text += "  • Request code examples: 'Show me how to create a glossary'\n"
        help_text += "  • Context is preserved across queries in the session\n"
        help_text += "  • Use arrow keys to navigate history\n"
        
        self.console.print(Panel(help_text, border_style="cyan", padding=(1, 2)))
    
    def _show_history(self):
        """Show query history."""
        if not self.history:
            self.console.print("[dim]No queries in history[/dim]")
            return
        
        self.console.print("[bold cyan]Query History:[/bold cyan]\n")
        
        for i, entry in enumerate(self.history[-10:], 1):  # Last 10 queries
            query = entry['query']
            num_sources = len(entry.get('sources', []))
            
            self.console.print(f"  [cyan]{i}.[/cyan] {query}")
            if self.verbose:
                self.console.print(f"     [dim]({num_sources} sources)[/dim]")
    
    def _cleanup(self):
        """Clean up session resources."""
        # Save any session data if needed
        pass


class SessionManager:
    """Manage session state and persistence."""
    
    def __init__(self, session_file: Optional[Path] = None):
        """
        Initialize session manager.
        
        Parameters
        ----------
        session_file : Path, optional
            Path to session file
        """
        if session_file is None:
            session_file = Path.home() / '.egeria_advisor_session.json'
        
        self.session_file = session_file
        self.session_data = {}
    
    def save_session(self, context: List[Dict], history: List[Dict]):
        """
        Save session to file.
        
        Parameters
        ----------
        context : list
            Conversation context
        history : list
            Query history
        """
        import json
        
        self.session_data = {
            'context': context,
            'history': history
        }
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception:
            pass  # Silently fail if can't save
    
    def load_session(self) -> Dict[str, List]:
        """
        Load session from file.
        
        Returns
        -------
        dict
            Session data with 'context' and 'history' keys
        """
        import json
        
        if not self.session_file.exists():
            return {'context': [], 'history': []}
        
        try:
            with open(self.session_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {'context': [], 'history': []}