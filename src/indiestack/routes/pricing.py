"""Pro maker subscription — pricing page and checkout."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from indiestack.routes.components import page_shell
from indiestack.db import get_active_subscription, create_subscription
from indiestack.payments import STRIPE_SECRET_KEY

router = APIRouter()

PRO_PRICE_PENCE = 900  # GBP 9/month


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    user = request.state.user
    db = request.state.db

    is_pro = False
    if user:
        sub = await get_active_subscription(db, user['id'])
        is_pro = sub is not None

    already_pro = ''
    if is_pro:
        already_pro = '<div class="alert alert-success" style="text-align:center;">You\'re already on the Pro plan!</div>'

    body = f"""
    <div class="container" style="padding:64px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:48px;">
            <h1 style="font-family:var(--font-display);font-size:40px;color:var(--ink);">Simple Pricing</h1>
            <p style="color:var(--ink-muted);font-size:18px;margin-top:8px;">
                Free to list. Go Pro to grow your business.
            </p>
        </div>

        {already_pro}

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">
            <!-- Free Tier -->
            <div class="card" style="padding:32px;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:4px;">Free</h2>
                <div style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:24px;">
                    &pound;0<span style="font-size:16px;color:var(--ink-muted);font-family:var(--font-body);">/month</span>
                </div>
                <ul style="list-style:none;display:flex;flex-direction:column;gap:12px;margin-bottom:32px;">
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink-light);">
                        <span style="color:#16a34a;font-weight:bold;">&#10003;</span> List unlimited tools
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink-light);">
                        <span style="color:#16a34a;font-weight:bold;">&#10003;</span> Claim &amp; manage your listing
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink-light);">
                        <span style="color:#16a34a;font-weight:bold;">&#10003;</span> Public maker profile
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink-light);">
                        <span style="color:#16a34a;font-weight:bold;">&#10003;</span> Receive reviews
                    </li>
                </ul>
                <a href="/signup" class="btn btn-secondary" style="width:100%;justify-content:center;padding:12px;">
                    Get Started Free
                </a>
            </div>

            <!-- Pro Tier -->
            <div class="card" style="padding:32px;border-color:var(--gold);background:linear-gradient(180deg,var(--warning-bg) 0%,white 30%);position:relative;">
                <span style="position:absolute;top:-12px;right:16px;font-size:11px;font-weight:700;color:var(--gold-dark);
                             background:linear-gradient(135deg,var(--gold-light),var(--gold));padding:4px 16px;
                             border-radius:999px;">COMING SOON</span>
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:4px;">Pro</h2>
                <div style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:24px;">
                    &pound;9<span style="font-size:16px;color:var(--ink-muted);font-family:var(--font-body);">/month</span>
                </div>
                <ul style="list-style:none;display:flex;flex-direction:column;gap:12px;margin-bottom:32px;">
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink-light);">
                        <span style="color:#16a34a;font-weight:bold;">&#10003;</span> Everything in Free
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink);">
                        <span style="color:var(--gold);font-weight:bold;">&#9733;</span> <strong>Featured placement boost</strong>
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink);">
                        <span style="color:var(--gold);font-weight:bold;">&#9733;</span> <strong>Priority listing placement</strong>
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink);">
                        <span style="color:var(--gold);font-weight:bold;">&#9733;</span> <strong>Tool view analytics</strong>
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink);">
                        <span style="color:var(--gold);font-weight:bold;">&#9733;</span> <strong>Verified badge included</strong>
                    </li>
                    <li style="display:flex;align-items:flex-start;gap:8px;font-size:14px;color:var(--ink);">
                        <span style="color:var(--gold);font-weight:bold;">&#9733;</span> <strong>Priority search ranking</strong>
                    </li>
                </ul>
                {'<span class="btn btn-secondary" style="width:100%;justify-content:center;padding:12px;opacity:0.7;cursor:default;">Current Plan</span>' if is_pro else '<a href="/signup" class="btn" style="width:100%;justify-content:center;padding:12px;background:linear-gradient(135deg,var(--gold),var(--gold-light));color:var(--gold-dark);font-weight:700;border:1px solid var(--gold);">Join the Waitlist</a>'}
            </div>
        </div>

        <p style="text-align:center;color:var(--ink-muted);font-size:13px;margin-top:24px;">
            Pro launching soon. Sign up free to be first in line when it goes live.
        </p>
    </div>
    """
    return HTMLResponse(page_shell("Pricing", body, user=user,
                                    description="IndieStack pricing — free to list, go Pro for analytics, lower fees, and verified badges."))


@router.get("/api/subscribe")
async def api_subscribe(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not STRIPE_SECRET_KEY:
        return JSONResponse({"error": "Payments not configured"}, status_code=503)

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    base_url = str(request.base_url).rstrip("/").replace("http://", "https://")
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {"name": "IndieStack Pro"},
                    "unit_amount": PRO_PRICE_PENCE,
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }],
            success_url=f"{base_url}/api/subscribe/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/pricing",
            customer_email=user['email'],
            metadata={"user_id": str(user['id'])},
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        body = f"""
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Subscription Error</h1>
            <p class="text-muted mt-4">{escape(str(e))}</p>
            <a href="/pricing" class="btn btn-primary mt-4">Try Again</a>
        </div>
        """
        return HTMLResponse(page_shell("Error", body, user=user), status_code=500)


@router.get("/api/subscribe/success", response_class=HTMLResponse)
async def subscribe_success(request: Request, session_id: str = ""):
    user = request.state.user
    if not user or not session_id:
        return RedirectResponse(url="/pricing", status_code=303)

    db = request.state.db

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid" or session.status == "complete":
            sub_id = session.subscription or session_id
            await create_subscription(db, user_id=user['id'],
                                       stripe_subscription_id=str(sub_id))
            return RedirectResponse(url="/dashboard", status_code=303)
    except Exception:
        pass

    # If we get here, something went wrong — show error instead of silently dropping
    body = """
    <div class="container" style="text-align:center;padding:80px 0;">
        <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Subscription Pending</h1>
        <p class="text-muted mt-4">
            We couldn't confirm your subscription right away. If you were charged,
            your Pro access will activate shortly. Please check back in a few minutes
            or contact us if the issue persists.
        </p>
        <a href="/dashboard" class="btn btn-primary mt-4">Go to Dashboard</a>
    </div>
    """
    return HTMLResponse(page_shell("Subscription Pending", body, user=user), status_code=200)
