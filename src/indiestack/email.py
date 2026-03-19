"""Email notifications — zero new dependencies, uses stdlib smtplib."""

import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from html import escape
from indiestack.config import BASE_URL

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("SMTP_FROM", SMTP_USER or "noreply@indiestack.ai")
FROM_NAME = "IndieStack"


def _email_wrapper(html_body: str, preview_text: str = "", unsubscribe_url: str = "") -> str:
    """Wrap HTML email body in a responsive template."""
    if unsubscribe_url:
        unsub = f'<br><a href="{unsubscribe_url}" style="color:#9C958E;font-size:12px;">Unsubscribe</a>'
    else:
        unsub = '<br><a href="mailto:pajebay1@gmail.com?subject=Unsubscribe" style="color:#9C958E;font-size:12px;">Unsubscribe</a>'
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;padding:0;background:#FAF7F2;}}
.container{{max-width:560px;margin:0 auto;padding:32px 24px;}}.card{{background:white;border-radius:16px;padding:32px;border:1px solid #E8E3DC;}}
a{{color:#C4714E;}}</style></head>
<body><div class="container"><div class="card">{html_body}</div>
<p style="text-align:center;font-size:12px;color:#9C958E;margin-top:24px;">
IndieStack &mdash; Discover developer tools built by independent makers{unsub}</p></div></body></html>"""


async def send_email(to: str, subject: str, html_body: str, *, unsubscribe_url: str = "") -> bool:
    """Send an email via SMTP. Returns True on success. Non-blocking."""
    if not SMTP_HOST or not SMTP_USER:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to
    if unsubscribe_url:
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    else:
        msg["List-Unsubscribe"] = "<mailto:pajebay1@gmail.com?subject=Unsubscribe>"
    msg.attach(MIMEText(_email_wrapper(html_body, unsubscribe_url=unsubscribe_url), "html"))

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
    tool_name = escape(tool_name)
    return f"""
    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;">Purchase Confirmation</h2>
    <p style="color:#6B6560;font-size:15px;">Thank you for purchasing <strong>{tool_name}</strong> for {amount}.</p>
    <div style="margin:24px 0;padding:16px;background:#FAF7F2;border-radius:10px;text-align:center;">
        <a href="{delivery_url}" style="display:inline-block;background:#C4714E;color:white;padding:12px 28px;
           border-radius:999px;font-weight:600;text-decoration:none;font-size:15px;">Access Your Purchase</a>
    </div>
    <p style="color:#9C958E;font-size:13px;">Keep this email as your receipt.</p>
    """


def maker_sale_notification_html(*, tool_name: str, buyer_email: str, amount: str,
                                   net_amount: str, dashboard_url: str) -> str:
    """Email sent to maker when someone purchases their tool."""
    tool_name = escape(tool_name)
    buyer_email = escape(buyer_email)
    return f"""
    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;">&#127881; You Made a Sale!</h2>
    <p style="color:#6B6560;font-size:15px;line-height:1.6;">
        Someone just purchased <strong>{tool_name}</strong>!
    </p>
    <div style="margin:24px 0;padding:20px;background:#ECFDF5;border-radius:12px;text-align:center;">
        <div style="font-size:32px;font-weight:800;color:#10B981;">{amount}</div>
        <div style="font-size:13px;color:#6B6560;margin-top:4px;">Sale amount</div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid #D1FAE5;">
            <div style="font-size:22px;font-weight:700;color:#059669;">{net_amount}</div>
            <div style="font-size:13px;color:#6B6560;margin-top:2px;">Your earnings</div>
        </div>
    </div>
    <p style="color:#9C958E;font-size:13px;">Buyer: {buyer_email}</p>
    <div style="margin:24px 0;text-align:center;">
        <a href="{dashboard_url}" style="display:inline-block;background:#C4714E;color:white;padding:12px 28px;
           border-radius:999px;font-weight:600;text-decoration:none;font-size:15px;">View Sales Dashboard</a>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;">
        Funds are deposited to your connected Stripe account.
    </p>
    """


def tool_approved_html(*, tool_name: str, tool_url: str) -> str:
    tool_name = escape(tool_name)
    return f"""
    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;">Your Tool is Live!</h2>
    <p style="color:#6B6560;font-size:15px;"><strong>{tool_name}</strong> has been approved and is now visible on IndieStack.</p>
    <div style="margin:24px 0;text-align:center;">
        <a href="{tool_url}" style="display:inline-block;background:#C4714E;color:white;padding:12px 28px;
           border-radius:999px;font-weight:600;text-decoration:none;">View Your Listing</a>
    </div>
    <div style="margin:24px 0;padding:20px;background:#EDF8FF;border-left:4px solid #00D4F5;border-radius:8px;">
        <p style="font-size:16px;font-weight:700;color:#1A2D4A;margin:0 0 8px;">Ready to sell?</p>
        <p style="color:#5A5550;font-size:14px;line-height:1.6;margin:0;">
            Connect your Stripe account from your dashboard to accept payments directly on IndieStack.
            We only take 5% (3% for Pro makers).
        </p>
    </div>
    """


def new_review_html(*, tool_name: str, reviewer_name: str, rating: int, review_body: str) -> str:
    tool_name = escape(tool_name)
    reviewer_name = escape(reviewer_name)
    review_body = escape(review_body)
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


def maker_weekly_digest_html(*, maker_name: str, tool_count: int, total_views: int,
                              total_upvotes: int, total_sales: int, revenue: str) -> str:
    maker_name = escape(maker_name)
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
        <a href="{BASE_URL}/dashboard" style="display:inline-block;background:#C4714E;color:white;
           padding:10px 24px;border-radius:999px;font-weight:600;text-decoration:none;">View Dashboard</a>
    </div>
    """


def weekly_digest_html(
    week_label: str,
    new_tools: list[dict],
    top_clicked: list[dict],
    top_searched: list[str],
    totw_name: str | None,
    totw_slug: str | None,
    totw_clicks: int,
    total_tools: int,
    total_makers: int,
    subscriber_count: int,
    unsubscribe_url: str = "",
) -> str:
    """Auto-generated weekly digest newsletter for subscribers."""
    base = BASE_URL

    # Stats bar
    stats_bar = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:20px 0;">
      <tr>
        <td style="text-align:center;padding:12px 0;background:#F0F7FA;border-radius:10px;">
          <span style="font-size:15px;color:#1A2D4A;font-weight:700;">{total_tools}</span>
          <span style="font-size:13px;color:#6B7280;"> tools</span>
          <span style="color:#D1D5DB;margin:0 8px;">&middot;</span>
          <span style="font-size:15px;color:#1A2D4A;font-weight:700;">{total_makers}</span>
          <span style="font-size:13px;color:#6B7280;"> makers</span>
          <span style="color:#D1D5DB;margin:0 8px;">&middot;</span>
          <span style="font-size:15px;color:#1A2D4A;font-weight:700;">{subscriber_count}</span>
          <span style="font-size:13px;color:#6B7280;"> subscribers</span>
        </td>
      </tr>
    </table>
    """

    # Tool of the Week
    totw_section = ""
    if totw_name and totw_slug:
        totw_name = escape(totw_name)
        totw_section = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0;">
      <tr><td style="font-size:14px;font-weight:700;color:#1A2D4A;padding-bottom:12px;">&#127942; Tool of the Week</td></tr>
      <tr>
        <td style="background:#1A2D4A;border-radius:12px;padding:20px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td>
                <a href="{base}/tool/{totw_slug}" style="font-size:20px;font-weight:700;color:#00D4F5;text-decoration:none;">{totw_name}</a>
                <p style="color:rgba(255,255,255,0.7);font-size:14px;margin:8px 0 0;">{totw_clicks} outbound clicks this week</p>
              </td>
              <td style="text-align:right;vertical-align:middle;">
                <span style="display:inline-block;background:#00D4F5;color:#1A2D4A;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:6px 12px;border-radius:999px;">Winner</span>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """

    # New This Week
    if new_tools:
        new_rows = ""
        for t in new_tools[:5]:
            name = escape(t.get("name", ""))
            slug = t.get("slug", "")
            tagline = escape(t.get("tagline", ""))
            new_rows += f"""
      <tr>
        <td style="padding:12px 16px;border-bottom:1px solid #E8E3DC;">
          <a href="{base}/tool/{slug}" style="font-size:15px;font-weight:600;color:#1A2D4A;text-decoration:none;">{name}</a>
          <p style="color:#6B7280;font-size:13px;margin:4px 0 0;line-height:1.4;">{tagline}</p>
        </td>
      </tr>"""
        new_section = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0;">
      <tr><td style="font-size:14px;font-weight:700;color:#1A2D4A;padding-bottom:12px;">&#127381; New This Week</td></tr>
      <tr><td>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FAFAF8;border-radius:10px;overflow:hidden;">
          {new_rows}
        </table>
      </td></tr>
    </table>"""
    else:
        new_section = """
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0;">
      <tr><td style="font-size:14px;font-weight:700;color:#1A2D4A;padding-bottom:12px;">&#127381; New This Week</td></tr>
      <tr><td style="padding:16px;background:#FAFAF8;border-radius:10px;color:#6B7280;font-size:14px;">No new tools this week</td></tr>
    </table>"""

    # Most Clicked
    if top_clicked:
        click_rows = ""
        for i, t in enumerate(top_clicked[:5], 1):
            name = escape(t.get("name", ""))
            slug = t.get("slug", "")
            clicks = t.get("clicks", t.get("count", 0))
            click_rows += f"""
      <tr>
        <td style="padding:10px 16px;border-bottom:1px solid #E8E3DC;width:30px;font-size:16px;font-weight:800;color:#00D4F5;">#{i}</td>
        <td style="padding:10px 16px;border-bottom:1px solid #E8E3DC;">
          <a href="{base}/tool/{slug}" style="font-size:14px;font-weight:600;color:#1A2D4A;text-decoration:none;">{name}</a>
        </td>
        <td style="padding:10px 16px;border-bottom:1px solid #E8E3DC;text-align:right;font-size:14px;font-weight:700;color:#1A2D4A;">{clicks} clicks</td>
      </tr>"""
        clicked_section = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0;">
      <tr><td style="font-size:14px;font-weight:700;color:#1A2D4A;padding-bottom:12px;">&#128293; Most Clicked</td></tr>
      <tr><td>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FAFAF8;border-radius:10px;overflow:hidden;">
          {click_rows}
        </table>
      </td></tr>
    </table>"""
    else:
        clicked_section = ""

    # Trending Searches
    if top_searched:
        search_items = ""
        for term in top_searched[:5]:
            search_items += f"""
      <tr>
        <td style="padding:8px 16px;border-bottom:1px solid #E8E3DC;">
          <span style="font-size:14px;color:#1A2D4A;">&#128269; {escape(term)}</span>
        </td>
      </tr>"""
        search_section = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0;">
      <tr><td style="font-size:14px;font-weight:700;color:#1A2D4A;padding-bottom:12px;">&#128270; Trending Searches</td></tr>
      <tr><td>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FAFAF8;border-radius:10px;overflow:hidden;">
          {search_items}
        </table>
      </td></tr>
    </table>"""
    else:
        search_section = ""

    # Footer
    footer = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:32px 0 0;">
      <tr><td style="text-align:center;padding:20px 0;border-top:1px solid #E8E3DC;">
        <a href="{base}/explore" style="display:inline-block;background:#00D4F5;color:#1A2D4A;padding:12px 28px;border-radius:8px;font-weight:700;font-size:15px;text-decoration:none;">Browse all tools &rarr;</a>
      </td></tr>
      <tr><td style="text-align:center;padding:12px 0;">
        <p style="color:#9C958E;font-size:12px;line-height:1.6;margin:0;">
          You're receiving this because you subscribed to IndieStack updates.<br>
          <a href="{unsubscribe_url or 'mailto:pajebay1@gmail.com?subject=Unsubscribe'}" style="color:#9C958E;">Unsubscribe</a>
          &nbsp;&middot;&nbsp;
          <a href="{base}/explore" style="color:#00D4F5;text-decoration:none;">indiestack.ai/explore</a>
        </p>
      </td></tr>
    </table>
    """

    return f"""
    <div style="text-align:center;margin-bottom:8px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Weekly Digest
        </div>
    </div>
    <h1 style="font-family:serif;font-size:24px;color:#1A2D4A;text-align:center;margin:12px 0 4px;">
        IndieStack Weekly &mdash; {week_label}
    </h1>
    {stats_bar}
    {totw_section}
    {new_section}
    {clicked_section}
    {search_section}
    {footer}
    """


def claim_tool_html(tool_name: str, verify_url: str) -> str:
    """Email sent to a user who wants to claim a tool listing."""
    tool_name = escape(tool_name)
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
    maker_name = escape(maker_name)
    new_tool_name = escape(new_tool_name)
    category_name = escape(category_name)
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
        tool_name = escape(spotlight_tool.get('name', ''))
        tool_tagline = escape(spotlight_tool.get('tagline', ''))
        tool_slug = spotlight_tool.get('slug', '')
        tool_url = spotlight_tool.get('url', '')

        # Generate a simple code snippet
        snippet = f'curl -s {BASE_URL}/api/tools/{tool_slug} | python3 -m json.tool'

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
                    <a href="{BASE_URL}/tool/{tool_slug}"
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
        name = escape(t.get('name', 'Unknown'))
        tagline = escape(t.get('tagline', ''))
        slug = t.get('slug', '')
        trending_html += f"""
        <div style="padding:16px;background:#F5F3F0;border-radius:8px;margin-bottom:12px;">
            <div style="display:flex;gap:8px;align-items:baseline;">
                <span style="font-size:20px;font-weight:800;color:#C4714E;">#{i}</span>
                <a href="{BASE_URL}/tool/{slug}" style="font-size:16px;font-weight:700;color:#2D2926;text-decoration:none;">{name}</a>
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
                <a href="{BASE_URL}/tool/{new_tool.get('slug', '')}" style="font-size:16px;font-weight:700;color:#2D2926;text-decoration:none;">{escape(new_tool.get('name', ''))}</a>
                <p style="color:#5A5550;font-size:14px;margin-top:4px;">{escape(new_tool.get('tagline', ''))}</p>
            </div>
        </div>
        """

    tokens_k = f"{total_tokens_saved // 1000:,}k" if total_tokens_saved >= 1000 else str(total_tokens_saved)

    return _email_wrapper(f"""
        <h1 style="font-size:24px;font-weight:700;color:#2D2926;margin-bottom:8px;">
            Your Weekly Vibe Check
        </h1>
        <p style="color:#8A8580;font-size:14px;margin-bottom:24px;">
            The hottest developer tools this week on IndieStack
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
            <a href="{BASE_URL}/explore" style="display:inline-block;padding:14px 32px;background:#C4714E;
               color:white;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
                Explore All Tools
            </a>
        </div>
    """)


def ego_ping_html(*, maker_name: str, tool_name: str, tool_slug: str,
                   views: int, clicks: int, upvotes: int, wishlists: int,
                   has_changelog: bool, has_active_badge: bool) -> str:
    """Weekly 'Ego Ping' email to hook makers back to their dashboard."""
    maker_name = escape(maker_name)
    tool_name = escape(tool_name)
    # Humanise the views number
    if views == 0:
        views_label = "Your tool is listed and waiting for its first visitors"
    elif views == 1:
        views_label = "1 developer discovered your tool this week"
    else:
        views_label = f"{views} developers discovered your tool this week"

    # Contextual CTA
    if not has_changelog:
        cta_text = "Post your first changelog to earn the Active badge"
        cta_sub = "Makers who post updates get 2x more visibility in search."
    elif not has_active_badge:
        cta_text = "Post an update to earn the Active badge"
        cta_sub = "You've posted before — one more recent update and you'll unlock the badge."
    else:
        cta_text = "Keep the streak! Post an update this week"
        cta_sub = "Active tools rank higher and get featured in the newsletter."

    base = BASE_URL

    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Weekly Stats
        </div>
    </div>
    <h2 style="font-family:serif;font-size:22px;color:#1A2D4A;margin-bottom:4px;text-align:center;">
        {tool_name}
    </h2>
    <p style="color:#6B6560;font-size:15px;text-align:center;margin-bottom:24px;">
        Hi {maker_name} &mdash; {views_label}
    </p>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0;">
        <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:28px;font-weight:bold;color:#1A2D4A;">{views}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Views</div>
        </div>
        <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:28px;font-weight:bold;color:#10B981;">{clicks}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Clicks</div>
        </div>
        <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:28px;font-weight:bold;color:#00D4F5;">{upvotes}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Upvotes</div>
        </div>
        <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:28px;font-weight:bold;color:#1A2D4A;">{wishlists}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Bookmarks</div>
        </div>
    </div>
    <div style="margin:28px 0;padding:20px;background:#1A2D4A;border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 4px;">{cta_text}</p>
        <p style="color:rgba(255,255,255,0.6);font-size:13px;margin:0;">{cta_sub}</p>
    </div>
    <div style="text-align:center;margin-top:24px;">
        <a href="{base}/dashboard" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            View Dashboard
        </a>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because you have a tool on
        <a href="{base}/tool/{tool_slug}" style="color:#00D4F5;">IndieStack</a>.
    </p>
    """


def citation_alert_html(*, maker_name: str, tool_name: str, tool_slug: str,
                         citation_count: int, agent_names: list[str],
                         is_pro: bool, sample_context: str = "") -> str:
    """Email alerting a maker that AI agents cited their tool this week."""
    maker_name = escape(maker_name)
    tool_name = escape(tool_name)
    sample_context = escape(sample_context)

    if citation_count == 1:
        headline = f"AI agents recommended {tool_name} 1 time this week"
    else:
        headline = f"AI agents recommended {tool_name} {citation_count} times this week"

    agents_display = ", ".join(escape(a) for a in agent_names) if agent_names else "Unknown agents"

    # Context section — the conversion mechanism
    if is_pro and sample_context:
        context_section = f"""
    <div style="margin:28px 0;padding:20px;background:#F0F7FA;border-left:4px solid #00D4F5;border-radius:8px;">
        <p style="font-size:12px;font-weight:700;color:#1A2D4A;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">
            Sample Citation Context
        </p>
        <p style="color:#1A2D4A;font-size:14px;line-height:1.6;margin:0;font-style:italic;">
            &ldquo;{sample_context}&rdquo;
        </p>
    </div>
    <div style="text-align:center;margin-top:24px;">
        <a href="{BASE_URL}/dashboard" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            View All Citations
        </a>
    </div>"""
    elif not is_pro:
        context_section = f"""
    <div style="margin:28px 0;padding:20px;background:#1A2D4A;border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 4px;">
            What did the agents say about your tool?
        </p>
        <p style="color:rgba(255,255,255,0.6);font-size:13px;margin:0;">
            Upgrade to Pro to see the full context of every AI citation.
        </p>
    </div>
    <div style="text-align:center;margin-top:24px;">
        <a href="{BASE_URL}/pricing" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Upgrade to Pro &mdash; $19/mo
        </a>
    </div>"""
    else:
        # Pro but no sample context
        context_section = f"""
    <div style="text-align:center;margin-top:24px;">
        <a href="{BASE_URL}/dashboard" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            View Dashboard
        </a>
    </div>"""

    base = BASE_URL

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
        <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:28px;font-weight:bold;color:#1A2D4A;">{citation_count}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Citations</div>
        </div>
        <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
            <div style="font-size:16px;font-weight:bold;color:#00D4F5;line-height:1.4;">{agents_display}</div>
            <div style="font-size:12px;color:#6B6560;margin-top:4px;">Citing Agents</div>
        </div>
    </div>
    {context_section}
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because {tool_name} is listed on
        <a href="{base}/tool/{tool_slug}" style="color:#00D4F5;">IndieStack</a>.
    </p>
    """


def citation_milestone_html(*, maker_name: str, tool_name: str, tool_slug: str,
                            milestone: int, total: int) -> str:
    """Email sent when a tool crosses a citation milestone."""
    maker_name = escape(maker_name)
    tool_name = escape(tool_name)
    base = BASE_URL

    # Contextual message based on milestone size
    if milestone >= 500:
        congrats = "This is exceptional."
        cta_text = "See which AI agents are recommending your tool"
        cta_sub = "Upgrade to Pro to unlock agent breakdown, daily trends, and more."
    elif milestone >= 100:
        congrats = "Your tool is building serious momentum."
        cta_text = "Want to know which AI agents recommend you?"
        cta_sub = "Pro makers get full agent breakdowns and daily citation trends."
    else:
        congrats = "Your tool is getting noticed by AI agents."
        cta_text = "Keep the momentum going"
        cta_sub = "Post a changelog update to stay top-of-mind for AI agents."

    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Milestone Reached
        </div>
    </div>
    <h2 style="font-family:serif;font-size:22px;color:#1A2D4A;margin-bottom:4px;text-align:center;">
        {tool_name}
    </h2>
    <p style="color:#6B6560;font-size:15px;text-align:center;margin-bottom:24px;">
        Hi {maker_name} &mdash; {congrats}
    </p>
    <div style="text-align:center;padding:32px;background:#F0F7FA;border-radius:12px;margin:24px 0;">
        <div style="font-size:48px;font-weight:bold;color:#1A2D4A;">{total}</div>
        <div style="font-size:14px;color:#6B6560;margin-top:4px;">
            times recommended by AI agents
        </div>
    </div>
    <div style="margin:28px 0;padding:20px;background:#1A2D4A;border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 4px;">{cta_text}</p>
        <p style="color:rgba(255,255,255,0.6);font-size:13px;margin:0;">{cta_sub}</p>
    </div>
    <div style="text-align:center;margin-top:24px;">
        <a href="{base}/tool/{tool_slug}" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            View Your Listing
        </a>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because you have a tool on
        <a href="{base}" style="color:#00D4F5;">IndieStack</a>.
    </p>
    """


def boost_expired_html(*, tool_name: str, tool_slug: str, views: int, upvotes: int, wishlists: int) -> str:
    """Email sent when a boost expires, highlighting the value delivered."""
    tool_name = escape(tool_name)
    impressions = views * 3
    return _email_wrapper(f"""
        <h1 style="font-size:24px;font-weight:700;color:#2D2926;margin-bottom:16px;">
            Your Boost Results for {tool_name}
        </h1>
        <p style="color:#5A5550;font-size:16px;line-height:1.6;margin-bottom:24px;">
            Your 30-day Featured boost has ended. Here's what it delivered:
        </p>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:24px 0;">
            <div style="text-align:center;padding:16px;background:#F0FFFE;border-radius:12px;">
                <div style="font-size:28px;font-weight:800;color:#1A2D4A;">{views}</div>
                <div style="font-size:12px;color:#6B7280;">Profile Views</div>
            </div>
            <div style="text-align:center;padding:16px;background:#F0FFFE;border-radius:12px;">
                <div style="font-size:28px;font-weight:800;color:#1A2D4A;">~{impressions}</div>
                <div style="font-size:12px;color:#6B7280;">Search Impressions</div>
            </div>
            <div style="text-align:center;padding:16px;background:#F0FFFE;border-radius:12px;">
                <div style="font-size:28px;font-weight:800;color:#1A2D4A;">{upvotes}</div>
                <div style="font-size:12px;color:#6B7280;">Upvotes</div>
            </div>
            <div style="text-align:center;padding:16px;background:#F0FFFE;border-radius:12px;">
                <div style="font-size:28px;font-weight:800;color:#1A2D4A;">{wishlists}</div>
                <div style="font-size:12px;color:#6B7280;">Bookmarks</div>
            </div>
        </div>
        <p style="color:#5A5550;font-size:14px;line-height:1.6;">
            During your boost, your tool was featured in the weekly newsletter,
            shown with priority placement in search results, and displayed with
            the &#9733; Featured badge on your listing.
        </p>
        <div style="text-align:center;margin:32px 0;">
            <a href="{BASE_URL}/tool/{tool_slug}"
               style="display:inline-block;padding:14px 32px;background:#1A2D4A;color:white;
                      border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
                Boost Again for &pound;29
            </a>
        </div>
        <p style="color:#8A8580;font-size:13px;text-align:center;">
            Re-boosting keeps your Featured badge active and maintains your priority placement.
        </p>
    """)


def wishlist_update_html(user_name: str, tool_name: str, update_title: str, tool_url: str) -> str:
    """Email sent when a bookmarked tool ships an update."""
    user_name = escape(user_name)
    tool_name = escape(tool_name)
    update_title = escape(update_title)
    return _email_wrapper(f"""
        <h1 style="font-size:24px;font-weight:700;color:#2D2926;margin-bottom:16px;">
            A Tool You Saved Just Shipped an Update
        </h1>
        <p style="color:#5A5550;font-size:16px;line-height:1.6;margin-bottom:16px;">
            Hey {user_name} — <strong>{tool_name}</strong> that you bookmarked just posted an update:
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
            You're receiving this because you bookmarked {tool_name} on IndieStack.
        </p>
    """)


def pro_weekly_report_html(
    *,
    maker_name: str,
    total_citations: int,
    top_tool_name: str | None,
    top_tool_slug: str | None,
    top_tool_citations: int,
    agent_breakdown: list[dict],
    new_tools_in_categories: list[dict],
    quality_score: int | None,
) -> str:
    """Weekly AI Report email for Pro subscribers — citation stats, top tool, new competitors."""
    maker_name = escape(maker_name)
    base = BASE_URL

    # Top tool section
    top_tool_html = ""
    if top_tool_name and top_tool_citations > 0:
        top_tool_html = f"""
    <div style="margin:24px 0;padding:20px;background:#F0F7FA;border-left:4px solid #00D4F5;border-radius:8px;">
        <p style="font-size:12px;font-weight:700;color:#1A2D4A;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">
            Top Cited Tool
        </p>
        <p style="font-size:18px;font-weight:700;color:#1A2D4A;margin:0 0 4px;">
            <a href="{base}/tool/{escape(top_tool_slug or '')}" style="color:#1A2D4A;text-decoration:none;">{escape(top_tool_name)}</a>
        </p>
        <p style="font-size:14px;color:#6B6560;margin:0;">
            {top_tool_citations} AI recommendation{"s" if top_tool_citations != 1 else ""} this week
        </p>
    </div>"""

    # Agent breakdown
    agent_html = ""
    if agent_breakdown:
        agent_rows = ""
        for ab in agent_breakdown:
            label = {
                "mcp": "MCP Server (Claude, Cursor, etc.)",
                "api": "REST API",
                "web": "Web Search",
            }.get(ab.get("agent_name", ""), ab.get("agent_name", "Unknown"))
            agent_rows += f"""
        <tr>
            <td style="padding:8px 0;font-size:14px;color:#1A2D4A;">{escape(label)}</td>
            <td style="padding:8px 0;font-size:14px;color:#1A2D4A;text-align:right;font-weight:600;">{ab['count']}</td>
        </tr>"""
        agent_html = f"""
    <div style="margin:24px 0;">
        <p style="font-size:12px;font-weight:700;color:#1A2D4A;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px;">
            Recommendation Sources
        </p>
        <table style="width:100%;border-collapse:collapse;">
            {agent_rows}
        </table>
    </div>"""

    # New tools in your categories
    new_tools_html = ""
    if new_tools_in_categories:
        items = ""
        for nt in new_tools_in_categories[:5]:
            items += f"""
        <li style="margin-bottom:8px;">
            <a href="{base}/tool/{escape(nt['slug'])}" style="color:#00D4F5;font-weight:600;text-decoration:none;">{escape(nt['name'])}</a>
            <span style="color:#6B6560;font-size:13px;"> &mdash; {escape(nt.get('tagline', ''))}</span>
        </li>"""
        new_tools_html = f"""
    <div style="margin:24px 0;">
        <p style="font-size:12px;font-weight:700;color:#1A2D4A;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px;">
            New in Your Categories
        </p>
        <ul style="padding-left:20px;margin:0;list-style:disc;">
            {items}
        </ul>
    </div>"""

    # Quality score nudge
    quality_html = ""
    if quality_score is not None and quality_score < 70:
        quality_html = f"""
    <div style="margin:24px 0;padding:16px 20px;background:#FEF3C7;border-radius:8px;">
        <p style="font-size:14px;color:#92400E;margin:0;">
            Your listing quality score is <strong>{quality_score}/100</strong>.
            <a href="{base}/dashboard" style="color:#92400E;font-weight:600;">Improve it</a> to rank higher in AI recommendations.
        </p>
    </div>"""

    return _email_wrapper(f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Pro Weekly Report
        </div>
    </div>
    <h2 style="font-family:serif;font-size:22px;color:#1A2D4A;margin-bottom:4px;text-align:center;">
        Your AI Intelligence Report
    </h2>
    <p style="color:#6B6560;font-size:15px;text-align:center;margin-bottom:24px;">
        Hi {maker_name} &mdash; here's how AI agents interacted with your tools this week.
    </p>
    <div style="text-align:center;padding:24px;background:#F0F7FA;border-radius:12px;margin-bottom:24px;">
        <div style="font-size:42px;font-weight:800;color:#1A2D4A;">{total_citations}</div>
        <div style="font-size:14px;color:#6B6560;margin-top:4px;">AI recommendations this week</div>
    </div>
    {top_tool_html}
    {agent_html}
    {new_tools_html}
    {quality_html}
    <div style="text-align:center;margin-top:32px;">
        <a href="{base}/dashboard" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            View Full Dashboard
        </a>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this as an IndieStack Pro subscriber.
    </p>
    """)


def maker_welcome_html(*, maker_name: str, tool_name: str, tool_slug: str,
                        dashboard_url: str = f"{BASE_URL}/dashboard") -> str:
    """Welcome email sent when a new maker claims a tool or signs up."""
    maker_name = escape(maker_name)
    tool_name = escape(tool_name)
    base = BASE_URL
    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Welcome to IndieStack
        </div>
    </div>
    <h2 style="font-family:serif;font-size:24px;color:#1A2D4A;margin-bottom:8px;text-align:center;">
        {tool_name} is Live!
    </h2>
    <p style="color:#6B6560;font-size:15px;line-height:1.6;text-align:center;margin-bottom:24px;">
        Hey {maker_name} &mdash; your tool is now listed on IndieStack and visible
        to developers browsing for indie alternatives.
    </p>
    <div style="margin:24px 0;">
        <p style="font-size:14px;font-weight:700;color:#1A2D4A;margin-bottom:16px;">
            Three quick wins to make your listing stand out:
        </p>
        <div style="padding:14px 16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;">1. Complete your maker profile</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;">
                Add a bio and avatar so buyers know the person behind the product.
            </p>
        </div>
        <div style="padding:14px 16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;">2. Post a changelog update</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;">
                Even a short &ldquo;launch day&rdquo; post earns you the Active badge and
                boosts your ranking in search.
            </p>
        </div>
        <div style="padding:14px 16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;">3. Add &ldquo;replaces&rdquo; competitors</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;">
                Tag the big-name tools yours replaces. This powers our alternatives
                pages and drives organic search traffic to your listing.
            </p>
        </div>
    </div>
    <div style="margin:28px 0;padding:20px;background:#1A2D4A;border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 6px;">
            Discoverable by AI
        </p>
        <p style="color:rgba(255,255,255,0.7);font-size:13px;margin:0;line-height:1.5;">
            Your tool is now searchable by AI coding assistants via our MCP server.
            Developers using Cursor, Windsurf, and other AI editors can find {tool_name} automatically.
        </p>
    </div>
    <div style="text-align:center;margin-top:28px;">
        <a href="{dashboard_url}" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Go to Your Dashboard
        </a>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because you claimed
        <a href="{base}/tool/{tool_slug}" style="color:#00D4F5;">{tool_name}</a> on IndieStack.
    </p>
    """


# Subject: "Marketplace Opens Monday — Here's What's Coming"
def marketplace_preview_html(tools: list, launch_url: str = f"{BASE_URL}/launch", unsubscribe_url: str = "") -> str:
    """Pre-launch email showing featured tools that will be available for purchase."""
    tool_cards = ""
    for t in tools[:5]:
        name = t.get('name', '')
        tagline = t.get('tagline', '')
        slug = t.get('slug', '')
        maker = t.get('maker_name', '')
        price_pence = t.get('price_pence', 0)
        price_str = f"£{price_pence / 100:.0f}/mo" if price_pence else "Free"
        tool_cards += f"""
        <div style="padding:16px;background:#F5F3F0;border-radius:10px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
            <div style="flex:1;">
                <a href="{BASE_URL}/tool/{slug}" style="font-size:16px;font-weight:700;color:#1A2D4A;text-decoration:none;">{name}</a>
                <p style="color:#6B6560;font-size:13px;margin:4px 0 0;line-height:1.4;">{tagline}</p>
                <p style="color:#9C958E;font-size:12px;margin:4px 0 0;">by {maker}</p>
            </div>
            <div style="text-align:right;min-width:70px;">
                <span style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:13px;font-weight:700;padding:4px 10px;border-radius:6px;">{price_str}</span>
            </div>
        </div>
        """

    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Launching Monday
        </div>
    </div>
    <h2 style="font-family:serif;font-size:26px;color:#1A2D4A;margin-bottom:8px;text-align:center;">
        The Marketplace Opens March 2nd
    </h2>
    <p style="color:#6B6560;font-size:15px;line-height:1.6;text-align:center;margin-bottom:28px;">
        Indie developers will be able to sell their tools directly on IndieStack.
        Here are some of the tools you'll be able to buy on day one.
    </p>

    {tool_cards}

    <div style="margin:28px 0;padding:16px;background:#F0F7FA;border-radius:10px;border-left:4px solid #00D4F5;text-align:center;">
        <p style="color:#1A2D4A;font-size:14px;font-weight:600;margin:0;">
            Makers keep 95% of every sale. No middlemen.
        </p>
    </div>

    <div style="text-align:center;margin:28px 0;">
        <a href="{launch_url}" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            See What's Available &rarr;
        </a>
    </div>

    <div style="margin-top:28px;padding:20px;background:linear-gradient(135deg,#1A2D4A,#0D1B2A);border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 6px;">Are you a maker?</p>
        <p style="color:rgba(255,255,255,0.7);font-size:13px;margin:0 0 12px;line-height:1.5;">
            List your tool for free. Set a price, connect Stripe, and start earning on Monday.
        </p>
        <a href="{BASE_URL}/submit" style="color:#00D4F5;font-weight:600;font-size:14px;text-decoration:none;">
            Submit your creation &rarr;
        </a>
    </div>

    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because you subscribed to IndieStack updates.
        {'<br><a href="' + unsubscribe_url + '" style="color:#9C958E;">Unsubscribe</a>' if unsubscribe_url else ''}
    </p>
    """


# Subject: "The IndieStack Marketplace is Live"
def marketplace_launch_blast_html(explore_url: str, unsubscribe_url: str = "") -> str:
    """Subscriber email blast for marketplace launch day."""
    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Launch Day
        </div>
    </div>
    <h2 style="font-family:serif;font-size:28px;color:#1A2D4A;margin-bottom:8px;text-align:center;">
        The IndieStack Marketplace is Live
    </h2>
    <p style="color:#6B6560;font-size:15px;line-height:1.6;text-align:center;margin-bottom:28px;">
        Indie developers can now sell their tools directly on IndieStack. Browse curated tools
        from solo makers and small teams &mdash; buy direct, support indie.
    </p>
    <div style="margin:24px 0;">
        <div style="padding:16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;font-size:15px;">95% Revenue to Makers</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;line-height:1.5;">
                We take just 5% platform fee. Makers keep the rest.
            </p>
        </div>
        <div style="padding:16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;font-size:15px;">Direct Stripe Payouts</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;line-height:1.5;">
                Money goes straight to the maker's bank account.
            </p>
        </div>
        <div style="padding:16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;font-size:15px;">Curated &amp; Verified</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;line-height:1.5;">
                Every tool is reviewed. Verified and Ejectable badges you can trust.
            </p>
        </div>
    </div>
    <div style="text-align:center;margin:32px 0;">
        <a href="{explore_url}" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Browse the Marketplace &rarr;
        </a>
    </div>
    <p style="color:#6B6560;font-size:14px;text-align:center;line-height:1.6;">
        Are you a maker? List your tool for free at
        <a href="{BASE_URL}/submit" style="color:#00D4F5;font-weight:600;">indiestack.ai/submit</a>
    </p>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because you subscribed to IndieStack updates.
        {'<br><a href="' + unsubscribe_url + '" style="color:#9C958E;">Unsubscribe</a>' if unsubscribe_url else ''}
    </p>
    """


# Subject: "The IndieStack Marketplace is Live — Browse {tool_count} Indie Creations"
def launch_day_html(*, tool_count: int, maker_count: int, explore_url: str = f"{BASE_URL}/explore", unsubscribe_url: str = "") -> str:
    """Launch day email — sent to all subscribers on March 2, 2026."""
    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            It's Launch Day
        </div>
    </div>
    <h2 style="font-family:serif;font-size:28px;color:#1A2D4A;margin-bottom:8px;text-align:center;">
        The IndieStack Marketplace is Open
    </h2>
    <p style="color:#6B6560;font-size:15px;line-height:1.6;text-align:center;margin-bottom:28px;">
        Starting today, indie developers can sell their tools directly on IndieStack.
        Browse {tool_count} tools from {maker_count} makers &mdash; and buy direct from the builders.
    </p>

    <div style="margin:24px 0;">
        <div style="padding:16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;font-size:15px;">&#128269; Discover</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;line-height:1.5;">
                Browse {tool_count} indie creations across 25 categories. No affiliate rankings, no ads &mdash; just real tools from real makers.
            </p>
        </div>
        <div style="padding:16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;font-size:15px;">&#128176; Buy Direct</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;line-height:1.5;">
                Your payment goes straight to the maker. No middlemen. Makers keep 95% of every sale.
            </p>
        </div>
        <div style="padding:16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;font-size:15px;">&#129302; AI-Powered</strong>
            <p style="color:#6B6560;font-size:13px;margin:4px 0 0;line-height:1.5;">
                Every tool is searchable by AI coding assistants via our MCP server.
                Your AI can find the right indie tool before writing code from scratch.
            </p>
        </div>
    </div>

    <div style="text-align:center;margin:32px 0;">
        <a href="{explore_url}" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Browse the Marketplace &rarr;
        </a>
    </div>

    <div style="margin-top:28px;padding:20px;background:linear-gradient(135deg,#1A2D4A,#0D1B2A);border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 6px;">Are you a maker?</p>
        <p style="color:rgba(255,255,255,0.7);font-size:13px;margin:0 0 12px;line-height:1.5;">
            List your tool for free. Set a price, connect Stripe, and start earning today.
        </p>
        <a href="{BASE_URL}/submit" style="color:#00D4F5;font-weight:600;font-size:14px;text-decoration:none;">
            Submit your creation &rarr;
        </a>
    </div>

    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because you subscribed to IndieStack updates.
        {'<br><a href="' + unsubscribe_url + '" style="color:#9C958E;">Unsubscribe</a>' if unsubscribe_url else ''}
    </p>
    """


# Subject: "Connect Stripe Before March 2nd"
def maker_stripe_nudge_html(tool_name: str, dashboard_url: str) -> str:
    """Targeted email for makers who have priced tools but haven't connected Stripe."""
    tool_name = escape(tool_name)
    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Action Required
        </div>
    </div>
    <h2 style="font-family:serif;font-size:24px;color:#1A2D4A;margin-bottom:8px;text-align:center;">
        Connect Stripe Before March 2nd
    </h2>
    <p style="color:#6B6560;font-size:15px;line-height:1.6;text-align:center;margin-bottom:24px;">
        The IndieStack Marketplace launches March 2nd. Your tool <strong>{tool_name}</strong> is listed
        and ready &mdash; but you need to connect Stripe to start accepting payments.
    </p>
    <div style="margin:24px 0;padding:20px;background:#1A2D4A;border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:14px;font-weight:700;margin:0 0 6px;">
            You keep 95% of every sale
        </p>
        <p style="color:rgba(255,255,255,0.7);font-size:13px;margin:0;line-height:1.5;">
            We handle checkout, delivery, and receipts.
        </p>
    </div>
    <div style="margin:28px 0;">
        <p style="font-size:14px;font-weight:700;color:#1A2D4A;margin-bottom:16px;">
            How it works:
        </p>
        <div style="padding:14px 16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;">1. Click Connect Stripe</strong>
        </div>
        <div style="padding:14px 16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;">2. Enter your bank details on Stripe</strong>
        </div>
        <div style="padding:14px 16px;background:#F0F7FA;border-radius:10px;margin-bottom:10px;border-left:4px solid #00D4F5;">
            <strong style="color:#1A2D4A;">3. Your tool gets a Buy Now button</strong>
        </div>
    </div>
    <div style="text-align:center;margin:32px 0;">
        <a href="{dashboard_url}" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Connect Stripe Now &rarr;
        </a>
    </div>
    <div style="margin:24px 0;padding:16px;background:#FFF7ED;border-radius:10px;border-left:4px solid #F59E0B;text-align:center;">
        <p style="color:#92400E;font-size:14px;font-weight:600;margin:0;">
            Launch is March 2nd &mdash; connect now so you're ready on day one.
        </p>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You're receiving this because {tool_name} is listed on IndieStack.
    </p>
    """


def tool_of_the_week_html(maker_name: str, tool_name: str, tool_slug: str, clicks: int, badge_url: str, tool_url: str) -> str:
    """Congrats email for Tool of the Week winner with embeddable badge code."""
    maker_name = escape(maker_name)
    tool_name = escape(tool_name)
    html_embed = f'&lt;a href=&quot;{tool_url}&quot;&gt;&lt;img src=&quot;{badge_url}&quot; alt=&quot;IndieStack Tool of the Week&quot;&gt;&lt;/a&gt;'
    md_embed = f'[![IndieStack Tool of the Week]({badge_url})]({tool_url})'
    return _email_wrapper(f"""
    <div style="text-align:center;margin-bottom:24px;">
        <span style="font-size:40px;">&#127942;</span>
    </div>
    <h1 style="font-family:serif;font-size:26px;color:#1A2D4A;text-align:center;margin-bottom:8px;">
        Tool of the Week
    </h1>
    <p style="text-align:center;color:#6B7280;font-size:15px;margin-bottom:24px;">
        Congrats {maker_name} &mdash; <strong>{tool_name}</strong> is IndieStack's Tool of the Week!
    </p>
    <div style="background:#FFFBEB;border:2px solid #E2B764;border-radius:12px;padding:20px;text-align:center;margin-bottom:24px;">
        <p style="color:#92400E;font-size:14px;margin:0 0 4px;font-weight:600;">{clicks} developers clicked through to {tool_name} this week</p>
        <p style="color:#92400E;font-size:13px;margin:0;">That&rsquo;s more than any other tool on IndieStack.</p>
    </div>
    <div style="text-align:center;margin-bottom:24px;">
        <img src="{badge_url}" alt="Tool of the Week badge" style="height:20px;">
    </div>
    <p style="font-size:15px;color:#1A2D4A;font-weight:600;margin-bottom:12px;">
        Show it off &mdash; embed this badge on your site or README:
    </p>
    <div style="margin-bottom:16px;">
        <p style="font-size:12px;font-weight:600;color:#6B7280;margin:0 0 4px;">HTML</p>
        <div style="background:#1A1A2E;color:#00D4F5;padding:10px 14px;border-radius:8px;font-family:monospace;font-size:12px;word-break:break-all;">
            {html_embed}
        </div>
    </div>
    <div style="margin-bottom:24px;">
        <p style="font-size:12px;font-weight:600;color:#6B7280;margin:0 0 4px;">Markdown</p>
        <div style="background:#1A1A2E;color:#00D4F5;padding:10px 14px;border-radius:8px;font-family:monospace;font-size:12px;word-break:break-all;">
            {md_embed}
        </div>
    </div>
    <p style="font-size:14px;color:#6B7280;margin-bottom:20px;">
        Every badge embed links back to your tool page on IndieStack &mdash; free traffic from your own audience.
    </p>
    <div style="text-align:center;">
        <a href="{tool_url}" style="display:inline-block;background:#1A2D4A;color:#fff;padding:14px 32px;border-radius:999px;font-size:15px;font-weight:600;text-decoration:none;">
            View your tool &rarr;
        </a>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:24px;">
        You&rsquo;re receiving this because {tool_name} is listed on IndieStack.
    </p>
    """, preview_text=f"Congrats! {tool_name} is IndieStack's Tool of the Week")


def welcome_signup_html() -> str:
    """Welcome email sent to new users on account creation."""
    from datetime import date
    marketplace_live = date.today() >= date(2026, 3, 2)
    if marketplace_live:
        marketplace_text = "The marketplace is live &mdash; browse and buy direct from indie makers."
    else:
        marketplace_text = "The marketplace opens March 2 &mdash; be ready to browse and buy direct from indie makers."

    return _email_wrapper(f"""
    <h2 style="font-family:serif;font-size:26px;color:#1A2D4A;margin-bottom:8px;text-align:center;">
        Welcome to IndieStack
    </h2>
    <p style="color:#6B6560;font-size:15px;line-height:1.6;">
        You&rsquo;ve joined a community of indie SaaS builders and buyers.
        IndieStack is where solo developers and small teams list, discover,
        and sell the tools they&rsquo;ve built.
    </p>

    <div style="margin:24px 0;padding:20px;background:#F0FDFD;border-radius:12px;border-left:4px solid #00D4F5;">
        <p style="margin:0 0 6px;font-weight:700;color:#1A2D4A;font-size:15px;">
            &#127881; Free Perplexity Comet access
        </p>
        <p style="margin:0;color:#6B6560;font-size:14px;line-height:1.5;">
            As a thank you for signing up, get free access to Perplexity Comet &mdash;
            <a href="https://pplx.ai/patrick-amey" style="color:#C4714E;font-weight:600;">claim it here</a>.
        </p>
    </div>

    <div style="margin:24px 0;padding:20px;background:#FAF7F2;border-radius:12px;">
        <p style="margin:0 0 6px;font-weight:700;color:#1A2D4A;font-size:15px;">
            &#128640; Referral programme
        </p>
        <p style="margin:0;color:#6B6560;font-size:14px;line-height:1.5;">
            Share IndieStack and earn boost days for your tools.
            Find your referral link on your dashboard.
        </p>
    </div>

    <p style="color:#6B6560;font-size:15px;line-height:1.6;">
        {marketplace_text}
    </p>

    <div style="margin:28px 0 12px;text-align:center;">
        <a href="{BASE_URL}/dashboard" style="display:inline-block;background:#1A2D4A;color:#fff;
           padding:14px 32px;border-radius:999px;font-weight:600;text-decoration:none;font-size:15px;">
            Go to your dashboard &rarr;
        </a>
    </div>
    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:20px;">
        You&rsquo;re receiving this because you just created an IndieStack account.
    </p>
    """, preview_text="Welcome to IndieStack — you've joined the indie SaaS community")


def badge_nudge_html(tool_name, tool_slug):
    """Email sent 48h after tool approval nudging maker to embed their badge."""
    tool_name = escape(tool_name)
    badge_url = f"{BASE_URL}/api/badge/{tool_slug}.svg"
    tool_url = f"{BASE_URL}/tool/{tool_slug}"

    html_snippet = f'&lt;a href=&quot;{tool_url}&quot;&gt;&lt;img src=&quot;{badge_url}&quot; alt=&quot;{tool_name} on IndieStack&quot;&gt;&lt;/a&gt;'
    md_snippet = f'[![{tool_name} on IndieStack]({badge_url})]({tool_url})'

    content = f"""
    <div style="text-align:center;padding:32px 0 24px;">
        <h1 style="font-size:24px;color:#1A2D4A;margin-bottom:8px;">Your badge is ready</h1>
        <p style="color:#666;font-size:15px;">Add it to your site or README — get discovered by AI coding assistants.</p>
    </div>

    <div style="text-align:center;padding:24px;background:#f8f8f8;border-radius:8px;margin-bottom:24px;">
        <img src="{badge_url}" alt="{tool_name} on IndieStack" style="margin-bottom:16px;">
        <p style="font-size:13px;color:#999;margin:0;">{tool_name} on IndieStack</p>
    </div>

    <div style="background:#1A2D4A;border-radius:8px;padding:20px 24px;margin-bottom:24px;">
        <p style="color:white;font-size:14px;font-weight:600;margin-bottom:12px;">HTML (for your website)</p>
        <div style="background:#0D1B2A;border-radius:4px;padding:12px;font-family:monospace;font-size:12px;color:#00D4F5;word-break:break-all;">
            {html_snippet}
        </div>
    </div>

    <div style="background:#1A2D4A;border-radius:8px;padding:20px 24px;margin-bottom:24px;">
        <p style="color:white;font-size:14px;font-weight:600;margin-bottom:12px;">Markdown (for your README)</p>
        <div style="background:#0D1B2A;border-radius:4px;padding:12px;font-family:monospace;font-size:12px;color:#00D4F5;word-break:break-all;">
            {md_snippet}
        </div>
    </div>

    <div style="background:#f0fafe;border:1px solid #00D4F5;border-radius:8px;padding:16px;margin-bottom:24px;">
        <p style="font-size:14px;color:#1A2D4A;margin:0;line-height:1.6;">
            <strong>Why add a badge?</strong> Every IndieStack badge is a backlink that helps your tool get discovered.
            Plus, your tool is now searchable by AI coding assistants (Cursor, Windsurf, Claude Code)
            through our MCP server.
        </p>
    </div>

    <div style="text-align:center;padding:16px 0;">
        <a href="{tool_url}" style="display:inline-block;background:#1A2D4A;color:white;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:600;font-size:15px;">
            View your listing &rarr;
        </a>
    </div>
    """
    return _email_wrapper(content)


def maker_launch_countdown_html(maker_name: str, maker_slug: str, tool_count: int) -> str:
    """Countdown email sent to claimed makers 3 days before marketplace launch."""
    maker_name = escape(maker_name)
    stripe_url = f"{BASE_URL}/stripe-guide"
    launch_url = f"{BASE_URL}/launch/{maker_slug}"
    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            The Marketplace Opens Monday &#9200;
        </div>
    </div>

    <p style="color:#2D2926;font-size:15px;line-height:1.6;">
        Hey {maker_name},
    </p>

    <p style="color:#6B6560;font-size:15px;line-height:1.6;">
        In 3 days, your {'tool becomes' if tool_count == 1 else str(tool_count) + ' tools become'} purchasable on IndieStack.
        Buyers will be able to pay you directly &mdash; all you need to do is connect Stripe.
    </p>

    <div style="margin:24px 0;padding:20px;background:#F0F7FA;border-radius:12px;border-left:4px solid #00D4F5;">
        <strong style="color:#1A2D4A;font-size:15px;">3 steps. 2 minutes.</strong>
        <ol style="color:#6B6560;font-size:14px;line-height:1.8;margin:8px 0 0;padding-left:20px;">
            <li>Go to your dashboard</li>
            <li>Click &ldquo;Connect Stripe&rdquo;</li>
            <li>Follow the Stripe onboarding flow</li>
        </ol>
    </div>

    <div style="text-align:center;margin:28px 0;">
        <a href="{stripe_url}" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Connect Stripe Now &rarr;
        </a>
    </div>

    <div style="margin:24px 0;padding:20px;background:linear-gradient(135deg,#1A2D4A,#0D1B2A);border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:20px;font-weight:700;margin:0 0 8px;">358 tools. 108 makers.</p>
        <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.6;margin:0;">
            Your tools will be recommended by AI agents.
        </p>
    </div>

    <div style="margin:24px 0;padding:16px;background:#F0F7FA;border-radius:10px;border-left:4px solid #00D4F5;">
        <strong style="color:#1A2D4A;font-size:14px;">&#129302; NEW: AI agents now recommend IndieStack tools</strong>
        <p style="color:#6B6560;font-size:13px;margin:6px 0 0;line-height:1.5;">
            AI coding assistants (Cursor, Windsurf, Claude Code) now recommend IndieStack tools via our MCP server.
            Your tool was already discoverable by agents &mdash; now they can recommend it to buyers too.
        </p>
    </div>

    <div style="margin:24px 0;padding:16px;background:#FFF7ED;border-radius:10px;border-left:4px solid #E2B764;">
        <strong style="color:#1A2D4A;font-size:14px;">&#128640; Your co-marketing launch page is ready</strong>
        <p style="color:#6B6560;font-size:13px;margin:6px 0 0;line-height:1.5;">
            Share your launch page on Twitter and Reddit to drive traffic on day 1.
            It has your tools, your bio, and share buttons built in.
        </p>
    </div>

    <div style="text-align:center;margin:28px 0;">
        <a href="{launch_url}" style="display:inline-block;background:#1A2D4A;color:white;
           padding:12px 28px;border-radius:8px;font-weight:700;font-size:15px;text-decoration:none;">
            Your Launch Page &rarr;
        </a>
    </div>

    <p style="color:#9C958E;font-size:12px;text-align:center;margin-top:28px;">
        Questions? Just reply to this email &mdash; we read every one.
    </p>
    """


def launch_morning_maker_html(maker_name: str, tool_name: str) -> str:
    """Launch-day email to claimed makers — review your listing before PH launch."""
    maker_name = escape(maker_name)
    tool_name = escape(tool_name)
    dashboard_url = f"{BASE_URL}/dashboard"
    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#2D2926;color:white;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            Launching Today
        </div>
    </div>

    <h2 style="font-family:serif;font-size:24px;color:#2D2926;margin-bottom:16px;text-align:center;">
        Your Tool Goes in Front of Product Hunt Today
    </h2>

    <p style="color:#2D2926;font-size:15px;line-height:1.6;">
        Hi {maker_name},
    </p>

    <p style="color:#6B6560;font-size:15px;line-height:1.6;">
        IndieStack is launching on Product Hunt today.
        <strong style="color:#2D2926;">{tool_name}</strong> will be in front of
        thousands of developers <em>and</em> the AI agents they build with.
    </p>

    <p style="color:#6B6560;font-size:15px;line-height:1.6;">
        IndieStack is becoming the open-source supply chain where AI agents learn what tools exist.
        We&rsquo;ve already seen <strong style="color:#2D2926;">2,000+ agent lookups</strong>
        across 480 tools &mdash; and that number is growing fast.
    </p>

    <div style="margin:24px 0;padding:20px;background:#FAF7F2;border-radius:12px;border-left:4px solid #C4714E;">
        <strong style="color:#2D2926;font-size:15px;">Quick pre-launch checklist:</strong>
        <ul style="color:#6B6560;font-size:14px;margin:10px 0 0;padding-left:20px;line-height:1.8;">
            <li>Is your <strong style="color:#2D2926;">description</strong> clear and up to date?</li>
            <li>Are your <strong style="color:#2D2926;">tags</strong> accurate?</li>
            <li>Posted a <strong style="color:#2D2926;">changelog</strong> recently?</li>
        </ul>
    </div>

    <div style="text-align:center;margin:32px 0;">
        <a href="{dashboard_url}" style="display:inline-block;background:#C4714E;color:white;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Review Your Listing &rarr;
        </a>
    </div>

    <p style="color:#6B6560;font-size:14px;line-height:1.6;text-align:center;">
        See you on launch day,<br>
        <strong style="color:#2D2926;">Patrick &amp; Ed</strong>
    </p>
    """


def ph_launch_announcement_html(ph_url: str, tool_count: int = 828) -> str:
    """Product Hunt launch day announcement — sent to all users and subscribers."""
    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            We're Live on Product Hunt
        </div>
    </div>

    <h2 style="font-family:serif;font-size:26px;color:#1A2D4A;margin-bottom:12px;text-align:center;">
        IndieStack just launched on Product Hunt
    </h2>

    <p style="color:#5A5550;font-size:15px;line-height:1.7;margin-bottom:16px;">
        Hey! Big day for us &mdash; IndieStack is live on Product Hunt today.
        {tool_count} indie creations, searchable by AI agents, browsable by everyone.
    </p>

    <p style="color:#5A5550;font-size:15px;line-height:1.7;margin-bottom:20px;">
        We also just shipped <strong style="color:#1A2D4A;">MCP Server v1.1</strong> &mdash;
        AI agents can now discover games, newsletters, creative tools, and learning apps alongside dev tools.
        The catalog goes way beyond code now.
    </p>

    <div style="text-align:center;margin:28px 0;">
        <a href="{escape(ph_url)}" style="display:inline-block;background:#FF6154;color:white;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            See us on Product Hunt &rarr;
        </a>
    </div>

    <p style="color:#5A5550;font-size:14px;line-height:1.6;margin-bottom:16px;">
        If IndieStack has been useful to you, an upvote or comment on PH would mean the world.
        We're two uni students in Cardiff building this &mdash; every bit of support matters.
    </p>

    <div style="margin:20px 0;padding:16px;background:#F0F7FA;border-radius:10px;border-left:4px solid #00D4F5;">
        <strong style="color:#1A2D4A;font-size:14px;">What's new in v1.1:</strong>
        <ul style="color:#6B6560;font-size:13px;margin:8px 0 0;padding-left:18px;line-height:1.8;">
            <li>Broader catalog &mdash; games, newsletters, creative tools, education</li>
            <li>Smarter agent discovery &mdash; finds creations across all categories</li>
            <li>AI Pulse &mdash; live feed of agent activity at <a href="{BASE_URL}/pulse" style="color:#00D4F5;">indiestack.ai/pulse</a></li>
        </ul>
    </div>

    <p style="color:#6B6560;font-size:14px;line-height:1.6;text-align:center;margin-top:24px;">
        Thank you for being here early,<br>
        <strong style="color:#1A2D4A;">Patrick &amp; Ed</strong>
    </p>
    """


def reengagement_march_html(*, user_name: str, has_tools: bool) -> str:
    """March 2026 re-engagement email — highlight growth from 300 to 3,099 tools + free Pro trial."""
    user_name = escape(user_name)

    maker_section = ""
    if has_tools:
        maker_section = f"""
    <div style="margin:24px 0;padding:20px;background:#F0F7FA;border-left:4px solid #00D4F5;border-radius:8px;">
        <p style="font-size:14px;font-weight:700;color:#1A2D4A;margin:0 0 4px;">For makers</p>
        <p style="font-size:13px;color:#1A2D4A;line-height:1.6;margin:0;">
            AI agents are now recommending tools from IndieStack. Your Pro trial includes
            <strong>AI citation tracking</strong> &mdash; see which agents recommend your tools, how often, and to whom.
        </p>
    </div>"""

    return f"""
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#1A2D4A;color:#00D4F5;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.5px;padding:6px 14px;border-radius:999px;">
            What's New
        </div>
    </div>
    <h2 style="font-family:serif;font-size:22px;color:#1A2D4A;margin-bottom:4px;text-align:center;">
        IndieStack just hit 3,099 tools
    </h2>
    <p style="color:#6B6560;font-size:15px;text-align:center;margin-bottom:24px;">
        Hi {user_name} &mdash; a lot has changed since you signed up. Here's what's new.
    </p>

    <div style="margin:24px 0;">
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
            <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
                <div style="font-size:28px;font-weight:bold;color:#00D4F5;">3,099</div>
                <div style="font-size:12px;color:#6B6560;margin-top:4px;">Tools Indexed</div>
            </div>
            <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
                <div style="font-size:28px;font-weight:bold;color:#00D4F5;">25</div>
                <div style="font-size:12px;color:#6B6560;margin-top:4px;">Categories</div>
            </div>
            <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
                <div style="font-size:28px;font-weight:bold;color:#1A2D4A;">5,031</div>
                <div style="font-size:12px;color:#6B6560;margin-top:4px;">Compatibility Pairs</div>
            </div>
            <div style="text-align:center;padding:16px 8px;background:#F0F7FA;border-radius:12px;">
                <div style="font-size:28px;font-weight:bold;color:#1A2D4A;">30K+</div>
                <div style="font-size:12px;color:#6B6560;margin-top:4px;">Tool Clicks</div>
            </div>
        </div>
    </div>

    <h3 style="font-size:16px;color:#1A2D4A;margin:28px 0 12px;">New since you joined</h3>
    <ul style="color:#6B6560;font-size:14px;line-height:2;padding-left:20px;margin:0;">
        <li><strong style="color:#1A2D4A;">MCP Server</strong> &mdash; Claude, Cursor, and Windsurf can search IndieStack directly while you code</li>
        <li><strong style="color:#1A2D4A;">Stack Auditor</strong> &mdash; paste your package.json to find indie replacements for your dependencies</li>
        <li><strong style="color:#1A2D4A;">Compatibility Pairs</strong> &mdash; see which tools work well together, verified by AI agents</li>
        <li><strong style="color:#1A2D4A;">Health Monitoring</strong> &mdash; every tool shows maintenance status (Active, Stale, Archived)</li>
        <li><strong style="color:#1A2D4A;">AI Citation Tracking</strong> &mdash; see which AI agents recommend which tools</li>
        <li><strong style="color:#1A2D4A;">Market Gap Detection</strong> &mdash; discover what developers are searching for but can't find</li>
    </ul>

    {maker_section}

    <div style="margin:28px 0;padding:24px;background:#1A2D4A;border-radius:12px;text-align:center;">
        <p style="color:#00D4F5;font-size:16px;font-weight:700;margin:0 0 4px;">
            You have a 7-day free Pro trial waiting
        </p>
        <p style="color:rgba(255,255,255,0.6);font-size:13px;margin:0 0 16px;">
            Full access to citation tracking, market gaps, data export, and 1,000 API queries/month.
        </p>
        <a href="{BASE_URL}/dashboard" style="display:inline-block;background:#00D4F5;color:#1A2D4A;
           padding:14px 32px;border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;">
            Explore Your Dashboard
        </a>
    </div>

    <div style="margin:24px 0;padding:20px;border:1px solid #E2B764;border-radius:12px;text-align:center;background:linear-gradient(135deg,#FEF9EF,#FFF7E6);">
        <p style="font-size:14px;font-weight:700;color:#1A2D4A;margin:0 0 4px;">Founding Member &mdash; $99 lifetime deal</p>
        <p style="font-size:13px;color:#6B6560;margin:0 0 12px;line-height:1.5;">
            Pay once, keep Pro forever. Only 50 seats available &mdash; once they're gone, it's $19/month.
        </p>
        <a href="{BASE_URL}/pricing" style="display:inline-block;background:#E2B764;color:#1A2D4A;
           padding:10px 24px;border-radius:8px;font-weight:700;font-size:14px;text-decoration:none;">
            Claim Your Seat
        </a>
    </div>

    <p style="color:#6B6560;font-size:14px;line-height:1.6;text-align:center;margin-top:24px;">
        Thanks for being part of this,<br>
        <strong style="color:#1A2D4A;">Patrick &amp; Ed</strong>
    </p>
    """
