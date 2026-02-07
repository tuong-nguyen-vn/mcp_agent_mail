#!/usr/bin/env bash
# E2E test: Orchestrator + Worker skill flow via `am` CLI
# Simulates a mini epic with 1 orchestrator (GoldFox) and 2 workers (BlueLake, RedStone)
#
# Usage: bash tests/e2e_skill_flow_test.sh
set -euo pipefail

PROJECT="/home/canhnguyen/WORKSPACES/AI/mcp_agent_mail"
EPIC="test-epic-001"
PASS=0; FAIL=0; TOTAL=0

step() { echo -e "\n\033[1;36m━━━ Step $1: $2 ━━━\033[0m"; }
ok()   { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo -e "\033[1;32m  ✓ $1\033[0m"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo -e "\033[1;31m  ✗ $1\033[0m"; }
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label"; fi
}

run() {
  local label="$1"; shift
  echo -e "\033[0;33m  → $*\033[0m"
  local out
  if out=$("$@" 2>&1); then
    ok "$label"
    echo "$out"
    return 0
  else
    fail "$label (exit $?)"
    echo "$out"
    return 1
  fi
}

# ─────────────────────────────────────────────
# PHASE 1 — PROJECT SETUP (Orchestrator)
# ─────────────────────────────────────────────
step 1 "ensure_project"
run "ensure_project" \
  am tool call ensure_project "{\"human_key\": \"$PROJECT\"}"

# ─────────────────────────────────────────────
# PHASE 2 — REGISTER AGENTS
# ─────────────────────────────────────────────
step 2a "register_agent — Orchestrator (GoldFox)"
run "register GoldFox" \
  am tool call register_agent "{\"project_key\": \"$PROJECT\", \"name\": \"GoldFox\", \"program\": \"amp\", \"model\": \"claude-sonnet-4\", \"task_description\": \"Orchestrator for $EPIC\"}"

step 2b "register_agent — Worker BlueLake"
run "register BlueLake" \
  am tool call register_agent "{\"project_key\": \"$PROJECT\", \"name\": \"BlueLake\", \"program\": \"amp\", \"model\": \"claude-sonnet-4\", \"task_description\": \"Track 1: backend work\"}"

step 2c "register_agent — Worker RedStone"
run "register RedStone" \
  am tool call register_agent "{\"project_key\": \"$PROJECT\", \"name\": \"RedStone\", \"program\": \"amp\", \"model\": \"claude-sonnet-4\", \"task_description\": \"Track 2: frontend work\"}"

# ─────────────────────────────────────────────
# PHASE 3 — CONTACT HANDSHAKES
# ─────────────────────────────────────────────
step 3a "macro_contact_handshake — GoldFox ↔ BlueLake"
run "handshake GoldFox↔BlueLake" \
  am tool call macro_contact_handshake "{\"project_key\": \"$PROJECT\", \"requester\": \"GoldFox\", \"target\": \"BlueLake\", \"auto_accept\": true}"

step 3b "macro_contact_handshake — GoldFox ↔ RedStone"
run "handshake GoldFox↔RedStone" \
  am tool call macro_contact_handshake "{\"project_key\": \"$PROJECT\", \"requester\": \"GoldFox\", \"target\": \"RedStone\", \"auto_accept\": true}"

step 3c "macro_contact_handshake — BlueLake ↔ RedStone (cross-worker)"
run "handshake BlueLake↔RedStone" \
  am tool call macro_contact_handshake "{\"project_key\": \"$PROJECT\", \"requester\": \"BlueLake\", \"target\": \"RedStone\", \"auto_accept\": true}"

# ─────────────────────────────────────────────
# PHASE 4 — WORKER BlueLake: BEAD LIFECYCLE
# ─────────────────────────────────────────────
step 4a "file_reservation_paths — BlueLake reserves src/mcp_agent_mail/llm.py"
run "BlueLake reserve files" \
  am tool call file_reservation_paths "{\"project_key\": \"$PROJECT\", \"agent_name\": \"BlueLake\", \"paths\": [\"src/mcp_agent_mail/llm.py\"], \"ttl_seconds\": 3600, \"exclusive\": true, \"reason\": \"$EPIC-bead-1\"}"

