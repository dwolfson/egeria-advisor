"""
Agent Interactive Session for Egeria Advisor

This module provides an interactive session using the ConversationAgent.
"""

import sys
import json
import asyncio
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
from advisor.mcp_agent import initialize_mcp_agent, shutdown_mcp_agent, get_mcp_agent
from advisor.mcp_client import MCPTool


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
        '/tools': 'List available MCP tools',
        '/execute': 'Execute an MCP tool',
        '/exec': 'Execute an MCP tool (alias)',
        '/e': 'Execute an MCP tool (short alias)',
        '/metrics': 'Show MCP tool metrics',
        '/clear-cache': 'Clear MCP tool cache',
        '/cc': 'Clear MCP tool cache (alias)',
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
        self.mcp_enabled = options.get('enable_mcp', True)
        
        # Initialize agents
        self.agent = None
        self.mcp_agent = None
        
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
        # Initialize conversation agent
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
        
        self.console.print("[green]✓[/green] Agent ready")
        
        # Initialize MCP agent (optional)
        if self.mcp_enabled:
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                    transient=True
                ) as progress:
                    progress.add_task("Initializing MCP tools...", total=None)
                    # Run async initialization in sync context
                    asyncio.run(self._init_mcp_agent())
                
                if self.mcp_agent:
                    tool_count = len(self.mcp_agent.get_available_tools())
                    self.console.print(f"[green]✓[/green] MCP tools ready ({tool_count} tools)")
            except Exception as e:
                self.console.print(f"[yellow]⚠ MCP tools unavailable:[/yellow] {e}")
                if self.verbose:
                    self.console.print_exception()
                self.mcp_agent = None
        
        self.console.print()  # Add spacing
        
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
        
        # MCP tool commands
        elif cmd == '/tools':
            self._show_tools()
        
        elif cmd in ['/execute', '/exec', '/e']:
            # Run async command in sync context
            asyncio.run(self._execute_tool(command))
        
        elif cmd == '/metrics':
            self._show_mcp_metrics()
        
        elif cmd in ['/clear-cache', '/cc']:
            if self.mcp_agent:
                self.mcp_agent.clear_cache()
                self.console.print("[green]✓[/green] MCP tool cache cleared")
            else:
                self.console.print("[yellow]MCP tools not available[/yellow]")
        
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
        
        help_text += "[bold]Conversation:[/bold]\n"
        help_text += "  [cyan]/help[/cyan]        - Show this help\n"
        help_text += "  [cyan]/clear[/cyan]       - Clear conversation history\n"
        help_text += "  [cyan]/history[/cyan]     - Show conversation history\n"
        help_text += "  [cyan]/stats[/cyan]       - Show agent statistics\n"
        help_text += "  [cyan]/verbose[/cyan]     - Toggle verbose mode\n"
        help_text += "  [cyan]/citations[/cyan]   - Toggle citation display\n"
        
        if self.mcp_agent:
            help_text += "\n[bold]MCP Tools:[/bold]\n"
            help_text += "  [cyan]/tools[/cyan]       - List available tools\n"
            help_text += "  [cyan]/execute[/cyan]     - Execute a tool (aliases: /exec, /e)\n"
            help_text += "  [cyan]/metrics[/cyan]     - Show tool metrics\n"
            help_text += "  [cyan]/clear-cache[/cyan] - Clear tool cache (alias: /cc)\n"
        
        help_text += "\n[bold]System:[/bold]\n"
        help_text += "  [cyan]/exit[/cyan]        - Exit (or Ctrl+D)\n"
        
        help_text += "\n[bold cyan]Agent Features:[/bold cyan]\n"
        help_text += "  • Conversational AI with memory\n"
        help_text += "  • RAG-enhanced responses with source citation\n"
        help_text += "  • Response caching for repeated queries\n"
        help_text += "  • Conversation history tracking\n"
        
        if self.mcp_agent:
            help_text += "  • MCP tool execution for reports and commands\n"
        
        help_text += "\n[bold cyan]Tips:[/bold cyan]\n"
        help_text += "  • Ask follow-up questions - context is preserved\n"
        help_text += "  • Request code examples: 'Show me how to create a glossary'\n"
        
        if self.mcp_agent:
            help_text += "  • Execute tools: '/execute list_reports'\n"
        
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
    def _show_tools(self):
        """Show available MCP tools."""
        if not self.mcp_agent:
            self.console.print("[yellow]MCP tools not available[/yellow]")
            return
        
        tools = self.mcp_agent.get_available_tools()
        
        if not tools:
            self.console.print("[dim]No MCP tools available[/dim]")
            return
        
        table = Table(title="Available MCP Tools", show_header=True, header_style="bold cyan")
        table.add_column("Tool", style="cyan")
        table.add_column("Description")
        table.add_column("Server", style="dim")
        
        for tool in tools:
            table.add_row(
                tool.name,
                tool.description or "No description",
                tool.server_name
            )
        
        self.console.print(table)
    
    async def _execute_tool(self, command: str):
        """Execute an MCP tool."""
        if not self.mcp_agent:
            self.console.print("[yellow]MCP tools not available[/yellow]")
            return
        
        # Parse command: /execute tool_name or /e tool_name
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            self.console.print("[yellow]Usage: /execute <tool_name>[/yellow]")
            self.console.print("[dim]Use /tools to see available tools[/dim]")
            return
        
        tool_name = parts[1].strip()
        
        # Get tool info
        tool = self.mcp_agent.get_tool(tool_name)
        if not tool:
            self.console.print(f"[red]Tool not found:[/red] {tool_name}")
            self.console.print("[dim]Use /tools to see available tools[/dim]")
            return
        
        # Get parameters interactively
        try:
            arguments = self._get_tool_arguments(tool)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Tool execution cancelled[/yellow]")
            return
        
        # Execute tool
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                progress.add_task(f"Executing {tool_name}...", total=None)
                result = await self.mcp_agent.execute_tool(tool_name, arguments)
            
            # Display result
            self._display_tool_result(result)
        
        except Exception as e:
            self.console.print(f"[red]✗ Tool execution failed:[/red] {e}")
            if self.verbose:
                self.console.print_exception()
    
    def _get_tool_arguments(self, tool: MCPTool) -> dict:
        """Get tool arguments from user input."""
        arguments = {}
        schema = tool.input_schema
        
        if not schema or 'properties' not in schema:
            return arguments
        
        properties = schema['properties']
        required = schema.get('required', [])
        
        self.console.print(f"\n[bold]Parameters for {tool.name}:[/bold]")
        
        for param_name, param_info in properties.items():
            param_type = param_info.get('type', 'string')
            description = param_info.get('description', '')
            default = param_info.get('default')
            enum_values = param_info.get('enum')
            
            # Show parameter info
            required_marker = "[red]*[/red]" if param_name in required else ""
            self.console.print(f"\n{required_marker} [cyan]{param_name}[/cyan] ({param_type})")
            
            if description:
                self.console.print(f"  [dim]{description}[/dim]")
            
            if enum_values:
                self.console.print(f"  [dim]Valid values: {', '.join(map(str, enum_values))}[/dim]")
            
            if default is not None:
                self.console.print(f"  [dim]Default: {default}[/dim]")
            
            # Get input
            prompt = f"  Value: "
            value = input(prompt).strip()
            
            # Use default if empty and not required
            if not value:
                if param_name in required:
                    self.console.print(f"[red]Error: {param_name} is required[/red]")
                    return self._get_tool_arguments(tool)  # Retry
                elif default is not None:
                    value = default
                else:
                    continue
            
            # Type conversion
            try:
                if param_type == 'integer':
                    value = int(value)
                elif param_type == 'number':
                    value = float(value)
                elif param_type == 'boolean':
                    value = value.lower() in ('true', 'yes', '1', 'y')
            except ValueError:
                self.console.print(f"[red]Invalid {param_type} value[/red]")
                return self._get_tool_arguments(tool)  # Retry
            
            arguments[param_name] = value
        
        return arguments
    
    def _display_tool_result(self, result):
        """Display tool execution result with pretty printing."""
        self.console.print("\n[bold green]✓ Tool Result:[/bold green]\n")
        
        # Handle MCP content format
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    content_type = item.get('type', 'text')
                    
                    if content_type == 'text':
                        text = item.get('text', '')
                        # Try to parse as JSON for pretty printing
                        try:
                            parsed = json.loads(text)
                            self.console.print(json.dumps(parsed, indent=2))
                        except:
                            # Display as-is (could be markdown)
                            self.console.print(text)
                    
                    elif content_type == 'image':
                        self.console.print(f"[dim]Image: {item.get('data', 'N/A')}[/dim]")
                    
                    elif content_type == 'resource':
                        self.console.print(f"[dim]Resource: {item.get('uri', 'N/A')}[/dim]")
        else:
            # Fallback for non-MCP format
            self.console.print(str(result))
    
    def _show_mcp_metrics(self):
        """Show MCP tool metrics."""
        if not self.mcp_agent:
            self.console.print("[yellow]MCP tools not available[/yellow]")
            return
        
        metrics = self.mcp_agent.get_metrics()
        
        table = Table(title="MCP Tool Metrics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Total Calls", str(metrics.get('total_calls', 0)))
        table.add_row("Successful Calls", str(metrics.get('successful_calls', 0)))
        table.add_row("Failed Calls", str(metrics.get('failed_calls', 0)))
        table.add_row("Success Rate", f"{metrics.get('success_rate', 0):.1%}")
        table.add_row("Cache Hits", str(metrics.get('cache_hits', 0)))
        table.add_row("Cache Misses", str(metrics.get('cache_misses', 0)))
        
        avg_time = metrics.get('avg_execution_time', 0)
        if avg_time > 0:
            table.add_row("Avg Execution Time", f"{avg_time:.2f}s")
        
        self.console.print(table)
    
    
    async def _init_mcp_agent(self):
        """Initialize MCP agent asynchronously."""
        try:
            self.mcp_agent = await initialize_mcp_agent()
        except Exception as e:
            if self.verbose:
                self.console.print(f"[dim]MCP initialization error: {e}[/dim]")
            self.mcp_agent = None
    
    def _cleanup(self):
        """Clean up session resources."""
        # Shutdown MCP agent if initialized
        if self.mcp_agent:
            try:
                asyncio.run(shutdown_mcp_agent())
            except Exception as e:
                if self.verbose:
                    self.console.print(f"[yellow]Warning: MCP shutdown error:[/yellow] {e}")