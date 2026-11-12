# LinkedIn promo post for a new event

Write a post that makes the right person register. This is pre-event promotion, so everything comes from the brief and the event details. There is no transcript. For after-the-fact recaps, use the goldcast-content-from-transcripts skill if it's available. Offered from SKILL.md Step 10.

## Inputs

Pull from what you already have. Ask only for what's missing and essential.

- **Event facts:** title, type, date, start time and timezone, duration. Use the confirmed values from event creation. `get_event` can refresh them.
- **What attendees get:** from the brief's description, agenda, or the user's own words. If thin, ask one question: "What's the one thing someone walks away with?"
- **Who it's for:** the audience from the brief.
- **Speakers:** names, titles and companies only if the brief or the user confirmed them (or `list_speakers` returned them). Never use emails.
- **Registration link:** the tools don't return one. Use the placeholder `[REGISTRATION LINK]` and tell the user to paste it from Goldcast Studio. Don't invent a URL.
- **Brand voice:** if the user points to a brand voice skill or guidelines (for Cvent events, `cvent-brand-voice` if it's installed), load them and let them win over the defaults here. Facts still come only from the sources above.

## Structure

1. **Hook (first ~200 characters).** LinkedIn cuts the post off after roughly this much on mobile, so the hook has to earn the "see more". Lead with the problem the audience has, a surprising specific, or the payoff. Not the event name, and not "We're excited to announce".
2. **What you'll get.** Two or three concrete takeaways or questions the session answers, as short lines. Drawn from the brief only.
3. **Who it's for.** One line.
4. **Speakers**, if confirmed: name and role, one line. Mention only what the brief supports.
5. **Logistics.** One line in plain language: "Thursday, Nov 5 at 11:00 AM ET (60 min), live and free" (only say "free" if the brief does). For a global audience add one more zone: "8:00 AM PT".
6. **Call to action.** One clear ask with the link: "Save your spot: [REGISTRATION LINK]".
7. **Hashtags.** Up to 3, relevant, at the end. Skip them if the brand voice guidance says to.

Target 900 to 1,300 characters. Short lines and white space. At most two emoji, and none if the voice is formal.

## Conference variants

- **Save-the-date:** date, theme, who should come, one or two standout sessions. Link to the event page.
- **Agenda highlight:** spotlight one session or speaker and what they'll cover. Good for a second or third post in a campaign.

If the user wants a campaign, offer a sequence (announce, session spotlight, last call) and write one at a time.

## Rules

- No invented claims: no attendance numbers, ratings, awards, customer names, or "limited seats" unless the brief says so.
- Don't promise content the brief doesn't mention.
- Don't tag or @-mention people. Name them, and tell the user they can tag in LinkedIn.
- Keep internal or unreleased details out. If the brief carried "Confidential / For Internal Use Only", ask the user what's cleared to be public before using any of it.
- No emails, phone numbers or other personal data.
- Avoid filler openers ("In today's fast-paced world", "Thrilled to share").

## Delivery

Put the post in the reply, ready to copy. A post this short doesn't need a file. Then:

- One line listing placeholders the user must fill (`[REGISTRATION LINK]`).
- Offer at most one follow-up: a shorter cut, an alternate hook, or a version speakers can repost from their own accounts.

Remind the user to review before posting.

## Example

For a webinar "Q4 Pipeline Planning" on Thursday Nov 5 at 11 AM ET, from a brief that lists stalled deals, coverage targets and a 20-minute weekly pipeline review as the three takeaways, aimed at sales and revenue ops leaders:

> Your Q4 forecast is only as good as the pipeline behind it. Here's how to pressure-test yours before the quarter gets away from you.
>
> Join us for a live 60-minute working session on Q4 Pipeline Planning. You'll leave knowing how to:
> → Spot the deals that quietly stall before they hit your forecast
> → Set coverage targets your CFO will actually trust
> → Run a weekly pipeline review in 20 minutes
>
> Built for sales and revenue ops leaders planning their final quarter.
>
> 📅 Thursday, Nov 5 at 11:00 AM ET (8:00 AM PT)
> 🔗 Save your spot: [REGISTRATION LINK]
>
> #RevOps #SalesPlanning

Note how every claim traces to the brief. If the brief hadn't said "weekly pipeline review", that line would not exist.
