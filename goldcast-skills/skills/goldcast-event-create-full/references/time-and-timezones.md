# Dates, times and timezones

Goldcast needs three things for every event: `startTime`, `endTime` and `timezone`. Most briefs give only some of them. Infer what you can, flag what you assumed, and let the confirmation summary catch mistakes.

## Contents
- Resolving the date
- Resolving the timezone
- Resolving start, end and duration
- Using the helper script
- Field formats Goldcast expects
- Showing dates and times to the user
- Conference windows
- Worked examples

## Resolving the date

Use today's date from the conversation context as the anchor.

| Input | Resolve to |
| --- | --- |
| "Nov 5", "11/5" | That date this year. If already past, next year, and flag it |
| "next Thursday" | The Thursday of next week, not the coming one. If ambiguous, say which date you picked |
| "this Thursday" | The coming Thursday. If today is Thursday, ask |
| "end of the month", "early Q1" | Too vague. Propose a specific date and mark it assumed |
| "Oct 7-8" | Two-day event: start on the 7th, end on the 8th |
| "the first week of December" | Propose Tue to Thu of that week and mark it assumed |
| Nothing | Propose a Tuesday to Thursday, 3 to 4 weeks out, and mark it assumed. Webinars rarely perform on Mondays or Fridays |

Always state the resolved weekday and date together ("Thu, Nov 5") so a wrong weekday is obvious. Take the weekday from the script's output, not from memory.

## Resolving the timezone

Use the first source that gives an answer:

1. **Stated explicitly:** "11am ET", "9:00 PT", "London time", "UTC".
2. **A place in the brief:** the host's city, the audience's region, "for our APAC team".
3. **The user's own location**, if you know it from context.
4. **Ask.** One short question, in the Step 3b round. The timezone can be edited later, but it's cheap to ask now.

Send IANA ids (`America/New_York`, `Europe/London`, `Asia/Kolkata`). Goldcast's web app shows a labeled form such as `America/New_York (GMT-04:00)` or `Asia/Kolkata (GMT+05:30)`. IANA ids usually work. If `create_event` rejects the timezone with `INPUT_ERROR`, retry once with the labeled form.

Abbreviation handling (the script maps these too):

| Written | Use | Caution |
| --- | --- | --- |
| ET, EST, EDT | `America/New_York` | Say "ET" to users. "EST" in July is wrong, and the script warns about it |
| CT / MT / PT | `America/Chicago`, `America/Denver`, `America/Los_Angeles` | |
| GMT, UK, BST | `Europe/London` | |
| CET, CEST | `Europe/Paris` | Pick the city if the brief names one (Berlin, Madrid) |
| IST | `Asia/Kolkata` | **Ambiguous** (India, Ireland, Israel). Confirm |
| CST | `America/Chicago` | **Ambiguous** (US Central, China). Confirm |
| AEST, AEDT | `Australia/Sydney` | Use `Australia/Brisbane` for Queensland (no DST) |

If the audience is global, set the event in the host's timezone.

## Resolving start, end and duration

| Situation | Default |
| --- | --- |
| Start and end both given | Use them |
| Start and duration given | End = start + duration |
| Start only, webinar | 60 minutes |
| "Quick demo", "lightning talk" | 30 minutes |
| "Workshop", "masterclass" | 90 minutes, flagged |
| Date only, webinar | 11:00 AM local, 60 minutes, flagged |
| Date only, conference, no agenda | 9:00 AM to 5:00 PM local, flagged |
| Conference with an agenda | Event start = first session start, event end = last session end |

Times in a brief are local to the stated timezone. Read 12-hour times carefully ("12:00 PM" is noon, "12:00 AM" is midnight).

## Using the helper script

Run it for every start/end pair. It handles daylight saving and warns about problems.

```bash
python scripts/iso_time.py --date 2026-11-05 --time 11:00 --tz ET --duration-min 60
python scripts/iso_time.py --date 2026-11-05 --time 09:00 --tz America/Los_Angeles --end-date 2026-11-06 --end-time 17:00
```

Output includes `startTime` and `endTime` (offset form, ready to pass to Goldcast), `timezone` (the IANA id), `weekday`, `display` (plain language, for the user) and `warnings`. Show any warnings to the user in plain language.

To show a UTC time that Goldcast returned (ending in `Z`):

```bash
python scripts/iso_time.py --utc 2026-10-22T04:00:00Z --utc-end 2026-10-22T05:00:00Z --tz America/New_York
# display: "Thu, Oct 22, 2026, 12:00–1:00 AM ET"
```

Without code execution, work out the UTC offset that applies on that specific date. US daylight time ends the first Sunday in November and begins the second Sunday in March, so the same city can have different offsets a week apart.

## Field formats Goldcast expects

- `startTime`, `endTime`: ISO 8601 with a numeric offset or `Z`: `2026-11-05T11:00:00-05:00`. No spaces, a `T` between date and time.
- Never append a label such as `(GMT-05:00)` or `EST` to a time string.
- `timezone`: the label only, for example `America/New_York`.
- `endTime` must be after `startTime`.

## Showing dates and times to the user

ISO strings are for tool calls only. Everything the user reads (questions, the summary, progress messages, the final report) uses plain language:

- Format: day of week, month, day, year, 12-hour time, timezone. For example "Fri, Feb 5, 2027, 2:00–3:00 PM ET".
- Multi-day: "Tue, Dec 8, 2026, 9:30 AM to Wed, Dec 9, 2026, 5:00 PM IST".
- US zones: say "ET", "CT", "MT", "PT", not "EST"/"EDT".
- Use the script's `display` field where possible.

## Conference windows

- Multi-day conferences: one `startTime` on day 1, one `endTime` on the last day.
- Parallel sessions may overlap in time. That's fine.
- If the agenda runs outside the event window, widen the window (after confirming) rather than squeezing the agenda.

## Worked examples

**"Webinar next Thursday at 11 ET"** (today is Wed Oct 21, 2026)
Next Thursday is Oct 29. Oct 29 is still daylight time, so the offset is `-04:00`: start `2026-10-29T11:00:00-04:00`, end `2026-10-29T12:00:00-04:00`, timezone `America/New_York`. Show it as "Thu, Oct 29, 2026, 11:00 AM–12:00 PM ET". Duration (60 min) is assumed, so flag it.

**"Summit Dec 8-9, 9:30 to 5, India"**
Timezone `Asia/Kolkata`, no DST: start `2026-12-08T09:30:00+05:30`, end `2026-12-09T17:00:00+05:30`. Show it as "Tue, Dec 8, 2026, 9:30 AM to Wed, Dec 9, 2026, 5:00 PM IST".

**"Customer webinar sometime in early November"**
No date. Propose Tuesday Nov 3 or Wednesday Nov 4 at 11:00 AM in the user's timezone. Offer one concrete choice, mark it assumed, and let the summary confirm it. Nov 3 is after daylight saving ends (Nov 1), so the offset differs from October dates.
