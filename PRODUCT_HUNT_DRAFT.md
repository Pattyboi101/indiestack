# Product Hunt Launch Draft

> Prepared 2026-02-20. Review and edit before posting.

---

## Tagline (60 chars max)

### 1. "Find indie dev tools your AI assistant can search too"
(54 chars) — Puts the user benefit first ("find"), hints at the AI angle without leading with jargon. PH audience skims fast; this is immediately clear. The word "too" creates intrigue: wait, my AI can search this?

### 2. "A curated index of indie dev tools with an MCP server"
(54 chars) — More literal and technical. Works well if the MCP angle is already gaining traction in PH circles. Clearly describes what it is in one line.

### 3. "Indie SaaS tools, curated for devs and their AI copilots"
(57 chars) — Slightly warmer tone, uses "copilots" which is familiar to the PH audience. The "and their AI copilots" framing positions IndieStack as serving two users at once — the developer and their AI.

**Recommendation**: Go with #1. PH rewards benefit-first taglines that spark curiosity. #2 is the safe fallback if you want pure clarity.

---

## Description (260 chars max)

A curated marketplace of 100+ indie SaaS tools — searchable by developers and AI assistants alike. Includes an MCP server so Claude Code and Cursor can find existing tools before rebuilding from scratch. Makers keep ~93% of revenue. Built by two CS students in 10 weeks.

(259 chars)

---

## Maker Comment (The First Comment)

Post this immediately after the launch goes live:

---

Hey PH! We're Patrick and Ed, CS students at Cardiff University in Wales.

