# MCP Agent Mail

![Agent Mail Showcase](screenshots/output/agent_mail_showcase.gif)

> "It's like Gmail for your coding agents!"

A mail-like coordination layer for coding agents via MCP. Provides identities, inbox/outbox, searchable threads, and file reservations to prevent conflicts.

## Features

- **Agent Identity** - Memorable names (e.g., GreenCastle, BlueMountain)
- **Messaging** - Send/receive Markdown messages with attachments
- **File Reservations** - Advisory leases to avoid edit conflicts
- **Search & Threads** - Searchable message history with threading
- **Git-backed** - Human-auditable artifacts

## Installation

### Requirements

- Python >= 3.14
- uv (package manager)
- Git

### Install

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/Dicklesworthstone/mcp_agent_mail
cd mcp_agent_mail

# Create venv and install
uv venv --python python3.14
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
```

### Verify Installation

```bash
am --help
# or
mcp-agent-mail --help
```

### Global CLI Access (Optional)

```bash
# Option 1: Symlink
sudo ln -sf $(pwd)/.venv/bin/am /usr/local/bin/am

# Option 2: Add to PATH in ~/.zshrc or ~/.bashrc
export PATH="/path/to/mcp_agent_mail/.venv/bin:$PATH"
```

## Usage

### Start Server

```bash
am                    # Uses alias (after install)
am serve-http         # Or directly
```

### CLI Commands

```bash
# Health check
am health_check '{}'

# Register project and agent
am ensure_project '{"human_key": "/path/to/project"}'
am register_agent '{"project_key": "/path/to/project", "program": "amp", "model": "claude-sonnet-4", "task_description": "My task"}'

# Send message
am send_message '{"project_key": "/path/to/project", "sender_name": "BlueLake", "to": ["GreenCastle"], "subject": "Hello", "body_md": "Content"}'

# Check inbox
am fetch_inbox '{"project_key": "/path/to/project", "agent_name": "BlueLake"}'

# File reservations
am file_reservation_paths '{"project_key": "/path/to/project", "agent_name": "BlueLake", "paths": ["src/**"], "ttl_seconds": 3600, "exclusive": true}'
```

## Configuration

Config location: `~/.mcp_agent_mail/.env`

```bash
HTTP_HOST=127.0.0.1
HTTP_PORT=8765
HTTP_BEARER_TOKEN=your-secret-token
```

## Integrations

Works with: Claude Code, Codex CLI, Gemini CLI, Cursor, Windsurf, and other MCP-compatible tools.

Auto-detect and configure:
```bash
scripts/automatically_detect_all_installed_coding_agents_and_install_mcp_agent_mail_in_all.sh
```

## Documentation

- [CLI Installation Guide](docs/CLI_INSTALLATION.md)
- [Project Guide](project_idea_and_guide.md)
- [Beads Integration](https://github.com/steveyegge/beads)

## License

MIT
