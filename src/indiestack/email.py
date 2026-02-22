"""Email notifications — zero new dependencies, uses stdlib smtplib."""

import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("SMTP_FROM", SMTP_USER or "noreply@indiestack.fly.dev")
FROM_NAME = "IndieStack"


def _email_wrapper(html_body: str, preview_text: str = "") -> str:
    """Wrap HTML email body in a responsive template."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;padding:0;background:#FAF7F2;}}
.container{{max-width:560px;margin:0 auto;padding:32px 24px;}}.card{{background:white;border-radius:16px;padding:32px;border:1px solid #E8E3DC;}}
a{{color:#C4714E;}}</style></head>
<body><div class="container"><div class="card">{html_body}</div>
<p style="text-align:center;font-size:12px;color:#9C958E;margin-top:24px;">
IndieStack &mdash; Discover indie SaaS tools built by solo developers</p></div></body></html>"""


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success. Non-blocking."""
    if not SMTP_HOST or not SMTP_USER:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(_email_wrapper(html_body), "html"))

    def _send():
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, [to], msg.as_string())
            return True
        except Exception as e:
            import logging
            logging.getLogger("indiestack.email").error(f"Failed to send email to {to}: {e}")
            return False

    return await asyncio.to_thread(_send)


# ── Email Templates ──────────────────────────────────────────────────────

def purchase_receipt_html(*, tool_name: str, amount: str, delivery_url: str) -> str:
    return f"""
    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;">Purchase Confirmation</h2>
    <p style="color:#6B6560;font-size:15px;">Thank you for purchasing <strong>{tool_name}</strong> for {amount}.</p>
    <div style="margin:24px 0;padding:16px;background:#FAF7F2;border-radius:10px;text-align:center;">
        <a href="{delivery_url}" style="display:inline-block;background:#C4714E;color:white;padding:12px 28px;
           border-radius:999px;font-weight:600;text-decoration:none;font-size:15px;">Access Your Purchase</a>
    </div>
    <p style="color:#9C958E;font-size:13px;">Keep this email as your receipt.</p>
    """


def tool_approved_html(*, tool_name: str, tool_url: str) -> str:
    return f"""
    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;">Your Tool is Live!</h2>
    <p style="color:#6B6560;font-size:15px;"><strong>{tool_name}</strong> has been approved and is now visible on IndieStack.</p>
    <div style="margin:24px 0;text-align:center;">
        <a href="{tool_url}" style="display:inline-block;background:#C4714E;color:white;padding:12px 28px;
           border-radius:999px;font-weight:600;text-decoration:none;">View Your Listing</a>
    </div>
    """


def new_review_html(*, tool_name: str, reviewer_name: str, rating: int, review_body: str) -> str:
    stars = "&#9733;" * rating + "&#9734;" * (5 - rating)
    return f"""
    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;">New Review for {tool_name}</h2>
    <p style="color:#E2B764;font-size:20px;margin-bottom:8px;">{stars}</p>
    <p style="color:#6B6560;font-size:15px;"><strong>{reviewer_name}</strong> left a review:</p>
    <blockquote style="border-left:3px solid #E8E3DC;padding:8px 16px;margin:16px 0;color:#6B6560;font-style:italic;">
        {review_body}
    </blockquote>
    """


def password_reset_html(reset_url: str) -> str:
    """Email template for password reset."""
    return f'''
    <h2 style="color:#1A2D4A;margin:0 0 16px;">Reset Your Password</h2>
    <p style="color:#444;line-height:1.6;">We received a request to reset your password. Click the button below to choose a new one.</p>
    <div style="text-align:center;margin:32px 0;">
        <a href="{reset_url}" style="display:inline-block;padding:14px 32px;background:#1A2D4A;color:white;text-decoration:none;border-radius:8px;font-weight:600;font-size:16px;">Reset Password</a>
    </div>
    <p style="color:#888;font-size:13px;line-height:1.5;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
    '''


def email_verification_html(verify_url: str) -> str:
    """Email template for email verification."""
    return f'''
    <h2 style="color:#1A2D4A;margin:0 0 16px;">Verify Your Email</h2>
    <p style="color:#444;line-height:1.6;">Welcome to IndieStack! Please verify your email address to get the most out of your account.</p>
    <div style="text-align:center;margin:32px 0;">
        <a href="{verify_url}" style="display:inline-block;padding:14px 32px;background:#1A2D4A;color:white;text-decoration:none;border-radius:8px;font-weight:600;font-size:16px;">Verify Email</a>
    </div>
    <p style="color:#888;font-size:13px;line-height:1.5;">This link expires in 24 hours.</p>
    '''


def weekly_digest_html(*, maker_name: str, tool_count: int, total_views: int,
                        total_upvotes: int, total_sales: int, revenue: str) -> str:
    return f"""
    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;">Your Weekly Digest</h2>
    <p style="color:#6B6560;font-size:15px;">Hi {maker_name}, here's how your tools performed this week:</p>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:24px 0;">
        <div style="text-align:center;padding:12px;background:#FAF7F2;border-radius:10px;">
            <div style="font-size:24px;font-weight:bold;color:#2D2926;">{tool_count}</div>
            <div style="font-size:12px;color:#9C958E;">Active Tools</div>
        </div>
        <div style="text-align:center;padding:12px;background:#FAF7F2;border-radius:10px;">
            <div style="font-size:24px;font-weight:bold;color:#7A9BB5;">{total_upvotes}</div>
            <div style="font-size:12px;color:#9C958E;">Upvotes</div>
        </div>
        <div style="text-align:center;padding:12px;background:#FAF7F2;border-radius:10px;">
            <div style="font-size:24px;font-weight:bold;color:#2D2926;">{total_views}</div>
            <div style="font-size:12px;color:#9C958E;">Views</div>
        </div>
        <div style="text-align:center;padding:12px;background:#FAF7F2;border-radius:10px;">
            <div style="font-size:24px;font-weight:bold;color:#C4714E;">{revenue}</div>
            <div style="font-size:12px;color:#9C958E;">Earnings</div>
        </div>
    </div>
    <div style="text-align:center;margin-top:16px;">
        <a href="https://indiestack.fly.dev/dashboard" style="display:inline-block;background:#C4714E;color:white;
           padding:10px 24px;border-radius:999px;font-weight:600;text-decoration:none;">View Dashboard</a>
    </div>
    """


def claim_tool_html(tool_name: str, verify_url: str) -> str:
    """Email sent to a user who wants to claim a tool listing."""
    return _email_wrapper(f"""
        <h1 style="font-size:24px;font-weight:700;color:#2D2926;margin-bottom:16px;">
            Claim Your Tool on IndieStack
        </h1>
        <p style="color:#5A5550;font-size:16px;line-height:1.6;margin-bottom:16px;">
            You requested to claim <strong>{tool_name}</strong> on IndieStack.
            Click the button below to verify ownership and take control of this listing.
        </p>
        <p style="color:#5A5550;font-size:14px;line-height:1.6;margin-bottom:24px;">
            Once claimed, you'll be able to edit the listing, track analytics,
            connect your Stripe account to accept payments, and post changelogs.
        </p>
        <div style="text-align:center;margin:32px 0;">
            <a href="{verify_url}" style="display:inline-block;padding:14px 32px;background:#C4714E;
               color:white;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
                Claim {tool_name}
            </a>
        </div>
        <p style="color:#8A8580;font-size:13px;text-align:center;">
            This link expires in 24 hours. If you didn't request this, ignore this email.
        </p>
    """)


def competitor_ping_html(maker_name: str, new_tool_name: str, category_name: str, explore_url: str) -> str:
    """Email sent to makers when a new tool launches in their category."""
    return _email_wrapper(f"""
        <h1 style="font-size:24px;font-weight:700;color:#2D2926;margin-bottom:16px;">
            New Competition in {category_name}
        </h1>
        <p style="color:#5A5550;font-size:16px;line-height:1.6;margin-bottom:16px;">
            Hey {maker_name} — heads up! <strong>{new_tool_name}</strong> just launched
            in the <strong>{category_name}</strong> category on IndieStack.
        </p>
        <p style="color:#5A5550;font-size:14px;line-height:1.6;margin-bottom:24px;">
            Make sure your listing is up to date — update your tags, description, and
            post a changelog to stay competitive. Active tools rank higher in search.
        </p>
        <div style="text-align:center;margin:32px 0;">
            <a href="{explore_url}" style="display:inline-block;padding:14px 32px;background:#C4714E;
               color:white;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
                View Your Dashboard
            </a>
        </div>
        <p style="color:#8A8580;font-size:13px;text-align:center;">
            You're receiving this because you have a tool listed in {category_name} on IndieStack.
        </p>
    """)


def subscriber_digest_html(trending_tools: list, new_tool: dict, total_tokens_saved: int, spotlight_tool=None) -> str:
    """Weekly newsletter for subscribers with trending tools and stats."""
    # Tool of the Week spotlight
    spotlight_html = ''
    if spotlight_tool:
        tool_name = spotlight_tool.get('name', '')
        tool_tagline = spotlight_tool.get('tagline', '')
        tool_slug = spotlight_tool.get('slug', '')
        tool_url = spotlight_tool.get('url', '')

        # Generate a simple code snippet
        snippet = f'curl -s https://indiestack.fly.dev/api/tools/{tool_slug} | python3 -m json.tool'

        spotlight_html = f"""
        <div style="margin-bottom:28px;">
            <div style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#C4714E;font-weight:700;margin-bottom:12px;">
                ⚡ Tool of the Week
            </div>
            <div style="background:#1A2D4A;border-radius:12px;padding:24px;margin-bottom:16px;">
                <div style="color:#fff;font-size:20px;font-weight:700;margin-bottom:4px;">{tool_name}</div>
                <div style="color:rgba(255,255,255,0.6);font-size:14px;margin-bottom:16px;">{tool_tagline}</div>
                <div style="background:#0D2137;border-radius:8px;padding:16px;font-family:'Courier New',monospace;font-size:13px;color:#00D4F5;overflow-x:auto;white-space:pre;line-height:1.6;">
{snippet}</div>
                <div style="margin-top:16px;">
                    <a href="https://indiestack.fly.dev/tool/{tool_slug}"
                       style="color:#00D4F5;text-decoration:none;font-weight:600;font-size:14px;">
                        View on IndieStack →
                    </a>
                </div>
            </div>
        </div>
        """

    # Build trending tools HTML
    trending_html = ""
    for i, t in enumerate(trending_tools[:3], 1):
        name = t.get('name', 'Unknown')
        tagline = t.get('tagline', '')
        slug = t.get('slug', '')
        trending_html += f"""
        <div style="padding:16px;background:#F5F3F0;border-radius:8px;margin-bottom:12px;">
            <div style="display:flex;gap:8px;align-items:baseline;">
                <span style="font-size:20px;font-weight:800;color:#C4714E;">#{i}</span>
                <a href="https://indiestack.fly.dev/tool/{slug}" style="font-size:16px;font-weight:700;color:#2D2926;text-decoration:none;">{name}</a>
            </div>
            <p style="color:#5A5550;font-size:14px;margin-top:4px;">{tagline}</p>
        </div>
        """

    # New tool spotlight
    new_html = ""
    if new_tool:
        new_html = f"""
        <div style="margin-top:24px;">
            <h2 style="font-size:18px;font-weight:700;color:#2D2926;margin-bottom:12px;">Fresh Off the Press</h2>
            <div style="padding:16px;background:#EDF4F9;border-radius:8px;border-left:4px solid #00A8C6;">
                <a href="https://indiestack.fly.dev/tool/{new_tool.get('slug', '')}" style="font-size:16px;font-weight:700;color:#2D2926;text-decoration:none;">{new_tool.get('name', '')}</a>
                <p style="color:#5A5550;font-size:14px;margin-top:4px;">{new_tool.get('tagline', '')}</p>
            </div>
        </div>
        """

    tokens_k = f"{total_tokens_saved // 1000:,}k" if total_tokens_saved >= 1000 else str(total_tokens_saved)

    return _email_wrapper(f"""
        <h1 style="font-size:24px;font-weight:700;color:#2D2926;margin-bottom:8px;">
            Your Weekly Vibe Check
        </h1>
        <p style="color:#8A8580;font-size:14px;margin-bottom:24px;">
            The hottest indie tools this week on IndieStack
        </p>
        {spotlight_html}
        <h2 style="font-size:18px;font-weight:700;color:#2D2926;margin-bottom:12px;">Trending This Week</h2>
        {trending_html}
        {new_html}
        <div style="margin-top:32px;padding:20px;background:linear-gradient(135deg,#2D2926,#3D3936);border-radius:12px;text-align:center;">
            <p style="color:#C4714E;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Community Impact</p>
            <p style="color:white;font-size:28px;font-weight:800;">{tokens_k} tokens saved</p>
            <p style="color:rgba(255,255,255,0.6);font-size:13px;">by developers using indie tools instead of building from scratch</p>
        </div>
        <div style="text-align:center;margin-top:32px;">
            <a href="https://indiestack.fly.dev/explore" style="display:inline-block;padding:14px 32px;background:#C4714E;
               color:white;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
                Explore All Tools
            </a>
        </div>
    """)


def wishlist_update_html(user_name: str, tool_name: str, update_title: str, tool_url: str) -> str:
    """Email sent when a wishlisted tool ships an update."""
    return _email_wrapper(f"""
        <h1 style="font-size:24px;font-weight:700;color:#2D2926;margin-bottom:16px;">
            A Tool You Saved Just Shipped an Update
        </h1>
        <p style="color:#5A5550;font-size:16px;line-height:1.6;margin-bottom:16px;">
            Hey {user_name} — <strong>{tool_name}</strong> on your wishlist just posted an update:
        </p>
        <div style="padding:16px;background:#F5F3F0;border-radius:8px;margin-bottom:24px;border-left:4px solid #C4714E;">
            <p style="font-size:16px;font-weight:600;color:#2D2926;margin:0;">
                {update_title if update_title else 'New update available'}
            </p>
        </div>
        <div style="text-align:center;margin:32px 0;">
            <a href="{tool_url}" style="display:inline-block;padding:14px 32px;background:#C4714E;
               color:white;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
                Check It Out
            </a>
        </div>
        <p style="color:#8A8580;font-size:13px;text-align:center;">
            You're receiving this because {tool_name} is on your IndieStack wishlist.
        </p>
    """)
