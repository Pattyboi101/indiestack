"""Submission guidelines — sets expectations before /submit."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/guidelines", response_class=HTMLResponse)
async def guidelines(request: Request):
    body = """
    <div style="max-width:680px;margin:0 auto;padding:32px 16px;">
        <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);margin-bottom:8px;">
            Submission Guidelines
        </h1>
        <p style="color:var(--ink-muted);font-size:16px;margin-bottom:32px;">
            IndieStack is a curated directory. AI agents rely on our curation signal to make
            reliable recommendations. These guidelines help us maintain that trust.
        </p>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            Scope: developer tools only
        </h2>
        <p style="color:var(--ink);font-size:15px;line-height:1.7;margin-bottom:16px;">
            IndieStack is for <strong>developer tools</strong> — software that helps developers and small teams build, ship, and run products.
            This includes: auth libraries, payment SDKs, databases, APIs, analytics, monitoring, CI/CD, email infrastructure, self-hosted services, CLI tools, and developer SaaS.
        </p>
        <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;margin-bottom:24px;padding:12px 16px;background:var(--cream-dark);border-radius:8px;border-left:3px solid var(--terracotta);">
            <strong>Out of scope:</strong> consumer apps (fitness trackers, recipe apps, social networks, weather apps, games), personal finance tools, crypto wallets, and non-developer productivity apps.
            If your tool&rsquo;s primary audience is end-users, not developers, it&rsquo;s likely not a fit.
        </p>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            What belongs on IndieStack
        </h2>
        <ul style="color:var(--ink);font-size:15px;line-height:1.8;margin-bottom:24px;padding-left:20px;">
            <li><strong>Independently built software</strong> &mdash; solo founders, small teams, bootstrapped projects</li>
            <li><strong>Actively maintained</strong> &mdash; your tool should work when someone tries it</li>
            <li><strong>Genuinely useful</strong> &mdash; solves a real problem for real developers</li>
        </ul>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            What we look for
        </h2>
        <ul style="color:var(--ink);font-size:15px;line-height:1.8;margin-bottom:24px;padding-left:20px;">
            <li><strong>Custom domain</strong> &mdash; not *.vercel.app or *.netlify.app</li>
            <li><strong>Working product</strong> &mdash; not a landing page or waitlist</li>
            <li><strong>Documentation</strong> that an AI agent can parse &mdash; structured docs, API reference, or a solid README</li>
            <li><strong>For SaaS:</strong> a free tier, trial, or sandbox so AI agents can verify your tool works</li>
        </ul>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            What gets rejected
        </h2>
        <ul style="color:var(--ink);font-size:15px;line-height:1.8;margin-bottom:24px;padding-left:20px;">
            <li><strong>Consumer apps</strong> &mdash; fitness trackers, recipe apps, weather apps, games, crypto wallets, and tools built for end-users rather than developers</li>
            <li>Default deployment URLs with no custom domain</li>
            <li>Dead links or tools that return errors</li>
            <li>AI-generated marketing copy with no substance</li>
            <li>Duplicate of a tool already in the catalog</li>
            <li>Paid-only SaaS with no programmatic access path</li>
        </ul>

        <div style="background:var(--cream-dark);border-radius:var(--radius);padding:20px 24px;margin-top:32px;">
            <p style="color:var(--ink);font-size:15px;margin:0;">
                <strong>Why these guidelines exist:</strong> IndieStack serves AI agents via the
                <a href="/mcp" style="color:var(--accent);">MCP server</a>. When an agent recommends a tool from our catalog,
                it needs to actually work. Every tool we list is a promise to the agents and developers who trust our curation.
            </p>
        </div>

        <div style="text-align:center;margin-top:32px;">
            <a href="/submit" class="btn" style="background:var(--accent);color:white;padding:12px 32px;text-decoration:none;font-size:16px;font-weight:600;border-radius:999px;">
                Submit Your Tool
            </a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell("Submission Guidelines", body, user=request.state.user, description="What we look for when reviewing tool submissions. IndieStack is a curated directory — AI agents rely on our curation to make reliable recommendations."))
