# Report styles

All four styles contain the same required content: registered vs. attended, audience (seniority and top companies), engagement, Q&A themes and poll responses, and exactly 3 recommendations. **A style changes order, emphasis, length and tone. It never drops a required section.** If a section has no data, it stays and says why.

The template's section order per style is fixed in code (`ORDER` in `assets/report-template.html`). Inline reports follow the same order.

| | Standard | Executive | Sales | Marketing |
|---|---|---|---|---|
| Reader | Whole event team | Leadership, 60-second read | Sales / SDR / AEs | Demand gen, content, field |
| Opens with | Headline + 5 insights | Headline built from numbers; max 3 insights | Headline about who is worth contacting | Headline about what content/format worked |
| Section order | Attendance → Audience → Engagement → Q&A/Polls → Actions → Notes | Actions → Attendance → Audience → Engagement → Q&A/Polls (collapsed) → Notes | **Follow-up priorities** → Audience → Q&A/Polls → Attendance → Engagement → Actions → Notes | Engagement → Q&A/Polls → **Content, pipeline signals, repurposing** → Audience → Attendance → Actions → Notes |
| Extra block | none | none | `sales` | `marketing` |
| Length (inline) | Full | ≤ ~250 words + 1 table | Full, focused on a table of accounts | Full |
| Recommendation flavor | Mixed: audience, content, ops | One line each; biggest-lever first | Follow-up actions with timing and owner role | Content, promotion and repurposing actions |

## Standard
Balanced overview. Neutral tone. Cover every section at normal depth. Recommendations should mix one audience/targeting action, one content/format action and one operational action (reminders, timing, follow-up) when the data supports it.

## Executive
- Lead with numbers: registered, attended, rate, change vs. the other event (compare mode).
- Headline pattern: "[Event] drew N registrants and N attended (X%); [one audience fact]."
- Max 3 insights. Recommendations come right after the numbers, one sentence of evidence + one sentence of action.
- Keep audience and engagement to the key shares (e.g., "Director+ = 38%"). In the artifact, Q&A and polls are collapsed under a toggle; inline, give 2–3 lines.
- No hedging paragraphs; put caveats in Data notes.

## Sales
Goal: who to contact first, what to say, and how to reach them. **Always includes a named follow-up list.**

**Named list (`sales.followUps`)**: every named person with recorded activity, up to 100, each with `priority`, `name`, `title`, `company`, `email`, `signal` (why now), optional `quote`, `event`, and `action` (suggested next step). Sources: `list_registrants` (name, email, company, title, looked up by the email from the engagement/repeat data), `list_engagement_activities` (who asked, voted, chatted, with question text), `list_repeat_attendees` (who attended 2+ events).

Who qualifies (because Goldcast has no per-person attended flag, only people whose activity proves they were there are listed):
- asked a Q&A question, voted in a poll, or chatted, **or**
- is a repeat attendee (attended 2+ events in the report or the prior-5 window).

Ranking:
- **Priority 1 (contact now)**: high-intent language (pricing, demo/trial, switching, a described project or pain point, asks for follow-up, integration/implementation question), **or** Director+ title with any activity, **or** repeat attendee with Director+ title.
- **Priority 2 (this week)**: Manager-level or above with a question or poll vote; repeat attendees; two or more contacts from the same account.
- **Priority 3 (nurture)**: everyone else on the list.
Break ties by seniority (C-Level, VP, Director, Manager), then by number of activities. Seniority per person comes from the title using the same buckets Goldcast uses; if a title is blank, leave seniority out of the ranking reason rather than guessing.

**Engagement drawer (`activity`)**: in the artifact, clicking a person's row opens a drawer listing how they engaged. The source is `list_engagement_activities` (one `users[]` row per attendee, each with `qna`, `chats`, `polls` and, if present, survey responses). Fill `activity` with one entry per recorded action: `type` (`Poll response`, `Question`, `Survey response`, `Chat`, or `Repeat attendance` from `list_repeat_attendees`), the `event` it happened at, and `text`: the poll as "<poll question> → <option they picked>", the question as asked, the survey answer as given, the chat message, or "Also attended <event name>". Use only what the data returned, in the person's own words; never summarize or invent. Read the real field names off the first response.

**Who appears in the list**: every named person with at least one recorded action (question, poll answer, survey response or chat), plus repeat attendees, ranked by the priority rules below. Show up to 100 rows; if there are more, say how many were left out. The anonymous row is never a person.

**Not in the drawer**: CTA clicks and resource downloads. Goldcast reports those as event totals only, not per person, and `list_engagement_activities` has no activity type for them. Don't add a CTA or resource section, and don't infer them for a person. Add one line to the Data notes gaps: "CTA clicks and resource downloads are available as event totals only, not per person." If a person's activity text isn't available, leave `activity` out: the drawer then shows the counts and the "why now" line instead. People whose Q&A was anonymous can't be matched, so don't attach anonymous rows to anyone.

Rules:
- Remove internal-domain people (the user's own domain and any the user named). Never list staff or speakers.
- `signal` states facts only ("Attended both events; asked about CRM sync"). `quote` is the person's own words, at most 25 words, only when it adds the reason. Don't paraphrase their words as a quote.
- `action` is specific and short ("Personal email within 24h referencing CRM sync question; offer integrations demo"). Never claim a person is interested, qualified, or ready to buy beyond what they said.
- Add a list note: "Attendance is inferred from activity; Goldcast doesn't expose a per-person attended flag, so silent attendees and no-shows can't be told apart."
- If no one qualifies, keep the block and say why. Do not pad the list with registrants.
- Emails are shown so the list is usable for outreach. The report carries the line "Contains individual attendee details. Internal use only."

**Account view (`sales.priorityAccounts`)**: accounts ranked by signal strength: Director+ attendee, 2+ events, 2+ contacts, high-intent question. Include `seniorContacts`, `eventsAttended` and a suggested action.

No CRM data exists in Goldcast, so never say "pipeline", "influenced" or "opportunity". Say "attended", "asked", "voted".

Recommendations: who to contact within 48 hours, which question or topic to reference, and which people to invite to the next event.

## Marketing
Goal: what worked, what signals pipeline, what to reuse.
- `marketing.contentSignals`: poll participation, Q&A volume per attendee, chat volume, CTA and resource clicks. Add a one-line "read" for each ("Strong: 63% of attendees voted").
- `marketing.pipelineSignals`: Goldcast-only proxies. Director+ share, number of companies with 2+ registrants, CTA click count, number of high-intent questions. Label this block "Pipeline signals (Goldcast data only)". Never state pipeline dollars.
- `marketing.repurpose`: 3–5 concrete assets, each tied to a source: a Q&A theme with the most questions → FAQ post or follow-up webinar; highest-voted poll → data post; a strong segment → targeted replay email. Base every idea on Q&A, poll and chat/CTA data; don't use transcripts.
- Recommendations: content topic, promotion/timing change, repurposing action.

## Choosing a style when the user doesn't say
- "How did the event do?" with no audience cue → Standard.
- "Give me the quick version / for my VP / for the leadership update" → Executive.
- "Who should we follow up with / for sales / SDR list" → Sales.
- "What should we repurpose / content performance / for the content team" → Marketing.
- If it's unclear and the user hasn't been asked yet this conversation, ask once (see SKILL.md, step 3).
