# MCP Agent Mail CLI Installation Guide

## Quick Start

Sau khi cài đặt, bạn có thể gọi CLI từ bất kỳ đâu với lệnh `am` hoặc `mcp-agent-mail`.

## Cài đặt Global

### Cách 1: Symlink (Khuyên dùng)

```bash
sudo ln -sf /Users/tuongnguyen/Workspaces/tool/mcp_agent_mail/.venv/bin/am /usr/local/bin/am
sudo ln -sf /Users/tuongnguyen/Workspaces/tool/mcp_agent_mail/.venv/bin/mcp-agent-mail /usr/local/bin/mcp-agent-mail
```

### Cách 2: Thêm vào PATH (Không cần sudo)

Thêm vào `~/.zshrc` hoặc `~/.bashrc`:

```bash
echo 'export PATH="/Users/tuongnguyen/Workspaces/tool/mcp_agent_mail/.venv/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Kiểm tra cài đặt

```bash
am --help
```

## Sử dụng CLI

### Các lệnh cơ bản

```bash
# Xem tất cả commands
am --help

# Health check
am health_check '{}'

# Ensure project
am ensure_project '{"human_key": "/path/to/project"}'

# Register agent
am register_agent '{"project_key": "/path/to/project", "program": "amp", "model": "claude-sonnet-4", "task_description": "My task"}'

# Send message
am send_message '{"project_key": "/path/to/project", "sender_name": "BlueLake", "to": ["GreenCastle"], "subject": "Hello", "body_md": "Message content"}'

# Fetch inbox
am fetch_inbox '{"project_key": "/path/to/project", "agent_name": "BlueLake", "include_bodies": true}'

# Search messages
am search_messages '{"project_key": "/path/to/project", "query": "keyword", "limit": 10}'

# Summarize thread
am summarize_thread '{"project_key": "/path/to/project", "thread_id": "thread-123"}'

# File reservations
am file_reservation_paths '{"project_key": "/path/to/project", "agent_name": "BlueLake", "paths": ["src/**"], "ttl_seconds": 3600, "exclusive": true, "reason": "working on feature"}'

# Release reservations
am release_file_reservations '{"project_key": "/path/to/project", "agent_name": "BlueLake"}'
```

### Orchestrator Workflow Example

```bash
# 1. Setup project
am ensure_project '{"human_key": "/path/to/project"}'

# 2. Register orchestrator
am register_agent '{"project_key": "/path/to/project", "name": "Orchestrator", "program": "amp", "model": "claude-sonnet-4", "task_description": "Epic orchestration"}'

# 3. Reserve files before editing
am file_reservation_paths '{"project_key": "/path/to/project", "agent_name": "BlueLake", "paths": ["src/**"], "ttl_seconds": 3600, "exclusive": true, "reason": "bd-123"}'

# 4. Send progress update
am send_message '{"project_key": "/path/to/project", "sender_name": "BlueLake", "to": ["Orchestrator"], "thread_id": "epic-001", "subject": "[bd-123] COMPLETE", "body_md": "Done with task"}'

# 5. Check inbox for blockers
am fetch_inbox '{"project_key": "/path/to/project", "agent_name": "Orchestrator", "urgent_only": true, "include_bodies": true}'

# 6. Release when done
am release_file_reservations '{"project_key": "/path/to/project", "agent_name": "BlueLake"}'
```

## Output Options

```bash
# Pretty print (default)
am fetch_inbox '{"project_key": "/path", "agent_name": "Agent"}' --pretty

# Raw JSON (for piping)
am fetch_inbox '{"project_key": "/path", "agent_name": "Agent"}' --no-pretty

# Suppress logs, only show result
am search_messages '{"project_key": "/path", "query": "test"}' 2>/dev/null
```

## Troubleshooting

### Command not found

Đảm bảo đã chạy một trong các cách cài đặt ở trên và restart terminal.

### Python version error

Package yêu cầu Python >= 3.14. Đảm bảo venv được tạo với Python 3.14+.

### Database errors

Chạy server một lần để khởi tạo database:
```bash
am serve-http
```
