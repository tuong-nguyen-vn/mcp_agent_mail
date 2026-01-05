"""Allow `python -m mcp_agent_mail` to invoke the CLI entry-point."""

from .cli import app


def main() -> None:
    """Dispatch to the Typer CLI entry-point."""
    app()


if __name__ == "__main__":  # pragma: no cover - manual execution path
    main()
