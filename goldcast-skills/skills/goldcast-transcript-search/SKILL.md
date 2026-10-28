---
name: goldcast-transcript-search
description: "Searches Goldcast event transcripts for a topic or keyword and returns timestamped quotes. Do NOT use for event reports or analytics."
license: "proprietary"
---

## Orchestration

1. **Identify events.** The user must name at least one event. If they give a UUID, use it directly. If they give a name, resolve it:
   - Call `mcp__Goldcast__search_events(query="<name>", upcomingOnly=false)` — past events are the common case for transcript search.
   - If multiple matches, show candidates and ask the user to pick.
   - If zero matches, ask the user to check the event name or provide a UUID.
   - You need 1–10 event IDs. If the user wants more than 10, explain the limit and ask them to narrow down.

2. **Search transcripts.** Call `mcp__Goldcast__search_transcripts(eventIds=[...], query="<topic>")`.
   - `query` must be 2–256 characters.
   - The tool searches every recorded session across the given events and tags each hit with its broadcastId.

3. **Handle truncation.** If `truncated` is true, narrow the search:
   - Reduce `eventIds` to fewer events, OR
   - Make the `query` more specific.
   - There is NO broadcast-level filter on `search_transcripts`.

4. **Present results.** For each hit, format as:

   **[HH:MM:SS]**
   > "[exact quote]"
   Session: [broadcast name or ID]

   `search_transcripts` returns timestamp and text per segment — speaker identity is not available. Do NOT invent or guess speaker names.

   If the user asked a question (e.g. "what did they say about pricing?"), synthesise an answer from the hits and cite timestamps.

5. **(Optional) Show sessions.** If the user wants to know which sessions exist, call `mcp__Goldcast__list_broadcasts(eventId=<uuid>)` to list them. This helps the user pick events more precisely but does not filter the transcript search.

## Tool References

| Tool | Purpose |
|---|---|
| `mcp__Goldcast__search_events` | Resolve event name → UUID |
| `mcp__Goldcast__search_transcripts` | Search transcript segments by keyword |
| `mcp__Goldcast__list_broadcasts` | List sessions for an event (informational) |
| `mcp__Goldcast__create_error_report` | Report terminal errors when `llmAction` starts with `report_` |

## Guardrails

**NEVER:**
- Invent timestamps, speaker names, or quotes — show only what the API returned.
- Promise "search across all events" — the tool requires explicit eventIds (1–10).
- Fabricate a broadcastId filter — `search_transcripts` has no broadcast-level filter parameter.

**Policy:** If the user does not specify an event, ask them to name one. "Search my transcripts" without an event is not actionable.

**Data quality:** If 0 results are returned, suggest:
- Broadening the keyword (shorter or more general).
- Checking whether the session was recorded (not all broadcasts have transcripts).
- Verifying the event name resolved to the intended event.

## Confirmation Gates

None — this is a read-only workflow.

## Communication Contract

**Before:** "I'll search the transcripts of [event name(s)] for '[topic]'."

**During:** If resolving event names, say which events were found. If the search returns many hits, summarise the count before presenting.

**After:** Present the hits. If the user asked a question, answer it with citations. End with: "Want me to search for a different topic or in other events?"

## Graceful Degradation

**Connection/auth failure from any tool → hard stop.** Tell the user: "The Goldcast MCP connection is not active. Please check your connection and try again." Do not continue with partial data.

| Tool | Failure | Action |
|---|---|---|
| `mcp__Goldcast__search_events` | No matches | Ask user to check the event name or provide a UUID |
| `mcp__Goldcast__search_transcripts` | Empty results | Report "no transcript matches found" with suggestions (see Guardrails) |
| `mcp__Goldcast__search_transcripts` | Error | Report failure; if error body has `llmAction` starting with `report_`, call `mcp__Goldcast__create_error_report` — pass `trackingId`, `mcpErrorCode`, `failedTool` unchanged; write `intentSummary` and `userRequestSummary` with no personal data (no names, emails, or user IDs). For other errors, tell the user the search failed and suggest retrying. |
| `mcp__Goldcast__list_broadcasts` | Fails | Skip session listing; note it. The core search still works without it. |

## Few-Shot Examples

### Happy path

**User:** "What did the speakers say about AI pricing in my Q4 Product Launch event?"

**Assistant:** "I'll search the transcripts of your Q4 Product Launch event for 'AI pricing'."

1. `mcp__Goldcast__search_events(query="Q4 Product Launch", upcomingOnly=false)` → finds event `3f2c9a1e-...`
2. `mcp__Goldcast__search_transcripts(eventIds=["3f2c9a1e-..."], query="AI pricing")` → 3 hits

**[00:14:32]**
> "The AI pricing model is per-seat, starting at $50 per month for the base tier."
Session: Main Stage

**[00:22:15]**
> "We looked at AI pricing across competitors and found our model is 30% below market average."
Session: Main Stage

**[01:05:48]**
> "For enterprise AI pricing, we offer volume discounts starting at 100 seats."
Session: Q&A Panel

**Summary:** The transcripts mention a per-seat AI pricing model starting at $50/month, positioned 30% below market average, with enterprise volume discounts at 100+ seats.

Want me to search for a different topic or in other events?

### Ambiguity — event name instead of UUID

**User:** "Search for 'customer onboarding' in our recent webinars"

**Assistant:** "I need to know which events to search — transcripts require specific event IDs (up to 10). Let me look for your recent webinars."

1. `mcp__Goldcast__search_events(query="webinar", upcomingOnly=false)` → 4 matches:
   - "Spring Onboarding Webinar" (2026-03-15)
   - "Product Demo Webinar" (2026-04-02)
   - "Customer Success Webinar" (2026-04-20)
   - "Q2 Launch Webinar" (2026-05-10)

"I found 4 webinars. Want me to search all 4 for 'customer onboarding', or would you like to narrow it down?"

## Output Formatting

- Timestamps: `[HH:MM:SS]` format as returned by the API.
- Quotes: Exact text in blockquotes — never paraphrase or truncate without noting it.
- Session: Name or broadcast ID after each quote.
- If the user asked a question, provide a synthesised answer at the end with timestamp citations.
- If results span multiple events, group by event.
- If truncated, note: "Results were truncated. Narrow the search to see more."
