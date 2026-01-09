# Approach: Fix Contact Approval Errors When Auto-Handshake Is Enabled (WSL)

## Problem Statement
On WSL, `am send_message` throws contact approval errors even when `messaging_auto_handshake_on_block` / auto-handshake is enabled. Discovery indicates two compounding issues:
1. Critical handshake/enforcement failures are silently swallowed (`except Exception: pass`), so auto-handshake may be failing without visibility
2. Project identification is derived from `slugify()` of user-provided identifiers/paths with no WSL/Windows canonicalization, so the same workspace can map to different `Project.slug` values (`/mnt/c/...` vs `C:\...`)

---

## 1) Gap Analysis

| Component | Have | Need | Gap |
|-----------|------|------|-----|
| Contact enforcement logging | Zero logs | Structured debug/warning logs | No visibility into failures |
| Exception handling | 10+ `except Exception: pass` | Specific exception catches + logging | Silent failures |
| Path normalization | `slugify()` directly | WSL/Windows canonicalization | Split-brain project identity |
| Error reporting | Generic "Contact approval required" | Specific failure reason | Hard to diagnose |
| Metrics | None for contact flow | Success/failure counters | No aggregate visibility |

---

## 2) Recommended Approach

### A. Add Structured Logging (LOW risk, highest leverage)

**Files:** `src/mcp_agent_mail/app.py`

**Changes in `send_message` contact enforcement (~3875-4124):**
1. Add "start" log: sender, project, recipients count, enforcement enabled
2. Replace `except Exception: pass` with `logger.debug(..., extra={...})`
3. Log blocked_reason per recipient (policy, no_agentlink, ttl_recent=false)
4. Log auto-handshake success/failure with exception details

### B. Fix Project Identifier Canonicalization (MEDIUM risk)

**Files:** `src/mcp_agent_mail/utils.py`, `src/mcp_agent_mail/app.py`

**New utility:**
```python
def canonicalize_project_identifier(identifier: str) -> str:
    # Normalize slashes: \ -> /
    # Normalize drive: C: -> c:
    # Convert WSL: /mnt/c/foo -> c:/foo
    # Convert Windows: C:\foo -> c:/foo
    # Collapse repeated /, trim whitespace
```

**Update `_get_project_by_identifier`:**
- Two-pass lookup: canonical first, then legacy fallback
- Log fallback hits for migration visibility

### C. Narrow Exception Handling (MEDIUM risk, after logging)

Replace broad `except Exception` with specific catches:
- `NoResultFound` for DB lookups
- `OperationalError` for DB issues
- Keep final broad catch but log at warning

### D. Add Contact Metrics (LOW risk)

New counters:
- `contact.auto_handshake.calls`
- `contact.auto_handshake.success`
- `contact.auto_handshake.error`
- `contact.enforcement.blocked`

---

## 3) Risk Assessment

| Component | Risk | Reason | Mitigation |
|-----------|------|--------|------------|
| Logging additions | LOW | No behavior change | Use debug for high-freq |
| Path canonicalization | MEDIUM | Changes project resolution | Two-pass lookup fallback |
| Exception narrowing | MEDIUM | May expose hidden bugs | Phase after logging |
| Metrics/counters | LOW | In-memory only | None needed |

---

## 4) Alternative Approaches Considered

1. **DB migration to merge projects** - Too risky, deferred
2. **Git-based stable project_key** - Good but out of scope for bugfix
3. **WSL filesystem calls (realpath)** - Environment-dependent, avoid
4. **Alias table for project identifiers** - Heavier than needed

---

## Implementation Order

1. **Phase 1:** Add logging (reveals actual failure points)
2. **Phase 2:** Path canonicalization (fixes WSL root cause)
3. **Phase 3:** Narrow exceptions (cleanup after visibility)
4. **Phase 4:** Add metrics (long-term observability)
