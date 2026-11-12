# Changes after creation

Read this when the user wants to change an event that already exists: one just created in this conversation, or one they name. Two paths:

- **The field can be changed with `update_event`:** make the change here, after a confirmation.
- **No tool can change it:** say so plainly and point the user to Goldcast Studio.

## Contents
- Finding the event
- What `update_event` can change
- Confirming and making the change
- What only Goldcast Studio can change
- Mixed requests

## Finding the event

- **Created in this conversation:** use its `eventId`.
- **Named by the user:** call `search_events` with the title (`upcomingOnly: false` if it may have passed). Confirm the match (title, plain-language date, type) before changing anything. If several match, list them and ask.
- Call `get_event` to read the current values so you can show before → after, including the description.

## What `update_event` can change

`update_event` takes `eventId` plus one or more of these fields. Omitted fields stay as they are.

| User might say | Field | Notes |
| --- | --- | --- |
| rename, new title | `title` | Max 256 characters. Public: registrants see it |
| description, registration copy, blurb | `description` | Plain text, max 4000. Drafting rules from SKILL.md Step 1c apply: no invented facts |
| move, reschedule, new date or time, longer, shorter | `startTime`, `endTime` | Convert with `scripts/iso_time.py`. Always send both. For a conference, check sessions afterwards (below) |
| timezone | `timezone` | Also resend `startTime` and `endTime` in the new zone. Ask whether the clock time should stay ("still 2 PM, but Pacific") or the moment should stay ("same moment, shown in Pacific") |
| custom URL, slug, short name | `shortName` | URL-safe. Public |
| pre-recorded, simulive, external stream, live | `broadcastType` | Say "live" to the user, never "live hybrid" |
| mark as test, sandbox, dry run | `test: true` | Test events skip on-demand availability and recording |
| live captions | `enableLiveCaptions` | |
| attendee profile (webinars only) | `showOnboarding` | Call it the "attendee profile", never "onboarding". Off by default for webinars |
| event chat (webinars only) | `broadcastChatDisabled` | Don't offer it. It stays off for webinars on purpose, because the session chat is already on and a second chat confuses attendees. If the user asks anyway, explain that, and change it only if they still want it |

`hostType` accepts `Virtual`, `In_Person` or `Hybrid`. Change it only when the user asks to switch.

**A mistaken event** (wrong type or template, or a duplicate): there's no delete tool. Offer to rename it (for example, prefix "[DUPLICATE - do not use]") and set `test: true`, then tell the user to delete it in Goldcast Studio.

## Confirming and making the change

1. Show what will change, before → after, in plain language:

   > **Update Q1 Product Launch?**
   > - **When:** Fri, Feb 5, 2027, 2:00–3:00 PM ET → Fri, Feb 12, 2027, 2:00–3:00 PM ET
   > - **Title:** Q1 Product Launch → Q1 Product Launch: Live Demo
   >
   > Registrants will see these changes. Make them?

2. For public fields (title, description, slug, times), mention that registrants see the change.
3. After a yes, call `update_event` **once** with all the confirmed fields together.
4. **Time changes on a conference:** call `list_broadcasts` afterwards. Any session must start within the new event window and end no more than 1 hour after it. List any that now fall outside and tell the user sessions are edited in Goldcast Studio (no tool here edits sessions).
5. Report what changed, in plain language.

If `update_event` errors, read the message and `references/errors.md`. Before retrying, call `get_event` to see whether the change already applied. Retry once at most.

New sessions can still be **added** to an existing event with this skill (`references/sessions.md`). New speakers and staff are added with `goldcast-speakers-onboard`. Only changing or removing any of them needs Studio.

## What only Goldcast Studio can change

No tool here can change these. Say so plainly, give the reason if it helps, and tell the user to open the event in Goldcast Studio (search the title). Don't guess menu paths in Studio.

| User wants to | What to say |
| --- | --- |
| Change the event type (webinar ↔ conference) | Locked at creation. Offer to create a new event, and to mark this one as a test |
| Change the template | Locked at creation. Same offer as above |
| Move to another workspace | Done in Goldcast Studio |
| Change the owner | Locked at creation, here and in Goldcast Studio. The owner is whoever created the event. If someone else needs to own it, offer to have them create a new event, and to mark this one as a test |
| Add the event to a series, or change its series | Done in Goldcast Studio |
| Edit, move or delete a session | Done in Goldcast Studio. New sessions can still be added here |
| Edit or remove a speaker or staff member, or change their sessions, role or a speaker's access level | Done in Goldcast Studio. New people can still be added with `goldcast-speakers-onboard` |
| Resend speaker or staff invites | Done in Goldcast Studio. Invites held at setup can be sent from there too |
| Delete the event | Done in Goldcast Studio. Offer to mark it as a test meanwhile |
| Set up tracks, rooms or booths | Done in Goldcast Studio |
| Change registration page design, branding or emails | Done in Goldcast Studio |
| Get the event link | The tools don't return it. Open the event in Goldcast Studio |

If a tool returns `NOT_AVAILABLE_VIA_MCP` for something not listed here, treat it the same way.

## Mixed requests

If one request mixes both kinds ("move it to Feb 12 and swap out Grace for Ada"), do the `update_event` part with its confirmation, and in the same message list what needs Studio:

> I can move the date here. Swapping a speaker needs Goldcast Studio, since no tool here can remove a speaker. (Ada can be added as a new speaker with the speaker onboarding skill if you'd like.)
