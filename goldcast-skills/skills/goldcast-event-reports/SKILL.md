---
name: goldcast-event-reports
description: "Builds a polished, structured Goldcast post-event report for one event, two events side by side, or many events across a timeframe, in Standard, Executive, Sales or Marketing style. Covers registered vs. attended and attendance rate, audience by seniority and top companies, engagement, Q&A themes and poll responses, and 3 data-backed recommendations. Delivered inline in chat or as a shareable artifact. Use whenever someone asks \"how did the event / webinar / these events do?\", wants a post-event recap, event performance report, event scorecard, event comparison (\"Q3 vs Q4\", \"this year's vs last year's\"), a quarterly or monthly roll-up of events, a leadership summary, a sales follow-up view of an event, or content-repurposing ideas from an event, even if they never say \"report\". Goldcast data only (no CRM or pipeline attribution). Read-only. Not for live/in-progress monitoring, or for creating or editing events."
license: "proprietary"
---

# Goldcast post-event report

Turns Goldcast event data into one report that answers the question marketers actually have after an event: **did the right people show up, did they engage, what did they ask, and what should we do next?**

Read-only. This skill never creates, edits or registers anything.

Companion files (read when the step says so):
- `references/data-contract.md`: tool→field mapping, calculation rules, JSON shape, Q&A theming. **Read before building any report.**
- `references/report-styles.md`: what each style emphasizes, how sections are ordered, and how the Sales named list is built.
- `references/colors.md`: how to read the user's color request (hex codes or color names) and apply it.
- `assets/report-template.html`: the artifact template. Do not edit its CSS or JS; only fill in the data.
- `MCP-GAPS.md`: what Goldcast doesn't expose yet, and what this version deliberately leaves out. Use it to answer "why isn't X in the report?".

---

## Required content (every report, every style)

1. Registered vs. attended and attendance rate
2. Audience breakdown by seniority, plus the companies that registered most
3. Engagement activity (chats, Q&A, polls, CTA clicks), Q&A themes and poll responses
4. Exactly 3 actionable recommendations, each tied to a number in the report

Styles change order and emphasis. They never remove a section. If data for a section is missing, keep the section and say why in one plain sentence.

## Non-negotiables

- **Never fabricate.** No invented numbers, themes, quotes, polls, companies or people. If something can't be retrieved, say so in the report. `null` means "not available", `0` means "recorded as zero".
- **Label what is inferred.** Seniority is inferred from job titles by Goldcast. Attended counts after internal removal are estimates.
- **Follow the chosen style's section order** and the delivery method the user picked.
- **Report tool failures** in the Data notes. Don't silently skip a section or swap in a different source.
- **Protect people.** Standard, Executive and Marketing reports use aggregate counts only; show individual names, emails or titles there only if the user explicitly asks. **Sales style always includes a named follow-up list** (see "Sales style specifics"), and marks it internal-use only. Never include credentials, tokens or API keys that appear in any data.
- If the user asks to skip something ("just the table", "no charts", "skip Q&A"), do exactly that and say what was left out in one line.

## Step 0: Connection check

Call `get_current_user` first. It returns the user's email (its domain is used for internal-traffic exclusion) and organization.

If any Goldcast tool returns a connection error, authentication failure or no response (as distinct from an empty result), stop and say:

> "It looks like the Goldcast connection isn't active for this session. To use this skill, your administrator needs to enable the Goldcast MCP. Once it's connected, I can pull event data for you."

Don't retry in a loop, don't return a raw tool error, and don't continue with partial tools.

## Step 1: Pick the mode

| The user says | Mode |
|---|---|
| One event named or described ("how did the Q3 Product Launch do?") | **single** |
| Two events, or "vs", "compared to", "against", "last year's", "the previous one", "before and after" | **compare** (exactly 2) |
| A date range or period ("Q3", "last 90 days", "since March", "this year"), a series, "all our webinars", "last 5 events" | **trend** (2+ events over time) |

If the mode is unclear, ask one short question. Compare with 3+ named events is **trend**. Compare is always A (earlier / baseline) vs. B.

## Step 2: Resolve the events

