---
name: goldcast-speakers-onboard
description: "Adds speakers and optionally staff to an existing Goldcast event from a list. Do NOT use for creating a new event with speakers."
license: "proprietary"
---

# goldcast-speakers-onboard

Bulk-add speakers (and optionally staff) to an existing Goldcast event.
Tool names in this skill are the Goldcast connector's own names (e.g. `list_roles`). Your client may show them with a prefix such as `mcp__Goldcast__list_roles`. Use whichever form your client exposes.

## Orchestration

1. **Resolve event** — if the user provides a UUID, call `get_event(eventId=<uuid>)` directly. If they provide an event name, call `search_events(query="<n>")` first; if multiple matches, show candidates and ask the user to pick; then `get_event` to confirm.
2. **Gather event context** — in parallel:
   - `list_broadcasts(eventId=<uuid>)` → collect all broadcast UUIDs.
   - `list_roles(roleGroup="Staff Roles")` → collect roleId for Producer / Coordinator (needed only if staff are requested).
3. **Resolve people** — for each name or email the user provided, call `search_users(query=<name_or_email>)`. Match by email when available; match by name when only a name is given. If a matched profile lacks `firstName` or `lastName`, treat it as unresolved for names. Collect all unresolved entries into a separate list.
4. **Ask about unresolved people** — if any person could not be resolved, present the unresolved list and ask the user to provide the missing details. `create_speaker` requires `firstName`, `lastName`, and `email`. For an email-only entry with no name match, ask the user for first and last name. For a name-only entry with no email match, ask the user for the email. Speakers can be created with a new email (they don't need to be existing users).
5. **Resolve speaker access levels** — if the user named or described a level for any speaker ("Ada needs full access"), call `list_roles(roleGroup="Speaker Roles")` and match by name or by what it allows. If a speaker has no stated level, show "Share Access (default)" for them in the gate. Role IDs differ per organization, so never hard-code them.
6. **Ask about invites — always, with no default.** Ask: "Should I send email and calendar invites when I add these people?" with the options "Email + calendar", "Email only", "Calendar only" and "Hold both". Never pre-select or suggest an option, and never skip the question because the user mentioned invites earlier.
7. **Confirmation gate** — present each person's full details and the invite answer, then wait for explicit approval (see § Confirmation Gates). Create no one before this.
8. **Create speakers** — for each confirmed speaker, call `create_speaker(eventId, email, firstName, lastName)` plus optional `company`, `title`, `eventAppRole` (only for a non-default level), `broadcastIds`, and both `sendEmailInvite` and `sendCalendarInvite` set from the user's answer. Run in parallel where possible.
9. **Create staff** (if requested) — for each confirmed staff member, call `create_staff(eventId, email, roleId, broadcastIds)` plus optional `firstName`, `lastName`, and both `sendEmailInvite` and `sendCalendarInvite` set from the user's answer. Run in parallel where possible.
10. **Report results** — present a per-person success/failure summary.

| Tool | Purpose |
|---|---|
| `search_events` | Resolve event name → UUID (when user provides a name, not a UUID) |
| `get_event` | Validate the target event exists and get its title |
| `list_broadcasts` | Get broadcast UUIDs for speaker/staff broadcast assignment |
| `list_roles` | Get roleId for staff roles (Producer, Coordinator) with `roleGroup="Staff Roles"`, and speaker access tiers with `roleGroup="Speaker Roles"` |
| `search_users` | Resolve names/emails to user profiles |
| `create_speaker` | Add a speaker to the event |
| `create_staff` | Add a staff member to the event with role + broadcast scope |
| `create_error_report` | Report terminal errors when `llmAction` starts with `report_` |

### Policy
- NEVER create a speaker or staff member without first showing that person's full details (name, email, role or access level, sessions, job title and company if given, invite settings) and getting the user's explicit approval.
- NEVER assume, default, pre-select or recommend an invite choice. `sendEmailInvite` and `sendCalendarInvite` default to `true` in the tools, so always ask first and always pass both explicitly.
- NEVER skip the invite question because the user mentioned invites earlier in the conversation.

### Capability
- `create_speaker` requires: `eventId`, `email`, `firstName`, `lastName`. Optional: `company`, `title`, `eventAppRole` (speaker access level; omit for Share Access), `broadcastIds`, `sendEmailInvite`, `sendCalendarInvite`.
- `create_staff` requires: `eventId`, `email`, `roleId`, `broadcastIds`. Optional: `firstName`, `lastName`, `sendEmailInvite`, `sendCalendarInvite`.
- `list_roles` must use `roleGroup="Staff Roles"` for staff roles and `roleGroup="Speaker Roles"` for speaker access levels. Role IDs are organization-specific.
- `search_users` matches on firstName, lastName, and email — a query like "sam" returns all matching users.

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
| Name | Email | Job title / Company | Access level | Sessions |
|---|---|---|---|---|
| Ada Lovelace | ada@example.com | CTO, Acme (if given) | Share Access (default) | All sessions |
| ... | ... | ... | ... | ... |

**Staff to add (M):** (if any)
| Name | Email | Job title / Company | Role | Sessions |
|---|---|---|---|---|
| Sam Rivera | sam@example.com | (if given) | Producer | All sessions |
| ... | ... | ... | ... | ... |

**Invites (as you answered):**
- Send / Hold

Reply **add them** to approve, or tell me what to change.
```

Wait for explicit user approval. If the user changes any detail, update the plan and re-confirm. A "yes" given before the summary was shown does not count.

## Communication Contract

**Before:** "I'll add [N] speakers [and M staff] to [event title]. Let me verify the event and resolve the people first."

**During:** Report progress for large batches: "Added 5 of 12 speakers…"

**After:** Present the per-person results table (see § Output Formatting).

| Failure | Response |
|---|---|
| Connection error / auth failure from any tool | **Hard stop.** Tell the user the MCP connection is not active. Do not continue. |
| `get_event` fails or returns empty | Stop — the target event does not exist or is inaccessible. |
| `list_broadcasts` fails | Stop — broadcast IDs are required for staff assignment and optional for speakers. Cannot proceed safely without knowing the event's sessions. |
| `list_roles` fails (staff requested) | Skip staff creation. Tell the user staff cannot be added without role information and suggest trying again. |
| `list_roles` fails (speaker access level requested) | Don't guess an access level. Tell the user the level can't be looked up, and offer to add the speaker with Share Access (default) only if they approve. |
| `search_users` fails for one person | Add to the unresolved list; ask user for email. Do not skip silently. |
| `create_speaker` fails for one person | Log the failure, continue with remaining speakers. Report in the final summary. |
| `create_staff` fails for one person | Log the failure, continue with remaining staff. Report in the final summary. |
| Error body has `llmAction` starting with `report_` | Call `create_error_report` — pass `trackingId`, `mcpErrorCode`, `failedTool` unchanged; write `intentSummary` and `userRequestSummary` with no PII (no names, emails, or user IDs). |

## Few-Shot Examples

### Happy path — event ID + list of emails

**User:** "Add these speakers to event 3f2c9a1e-7b4d-4c58-9e21-6a0f8d2b5c73: ada@example.com (Ada Lovelace), grace@example.com (Grace Hopper)"

**Assistant:** "I'll add 2 speakers to that event. Let me verify the event and resolve the people."

1. Call `get_event(eventId="3f2c9a1e-7b4d-4c58-9e21-6a0f8d2b5c73")` → confirms "Q4 Product Launch"
2. Call `list_broadcasts(eventId="3f2c9a1e-7b4d-4c58-9e21-6a0f8d2b5c73")` → 1 broadcast (Main Session)
3. Ask the invite question: "Should I send email and calendar invites when I add these people?" with no option pre-selected. The user picks "Email + calendar".
4. Present confirmation:
   > **Speakers to add (2):**
   > | Name | Email | Job title / Company | Access level | Sessions |
   > |---|---|---|---|---|
   > | Ada Lovelace | ada@example.com | n/a | Share Access (default) | Main Session |
   > | Grace Hopper | grace@example.com | n/a | Share Access (default) | Main Session |
   >
   > **Invites:** Email: Send · Calendar: Send
   >
   > Reply **add them** to approve, or tell me what to change.

5. On approval → create both speakers in parallel → report results.

### Ambiguity — names only, multiple broadcasts

**User:** "Add Sam and Jordan as speakers to the Q4 Launch event, and also add Sam as a producer"

**Assistant:** "I'll look up the event and resolve Sam and Jordan. Since you mentioned a producer role, I'll also check staff roles."

1. Call `search_events(query="Q4 Launch")` → 1 match: "Q4 Launch" (`evt-abc`). Call `get_event(eventId="evt-abc")` → confirms event.
2. Parallel: `list_broadcasts(...)` → 3 broadcasts (Keynote, Breakout A, Breakout B), `list_roles(roleGroup="Staff Roles")` → Producer (roleId=9), Coordinator (roleId=10)
3. Call `search_users(query="Sam")` → 2 matches: Sam Rivera (sam@example.com), Sam Chen (schen@example.com)
4. Call `search_users(query="Jordan")` → 1 match: Jordan Lee (jordan@example.com)
5. Ask: "I found two Sams — Sam Rivera (sam@example.com) and Sam Chen (schen@example.com). Which Sam should I add as speaker and producer?"
6. User clarifies → "Sam Rivera for both"
7. Ask: "The event has 3 sessions: Keynote, Breakout A, Breakout B. Which sessions should each person be assigned to?"
8. User: "All of them"
9. Ask the invite question (no default), then present the confirmation with each person's access level, sessions and invite settings → proceed only on approval.

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
