"""Top-level package for the MCP Agent Mail server."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, cast

# Python 3.14 warns when third-party code calls asyncio.iscoroutinefunction.
# Patch it globally to the inspect implementation before importing submodules.
asyncio.iscoroutinefunction = cast(Any, inspect.iscoroutinefunction)


def __getattr__(name: str) -> Any:
    """Lazy import heavy modules to speed up CLI startup time."""
    if name == "build_mcp_server":
        import importlib

        _app_module = cast(Any, importlib.import_module(".app", __name__))
        return _app_module.build_mcp_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["build_mcp_server"]
