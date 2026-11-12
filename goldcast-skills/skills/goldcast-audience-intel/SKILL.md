---
name: goldcast-audience-intel
description: "Analyses audience demographics for a Goldcast event or series. Do NOT use for event performance reports or individual attendee lists."
license: "proprietary"
---

# Audience Intel

Analyse audience composition for a Goldcast event or series — company mix, seniority breakdown, repeat-attendance patterns, and series loyalty.

## Orchestration

Determine whether the user is asking about an **event** or a **series**, then follow the matching branch.

### Event Branch

1. **Resolve event.** If the user provides a UUID, use it directly. If they provide a name, call `mcp__Goldcast__search_events(query="<name>", upcomingOnly=false)`. Past events are the common case for audience analysis. If multiple matches, show candidates and ask the user to pick.
2. **Parallel fan-out** — call all three simultaneously:
   - `mcp__Goldcast__get_attendee_demographics(eventId="<uuid>")` — returns up to 100 per page. Use the first page as a representative sample; do not paginate exhaustively. Always state sample size in output. NOT event totals.
   - `mcp__Goldcast__get_registration_breakdown(eventId="<uuid>")` — whole-event counts
   - `mcp__Goldcast__list_repeat_attendees(eventId="<uuid>")` — interaction-level rows. **Paginate with `offset`** until `hasMore=false`, then deduplicate by `email` before counting unique repeat attendees.
3. **Synthesise** the audience profile from the combined data.

### Series Branch

1. **Resolve series.** If the user provides a UUID, use it directly. If they provide a name, call `mcp__Goldcast__list_series(name="<name>")` and paginate if needed. If multiple matches, ask the user to pick.
2. **Parallel fan-out:**
   - `mcp__Goldcast__get_series_engagement(seriesId="<uuid>", minSessions=2)` — returns **qualified attendees** (attended 2+ sessions)
   - `mcp__Goldcast__list_series_loyal_attendees(seriesId="<uuid>", minSessions=3)` — returns **loyal attendees** (attended 3+ sessions)
3. **Synthesise** the series audience profile. Report seniority and company commonalities across the two cohorts.

**Label the two cohorts distinctly.** "Qualified attendees" (minSessions=2) and "loyal attendees" (minSessions=3) are different thresholds and different data sets — never use one label for both.

## Tool References

| Tool | Purpose |
|---|---|
| `mcp__Goldcast__search_events` | Resolve event name → UUID (`upcomingOnly=false` for past events) |
| `mcp__Goldcast__get_attendee_demographics` | Paginated sample of registrant demographics (company, title, seniority) |
| `mcp__Goldcast__get_registration_breakdown` | Whole-event registration totals by seniority and company |
| `mcp__Goldcast__list_repeat_attendees` | Attendees who also attended prior events (interaction-level rows) |
| `mcp__Goldcast__list_series` | Resolve series name → UUID |
| `mcp__Goldcast__list_series_loyal_attendees` | Series attendees with 3+ sessions (loyal attendees) |
| `mcp__Goldcast__get_series_engagement` | Series attendees with 2+ sessions (qualified attendees) |
| `mcp__Goldcast__create_error_report` | Report terminal errors when `llmAction` starts with `report_` |

## Guardrails

- **NEVER** surface individual names, emails, or titles unless the user explicitly requests them. This is an aggregate-only skill by default.
- **NEVER** promise "all attendees" from `get_attendee_demographics` — it returns a paginated sample. Always state the sample size.
- **NEVER** report raw row counts from `list_repeat_attendees` as unique attendees — deduplicate by `email` first.
- **NEVER** attempt series→event enumeration via `search_events` name matching. If the user asks for per-event breakdown within a series, explain the limitation and suggest using `goldcast-event-reports` on specific events.
- Pass `upcomingOnly=false` to `search_events` for audience analysis — past events are the common case.

## Confirmation Gates

None — this is a read-only workflow.

## Communication Contract

**Before:** "I'll analyse the audience for [event/series name]. One moment while I pull the data."

**During:** If fetching multiple pages or both cohorts, brief status: "Pulling registration breakdown and demographics…"

**After:** Deliver the formatted audience profile.

## Graceful Degradation

**Connection/auth hard stop:** If any tool returns a connection error, authentication failure, or no response (not just an empty result), stop immediately. Tell the user: "The Goldcast MCP connection is not active. Please check your connection and try again." Do not continue with partial data.

