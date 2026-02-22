# IndieStack Launch Content

> Prepared 2026-02-20. All copy is draft — edit freely before posting.

---

## 1. The "Naked Truth" LinkedIn/Twitter Post

### LinkedIn Version (~400 words)

---

**I built a full-stack marketplace over 10 weeks. It has 100+ tools, Stripe payments, an MCP server, and zero real users. Here's what I learned.**

I'm Patrick, a CS student at Cardiff University. Over the past 10 weeks, my co-founder Ed and I built IndieStack — a curated marketplace where indie SaaS tools compete with the giants.

The tech stack is deliberately boring: Python/FastAPI, SQLite, pure HTML templates, zero JavaScript frameworks. Deployed on Fly.io. The entire thing runs on a single server.

Here's what's inside:

- 21 route files, 29 database tables, 44+ API endpoints
- Stripe Connect integration with real payment processing (makers keep ~92%)
- Full-text search with faceted filtering across 20 categories and 197 tag pages
- A working MCP server — so Claude Code, Cursor, and Windsurf can search our marketplace before developers waste tokens rebuilding something that already exists
- Programmatic SEO pages ("alternatives to Intercom," "alternatives to Mailchimp")
- Embeddable SVG trust badges, dynamic OG share cards, RSS feeds
- Email verification, password reset, weekly digest newsletters
- A maker dashboard with analytics, changelogs, milestone tracking, and search intent data

100+ indie tools are listed. Reviews exist. Upvotes exist. The trending algorithm works. Vibe Stacks (curated bundles at 15% off) are ready to go.

And the user count? Zero.

Every review is seeded. Every upvote is synthetic. Not a single organic user has signed up, listed a tool, or made a purchase. The site exists in a vacuum.

This is the most important thing I've learned: building is the easy part. Distribution is the real skill. I spent 10 rounds adding features for imaginary users instead of talking to real ones. I built a notification system before anyone needed to be notified.

If I were starting over, I'd list 10 tools, DM 10 makers, and ship in a weekend. The other 20 database tables could wait.

But I don't regret it. This project taught me more about full-stack architecture, payment systems, search infrastructure, and API design than any module at university. And the codebase is real — no tutorials, no templates, no AI-generated boilerplate that I don't understand.

IndieStack is live: https://indiestack.fly.dev

If you're a hiring manager — I'd love to chat about the engineering decisions behind this. The Stripe Connect integration alone has a few good war stories.

If you're an indie maker — your tool might already be listed. Claim it for free and get analytics, changelogs, and an embeddable trust badge: https://indiestack.fly.dev/explore

#buildinpublic #indiedev #python #fastapi #saas #portfolio

---

### Twitter/X Thread Version (10 tweets)

---

**Tweet 1 (Hook)**

I'm a CS student. I spent 10 weeks building a full-stack marketplace.

It has 100+ tools, Stripe payments, an MCP server, and 44+ API endpoints.

It has zero real users.

Here's the whole story:

**Tweet 2 (What it is)**

IndieStack is a curated marketplace for indie SaaS tools.

The pitch: developers waste tokens rebuilding tools that already exist. We index the indie alternatives so your AI assistant finds them first.

https://indiestack.fly.dev

**Tweet 3 (The stack)**

The stack is deliberately boring:

- Python/FastAPI
- SQLite (WAL mode)
- Pure HTML string templates
- Zero JS frameworks
- Deployed on Fly.io

One server. One database file. 21 route files. That's it.

