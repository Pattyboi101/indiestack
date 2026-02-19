"""Stripe payment helpers for IndieStack marketplace."""

import os
import stripe

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PLATFORM_FEE_PERCENT = 20  # 20% platform commission

stripe.api_key = STRIPE_SECRET_KEY


def calculate_commission(amount_pence: int) -> int:
    """Calculate platform commission (20% of total)."""
    return int(amount_pence * PLATFORM_FEE_PERCENT / 100)


def create_checkout_session(
    *,
    tool_name: str,
    tool_id: int,
    price_pence: int,
    stripe_account_id: str,
    success_url: str,
    cancel_url: str,
    buyer_email: str = "",
) -> stripe.checkout.Session:
    """Create a Stripe Checkout session with Connect application fee."""
    commission = calculate_commission(price_pence)

    params = dict(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": tool_name},
                "unit_amount": price_pence,
            },
            "quantity": 1,
        }],
        payment_intent_data={
            "application_fee_amount": commission,
            "transfer_data": {"destination": stripe_account_id},
        },
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tool_id": str(tool_id)},
    )
    if buyer_email:
        params["customer_email"] = buyer_email

    return stripe.checkout.Session.create(**params)


def create_connect_account() -> stripe.Account:
    """Create a Stripe Connect Express account for a maker."""
    return stripe.Account.create(type="express")


def create_onboarding_link(account_id: str, return_url: str, refresh_url: str) -> str:
    """Generate a Stripe Connect onboarding link."""
    link = stripe.AccountLink.create(
        account=account_id,
        return_url=return_url,
        refresh_url=refresh_url,
        type="account_onboarding",
    )
    return link.url


def verify_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify and parse a Stripe webhook event."""
    event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    return event


def retrieve_checkout_session(session_id: str) -> stripe.checkout.Session:
    """Retrieve a completed checkout session with customer details."""
    return stripe.checkout.Session.retrieve(session_id, expand=["customer_details"])
