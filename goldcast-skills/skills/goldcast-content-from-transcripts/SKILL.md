---
name: goldcast-content-from-transcripts
description: "Turn Goldcast webinar or virtual-event session transcripts into a LinkedIn post, blog post, or follow-up email, for one session or a list of sessions. Use whenever the user wants to repurpose, recap, promote, or follow up on a Goldcast event, webinar, session, panel, keynote, or recording, or mentions a Goldcast event alongside words like \"post\", \"blog\", \"recap\", \"follow-up email\", \"thank-you email\", \"no-show email\", or \"social copy\", even if they don't say \"repurpose\". Requires the Goldcast MCP connector. Not for live event monitoring, post-event analytics reports (use goldcast-event-reports), or creating or editing events."
license: "proprietary"
---

# Webinar Content from Transcripts (Goldcast)

Turn what was actually said in a Goldcast session into content people want to read. The session transcript is the only source of truth for what speakers said. Everything else (audience, CTA, links, brand voice) comes from the user.

Three output formats, each with its own reference file. Read only the one(s) requested:

- LinkedIn post: `references/linkedin-post.md`
- Blog post: `references/blog-post.md`
- Follow-up email: `references/follow-up-email.md`

This skill is built for Goldcast events and uses the Goldcast MCP connector. If the user pastes or attaches a transcript instead, follow "Pasted or attached transcripts" below.

**Tools used (Goldcast connector).** This skill only reads data. Never call `create_event`, `create_broadcast`, `create_speaker`, `create_staff`, `create_registration`, `create_clip`, `update_event`, or any other tool that changes Goldcast. The one exception is `create_error_report`, which only files a failure report.

| Need | Tool | Notes |
| --- | --- | --- |
| Confirm the connection | `get_current_user` | Returns identity only (id, name, email, org, admin flag, primary role) |
| Find the event | `search_events` | `query` matches titles only. Set `upcomingOnly: false` for past events |
| Event details | `get_event` | Title, description, type, hostType, schedule, timezone, workspace, series, flags. No viewing link |
| List sessions | `list_broadcasts` | `broadcastId`, title, times, type, `recorded`, `transcriptLanguages` |
| Speakers | `list_speakers` | Name, company, title, assigned broadcasts (also email: never output it) |
| Transcript text | `search_transcripts` | Keyword search that returns timestamped segments and transcript URLs |
| Workspace names | `list_workspaces` | Only to label events that span workspaces |
| Report a failed call | `create_error_report` | Only when an error's `llmAction` starts with `report_` |

## Step 1: Pick the path and verify the Goldcast connection (always first, before intake)

1. **Pasted or attached transcript?** If the user supplied the transcript text or a transcript file, go to "Pasted or attached transcripts" below and skip the rest of Step 1 and Steps 2 and 3.
2. **Check the connector.** Confirm the Goldcast MCP tools (such as `get_current_user` and `search_events`) are available. If they aren't, tell the user to connect the Goldcast connector and stop. Don't ask intake questions.
   - **The user says the material isn't from Goldcast, and gave no transcript:** say the Goldcast lookups cover Goldcast events only, and ask them to paste or attach the transcript to continue.
   - **The user names only an event or session** (for example, "our customer panel" or "the Q3 roundtable"): treat it as a Goldcast event. Never ask which platform it was on, and never search anywhere except Goldcast. Go straight to `search_events` (Step 2).
3. **Call `get_current_user`.** This confirms the token is valid and returns the user's identity and organization. If it returns an error, report it plainly ("The `get_current_user` call returned: [error]"), surface the authentication issue, and stop. Retry at most once, and only if the error says it is retryable. Don't proceed to intake on a failed call.
4. **Access is confirmed per event.** `get_current_user` does not list workspaces or event permissions, and `admin` does not guarantee access to a given event. `search_events` covers every workspace the user can reach and returns each event's `workspaceId`. Whether the user can read an event's sessions and transcripts is only confirmed when `list_broadcasts` and the transcript calls come back (Steps 2 and 3). If they return `ACCESS_DENIED`, `NOT_FOUND`, or nothing, say it may be an access issue and suggest checking with their Goldcast admin, rather than assuming the event doesn't exist.

