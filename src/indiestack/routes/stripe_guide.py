"""Stripe setup guide — how to connect Stripe and start selling."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


def _step_card(number: str, title: str, body: str) -> str:
    return f'''
    <div style="display:flex;gap:20px;align-items:flex-start;">
        <div style="min-width:48px;height:48px;background:linear-gradient(135deg,#1A2D4A,#0D1B2A);
                    border-radius:50%;display:flex;align-items:center;justify-content:center;
                    font-family:var(--font-display);font-size:22px;color:#00D4F5;font-weight:700;">{number}</div>
        <div>
            <h3 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin:0 0 8px;">{title}</h3>
            <p style="color:var(--ink-muted);font-size:15px;line-height:1.6;margin:0;">{body}</p>
        </div>
    </div>
    '''


def _faq_item(q: str, a: str) -> str:
    return f'''
    <div style="border-bottom:1px solid var(--border);padding:16px 0;">
        <h4 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 6px;">{q}</h4>
        <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;margin:0;">{a}</p>
    </div>
    '''


@router.get("/stripe-guide", response_class=HTMLResponse)
async def stripe_guide(request: Request):
    user = request.state.user

    steps_html = f'''
    <div style="display:flex;flex-direction:column;gap:32px;margin:40px 0;">
        {_step_card("1", "Set your price",
            "Log into your <a href='/dashboard' style='color:#00D4F5;'>dashboard</a>, click <strong>Edit</strong> on your tool, "
            "and set a monthly price in GBP. This is what buyers will pay."
        )}
        {_step_card("2", "Connect Stripe",
            "On your dashboard, click the <strong>Connect Stripe</strong> button. "
            "You'll be taken to Stripe Express onboarding -- it takes about 2 minutes. "
            "You'll need your bank details and a form of ID. Once connected, a <strong>Buy Now</strong> button "
            "appears on your tool page automatically."
        )}
        {_step_card("3", "Get paid",
            "When someone buys your tool, the payment goes straight to your Stripe account. "
            "We take a small commission (5% standard, 3% for Pro makers) plus Stripe's standard processing fees. "
            "The rest is yours. Stripe pays out to your bank daily."
        )}
    </div>
    '''

    faq_html = f'''
    <div class="card" style="padding:24px;margin-top:40px;">
        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0 0 8px;">FAQ</h2>
        {_faq_item("What does IndieStack take?",
            "5% commission on each sale (3% if you're a Pro maker at &pound;9/month). "
            "Plus Stripe's standard processing fee (1.5% + 20p for UK cards). "
            "You keep the rest."
        )}
        {_faq_item("When do I get paid?",
            "Stripe pays out to your bank account daily (after an initial 7-day holding period for new accounts). "
            "You can track all your sales in your <a href='/dashboard/sales' style='color:#00D4F5;'>dashboard</a>."
        )}
        {_faq_item("Can I change my price later?",
            "Yes. Edit your tool from your dashboard anytime. The new price takes effect immediately."
        )}
        {_faq_item("What if I don't have a Stripe account?",
            "No problem. Clicking 'Connect Stripe' creates one for you through Stripe Express. "
            "It's free and takes about 2 minutes."
        )}
        {_faq_item("Do I need to handle payments or invoices?",
            "No. IndieStack handles the entire checkout, receipt emails, and delivery page. "
            "You just set your price and connect Stripe."
        )}
    </div>
    '''

    body = f'''
    <div class="container" style="max-width:680px;padding:48px 24px;">
        <div style="text-align:center;margin-bottom:16px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin:0;">
                Start Selling in 3 Steps
            </h1>
            <p style="color:var(--ink-muted);margin-top:8px;font-size:16px;">
                Connect Stripe, set your price, and start earning from your indie tool.
            </p>
        </div>

        {steps_html}

        <div style="text-align:center;margin-top:40px;">
            <a href="/dashboard" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
                Go to Dashboard &rarr;
            </a>
            <p style="color:var(--ink-muted);font-size:13px;margin-top:12px;">
                Don't have a tool listed yet? <a href="/submit" style="color:#00D4F5;">Submit one free</a>.
            </p>
        </div>

        {faq_html}
    </div>
    '''

    return HTMLResponse(page_shell(
        "Start Selling — Stripe Setup Guide",
        body,
        user=user,
        description="How to connect Stripe and start selling your indie tool on IndieStack. Set a price, connect Stripe, get paid.",
    ))
