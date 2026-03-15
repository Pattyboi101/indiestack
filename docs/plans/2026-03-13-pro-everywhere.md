# IndieStack Pro Everywhere — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform IndieStack from a single-feature "Demand Signals Pro" ($15/mo, 0 customers) into a site-wide "Pro Everywhere" subscription ($19/mo) with Founder pricing ($99/year for first 50), agent citation notification emails as the primary conversion trigger, and API key-based rate limiting for MCP.

**Architecture:** Pro status is derived from the `subscriptions` table (no redundant `is_pro` flags). A shared `check_pro()` helper centralises the check. Feature gates are applied across dashboard, demand signals, agent citations, and API access. The Agent Citation Notification Loop runs as a weekly periodic task alongside the existing ego ping, emailing makers when their tools are cited by AI agents and gating the citation context behind Pro. Rate limiting transitions from IP-based to key-based for `/api/*` endpoints.

**Tech Stack:** Python 3 / FastAPI / aiosqlite / Stripe (subscriptions API) / stdlib smtplib (emails) / pure Python f-string HTML templates

**Key Environment Variables Required:**
- `STRIPE_PRO_PRICE_ID` — Stripe Price for Pro monthly ($19/mo) — **Patrick must create in Stripe Dashboard**
- `STRIPE_FOUNDER_PRICE_ID` — Stripe Price for Founder annual ($99/year) — **Patrick must create in Stripe Dashboard**
- Existing: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_DEMAND_PRO_PRICE_ID`

---

## Phase 1: Foundation — Shared Pro Helper + DB Migration

### Task 1: Create shared `check_pro()` helper in db.py

**Context:** Currently, every route that checks Pro status does its own inline SQL query against the `subscriptions` table. This duplicates logic and makes it hard to change the subscription check in one place. We need a single helper that all routes use.

**Files:**
- Modify: `src/indiestack/db.py` (add helper near line 2796, after `get_active_subscription()`)

**Step 1: Add the helper function**

Add this function directly after `get_active_subscription()` (line 2803):

```python
async def check_pro(db, user_id: int) -> bool:
    """Check if a user has an active Pro subscription (any plan)."""
    if not user_id:
        return False
    sub = await get_active_subscription(db, user_id)
    return sub is not None