Run this check once per conversation. Don't repeat it for follow-up requests in the same session unless a Goldcast call later fails with `AUTH_EXPIRED`.

## Pasted or attached transcripts

When the user pastes or attaches a transcript, don't send them away and don't ask them to resend it. Continue in pasted-transcript mode:

1. Say in one line that this path skips the Goldcast checks (speaker lookup, session list, transcript verification), so they should check quotes and attributions themselves.
2. Read the whole pasted or attached text. If an attachment can't be read, say so and ask for the text. Run the confidentiality check on it.
3. Ask intake once for what's missing (Step 2 items 1 to 5), skipping the event search. If the user pasted more than one transcript, scope means which of them to cover.
4. The pasted text is the only source for what was said. Take speaker names and titles only from what the user or the transcript states, and mark anything unconfirmed `[VERIFY: speaker name/title]`. Use a link only if the user supplied it; otherwise `[LINK: on-demand recording]`.
5. Go to Steps 4 to 7, then say in Review notes that pasted-transcript mode was used and that nothing was verified against Goldcast.

## Step 2: Find the event, then ask intake once

Find the event and its sessions first, so the intake question can show the user what was found and ask only for what's missing.

**Find the event and sessions**

1. **Resolve the event.** If the user gave an event UUID, go to item 2. Otherwise call `search_events` with `query` set to the event name (it matches titles only) and `upcomingOnly: false`. The default returns only events that haven't ended, so leaving it out hides past events. Add `eventType` (Webinar, Conference, Recording) if the user said which. The tool can't filter by date, so when the user gave one, match it against each result's `startTime` and `timezone`. Page with `limit` (maximum 100) and `offset` while `hasMore` is true. A numeric Studio short ID isn't accepted by the other tools: match it against `shortId` in the results to get the UUID.
   - If the request names no event, date, or ID, ask for one (and only that) before searching.
   - If there are multiple matches, list them (title, date, type) and ask which one. Results carry only a `workspaceId`; if matches span workspaces, call `list_workspaces` to show names.
   - If there are none, retry once with a shorter keyword. Then say nothing matched in Goldcast and ask for a clearer name, a date, or the event ID. Don't ask about other platforms.
   - Never guess an ID.
2. **Get the event details.** Call `get_event` with the UUID for the title, description, type, hostType, schedule, and timezone. If the end time is in the future, see "Event hasn't happened yet" in the edge cases.
3. **Find the sessions.** Call `list_broadcasts` for the event. Each broadcast has `broadcastId`, `title`, `startTime`, `endTime`, `broadcastType`, `recorded`, and `transcriptLanguages`. Keep paging with `offset` (and `limit`, maximum 100) until `hasMore` is false; don't stop at the first page. It does not return speakers or descriptions. A session with `recorded: false` or an empty `transcriptLanguages` has no transcript to read (see the edge cases).
4. **Descriptions.** `get_event` returns the event description; `list_broadcasts` does not return session descriptions. Use the event description as context for framing and audience inference. Session titles are fine for naming and for the intake confirmation, but they aren't evidence of what was said.
5. **Run the confidentiality check** (see "Confidentiality check" below) on the event and session titles and any descriptions you have. If it trips, stop before intake.

