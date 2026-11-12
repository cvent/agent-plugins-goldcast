# Data contract

How Goldcast tool output maps to the report JSON that `assets/report-template.html` renders, plus the calculation rules. Read this before building the JSON for an artifact; use the same numbers for inline reports.

## Contents
1. Tool → field mapping
2. JSON shape
3. Calculation rules
4. Colors
5. Q&A theming and intent

---

## 1. Tool → field mapping

| Report field | Source tool | Field(s) |
|---|---|---|
| name, date, type | `search_events` / `get_event` | `title`, `startTime` (date part), event type. `get_event_comparison` often returns an empty `title`; always take the title from `search_events`/`get_event`. |
| registered | `get_registration_breakdown` | `totalRegistrations` (the comparison endpoint's value may be zero) |
| attended | `get_event_comparison` | `attendance.total` (deprecated `totalAttended` still emitted). **Unreliable** — always present with the caveat "approximate, may not reflect actual attendance". Never use this value in calculations or headlines without the caveat. |
| attendanceRate | `get_event_comparison` | `attendanceRate` (decimal 0.0–1.0). Multiply by 100 and round to 1 decimal for the report JSON. Do NOT compute from attended / registered — the attended count is unreliable. If missing, say attendance rate is unavailable. |
| engagement{polls,qa,chats,cta,resource_click,survey} | `get_event_comparison` | `engagementBreakdown`. `null` means "not recorded", not zero. |
| totalEngagement | computed | Sum of the `engagementBreakdown` counts (polls + qa + chats + cta + resource_click + survey). The tool's own `totalEngagement` can disagree with its breakdown; use the sum and don't show the tool's figure. |
| data-quality notes | `get_event_comparison` | `enrichedDataQualityFlags` → plain-English entries in `notes.flags` |
| seniority | `get_registration_breakdown` | `seniorityBreakdown` → `[{label, count}]` (labels: C-Level, VP, Director, Manager, Individual, Other, Unknown) |
| topCompanies | `get_registration_breakdown` | `companyBreakdown` / `topCompanies` → `[{name, count}]`, minus the user's own company |
| internalRemoved | `list_registrants` | `totalCount` when `search=<internal domain>`, summed over domains. A registrant can match more than one domain; subtract only the sum, and say it is approximate |
| Q&A themes, poll responses | `list_engagement_activities` | see §5. Inspect the real response keys on the first call; do not assume them. |
| Sales follow-ups (Sales style only) | `list_repeat_attendees` | repeat attendees, de-duplicated by `email` (rows are interaction-level) |

## 2. JSON shape

Everything the template reads. Omit a key to hide that block; use `null` for "unavailable" so the template shows the right notice.

```json
{
  "meta": {
    "mode": "single | compare | trend",
    "style": "standard | executive | sales | marketing",
    "title": "string",
    "subtitle": "scope sentence: events, dates, how counts were derived",
    "timeframe": "string",
    "generatedOn": "YYYY-MM-DD",
    "workspace": "string",
    "internalExcluded": true,
    "internalDomains": ["example.com"],
    "audienceBase": "registrants",
    "accent": "#RRGGBB (optional, the user's main color)",
    "accent2": "#RRGGBB (optional, second series color; derived if omitted)"
  },
  "headline": "One sentence that answers 'how did it do?' with numbers.",
  "insights": ["3-5 short findings, most important first"],
  "events": [{
    "name": "", "date": "YYYY-MM-DD", "type": "Webinar",
    "registered": 0, "attended": null, "attendedIsEstimate": true, "internalRemoved": 0,
    "attendanceRate": 0.0,
    "totalEngagement": 0,
    "engagement": { "polls": 0, "qa": 0, "chats": 0, "cta": 0, "resource_click": 0, "survey": 0 },
    "seniority":  [{ "label": "Director", "count": 0 }],
    "topCompanies": [{ "name": "", "count": 0 }],
    "qaThemes": [{ "theme": "", "count": 0, "summary": "", "example": "" }],
    "qaStatus": { "note": "shown when qaThemes is missing" },
    "polls": [{ "question": "", "responses": [{ "option": "", "count": 0 }] }],
    "pollStatus": { "note": "shown when polls is empty" }
  }],
  "rollup": { "qaThemes": [{ "theme": "", "count": 0 }] },
  "sales": {
    "priorityAccounts": [{ "account": "", "signals": [""], "seniorContacts": 0, "eventsAttended": 0, "action": "" }],
    "followUps": [{ "priority": 1, "name": "", "title": "", "company": "", "email": "", "signal": "", "quote": "", "event": "", "action": "",
      "activity": [{ "type": "Question | Poll response | Chat | Repeat attendance", "event": "", "text": "" }] }],
    "note": ""
  },
  "marketing": {
    "contentSignals":  [{ "label": "", "value": "", "read": "" }],
    "pipelineSignals": [{ "label": "", "value": "", "note": "" }],
    "repurpose":       [{ "asset": "", "source": "", "why": "" }]
  },
  "recommendations": [{ "title": "", "evidence": "", "action": "", "metric": "" }],
  "notes": { "flags": [""], "gaps": [""], "sources": ["tool names used"] }
}
```

Rules for the JSON:
- Events in `events` are in **date order, oldest first**. In `compare` mode, `events[0]` is "A" (baseline) and `events[1]` is "B"; deltas read "B vs A".
- `recommendations` has exactly 3 entries.
- Percentages are numbers 0–100, not strings, and are not pre-formatted. The template computes shares from counts.
- When writing the JSON into the template, replace every `<` inside the JSON text with `\u003c` so attendee-written text can never close the script tag.
- Never put placeholder or sample values in the file. If a number was not retrieved, use `null` and say so in `notes`.

## 3. Calculation rules

- **Attendance rate.** `get_event_comparison` returns `attendanceRate` as a **decimal (0.0–1.0)**. Multiply by 100 and round to 1 decimal place for the report JSON (the template expects 0–100 scale, e.g. 80.0 for 80%). If the field is missing or null, report "attendance rate unavailable". Never compute attendance rate from attended ÷ registered — the attended count is unreliable.
- **Attended count.** `attendance.total` / `totalAttended` is unreliable. When the report needs an attended figure, show the value with the caveat "approximate" and never use it in calculations (rate derivations, internal-exclusion scaling, trend sums). If it is zero, say "attended count unavailable" instead.
- **Registered count.** Use `get_registration_breakdown.totalRegistrations` as the canonical registered count (excludes staff and speakers). `get_event_comparison.totalRegistered` may be zero or differ — if the report also shows it, flag the discrepancy but prefer the breakdown tool's figure.
- **Internal exclusion (default on).** For each internal domain, call `list_registrants(eventId, search="<domain>", limit=1)` and read `totalCount`. Internal domains = the signed-in user's email domain from `get_current_user` plus any the user names. Then:
  - `registered = registeredRaw − internalRemoved`
  - `attendanceRate` stays as reported by the tool (converted to 0–100 per the rule above; do not recompute).
  - Attended counts cannot be filtered for internal attendees. When displayed alongside filtered registered counts, label them "all-audience (incl. internal)" so the reader knows they include internal attendees. Do not use the attended count in calculations when internal exclusion is active.
  - Seniority and company counts cannot be filtered per person; if internal share ≥ 10% add a flag that the audience mix still includes internal registrants.
  - Flag any event whose internal share exceeds 30%.
  - If the user says "include internal", skip all of this and set `internalExcluded: false`.
- **Sample flag.** If `get_registration_breakdown` hit `fetchLimit` (total registrations > fetched), say the audience mix is a sample.
- **Zero / empty events.** Events with 0 registered are excluded from trend and compare math and listed in `notes.flags` (name + reason). Do not report 0% rates for them.
- **Waitlist.** Never fold waitlist counts into registered or attended.
- **Trend totals.** Sum the registered counts across events. For blended attendance rate, average the per-event `attendanceRate` values (weighted by registered count when available). Never sum attended counts — they are unreliable.

## 4. Colors

See `colors.md`. The template corrects contrast per theme, so pass the user's colors as given.

## 5. Q&A theming and intent

### 5a. Pulling the full engagement picture (pagination)

`list_engagement_activities` returns one page per call: up to 100 **users**, each with up to 100 questions, 100 chats and 100 poll answers. It pages two ways: `offset` moves through users, and `activityOffset` moves through each user's activities. One call is never the whole event. Follow this procedure for every event:

1. **One event per call, one activity type per pass.** Run `activityTypes=["QNA"]` and `["POLLS"]` as separate passes, each with `limit=100`. Add a `["CHATS"]` pass only for Sales or Marketing style (chat text is used for intent). Chat *counts* come from `get_event_comparison`, so Standard and Executive reports don't need the chat pass. Use `["SURVEY"]` only if the user asks for survey answers.
2. **Read the total from the first response** (`totalCount`). It includes the anonymous row. Send the first page of every pass (every event, every activity type) in the same parallel batch.
3. **Fetch the remaining pages in parallel.** Once a pass's `totalCount` is known, the offsets are known: 100, 200, 300… up to `totalCount`. Request all of that pass's remaining pages together (in batches of about 10), together with the other passes' remaining pages, rather than waiting for each page before asking for the next. Don't stop because one page looked short, and don't stop at the first page because the counts "look right". If a page fails, retry that page once; if it still fails, flag the pass as partial. Because pages may arrive in any order, merge them by user id or email, not by arrival order.
4. **Cap with a flag, not silently.** Stop at 5,000 users (50 calls) per pass. If the cap is hit, say so in `notes.flags` ("Q&A is based on the first 5,000 of N users") and treat themes and poll shares as a sample.
5. **De-duplicate** by user id or email across pages before counting. The anonymous row appears once; keep its text for themes but don't count it as a person.
6. **Reconcile with `get_event_comparison`.** Compare what you collected with the tool's `engagementBreakdown`: number of questions collected vs. `qa`, number of poll answers collected vs. `polls`. If you collected fewer than reported, flag it ("retrieved 31 of 39 questions") and say themes and poll shares are partial. If you collected more, use the collected numbers and flag the mismatch. Never scale or pad numbers to make them agree.
7. **Poll tallies.** Group answers by poll question text, then count answers per option label across all pages. State the number of responses behind each poll. If the option counts don't add up to the poll total, say so rather than adjusting one.
8. **Large events and many events.** In trend mode run the passes per event, not with all `eventIds` at once, so rows stay attributable to an event. For events with more than 1,000 users, tell the user it is a longer pull.

### 5b. Theming and intent

1. Drop messages from internal domains (match on the user's email). The anonymous row has no email, so it can't be filtered; note that in Data notes.
2. Read all question text, then group into 3–7 themes by meaning (not keywords). Examples: Integrations, Pricing and packaging, Getting started, Measurement and ROI, Specific feature requests, Competitor comparisons.
3. For each theme: `count` = number of distinct questions, a one-sentence `summary`, and optionally one `example` of at most 20 words, with names and companies removed.
4. Order themes by count. Put an "Other" bucket last only if it holds more than 15% of questions.
5. Polls: use the poll question text and option labels exactly as returned. If only counts or only per-user answers come back and the question text is missing, say so in `pollStatus.note` and show what exists. Never invent a question or option label.
6. **Intent signal** (Sales and Marketing styles): a question or message counts as intent when it asks about pricing, a demo or trial, switching from another tool, a described project or pain point, a request for follow-up, or integration/implementation. Rate `high` (explicit ask to talk, buy or switch), `medium` (specific implementation or pricing question), `low` (general interest).

If `list_engagement_activities` errors (see Known tool issues in SKILL.md): retry once per activity type (`QNA`, `POLLS`, `CHATS`). If it still fails, fall back to `list_repeat_attendees`, which carries `question_text` and `poll_response` for returning attendees only. Treat that as a partial view and say so, and treat `"0"` or null values as "no data", never as an answer. If both fail, set `qaStatus.note` / `pollStatus.note` to the plain reason and move on.
