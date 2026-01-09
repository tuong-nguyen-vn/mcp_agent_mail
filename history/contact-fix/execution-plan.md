# Execution Plan: Fix Contact Approval Auto-Handshake Bug

Epic: mcpagentmail-1
Generated: 2026-01-09

## Problem Summary

WSL users experience "Contact approval required" errors even when auto-handshake is enabled because:
1. Silent exception swallowing hides failures
2. `/mnt/c/...` and `C:\...` create different project slugs (split-brain identity)

## Tracks

| Track | Agent | Beads (in order) | File Scope |
|-------|-------|------------------|------------|
| 1 | BlueLake | mcpagentmail-2 → mcpagentmail-5 → mcpagentmail-6 | `src/mcp_agent_mail/app.py` (contact/logging) |
| 2 | GreenCastle | mcpagentmail-3 → mcpagentmail-7 → mcpagentmail-4 | `src/mcp_agent_mail/utils.py`, `tests/` |

## Track Details

### Track 1: BlueLake - Logging & Exception Handling

**File scope**: `src/mcp_agent_mail/app.py` (contact enforcement sections)

**Beads**:
1. `mcpagentmail-2`: Add structured logging to contact enforcement flow (P1, LOW risk)
2. `mcpagentmail-5`: Narrow exception handling in auto-handshake path (P2, MEDIUM risk)
3. `mcpagentmail-6`: Add contact enforcement metrics (P3, LOW risk)

### Track 2: GreenCastle - Path Canonicalization

**File scope**: `src/mcp_agent_mail/utils.py`, `tests/`

**Beads**:
1. `mcpagentmail-3`: Add WSL/Windows path canonicalization utility (P1, LOW risk)
2. `mcpagentmail-7`: Add unit tests for path canonicalization (P1, LOW risk)
3. `mcpagentmail-4`: Integrate path canonicalization into project lookup (P1, MEDIUM risk)

## Cross-Track Dependencies

- Both tracks can start in parallel (no cross-track deps)
- Track 1 provides visibility; Track 2 fixes root cause
- Recommend completing both before declaring bug fixed

## Suggested Starting Points

Ready now:
- `mcpagentmail-1` (Epic - mark in-progress)
- `mcpagentmail-2` (Logging - highest leverage, reveals failures)
- `mcpagentmail-3` (Path util - fixes root cause)

## Verification

After implementation:
1. Test on WSL with `/mnt/c/...` path
2. Verify auto-handshake succeeds without manual intervention
3. Check logs show handshake flow
4. Confirm same project identity for WSL and Windows paths