**Ask intake once (only for what's missing)**

Infer from the request first. Send one short message that does two things: confirm the match with the user (for example: "I found 'AI Pipeline Trends, June 18, 2026' with 5 sessions: [titles]. Tell me if that's the wrong event.") and ask together whatever is still missing from this list:

1. **Format(s):** LinkedIn, blog, email, or several.
2. **Scope:** all sessions in the event, or specific ones (skip this if the event has one session). If more than one, is this one piece that covers all of them, or one piece per session? If the user names sessions, match them to the list and confirm any that are ambiguous.
3. **Audience and goal (optional):** who reads it, and what should they do next (watch the recording, register for the next event, book a demo, download slides)?
4. **Assets (optional):** on-demand (recording) link, next-event link, slides, target keyword for blogs. Goldcast doesn't return an on-demand link through these tools, so ask for it here. Speaker names and titles come from `list_speakers`, so only ask if the user wants something different.
5. **Voice and brand (optional):** ask whether they have brand voice guidance this content should follow (a brand voice skill, a style guide, or a sample of writing they like). If they do, use it (see "Brand voice" below).

Items 1 and 2 are needed to proceed. Items 3, 4, and 5 are optional: mention that the user can provide them if they'd like, but don't press, and don't hold up the draft waiting for them. If they're skipped:

- **Audience and goal:** infer the audience from the event and session titles, any descriptions you have, and the topics discussed, and use a single CTA to watch the recording.
- **Assets:** use an on-demand link the user supplied, or one a Goldcast field returned explicitly (Step 3). For anything else you don't have (recording, next event, slides), use clearly marked placeholders such as `[LINK: on-demand recording]` and `[LINK: next event]`. Never make up a URL.
- **Voice and brand:** write in a clear, professional, conversational voice and note the assumption in Review notes.

For email, also confirm the segment (attendees, registered no-shows, or both) unless it's obvious from the request. If it isn't, write a neutral version.

If the request already supplies everything needed and the event match is exact (one result matching the name, date, or ID the user gave), state the match in one line and continue without waiting.

## Step 3: Get the transcripts from Goldcast

1. **Identify the speakers.** Call `list_speakers` for the event (page with `limit` and `offset`). Each record has the speaker's name, company, title, and assigned broadcasts; use the assigned broadcasts to match speakers to sessions. Use these details, not the transcript's auto-captioned spellings, whenever you name or attribute a speaker. If a speaker in a transcript can't be matched to the list, mark them `[VERIFY: speaker name/title]` rather than guessing. The records also include email addresses; never output them.
2. **Get the on-demand link.** `get_event` and `list_broadcasts` return no viewing link (only `recorded` and `public`). Use a link the user supplied. Use a link from a Goldcast field only if it is explicitly labeled as the on-demand or viewing link for the event or session. Never build a URL yourself from an event ID, `shortId`, slug, or name, and don't use a transcript URL as the viewing link. If several sessions each have their own link and the piece covers them separately, use each session's link; otherwise use the event-level link. If there is none, use `[LINK: on-demand recording]` and say so in Review notes.
3. **Pull the transcripts and read every one in full.** For each broadcast in scope, use the language code from its `transcriptLanguages`.
   - **If your client exposes a transcript resource** for the broadcast (for example `resource://broadcast/{id}/transcript`), read it from beginning to end. The Goldcast pr50 tools don't include one, so don't assume it exists.
   - **Otherwise, use `search_transcripts`.** Call it with `{"eventIds": ["<event UUID>"], "query": "<keyword>", "language": "<code>"}`. It is a case-insensitive keyword search (at least two characters), not a reader. For each matching broadcast it returns timestamped segments plus transcript URLs. Broadcasts with no match are omitted, `skipped` lists broadcasts whose transcript couldn't be read, and `truncated: true` means narrow the query.
   - **Read in full through the transcript URLs.** Open each returned transcript URL with `web_fetch` and read it from beginning to end, for every session in scope. Don't sample, skim, read only the opening, or stop once you've found a theme that seems good enough. If a transcript comes back in parts, keep reading until you've reached the end.
   - **If a URL can't be opened** (login required, error, empty), the transcript can't be read in full. Tell the user which sessions are affected and ask whether to continue from search excerpts only or to have them paste the transcripts. If they choose excerpts, run varied queries (terms from the session title, speaker surnames, "question", "customers") until the timestamps cover the beginning, middle, and end, write only what the segments show, and state in Review notes that the piece is excerpt-based and the transcripts were not read in full. Never describe that as a full read.
   Use these transcripts as the source material for everything you write.

**Batching.** When the scope is too large to read comfortably in one pass (many sessions, or long transcripts), work in batches. Every session still gets read in full.

- Tell the user in one line that you're working in batches.
- Read a batch of roughly 3 to 5 sessions (fewer if the transcripts are long), then write that batch's source-tagged notes (Step 4 format) before starting the next batch.
- Keep verbatim quote candidates, timestamps, and speaker attributions in the notes, so quoting never depends on re-reading a transcript.
- After the last batch, merge the notes and only then choose the angle (Step 5).
- If the scope is beyond what batching can cover (dozens of sessions), say so and ask the user which sessions to cover. Every session in scope stays in scope until the user narrows it.

If a transcript comes back empty or cut off, or a call fails, tell the user which session is affected and why, and continue with the others if it makes sense. Report an error once and retry at most once; if it keeps failing, stop and let the user decide. Never write from a session title or abstract alone and imply it reflects what was said.

Goldcast errors include `llmAction`, `retryable`, `trackingId`, and `mcpErrorCode` (for example `SERVICE_ERROR`, `ACCESS_DENIED`, `NOT_FOUND`, `AUTH_EXPIRED`, `RESPONSE_TOO_LARGE`). Follow the `llmAction`. If it starts with `report_`, call `create_error_report` with `trackingId`, `mcpErrorCode`, and `failedTool` copied unchanged, and summaries that contain no names, emails, or other personal data. For `RESPONSE_TOO_LARGE`, narrow the query or page size.

## Confidentiality check

Run this on the event and session titles and any descriptions you have (Step 2) and on each transcript as you read it. Match the phrase "Confidential / For internal Use Only" case-insensitively, ignoring differences in spacing and punctuation. Treat close variants used as a document marking (for example "Internal Use Only" or "Confidential, Do Not Distribute") the same way. A speaker who merely mentions confidential data in conversation doesn't trigger this.

If the phrase appears, stop and tell the user the material should be kept private and internal. Do not turn it into external-facing copy unless they confirm it has been cleared. Also ask before proceeding if the session appears clearly internal (an all-hands, an NDA-covered advisory board, and so on).

## Step 4: Mine the transcript before writing

**Sources.** Every claim in the piece traces to the session transcripts, or to an event or session description returned by `get_event` or pasted by the user. Nothing else counts: no invented quotes, statistics, examples, customer stories, outcomes, speaker opinions, product details, dates, or "industry context" from general knowledge or memory. Links, CTAs, and brand guidance from the user are used as given, but they don't describe what happened in a session. A point that would strengthen the piece but isn't in the sources stays out. A shorter, plainer piece beats one unsupported sentence.

**Where synthesis stops.** A good piece synthesizes: it chooses, orders, connects, and frames what the sources say. It never infers: adding claims the sources don't make.

| Synthesis (do this) | Inference (cut it, or mark `[VERIFY: ...]`) |
| --- | --- |
| Group and order ideas by theme | A cause, result, or trend no speaker stated |
| Connect statements from the sources ("both speakers pointed to X") | Agreement, motive, or feeling nobody expressed |
| Reword in plain language, keeping the speaker's meaning and hedging | Background, benchmarks, or context from your own knowledge |
| Frame the reader's problem using the event or session titles and descriptions (if you have them), or as a question | A general rule drawn from one speaker's example |
| Write takeaways and "so what" lines that restate what a speaker recommended or demonstrated | Advice of your own that no speaker gave |
| Infer the audience from the event and session titles, any descriptions, and the topics discussed | Details about the audience that the sources don't support |

The test for each sentence: can you point to where in the sources it comes from? If a sentence needs an extra "and therefore" beyond what a speaker said, cut it, turn it into a question to the reader, or mark it `[VERIFY: ...]`.

**Finish reading before deciding anything.** Settle the thesis, angle, and through-line only after every transcript is read (with batching, after the last batch). The first theme you notice is often not the strongest one, and a late question, a disagreement, or a closing remark can change what the session was really about. For multiple sessions, compare only once all of them have been read, so the through-line reflects the whole set.

Build working notes for yourself (share them only if asked). Tag every item with its source (session and timestamp if available, or "event description" / "session description"). Any item you can't tag doesn't go in the notes, and so doesn't go in the piece:

- **Core thesis:** the one point the session is really about, in a sentence.
- **3 to 5 insights:** each with speaker, and timestamp if available.
- **Concrete specifics:** numbers, examples, stories, named frameworks, with who said them.
- **Quotable lines:** verbatim, short (under about 25 words), self-contained, and attributed.
- **Audience questions and answers:** the ones that reveal what attendees care about.
- **Tension or surprise:** anything counterintuitive, since it usually makes the best hook.

Transcripts are noisy. Auto-captions mangle names, product terms, and numbers, so check spellings against the speaker details from `list_speakers` and anything the user supplied, and flag anything uncertain with `[VERIFY: ...]`. Ignore housekeeping (intros, tech issues, "can you hear me"), sponsor pitches unless the user wants them, and tangents.

**For multiple sessions:** once every session has been read, find the through-line across sessions (a shared theme, a disagreement, a progression) and write around it instead of summarizing each session in turn. A "recap of five talks" reads like minutes. Only do a session-by-session roundup if the user asks for one.

## Step 5: Choose one angle, then draft

Pick a single angle from your notes and commit to it. Content that tries to cover everything says nothing memorable. The angle should be something the reader gets value from even if they never watch the recording, which is also what makes them want to.

Then read the relevant reference file and draft to its structure and length guidance.

## Step 6: Fidelity rules (these apply to every format)

- **Quotes are verbatim.** You may trim filler words ("um", "you know") and mark cuts with an ellipsis. Do not paraphrase inside quotation marks or stitch two separate statements into one quote. If you paraphrase, drop the quote marks.
- **Attribute accurately.** Right speaker, right title, right company, taken from `list_speakers`. If the transcript doesn't identify who said something, don't guess.
- **Numbers belong to the speaker.** A number a speaker mentioned is "according to [speaker]", not a fact you assert in your own voice. If you need a fact that isn't in the Step 4 sources, cut it, or mark `[VERIFY: ...]` if it's something the user could confirm.
- **Stay faithful to meaning.** A hedged statement stays hedged. Don't sharpen it into an absolute, and don't put words in a speaker's mouth to fit a narrative.
- **Protect attendees.** Don't name attendees who asked questions, and don't include emails or other personal data. Refer to "one attendee asked" unless the user has consent to name them.
- **Speaker and customer sensitivity.** Flag anything that reads as an unreleased product, roadmap commitment, legal or financial claim, or criticism of a named company, so the user can get sign-off.

## Brand voice

If the user points you to a skill or brand voice guidance in Step 2, follow it. Load that skill or read those guidelines before drafting, and let them win over the defaults in this skill on tone, vocabulary, naming, and CTA style. Facts still come only from the Step 4 sources; brand guidance does not license adding proof points, awards, or product claims that aren't in them. If the guidance is silent on something, say so and use your best judgment. If the user has no guidance, proceed with the default voice and mention in Review notes that you did.

## Step 7: Deliver

1. **In the reply:** deliver each piece (LinkedIn post, email, blog post, and so on) ready to copy.
2. **As files:** unless the user asked for a different format or for reply-only, also generate a file for each piece, as a `.docx`. Create one file per piece (for example, one file per LinkedIn post, per email, per blog post), named clearly, such as `linkedin-post-[event-or-session].docx`. Before creating the files, read the docx skill (or the skill for whichever format the user asked for) and follow it. Save them to `/mnt/user-data/outputs/` and share them with `present_files`. The file should contain only the copy-ready content (including title/subject options and meta description where relevant), not the Review notes.
   - **If file creation isn't available** (the Code Execution and File Creation setting is off, the tools aren't offered, or the file step fails): say so in one line, and keep the drafts in the reply, which is already complete. Offer two options: turn on Code Execution and File Creation in Settings and ask you to retry, or copy the drafts from the reply into Word or Google Docs. Don't let this hold up the drafts.
