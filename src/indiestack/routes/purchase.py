"""Purchase flow: checkout, success, cancel, webhook."""

from html import escape

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from indiestack.routes.components import page_shell, integration_snippet_html
from indiestack.db import get_tool_by_slug, create_purchase, get_purchase_by_token, get_purchase_by_session, get_tool_by_id, get_active_subscription
from indiestack.email import send_email, purchase_receipt_html, maker_sale_notification_html
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
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
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
        return RedirectResponse(url="/?toast=This+tool+isn%27t+available+for+purchase", status_code=303)

    if not tool.get('stripe_account_id'):
        return RedirectResponse(url=f"/tool/{tool['slug']}?toast=This+tool+isn%27t+set+up+for+payments+yet", status_code=303)

    # Indie Ring: 50% off for makers buying OTHER makers' tools
    discount_pence = 0
    effective_price = tool['price_pence']
    user = request.state.user
    if user:
        buyer_maker_id = user.get('maker_id')
        tool_maker_id = tool.get('maker_id')
        if buyer_maker_id and tool_maker_id and buyer_maker_id != tool_maker_id:
            discount_pence = tool['price_pence'] // 2
            effective_price = tool['price_pence'] - discount_pence

    # Check if maker has Pro subscription for reduced commission
    is_pro = False
    maker_id = tool.get('maker_id')
    if maker_id:
        maker_user_cur = await db.execute("SELECT id FROM users WHERE maker_id = ?", (maker_id,))
        maker_user_row = await maker_user_cur.fetchone()
        if maker_user_row:
            sub = await get_active_subscription(db, maker_user_row['id'])
            is_pro = sub is not None

    base_url = str(request.base_url).rstrip("/").replace("http://", "https://")
    try:
        session = create_checkout_session(
            tool_name=tool['name'],
            tool_id=tool['id'],
            price_pence=effective_price,
            stripe_account_id=tool['stripe_account_id'],
            success_url=f"{base_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/tool/{tool['slug']}",
            is_pro=is_pro,
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception:
        body = f"""
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Payment Error</h1>
            <p style="color:var(--ink-muted);margin-top:16px;">Something went wrong creating the checkout session. Please try again or contact support.</p>
            <a href="/tool/{escape(str(tool['slug']))}" class="btn btn-primary mt-4">Back to Tool</a>
        </div>
        """
        return HTMLResponse(page_shell("Payment Error", body, user=request.state.user), status_code=500)


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
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Session Not Found</h1>
            <p style="color:var(--ink-muted);margin-top:16px;">We couldn't verify your payment. Please contact support.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Session Not Found", body, user=request.state.user), status_code=404)

    if session.payment_status != "paid":
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Payment Incomplete</h1>
            <p style="color:var(--ink-muted);margin-top:16px;">Your payment hasn't been confirmed yet. Please try again.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Payment Incomplete", body, user=request.state.user))

    tool_id = int(session.metadata.get("tool_id", 0))
    buyer_email = ""
    if session.customer_details:
        buyer_email = session.customer_details.email or ""
    amount = session.amount_total or 0

    # Check maker's Pro status for correct commission
    is_pro = False
    tool_for_commission = await get_tool_by_id(db, tool_id) if tool_id else None
    if tool_for_commission and tool_for_commission.get('maker_id'):
        maker_user_cur = await db.execute("SELECT id FROM users WHERE maker_id = ?", (tool_for_commission['maker_id'],))
        maker_user_row = await maker_user_cur.fetchone()
        if maker_user_row:
            sub = await get_active_subscription(db, maker_user_row['id'])
            is_pro = sub is not None
    commission = calculate_commission(amount, is_pro=is_pro)

    # Calculate discount for record-keeping
    tool_cur = await db.execute("SELECT price_pence FROM tools WHERE id = ?", (tool_id,))
    tool_row = await tool_cur.fetchone()
    discount_pence = 0
    if tool_row and tool_row['price_pence']:
        discount_pence = max(0, tool_row['price_pence'] - amount)

    token = await create_purchase(
        db,
        tool_id=tool_id,
        buyer_email=buyer_email,
        stripe_session_id=session_id,
        amount_pence=amount,
        commission_pence=commission,
        discount_pence=discount_pence,
    )

    # Fetch tool for emails
    tool_obj = await get_tool_by_id(db, tool_id) if tool_id else None

    # Send receipt email
    if buyer_email:
        tool_name_str = tool_obj['name'] if tool_obj else 'Your purchase'
        delivery = tool_obj.get('delivery_url', '') if tool_obj else ''
        receipt_html = purchase_receipt_html(
            tool_name=tool_name_str,
            amount=f"£{amount/100:.2f}",
            delivery_url=f"{str(request.base_url).rstrip('/')}/purchase/{token}",
        )
        await send_email(buyer_email, f"Your IndieStack purchase: {tool_name_str}", receipt_html)

    # Notify the maker of the sale
    if tool_obj and tool_obj.get('maker_id'):
        maker_email_cur = await db.execute(
            "SELECT u.email FROM users u WHERE u.maker_id = ?",
            (tool_obj['maker_id'],)
        )
        maker_user = await maker_email_cur.fetchone()
        if maker_user and maker_user.get('email'):
            net_pence = amount - commission
            maker_html = maker_sale_notification_html(
                tool_name=tool_obj.get('name', 'Unknown'),
                buyer_email=buyer_email,
                amount=f"£{amount / 100:.2f}",
                net_amount=f"£{net_pence / 100:.2f}",
                dashboard_url=f"{str(request.base_url).rstrip('/')}/dashboard/sales",
            )
            await send_email(
                maker_user['email'],
                f"New sale: {tool_obj.get('name', 'your tool')}",
                maker_html,
            )

    return RedirectResponse(url=f"/purchase/{token}", status_code=303)


@router.get("/purchase/cancel", response_class=HTMLResponse)
async def purchase_cancel(request: Request):
    body = """
    <div class="container" style="text-align:center;padding:80px 0;">
        <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Payment Cancelled</h1>
        <p style="color:var(--ink-muted);margin-top:16px;">Your payment was cancelled. No charge was made.</p>
        <a href="/" class="btn btn-primary mt-4">Back to Home</a>
    </div>
    """
    return HTMLResponse(page_shell("Payment Cancelled", body, user=request.state.user))


@router.get("/purchase/{token}", response_class=HTMLResponse)
async def purchase_delivery(request: Request, token: str):
    db = request.state.db
    purchase = await get_purchase_by_token(db, token)

    if not purchase:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Purchase Not Found</h1>
            <p style="color:var(--ink-muted);margin-top:16px;">This purchase link is invalid or has expired.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    tool_name = escape(str(purchase['tool_name'] or 'Removed Tool'))
    tool_slug = escape(str(purchase['tool_slug'] or ''))
    delivery_type = purchase.get('delivery_type') or 'link'
    delivery_url = str(purchase.get('delivery_url') or '')

    # Build tool dict for integration snippet
    tool_for_snippet = {
        'name': purchase.get('tool_name', ''),
        'url': delivery_url or '',
        'delivery_url': delivery_url,
    }
    snippet_html = integration_snippet_html(tool_for_snippet)

    amount_display = format_price(purchase['amount_pence'])

    # Delivery section depends on type
    if not delivery_url:
        delivery_html = f"""
        <div style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-top:12px;">
            <p style="font-size:15px;color:var(--ink);">The maker hasn't set up delivery yet.</p>
            <p style="font-size:14px;color:var(--ink-muted);margin-top:8px;">We've notified them -- you'll receive an email at <strong>{escape(str(purchase['buyer_email']))}</strong> once it's ready.</p>
        </div>
        """
    elif delivery_type == 'download':
        delivery_html = f"""
        <a href="{escape(delivery_url)}" class="btn btn-slate" style="font-size:16px;padding:14px 32px;" target="_blank" rel="noopener">
            Download Now &darr;
        </a>
        """
    elif delivery_type == 'license_key':
        delivery_html = f"""
        <div style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-top:12px;">
            <p style="font-size:14px;color:var(--ink-muted);margin-bottom:8px;">Your license / access link:</p>
            <a href="{escape(delivery_url)}" target="_blank" rel="noopener"
               style="font-family:var(--font-mono);font-size:14px;word-break:break-all;">{escape(delivery_url)}</a>
        </div>
        """
    else:
        delivery_html = f"""
        <a href="{escape(delivery_url)}" class="btn btn-slate" style="font-size:16px;padding:14px 32px;" target="_blank" rel="noopener">
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
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Purchase Complete!</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">Thank you for purchasing <strong>{tool_name}</strong> for {amount_display}.</p>
        </div>

        <div class="card" style="text-align:center;padding:32px;">
            <h2 style="font-family:var(--font-display);font-size:22px;margin-bottom:20px;color:var(--ink);">
                Your Purchase
            </h2>
            {delivery_html}
            <p style="color:var(--ink-muted);font-size:14px;margin-top:16px;">
                Bookmark this page &mdash; it's your receipt and access link.
            </p>
        </div>

        {snippet_html}

        <div style="text-align:center;margin-top:32px;">
            <a href="{'/' if not tool_slug else f'/tool/{tool_slug}'}" class="btn btn-secondary">{'Back to Home' if not tool_slug else f'Back to {tool_name}'}</a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell(f"Purchase: {tool_name}", body, user=request.state.user))


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
        metadata = session.get("metadata", {})

        # Skip verification purchases — they're handled by the verify route
        if metadata.get("type") == "verification":
            return JSONResponse({"received": True})

        session_id = session.get("id", "")
        tool_id = int(metadata.get("tool_id", 0))
        buyer_email = session.get("customer_details", {}).get("email", "") if session.get("customer_details") else ""
        amount = session.get("amount_total", 0)

        db = request.state.db

        # Check maker's Pro status for correct commission
        is_pro_wh = False
        tool_for_wh = await get_tool_by_id(db, tool_id) if tool_id else None
        if tool_for_wh and tool_for_wh.get('maker_id'):
            mk_cur = await db.execute("SELECT id FROM users WHERE maker_id = ?", (tool_for_wh['maker_id'],))
            mk_row = await mk_cur.fetchone()
            if mk_row:
                sub_wh = await get_active_subscription(db, mk_row['id'])
                is_pro_wh = sub_wh is not None
        commission = calculate_commission(amount, is_pro=is_pro_wh)

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

            # Notify the maker of the sale
            if tool_for_wh and tool_for_wh.get('maker_id'):
                maker_email_cur = await db.execute(
                    "SELECT u.email FROM users u WHERE u.maker_id = ?",
                    (tool_for_wh['maker_id'],)
                )
                maker_user = await maker_email_cur.fetchone()
                if maker_user and maker_user.get('email'):
                    net_pence = amount - commission
                    base_url = str(request.base_url).rstrip('/')
                    maker_html = maker_sale_notification_html(
                        tool_name=tool_for_wh.get('name', 'Unknown'),
                        buyer_email=buyer_email,
                        amount=f"£{amount / 100:.2f}",
                        net_amount=f"£{net_pence / 100:.2f}",
                        dashboard_url=f"{base_url}/dashboard/sales",
                    )
                    await send_email(
                        maker_user['email'],
                        f"New sale: {tool_for_wh.get('name', 'your tool')}",
                        maker_html,
                    )

    return JSONResponse({"received": True})
