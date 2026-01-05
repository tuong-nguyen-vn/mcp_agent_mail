# MCP Agent Mail CLI Installation Guide

## Yêu cầu hệ thống

- **Python**: >= 3.14 (bắt buộc)
- **uv**: Package manager (khuyên dùng thay pip)
- **Git**: Để clone repo và lưu trữ Agent Mail data

## Cài đặt từ đầu

### 1. Cài đặt Python 3.14+

**macOS (Homebrew):**
```bash
brew install python@3.14
```

**Ubuntu/Debian:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.14 python3.14-venv
```

**Kiểm tra version:**
```bash
python3.14 --version
```

### 2. Cài đặt uv (Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Hoặc với Homebrew:
```bash
brew install uv
```

### 3. Clone repo và setup

```bash
# Clone repo
git clone https://github.com/Dicklesworthstone/mcp_agent_mail.git
cd mcp_agent_mail

# Tạo virtual environment với Python 3.14
uv venv --python python3.14

# Activate venv
source .venv/bin/activate  # Linux/macOS
# hoặc
.venv\Scripts\activate     # Windows

# Cài dependencies
uv pip install -e .

# Cài dev dependencies (optional)
uv pip install -e ".[dev]"
```

### 4. Kiểm tra cài đặt

```bash
# Trong venv
python -m mcp_agent_mail --help

# Hoặc dùng alias
am --help
mcp-agent-mail --help
```

---

## Cài đặt Global (gọi từ bất kỳ đâu)

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

### Cách 3: Alias trong shell config

Thêm vào `~/.zshrc` hoặc `~/.bashrc`:

```bash
alias am='/Users/tuongnguyen/Workspaces/tool/mcp_agent_mail/.venv/bin/am'
alias mcp-agent-mail='/Users/tuongnguyen/Workspaces/tool/mcp_agent_mail/.venv/bin/mcp-agent-mail'
```

Sau đó:
```bash
source ~/.zshrc
```

---

## Cấu hình

### File .env

MCP Agent Mail lưu config tại `~/.mcp_agent_mail/.env` (KHÔNG phải trong thư mục project).

Điều này đảm bảo khi chạy `am` trong bất kỳ dự án nào, nó không bị conflict với `.env` của dự án đó.

```bash
# Tạo thư mục config
mkdir -p ~/.mcp_agent_mail

# Copy file example
cp .env.example ~/.mcp_agent_mail/.env

# Hoặc tạo mới
nano ~/.mcp_agent_mail/.env
```

Các biến quan trọng:

```bash
# Database (mặc định: ~/.mcp_agent_mail/storage.sqlite3)
# DATABASE_URL=sqlite+aiosqlite:///path/to/custom.sqlite3

# HTTP Server
HTTP_HOST=127.0.0.1
HTTP_PORT=8765
HTTP_PATH=/mcp

# Authentication (optional)
HTTP_BEARER_TOKEN=your-secret-token

# Logging
TOOLS_LOG_ENABLED=true
```

### Vị trí lưu trữ data

| Data | Đường dẫn mặc định |
|------|-------------------|
| Config `.env` | `~/.mcp_agent_mail/.env` |
| Database | `~/.mcp_agent_mail/storage.sqlite3` |
| Git mailbox | `~/.mcp_agent_mail_git_mailbox_repo/` |

### Khởi tạo database

Database được tạo tự động khi chạy lệnh đầu tiên:

```bash
am health_check '{}'
```

Hoặc chạy server:
```bash
am serve-http
```

---

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

---

## Output Options

```bash
# Pretty print (default)
am fetch_inbox '{"project_key": "/path", "agent_name": "Agent"}' --pretty

# Raw JSON (for piping)
am fetch_inbox '{"project_key": "/path", "agent_name": "Agent"}' --no-pretty

# Suppress logs, only show result
am search_messages '{"project_key": "/path", "query": "test"}' 2>/dev/null
```

---

## Chạy HTTP Server

Nếu cần dùng MCP qua HTTP thay vì CLI:

```bash
# Default settings
am serve-http

# Custom host/port
am serve-http --host 0.0.0.0 --port 9000
```

Server sẽ chạy tại `http://127.0.0.1:8765/mcp` (mặc định).

---

## Troubleshooting

### Command not found

Đảm bảo đã chạy một trong các cách cài đặt global ở trên và restart terminal.

### Python version error

```
ERROR: Package 'mcp-agent-mail' requires a different Python: 3.13.x not in '>=3.14'
```

Package yêu cầu Python >= 3.14. Cài Python 3.14+ và tạo lại venv:

```bash
uv venv --python python3.14
source .venv/bin/activate
uv pip install -e .
```

### Database errors

Chạy health check để khởi tạo database:
```bash
am health_check '{}'
```

### Permission denied (symlink)

Dùng sudo hoặc chọn cách 2/3 (PATH hoặc alias) không cần sudo.

### Import errors

Đảm bảo đang ở trong venv:
```bash
source /path/to/mcp_agent_mail/.venv/bin/activate
which python  # Phải trỏ đến .venv/bin/python
```

---

## Cập nhật

```bash
cd /path/to/mcp_agent_mail
git pull
source .venv/bin/activate
uv pip install -e .
```

---

## Gỡ cài đặt

### Xóa symlinks
```bash
sudo rm /usr/local/bin/am /usr/local/bin/mcp-agent-mail
```

### Xóa khỏi PATH
Sửa `~/.zshrc` hoặc `~/.bashrc`, xóa dòng export PATH.

### Xóa data và config
```bash
rm -rf ~/.mcp_agent_mail
rm -rf ~/.mcp_agent_mail_git_mailbox_repo
```

### Xóa toàn bộ source code
```bash
rm -rf /path/to/mcp_agent_mail
```