step 4b "send_message — BlueLake announces bead start to GoldFox"
run "BlueLake → GoldFox: bead start" \
  am tool call send_message "{\"project_key\": \"$PROJECT\", \"sender_name\": \"BlueLake\", \"to\": [\"GoldFox\"], \"thread_id\": \"$EPIC\", \"subject\": \"[$EPIC-bead-1] START: Refactor llm module\", \"body_md\": \"Starting work on llm.py lazy imports.\", \"importance\": \"normal\"}"

step 4c "send_message — BlueLake saves context to track thread (self-addressed)"
run "BlueLake → BlueLake: track context" \
  am tool call send_message "{\"project_key\": \"$PROJECT\", \"sender_name\": \"BlueLake\", \"to\": [\"BlueLake\"], \"thread_id\": \"track:BlueLake:$EPIC\", \"subject\": \"$EPIC-bead-1 Context\", \"body_md\": \"## Learnings\\n- litellm takes 11s to import\\n- Use _get_litellm() lazy helper\\n## Files Changed\\n- src/mcp_agent_mail/llm.py\"}"

step 4d "send_message — BlueLake reports bead complete to GoldFox"
run "BlueLake → GoldFox: bead complete" \
  am tool call send_message "{\"project_key\": \"$PROJECT\", \"sender_name\": \"BlueLake\", \"to\": [\"GoldFox\"], \"thread_id\": \"$EPIC\", \"subject\": \"[$EPIC-bead-1] COMPLETE\", \"body_md\": \"Done: Refactored llm.py with lazy litellm import. Startup reduced by ~11s.\"}"

step 4e "release_file_reservations — BlueLake releases files"
run "BlueLake release" \
  am tool call release_file_reservations "{\"project_key\": \"$PROJECT\", \"agent_name\": \"BlueLake\"}"

# ─────────────────────────────────────────────
# PHASE 5 — WORKER RedStone: BEAD LIFECYCLE
# ─────────────────────────────────────────────
step 5a "file_reservation_paths — RedStone reserves src/mcp_agent_mail/cli.py"
run "RedStone reserve files" \
  am tool call file_reservation_paths "{\"project_key\": \"$PROJECT\", \"agent_name\": \"RedStone\", \"paths\": [\"src/mcp_agent_mail/cli.py\"], \"ttl_seconds\": 3600, \"exclusive\": true, \"reason\": \"$EPIC-bead-2\"}"

step 5b "send_message — RedStone announces bead start"
run "RedStone → GoldFox: bead start" \
  am tool call send_message "{\"project_key\": \"$PROJECT\", \"sender_name\": \"RedStone\", \"to\": [\"GoldFox\"], \"thread_id\": \"$EPIC\", \"subject\": \"[$EPIC-bead-2] START: Fix CLI lazy loading\", \"body_md\": \"Starting work on cli.py import cleanup.\"}"

step 5c "send_message — RedStone reports blocker to GoldFox"
run "RedStone → GoldFox: BLOCKER" \
  am tool call send_message "{\"project_key\": \"$PROJECT\", \"sender_name\": \"RedStone\", \"to\": [\"GoldFox\"], \"thread_id\": \"$EPIC\", \"subject\": \"[$EPIC-bead-2] BLOCKER: Need app.py change\", \"body_md\": \"## Blocker\\nNeed _sanitize_fts_query moved to a shared util. Requires BlueLake to modify app.py.\", \"importance\": \"high\"}"

# ─────────────────────────────────────────────
# PHASE 6 — ORCHESTRATOR: MONITOR & RESPOND
# ─────────────────────────────────────────────
step 6a "fetch_inbox — GoldFox checks inbox (urgent only)"
run "GoldFox inbox (urgent)" \
  am tool call fetch_inbox "{\"project_key\": \"$PROJECT\", \"agent_name\": \"GoldFox\", \"urgent_only\": true, \"include_bodies\": true}"

step 6b "fetch_inbox — GoldFox checks full inbox"
run "GoldFox inbox (all)" \
  am tool call fetch_inbox "{\"project_key\": \"$PROJECT\", \"agent_name\": \"GoldFox\", \"include_bodies\": true, \"limit\": 20}"

step 6c "search_messages — GoldFox searches epic thread"
run "GoldFox search epic" \
  am tool call search_messages "{\"project_key\": \"$PROJECT\", \"query\": \"$EPIC\", \"limit\": 20}"

