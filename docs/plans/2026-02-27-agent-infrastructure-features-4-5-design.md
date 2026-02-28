# Agent Infrastructure — Features 4 & 5 Design

**Date:** 2026-02-27
**Context:** Features 1-3 (Prompt Cache Index, Agent Citation Tracking, Dual-Audience Messaging) are deployed. Features 4-5 complete the agent infrastructure vision.

---

## Feature 4: Stack Builder API

### Purpose
An agent says "I need auth, payments, and analytics." The Stack Builder returns the best indie tool for each need, matching Vibe Stacks if they cover the requirements, plus total tokens saved. This is the "procurement endpoint" — agents reach for it before architecting.

### Approach: Keyword-to-Category Mapping
A `NEED_MAPPINGS` dict maps ~20 common need keywords to category slugs, search terms, and known competitors. Unrecognized needs fall back to FTS5 search.

### Endpoints
- `GET /api/stack-builder?needs=auth,payments,analytics&budget=50` — JSON API
- `build_stack` MCP tool — wraps the API

### Data Flow
1. Parse comma-separated needs
2. For each need: resolve via NEED_MAPPINGS → get category slug + search terms
3. Query tools by category (precision), then FTS5 (catchall)
4. Also query Vibe Stacks for coverage overlap
5. Return per-need tools + matching stacks + summary with tokens saved

### Response Format
```json
{
  "stack": [
    {
      "need": "auth",
      "category": "Authentication",
      "tokens_saved": 50000,
      "matched_via": "category",
      "tools": [
        {
          "name": "Tool", "slug": "tool", "tagline": "...",
          "price": "Free", "verified": true, "upvotes": 12,
          "url": "https://indiestack.fly.dev/tool/tool"
        }
      ]
    }
  ],
  "matching_stacks": [
    {
      "title": "SaaS Starter", "slug": "saas-starter",
      "coverage": ["auth", "payments"], "discount": 15,
      "url": "https://indiestack.fly.dev/stacks/saas-starter"
    }
  ],
  "summary": {
    "total_needs": 3, "needs_covered": 3,
    "total_tokens_saved": 160000
  }
}
```

### NEED_MAPPINGS (subset)
```python
{
    "auth": {"category": "authentication", "terms": ["auth","login","SSO"], "competitors": ["Auth0","Firebase Auth","Okta"]},
    "payments": {"category": "payments", "terms": ["payments","billing","checkout"], "competitors": ["Stripe","PayPal"]},
    "analytics": {"category": "analytics-metrics", "terms": ["analytics","metrics","tracking"], "competitors": ["Google Analytics","Mixpanel"]},
    "email": {"category": "email-marketing", "terms": ["email","newsletter","drip"], "competitors": ["Mailchimp","SendGrid"]},
    "invoicing": {"category": "invoicing-billing", "terms": ["invoicing","billing","receipts"], "competitors": ["FreshBooks","QuickBooks"]},
    "monitoring": {"category": "monitoring-uptime", "terms": ["monitoring","uptime","alerting"], "competitors": ["Datadog","PagerDuty"]},
    "forms": {"category": "forms-surveys", "terms": ["forms","surveys","feedback"], "competitors": ["Typeform","Google Forms"]},
    "scheduling": {"category": "scheduling-booking", "terms": ["scheduling","booking","calendar"], "competitors": ["Calendly","Acuity"]},
    "cms": {"category": "cms-content", "terms": ["cms","content","blog"], "competitors": ["WordPress","Contentful"]},
    "support": {"category": "customer-support", "terms": ["support","helpdesk","chat"], "competitors": ["Zendesk","Intercom"]},
    "seo": {"category": "seo-tools", "terms": ["seo","search","ranking"], "competitors": ["Ahrefs","SEMrush"]},
    "storage": {"category": "file-management", "terms": ["storage","files","upload"], "competitors": ["AWS S3","Dropbox"]},
    "crm": {"category": "crm-sales", "terms": ["crm","sales","leads"], "competitors": ["Salesforce","HubSpot"]},
    "devtools": {"category": "developer-tools", "terms": ["developer","tools","sdk"], "competitors": []},
    "ai": {"category": "ai-automation", "terms": ["ai","automation","ml"], "competitors": ["OpenAI","AWS AI"]},
    "design": {"category": "design-creative", "terms": ["design","ui","creative"], "competitors": ["Figma","Canva"]},
    "testing": {"category": "testing-qa", "terms": ["testing","qa","test"], "competitors": ["Selenium","Cypress"]},
    "feedback": {"category": "feedback-reviews", "terms": ["feedback","reviews","nps"], "competitors": ["Hotjar","UserTesting"]},
}
```

### Error Handling
- Empty needs → 400 with example usage
- Unrecognized need → FTS5 fallback, `"matched_via": "search"`
- No tools found → empty tools array with note
- Budget=0 means no limit (don't filter)

---

## Feature 5: Use Case Pages

### Purpose
Human-readable comparison pages with structured data that agents can also parse. Each shows tools for a use case ranked by trust and price. Dual-audience: SEO for humans, JSON-LD + API for agents.

### Approach: Curated Dict + Category Fallback
~15 hand-curated use cases with quality copy. Any category without a curated entry gets an auto-generated page.

### Endpoints
- `GET /use-cases` — HTML index page (grid of all use cases)
- `GET /use-cases/{slug}` — HTML detail page (comparison table, build-vs-buy)
- `GET /api/use-cases` — JSON API listing all use cases
- `GET /api/use-cases/{slug}` — JSON API for single use case with tools

### USE_CASES Dict Structure
```python
{
    "auth": {
        "title": "Authentication",
        "description": "Add login, signup, SSO, and session management.",
        "category_slug": "authentication",
        "search_terms": ["auth", "login", "SSO"],
        "competitors": ["Auth0", "Firebase Auth", "Okta", "Cognito"],
        "build_estimate": "2-3 weeks",
        "icon": "🔐",
    },
    # ... 14 more curated entries
}
```

### HTML Detail Page Structure
1. Hero: icon + title + description
2. Stats bar: X tools | Y verified | Z tokens saved
3. Build vs Buy: estimated effort to build from scratch vs using a tool
4. Comparison Table: Tool | Price | Verified | Upvotes | Replaces
5. Competitors section: mainstream tools these replace
6. CTA: "Build your full stack" → stack builder
7. JSON-LD: ItemList schema
8. Breadcrumbs: Home > Use Cases > {Title}

### Category Fallback
Any category slug not in USE_CASES gets an auto-generated page:
- Title from category name
- Generic description
- Token estimate from CATEGORY_TOKEN_COSTS
- Tools from category query
- No custom competitors list

### SEO
- JSON-LD ItemList on each detail page
- Breadcrumb JSON-LD
- OG tags
- Internal links to tool pages, alternatives, stacks

### Files
- New: `routes/use_cases.py`
- Modified: `main.py` (register router, add to sitemap, JSON API endpoints, llms.txt)
- Modified: `mcp_server.py` (add build_stack tool)

---

## Implementation Order
1. Feature 4: Stack Builder API (main.py + mcp_server.py)
2. Feature 5: Use Case Pages (new route file + main.py registration)
3. Verify + deploy together
