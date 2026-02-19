"""Stripe payment helpers for IndieStack marketplace."""

import os
import stripe

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PLATFORM_FEE_PERCENT = 5  # 5% standard platform commission
PRO_FEE_PERCENT = 3  # 3% for Pro makers

stripe.api_key = STRIPE_SECRET_KEY


def calculate_commission(amount_pence: int, is_pro: bool = False) -> int:
    """Calculate platform commission (5% standard, 3% for Pro makers)."""
    rate = PRO_FEE_PERCENT if is_pro else PLATFORM_FEE_PERCENT
    return int(amount_pence * rate / 100)


def create_checkout_session(
    *,
    tool_name: str,
    tool_id: int,
    price_pence: int,
    stripe_account_id: str,
    success_url: str,
    cancel_url: str,
    buyer_email: str = "",
    is_pro: bool = False,
) -> stripe.checkout.Session:
    """Create a Stripe Checkout session with Connect application fee."""
    commission = calculate_commission(price_pence, is_pro=is_pro)

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


VERIFICATION_PRICE_PENCE = 2900  # £29


def create_verification_checkout(
    *,
    tool_name: str,
    tool_id: int,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """Create a Stripe Checkout session for paid verification.

    This is a direct charge to the platform (no Connect) — 100% revenue to IndieStack.
    """
    return stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {
                    "name": f"Verified Badge — {tool_name}",
                    "description": "Gold verified badge, boosted search ranking, and trust signal for your tool listing.",
                },
                "unit_amount": VERIFICATION_PRICE_PENCE,
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tool_id": str(tool_id), "type": "verification"},
    )


def create_stack_checkout_session(
    *,
    stack_title: str,
    stack_id: int,
    total_pence: int,
    success_url: str,
    cancel_url: str,
    buyer_email: str = "",
) -> stripe.checkout.Session:
    """Create a Stripe Checkout session for a Vibe Stack bundle.

    Payment goes to platform account (no destination charge).
    Transfers to individual makers happen post-payment.
    """
    params = dict(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": f"Vibe Stack: {stack_title}"},
                "unit_amount": total_pence,
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"stack_id": str(stack_id), "type": "stack"},
    )
    if buyer_email:
        params["customer_email"] = buyer_email
    return stripe.checkout.Session.create(**params)


def create_transfer(amount_pence: int, destination_account: str, transfer_group: str) -> stripe.Transfer:
    """Create a transfer to a connected account (for stack payouts to makers)."""
    return stripe.Transfer.create(
        amount=amount_pence,
        currency="gbp",
        destination=destination_account,
        transfer_group=transfer_group,
    )