3. **Review notes** (in the reply, after the drafts):
   - Any `[VERIFY: ...]` items, and anything the user must fill in (links, tags, merge fields).
   - Which sessions' transcripts were read in full (and whether you worked in batches), which were excerpt-based, and any that were missing or incomplete. In pasted-transcript mode, say that nothing was verified against Goldcast.
   - Where the key claims came from (session, and timestamp if known), so a reviewer can spot-check quickly.
   - Which on-demand link was used and where it came from, or that none was returned and a placeholder was left.
   - Any sensitivity flags from Step 6.
   - Which brand voice guidance was used, or that a default voice was assumed.
   - Whether the `.docx` files were created, or that the file fallback was used.
4. Offer at most one useful next step, such as a second hook option, a shorter cut, or a companion piece in another format. Don't list a menu of options.
5. Remind the user that a human should review before publishing, especially the quotes and attributions.

## Edge cases

| Situation | What to do |
| --- | --- |
| `get_current_user` errors | Surface the authentication issue and stop. |
| Transcript pasted or attached | Use pasted-transcript mode (see "Pasted or attached transcripts"). Skip the Goldcast steps. |
| Material isn't from Goldcast and no transcript was given | Ask the user to paste or attach the transcript. |
| Only a session or panel is named | Search Goldcast with `search_events` (`upcomingOnly: false`). Never ask about the platform. If nothing matches, ask for a clearer name, date, or event ID. |
| Event not found or ambiguous | Confirm you searched with `upcomingOnly: false`, retry once with a shorter keyword, then ask the user to clarify the name, date, or ID. Don't guess. |
| Event has no broadcasts | Tell the user; the event may be upcoming or not yet set up. |
| Session has `recorded: false` or no `transcriptLanguages` | Name the session, say there is no transcript to read, and ask whether to continue with the others. Test events may skip recording. |
| Transcript is empty, unreadable, or listed in `skipped` | Name the session, say the transcript isn't available, and ask whether to continue with the other sessions or have them paste it. The transcript may still be processing. |
| `search_transcripts` returns `SERVICE_ERROR` | Retry once. If it fails again, stop, tell the user, and file `create_error_report` if the error asks for it. |
| Transcript is very long, or many sessions | Read all of it, taking notes as you go, and batch as described in Step 3. Write from the notes; don't try to reproduce the transcript. |
| Multiple speakers disagree | Use the disagreement as the angle; represent each side fairly and attribute each. |
| Session was mostly demo or product pitch | Focus on the problem, the outcome shown, and what viewers can try, not a feature list. |
| Little substance to quote | Say so, then write a shorter piece around the one strong idea instead of padding. |
| User wants all three formats | Draft each from the same angle but with format-native structure, not copy-pasted. Keep the hook different across them. |
| Transcript language isn't English (see `transcriptLanguages`) | Ask which language to write in. Translate quotes faithfully and note that they are translated. |
| Event hasn't happened yet (`get_event` end time is in the future) | This skill is for after the fact. Offer to write promo copy from the event details, clearly labeled as pre-event. |
| File creation unavailable | Follow the fallback in Step 7. |

## What not to do

- Don't summarize chronologically ("First, X spoke about... then Y said...").
- Don't open with filler like "We're thrilled to share" or "In today's fast-paced world".
- Don't paste long stretches of transcript text; write original copy that draws on it.
- Don't include registrant, attendee, or speaker email addresses or other personal data in any output.
- Don't use anything outside the Step 4 sources for what was said or covered in a session.