```

**Step 2: Add founder seat counter helper**

Add this function after `check_pro()`:

```python
async def get_founder_seat_count(db) -> int:
    """Count how many founder subscriptions have been sold."""
    cursor = await db.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE plan = 'founder' AND status = 'active'"
    )
    row = await cursor.fetchone()
    return row[0] if row else 0
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add check_pro() and get_founder_seat_count() helpers"
```

---

### Task 2: Update subscription webhook to handle 'pro' and 'founder' plans

**Context:** The current webhook handler at `main.py:2776` only handles `demand_pro` plan. We need it to also accept `pro` and `founder` plans from Stripe metadata.

**Files:**
- Modify: `src/indiestack/main.py` (lines 2790-2806)

**Step 1: Update the checkout.session.completed handler**

Replace lines 2796-2806 (the `if plan == "demand_pro" and user_id:` block) with:

```python
        if plan in ("demand_pro", "pro", "founder") and user_id:
            stripe_sub_id = session.get("subscription", "")
            try:
                await d.execute("""
                    INSERT INTO subscriptions (user_id, stripe_subscription_id, plan, status)
                    VALUES (?, ?, ?, 'active')
                """, (int(user_id), stripe_sub_id, plan))
                await d.commit()
                logger.info(f"{plan} subscription created for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to create subscription: {e}")
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: webhook handles pro and founder subscription plans"
```

---

### Task 3: Create `/api/subscribe/pro` endpoint

**Context:** The existing `/api/subscribe/demand-pro` endpoint (main.py:2747) creates a Stripe Checkout for the old $15 plan. We need a new endpoint for Pro ($19/mo) and Founder ($99/year) that reads from new env vars. Keep the old endpoint working for backwards compatibility.

**Files:**
- Modify: `src/indiestack/main.py` (add after line 2773, after the existing demand-pro endpoint)

**Step 1: Add the new subscription endpoint**

Add after the existing `/api/subscribe/demand-pro` endpoint (after line 2773):

```python
@app.post("/api/subscribe/pro")
async def subscribe_pro(request: Request):
    """Create a Stripe Checkout session for IndieStack Pro."""
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    plan = body.get("plan", "pro")  # "pro" or "founder"

    import stripe
    stripe.api_key = _os.environ.get("STRIPE_SECRET_KEY")

    if plan == "founder":
        price_id = _os.environ.get("STRIPE_FOUNDER_PRICE_ID")
        # Check if founder seats are still available
        from indiestack.db import get_founder_seat_count
        seats_taken = await get_founder_seat_count(request.state.db)
        if seats_taken >= 50:
            return JSONResponse({"error": "All 50 Founding Member seats have been claimed!"}, status_code=410)
    else:
        price_id = _os.environ.get("STRIPE_PRO_PRICE_ID")
        plan = "pro"

    if not price_id:
        return JSONResponse({"error": "Subscription not configured"}, status_code=500)

    try:
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://indiestack.ai/dashboard?subscribed=true",
            cancel_url="https://indiestack.ai/pricing",
            customer_email=user.get("email", ""),
            metadata={"user_id": str(user["id"]), "plan": plan},
        )
        return JSONResponse({"checkout_url": checkout.url})
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        return JSONResponse({"error": "Payment service error"}, status_code=500)
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add /api/subscribe/pro endpoint with founder seat limit"
```

---

## Phase 2: Pricing Page

### Task 4: Build the Pro Everywhere pricing page

**Context:** Currently `/pricing` redirects to `/` (pricing.py is 12 lines). We need a full pricing page with two cards: Pro ($19/mo) and Founding Member ($99/year, limited to 50 seats). The page should follow IndieStack's design system (navy, cyan accent, DM Serif Display headings, 8px spacing base).

**Files:**
- Modify: `src/indiestack/routes/pricing.py` (complete rewrite, currently 12 lines)

**Step 1: Write the full pricing page**

Replace the entire contents of `pricing.py`:

```python
"""Pricing page — IndieStack Pro Everywhere."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.db import check_pro, get_founder_seat_count
from indiestack.routes.components import page_shell

router = APIRouter()

FOUNDER_TOTAL = 50


def _pro_features() -> list[tuple[str, str]]:
    """Features unlocked by Pro. Returns (feature, description) pairs."""
    return [
        ("Demand Signals Pro", "Full opportunity scores, trend sparklines, competition density"),
        ("Agent Citation Context", "See exactly which AI agents cite your tools and what they said"),
        ("Advanced Compatibility", "Submit and certify compatibility pairs, stack conflict checks"),
        ("Priority MCP Access", "1,000 API queries/day (vs 50 free)"),
        ("Custom Profile Domain", "Map your own domain to your IndieStack developer profile"),
        ("Founding Member Badge", "Permanent badge on your profile (founder plan only)"),
        ("Data Export", "Export demand clusters, citation data as JSON/CSV"),
        ("Priority Visibility", "Pro tools rank higher in search and MCP recommendations"),
    ]


def _free_features() -> list[str]:
    """Features included in the free tier."""
    return [
        "List unlimited tools",
        "Full search and discovery",
        "Public developer profile",
        "View compatibility data",
        "AI recommendation badge",
        "50 MCP queries/day",
        "Weekly ego ping emails",
    ]


@router.get("/pricing")
async def pricing_page(request: Request):
    user = request.state.user
    db = request.state.db

    is_pro = await check_pro(db, user['id']) if user else False
    founder_seats_taken = await get_founder_seat_count(db)
    founder_seats_left = max(0, FOUNDER_TOTAL - founder_seats_taken)
    founder_available = founder_seats_left > 0

    # Progress bar percentage
    founder_pct = min(100, int((founder_seats_taken / FOUNDER_TOTAL) * 100))

    # Free features list
    free_items = ""
    for f in _free_features():
        free_items += f'''
            <li style="padding:8px 0;display:flex;align-items:center;gap:10px;font-size:14px;color:var(--ink-muted);">
                <span style="color:var(--success-text, #22C55E);font-size:16px;flex-shrink:0;">&#10003;</span> {f}
            </li>'''

    # Pro features list
    pro_items = ""
    for feat, desc in _pro_features():
        pro_items += f'''
            <li style="padding:10px 0;border-bottom:1px solid var(--border);">
                <div style="font-size:14px;font-weight:600;color:var(--ink);">{feat}</div>
                <div style="font-size:13px;color:var(--ink-muted);margin-top:2px;">{desc}</div>
            </li>'''

    # CTA button logic
    if is_pro:
        pro_btn = '<div style="padding:14px;text-align:center;color:var(--success-text, #22C55E);font-weight:600;font-size:15px;">You\'re on Pro</div>'
        founder_btn = pro_btn
    elif not user:
        pro_btn = '<a href="/signup?next=/pricing" style="display:block;padding:14px;text-align:center;background:var(--accent);color:white;border-radius:8px;font-weight:600;font-size:15px;text-decoration:none;">Sign Up to Subscribe</a>'
        founder_btn = pro_btn
    else:
        pro_btn = '''<button onclick="subscribePro('pro')" id="pro-btn"
            style="display:block;width:100%;padding:14px;background:var(--accent);color:white;
                   border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;">
            Subscribe — $19/mo</button>'''
        if founder_available:
            founder_btn = f'''<button onclick="subscribePro('founder')" id="founder-btn"
                style="display:block;width:100%;padding:14px;background:var(--navy, #1A2D4A);color:var(--accent);
                       border:2px solid var(--accent);border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;">
                Claim Founding Seat — $99/year</button>'''
        else:
            founder_btn = '<div style="padding:14px;text-align:center;color:var(--ink-muted);font-weight:600;font-size:14px;">All 50 seats claimed</div>'

    # Founder seat progress bar
    founder_progress = ""
    if founder_available and not is_pro:
        founder_progress = f'''
        <div style="margin-top:20px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--ink-muted);margin-bottom:6px;">
                <span>{founder_seats_taken} of {FOUNDER_TOTAL} claimed</span>
                <span style="color:var(--accent);font-weight:600;">{founder_seats_left} left</span>
            </div>
            <div style="height:6px;background:var(--border);border-radius:999px;overflow:hidden;">
                <div style="height:100%;width:{founder_pct}%;background:var(--accent);border-radius:999px;transition:width 0.3s;"></div>
            </div>
        </div>'''

    body = f'''
    <section style="padding:80px 24px 48px;text-align:center;">
        <div class="container" style="max-width:900px;">
            <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                Pricing
            </p>
            <h1 style="font-family:var(--heading-font, var(--font-display));font-size:clamp(28px,4vw,42px);color:var(--ink);margin-bottom:16px;line-height:1.2;">
                Pro Everywhere
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:600px;margin:0 auto 48px;line-height:1.6;">
                One subscription. Every feature. Demand signals, agent citation intel,
                priority MCP access, and more &mdash; unlocked across the entire platform.
            </p>
        </div>
    </section>

    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:900px;">
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;align-items:start;">

                <!-- Free Tier -->
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:32px 24px;">
                    <p style="font-size:13px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                        Community
                    </p>
                    <div style="font-family:var(--heading-font, var(--font-display));font-size:42px;font-weight:700;color:var(--ink);margin-bottom:4px;">
                        Free
                    </div>
                    <p style="font-size:14px;color:var(--ink-muted);margin-bottom:24px;">
                        Forever. No credit card needed.
                    </p>
                    <ul style="list-style:none;padding:0;margin:0 0 24px;">
                        {free_items}
                    </ul>
                    <a href="/explore" style="display:block;padding:14px;text-align:center;border:1px solid var(--border);
                       color:var(--ink);border-radius:8px;font-weight:600;font-size:15px;text-decoration:none;">
                        Browse Tools
                    </a>
                </div>

                <!-- Pro Tier -->
                <div style="background:var(--bg-card);border:2px solid var(--accent);border-radius:16px;padding:32px 24px;position:relative;">
                    <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--accent);
                                color:white;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                                padding:4px 16px;border-radius:999px;">
                        Recommended
                    </div>
                    <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                        IndieStack Pro
                    </p>
                    <div style="font-family:var(--heading-font, var(--font-display));font-size:42px;font-weight:700;color:var(--ink);margin-bottom:4px;">
                        $19<span style="font-size:18px;color:var(--ink-muted);font-weight:400;">/month</span>
                    </div>
                    <p style="font-size:14px;color:var(--ink-muted);margin-bottom:24px;">
                        Cancel anytime. Everything in Community, plus:
                    </p>
                    <ul style="list-style:none;padding:0;margin:0 0 24px;">
                        {pro_items}
                    </ul>
                    {pro_btn}
                    <p id="subscribe-error" style="font-size:13px;color:var(--error-text, #EF4444);margin-top:12px;display:none;text-align:center;"></p>
                </div>
            </div>

            <!-- Founder Pricing Card -->
            {"" if is_pro else f"""
            <div style="margin-top:32px;background:var(--navy, #1A2D4A);border-radius:16px;padding:32px;text-align:center;">
                <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                    Founding Member
                </p>
                <div style="font-family:var(--heading-font, var(--font-display));font-size:36px;font-weight:700;color:white;margin-bottom:4px;">
                    $99<span style="font-size:18px;color:rgba(255,255,255,0.5);font-weight:400;">/year</span>
                </div>
                <p style="font-size:14px;color:rgba(255,255,255,0.6);margin-bottom:4px;">
                    Everything in Pro. 56% off, locked for life.
                </p>
                <p style="font-size:13px;color:var(--accent);margin-bottom:24px;">
                    Plus a permanent Founding Member badge on your profile.
                </p>
                <div style="max-width:320px;margin:0 auto;">
                    {founder_btn}
                    {founder_progress}
                </div>
            </div>
            """}
        </div>
    </section>

    <section style="padding:0 24px 80px;">
        <div class="container" style="max-width:600px;text-align:center;">
            <h2 style="font-family:var(--heading-font, var(--font-display));font-size:24px;color:var(--ink);margin-bottom:16px;">
                Why Pro?
            </h2>
            <p style="font-size:15px;color:var(--ink-muted);line-height:1.7;">
                IndieStack tracks what AI agents recommend, what developers search for,
                and which tools work together. Free gives you the catalog. Pro gives you the intelligence.
            </p>
        </div>
    </section>

    <script>
    async function subscribePro(plan) {{
        const btn = document.getElementById(plan === 'founder' ? 'founder-btn' : 'pro-btn');
        const err = document.getElementById('subscribe-error');
        if (!btn) return;
        btn.disabled = true;
        const orig = btn.textContent;
        btn.textContent = 'Loading...';
        if (err) err.style.display = 'none';
        try {{
            const res = await fetch('/api/subscribe/pro', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{plan}})
            }});
            const data = await res.json();
            if (data.checkout_url) {{
                window.location.href = data.checkout_url;
            }} else {{
                if (err) {{ err.textContent = data.error || 'Something went wrong'; err.style.display = 'block'; }}
                btn.disabled = false;
                btn.textContent = orig;
            }}
        }} catch (e) {{
            if (err) {{ err.textContent = 'Network error. Please try again.'; err.style.display = 'block'; }}
            btn.disabled = false;
            btn.textContent = orig;
        }}
    }}
    </script>
    '''

    return HTMLResponse(page_shell(
        title="Pricing — IndieStack Pro",
        body=body,
        user=user,
        description="IndieStack Pro unlocks demand signals, agent citation intel, priority API access, and more across the entire platform. $19/mo or $99/year as a Founding Member.",
    ))
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/pricing.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/routes/pricing.py
git commit -m "feat: build Pro Everywhere pricing page with founder seats"
```

---

## Phase 3: Agent Citation Notification Loop

### Task 5: Create the citation notification email template

**Context:** This is the highest-ROI conversion mechanism. When an AI agent cites a maker's tool, we email the maker: "Your tool was cited by Claude 3 times this week." The count is free. The context (what the agent said) is gated behind Pro. The email template goes in `email.py` alongside the 17 existing templates.

**Files:**
- Modify: `src/indiestack/email.py` (add after `ego_ping_html` function, around line 591)

**Step 1: Add the citation notification email template**

Add this function after the `ego_ping_html` function (after line 591):

```python
def citation_alert_html(*, maker_name: str, tool_name: str, tool_slug: str,
                         citation_count: int, agent_names: list[str],
                         is_pro: bool, sample_context: str = "") -> str:
    """Email alerting a maker that AI agents cited their tool this week."""
    maker_name = escape(maker_name)
    tool_name = escape(tool_name)
    base = BASE_URL

    # Agent names list
    agents_text = ", ".join(agent_names[:5]) if agent_names else "AI agents"
    if len(agent_names) > 5:
        agents_text += f" and {len(agent_names) - 5} more"

    if citation_count == 1:
        headline = f"An AI agent recommended {tool_name} this week"
    else:
        headline = f"AI agents recommended {tool_name} {citation_count} times this week"

    # Context teaser — show for Pro, gate for free
    if is_pro and sample_context:
        context_section = f"""
        <div style="margin:24px 0;padding:16px;background:#F0F7FA;border-radius:12px;border-left:3px solid #00D4F5;">
            <p style="font-size:11px;font-weight:600;color:#00D4F5;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">
                Latest Citation Context
            </p>
            <p style="font-size:14px;color:#1A2D4A;margin:0;line-height:1.5;font-style:italic;">
                &ldquo;{escape(sample_context[:200])}&rdquo;
            </p>
        </div>
        <div style="text-align:center;">
            <a href="{base}/dashboard" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
               padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
                View All Citations
            </a>
        </div>"""
    else:
        context_section = f"""
        <div style="margin:24px 0;padding:20px;background:#1A2D4A;border-radius:12px;text-align:center;">
            <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 4px;">
                What did the agents say about your tool?
            </p>
            <p style="color:rgba(255,255,255,0.6);font-size:13px;margin:0 0 16px;">
                Upgrade to Pro to see the full context of every citation.
            </p>
            <a href="{base}/pricing" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
               padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;text-decoration:none;">
                Upgrade to Pro &mdash; $19/mo
            </a>
        </div>"""

    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            AI Citation Alert
        </div>
    </div>
    <h2 style="font-family:serif;font-size:22px;color:#1A2D4A;margin-bottom:4px;text-align:center;">
        {tool_name}
    </h2>
    <p style="color:#6B6560;font-size:15px;text-align:center;margin-bottom:24px;">
        Hi {maker_name} &mdash; {headline}
    </p>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:24px 0;">
        <div style="text-align:center;padding:20px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:32px;font-weight:bold;color:#00D4F5;">{citation_count}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Citations This Week</div>
        </div>
        <div style="text-align:center;padding:20px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:14px;font-weight:600;color:#1A2D4A;margin-top:8px;">{agents_text}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Citing Agents</div>
        </div>
    </div>
    {context_section}
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because <a href="{base}/tool/{tool_slug}" style="color:#00D4F5;">{tool_name}</a>
        is listed on IndieStack.
    </p>
    """
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/email.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/email.py
git commit -m "feat: add citation alert email template with Pro/free context gating"
```

---

### Task 6: Add citation notification query helper to db.py

**Context:** We need a query that joins `agent_citations` → `tools` → `makers` → `users` to find all makers who had tools cited in the last 7 days, along with citation counts and agent names. This powers the weekly notification loop.

**Files:**
- Modify: `src/indiestack/db.py` (add after `get_citation_percentile()`, around line 1920)

**Step 1: Add the helper function**

Add after `get_citation_percentile()`:

```python
async def get_weekly_citation_digest(db, days: int = 7) -> list[dict]:
    """Get citation data for all makers with cited tools in the last N days.

    Returns a list of dicts, one per tool that was cited:
    {maker_email, maker_name, tool_name, tool_slug, citation_count,
     agent_names (comma-separated), sample_context, user_id}
    """
    cursor = await db.execute("""
        SELECT
            u.email AS maker_email,
            m.name AS maker_name,
            t.name AS tool_name,
            t.slug AS tool_slug,
            COUNT(ac.id) AS citation_count,
            GROUP_CONCAT(DISTINCT ac.agent_name) AS agent_names,
            MAX(ac.context) AS sample_context,
            u.id AS user_id
        FROM agent_citations ac
        JOIN tools t ON t.id = ac.tool_id
        JOIN makers m ON m.id = t.maker_id
        JOIN users u ON u.maker_id = m.id
        WHERE ac.created_at >= datetime('now', ?)
          AND u.email IS NOT NULL
          AND u.email != ''
        GROUP BY t.id
        ORDER BY citation_count DESC
    """, (f'-{days} days',))
    rows = await cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add get_weekly_citation_digest() for notification loop"
