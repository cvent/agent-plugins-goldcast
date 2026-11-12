---
name: goldcast-analytics-query
description: "Answers ad-hoc analytics questions across Goldcast events. Do NOT use for full event reports, series trends, or audience-only breakdowns."
license: "proprietary"
---

# goldcast-analytics-query

Answer ad-hoc, cross-event analytics questions by selecting and combining the right Goldcast data tools. This skill handles focused questions ("how many people registered for X?", "compare engagement across these events") — not full reports or series-level analysis.

## Orchestration

Execute sequentially:

1. **Classify the question.** Determine which data the user needs:
   - **Registration** counts (how many signed up) → `mcp__Goldcast__get_registration_breakdown`
   - **Attendance** counts (how many showed up) → `mcp__Goldcast__get_event_comparison` includes the requested target event and its prior/comparison events in single-event mode. Use the target's `attendanceRate` directly; `attendance.total`/`totalAttended` is approximate, and use `get_registration_breakdown` for registration totals.
   - Engagement details (Q&A, polls, chat) → `mcp__Goldcast__list_engagement_activities`
   - Audience composition (seniority, company, title) → `mcp__Goldcast__get_attendee_demographics` and/or `mcp__Goldcast__get_registration_breakdown`
   - Cross-event comparison → `mcp__Goldcast__get_event_comparison`
   - Multiple dimensions → combine tools as needed

2. **Resolve events.** If the user names events by title, call `mcp__Goldcast__search_events(upcomingOnly=false)` to get UUIDs. Past events are the common case — `upcomingOnly` defaults to `true`, so always pass `false` for historical lookups. If multiple matches, show candidates and ask the user to pick. If the user says "recent events" without names, call `mcp__Goldcast__get_event_comparison(eventCount=5)` with no `eventId` to get the 5 most recent org-wide events.

