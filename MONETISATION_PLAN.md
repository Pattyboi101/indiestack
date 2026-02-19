# IndieStack Monetisation Plan — From Directory to Marketplace

## The Problem Right Now

IndieStack is an advertising board. Users find a tool, click "Visit Website", and leave forever. We capture zero value from that transaction. The maker gets a free listing, the buyer leaves our site, and we get nothing.

## The Vision

**IndieStack becomes the Etsy for simple software tools.** Makers list tools with a price. Buyers purchase directly on IndieStack. We take a cut. Simple.

Target buyer: **non-technical people** who want a tool that solves a specific problem (invoice generator, meal planner, booking page, habit tracker) without building it themselves.

Target seller: **developers using AI coding tools** (Claude Code, Cursor, etc.) who can build focused utility tools in hours and want passive income.

Price sweet spot: **£5–£19** per tool (impulse buy territory).

---

## Revenue Streams (in priority order)

### 1. Marketplace Commission (primary — build this first)
- Makers set a price on their tool (free tools still allowed)
- Buyers pay on IndieStack via Stripe Checkout
- **IndieStack takes 20% commission** (industry standard for curated marketplaces)
- Maker receives 80% via Stripe Connect (automated payouts)
- Example: tool sells for £9 → maker gets £7.20, IndieStack gets £1.80

### 2. Verified Maker Badge (already built — just needs payment gate)
- **£7/month** subscription via Stripe
- Benefits: ranking boost (already implemented), gold badge, analytics on views/clicks
- Stripe Billing for recurring subscription

### 3. Featured Placement (bolt-on, easy money)
- **£15 one-off** to pin a tool at the top of its category for 7 days
- Shown with a subtle "Featured" label
- Limit: 1 featured slot per category at a time (scarcity = value)

---

## What Needs Building

### Phase 1: Stripe Connect + Tool Purchases

**Database changes:**
- Add `price_pence` (INTEGER, nullable — null = free tool) to `tools` table
- Add `stripe_account_id` to a new `makers` table (or add to tools for now)
- Add `purchases` table: id, tool_id, buyer_email, stripe_session_id, amount_pence, commission_pence, created_at
- Add `delivery_type` to tools: 'link' (hosted URL), 'download' (file), or 'license_key'
- Add `delivery_url` or `delivery_content` to tools (what the buyer gets after paying)

**New routes:**
- `GET /tool/{slug}` — update existing page: show price + "Buy Now" button (replaces "Visit Website" for paid tools). Free tools keep the current "Visit Website" link.
- `POST /api/checkout` — creates a Stripe Checkout Session, redirects buyer to Stripe
- `GET /purchase/success?session_id=...` — Stripe redirects here after payment. Verify session, record purchase, show delivery (download link / hosted URL / license key)
- `GET /purchase/cancel` — buyer cancelled, redirect back to tool page
- `POST /webhooks/stripe` — Stripe webhook for payment confirmations (belt-and-suspenders with the success redirect)

**Stripe integration:**
- Use Stripe Checkout (hosted payment page — no PCI scope for us)
- Use Stripe Connect Express for maker payouts (makers onboard via Stripe's hosted flow)
- Set `application_fee_amount` to 20% on each checkout session
- Environment variables: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_CONNECT_CLIENT_ID`

**Submit form changes:**
- Add optional "Price (£)" field — leave blank for free
- Add "Delivery type" dropdown: Link to hosted tool / Downloadable file / License key
- Add "Delivery URL or content" field
- Add "Connect your Stripe account" button (redirects to Stripe Connect onboarding)

**Admin changes:**
- Show price and delivery info in pending review
- Ability to set/override price

### Phase 2: Verified Maker Subscription (Stripe Billing)

- Add Stripe Billing subscription for verified makers
- `POST /api/subscribe-verified` — creates Stripe Checkout in subscription mode
- Webhook handles `customer.subscription.created`, `customer.subscription.deleted`
- Auto-toggle `is_verified` based on subscription status
- Maker dashboard page (`GET /dashboard`) showing: subscription status, tools listed, total sales, earnings

### Phase 3: Featured Placement

- Add `featured_until` (TIMESTAMP, nullable) to `tools` table
- `POST /api/feature/{tool_id}` — Stripe Checkout for one-off £15
- On success, set `featured_until` = now + 7 days
- Update category queries: featured tools (where `featured_until > now`) pinned at top with "Featured" badge
- Limit: reject if category already has an active featured tool

---

## Key Technical Decisions

1. **Stripe Checkout (not custom payment form)** — Stripe hosts the payment page. Zero PCI compliance burden. Buyers trust the Stripe branding. We just redirect.

2. **Stripe Connect Express** — Makers onboard through Stripe's hosted flow (KYC, bank details, etc.). We never touch their banking info. Payouts are automatic.

3. **No user accounts for buyers (yet)** — Purchases tied to email address. Buyer gets a confirmation email with their delivery link. Keep it frictionless. Add accounts later if needed.

4. **No file hosting (yet)** — For "download" delivery type, maker provides a URL (Gumroad, S3, Google Drive, etc.). We just reveal it after payment. Hosting files ourselves is Phase 4.

5. **Delivery via "purchase token"** — After payment, generate a unique token. The delivery page (`/purchase/success?token=xxx`) is only accessible with this token. Simple, no auth needed.

---

## Dependencies

- `stripe` Python package (add to pyproject.toml)
- Stripe account with Connect enabled
- Environment secrets on Fly.io: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

---

## Build Order for the Agent

1. Add `stripe` to pyproject.toml dependencies
2. Update `db.py`: new columns, new tables, new queries
3. Create `src/indiestack/payments.py`: Stripe helper functions (create checkout, verify webhook, create connect account link)
4. Update `submit.py`: add price + delivery fields
5. Update `tool.py`: show price + "Buy Now" button for paid tools
6. Create `src/indiestack/routes/purchase.py`: checkout, success, cancel, webhook routes
7. Update `admin.py`: show price/delivery in review
8. Wire new routes in `main.py`
9. Test end-to-end with Stripe test mode
10. Deploy

---

## Success Metrics

- First paid tool listed within 1 week of launch
- First sale within 2 weeks
- 10 paid tools listed within 1 month
- £100 in commission within 2 months

---

## What This Turns IndieStack Into

**Before:** "Here's a list of tools, go visit their websites" (advertising board)
**After:** "Find the tool, buy it here, get it instantly" (marketplace)

The moat becomes: curation (we review every tool), trust (buyers know they'll get what they paid for), and discovery (makers can't get found on their own).
