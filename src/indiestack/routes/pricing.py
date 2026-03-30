"""Pricing page — everything free for developers, data products for tool makers."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell

router = APIRouter()


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
        free_cta = '<a href="/signup" class="btn-primary" style="display:block;text-align:center;padding:12px;text-decoration:none;">Create Free Account</a>'

    body = f"""
<style>
.pricing-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:24px; max-width:880px; margin:0 auto; }}
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
      Free for developers. Data for tool makers.
    </h1>
    <p style="font-size:var(--text-md);color:var(--ink-muted);margin:0;max-width:550px;margin-left:auto;margin-right:auto;line-height:1.6;">
      Every search, every analysis, every MCP query is free and unlimited.
      We make money by selling the intelligence this data creates.
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
        {_feature_row("GitHub Action — auto-check PRs")}
        {_feature_row("Personalized recommendations")}
        {_feature_row("Data export")}
      </ul>
      {free_cta}
    </div>

    <!-- Tool Makers -->
    <div class="pricing-card">
      <h2>Tool Makers</h2>
      <div class="price">$299<span> / month</span></div>
      <div class="desc">Competitive intelligence from real migration data.</div>
      <ul>
        {_feature_row("See who's migrating FROM your competitors")}
        {_feature_row("See who's migrating TO you")}
        {_feature_row("Verified production combos for your tool")}
        {_feature_row("CI outcome data — what actually works")}
        {_feature_row("Weekly competitive reports")}
        {_feature_row("Repo-level migration detail")}
        {_feature_row("CSV data exports")}
      </ul>
      <a href="mailto:patrick@indiestack.ai?subject=Migration%20Intelligence" class="btn-primary" style="display:block;text-align:center;padding:12px;text-decoration:none;">
        Contact Us
      </a>
    </div>

    <!-- Enterprise -->
    <div class="pricing-card">
      <h2>Enterprise</h2>
      <div class="price">Custom</div>
      <div class="desc">Raw data licensing for VCs and market intelligence.</div>
      <ul>
        {_feature_row("Everything in Tool Makers")}
        {_feature_row("Raw data licensing")}
        {_feature_row("Custom repo scanning targets")}
        {_feature_row("CI outcome data feed")}
        {_feature_row("Dedicated support")}
        {_feature_row("Custom integrations")}
      </ul>
      <a href="mailto:patrick@indiestack.ai?subject=Enterprise%20Data%20Licensing" class="btn-secondary" style="display:block;text-align:center;padding:12px;text-decoration:none;">
        Let's Talk
      </a>
    </div>

  </div>

  <!-- Try it CTA -->
  <div style="max-width:600px;margin:48px auto 0;text-align:center;padding:32px 24px;background:var(--cream-dark);border-radius:var(--radius-lg);">
    <h2 style="font-family:var(--font-display);font-size:var(--heading-sm);color:var(--ink);margin:0 0 8px;">
      See the data in action
    </h2>
    <p style="color:var(--ink-muted);font-size:var(--text-sm);margin:0 0 16px;">
      Paste a package.json and get instant migration intelligence, health scores, and compatibility data.
    </p>
    <a href="/analyze" class="btn-primary" style="padding:12px 32px;text-decoration:none;">
      Analyze Your Stack
    </a>
  </div>

</div>
"""

    return HTMLResponse(page_shell(
        "Pricing — IndieStack",
        body,
        description="Free for developers. Unlimited searches, analyses, and MCP queries. Data products for tool makers starting at $299/mo.",
        user=user,
    ))
