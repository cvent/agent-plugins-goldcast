---
name: goldcast-speakers-onboard
description: "Adds speakers and optionally staff to an existing Goldcast event from a list. Do NOT use for creating a new event with speakers."
license: "proprietary"
---

# goldcast-speakers-onboard

Bulk-add speakers (and optionally staff) to an existing Goldcast event.

## Orchestration

1. **Resolve event** — if the user provides a UUID, call `mcp__Goldcast__get_event(eventId=<uuid>)` directly. If they provide an event name, call `mcp__Goldcast__search_events(query="<name>")` first; if multiple matches, show candidates and ask the user to pick; then `get_event` to confirm.
2. **Gather event context** — in parallel:
   - `mcp__Goldcast__list_broadcasts(eventId=<uuid>)` → collect all broadcast UUIDs.
   - `mcp__Goldcast__list_roles(roleGroup="Staff Roles")` → collect roleId for Producer / Coordinator (needed only if staff are requested).
3. **Resolve people** — for each name or email the user provided, call `mcp__Goldcast__search_users(query=<name_or_email>)`. Match by email when available; match by name when only a name is given. If a matched profile lacks `firstName` or `lastName`, treat it as unresolved for names. Collect all unresolved entries into a separate list.
4. **Ask about unresolved people** — if any person could not be resolved, present the unresolved list and ask the user to provide the missing details. `create_speaker` requires `firstName`, `lastName`, and `email`. For an email-only entry with no name match, ask the user for first and last name. For a name-only entry with no email match, ask the user for the email. Speakers can be created with a new email (they don't need to be existing users).
5. **Confirmation gate** — present the full plan and wait for approval (see § Confirmation Gates).
6. **Create speakers** — for each confirmed speaker, call `mcp__Goldcast__create_speaker(eventId, email, firstName, lastName)` plus optional `company`, `title`, `broadcastIds`, `sendEmailInvite`, `sendCalendarInvite`. Run in parallel where possible.
7. **Create staff** (if requested) — for each confirmed staff member, call `mcp__Goldcast__create_staff(eventId, email, roleId, broadcastIds)` plus optional `firstName`, `lastName`, `sendEmailInvite`, `sendCalendarInvite`. Run in parallel where possible.
8. **Report results** — present a per-person success/failure summary.

## Tool References

| Tool | Purpose |
|---|---|
| `mcp__Goldcast__search_events` | Resolve event name → UUID (when user provides a name, not a UUID) |
| `mcp__Goldcast__get_event` | Validate the target event exists and get its title |
| `mcp__Goldcast__list_broadcasts` | Get broadcast UUIDs for speaker/staff broadcast assignment |
| `mcp__Goldcast__list_roles` | Get roleId for staff roles (Producer, Coordinator) |
| `mcp__Goldcast__search_users` | Resolve names/emails to user profiles |
| `mcp__Goldcast__create_speaker` | Add a speaker to the event |
| `mcp__Goldcast__create_staff` | Add a staff member to the event with role + broadcast scope |
| `mcp__Goldcast__create_error_report` | Report terminal errors when `llmAction` starts with `report_` |

## Guardrails

### Policy
- NEVER create a speaker or staff member without the user's confirmation.
- NEVER send invites without confirming the user's preference — `sendEmailInvite` and `sendCalendarInvite` both default to `true`.

### Capability
- `mcp__Goldcast__create_speaker` requires: `eventId`, `email`, `firstName`, `lastName`. Optional: `company`, `title`, `broadcastIds`, `sendEmailInvite`, `sendCalendarInvite`.
- `mcp__Goldcast__create_staff` requires: `eventId`, `email`, `roleId`, `broadcastIds`. Optional: `firstName`, `lastName`, `sendEmailInvite`, `sendCalendarInvite`.
- `mcp__Goldcast__list_roles` must use `roleGroup="Staff Roles"` to get staff-appropriate roles. Role IDs are organization-specific.
- `mcp__Goldcast__search_users` matches on firstName, lastName, and email — a query like "sam" returns all matching users.

### Operational
- Paginate `mcp__Goldcast__list_broadcasts` if the event has many sessions (default 25, max 100 per page).
- For events with a single broadcast, assign all speakers/staff to that broadcast. For multi-broadcast events, ask the user which sessions each person should be assigned to.

### Data Quality
- Deduplicate the input list by email before proceeding — reject duplicate entries.
- If `mcp__Goldcast__search_users` returns multiple matches for a name, present the candidates and ask the user to pick.

## Confirmation Gates

Before creating any speaker or staff member, present a confirmation summary:

```
**Speakers to add (N):**
| Name | Email | Broadcasts |
|---|---|---|
| Ada Lovelace | ada@example.com | All sessions |
| ... | ... | ... |

**Staff to add (M):** (if any)
| Name | Email | Role | Broadcasts |
|---|---|---|---|
| Sam Rivera | sam@example.com | Producer | All sessions |
| ... | ... | ... | ... |

**Invite settings:**
- Send email invite: yes / no
- Send calendar invite: yes / no

Proceed?
```

Wait for explicit user approval. If the user changes any detail, update the plan and re-confirm.

## Communication Contract

**Before:** "I'll add [N] speakers [and M staff] to [event title]. Let me verify the event and resolve the people first."

**During:** Report progress for large batches: "Added 5 of 12 speakers…"

**After:** Present the per-person results table (see § Output Formatting).

## Graceful Degradation

| Failure | Response |
|---|---|
| Connection error / auth failure from any tool | **Hard stop.** Tell the user the MCP connection is not active. Do not continue. |
| `mcp__Goldcast__get_event` fails or returns empty | Stop — the target event does not exist or is inaccessible. |
| `mcp__Goldcast__list_broadcasts` fails | Stop — broadcast IDs are required for staff assignment and optional for speakers. Cannot proceed safely without knowing the event's sessions. |
| `mcp__Goldcast__list_roles` fails (staff requested) | Skip staff creation. Tell the user staff cannot be added without role information and suggest trying again. |
| `mcp__Goldcast__search_users` fails for one person | Add to the unresolved list; ask user for email. Do not skip silently. |
| `mcp__Goldcast__create_speaker` fails for one person | Log the failure, continue with remaining speakers. Report in the final summary. |
| `mcp__Goldcast__create_staff` fails for one person | Log the failure, continue with remaining staff. Report in the final summary. |
| Error body has `llmAction` starting with `report_` | Call `mcp__Goldcast__create_error_report` — pass `trackingId`, `mcpErrorCode`, `failedTool` unchanged; write `intentSummary` and `userRequestSummary` with no PII (no names, emails, or user IDs). |

## Few-Shot Examples

### Happy path — event ID + list of emails

**User:** "Add these speakers to event 3f2c9a1e-7b4d-4c58-9e21-6a0f8d2b5c73: ada@example.com (Ada Lovelace), grace@example.com (Grace Hopper)"

**Assistant:** "I'll add 2 speakers to that event. Let me verify the event and resolve the people."

1. Call `mcp__Goldcast__get_event(eventId="3f2c9a1e-7b4d-4c58-9e21-6a0f8d2b5c73")` → confirms "Q4 Product Launch"
2. Call `mcp__Goldcast__list_broadcasts(eventId="3f2c9a1e-7b4d-4c58-9e21-6a0f8d2b5c73")` → 1 broadcast (Main Session)
3. Present confirmation:
   > **Speakers to add (2):**
   > | Name | Email | Broadcasts |
   > |---|---|---|
   > | Ada Lovelace | ada@example.com | Main Session |
   > | Grace Hopper | grace@example.com | Main Session |
   >
   > **Send email invite:** yes | **Send calendar invite:** yes
   >
   > Proceed?

4. On approval → create both speakers in parallel → report results.

### Ambiguity — names only, multiple broadcasts

**User:** "Add Sam and Jordan as speakers to the Q4 Launch event, and also add Sam as a producer"

**Assistant:** "I'll look up the event and resolve Sam and Jordan. Since you mentioned a producer role, I'll also check staff roles."

1. Call `mcp__Goldcast__search_events(query="Q4 Launch")` → 1 match: "Q4 Launch" (`evt-abc`). Call `mcp__Goldcast__get_event(eventId="evt-abc")` → confirms event.
2. Parallel: `mcp__Goldcast__list_broadcasts(...)` → 3 broadcasts (Keynote, Breakout A, Breakout B), `mcp__Goldcast__list_roles(roleGroup="Staff Roles")` → Producer (roleId=9), Coordinator (roleId=10)
3. Call `mcp__Goldcast__search_users(query="Sam")` → 2 matches: Sam Rivera (sam@example.com), Sam Chen (schen@example.com)
4. Call `mcp__Goldcast__search_users(query="Jordan")` → 1 match: Jordan Lee (jordan@example.com)
5. Ask: "I found two Sams — Sam Rivera (sam@example.com) and Sam Chen (schen@example.com). Which Sam should I add as speaker and producer?"
6. User clarifies → "Sam Rivera for both"
7. Ask: "The event has 3 sessions: Keynote, Breakout A, Breakout B. Which sessions should each person be assigned to?"
8. User: "All of them"
9. Present confirmation with all details including broadcast assignments and invite preferences → proceed on approval.

## Output Formatting

After all creates complete, present a results table:

```
**Results — [event title]**

| Person | Role | Status | Details |
|---|---|---|---|
| Ada Lovelace (ada@example.com) | Speaker | Added | Assigned to: Main Session |
| Grace Hopper (grace@example.com) | Speaker | Added | Assigned to: Main Session |
| Sam Rivera (sam@example.com) | Staff (Producer) | Failed | Error: [reason] |

**Summary:** 2 of 3 succeeded. 1 failed — see details above.
```

- Group speakers first, then staff.
- For failures, include the error reason from the tool response.
- Do not include user IDs or internal identifiers in the output.