```

---

### Task 7: Build the weekly citation notification periodic task

**Context:** IndieStack already runs periodic tasks in `main.py` (session cleanup every hour, ego ping every Friday, auto tool-of-the-week every Monday). We'll add a citation notification that runs every Wednesday (offset from the Friday ego ping to space out maker emails). It uses the same pattern: `asyncio.create_task()` in the startup event.

**Files:**
- Modify: `src/indiestack/main.py` (add periodic task function and register it in startup)

**Step 1: Find the startup event**

Search for the existing `_weekly_ego_ping` function and the startup registration. The periodic tasks are registered in the `@app.on_event("startup")` handler. Find the pattern and add the citation task after the ego ping registration.

**Step 2: Add the citation notification periodic task**

Add this function near the other periodic tasks (after `_weekly_ego_ping`, around line 212):

```python
async def _weekly_citation_alert():
    """Send citation alert emails to makers every Wednesday."""
    import asyncio
    await asyncio.sleep(120)  # Wait for app to fully start
    while True:
        try:
            from datetime import datetime
            now = datetime.now()
            if now.weekday() == 2 and now.hour == 10:  # Wednesday 10am
                import aiosqlite
                from indiestack.db import get_weekly_citation_digest, check_pro, DB_PATH
                from indiestack.email import send_email, citation_alert_html, _email_wrapper
                async with aiosqlite.connect(DB_PATH) as db:
                    db.row_factory = aiosqlite.Row
                    digests = await get_weekly_citation_digest(db, days=7)
                    sent = 0
                    for d in digests:
                        if d['citation_count'] == 0:
                            continue
                        is_pro = await check_pro(db, d['user_id'])
                        agent_list = d['agent_names'].split(',') if d['agent_names'] else []
                        html = citation_alert_html(
                            maker_name=d['maker_name'],
                            tool_name=d['tool_name'],
                            tool_slug=d['tool_slug'],
                            citation_count=d['citation_count'],
                            agent_names=agent_list,
                            is_pro=is_pro,
                            sample_context=d['sample_context'] or "",
                        )
                        await send_email(
                            to=d['maker_email'],
                            subject=f"AI agents cited {d['tool_name']} {d['citation_count']} times this week",
                            html_body=_email_wrapper(html, unsubscribe_url=f"https://indiestack.ai/account/notifications"),
                        )
                        sent += 1
                    if sent:
                        logger.info(f"Sent {sent} citation alert emails")
        except Exception as e:
            logger.error(f"Citation alert error: {e}")
        await asyncio.sleep(3600)  # Check every hour
