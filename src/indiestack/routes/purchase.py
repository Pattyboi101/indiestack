"""Purchase flow: checkout, success, cancel, webhook."""

from html import escape

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from indiestack.routes.components import page_shell
from indiestack.db import get_tool_by_slug, create_purchase, get_purchase_by_token, get_purchase_by_session
from indiestack.payments import (
    create_checkout_session, verify_webhook, retrieve_checkout_session,
    calculate_commission, STRIPE_SECRET_KEY,
)

router = APIRouter()


def format_price(pence: int) -> str:
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


@router.post("/api/checkout")
async def api_checkout(request: Request, tool_id: int = Form(0)):
    if not STRIPE_SECRET_KEY:
        return JSONResponse({"error": "Payments not configured"}, status_code=503)

    db = request.state.db
    cursor = await db.execute(
        "SELECT t.*, c.name as category_name, c.slug as category_slug "
        "FROM tools t JOIN categories c ON t.category_id = c.id WHERE t.id = ? AND t.status = 'approved'",
        (tool_id,),
    )
    tool = await cursor.fetchone()

    if not tool or not tool.get('price_pence') or tool['price_pence'] <= 0:
        return RedirectResponse(url="/", status_code=303)

    if not tool.get('stripe_account_id'):
        return RedirectResponse(url=f"/tool/{tool['slug']}", status_code=303)

    base_url = str(request.base_url).rstrip("/")
    try:
        session = create_checkout_session(
            tool_name=tool['name'],
            tool_id=tool['id'],
            price_pence=tool['price_pence'],
            stripe_account_id=tool['stripe_account_id'],
            success_url=f"{base_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/tool/{tool['slug']}",
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        body = f"""
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Payment Error</h1>
            <p class="text-muted mt-4">Something went wrong creating the checkout session.</p>
            <p class="text-sm mt-2" style="color:var(--stone-400);">{escape(str(e))}</p>
            <a href="/tool/{escape(str(tool['slug']))}" class="btn btn-primary mt-4">Back to Tool</a>
        </div>
        """
        return HTMLResponse(page_shell("Payment Error", body), status_code=500)


@router.get("/purchase/success", response_class=HTMLResponse)
async def purchase_success(request: Request, session_id: str = ""):
    db = request.state.db

    if not session_id:
        return RedirectResponse(url="/", status_code=303)

    # Check if we already recorded this purchase
    existing = await get_purchase_by_session(db, session_id)
    if existing:
        return RedirectResponse(url=f"/purchase/{existing['purchase_token']}", status_code=303)

    # Retrieve session from Stripe
    try:
        session = retrieve_checkout_session(session_id)
    except Exception:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Session Not Found</h1>
            <p class="text-muted mt-4">We couldn't verify your payment. Please contact support.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Session Not Found", body), status_code=404)

    if session.payment_status != "paid":
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Payment Incomplete</h1>
            <p class="text-muted mt-4">Your payment hasn't been confirmed yet. Please try again.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Payment Incomplete", body))

    tool_id = int(session.metadata.get("tool_id", 0))
    buyer_email = ""
    if session.customer_details:
        buyer_email = session.customer_details.email or ""
    amount = session.amount_total or 0
    commission = calculate_commission(amount)

    token = await create_purchase(
        db,
        tool_id=tool_id,
        buyer_email=buyer_email,
        stripe_session_id=session_id,
        amount_pence=amount,
        commission_pence=commission,
    )

    return RedirectResponse(url=f"/purchase/{token}", status_code=303)


@router.get("/purchase/{token}", response_class=HTMLResponse)
async def purchase_delivery(request: Request, token: str):
    db = request.state.db
    purchase = await get_purchase_by_token(db, token)

    if not purchase:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Purchase Not Found</h1>
            <p class="text-muted mt-4">This purchase link is invalid or has expired.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body), status_code=404)

    tool_name = escape(str(purchase['tool_name']))
    tool_slug = escape(str(purchase['tool_slug']))
    delivery_type = purchase.get('delivery_type', 'link')
    delivery_url = str(purchase.get('delivery_url', ''))
    amount_display = format_price(purchase['amount_pence'])

    # Delivery section depends on type
    if delivery_type == 'download':
        delivery_html = f"""
        <a href="{escape(delivery_url)}" class="btn btn-violet" style="font-size:16px;padding:14px 32px;" target="_blank" rel="noopener">
            Download Now &darr;
        </a>
        """
    elif delivery_type == 'license_key':
        delivery_html = f"""
        <div style="background:var(--stone-100);border:1px solid var(--stone-200);border-radius:var(--radius);padding:20px;margin-top:12px;">
            <p class="text-sm text-muted" style="margin-bottom:8px;">Your license / access link:</p>
            <a href="{escape(delivery_url)}" target="_blank" rel="noopener"
               style="font-family:var(--font-mono);font-size:14px;word-break:break-all;">{escape(delivery_url)}</a>
        </div>
        """
    else:
        delivery_html = f"""
        <a href="{escape(delivery_url)}" class="btn btn-violet" style="font-size:16px;padding:14px 32px;" target="_blank" rel="noopener">
            Access {tool_name} &rarr;
        </a>
        """

    body = f"""
    <div class="container" style="max-width:640px;padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <div style="width:64px;height:64px;background:#ECFDF5;border-radius:50%;display:inline-flex;
                        align-items:center;justify-content:center;margin-bottom:16px;">
                <span style="font-size:28px;">&#10003;</span>
            </div>
            <h1 style="font-family:var(--font-display);font-size:32px;">Purchase Complete!</h1>
            <p class="text-muted mt-2">Thank you for purchasing <strong>{tool_name}</strong> for {amount_display}.</p>
        </div>

        <div class="card" style="text-align:center;padding:32px;">
            <h2 style="font-family:var(--font-display);font-size:22px;margin-bottom:20px;">
                Your Purchase
            </h2>
            {delivery_html}
            <p class="text-muted text-sm mt-4">
                Bookmark this page &mdash; it's your receipt and access link.
            </p>
        </div>

        <div style="text-align:center;margin-top:32px;">
            <a href="/tool/{tool_slug}" class="btn btn-secondary">Back to {tool_name}</a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell(f"Purchase: {tool_name}", body))


@router.get("/purchase/cancel", response_class=HTMLResponse)
async def purchase_cancel(request: Request):
    body = """
    <div class="container" style="text-align:center;padding:80px 0;">
        <h1 style="font-family:var(--font-display);font-size:32px;">Payment Cancelled</h1>
        <p class="text-muted mt-4">Your payment was cancelled. No charge was made.</p>
        <a href="/" class="btn btn-primary mt-4">Back to Home</a>
    </div>
    """
    return HTMLResponse(page_shell("Payment Cancelled", body))


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Belt-and-suspenders: handle checkout.session.completed webhook."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook(payload, sig)
    except Exception:
        return JSONResponse({"error": "Invalid signature"}, status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id", "")
        tool_id = int(session.get("metadata", {}).get("tool_id", 0))
        buyer_email = session.get("customer_details", {}).get("email", "") if session.get("customer_details") else ""
        amount = session.get("amount_total", 0)
        commission = calculate_commission(amount)

        db = request.state.db
        existing = await get_purchase_by_session(db, session_id)
        if not existing and tool_id:
            await create_purchase(
                db,
                tool_id=tool_id,
                buyer_email=buyer_email,
                stripe_session_id=session_id,
                amount_pence=amount,
                commission_pence=commission,
            )

    return JSONResponse({"received": True})
