# Discovery Report: Contact Approval & Auto-Handshake

## Architecture Snapshot

### Relevant Modules
- `src/mcp_agent_mail/app.py` — Core MCP server, all contact enforcement and handshake logic
- `src/mcp_agent_mail/utils.py` — `slugify()` for project_key normalization

### Key Entry Points
| Function | Lines | Purpose |
|----------|-------|---------|
| `send_message` contact enforcement | 3875–4124 | Per-recipient contact policy enforcement with auto-handshake |
| `macro_contact_handshake` | 5452–5589 | High-level orchestration: request + respond + optional welcome |
| `request_contact` | 4786–4925 | Create/update AgentLink with `pending` status |
| `respond_contact` | 4927–4990 | Approve/deny contact request, set `approved`/`blocked` status |
| `_get_project_by_identifier` | 1409–1481 | Project lookup by slug with suggestions |

---

## Current Architecture of Contact Enforcement

### Flow in `send_message` (lines 3875–4124)

```
1. Check settings_local.contact_enforcement_enabled
2. If ack_required=True → bypass enforcement entirely (line 3878)
3. Build auto_ok_names set:
   a. Thread participants (lines 3881–3904)
   b. Overlapping file reservations (lines 3905–3927)
4. For each recipient not in auto_ok_names:
   a. Get recipient Agent (may fail silently)
   b. Check recipient contact_policy (open/auto/contacts_only/block_all)
   c. Check for recent messages (TTL-based auto-allow)
   d. Check for approved AgentLink
   e. If all fail → add to blocked_recipients
5. If blocked_recipients and auto_contact_if_blocked enabled:
   a. Run macro_contact_handshake for each blocked recipient
   b. Re-evaluate after handshake attempts
6. If still blocked → raise CONTACT_REQUIRED error
```

### Auto-Handshake Integration (lines 4006–4055)

The auto-handshake is triggered when:
- `auto_contact_if_blocked` param is truthy, OR
- `settings_local.messaging_auto_handshake_on_block` is True (default)

---

## Exception Handling Patterns (Silent Swallows)

### Critical: Exceptions Silently Swallowed

| Location | Lines | What's Swallowed | Impact |
|----------|-------|------------------|--------|
| Thread participant lookup | 3903–3904 | `except Exception: pass` | Thread-based auto-allow fails silently |
| File reservation lookup | 3926–3927 | `except Exception: pass` | Reservation-based auto-allow fails silently |
| Recipient agent lookup | 3937–3938 | `except Exception: continue` | Unknown recipients silently skipped |
| Recent message check | 3973–3974 | `except Exception: recent_ok = False` | TTL auto-allow fails silently |
| AgentLink check | 3992–3993 | `except Exception: pass` | Approved link check fails silently |
| **Auto-handshake per-recipient** | **4023–4024** | `except Exception: pass` | **Handshake failures completely invisible** |
| Re-evaluation after handshake | 4054–4055 | `except Exception: pass` | Re-check failures invisible |
| Suggested tool calls generation | 4116–4117 | `except Exception: pass` | Example generation fails silently |
| `macro_contact_handshake` inference | 5504–5505 | `except Exception: pass` | Agent inference fails silently |

### Pattern Analysis

The codebase uses a **fail-soft** pattern extensively:
- Every database/network operation wrapped in `try/except Exception: pass`
- No logging of swallowed exceptions
- No differentiation between transient and permanent failures
- No metrics/counters for failure rates

This makes debugging extremely difficult because:
1. Failures are invisible
2. No way to distinguish "working correctly" from "silently failing"
3. Auto-handshake could be broken and nobody would know

---

## Path Handling for Project Lookup

### `slugify()` Function (utils.py:168–172)

```python
def slugify(value: str) -> str:
    normalized = value.strip().lower()
    slug = _SLUG_RE.sub("-", normalized).strip("-")
    return slug or "project"
```

Where `_SLUG_RE = re.compile(r"[^a-z0-9]+")`

### Path Normalization Behavior

| Input | Slugified Output |
|-------|------------------|
| `/mnt/c/WORKSPACES/project` | `mnt-c-workspaces-project` |
| `C:\Users\Me\project` | `c-users-me-project` |
| `/home/user/project` | `home-user-project` |
| `my-project` | `my-project` |

### WSL/Windows Considerations

**Current handling:**
- No WSL-specific path translation (e.g., `/mnt/c/...` ↔ `C:\...`)
- Slugify treats both as different slugs
- Windows backslashes (`\`) become dashes just like forward slashes

**Potential issues:**
- Same physical directory accessed via WSL path vs Windows path → different slugs → different projects
- No path canonicalization before slugify

### `_get_project_by_identifier()` Logic (lines 1409–1481)

1. Validate non-empty input
2. Detect placeholder patterns (YOUR_PROJECT, etc.)
3. `slugify(identifier)` → lookup by `Project.slug`
4. If not found → `_find_similar_projects()` for suggestions
5. Raise `NOT_FOUND` with helpful message

**No normalization applied before slugify** — the raw identifier goes straight through.

---

## Existing Logging Patterns

### Logger Usage (app.py)

| Line | Level | Context |
|------|-------|---------|
| 130 | `warning` | `tool_error` — generic tool error recording |
| 427 | `warning` | `capability_mapping.load_failed` |
| 462 | `info` | Startup info |
| 1794 | `debug` | `project_sibling.llm_failed` |
| 3004 | `debug` | `thread_summary.llm_skipped` |
| 5691 | `warning` | FTS query failed |
| 6900 | `warning` | FTS product query failed |

### Observations

1. **Structured logging** is used with `extra={}` dict
2. **Very sparse logging** — only 7 log statements in 8400+ lines
3. **No logging in contact enforcement flow** — entire 250-line section is log-silent
4. **Context mechanism exists** via `ctx.debug()`, `ctx.info()`, `ctx.error()` but:
   - These write to MCP client, not server logs
   - Used inconsistently
   - `ctx.debug()` at line 5583 in macro_contact_handshake is the only trace

---

## Key Findings Summary

### High Priority Issues

1. **Silent exception swallowing in auto-handshake** (lines 4023–4024)
   - When handshake fails, no error is raised or logged
   - `attempted` list is only populated on success
   - Impossible to debug handshake failures

2. **No logging in contact enforcement**
   - 250 lines of critical logic with zero visibility
   - All failures fall through silently

3. **Path normalization gap**
   - No WSL/Windows path equivalence
   - Same directory = different projects if accessed via different paths

### Medium Priority Issues

4. **Overly broad exception handling**
   - `except Exception` everywhere catches programming errors
   - Should be `except (OperationalError, NoResultFound)` etc.

5. **No metrics/counters**
   - No way to measure handshake success rate
   - No way to detect systemic failures

### Recommendations for Fix

1. Add structured logging to auto-handshake flow:
   ```python
   except Exception as exc:
       logger.warning("contact.auto_handshake.failed", extra={
           "recipient": nm,
           "sender": sender.name,
           "project": project.human_key,
           "error": str(exc),
       })
   ```

2. Narrow exception types to expected failures only

3. Consider path canonicalization before slugify for WSL compatibility

4. Add success/failure counters for observability

---

## Files for Modification

| File | Changes Needed |
|------|----------------|
| `app.py` lines 4006–4055 | Add logging to auto-handshake, narrow exceptions |
| `app.py` lines 5452–5589 | Add logging to macro_contact_handshake |
| `utils.py` lines 168–172 | Consider path normalization enhancement |
| New: observability | Add counters/metrics for handshake outcomes |
