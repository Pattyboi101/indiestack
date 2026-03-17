---
paths:
  - "src/indiestack/payments.py"
  - "src/indiestack/routes/pricing.py"
  - "src/indiestack/routes/dashboard.py"
---

# IndieStack — Stripe Integration

## Secrets
- Stripe keys on Fly secrets: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- Patrick's Stripe email: ameyjonesp@gmail.com

## Webhooks
- Endpoint: `POST /webhooks/stripe` — handles `checkout.session.completed` + `customer.subscription.deleted`
- Webhook endpoint ID: `we_1TAFCFKzUt3DIisgMKx2boTz`
- Always verify `Stripe-Signature` header on webhooks

## Pro Gating
- `check_pro()` is the standard Pro gating function — use it for all Pro features

## Pricing
- Pro subscription: $19/mo or $99/year Founder tier (50 seats)
- Demand Signals Pro: $15/mo, separate product (`prod_U8VwBtZHSxDmoB`, price `price_1TAEuAKzUt3DIisg4a0waYsy`)
- Subscribe via `POST /api/subscribe/demand-pro` (uses `request.state.user`)

## Pro Features
Find Market Gaps, See Who Recommends You, Weekly AI Report, Pro Dashboard, 1000 API queries/day, Data Export, Search Boost

## Email
- SMTP: Gmail via Fly secrets (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`: pajebay1@gmail.com)