| Tool failure | Action |
|---|---|
| `search_events` returns no match | Ask the user to verify the event name or provide a UUID |
| `get_attendee_demographics` fails | Skip demographics sample; note "demographics unavailable" in output; `get_registration_breakdown` still provides totals |
| `get_registration_breakdown` fails | Use `get_attendee_demographics` counts as a sample-based estimate; note the limitation |
| `list_repeat_attendees` fails | Omit repeat-attendee section; note it in output |
| `list_series` returns no match | Ask the user to verify the series name or provide a UUID |
| `get_series_engagement` fails | Report loyal attendees only; note "qualified-attendee data unavailable" |
| `list_series_loyal_attendees` fails | Report qualified attendees only; note "loyal-attendee data unavailable" |

**Truncation caveats:**
- `get_series_engagement`: check the `truncated` and `truncationNote` fields. When `truncated=true`, `totalAttendees` is a lower bound. Surface: "Based on a scan of N registrants; the full series may have more."
- `get_registration_breakdown`: check for truncation and note if counts are partial.
- `list_repeat_attendees`: returns interaction-level rows (one per attendee per interaction type). Walk all pages (`hasMore`/`offset`), then deduplicate by `email` before counting.

**Error reporting:** If a tool error body has `llmAction` starting with `report_`, call `mcp__Goldcast__create_error_report` — pass `trackingId`, `mcpErrorCode`, and `failedTool` unchanged; write `intentSummary` and `userRequestSummary` yourself with no personal data (names, emails, IDs). For other errors, use the degradation path above.

## Few-Shot Examples

### Example 1: Happy path — event UUID

**User:** "What does the audience look like for event 8a3f1b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c?"

**Assistant:** "I'll analyse the audience for that event. One moment."

Calls in parallel:
- `mcp__Goldcast__get_attendee_demographics(eventId="8a3f1b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c")`
- `mcp__Goldcast__get_registration_breakdown(eventId="8a3f1b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c")`
- `mcp__Goldcast__list_repeat_attendees(eventId="8a3f1b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c")`

Delivers audience profile with seniority breakdown, top companies, and repeat-attendee count (deduplicated by email).

### Example 2: Ambiguity — "audience for my series"

**User:** "Who attends my webinar series?"

**Assistant:** "I'll look up your series. What's the series name?"

User provides: "Product Launch Series"

Calls `mcp__Goldcast__list_series(name="Product Launch Series")`. If one match, proceeds. If multiple, shows candidates.

Then calls in parallel:
- `mcp__Goldcast__get_series_engagement(seriesId="<resolved-uuid>", minSessions=2)`
- `mcp__Goldcast__list_series_loyal_attendees(seriesId="<resolved-uuid>", minSessions=3)`

Delivers series audience profile:
- **Qualified attendees** (2+ sessions): N attendees — seniority and company commonalities
- **Loyal attendees** (3+ sessions): N attendees — top individuals by engagement (aggregated by default)

## Output Formatting

### Event Branch

```
## Audience Profile — [Event Name]

### Overview
- Registered: N
- Repeat attendees: N unique (X% attended a prior event)

### Seniority Breakdown
| Level | Count | % |
|---|---|---|
| C-Level | N | X% |
| VP | N | X% |
| Director | N | X% |
| Manager | N | X% |
| Individual Contributor | N | X% |

(From registration breakdown — whole-event totals)

### Top Companies
| Company | Registrants |
|---|---|
| Acme Corp | N |
| ... | ... |

(Top 10 by registrant count)

### Repeat Attendees
N unique attendees also attended a prior event.
(Deduplicated by email from interaction-level data)
```

Demographics from `get_attendee_demographics` are a sample of N registrants — always state the sample size when reporting percentages from that tool. Use `get_registration_breakdown` for whole-event totals.

### Series Branch

```
## Series Audience Profile — [Series Name]

### Qualified Attendees (2+ sessions)
- Total: N attendees
- Common seniority: ...
- Common companies: ...

### Loyal Attendees (3+ sessions)
- Total: N attendees
- Common seniority: ...
- Common companies: ...

### Recommendation
1-2 sentences on who to invite to advisory boards or target in the next campaign.
```

When `truncated=true` on `get_series_engagement`, add: "Based on a scan of N registrants; the full series may have more."

**Privacy:** Show aggregate counts only. Individual names, emails, titles from `list_repeat_attendees`, `list_series_loyal_attendees`, or `get_series_engagement` are shown only when the user explicitly requests them. If shown, label: "Contains individual attendee details. Internal use only."

All output is inline markdown tables and text — no artifacts, no charts.
