"""Oracle API landing page — explains x402 pay-per-call endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from indiestack.routes.components import page_shell
from indiestack.config import BASE_URL

router = APIRouter()


@router.get("/oracle", response_class=HTMLResponse)
async def oracle_page(request: Request):
    """Human-readable landing page for the x402 Oracle API."""
    content = f"""
    <div style="max-width:720px;margin:0 auto;padding:40px 20px;">
      <h1 style="font-family:var(--font-heading);font-size:2rem;margin-bottom:8px;">
        Oracle API
      </h1>
      <p style="color:var(--text-muted);font-size:1.1rem;margin-bottom:32px;">
        Pay-per-call compatibility and migration intelligence for developer tools.
        No API key. No account. Just USDC on Base via the
        <a href="https://www.x402.org/" target="_blank" rel="noopener" style="color:var(--accent);">x402 protocol</a>.
      </p>

      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:40px;">
        <div style="flex:1;min-width:260px;background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;">
          <div style="font-family:var(--font-mono);font-size:0.85rem;color:var(--accent);margin-bottom:8px;">$0.02 / call</div>
          <h3 style="margin:0 0 8px;">Compatibility Check</h3>
          <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:16px;">
            Are two tools compatible? Verified data from 6,622 pairs and 58,638 manifest co-occurrences from real repos.
          </p>
          <code style="display:block;background:var(--bg);padding:12px;border-radius:8px;font-size:0.8rem;overflow-x:auto;white-space:nowrap;">
            GET /v1/compatibility/nextjs/supabase
          </code>
        </div>
        <div style="flex:1;min-width:260px;background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;">
          <div style="font-family:var(--font-mono);font-size:0.85rem;color:var(--accent);margin-bottom:8px;">$0.05 / call</div>
          <h3 style="margin:0 0 8px;">Migration Data</h3>
          <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:16px;">
            How many repos switched between two packages, when, and with what confidence. 422 migration paths from real git history.
          </p>
          <code style="display:block;background:var(--bg);padding:12px;border-radius:8px;font-size:0.8rem;overflow-x:auto;white-space:nowrap;">
            GET /v1/migration/jest/vitest
          </code>
        </div>
      </div>

      <h2 style="font-family:var(--font-heading);font-size:1.4rem;margin-bottom:16px;">How it works</h2>
      <ol style="color:var(--text-muted);line-height:1.8;padding-left:20px;margin-bottom:32px;">
        <li>Agent sends a GET request to an oracle endpoint</li>
        <li>Server responds with <strong>HTTP 402</strong> and a payment requirement (amount, wallet, network)</li>
        <li>Agent signs a USDC payment on Base and resends with the payment header</li>
        <li>Server verifies payment and returns the data</li>
      </ol>

      <h2 style="font-family:var(--font-heading);font-size:1.4rem;margin-bottom:16px;">Try it</h2>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:32px;">
        <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:12px;">
          Hit an endpoint to see the 402 payment challenge:
        </p>
        <pre style="margin:0;font-size:0.8rem;overflow-x:auto;"><code>curl -v {BASE_URL}/v1/compatibility/nextjs/supabase</code></pre>
      </div>

      <h2 style="font-family:var(--font-heading);font-size:1.4rem;margin-bottom:16px;">Discovery</h2>
      <p style="color:var(--text-muted);margin-bottom:16px;">
        x402-capable agents can discover these endpoints programmatically:
      </p>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:32px;">
        <pre style="margin:0;font-size:0.8rem;overflow-x:auto;"><code>curl {BASE_URL}/.well-known/x402-resources</code></pre>
      </div>

      <h2 style="font-family:var(--font-heading);font-size:1.4rem;margin-bottom:16px;">Example response</h2>
      <p style="color:var(--text-muted);margin-bottom:12px;">
        After payment, a compatibility check returns:
      </p>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:32px;">
        <pre style="margin:0;font-size:0.8rem;overflow-x:auto;"><code>{{"tool_a": "nextjs",
 "tool_b": "supabase",
 "compatible": true,
 "confidence": "verified",
 "success_count": 47,
 "cooccurrence_count": 312,
 "related_tools": ["prisma", "lucia-auth"]}}</code></pre>
      </div>

      <div style="text-align:center;padding:24px 0;border-top:1px solid var(--border);color:var(--text-muted);font-size:0.85rem;">
        Powered by <a href="https://www.x402.org/" target="_blank" rel="noopener" style="color:var(--accent);">x402</a>
        &middot; Payments on <a href="https://base.org/" target="_blank" rel="noopener" style="color:var(--accent);">Base</a>
        &middot; <a href="{BASE_URL}/.well-known/x402-resources" style="color:var(--accent);">API metadata</a>
      </div>
    </div>
    """
    return HTMLResponse(page_shell(request, "Oracle API — IndieStack", content))