Use Goldcast terms in tool calls; use the user's words in replies. "Webinar", "event", "session" and "broadcast" mean different things in Goldcast: an **event** (what the user usually means) can contain one or more **broadcasts/sessions** and can belong to a **series**. For "how did the series do", treat the series as one unit and list its events beneath it.

**single / compare**
1. `search_events(query=<name>, upcomingOnly=false, limit=10)`. Past events are excluded by default, so always pass `upcomingOnly=false`. Later tools need the event **UUID** from these results, not the short numeric id.
2. 0 results → "I couldn't find an event matching '…'. Can you double-check the name?" and stop.
3. More than one plausible match → show a numbered list (title, date, workspace) and let the user pick. Never guess.
4. "vs the previous one": resolve it explicitly and show its title and date before using it; don't assume the prior event is comparable.

**trend**
`search_events` has no date filter. With `upcomingOnly=false` it returns events **newest first** (ordered by `-startTime`), so find the window by offset:
1. `search_events(upcomingOnly=false, limit=1)` → read the total count in the response. The first result is the most recent event.
2. Binary-search `offset` using `limit=1` calls until you locate the first event on or before the **end** date (≈10 calls for ~1,000 events).
3. Page forward (increasing offset) with `limit=100` — events get older as offset grows — until `startTime` falls before the **start** date. Once you know the starting offset and the span, request the pages in parallel (offsets in steps of 100) instead of one after another. Add `workspaceId` (from `list_workspaces`) if the user named a workspace, and `eventType` if they asked for webinars only.
4. Remove from scope: events not yet ended, and likely tests or non-events (titles containing test, dry run, rehearsal, prep, copy of, demo, all hands, or nonsense strings), plus events with 0 registrations. Tell the user what you removed and why in one line.
5. If more than 8 events remain, show the list and ask for a quick confirm before pulling. If more than 20 remain, ask the user to narrow the window or confirm a batched run (comparison calls take at most 20 events).

## Step 3: Ask only what's missing (one question set, max 2 questions), and read any color request

Ask about **style** only if the user didn't say one and the cue isn't obvious (see `references/report-styles.md`, "Choosing a style"). Ask about **delivery** only if it hasn't been chosen earlier in this conversation. Use the tappable-options tool (`ask_user_input_v0`) when available; otherwise one plain-text question. Combine both into one prompt.

- Style: Standard · Executive · Sales · Marketing
- Delivery: **Inline** in this chat · **Artifact** (a designed page you can revisit and share)

**Colors are never a question.** If the user gave hex codes ("use #0A7B5C and #F2A900") or a color word ("make it green", "blue accents"), apply them as described in `references/colors.md`. If they didn't, use the Goldcast default (orange and purple). Only ask if they say "use our brand colors" without giving values: ask for the hex codes in one line, and use the default meanwhile.

Rules: if the user says "whatever" or has no preference, use Standard and Artifact. Reuse the style, delivery and color choices for later reports in the same conversation unless the user changes them. Never ask for what the user already said ("exec summary" = Executive; "give me a link / page" = Artifact).

## Step 4: Pull the data (in parallel)

Post one line first: "Pulling data for [event name(s)]…". For 10+ events: "Retrieving N events. This may take a moment."

**Always run independent calls in parallel.** Send every call that doesn't need another call's result in the same turn, never one at a time. That covers every lookup in the table below, every event, every activity-type pass and every page after the first. Only run a call after another when it needs that call's output: the event UUID from `search_events` before anything else, the first page's `totalCount` before the remaining pages, and the binary-search steps in trend mode (each depends on the last). Cap a single batch at about 10 calls; if there are more, send them as consecutive batches. If a call in a batch fails, retry just that call once, then follow the fallback below. Don't redo the calls that succeeded.

Read `references/data-contract.md` for exact fields.

