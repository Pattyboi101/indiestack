"""Pricing page — free for developers, makers pay for visibility and analytics."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/claim")
async def claim_redirect(request: Request):
    """Redirect /claim to explore so makers can search for and claim their tool."""
    user = request.state.user
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/signup?next=/dashboard", status_code=302)


def _check_icon() -> str:
    return (
        '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="flex-shrink:0;margin-top:2px">'
        '<path d="M3 8.5L6.5 12L13 4" style="stroke:var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )


def _feature_row(text: str) -> str:
    return f'<li style="display:flex;gap:10px;align-items:flex-start;font-size:var(--text-base);color:var(--ink);line-height:1.5">{_check_icon()} <span>{text}</span></li>'


@router.get("/pricing")
async def pricing_page(request: Request):
    user = request.state.user

    if user:
        free_cta = '<a href="/dashboard" class="btn-secondary" style="display:block;text-align:center;padding:12px;text-decoration:none;">Go to Dashboard</a>'
    else:
        free_cta = '<a href="/signup" class="btn-primary" style="display:block;text-align:center;padding:12px;text-decoration:none;">Get Started Free</a>'

    body = f"""
<style>
.pricing-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:24px; max-width:700px; margin:0 auto; }}
.pricing-card {{ background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius-lg); padding:32px; }}
.pricing-card.highlight {{ border:2px solid var(--slate); position:relative; }}
.pricing-card h2 {{ font-family:var(--font-display); font-size:20px; margin:0 0 8px; color:var(--ink); }}
.pricing-card .price {{ font-family:var(--font-display); font-size:var(--heading-md); color:var(--ink); margin-bottom:4px; }}
.pricing-card .price span {{ font-size:var(--text-sm); color:var(--ink-muted); font-family:var(--font-body); }}
.pricing-card .desc {{ font-size:var(--text-sm); color:var(--ink-muted); margin-bottom:20px; }}
.pricing-card ul {{ list-style:none; padding:0; margin:0 0 24px; }}
.pricing-card li {{ display:flex; gap:10px; align-items:flex-start; font-size:var(--text-sm); color:var(--ink); line-height:1.5; margin-bottom:8px; }}
</style>

<div style="max-width:900px;margin:0 auto;padding:0 24px 64px;">

  <div style="text-align:center;padding:48px 0 40px;">
    <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 12px;">
      Free for developers. Visibility for makers.
    </h1>
    <p style="font-size:var(--text-md);color:var(--ink-muted);margin:0;max-width:550px;margin-left:auto;margin-right:auto;line-height:1.6;">
      Search, analyse, and discover tools with no limits.
      Tool makers pay for analytics on how AI agents recommend their tools.
    </p>
  </div>

  <div class="pricing-grid">

    <!-- Developers -->
    <div class="pricing-card highlight">
      <div style="position:absolute;top:-12px;right:20px;background:var(--slate);color:white;font-size:11px;font-weight:600;padding:4px 12px;border-radius:12px;">FREE FOREVER</div>
      <h2>Developers</h2>
      <div class="price">Free</div>
      <div class="desc">Everything. No limits. No credit card.</div>
      <ul>
        {_feature_row("Unlimited MCP searches")}
        {_feature_row("Unlimited API queries")}
        {_feature_row("Stack health analysis")}
        {_feature_row("Migration intelligence")}
        {_feature_row("Verified package combinations")}
        {_feature_row("Personalised recommendations")}
      </ul>
      {free_cta}
    </div>

    <!-- Tool Makers -->
    <div class="pricing-card">
      <h2>Tool Makers</h2>
      <div class="price">$19<span> / month</span></div>
      <div class="desc">See how AI agents recommend your tool.</div>
      <ul>
        {_feature_row("Claim and manage your listing")}
        {_feature_row("Agent citation analytics — how often agents recommend you")}
        {_feature_row("Search query data — what developers ask for in your category")}
        {_feature_row("Verified badge on your listing")}
        {_feature_row("Competitor comparison — how you rank vs alternatives")}
        {_feature_row("Priority placement in search results")}
      </ul>
      <a href="/claim" class="btn-primary" style="display:block;text-align:center;padding:12px;text-decoration:none;">
        Claim Your Tool
      </a>
      <p style="font-size:12px;color:var(--ink-muted);text-align:center;margin:8px 0 0;">
        Claiming is free. Pro analytics is $19/mo.
      </p>
    </div>

  </div>

  <!-- Try it CTA -->
  <div style="max-width:600px;margin:48px auto 0;text-align:center;padding:32px 24px;background:var(--cream-dark);border-radius:var(--radius-lg);">
    <h2 style="font-family:var(--font-display);font-size:var(--heading-sm);color:var(--ink);margin:0 0 8px;">
      Try it now
    </h2>
    <p style="color:var(--ink-muted);font-size:var(--text-sm);margin:0 0 16px;">
      One command. Your AI agent searches 8,000+ developer tools before writing code from scratch.
    </p>
    <pre style="background:var(--terracotta);color:var(--slate);padding:14px;border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-mono);margin:0 0 16px;text-align:left;overflow-x:auto;">claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</pre>
    <a href="/analyze" class="btn-secondary" style="padding:10px 24px;text-decoration:none;font-size:14px;">
      Or analyse your stack
    </a>
  </div>

</div>
"""

    return HTMLResponse(page_shell(
        "Pricing — IndieStack",
        body,
        description="Free for developers — unlimited searches, MCP queries, and stack analysis. Tool makers get AI agent analytics starting at $19/mo.",
        user=user,
    ))
