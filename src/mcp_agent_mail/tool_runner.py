"""Run MCP tools directly from CLI without requiring a server.

This module provides a bridge between the CLI and MCP tools, allowing
tools like ensure_project, register_agent, send_message etc. to be
invoked directly via command line.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from rich.console import Console

console = Console()

# Cache for the MCP server instance
_mcp_server: Any = None


def _get_mcp_server() -> Any:
    """Get or create the MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        from .app import build_mcp_server
        _mcp_server = build_mcp_server()
    return _mcp_server


async def _run_tool_async(tool_name: str, arguments: dict[str, Any]) -> Any:
    """Run an MCP tool asynchronously.

    Args:
        tool_name: Name of the MCP tool to invoke
        arguments: Dictionary of arguments to pass to the tool

    Returns:
        The tool's return value

    Raises:
        ValueError: If tool not found
        Exception: Any exception raised by the tool
    """
    from .db import ensure_schema

    # Ensure database schema exists
    await ensure_schema()

    mcp = _get_mcp_server()

    # Get all registered tools
    tools = mcp._tool_manager._tools if hasattr(mcp, '_tool_manager') else {}

    if tool_name not in tools:
        available = list(tools.keys())
        raise ValueError(
            f"Tool '{tool_name}' not found. Available tools: {', '.join(sorted(available)[:20])}..."
        )

    tool = tools[tool_name]

    # Create a minimal context object for tools that need it
    class MinimalContext:
        """Minimal context for CLI tool invocation."""

        async def info(self, message: str) -> None:
            """Log info message."""
            console.print(f"[dim]{message}[/dim]")

        async def debug(self, message: str) -> None:
            """Log debug message."""
            pass

        async def warning(self, message: str) -> None:
            """Log warning message."""
            console.print(f"[yellow]{message}[/yellow]")

        async def error(self, message: str) -> None:
            """Log error message."""
            console.print(f"[red]{message}[/red]")

    ctx = MinimalContext()

    # Call the tool's function directly
    # The function is stored in tool.fn
    fn = tool.fn

    # Inject ctx as first argument if the function expects it
    import inspect
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())

    if params and params[0] == 'ctx':
        result = await fn(ctx, **arguments)
    else:
        result = await fn(**arguments)

    return result


def run_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    """Run an MCP tool synchronously.

    This is the main entry point for CLI commands to invoke MCP tools.

    Args:
        tool_name: Name of the MCP tool to invoke
        arguments: Dictionary of arguments to pass to the tool

    Returns:
        The tool's return value
    """
    return asyncio.run(_run_tool_async(tool_name, arguments))


def run_mcp_tool_json(tool_name: str, json_args: str) -> Any:
    """Run an MCP tool with JSON-encoded arguments.

    Args:
        tool_name: Name of the MCP tool to invoke
        json_args: JSON string of arguments

    Returns:
        The tool's return value
    """
    try:
        arguments = json.loads(json_args) if json_args else {}
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON arguments: {e}") from e

    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a JSON object (dict)")

    return run_mcp_tool(tool_name, arguments)
