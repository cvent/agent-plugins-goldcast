# Sessions (conferences only)

Read this when a conference brief includes an agenda. A webinar has exactly one session, which Goldcast creates automatically. Never call `create_broadcast` for a webinar.

## Contents
- Collecting the agenda
- Times and the event window
- What goes in the summary
- Creating sessions
- When a session fails
- Large agendas
- Tracks and formats
- Worked example

## Collecting the agenda

From the brief (an agenda table, run-of-show or list), collect for each session:

| Field | Required | Notes |
| --- | --- | --- |
| Title | yes | Max 256 characters. Use the brief's wording |
| Start and end (local) | yes | In the event's timezone unless the brief says otherwise |
| Description | no | Only text the brief gives. Don't invent blurbs |
| Speakers | no | Names only at this stage. Step 3a maps them to sessions |

If a session has a start but no end, use the next session's start, or 30 minutes for the last one, and mark it assumed. If a session has no time at all, ask in Step 3b. Don't place it yourself.

Breaks, lunch and networking blocks are not sessions unless the brief clearly treats them as one (a named networking session with a host, for example). If unsure, leave them out and say so in the summary.

## Times and the event window

Convert every session's start and end with `scripts/iso_time.py`, using the event's timezone.

Goldcast's rules for `create_broadcast`:

- A session must **start** within the event's `startTime` and `endTime`.
- A session must **end** no more than 1 hour after the event's `endTime`.

The event is created before its sessions, so set the event window to fit the agenda first:

- **No event times given:** event start = first session start, event end = last session end.
- **Event times given and the agenda fits:** keep them.
- **Event times given and a session falls outside:** ask in Step 3b whether to widen the event to fit the agenda or to change the session. Never quietly move a session.

Parallel sessions may overlap in time. That's fine.

## What goes in the summary

Add a **Sessions** section to the Step 4 summary: a table of title and plain-language local time, plus each session's speakers.

> **Sessions (4)**
>
> | Session | When (ET) | Speakers |
> | --- | --- | --- |
> | Opening keynote | Tue, Dec 8, 10:00–10:45 AM | Ada Lovelace |
> | Product roadmap | Tue, Dec 8, 11:00–11:45 AM | Grace Hopper |
> | Customer panel | Tue, Dec 8, 1:00–2:00 PM | Ada Lovelace, Sam Lee |
> | Closing remarks | Tue, Dec 8, 2:15–2:30 PM | (none) |

For agendas over about 10 sessions, show the first 5 and the count, and say the full agenda will be used. The one confirmation covers the whole agenda.

## Creating sessions

Right after `create_event` succeeds, and before any speakers or staff:

1. Call `create_broadcast` once per session, **one at a time, in agenda order** (not in parallel), with:
   - `eventId`: the new event
   - `title`, `startTime`, `endTime` (ISO from the script)
   - `description`: only if the brief gave one
   - `broadcastType`: the event's format (default `LIVE_HYBRID`). Call it "live" to the user, never "live hybrid"
   - `location`: leave blank unless the brief includes a venue for that session
   - `trackIds`: omit (see "Tracks and formats")
2. Record each returned `broadcastId` against its agenda item.
3. When all are done, call `list_broadcasts` (page with `offset` while `hasMore`) to verify the count and collect every `broadcastId`.
4. Continue to speakers and staff, using the Step 3a mapping.

Progress message: "Creating sessions… 3 of 5 done."

## When a session fails

- **Before retrying, check whether it landed:** call `list_broadcasts` and look for the title and start time. If it's there, carry on. If not, fix the cause and retry once.
- **Keep going** with the remaining sessions after a failure.
- **People assigned to a failed session wait.** Don't move them to another session or to the event only. Report them as "waiting for [session title]" and offer to add them once the session exists.
- Staff with "all sessions" scope go on the sessions that were created.
- Common cause: `INPUT_ERROR` because the session is outside the event window. Report the exact error and offer to widen the event with `update_event` (with a before → after confirmation, see `references/changes.md`), then retry the session.

Report sessions in the final results table: created / failed, with the reason for each failure.

## Large agendas

For 20 or more sessions: confirm once, create sequentially, send a short progress note about every 5 sessions, and report all failures together at the end. Don't stop at the first failure.

## Tracks and formats

- **Tracks:** no tool lists track IDs, so if the brief names tracks ("Database track", "Observability"), omit `trackIds` and tell the user tracks need setting up in Goldcast Studio. Sessions land in the event's default track.
- **Format per session:** use the event's format unless the brief clearly says a session differs, e.g. a pre-recorded keynote (`SIMULIVE`), or pre-recorded with live Q&A (`HYBRID_SIMULIVE`). Show any non-live session's format in the summary.
- **In-person or hybrid sessions:** for events with `hostType` `In_Person` or `Hybrid`, set `broadcastType` to `IN_PERSON_HYBRID` and pass `location` (e.g. "Main Hall, Building A"). Leave `location` blank for virtual sessions within a hybrid event.

## Worked example

**User:** "Create our Customer Summit on Dec 8, ET. Agenda: 10:00 keynote (Ada Lovelace), 11:00 product roadmap (Grace Hopper), 1:00 customer panel (Ada, Sam Lee). Sam Lee is also our producer."

**Assistant:**

1. Event type: an agenda with 3 sessions → `Conference`. Reads `references/sessions.md`.
2. Converts each session with the script. No event times given, so the window is 10:00 AM to the last session's end. The panel has no end time, so it's assumed to be 30 minutes (marked assumed).
3. Maps speakers: Ada → keynote + panel, Grace → roadmap, Sam Lee → panel (speaker), and Producer (from the brief) on all sessions (default).
4. Asks the open questions in one message: template, Ada's and Grace's emails if `search_users` doesn't find them, a description (draft or leave blank, since the request has none), and invites.
5. Summary shows the event, a 3-row sessions table, speakers with their sessions, and staff.
6. After a yes: `create_event` → `create_broadcast` ×3 in order → `list_broadcasts` → speakers and staff with their mapped `broadcastIds` → reports sessions, speakers and staff in the results.
