# The Indie Tool Stack: What Solo Founders Actually Use in 2026

*We looked at what 100+ indie makers are actually running their businesses on. Spoiler: it's not Salesforce and AWS.*

---

## The Problem With "What Tools Do You Use?" Posts

Every month someone posts "what's your tech stack?" on Reddit and the answers are always the same: Stripe, Vercel, Supabase, Clerk, Resend. There's nothing wrong with those tools but they're only part of the picture -- and most of them are VC-backed companies that will eventually need to justify their valuations with price hikes.

We run [IndieStack](https://indiestack.fly.dev), a directory of 350+ indie and open-source developer tools. We see what makers are actually using, what they're switching to, and what's getting the most clicks. Here's what the real indie tool stack looks like.

---

## Analytics: The Great Google Analytics Exodus

**What most people use:** Google Analytics, Mixpanel, Amplitude
**What indie founders are switching to:**

- **Plausible** -- lightweight, privacy-focused, open-source. One script tag, no cookies, GDPR compliant out of the box. This is the single most popular switch we see on IndieStack.
- **Umami** -- self-hostable alternative to Plausible. Free if you run it yourself, incredibly lightweight.
- **PostHog** -- if you need product analytics (funnels, session replays, feature flags) not just page views. Open-source core with a generous free tier.

The pattern: founders are moving away from heavy analytics platforms toward tools that respect user privacy and don't require cookie banners. [Compare indie analytics tools](https://indiestack.fly.dev/category/analytics)

---

## Authentication: Nobody Wants to Build Login Screens

**What most people use:** Auth0, Firebase Auth, Clerk
**What indie founders are switching to:**

- **SuperTokens** -- open-source, prebuilt UI components, self-hostable. The migration docs are excellent if you're switching from another provider.
- **Logto** -- clean admin console, social login out of the box, RBAC. The developer experience is noticeably better than Auth0.
- **Lucia** -- if you want something minimal that integrates with your existing framework rather than being a separate service.

The pattern: indie founders want auth that doesn't charge per MAU and doesn't lock them into a vendor. Self-hostable options are winning. [Compare indie auth tools](https://indiestack.fly.dev/category/authentication)

---

## Deployment: The Heroku Refugees

**What most people use:** AWS, Vercel, Railway
**What indie founders are switching to:**

- **Coolify** -- self-hosted Heroku/Netlify alternative. Deploy anything with Docker, automatic SSL, built-in monitoring. The UI is surprisingly polished.
- **Dokploy** -- similar to Coolify but lighter. Good for single-server deployments.
- **Fly.io** -- not self-hosted but indie-friendly pricing. Pay for what you use, no surprise bills. (Full disclosure: IndieStack runs on Fly.io)

The pattern: after Heroku killed its free tier, a wave of founders moved to self-hosted deployment platforms. The tooling has caught up to the point where self-hosting is genuinely easier than managing AWS. [Compare indie deployment tools](https://indiestack.fly.dev/category/deployment)

---

## Payments: Beyond Stripe

**What most people use:** Stripe (and nothing else)
**What indie founders are adding:**

- **Hyperswitch** -- open-source payment orchestrator. Route payments through multiple processors, reduce fees, handle failovers. Think of it as a layer on top of Stripe rather than a replacement.
- **Lago** -- open-source billing engine. If you have usage-based pricing, metered billing, or complex plan structures, Lago handles the invoicing and metering side that Stripe doesn't do well.

The pattern: Stripe is still the default for payment processing, but founders are adding indie tools on top to handle billing logic, usage metering, and multi-processor routing. [Compare indie payment tools](https://indiestack.fly.dev/category/payments)

---

## Email: The SMTP Renaissance

**What most people use:** SendGrid, Mailchimp, ConvertKit
**What indie founders are switching to:**

- **Listmonk** -- self-hosted newsletter and mailing list manager. Single Go binary, handles millions of emails. Free forever because you run it yourself.
- **Buttondown** -- indie-run newsletter platform. Clean, simple, no bloat. The anti-Mailchimp.
- **Resend** -- developer-first transactional email. Actually this one is VC-backed but developers love the DX so it keeps showing up.

The pattern: newsletter/marketing email is moving to self-hosted (Listmonk) or indie alternatives (Buttondown). Transactional email is less differentiated -- most people pick whatever has the best API. [Compare indie email tools](https://indiestack.fly.dev/category/email)

---

## Customer Support: Chat Without the $50/Agent/Month

**What most people use:** Intercom, Zendesk, Freshdesk
**What indie founders are switching to:**

- **Chatwoot** -- open-source Intercom alternative. Live chat, email, social media -- all in one inbox. Self-hostable.
- **Formbricks** -- open-source surveys and feedback collection. Not a chat tool but solves the same problem (understanding what users want) differently.

The pattern: Intercom's pricing ($74/agent/month) is absurd for a solo founder. Chatwoot gives you 90% of the functionality for free. [Compare indie support tools](https://indiestack.fly.dev/category/customer-support)

---

## Monitoring & Error Tracking: Know When Things Break

**What most people use:** Datadog, Sentry, New Relic
**What indie founders are switching to:**

- **GlitchTip** -- open-source Sentry alternative. Same error tracking, fraction of the cost.
- **Uptime Kuma** -- self-hosted uptime monitoring with a beautiful dashboard. Supports 20+ notification types.
- **Highlight.io** -- open-source full-stack monitoring (errors, logs, session replay).

The pattern: observability tools are absurdly expensive at scale. Self-hosted alternatives have reached feature parity for indie-scale workloads. [Compare indie monitoring tools](https://indiestack.fly.dev/category/monitoring)

---

## The Full Stack

Here's what a complete indie tool stack looks like in 2026:

| Need | Indie Tool | Replaces |
|------|-----------|----------|
| Analytics | Plausible / Umami | Google Analytics |
| Auth | SuperTokens / Logto | Auth0 / Clerk |
| Deployment | Coolify / Fly.io | Heroku / AWS |
| Payments | Stripe + Lago | Stripe + custom billing |
| Email | Listmonk / Buttondown | Mailchimp / SendGrid |
| Support | Chatwoot | Intercom |
| Monitoring | GlitchTip + Uptime Kuma | Sentry + Datadog |
| Search | Meilisearch / Typesense | Algolia |
| CMS | Strapi / Directus | Contentful |
| Forms | Formbricks / Tally | Typeform |

**Total cost if self-hosted:** $5-20/month for a VPS
**Total cost of enterprise equivalents:** $500-2000/month

---

## How to Find These Tools

The hardest part of going indie isn't switching -- it's knowing what exists. That's why we built [IndieStack](https://indiestack.fly.dev). It's a curated directory of 350+ indie and open-source tools across 21 categories, with side-by-side comparisons, maker profiles, and an MCP server so AI agents can search it too.

Every tool mentioned in this post (and hundreds more) is listed there. Browse by category, compare alternatives, and find the indie tool for whatever you're building.

---

*IndieStack is a free, curated directory for indie developer tools. Browse tools at [indiestack.fly.dev](https://indiestack.fly.dev).*