```

**Step 3: Register the task in startup**

Find the startup event handler and add `asyncio.create_task(_weekly_citation_alert())` alongside the other periodic task registrations.

**Step 4: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add weekly citation alert email loop (Wednesdays 10am)"
```

---

## Phase 4: Pro Feature Gates Across the Site

### Task 8: Gate agent citation context on the maker dashboard

**Context:** The dashboard (`dashboard.py:56`) already shows `agent_citations_30d` count and `citation_percentile` for makers. Currently this data is shown to everyone. We need to:
1. Keep showing the citation COUNT to all makers (it's the teaser)
2. Gate the citation CONTEXT and agent breakdown behind Pro
3. Add an upgrade CTA for non-Pro makers

**Files:**
- Modify: `src/indiestack/routes/dashboard.py` (lines 88-93 and the section where citation data is rendered)

**Step 1: Update the dashboard to use `check_pro()` and show gated citations**

The dashboard already has `is_pro` from line 82. Find where agent citation data is displayed in the dashboard HTML and modify it to:
- Show citation count always (free)
- Show "Upgrade to see what agents said" CTA for non-Pro
- Show full citation breakdown for Pro users

At line 92-93, replace the empty `pro_badge` and `upgrade_html`:

```python
    pro_badge = ' <span style="display:inline-block;background:var(--accent);color:white;font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;vertical-align:middle;margin-left:8px;">PRO</span>' if is_pro else ''
    upgrade_html = '' if is_pro else '''
        <a href="/pricing" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;
           background:var(--accent);color:white;border-radius:8px;font-size:13px;font-weight:600;
           text-decoration:none;margin-left:auto;">
            Upgrade to Pro
        </a>''' if user else ''
```

**Step 2: Add citation context section to dashboard**

Find the dashboard body HTML where funnel analytics are rendered (around line 172+). After the funnel analytics section, add a citation insights section that is gated:

```python
    # Citation insights (Pro-gated)
    citation_section = ''
    if maker_id and agent_citations_30d > 0:
        if is_pro:
            # Full breakdown for Pro users
            from indiestack.db import get_maker_agent_breakdown
            agent_breakdown = await get_maker_agent_breakdown(db, maker_id, days=30)
            breakdown_rows = ''
            for ab in agent_breakdown:
                breakdown_rows += f'''
                <tr>
                    <td style="padding:8px 12px;font-weight:600;color:var(--ink);">{ab['agent_name']}</td>
                    <td style="padding:8px 12px;text-align:center;color:var(--accent);">{ab['count']}</td>
                </tr>'''
            citation_section = f'''
            <div class="card" style="margin-top:24px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">
                    AI Citation Intel <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">(last 30 days)</span>
                </h3>
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:2px solid var(--border);">
                            <th style="padding:8px 12px;text-align:left;font-size:12px;color:var(--ink-muted);text-transform:uppercase;">Agent</th>
                            <th style="padding:8px 12px;text-align:center;font-size:12px;color:var(--ink-muted);text-transform:uppercase;">Citations</th>
                        </tr>
                    </thead>
                    <tbody>{breakdown_rows}</tbody>
                </table>
            </div>'''
        else:
            # Teaser for free users
            citation_section = f'''
            <div class="card" style="margin-top:24px;position:relative;overflow:hidden;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                    AI Citation Intel
                </h3>
                <p style="font-size:14px;color:var(--ink-muted);margin-bottom:16px;">
                    Your tools were cited <strong style="color:var(--accent);">{agent_citations_30d} times</strong> by AI agents in the last 30 days.
                </p>
                <div style="padding:20px;background:var(--navy, #1A2D4A);border-radius:12px;text-align:center;">
                    <p style="color:var(--accent);font-size:14px;font-weight:700;margin:0 0 4px;">
                        Which agents? What did they say?
                    </p>
                    <p style="color:rgba(255,255,255,0.6);font-size:13px;margin:0 0 16px;">
                        Upgrade to Pro to see the full breakdown.
                    </p>
                    <a href="/pricing" style="display:inline-block;background:var(--accent);color:var(--navy, #1A2D4A);
                       padding:10px 24px;border-radius:8px;font-weight:700;font-size:14px;text-decoration:none;">
                        Upgrade to Pro
                    </a>
                </div>
            </div>'''
```

Then insert `{citation_section}` into the dashboard HTML body after the funnel analytics section.

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/dashboard.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: gate citation context behind Pro, add upgrade CTA to dashboard"
```

---

### Task 9: Update Demand Signals Pro page for new pricing

**Context:** The `/demand` page (gaps.py:542) currently shows "$15/month" for "Demand Signals Pro" and calls `/api/subscribe/demand-pro`. We need to update it to point to the new Pro plan ($19/mo) since demand signals are now part of the Pro Everywhere bundle. The Pro dashboard functionality stays the same — we're just updating the marketing and checkout flow.

**Files:**
- Modify: `src/indiestack/routes/gaps.py` (lines 559-650, the CTA page shown to non-Pro users)

**Step 1: Update the CTA page**

In `gaps.py`, find the CTA page content (lines 561-651). Update:
1. Change "$15" to "$19" (line 606)
2. Change the heading from "Demand Signals Pro" to "Part of IndieStack Pro"
3. Change the subscribe button to link to `/pricing` instead of calling `subscribeDemandPro()`
4. Update the copy to position this as part of Pro Everywhere

Replace the pricing card section (lines 599-622) with:

```python
    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:480px;text-align:center;">
            <div style="background:var(--bg-card);border:2px solid var(--accent);border-radius:16px;padding:40px 32px;">
                <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                    Part of IndieStack Pro
                </p>
                <div style="font-family:var(--heading-font, var(--font-display));font-size:48px;font-weight:700;color:var(--ink);margin-bottom:4px;">
                    $19<span style="font-size:18px;color:var(--ink-muted);font-weight:400;">/month</span>
                </div>
                <p style="font-size:14px;color:var(--ink-muted);margin-bottom:24px;">
                    Demand signals + agent citations + priority API access. One subscription, everything unlocked.
                </p>
                <a href="/pricing"
                    style="display:inline-block;padding:14px 40px;background:var(--accent);color:white;
                           border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;
                           text-decoration:none;width:100%;box-sizing:border-box;text-align:center;">
                    View Pricing
                </a>
            </div>
            <p style="font-size:13px;color:var(--ink-muted);margin-top:16px;">
                Want the basics? Check out the free <a href="/gaps" style="color:var(--accent);text-decoration:underline;">Demand Bounty Board</a>.
            </p>
        </div>
    </section>
```

Remove the old `subscribeDemandPro()` JavaScript (lines 625-650) since we're linking to `/pricing` now.

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/gaps.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/routes/gaps.py
git commit -m "feat: update demand signals CTA to point to Pro Everywhere pricing"
```

---

### Task 10: Add Pro badge to subscribed users' profiles and tool cards

**Context:** Pro users should have a visible badge on their maker cards and tool cards, signaling trust and status. This is a subtle but important conversion trigger for other makers who see it.

**Files:**
- Modify: `src/indiestack/routes/components.py` (tool_card function ~line 1061, maker_card function ~line 1176)

**Step 1: Add Pro badge rendering helper**

Add near the other badge helpers (around line 1011, after `verified_badge_html`):

```python
def pro_badge_html() -> str:
    """Small Pro badge for tool cards and maker cards."""
    return '<span style="display:inline-block;background:var(--accent);color:white;font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;text-transform:uppercase;letter-spacing:0.5px;">Pro</span>'
```

**Step 2: Add Pro badge to tool_card()**

In the `tool_card()` function, find the badges section (around lines 1105-1114). Add the Pro badge if the tool's maker has a Pro subscription. This requires passing an `is_pro` flag into the tool card data.

Since `tool_card()` renders from a tool dict, add a check: if `tool.get('maker_is_pro')`, show the Pro badge. The query that feeds tool cards will need to be updated to include this flag — but that's a JOIN change. For now, add the rendering logic:

After the existing badges (line 1114), add:

```python
                    {"" if not tool.get('maker_is_pro') else pro_badge_html()}
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add src/indiestack/routes/components.py
git commit -m "feat: add Pro badge rendering to tool cards and maker cards"
```

---

## Phase 5: API Key-Based Rate Limiting

### Task 11: Add key-based rate limiting for API endpoints

**Context:** Currently all rate limiting is IP-based (`main.py:41-100`). For the Pro tier to offer higher API limits (1000/day vs 50/day), we need to rate-limit by API key when one is present. The existing middleware already resolves API keys (main.py:586-604) and stores them in `request.state.api_key`.

**Files:**
- Modify: `src/indiestack/main.py` (rate limiting section, lines 37-100, and middleware lines 574-618)

**Step 1: Add daily API key rate tracking**

Add a new dict and function after the existing rate limit code (after line 100):

```python
# ── API Key Daily Rate Limiting ──────────────────────────────────────────
_api_key_daily: dict[str, dict] = {}  # {key_id: {"date": "YYYY-MM-DD", "count": N}}

API_DAILY_LIMITS = {
    "free": 50,
    "pro": 1000,
}


def _check_api_key_rate_limit(key_id: int, tier: str) -> bool:
    """Returns True if API key has exceeded its daily limit."""
    from datetime import date
    today = date.today().isoformat()
    entry = _api_key_daily.get(key_id)
    if not entry or entry["date"] != today:
        _api_key_daily[key_id] = {"date": today, "count": 1}
        return False
    limit = API_DAILY_LIMITS.get(tier, 50)
    if entry["count"] >= limit:
        return True
    entry["count"] += 1
    return False
```

**Step 2: Integrate into the middleware**

In the `db_middleware` function (around line 574-618), after the API key is resolved (around line 604), add the daily rate check for `/api/*` requests:

```python
        # API key daily rate limiting
        if request.state.api_key and path.startswith("/api/"):
            key_data = request.state.api_key
            if _check_api_key_rate_limit(key_data['id'], key_data.get('tier', 'free')):
                return JSONResponse(
                    {"error": "Daily API limit exceeded. Upgrade to Pro for higher limits.", "upgrade_url": "https://indiestack.ai/pricing"},
                    status_code=429
                )
```

**Step 3: Update API key lookup to include tier**

Check that `get_api_key_by_key()` in db.py returns the `tier` column. It should already since it does `SELECT *`, but verify. If it returns a dict, the tier should be accessible as `key['tier']`.

**Step 4: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add API key daily rate limiting (50 free, 1000 pro)"
```

---

### Task 12: Auto-upgrade API key tier when user subscribes to Pro

**Context:** When a user subscribes to Pro via Stripe webhook, their API keys should automatically be upgraded from 'free' to 'pro' tier. This happens in the webhook handler.

**Files:**
- Modify: `src/indiestack/main.py` (webhook handler, around lines 2796-2806)

**Step 1: Add tier upgrade to webhook handler**

After the subscription INSERT succeeds in the webhook handler, add:

```python
                # Upgrade API keys to pro tier
                await d.execute(
                    "UPDATE api_keys SET tier = 'pro' WHERE user_id = ? AND is_active = 1",
                    (int(user_id),)
                )
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: auto-upgrade API keys to pro tier on subscription"
```

---

## Phase 6: Dashboard Pro Welcome + Smoke Test

### Task 13: Add Pro welcome banner to dashboard

**Context:** When a user subscribes and returns to `/dashboard?subscribed=true`, they should see a welcome banner confirming their Pro status and showing what's unlocked.

**Files:**
- Modify: `src/indiestack/routes/dashboard.py` (near the top of the dashboard body HTML)

**Step 1: Add welcome banner**

After the `is_pro` check (line 82), check for the `subscribed` query param:

```python
    just_subscribed = request.query_params.get('subscribed') == 'true' and is_pro
```

Then add a banner at the top of the dashboard body HTML:

```python
    welcome_banner = ''
    if just_subscribed:
        welcome_banner = '''
        <div style="background:var(--accent);color:white;padding:16px 24px;border-radius:12px;margin-bottom:24px;text-align:center;">
            <p style="font-size:16px;font-weight:700;margin:0 0 4px;">Welcome to IndieStack Pro!</p>
            <p style="font-size:14px;opacity:0.9;margin:0;">All Pro features are now unlocked across the platform.</p>
        </div>'''
```

Insert `{welcome_banner}` at the top of the dashboard body.

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/dashboard.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: add Pro welcome banner on successful subscription"
```

---

### Task 14: Run smoke tests and deploy

**Step 1: Verify all modified files parse correctly**

```bash
cd /home/patty/indiestack && python3 -c "
import ast, glob
files = ['src/indiestack/db.py', 'src/indiestack/main.py', 'src/indiestack/email.py',
         'src/indiestack/routes/pricing.py', 'src/indiestack/routes/gaps.py',
         'src/indiestack/routes/dashboard.py', 'src/indiestack/routes/components.py']
for f in files:
    try:
        ast.parse(open(f).read())
        print(f'OK: {f}')
    except SyntaxError as e:
        print(f'FAIL: {f} — {e}')
"
```

**Step 2: Run smoke tests**

```bash
cd /home/patty/indiestack && python3 smoke_test.py
```

Expected: All tests pass. The `/pricing` endpoint should now return 200 instead of 303.

**Step 3: Update smoke test expectation for /pricing**

In `smoke_test.py`, find the test for `/pricing` — it likely expects a 303 redirect. Update it to expect 200.

**Step 4: Deploy**

```bash
cd /home/patty/indiestack && fly deploy
```

---

## Execution Order (Optimised for Parallel Agents)

Tasks 1-3 must run first (foundation). After that:

- **Agent A**: Tasks 4 (pricing page) + Task 9 (demand signals CTA update)
- **Agent B**: Tasks 5 + 6 + 7 (citation email template + query + periodic task)
- **Agent C**: Tasks 8 + 13 (dashboard gates + welcome banner)
- **Agent D**: Tasks 10 + 11 + 12 (Pro badge + rate limiting + auto-upgrade)
- **Final**: Task 14 (smoke test + deploy)

---

## Manual Steps for Patrick (Stripe Dashboard)

Before deploying, Patrick needs to create two Stripe Prices:

1. **Pro Monthly**: $19/month recurring → copy Price ID → set as `STRIPE_PRO_PRICE_ID` on Fly
2. **Founder Annual**: $99/year recurring → copy Price ID → set as `STRIPE_FOUNDER_PRICE_ID` on Fly

```bash
fly secrets set STRIPE_PRO_PRICE_ID=price_xxxxx STRIPE_FOUNDER_PRICE_ID=price_yyyyy
```

---

## What This Does NOT Include (Deferred)

- **Verified Compatible certification** — requires CI pipeline, defer to Month 4+
- **Custom profile domains** — listed as Pro feature but implementation deferred
- **Consumer agent play** — trigger: 10K weekly MCP queries from consumer LLM IPs
- **Usage-based billing** — defer until >1M API queries/month
- **Data Co-op** — interesting idea but adds complexity, revisit after Pro has paying users
- **HTTP 402 agent payments** — science fiction, defer indefinitely