**Tweet 4 (What's inside)**

What we actually built:

- 29 database tables
- 44+ API endpoints
- Stripe Connect (makers keep ~92%)
- Full-text search + 197 tag pages
- Programmatic SEO ("alternatives to X")
- Email system (verification, reset, weekly digest)
- Dark mode, mobile nav, the works

**Tweet 5 (The MCP angle)**

The wildest feature: a working MCP server.

Claude Code, Cursor, and Windsurf can search IndieStack before you build from scratch.

"Find me an indie analytics tool" -> returns Plausible, Fathom, Simple Analytics with install snippets.

This is the future of dev tool discovery.

**Tweet 6 (Trust system)**

We built a full trust system:

- Verified badge (gold)
- Ejectable badge (green) — clean data export, no lock-in
- Maker Pulse — freshness indicator
- Changelog Streak — fire badge for active tools
- Indie Score — composite trust metric

Trust infrastructure before trust was earned. Classic.

**Tweet 7 (The honest part)**

Now the uncomfortable truth.

User count: 0
Organic signups: 0
Real purchases: 0
Maker claims: 0

Every review is seeded. Every upvote is synthetic. The trending algorithm trends nothing.

I built a notification system before anyone needed to be notified.

**Tweet 8 (The lesson)**

The lesson cost me 10 weeks:

Building is the easy part. Distribution is the real skill.

I could have listed 10 tools, DMed 10 makers, and shipped in a weekend. Instead I built 29 database tables for imaginary users.

Don't be me. Ship, then build.

**Tweet 9 (No regrets)**

But I don't regret it.

This project taught me more about:
- Payment integrations (Stripe Connect)
- Search infrastructure (FTS5)
- API design (MCP protocol)
- Auth systems
- Email delivery

...than any university module.

The codebase is real. No tutorials. No templates.

**Tweet 10 (CTA)**

IndieStack is live: https://indiestack.fly.dev

If you're hiring — I'd love to talk about the engineering behind this.

If you're an indie maker — your tool might already be listed. Claim it free. You get analytics, changelogs, and an embeddable trust badge.

DMs open.

---

## 2. The "Hostage Rescue" DM Templates

### Version A — Twitter DM (short, ~100 chars)

> Hey! Your tool {Tool Name} is listed on IndieStack. Claim it free and get analytics + a trust badge: https://indiestack.fly.dev/tool/{slug}

### Version B — Twitter DM (medium, ~250 chars)

> Hey {Name}! I built IndieStack — a curated marketplace for indie tools. {Tool Name} is already listed and getting search impressions. If you claim it (30 sec, verify via GitHub), you get an analytics dashboard, changelog posting, embeddable SVG badge, and MCP server integration. Totally free: https://indiestack.fly.dev/tool/{slug}

### Version C — Email (detailed)

**Subject line:** Your tool {Tool Name} is already listed on IndieStack — claim it?

**Body:**

Hi {Name},

I'm Patrick, a CS student who built IndieStack — a curated marketplace where developers discover indie SaaS tools instead of rebuilding from scratch. Think of it as an indie-first alternative to G2 or Product Hunt, with an MCP server so AI coding assistants can recommend your tool automatically.

{Tool Name} is already listed on IndieStack and indexed in our search engine and MCP server. Developers searching for tools in your category will find it.

If you claim your listing (takes about 30 seconds via GitHub verification), you get:

- An analytics dashboard showing views, clicks, and search queries that surface your tool
- Changelog posting so developers see you're actively maintained
- An embeddable SVG trust badge for your website or README
- MCP server integration — Claude Code, Cursor, and Windsurf can recommend your tool to developers

It's completely free. Our standard platform fee is 5% on paid transactions, but the first 100 makers to claim get **0% platform fee locked in forever**. You keep everything minus Stripe's ~3%.

Claim your listing here: https://indiestack.fly.dev/tool/{slug}

Happy to answer any questions. And if you'd rather not be listed, just let me know and I'll remove it immediately.

Cheers,
Patrick

---

## 3. Maker Contact List

### SEED_MAKERS with Twitter handles and tool mappings

| Maker | Tool(s) | Tool Slug | Twitter | GitHub | Status |
|-------|---------|-----------|---------|--------|--------|
| Uku Taht | Plausible Analytics | `plausible-analytics` | [@ukutaht](https://twitter.com/ukutaht) | [plausible](https://github.com/plausible) | |
| Jack Ellis | Fathom Analytics | `fathom-analytics` | [@JackEllis](https://twitter.com/JackEllis) | TBD | |
| Adriaan van Rossum | Simple Analytics | `simple-analytics` | -- | [simpleanalytics](https://github.com/simpleanalytics) | |
| Justin Duke | Buttondown | `buttondown` | [@justinmduke](https://twitter.com/justinmduke) | [buttondown](https://github.com/buttondown) | |
| Nathan Barry | Kit | `kit` | [@nathanbarry](https://twitter.com/nathanbarry) | TBD | |
| Fabrizio Rinaldi | Mailbrew | `mailbrew` | -- | TBD | |
| AJ | Carrd | `carrd` | [@ajlkn](https://twitter.com/ajlkn) | TBD | |
| Traf | Super.so | `super-so` | -- | TBD | |
| Kevin Conti | Typedream | `typedream` | -- | TBD | |
| Sahil Lavingia | Gumroad | `gumroad` | [@shl](https://twitter.com/shl) | [shl](https://github.com/shl) | |
| JJ Lee | Lemon Squeezy | `lemon-squeezy` | -- | TBD | |
| Christian Owens | Paddle | `paddle` | -- | TBD | |
| Jake Cooper | Railway | `railway` | -- | [jake-coop](https://github.com/jake-coop) | |
| Anurag Goel | Render | `render` | -- | TBD | |
| Sam Lambert | PlanetScale | `planetscale` | -- | TBD | |
| Fabrizio Rinaldi | Typefully | `typefully` | -- | TBD | |
| Yannick Veys | Hypefury | `hypefury` | -- | TBD | |
| Joel Gascoigne | Buffer | `buffer` | [@joelgascoigne](https://twitter.com/joelgascoigne) | [joelgascoigne](https://github.com/joelgascoigne) | |
| Joshua Beckman | Pika | `pika` | -- | TBD | |
| Mehdi Merah | Screely | `screely` | -- | TBD | |
| Devin Jacoviello | Shots.so | `shots-so` | -- | TBD | |
| Sarah Cannon | Canny | `canny` | -- | TBD | |
| Fred Rivett | Nolt | `nolt` | -- | TBD | |
| Guilherme Oenning | Fider | `fider` | -- | [goenning](https://github.com/goenning) | |
| Hannes Lenke | Checkly | `checkly` | -- | [checkly](https://github.com/checkly) | |
| Ralph Chua | Better Stack | `better-stack` | -- | TBD | |

### Priority Outreach Order

Makers with known Twitter handles should be contacted first (DM is faster and more personal than cold email). Prioritized by approachability and indie alignment:

1. **Uku Taht** (@ukutaht) — Plausible is the poster child of indie analytics. Solo maker. Open source. Perfect fit.
2. **Justin Duke** (@justinmduke) — Buttondown is indie-native, Justin is active on Twitter, and the tool is both Verified and Ejectable on IndieStack.
3. **AJ** (@ajlkn) — Carrd is one of the most successful solo-maker tools. AJ is active on Twitter.
4. **Jack Ellis** (@JackEllis) — Fathom is privacy-first analytics, strong indie ethos.
5. **Joel Gascoigne** (@joelgascoigne) — Buffer's founder is very public about indie/transparent business. Bigger company but indie roots.
6. **Nathan Barry** (@nathanbarry) — Kit (formerly ConvertKit) is larger but Nathan is the face of indie SaaS. A claim from him would be a massive signal.
7. **Sahil Lavingia** (@shl) — Gumroad's founder is extremely online and supportive of indie makers. Even a retweet would be huge.

### Claim Link Format

For each maker DM, the claim link is:

```
https://indiestack.fly.dev/tool/{tool-slug}
```

The tool page has a "Claim this tool" button visible to logged-in users. Claiming verifies via GitHub URL match.

### Tracking

Fill in the **Status** column as outreach progresses:
- **DMed** — message sent, awaiting response
- **Replied** — got a response (note positive/negative)
- **Claimed** — maker claimed their listing
- **No response** — no reply after 7 days
- **Declined** — asked to be removed or not interested