We built IndieStack in 10 weeks with zero budget, zero JS frameworks, and zero users (yes, really — we purged all our test data before launching because we'd rather be honest than fake it).

**The backstory**: We kept watching our AI coding assistants spend hundreds of tokens rebuilding authentication, billing, and email systems from scratch — when perfectly good indie tools already existed. The problem? There was no structured way for an AI to check "does a tool for this already exist?" before generating boilerplate. G2 and Capterra are built for enterprise procurement, not developer workflows.

**So we built IndieStack**: a curated index of indie SaaS tools with a JSON API and an MCP server. Point your AI assistant at it, and it can search for existing solutions — with integration snippets, pricing, and "tokens saved" estimates — before writing code from scratch.

**The stack** (for the curious): Pure Python/FastAPI, SQLite, zero JavaScript frameworks. The entire frontend is Python string templates. No React, no build step. Single Fly.io machine. The MCP server is about 150 lines of Python.

**What we'd love feedback on**:
- Is the MCP/AI integration angle actually useful, or just a novelty?
- What tool categories should we expand into next?
- How do you currently discover indie alternatives to big SaaS products?

We're building this in public and documenting everything. This is a real product we're trying to make real, not a class assignment — but we're not going to pretend we've cracked distribution yet. We're here to learn and iterate.

Thanks for checking it out!

---

(~235 words)

---

## Topics/Tags

1. **Developer Tools** — Primary category. This is where the PH dev audience browses.
2. **Artificial Intelligence** — The MCP angle makes this relevant to the AI tools crowd.
3. **SaaS** — Core product type. Appears in most PH discovery feeds.
4. **Open Source** — The MCP server and API are open. This tag attracts builders.
5. **Productivity** — "Stop rebuilding what exists" is a productivity pitch at its core.

---

## Gallery Images

Capture these 4-5 screenshots for the PH gallery. PH displays them as a carousel — the first image is the most important.

### 1. Homepage Hero (FIRST IMAGE)
Full-width screenshot of the landing page hero section: the IndieStack logo, tagline, search bar, and trending tools scroll-row. Make sure dark mode is OFF — PH galleries look best with light backgrounds. Crop to 1270x760px.

### 2. Tool Detail Page
Screenshot of a well-populated tool page (pick one with a Verified badge, Ejectable badge, star ratings, and a code integration snippet visible). Show the full "above the fold" including pricing, badges, and the first review. This demonstrates depth.

### 3. /explore Page with Filters
Show the unified explore page with at least one filter active (e.g., category = "Authentication" or tag = "open-source"). Include the sidebar filters and the grid of tool cards. This demonstrates discoverability.

### 4. /alternatives Page (Programmatic SEO)
Screenshot of an alternatives page like `/alternatives/auth0` showing indie alternatives to a well-known product. This is a unique differentiator — PH audience loves "X alternatives" content.

### 5. MCP Server in Action (Terminal)
A terminal screenshot showing Claude Code (or Cursor) using the MCP server to search IndieStack. Show the query and the structured JSON response with tool names, descriptions, and pricing. This is the "wow" screenshot that makes the AI angle tangible.

**Image tips**:
- Use a clean browser with no extensions visible
- Ensure real data is showing (not placeholder/lorem ipsum)
- Add a thin 1px border (#E5E5E5) around screenshots so they don't bleed into PH's white background
- Consider adding a short caption text overlay at the top of each image (PH supports this)

---

## Timing Advice

### Best Day
**Tuesday, Wednesday, or Thursday**. Tuesday and Wednesday historically have the highest engagement on PH. Thursday is solid but has more competition from established companies launching mid-week.

### Best Time
**12:01 AM Pacific Time (8:01 AM GMT)**. Product Hunt resets its daily leaderboard at midnight Pacific. Launching at 12:01 AM PT gives you a full 24 hours on the board. For Cardiff, this means scheduling the launch to go live at **8:01 AM GMT**.

### Coordinating with HN
Launch on Product Hunt **2-3 days after** the Show HN post:
- If HN goes well, you can reference it: "We launched on HN earlier this week and the feedback was incredible..."
- If HN goes poorly, you can iterate on the messaging before PH
- Having two separate launch events creates two waves of traffic instead of splitting one
- If HN post is on Tuesday, target PH for Thursday of the same week

### Pre-Launch Checklist
- Set up the PH "Coming Soon" page at least 1 week before launch
- Collect early subscribers via the Coming Soon page
- Notify subscribers 24 hours before launch
- Have all gallery images and copy ready the night before
- Schedule a "teaser" tweet for 12 hours before launch

---

## Common PH Pitfalls

### 1. Don't ask friends to hunt you
Getting a genuine hunter (someone with an established PH following) to hunt your product carries more weight than self-hunting. If you can't find a hunter, self-hunting is fine — but do NOT pay for a hunter or trade hunts. PH's algorithm detects and deprioritises these patterns.

### 2. Engage with every single comment
PH rewards makers who respond to every comment within minutes. The algorithm factors in maker engagement when ranking products. Set aside the ENTIRE launch day — no classes, no other work. Treat it like a 16-hour shift.

### 3. Have a "special offer" ready for PH visitors
PH audience loves exclusive deals. Ideas for IndieStack:
- "First 50 PH makers can list their tool for free with a Featured boost"
- "PH visitors get free Verified badge review for launch week"
- "Use code PRODUCTHUNT for 3 months of Pro at 50% off"
- Display a banner on the site: "As seen on Product Hunt" with the PH kitty logo

### 4. Update the page throughout the day
Post "EDIT" updates to your maker comment with live metrics:
- "EDIT (4 hours in): 150 upvotes, 12 tools submitted by PH makers, fixed the bug @username found"
- This shows you're actively building and listening. PH audience loves real-time transparency.

### 5. Don't launch with broken flows
Test every user-facing flow the night before: signup, search, explore, tool detail, submit, MCP server. PH visitors are ruthless about first impressions. If the site is slow or buggy, the comments will be about that instead of the product.

### 6. Don't ignore the mobile experience
A significant chunk of PH browsing happens on phones. Make sure the homepage, tool pages, and explore page render well on mobile. PH's own app drives a lot of traffic.

---

## Upvote Strategy

### Morning of Launch (8:00 AM GMT / 12:00 AM PT)
- **Tweet the launch link** from both personal accounts and the IndieStack account. Pin the tweet. Include a screenshot or GIF, not just a link.
- **Post on LinkedIn** with a short personal story: "Two CS students, 10 weeks, zero budget. We just launched on Product Hunt..."
- **Share in relevant Discord/Slack communities**: Indie Hackers, WIP.co, Developer DAO, any AI-focused communities you're in. Don't just drop a link — write a genuine message about what you built and why.

### DM Outreach
- Reference contacts from `LAUNCH_CONTENT.md` — DM maker contacts who have their own PH audiences
- Keep DMs short and genuine: "Hey [name], we launched IndieStack on PH today — it's a curated index of indie tools with an MCP server for AI assistants. Would love your thoughts if you have a sec: [link]"
- Do NOT say "please upvote" — say "would love your feedback." People who find it interesting will upvote naturally.

### Throughout the Day
- Respond to every PH comment within 10 minutes
- Cross-post interesting PH comments to Twitter with commentary
- If you hit milestones (Top 10, Top 5, #1), tweet about it — social proof drives more visits

### What NOT to Do
- **Do not use upvote services or pods.** Product Hunt's detection is sophisticated. Accounts that only upvote during launches get flagged, and your product gets shadow-deprioritised. It's not worth the risk.
- **Do not create fake accounts.** PH requires email verification and has device fingerprinting. Getting caught means a permanent ban.
- **Do not send mass emails asking for upvotes.** This violates PH's terms and reads as spam. A personal DM to 20 people you actually know is fine. A Mailchimp blast to 500 people is not.
- **Do not obsess over the leaderboard position.** A #5 finish with 30 genuine comments is worth more long-term than a #1 finish from botted upvotes with zero engagement. The comments and relationships are the real value.