step 6d "reply_message — GoldFox resolves blocker"
# First find the blocker message ID from search results
BLOCKER_MSG=$(am tool call search_messages "{\"project_key\": \"$PROJECT\", \"query\": \"BLOCKER\", \"limit\": 1}" 2>&1 | grep -o '"id": "[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$BLOCKER_MSG" ]; then
  run "GoldFox → RedStone: resolve blocker" \
    am tool call reply_message "{\"project_key\": \"$PROJECT\", \"message_id\": \"$BLOCKER_MSG\", \"sender_name\": \"GoldFox\", \"body_md\": \"Resolution: BlueLake will extract _sanitize_fts_query to utils. Proceed with other work.\"}"
else
  echo "  (skipping reply_message — could not extract blocker message ID)"
  fail "reply_message — no message ID found"
fi

# ─────────────────────────────────────────────
# PHASE 7 — WORKER BlueLake: READ TRACK CONTEXT
# ─────────────────────────────────────────────
step 7a "summarize_thread — BlueLake reads track context"
run "BlueLake summarize track" \
  am tool call summarize_thread "{\"project_key\": \"$PROJECT\", \"thread_id\": \"track:BlueLake:$EPIC\"}"

step 7b "acknowledge_message — BlueLake ACKs messages"
# Get first unacked message for BlueLake
BLUELAKE_MSG=$(am tool call fetch_inbox "{\"project_key\": \"$PROJECT\", \"agent_name\": \"BlueLake\", \"limit\": 1}" 2>&1 | grep -o '"id": "[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$BLUELAKE_MSG" ]; then
  run "BlueLake ACK" \
    am tool call acknowledge_message "{\"project_key\": \"$PROJECT\", \"message_id\": \"$BLUELAKE_MSG\", \"agent_name\": \"BlueLake\"}"
else
  echo "  (no messages to ACK for BlueLake)"
  ok "acknowledge_message — no pending messages (OK)"
fi

# ─────────────────────────────────────────────
# PHASE 8 — WORKER RedStone: COMPLETE & RELEASE
# ─────────────────────────────────────────────
step 8a "send_message — RedStone completes bead"
run "RedStone → GoldFox: bead complete" \
  am tool call send_message "{\"project_key\": \"$PROJECT\", \"sender_name\": \"RedStone\", \"to\": [\"GoldFox\"], \"thread_id\": \"$EPIC\", \"subject\": \"[$EPIC-bead-2] COMPLETE\", \"body_md\": \"Done: Removed eager _sanitize_fts_query import and _register_mcp_tool_commands() call from cli.py.\"}"

step 8b "release_file_reservations — RedStone releases"
run "RedStone release" \
  am tool call release_file_reservations "{\"project_key\": \"$PROJECT\", \"agent_name\": \"RedStone\"}"

# ─────────────────────────────────────────────
# PHASE 9 — FILE RESERVATION CONFLICT TEST
# ─────────────────────────────────────────────
step 9a "file_reservation_paths — BlueLake reserves src/mcp_agent_mail/app.py"
run "BlueLake reserve app.py" \
  am tool call file_reservation_paths "{\"project_key\": \"$PROJECT\", \"agent_name\": \"BlueLake\", \"paths\": [\"src/mcp_agent_mail/app.py\"], \"ttl_seconds\": 3600, \"exclusive\": true, \"reason\": \"$EPIC-bead-3\"}"

step 9b "file_reservation_paths — RedStone tries same file (expect CONFLICT)"
echo -e "\033[0;33m  → Expecting conflict...\033[0m"
CONFLICT_OUT=$(am tool call file_reservation_paths "{\"project_key\": \"$PROJECT\", \"agent_name\": \"RedStone\", \"paths\": [\"src/mcp_agent_mail/app.py\"], \"ttl_seconds\": 3600, \"exclusive\": true, \"reason\": \"$EPIC-bead-4\"}" 2>&1) || true
if echo "$CONFLICT_OUT" | grep -qi "conflict\|error\|denied\|reserved"; then
  ok "Conflict correctly detected"
  echo "$CONFLICT_OUT" | head -5
else
  fail "No conflict detected — reservation should have been denied"
  echo "$CONFLICT_OUT" | head -5
fi

step 9c "release — BlueLake releases app.py"
run "BlueLake release app.py" \
  am tool call release_file_reservations "{\"project_key\": \"$PROJECT\", \"agent_name\": \"BlueLake\"}"

# ─────────────────────────────────────────────
# PHASE 10 — ORCHESTRATOR: EPIC COMPLETION
# ─────────────────────────────────────────────
step 10a "send_message — GoldFox announces epic complete"
run "GoldFox → all: EPIC COMPLETE" \
  am tool call send_message "{\"project_key\": \"$PROJECT\", \"sender_name\": \"GoldFox\", \"to\": [\"BlueLake\", \"RedStone\"], \"thread_id\": \"$EPIC\", \"subject\": \"[$EPIC] EPIC COMPLETE\", \"body_md\": \"## Epic Complete: CLI Performance Fix\\n\\n### Track Summaries\\n- Track 1 (BlueLake): Refactored llm.py lazy imports (-11s)\\n- Track 2 (RedStone): Cleaned cli.py imports (-16s)\\n\\n### Result\\nCLI startup: 37s → 4.5s\"}"

step 10b "summarize_thread — GoldFox summarizes epic thread"
run "GoldFox summarize epic" \
  am tool call summarize_thread "{\"project_key\": \"$PROJECT\", \"thread_id\": \"$EPIC\"}"

step 10c "list_contacts — GoldFox checks contacts"
run "GoldFox list contacts" \
  am tool call list_contacts "{\"project_key\": \"$PROJECT\", \"agent_name\": \"GoldFox\"}"

step 10d "whois — check BlueLake profile"
run "whois BlueLake" \
  am tool call whois "{\"project_key\": \"$PROJECT\", \"agent_name\": \"BlueLake\"}"

# ─────────────────────────────────────────────
# PHASE 11 — MACRO TOOLS
# ─────────────────────────────────────────────
step 11a "macro_start_session — new agent SilverWolf"
run "macro_start_session SilverWolf" \
  am tool call macro_start_session "{\"project_key\": \"$PROJECT\", \"agent_name\": \"SilverWolf\", \"program\": \"amp\", \"model\": \"claude-sonnet-4\", \"task_description\": \"Test macro session\"}"

step 11b "macro_prepare_thread — SilverWolf joins epic thread"
run "macro_prepare_thread SilverWolf" \
  am tool call macro_prepare_thread "{\"project_key\": \"$PROJECT\", \"agent_name\": \"SilverWolf\", \"thread_id\": \"$EPIC\"}"

step 11c "macro_file_reservation_cycle — SilverWolf reserve+release"
run "macro_file_reservation_cycle" \
  am tool call macro_file_reservation_cycle "{\"project_key\": \"$PROJECT\", \"agent_name\": \"SilverWolf\", \"paths\": [\"tests/**\"], \"ttl_seconds\": 60, \"exclusive\": false, \"reason\": \"test-cycle\", \"release_immediately\": true}"

# ─────────────────────────────────────────────
# PHASE 12 — HEALTH & MISC
# ─────────────────────────────────────────────
step 12a "health_check"
run "health_check" \
  am tool call health_check '{}'

step 12b "mark_message_read"
SOME_MSG=$(am tool call fetch_inbox "{\"project_key\": \"$PROJECT\", \"agent_name\": \"RedStone\", \"limit\": 1}" 2>&1 | grep -o '"id": "[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$SOME_MSG" ]; then
  run "mark_message_read" \
    am tool call mark_message_read "{\"project_key\": \"$PROJECT\", \"message_id\": \"$SOME_MSG\", \"agent_name\": \"RedStone\"}"
else
  ok "mark_message_read — no messages to mark"
fi

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
echo ""
echo -e "\033[1;35m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "\033[1;35m  E2E SKILL FLOW TEST RESULTS\033[0m"
echo -e "\033[1;35m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "  Total: $TOTAL  |  \033[1;32mPass: $PASS\033[0m  |  \033[1;31mFail: $FAIL\033[0m"
if [ "$FAIL" -eq 0 ]; then
  echo -e "\033[1;32m  ✓ ALL TESTS PASSED\033[0m"
else
  echo -e "\033[1;31m  ✗ SOME TESTS FAILED\033[0m"
fi
echo -e "\033[1;35m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
exit $FAIL