| Tool | For | Notes |
|---|---|---|
| `get_event_comparison(eventId="id1,id2,…")` | registered, attended, rate, engagement breakdown (counts) | One call for all events (≤20). Pass explicit IDs. It may also return prior events; ignore any row whose event isn't one you asked for. |
| `get_event(eventId)` | title, dates, workspace, series | Titles from the comparison tool are often blank. |
| `get_registration_breakdown(eventId, fetchLimit=5000, topCompaniesLimit=15)` | seniority, companies | One per event. |
| `list_engagement_activities(eventIds=[<one id>], activityTypes=["QNA"] then ["POLLS"], limit=100)` | Q&A text, poll responses (add `"CHATS"` for Sales and Marketing, and `"SURVEY"` for Sales: it feeds each person's drawer) | One event per call. **Each call is one page of ≤100 users, each with ≤100 items per activity list: page users with `offset` until `totalCount` is reached, page each page's activities with `activityOffset` while `activityHasMore` is true, then reconcile with the comparison counts.** Procedure in `data-contract.md` §5a. |
| `list_registrants(eventId, search="<domain>", limit=1)` | internal registrant count (total count in the response) | One per internal domain per event. Skip if the user said "include internal". |
| `list_repeat_attendees(eventId, priorEventsCount=5, limit=100)` | repeat attendees for the named follow-up list and account view | **Sales style only.** Single/compare: each event. Trend: only the 3 largest events. |

Do not use `get_attendee_demographics` for whole-event numbers (it covers a single page); `get_registration_breakdown` scans up to 5000 registrants.

**Tool names.** The names above are the ones on the current Goldcast connector. If your session shows differently prefixed or older names (for example `analytics_engagement_data`, `event_search`), use the closest match by purpose and note it in the Data notes. Pass event UUIDs, not short ids, and take response field names from the actual response, not from this document.

If a tool fails, don't loop: apply the fallback in `data-contract.md` §5, record it in `notes.flags`, and keep going.

## Step 5: Compute

Apply the rules in `references/data-contract.md` §3 exactly: attendance rate, registered reconciliation, internal exclusion and estimates, sample flags, excluded empty events, total interactions. Cluster Q&A with §5.

Data-quality flags to surface (Data notes) whenever true: internal share over 30% on any event; engagement pulled in part (cap hit, or collected counts below the comparison tool's counts); Q&A/poll retrieval failed or partial; audience mix is a sample; registered counts differ between tools by more than 5%; events excluded for 0 registrations; seniority "Unknown" exceeds 25% of registrants.

## Step 6: Write the story

- **Headline**: one sentence that answers "how did it do?" using numbers (rate, change, one audience fact).
- **Insights**: 3–5 findings (3 max for Executive). Each must trace to a number. Prefer contrasts: A vs. B, early vs. late events, Director+ share, theme concentration.
- **Exactly 3 recommendations.** Each has: a title; the evidence (a specific number from this report); the action (concrete, doable in the next event cycle, naming a channel/format/timing/segment); and the metric to watch. Not generic advice ("promote more"). If the data is too thin to support three evidence-backed actions (e.g., 0 attendees, no engagement data), make the weakest one about fixing the data gap and say that is why. Tune the flavor to the style (see `report-styles.md`).
- Compare mode: describe differences, not just numbers. Say what changed and the most likely driver the data supports, framed as a hypothesis not a fact.
- Trend mode: call out the best and worst event, the direction of attendance rate over time, and any series or format pattern.

## Step 7: Deliver

### Inline
Use this when the user chose Inline.
- Lead with the headline sentence, then a compact KPI table (columns per event in compare mode; a per-event table in trend mode).
- Follow the section order for the chosen style (`report-styles.md`). Use short markdown tables for audience, engagement and polls; bullets for Q&A themes.
- Include visuals if your client has an inline charting/visualization tool, using the user's accent colors for series fills when they gave any: read that tool's guidance first (chart and data-viz modules) silently, then render the widget. At most 3 widgets: (1) registered vs. attended, (2) seniority mix (a donut for a single event, a paired bar for compare), (3) engagement mix. Interleave each widget between prose, never stacked back to back, and don't narrate the tool. If no charting tool is available, use the markdown tables only. Skip visuals only if the user asked for text only.
- Executive inline: under ~250 words plus one table; recommendations before the detail.
- End with the Data notes section ("Read before quoting these numbers"), then one follow-up offer.

### Artifact
Use this when the user chose Artifact. The report is a fixed template, so the layout is identical every time; you only provide data.
1. Read `assets/report-template.html` (resolve the path relative to this SKILL.md).
2. Build the JSON per `references/data-contract.md` §2 (set `meta.accent` and `meta.accent2` from the user's colors; leave them out for the default). Write it with a script, not by hand-pasting: validate that it parses, then replace every `<` with `\u003c`.
3. Copy the template to `/mnt/user-data/outputs/<slug>.html`, replacing `__REPORT_DATA__` with the JSON and `__REPORT_TITLE__` with the HTML-escaped title. Do not change anything else in the template.
4. Sanity check before publishing: JSON parses; exactly 3 recommendations; events are date-ordered; no `null` where a number was retrieved; every `notes.flags` item you identified is present.
5. Publish with the Artifact tool (`file_path`, a clear `title`, favicon 📊). It's a static page: don't declare runtime capabilities, and don't use browser storage. Publishing is the delivery step, so don't also call `present_files` for it.
6. In chat, give the link plus 2–3 lines: the headline sentence and anything the user must know before sharing (estimates, missing sections).
7. If the Artifact tool is unavailable, say so in one line and offer the inline version instead.

### Sales style specifics
Sales reports always include a **named follow-up list** of people to contact, plus a short account view. Build it per `references/report-styles.md` ("Sales"): name, title, company, email, why now, event, suggested next step, ranked into Priority 1 (contact now), 2 (this week), 3 (nurture). Show a list of 5 users per priority 1, 2, and 3 with recorded activity, up to 100 rows, and say how many were left out if there are more. Remove internal-domain people IF prompted to do so by the user. Always add the line "Contains individual attendee details. Internal use only." (the artifact adds it automatically).

Attendance caveat: Don't present anyone as having attended unless the data shows it.

### Marketing style specifics
- Pipeline block is Goldcast-only engagement proxies. Never state revenue or "influenced pipeline". Say so in the block.
- Repurposing ideas come from Q&A themes, poll results and chat/CTA activity. Don't pull transcripts.

## Left out on purpose

This version drops report parts that came back blank in test runs. Don't add them back, don't show empty placeholders for them, and don't mention them unless the user asks (then point to `MCP-GAPS.md`):

- Engagement per attendee, engagement rate, average watch time (KPI tiles, stat rows, trend-table columns)
- Prior-event benchmarks and "vs. benchmark" comparisons (so no `event_count=5` call)
- Repeat-attendee metrics outside Sales style (repeat share, repeat-company markers)
- Transcript highlights and transcript-based repurposing

Everything else stays, and a section that has no data still follows the "keep the section, say why" rule.

## Step 8: One follow-up

End with exactly one offer matched to what wasn't shown: Inline → "Want this as a shareable artifact?"; compare → "Want the same view for [another event]?"; single → "Want me to compare this with your previous event?"; Standard → "Want an Executive or Sales version?"; Sales → "Want this list as a CSV for your sequencing tool or CRM import?". Don't list several.

---

## Data dictionary (resolve the user's words)

| User says | In Goldcast | Handling |
|---|---|---|
| Event, webinar, program | Event (type Webinar / Conference) | The unit of the report. |
| Session, track | Broadcast within an event | Per-session metrics are not available (see MCP-GAPS #18). |
| Series | Series | Treat as one unit; list its events beneath it. |
| Registered, signups | Registrants (excludes staff and speakers in the demographic tools) | Never include waitlist. |
| Attended, showed up, live attendees | `attendance.total` (deprecated `totalAttended` still emitted) | **Unreliable** — always caveat as approximate. Never use in calculations or headlines without the caveat. |
| Attendance rate, show rate | `attendanceRate` from `get_event_comparison` | MCP returns a decimal (0.0–1.0); multiply by 100 for the report JSON (template expects 0–100). Do NOT compute from attended ÷ registered — the attended count is unreliable. If `attendanceRate` is missing, say unavailable. |
| Engagement | Chats, Q&A, polls, CTA clicks, resource clicks, survey | Goldcast has no single engagement score. Show the activity counts only. Don't invent a composite, don't show Goldcast's quality rating or a "Data quality" row, and don't add a line explaining that there is no single engagement score. |
| Seniority | Inferred by Goldcast from job title (C-Level, VP, Director, Manager, Individual, Other, Unknown) | "Director+" = Director + VP + C-Level. |
| High-intent | Derived | Director+, asked a question or voted, or intent language in Q&A. Not a Goldcast field. |

Disambiguation: if "attended" or "participants" is unclear, show registered count and attendance rate together (attended count is unreliable — caveat it as approximate if shown at all). If "engagement" is used loosely, give the full engagement view. If a "top-performing" ranking is requested, rank by attendance rate and say that's the basis, or by total interactions if the user said engagement.

## Known tool issues (re-test periodically; observed 2026-10-13)

- `list_engagement_activities` returns one **anonymous** row (`anonymous: true`, no user id or email) that combines all unattributed chat and Q&A. It counts toward totals but is not a person: use its text for themes, never list it as an attendee. If most or all Q&A and poll rows are anonymous, say Q&A/polls can't be split by person or company. Older versions of this tool failed with `users.0.user_id: Input should be a valid string`; if you see that, retry once per activity type, then use `list_repeat_attendees` as a partial fallback (returning attendees only); otherwise report Q&A/polls as not retrievable.
- `get_event_comparison` may return empty `title`s and will include placeholder or future events when called without IDs. Always pass explicit IDs.
- `list_repeat_attendees` returns interaction-level duplicates and may return `"0"` placeholders for `question_text` and `poll_response`. De-duplicate by email; treat `"0"` as no data.
- `get_registration_breakdown` may return the full company list even when `topCompaniesLimit` is small; trim it yourself.
- `search_events` has no date filter, sorts newest first (`-startTime`) when `upcomingOnly=false`, and may include tests.

## Before delivering, verify all

- [ ] Called `get_current_user`; connection was healthy
- [ ] Resolved every event to exactly one match (or the user chose from a list)
- [ ] Mode, style, delivery method and colors match what the user asked for or chose
- [ ] Registered, attended and rate are present for every event (or marked unavailable), with consistent numbers
- [ ] Seniority breakdown and top companies are present, labeled as registrants
- [ ] Engagement, Q&A themes and poll responses present, or an explicit reason given
- [ ] Exactly 3 recommendations, each citing a number from this report
- [ ] Nothing fabricated; estimates and samples labeled; internal exclusion stated
- [ ] No individual names, emails or titles outside Sales style unless explicitly requested; Sales style has its named list and the internal-use notice
- [ ] Data notes include every applicable flag and tool failure
- [ ] Artifact: JSON parsed, `<` escaped, template untouched, published via Artifact tool. Inline: at most 3 visuals, interleaved with prose
- [ ] Exactly one follow-up offered

## Examples

**Single, no style given.** "How did the Fall Product Webinar do?" → `search_events` returns one match → ask style + delivery in one prompt → pull data in parallel → headline: "The Fall Product Webinar drew 496 registrants and 186 attended (37.5%); Director+ made up 31% of registrants and chat carried most of the interaction." → three recommendations → Standard report.

**Compare.** "Compare our Spring and Fall webinars, exec style, as an artifact." → resolve both → no questions needed → Executive order (actions first) → artifact link + headline.

**Trend.** "How did our webinars do in Q3?" → date-window search → show removed events and the confirmed list of 9 → blended attendance, best/worst event, rate trend chart, aggregated audience, rolled-up Q&A themes.

**Sales.** "Who should SDRs follow up with from the Fall webinar?" → Sales style → ranked named list (Priority 1: Director of Demand Gen at Acme Co, attended both events, asked about CRM sync, with their email and a suggested next step) plus an account view, marked internal-use only. Offer a CSV as the follow-up.

**Engagement tool fails.** `list_engagement_activities` errors → retry per activity type → still fails → report attendance and audience in full; Q&A and polls sections stay and read: "Q&A and poll detail couldn't be retrieved for this event (Goldcast data tool error). Attendance and audience figures are unaffected." Recommendation 3 addresses the data gap.

**Ambiguous event.** "How did our summit do?" with three matches → numbered list, wait for the user's pick.

**Not found.** "How did the Denver Leadership Forum do?" → no results → "I couldn't find an event matching 'Denver Leadership Forum'. Can you double-check the name?" → stop.

**Out of scope.** "Which of these events created pipeline?" → "I can show Goldcast engagement signals (Director+ share, companies with 2+ registrants, high-intent questions), but pipeline and CRM attribution aren't available from this data, so I won't state it." Then deliver the Marketing-style signals.
