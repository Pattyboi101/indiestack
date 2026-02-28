"""Paid verification — self-service badge checkout."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell, verified_badge_html
from indiestack.db import get_tool_by_slug, verify_tool, get_tool_by_id
from indiestack.payments import create_verification_checkout, VERIFICATION_PRICE_PENCE, retrieve_checkout_session

router = APIRouter()


# NOTE: /verify/success MUST come before /verify/{slug} so FastAPI doesn't
# match "success" as a slug parameter.

@router.get("/verify/success", response_class=HTMLResponse)
async def verify_success(request: Request, session_id: str = ""):
    if not session_id:
        return RedirectResponse(url="/", status_code=303)

    db = request.state.db
    try:
        session = retrieve_checkout_session(session_id)
        if session.payment_status != "paid":
            raise ValueError("Payment not completed")

        tool_id = int(session.metadata.get("tool_id", 0))
        if not tool_id:
            raise ValueError("Missing tool_id")

        await verify_tool(db, tool_id)
        tool = await get_tool_by_id(db, tool_id)
        tool_slug = tool['slug'] if tool else ''
        tool_name = escape(tool['name']) if tool else 'Your tool'

        body = f"""
        <div class="container" style="max-width:600px;padding:64px 24px;text-align:center;">
            <div style="display:inline-flex;align-items:center;justify-content:center;width:72px;height:72px;
                        border-radius:50%;background:#ECFDF5;margin-bottom:16px;">
                <span style="font-size:36px;">&#9989;</span>
            </div>
            <h1 style="font-family:var(--font-display);font-size:32px;margin-bottom:12px;">
                You're Verified!
            </h1>
            <p style="color:var(--ink-muted);font-size:16px;margin-bottom:8px;">
                <strong>{tool_name}</strong> now has the {verified_badge_html()} badge.
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:32px;">
                Your listing is now boosted in search and category rankings.
            </p>
            <a href="/tool/{escape(tool_slug)}" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
                View Your Listing &rarr;
            </a>
        </div>
        """
        return HTMLResponse(page_shell("Verified!", body, user=request.state.user))

    except Exception:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Verification Error</h1>
            <p class="text-muted mt-4">We couldn't confirm your payment. Please contact support.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Error", body, user=request.state.user), status_code=500)


@router.get("/verify/{slug}", response_class=HTMLResponse)
async def verify_page(request: Request, slug: str):
    db = request.state.db
    tool = await get_tool_by_slug(db, slug)

    if not tool or tool['status'] != 'approved':
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Tool Not Found</h1>
            <p class="text-muted mt-4">This tool doesn't exist or hasn't been approved yet.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    name = escape(str(tool['name']))
    tool_slug = escape(str(tool['slug']))
    is_verified = bool(tool.get('is_verified', 0))

    if is_verified:
        body = f"""
        <div class="container" style="max-width:600px;padding:64px 24px;text-align:center;">
            <div style="font-size:48px;margin-bottom:16px;">&#9989;</div>
            <h1 style="font-family:var(--font-display);font-size:32px;margin-bottom:12px;">Already Verified</h1>
            <p style="color:var(--ink-muted);font-size:16px;">
                <strong>{name}</strong> already has the {verified_badge_html()} badge.
            </p>
            <a href="/tool/{tool_slug}" class="btn btn-primary mt-8">View Listing &rarr;</a>
        </div>
        """
        return HTMLResponse(page_shell(f"{tool['name']} — Verified", body, user=request.state.user))

    price_display = f"\u00a3{VERIFICATION_PRICE_PENCE / 100:.0f}"

    body = f"""
    <div class="container" style="max-width:640px;padding:64px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <div style="display:inline-flex;align-items:center;justify-content:center;width:72px;height:72px;
                        border-radius:50%;background:linear-gradient(135deg, var(--gold-light), var(--gold));
                        margin-bottom:16px;">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#92400E" stroke-width="2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
            </div>
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">
                Get Verified
            </h1>
            <p style="color:var(--ink-muted);font-size:16px;margin-top:8px;">
                Boost <strong>{name}</strong> with a verified badge
            </p>
        </div>

        <div class="card" style="border-color:var(--gold-light);background:linear-gradient(180deg, #FDF8EE 0%, white 30%);">
            <h3 style="font-family:var(--font-display);font-size:20px;margin-bottom:20px;color:var(--ink);">
                What you get
            </h3>
            <div style="display:flex;flex-direction:column;gap:16px;">
                <div style="display:flex;gap:12px;align-items:flex-start;">
                    <span style="font-size:20px;">&#127942;</span>
                    <div>
                        <strong style="color:var(--ink);">Gold Verified Badge</strong>
                        <p style="color:var(--ink-muted);font-size:14px;margin-top:2px;">
                            The {verified_badge_html()} badge appears on your listing and in search results.
                        </p>
                    </div>
                </div>
                <div style="display:flex;gap:12px;align-items:flex-start;">
                    <span style="font-size:20px;">&#128200;</span>
                    <div>
                        <strong style="color:var(--ink);">Boosted Ranking</strong>
                        <p style="color:var(--ink-muted);font-size:14px;margin-top:2px;">
                            Verified tools rank higher in search, trending, and category pages.
                        </p>
                    </div>
                </div>
                <div style="display:flex;gap:12px;align-items:flex-start;">
                    <span style="font-size:20px;">&#128176;</span>
                    <div>
                        <strong style="color:var(--ink);">Trust Signal</strong>
                        <p style="color:var(--ink-muted);font-size:14px;margin-top:2px;">
                            Buyers trust verified tools more. Stand out from the crowd.
                        </p>
                    </div>
                </div>
            </div>

            <div style="margin-top:28px;padding-top:24px;border-top:1px solid var(--border);text-align:center;">
                <div style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:4px;">
                    {price_display}
                </div>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">One-time payment</p>
                <form method="post" action="/verify/{tool_slug}">
                    <button type="submit" class="btn" style="background:linear-gradient(135deg, var(--gold), #D4A24A);
                            color:#5C3D0E;font-weight:700;padding:14px 40px;font-size:16px;border-radius:999px;
                            width:100%;justify-content:center;border:1px solid var(--gold);">
                        Get Verified &rarr;
                    </button>
                </form>
            </div>
        </div>

        <p style="text-align:center;color:var(--ink-muted);font-size:13px;margin-top:16px;">
            Secure payment via Stripe. Badge appears instantly after payment.
        </p>
    </div>
    """
    return HTMLResponse(page_shell(f"Get Verified \u2014 {tool['name']}", body,
                                    description=f"Get a verified badge for {tool['name']} on IndieStack.", user=request.state.user))


@router.post("/verify/{slug}")
async def verify_checkout(request: Request, slug: str):
    db = request.state.db
    tool = await get_tool_by_slug(db, slug)

    if not tool or tool['status'] != 'approved':
        return RedirectResponse(url="/", status_code=303)

    if tool.get('is_verified'):
        return RedirectResponse(url=f"/tool/{slug}", status_code=303)

    base_url = str(request.base_url).rstrip('/').replace("http://", "https://")
    try:
        session = create_verification_checkout(
            tool_name=tool['name'],
            tool_id=tool['id'],
            success_url=f"{base_url}/verify/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/verify/{slug}",
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        body = f"""
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Payment Error</h1>
            <p class="text-muted mt-4">Something went wrong setting up payment. Please try again.</p>
            <a href="/verify/{escape(slug)}" class="btn btn-primary mt-4">Try Again</a>
        </div>
        """
        return HTMLResponse(page_shell("Payment Error", body, user=request.state.user), status_code=500)
