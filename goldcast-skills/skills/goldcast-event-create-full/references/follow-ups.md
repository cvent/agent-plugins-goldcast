# Follow-ups after creation

Read this for SKILL.md Step 10, right after the final report. Offer only what applies, and don't re-offer anything that was just built. Each follow-up the user picks gets its own confirmation before anything is created.

## Contents
- 1. Flag what's missing
- 2. Offer the next steps
- 3. Register attendees
- 4. LinkedIn post
- 5. Readiness check

## 1. Flag what's missing

Before offering anything new, list in plain words anything the event should have that isn't there yet. Use what this conversation already knows, with no extra tool calls:

| Missing | What to offer |
| --- | --- |
| A person left out because their email wasn't known | "Send me [name]'s email and I'll add them." |
| A session, speaker or staff member that failed | Retry it (after checking whether it landed), or say what needs fixing first |
| People waiting on a session that failed | Add them once the session exists |
| A conference with no sessions | Offer to add the agenda (`references/sessions.md`) |
| Speakers on the event only, now that sessions exist | Offer to assign them to sessions |
| No speakers at all | Offer to add them now. Later, in a new conversation, that's `goldcast-speakers-onboard` |
| No staff, or no Producer | Mention it once. Someone usually needs to run the event backstage |
| Description left blank | Offer to draft one or take the user's text (`update_event`, `references/changes.md`) |
| Staff not added because roles couldn't be loaded | Offer to retry |
| Webinar attendee profile is off | Offer once to turn it on (`showOnboarding: true`). Call it the "attendee profile", never "onboarding" |
| Tracks, rooms or booths named in the brief | Remind the user to set them up in Goldcast Studio |

Keep it short: one line per item, most important first. Skip the section if nothing is missing.

## 2. Offer the next steps

Then offer these in one plain-text line at the end of the final report, not as a selection-UI call (a tool call right after the report can hide it):

- **Register attendees**
- **Draft a LinkedIn post**
- **Run a readiness check**

Leave out any the user already did or declined in this conversation. When the user picks one, run its section below.

## 3. Register attendees

For one person or a list: pasted, or an uploaded csv or xlsx. If only a file path is shown, read the file first. If the brief already included a registrant list, use that list (it was held back during setup on purpose), and still confirm before registering.

**Required per person:** email, first name, last name. Optional: company, title, LinkedIn URL, X URL, bio. Don't set `username`. The tool defaults it correctly.

**Prepare the list:**
1. Parse it. Show the count and the first 3 to 5 rows so the user can spot a column mix-up.
2. Drop exact duplicate emails within the list, and say how many were dropped.
3. Flag rows missing a required field, or with an obviously malformed email. Ask whether to skip them. Never guess a missing name or email.
4. Speakers and staff don't need registering. If someone on the list is already a speaker or staff member, skip them and say so.

**Confirm** with the count and a note that registering people can trigger event emails to them, depending on the event's settings:

> Register 48 people for Q1 Product Launch? (2 duplicates dropped, 1 row skipped for a missing email.) Registering may send them event emails, depending on the event's settings.

Send this as the visible final text of the turn and end with "Reply **register them**, or tell me what to change."

**Create** with `create_registration`, one person at a time. For lists over about 50, send a short progress note every 25 or so. For very large lists (hundreds), register a first batch, report, and ask whether to continue.

**Already registered:** treat it as a skip, not a failure. For a single person, check first with `list_registrants` using the exact `email` filter. Before retrying a failed registration, check the same way.

**Report:** registered, skipped (already registered or duplicate), failed (with the reason). Keep emails out of the report except for failures the user must fix.

## 4. LinkedIn post

Read `references/linkedin-promo.md` and follow it. Use the event's confirmed details from this conversation. The registration link isn't returned by any tool, so use the `[REGISTRATION LINK]` placeholder.

## 5. Readiness check

A quick "is this ready to launch" scan. Make these reads in parallel:

- `get_event` (title, type, dates, timezone)
- `list_broadcasts` (all pages)
- `list_speakers` (all pages, including hidden)
- `list_staff`
- `list_registrants` with `limit: 1` (read the total count)

Report a short checklist, with a clear ✓ or ✗ for each:

- **Sessions:** count, and any outside the event's times or with no speaker
- **Speakers:** count (note any hidden), and sessions with none
- **Staff:** count, and whether there's a Producer. Event-only staff show `roles: []`, which is normal
- **Registrants:** total
- **Description:** set or blank, if known from this conversation (`get_event` doesn't return it)
- **Timing:** days until start. Flag under 7 days with no registrants, or under 48 hours with anything missing
- **Not checkable from here:** the registration link, the template's look, promotion status. Say so, don't guess

End with the one or two most valuable fixes, and offer to do the ones this skill can do. Dates and times in plain language.