3. **Fetch data.** Call the selected tools in parallel where possible:
   - `mcp__Goldcast__get_event_comparison(eventId=<uuid>, eventCount=5)` — returns up to `eventCount` events; in single-event mode the requested target is first, followed by prior events, and is retained when truncating. With multiple event IDs or no event ID, the last `eventCount` backend events are returned. `attendanceRate` is a decimal `0.0–1.0`; multiply by 100 for display. `totalRegistered` and `attendance.total`/`totalAttended` are **unreliable** (may be zero or inaccurate even when nonzero) — use `get_registration_breakdown` for registration totals, and always caveat attended counts as approximate. `title` is often blank — get event names from the user's input or `mcp__Goldcast__search_events`.
   - `mcp__Goldcast__get_registration_breakdown(eventId=<uuid>, fetchLimit=5000, topCompaniesLimit=15)` — whole-event counts by seniority/company/title.
   - `mcp__Goldcast__get_attendee_demographics(eventId=<uuid>)` — paginated sample (up to 100 per page), NOT event totals. Always state sample size. Takes a single `eventId`, not a list.
   - `mcp__Goldcast__list_engagement_activities(eventIds=[<uuid>], limit=100)` — paginate users with `offset` until all collected (max 100 per page); within each page, repeat the call with `activityOffset=nextActivityOffset` while `activityHasMore` is true (each user's Q&A, chat and poll lists hold 100 per call).

4. **Synthesise.** Answer the user's question directly. Lead with the number or comparison they asked for, then supporting context. Do not produce a full report — answer the question.

## Tool References

| Tool | Purpose |
|---|---|
| `mcp__Goldcast__search_events` | Resolve event name → UUID; `upcomingOnly=false` for past events |
| `mcp__Goldcast__get_event_comparison` | Attendance rates, engagement scores, cross-event benchmarks |
| `mcp__Goldcast__get_registration_breakdown` | Whole-event registration counts by seniority, company, title |
| `mcp__Goldcast__get_attendee_demographics` | Paginated sample of registrant demographics (NOT event totals) |
| `mcp__Goldcast__list_engagement_activities` | Per-attendee Q&A, chat, poll, survey data with timestamps |
| `mcp__Goldcast__create_error_report` | Report terminal errors when `llmAction` starts with `report_` |

## Guardrails

### Policy
- **Aggregate by default.** Show counts and percentages. Individual names/emails only when the user explicitly asks — label "contains individual attendee details — internal use only."
- **No PII in error reports.** `intentSummary` and `userRequestSummary` must contain no names, emails, or user IDs.

### Capability
- **No date-range filtering.** `mcp__Goldcast__search_events` has no date filter. Do not promise "events between date A and B." If the user asks for a time range, explain that event discovery is by name or most-recent ordering only.
- **No series-level analysis.** Series tools are not in this skill's allowed-tools. Suggest using series tools directly if available.

### Operational
- **`get_attendee_demographics` is a sample.** Always clarify counts are "from a sample of N registrants." Use `mcp__Goldcast__get_registration_breakdown` for whole-event totals.
- **`list_engagement_activities` max 100 per page.** Paginate with `offset` until `hasMore` is false or all data collected.
- **`list_engagement_activities` activity lists hold 100 per call.** When `activityHasMore` is true, call again with the same arguments and `activityOffset=nextActivityOffset`, and append each user's lists. Skipping this on the anonymous row, which holds every unattributed chat, leaves chat themes covering only the opening minutes of the event.
- **`get_event_comparison` known data issues:** `title` always blank; `totalRegistered` and `attendance.total`/`totalAttended` **unreliable** — may be zero or inaccurate even when nonzero (use `attendanceRate` directly; use `get_registration_breakdown` for registration totals; always caveat attended counts as approximate); `totalEngagement` is a fixed value unrelated to actual counts — use `engagementBreakdown` fields instead.

### Data Quality
- **Deduplicate `list_engagement_activities`.** The anonymous user row (email = `anonymous`, userId = null) aggregates unattributed activity. Do not report it as an individual attendee.
- **`get_registration_breakdown` truncation.** Check `truncated` field. If true, note "based on first N registrants scanned" in the answer.

### NEVER
- NEVER produce a full multi-section event report — redirect to `goldcast-event-reports`.
- NEVER attempt series-level queries — suggest using series tools directly if available.
- NEVER promise date-range event discovery — it is not supported.
- NEVER fabricate data or interpolate between data points.

## Confirmation Gates

None — this is a read-only skill. No mutations are performed.

## Communication Contract

**Before:** "Let me look up the analytics data for [event(s)/question summary]."

**During:** If fetching multiple tools or paginating, give a brief status: "Pulling registration and engagement data…"

**After:** Deliver the direct answer. If data was incomplete or caveated, state it after the answer, not before.

## Graceful Degradation

### Hard failures (stop execution)
- **Connection/auth error** from any tool → stop immediately. Tell the user: "The Goldcast MCP connection is not active. Please check your connection and try again." Do not continue with partial data.

### Degradable failures
- `mcp__Goldcast__search_events` returns no match → ask the user for the event UUID or a more specific title.
- `mcp__Goldcast__get_event_comparison` fails → fall back to `mcp__Goldcast__get_registration_breakdown` for basic counts. Note the comparison data is unavailable.
- `mcp__Goldcast__get_attendee_demographics` fails → use `mcp__Goldcast__get_registration_breakdown` for seniority/company data (whole-event, not sample). Note the sample-level detail is unavailable.
- `mcp__Goldcast__list_engagement_activities` fails → note engagement data is not retrievable. Do not estimate.
- `mcp__Goldcast__get_registration_breakdown` truncated → include caveat: "based on the first N registrants."

### Error reporting
If a tool error body contains `llmAction` starting with `report_`, call `mcp__Goldcast__create_error_report`:
- Pass `trackingId`, `mcpErrorCode`, `failedTool` unchanged from the error body
- Write `intentSummary` and `userRequestSummary` yourself — **no PII** (no names, emails, or user IDs)
- For all other errors, use the degradation paths above

## Few-Shot Examples

### Example 1: Happy path — cross-event comparison

**User:** "Compare the Fall Product Launch and Spring Summit webinars — which had better engagement?"

**Assistant:** "Let me look up those events and compare their engagement metrics."

1. `mcp__Goldcast__search_events(query="Fall Product Launch", upcomingOnly=false)` → resolves to UUID `aaa…`
2. `mcp__Goldcast__search_events(query="Spring Summit", upcomingOnly=false)` → resolves to UUID `bbb…`
3. `mcp__Goldcast__get_event_comparison(eventId="aaa…,bbb…")` → returns per-event attendance rates, engagement scores, quality signals
4. `mcp__Goldcast__list_engagement_activities(eventIds=["aaa…"], limit=100)` and `mcp__Goldcast__list_engagement_activities(eventIds=["bbb…"], limit=100)` → per-attendee engagement detail

**Output:**

> **Fall Product Launch vs Spring Summit**
>
> | Metric | Fall Product Launch | Spring Summit |
> |---|---|---|
> | Attendance rate | 62% | 48% |
> | Avg engagement score | 34.2 | 28.7 |
> | Q&A questions | 47 | 23 |
> | Poll responses | 112 | 89 |
>
> The Fall Product Launch had stronger attendance and engagement across all metrics. Q&A participation was notably higher (2×), suggesting the topic drove more active discussion.

### Example 2: Ambiguity — vague question

**User:** "How are our events doing?"

**Assistant:** "That's a broad question — I can help narrow it down. I don't have date-range filtering, but I can show you metrics for your most recent events. Would you like me to compare your 5 most recent events, or do you have specific events in mind?"

*If user says "yeah, recent ones":*

1. `mcp__Goldcast__get_event_comparison(eventCount=5)` → returns the 5 most recent org-wide events with attendance and engagement metrics

**Output:**

> **Your 5 Most Recent Events**
>
> | Event | Attendance Rate | Engagement Score |
> |---|---|---|
> | *(titles unavailable — shown by date)* | | |
> | Oct 15, 2026 | 58% | 31.4 |
> | Oct 8, 2026 | 45% | 22.1 |
> | Sep 30, 2026 | 67% | 41.8 |
> | Sep 22, 2026 | 52% | 27.3 |
> | Sep 15, 2026 | 61% | 35.6 |
>
> Your Sep 30 event had the highest attendance and engagement. Want me to dig into any of these? I'd need the event name or UUID to pull detailed breakdowns.
>
> *Note: Event titles are not available in comparison data. Provide an event name to get full details.*

## Output Formatting

- **Lead with the answer.** The number, comparison, or finding the user asked for comes first.
- **Tables** for multi-event comparisons. Inline markdown tables, no artifacts.
- **Dates:** ISO 8601 or human-readable (e.g., "Oct 15, 2026"). Match what the data provides.
- **Numbers:** Whole numbers for counts; one decimal for rates and scores (e.g., 62%, 34.2).
- **Truncation:** If `list_engagement_activities` or `get_registration_breakdown` was truncated, state it: "Based on a sample of N registrants" or "Showing first 100 engaged attendees."
- **Data Notes:** If any tool failed or returned partial data, add a brief note at the end — not a separate section, just a parenthetical or footnote line.
