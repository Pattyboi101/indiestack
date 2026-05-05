"""Static content pages — about, terms, privacy, FAQ, blog, best-of."""

import json
import re
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, tool_card
from indiestack.routes.category_icons import category_icon
from indiestack import db as _db


async def _inject_tool_cards(db, content: str) -> str:
    """Replace {{ tool: slug }} placeholders with interactive tool cards."""
    pattern = r'\{\{\s*tool:\s*([\w-]+)\s*\}\}'
    matches = re.findall(pattern, content)

    for slug in matches:
        tool = await _db.get_tool_by_slug(db, slug)
        if tool:
            card_html = f'<div style="margin:24px 0;">{tool_card(tool)}</div>'
            content = content.replace(f'{{{{ tool: {slug} }}}}', card_html)
        else:
            content = content.replace(f'{{{{ tool: {slug} }}}}', '')

    return content

router = APIRouter()

_CONTAINER = 'style="max-width:800px; margin:40px auto; padding:0 24px; line-height:1.8;"'
_HEADING = 'style="color:var(--terracotta);"'
_TEXT = 'style="color:var(--ink);"'


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    body = f"""
    <div style="max-width:720px;margin:0 auto;padding:64px 24px;">

      <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);line-height:1.2;margin-bottom:8px;">
        Two uni students, 5 hours of sleep, and a guardrail for AI agents.
      </h1>
      <p style="font-size:18px;color:var(--ink-muted);line-height:1.6;margin-bottom:48px;">
        IndieStack is built by people who know what it&rsquo;s like to ship something and have nobody see it.
      </p>

      <!-- The story -->
      <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
        How this started
      </h2>
      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        Pat kept trying to launch side projects &mdash; GovLink, Logic Gate &mdash; and kept hitting the same wall:
        nobody could find them. Reddit wants you to farm karma before you can post. Product Hunt is a
        popularity contest. Hacker News is gated. The places where indie makers are supposed to get
        discovered are ironically the hardest places to be seen.
      </p>
      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        Meanwhile Ed was building AI automations for solar panel businesses and running into the same
        problem &mdash; every tool cost $29.99 a month, and the good stuff built by real people was
        impossible to find. One night Pat texted: <em>&ldquo;There&rsquo;s a gap here we need to fill.
        This will solve all of our problems with SaaS.&rdquo;</em> That text became IndieStack.
      </p>

      <!-- The mission -->
      <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-top:40px;margin-bottom:12px;">
        What we&rsquo;re actually building
      </h2>
      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        A dependency guardrail for AI coding agents. We have an
        <a href="https://pypi.org/project/indiestack/" style="color:var(--accent);">MCP server</a>
        that plugs into Claude, Cursor, and Windsurf &mdash; so when a developer asks their AI to build
        something, it checks IndieStack first. If a developer tool already does the job, the agent recommends
        it instead of building from scratch.
      </p>
      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        Think of it like humans sharing knowledge across generations &mdash; except we&rsquo;re building the same
        system for AI agents. Every tool listed here saves someone else from reinventing the wheel, saves
        tokens, and helps the maker build a reputation.
      </p>

      <!-- Who we are -->
      <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-top:40px;margin-bottom:24px;">
        Who we are
      </h2>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px;">
        <!-- Pat -->
        <div class="card" style="padding:24px;">
          <img src="/founders/pat.jpg" alt="Patrick Amey-Jones" style="width:56px;height:56px;border-radius:50%;object-fit:cover;margin-bottom:12px;">
          <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:4px;">
            Pat <span style="font-size:13px;color:var(--ink-muted);font-family:var(--font-body);font-weight:400;">(a.k.a. Oatcake)</span>
          </h3>
          <p style="color:var(--accent);font-size:13px;font-weight:600;margin-bottom:12px;">Builds the product</p>
          <p style="color:var(--ink-light);font-size:14px;line-height:1.7;">
            Final-year Zoology student at Cardiff Uni. Does data analytics in R and Python by day, builds
            IndieStack with Claude by night. Averages 5&ndash;6 hours of sleep. Previously shipped GovLink.
            Believes the second mouse gets the cheese. Maybe the best Binding of Isaac player in the world.
          </p>
          <div style="display:flex;gap:12px;margin-top:12px;">
            <a href="https://github.com/pattyboi101" style="color:var(--ink-muted);font-size:13px;text-decoration:none;">GitHub</a>
            <a href="https://instagram.com/pattyaj_" style="color:var(--ink-muted);font-size:13px;text-decoration:none;">Instagram</a>
          </div>
        </div>
        <!-- Ed -->
        <div class="card" style="padding:24px;">
          <img src="/founders/ed.jpg" alt="Edward" style="width:56px;height:56px;border-radius:50%;object-fit:cover;margin-bottom:12px;">
          <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:4px;">
            Ed <span style="font-size:13px;color:var(--ink-muted);font-family:var(--font-body);font-weight:400;">(a.k.a. Jabba)</span>
          </h3>
          <p style="color:var(--accent);font-size:13px;font-weight:600;margin-bottom:12px;">Handles growth</p>
          <p style="color:var(--ink-light);font-size:14px;line-height:1.7;">
            Co-founder. Student teacher by day, built an AI receptionist and lead verifier for solar
            panel businesses on n8n before channelling that energy into IndieStack. Runs Reddit outreach,
            maker relationships, and social strategy. Semi-professional Brawlhalla player.
          </p>
          <div style="display:flex;gap:12px;margin-top:8px;">
            <a href="https://x.com/indiestack_dev" style="color:var(--ink-muted);font-size:13px;text-decoration:none;">X / Twitter</a>
          </div>
        </div>
      </div>

      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        We&rsquo;ve been friends since school &mdash; we used to play Pok&eacute;mon Go together before
        either of us knew what an API was. Now we&rsquo;re based in Cardiff, building IndieStack with the
        same energy and a lot of late nights.
      </p>
      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        Neither of us has a background in SaaS or startups &mdash; Pat studies zoology and Ed was
        automating solar businesses. This whole thing started because we couldn&rsquo;t get our own
        projects noticed. That frustration turned into IndieStack.
      </p>

      <!-- Why indie tools -->
      <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-top:40px;margin-bottom:12px;">
        Why indie tools specifically
      </h2>
      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        Because we were sick of every tool costing $29.99 a month. We just wanted a place to find
        powerful tools built by real people, not corporations. The vibecoding wave means more people
        than ever are building real software &mdash; but getting discovered is still the hardest part.
        If you&rsquo;ve built something useful, you should be able to put it in front of people without
        farming karma or paying for placement.
      </p>
      <p style="color:var(--ink-light);line-height:1.8;margin-bottom:16px;">
        Abandonware is a real problem &mdash; that&rsquo;s why we verify every tool on IndieStack. Each one is
        reviewed by a human before it goes live. No spam. No abandoned projects. No enterprise products
        pretending to be indie. Just real tools by real people.
      </p>

      <!-- Contact -->
      <div style="text-align:center;margin-top:40px;padding:24px 0;">
        <p style="color:var(--ink-muted);font-size:15px;">
          Get in touch: <a href="mailto:pajebay1@gmail.com" style="color:var(--accent);font-weight:600;text-decoration:none;">pajebay1@gmail.com</a>
        </p>
      </div>

      <!-- CTA -->
      <div style="text-align:center;padding:40px 0;border-top:1px solid var(--border);margin-top:16px;">
        <p style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
          Built something? We&rsquo;d love to see it.
        </p>
        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
          <a href="/submit" class="btn btn-primary" style="padding:12px 24px;">Submit Your Tool</a>
          <a href="/why-list" class="btn btn-secondary" style="padding:12px 24px;">Why list here?</a>
        </div>
      </div>

    </div>
    """
    return HTMLResponse(page_shell("About", body, user=request.state.user,
                                    description="IndieStack is built by two uni students in Cardiff. We're building the dependency guardrail that AI coding agents use to validate packages before installing."))


@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    body = f"""
    <div {_CONTAINER}>
      <h1 {_HEADING}>Terms of Service</h1>
      <p {_TEXT}>Last updated: February 2026</p>

      <ol {_TEXT}>
        <li>
          <h2 {_HEADING}>Acceptance of Terms</h2>
          <p>By accessing or using IndieStack ("the Platform"), you agree to be bound by these
          Terms of Service. If you do not agree to these terms, you may not use the Platform.</p>
        </li>

        <li>
          <h2 {_HEADING}>User Accounts</h2>
          <p>You may need to create an account to access certain features. You are responsible
          for maintaining the confidentiality of your account credentials and for all activity
          that occurs under your account. You must provide accurate and complete information
          when creating an account and keep it up to date.</p>
        </li>

        <li>
          <h2 {_HEADING}>User-Generated Content</h2>
          <p>Tool listings, descriptions, images, and other content you submit remain your
          intellectual property. By submitting content to IndieStack, you grant us a
          non-exclusive, worldwide licence to display, distribute, and promote your content
          on the Platform. You represent that you have the right to submit all content you
          provide and that it does not infringe any third party's rights.</p>
        </li>

        <li>
          <h2 {_HEADING}>Payments</h2>
          <p>IndieStack offers both free and paid tiers. Core features including tool search,
          browsing, and MCP server access are free. Optional paid plans provide additional
          capabilities such as enhanced analytics and priority support. All payments are processed
          securely through Stripe. We do not store your payment card details — these are handled
          entirely by Stripe.</p>
        </li>

        <li>
          <h2 {_HEADING}>Intellectual Property</h2>
          <p>The IndieStack name, logo, design, and platform code are the property of
          IndieStack and its founders. You may not copy, modify, or distribute any part
          of the Platform without written permission. Tool makers retain full ownership
          of their products listed on the Platform.</p>
        </li>

        <li>
          <h2 {_HEADING}>Prohibited Conduct</h2>
          <p>You agree not to: submit false or misleading listings; scrape or harvest data
          from the Platform beyond what is available via our public API and MCP server;
          interfere with the Platform's operation; impersonate another user or maker;
          abuse the search or reaction features (e.g. automated clicking); or use the
          Platform for any unlawful purpose.</p>
        </li>

        <li>
          <h2 {_HEADING}>Termination</h2>
          <p>We reserve the right to suspend or terminate your account at any time if you
          violate these terms or engage in conduct that we determine is harmful to the
          Platform, other users, or third parties. You may close your account at any time
          by contacting us.</p>
        </li>

        <li>
          <h2 {_HEADING}>Limitation of Liability</h2>
          <p>IndieStack is provided "as is" without warranties of any kind, express or
          implied. To the maximum extent permitted by law, IndieStack and its founders shall
          not be liable for any indirect, incidental, special, consequential, or punitive
          damages arising from your use of the Platform. Our total liability shall not exceed
          the amount you have paid to IndieStack in the twelve months preceding the claim.</p>
        </li>

        <li>
          <h2 {_HEADING}>Changes to Terms</h2>
          <p>We may update these terms from time to time. Continued use of the Platform after
          changes constitutes acceptance of the updated terms. We will notify registered users
          of material changes via email.</p>
        </li>

        <li>
          <h2 {_HEADING}>Governing Law</h2>
          <p>These terms are governed by and construed in accordance with the laws of England
          and Wales. Any disputes arising from these terms shall be subject to the exclusive
          jurisdiction of the courts of England and Wales.</p>
        </li>
      </ol>
    </div>
    """
    return HTMLResponse(page_shell(
        "Terms of Service", body,
        user=request.state.user,
        description="Terms of Service for IndieStack, the dependency guardrail for AI coding agents.",
        canonical="/terms",
    ))


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    body = f"""
    <div {_CONTAINER}>
      <h1 {_HEADING}>Privacy Policy</h1>
      <p {_TEXT}>Last updated: April 2026</p>

      <h2 {_HEADING}>Data We Collect</h2>
      <p {_TEXT}>We collect the following information:</p>
      <ul {_TEXT}>
        <li><strong>Account information:</strong> your email address and display name when you create
        an account.</li>
        <li><strong>Session cookie:</strong> a session identifier (<code>indiestack_session</code>)
        stored in your browser to keep you logged in. Anonymous visitors also receive a session
        cookie so that features like tool reactions work without an account.</li>
        <li><strong>IP address and User-Agent:</strong> your IP address and browser User-Agent string
        are hashed together to produce an anonymous visitor identifier used for aggregate analytics
        (e.g. unique visitor counts). We do not store raw IP addresses or build individual profiles.</li>
        <li><strong>Usage data:</strong> page views, search queries, outbound clicks to tool websites,
        and tool reactions ("I use this" / "Bookmarked"). This data is stored in our database and
        used to power activity feeds, search rankings, and aggregate statistics shown on the site.</li>
        <li><strong>MCP server queries:</strong> when an AI agent searches our catalog via the MCP
        server, we log the search query, the agent platform identifier (e.g. "Claude Desktop"),
        and increment view counts. No personal data from the agent's user is collected.</li>
        <li><strong>MCP agent feedback:</strong> AI agents may optionally report tool integration
        outcomes (success/failure) and tool compatibility data via <code>report_outcome</code>
        and <code>report_compatibility</code> functions. This data is used to improve tool
        recommendations and build trust signals. No personal data is included in these reports.</li>
        <li><strong>Oracle API calls:</strong> when an AI agent queries our paid Oracle API
        (via the <a href="https://www.x402.org/" style="color:var(--accent);">x402 protocol</a>),
        we log the endpoint called, the tool slugs queried, and a timestamp. We do not log
        wallet addresses, payment signatures, or any identifying information about the agent
        or its user. Payment verification is handled entirely by the x402 protocol and the
        Base blockchain network — we receive USDC but do not process or store payment credentials.</li>
      </ul>

      <h2 {_HEADING}>How We Use Your Data</h2>
      <p {_TEXT}>Your data is used to: provide and maintain your account, send transactional emails
      (e.g. email verification, tool approval notifications), improve search results and tool
      rankings, display aggregate activity on the site (e.g. "X searches this week"), and prevent
      abuse or fraud.</p>

      <h2 {_HEADING}>Third-Party Services</h2>
      <p {_TEXT}>We use the following third-party services:</p>
      <ul {_TEXT}>
        <li><strong>Fly.io</strong> — hosting. Your requests are processed on Fly.io infrastructure.</li>
        <li><strong>Gmail SMTP</strong> — transactional emails are sent from our Gmail account.</li>
        <li><strong>Stripe</strong> — payments for paid plans are processed by Stripe. We do not
        store your payment card details — these are handled entirely by Stripe.</li>
        <li><strong>Base network (x402)</strong> — Oracle API payments are processed on the
        <a href="https://base.org/" style="color:var(--accent);">Base</a> blockchain via the
        x402 protocol. Payments are peer-to-peer USDC transfers verified by a facilitator service.
        On-chain transaction data (wallet addresses, amounts, timestamps) is publicly visible on
        the Base blockchain as with any blockchain transaction.</li>
      </ul>
      <p {_TEXT}>We do not sell your personal data. We do not use any third-party analytics,
      advertising, or tracking services.</p>

      <h2 {_HEADING}>Cookies</h2>
      <p {_TEXT}>IndieStack uses a single session cookie (<code>indiestack_session</code>) for
      authentication and anonymous feature access (e.g. reactions). A temporary
      <code>github_oauth_state</code> cookie is used during GitHub login for security (expires
      after 10 minutes). We do not use tracking cookies, advertising cookies, or any third-party
      cookie-based analytics. No cookie consent banner is needed because we only use strictly
      necessary cookies.</p>

      <h2 {_HEADING}>Data Retention</h2>
      <p {_TEXT}>Account data is retained for as long as your account is active. If you delete your
      account, your personal data will be removed within 30 days. Anonymised analytics data (page
      views, search logs, aggregated usage statistics) may be retained indefinitely. Session data
      for anonymous visitors is periodically cleaned up.</p>

      <h2 {_HEADING}>Your Rights (GDPR)</h2>
      <p {_TEXT}>If you are in the UK or EU, you have the right to:</p>
      <ul {_TEXT}>
        <li><strong>Access</strong> — request a copy of the personal data we hold about you.</li>
        <li><strong>Rectification</strong> — ask us to correct any inaccurate data.</li>
        <li><strong>Erasure</strong> — ask us to delete your personal data ("right to be forgotten").</li>
        <li><strong>Portability</strong> — request your data in a machine-readable format.</li>
        <li><strong>Object</strong> — object to processing of your data in certain circumstances.</li>
      </ul>

      <h2 {_HEADING}>Contact</h2>
      <p {_TEXT}>For any privacy-related questions or to exercise your rights, contact us at
      <a href="mailto:pajebay1@gmail.com" style="color:var(--accent);">pajebay1@gmail.com</a>.</p>
    </div>
    """
    return HTMLResponse(page_shell(
        "Privacy Policy", body,
        user=request.state.user,
        description="Privacy policy for IndieStack. We collect minimal data, use no third-party trackers, and never sell your information.",
        canonical="/privacy",
    ))


@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    questions = [
        (
            "What is IndieStack?",
            "IndieStack is a dependency guardrail for AI coding agents. It validates packages before "
            "install, catches hallucinations and typosquats, and provides migration intelligence from "
            "real GitHub data. 6,500+ developer tools tracked, searchable via our "
            "<a href='https://pypi.org/project/indiestack/' style='color:var(--accent);'>MCP server</a>."
        ),
        (
            "How do I list my tool?",
            "Click <a href='/submit' style='color:var(--accent);'>Submit a Tool</a> in the navigation bar. "
            "Fill out the form with your tool's name, description, pricing, and a link to your website. "
            "Takes about 2 minutes. Our team reviews every submission and approves it &mdash; usually "
            "within 24&ndash;48 hours."
        ),
        (
            "Is it free to list?",
            "Yes. Listing your tool on IndieStack is completely free. No monthly charges, no upfront "
            "fees. We want the catalog to be as comprehensive as possible."
        ),
        (
            "How does AI agent discovery work?",
            "IndieStack has an MCP server listed on <a href='https://pypi.org/project/indiestack/' "
            "style='color:var(--accent);'>PyPI</a> and the "
            "<a href='https://registry.modelcontextprotocol.io/' style='color:var(--accent);'>official MCP Registry</a>. "
            "When developers install it in Claude, Cursor, or Windsurf, their AI assistant can search "
            "our catalog before building from scratch. Your tool gets recommended directly in "
            "the conversation &mdash; not buried on page 3 of a directory."
        ),
        (
            "How does tool verification work?",
            "Every listing is manually reviewed by our team before it goes live. We check that the "
            "tool is a real, functional product, that the description is accurate, and that it meets "
            "our quality standards. Verified tools display a badge on their listing."
        ),
        (
            "Can I list a free tool?",
            "Absolutely. Free and open-source tools are welcome. Many makers list a free version "
            "alongside a paid tier. All tools get the same visibility regardless of pricing."
        ),
        (
            "Can I edit my listing after it's published?",
            "Yes. Log in to your maker dashboard and you can update your tool's description, pricing, "
            "tags, and other details at any time. Major changes may trigger a brief re-review."
        ),
        (
            "What are reactions (&ldquo;I use this&rdquo; / &ldquo;Bookmarked&rdquo;)?",
            "Anyone can react to a tool to signal that they use it or want to remember it. "
            "These help other developers gauge real adoption and help makers see who's interested. "
            "You don't need an account to react."
        ),
        (
            "Who's behind IndieStack?",
            "Two uni students in Cardiff &mdash; Pat and Ed. Pat builds the product, Ed handles "
            "growth and maker outreach. You can read the full story on our "
            "<a href='/about' style='color:var(--accent);'>about page</a>."
        ),
        (
            "Why use an indie tool instead of building it myself with AI?",
            "You <em>could</em> vibe-code anything &mdash; but should you? Every tool you build from "
            "scratch is tokens burned, bugs to fix, and features to maintain forever. A polished indie "
            "tool saves you thousands of tokens and gives you something battle-tested from day one. "
            "Save your tokens for the parts that make your project unique."
        ),
    ]

    details_html = "\n".join(
        f'<details style="border-bottom:1px solid var(--border); padding:16px 0;">'
        f'<summary style="cursor:pointer; font-weight:600; font-size:18px; color:var(--ink);">{q}</summary>'
        f'<p style="margin-top:12px; color:var(--ink);">{a}</p>'
        f'</details>'
        for q, a in questions
    )

    body = f"""
    <div {_CONTAINER}>
      <h1 {_HEADING}>Frequently Asked Questions</h1>
      <p {_TEXT}>Got questions? We've got answers. If you can't find what you're looking for,
      drop us an email at <a href="mailto:pajebay1@gmail.com" style="color:var(--accent);">pajebay1@gmail.com</a>.</p>
      {details_html}
    </div>
    """
    return HTMLResponse(page_shell(
        "FAQ — IndieStack", body,
        user=request.state.user,
        description="Frequently asked questions about IndieStack — how to list your tool, AI agent discovery via MCP, verification, and more.",
        canonical="/faq",
    ))


# ── Blog ─────────────────────────────────────────────────────────────────

_BLOG_POSTS = [
    {
        "slug": "agent-infrastructure",
        "title": "IndieStack Is Now the Procurement Layer for AI Agents",
        "date": "2026-02-27",
        "reading_time": "5 min read",
        "excerpt": "AI agents waste 30k-120k tokens building things that already exist. We built 5 features to make IndieStack the first place agents check before writing code.",
    },
    {
        "slug": "marketplace-launch",
        "title": "IndieStack Marketplace is Live — Sell Your Tools, Keep 95%",
        "date": "2026-03-02",
        "reading_time": "4 min read",
        "excerpt": "Indie developers can now sell their tools directly on IndieStack. 5% platform fee, Stripe payouts to your bank, and a curated audience of developers who want alternatives to big SaaS.",
    },
    {
        "slug": "tokens-saved",
        "title": "I asked Claude to build analytics from scratch. It cost 47,000 tokens. The alternative cost 2 lines.",
        "date": "2026-02-23",
        "reading_time": "4 min read",
        "excerpt": "A real comparison: 47,000 tokens and three hours of back-and-forth versus 700 tokens and four minutes. The MCP server that makes the difference.",
    },
    {
        "slug": "zero-js-frameworks",
        "title": "How We Built a Full Marketplace With Python, SQLite, and Zero JS Frameworks",
        "date": "2026-02-20",
        "reading_time": "6 min read",
        "excerpt": "No React. No Vue. No build step. Just Python f-strings, SQLite with WAL mode, and a single Fly.io machine serving 100+ tools.",
    },
    {
        "slug": "stop-wasting-tokens",
        "title": "Why Your AI Assistant Wastes Tokens Rebuilding Tools That Already Exist",
        "date": "2026-02-20",
        "reading_time": "5 min read",
        "excerpt": "Every day, developers burn thousands of tokens asking AI to build invoicing, analytics, and feedback widgets from scratch — when battle-tested developer tools already exist.",
    },
    {
        "slug": "indiestack-vs-stackshare",
        "title": "IndieStack vs StackShare: Why Developers Are Switching in 2026",
        "date": "2026-03-19",
        "reading_time": "6 min read",
        "excerpt": "StackShare showed what developers said they used. IndieStack shows what actually works — verified by AI agents, updated daily, and free to query via MCP.",
    },
]

_BLOG_CONTAINER = 'style="max-width:720px; margin:64px auto; padding:0 24px;"'
_BLOG_TITLE = 'style="font-family:var(--font-display); font-size:38px; line-height:1.2; color:var(--ink); margin-bottom:16px;"'
_BLOG_BODY = 'style="font-size:17px; line-height:1.8; color:var(--ink);"'


@router.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    cards = ""
    for post in _BLOG_POSTS:
        cards += f"""
        <a href="/blog/{post['slug']}" class="card hover-lift" style="display:block;text-decoration:none;color:inherit;
                  padding:24px;margin-bottom:24px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">{post['title']}</h2>
            <p style="color:var(--ink-muted);font-size:15px;line-height:1.6;">{post['excerpt']}</p>
        </a>
        """

    body = f"""
    <div {_BLOG_CONTAINER}>
        <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:8px;">IndieStack Blog</h1>
        <p style="color:var(--ink-muted);font-size:16px;margin-bottom:40px;">Indie tools, AI agent workflows, and building in public.</p>
        {cards}
    </div>
    """
    blog_ld = (
        json.dumps({
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "IndieStack Blog",
            "description": "Thoughts on developer tools, AI workflows, and the future of software discovery.",
            "url": f"{BASE_URL}/blog",
            "publisher": {"@type": "Organization", "name": "IndieStack", "url": BASE_URL},
        }, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    blog_head = f'<script type="application/ld+json">{blog_ld}</script>'

    return HTMLResponse(page_shell(
        "IndieStack Blog — Indie Tools, AI Agents & Building in Public", body,
        user=request.state.user,
        description="Thoughts on developer tools, AI workflows, and the future of software discovery.",
        canonical="/blog",
        extra_head=blog_head,
    ))


@router.get("/blog/agent-infrastructure", response_class=HTMLResponse)
async def blog_agent_infrastructure(request: Request):
    post = _BLOG_POSTS[0]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "IndieStack Is Now the Procurement Layer for AI Agents",
        "datePublished": "2026-02-27",
        "dateModified": "2026-02-27",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "_BASE_URL_PLACEHOLDER_"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "_BASE_URL_PLACEHOLDER_/logo.png"
            }
        },
        "description": "AI agents waste 30k-120k tokens building things that already exist. We built 5 features to make IndieStack the first place agents check before writing code.",
        "mainEntityOfPage": "_BASE_URL_PLACEHOLDER_/blog/agent-infrastructure",
        "wordCount": 1100
    }""".replace("_BASE_URL_PLACEHOLDER_", BASE_URL)

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-02-27">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{
            font-family: var(--font-display);
            font-size: 24px;
            color: var(--ink);
            margin: 40px 0 16px;
        }}
        .blog-article p {{
            margin-bottom: 24px;
        }}
        .blog-article blockquote {{
            border-left: 4px solid var(--slate);
            margin: 32px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}
        .blog-article pre {{
            background: var(--terracotta);
            color: var(--border);
            border-radius: var(--radius-sm);
            padding: 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}
        .blog-article pre code {{
            color: var(--border);
        }}
        .blog-article code {{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .blog-article a {{
            color: var(--slate-dark);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}
        .blog-article a:hover {{
            color: var(--terracotta);
        }}
        .blog-article ol {{
            padding-left: 24px;
            margin: 24px 0;
        }}
        .blog-article ol li {{
            margin-bottom: 12px;
        }}
        .blog-article ul {{
            padding-left: 24px;
            margin: 24px 0;
        }}
        .blog-article ul li {{
            margin-bottom: 8px;
        }}
    </style>
    """

    tweet_text = "IndieStack%20is%20now%20the%20procurement%20layer%20for%20AI%20agents.%205%20features%20so%20agents%20check%20IndieStack%20before%20writing%20boilerplate.%0A%0Ahttps%3A%2F%2Findiestack.ai%2Fblog%2Fagent-infrastructure%0A%0A%40indiestack_dev"

    body = f"""
    <article class="blog-article" {_BLOG_CONTAINER}>
        <header style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h1 {_BLOG_TITLE}>{post['title']}</h1>
            <p style="font-size:17px;color:var(--ink-muted);line-height:1.6;margin-top:12px;">{post['excerpt']}</p>
        </header>

        <div {_BLOG_BODY}>

            <h2>The Problem</h2>
            <p>
                Every time an AI agent is asked to build auth, payments, or analytics, it burns
                30,000 to 120,000 tokens building from scratch. It generates middleware,
                database schemas, API routes, error handling &mdash; the full stack. Three hours
                and 47,000 tokens later, you have a serviceable but unpolished implementation
                of something that already exists as a battle-tested developer tool.
            </p>
            <p>
                The agent is not lazy. It is uninformed. It does not know that a focused indie
                tool already handles exactly this problem, maintained by a developer who has
                spent months getting the edge cases right. The agent just does not have a way
                to check.
            </p>
            <p>
                Until now.
            </p>

            <h2>What We Built</h2>
            <p>
                We shipped five features in one push to make IndieStack the first place AI agents
                check before writing boilerplate code:
            </p>

            <ol>
                <li>
                    <strong>Prompt Cache Index</strong> &mdash;
                    <code>/api/tools/index.json</code> returns a compact JSON array of all 358 tools
                    on the platform. An agent includes this once in its system prompt and can
                    reference tools by slug forever after. With prompt caching, the first query
                    costs tokens; every subsequent query is nearly free.
                    <pre><code>curl https://indiestack.ai/api/tools/index.json | jq '.[0]'
{{
  "slug": "simple-analytics",
  "name": "Simple Analytics",
  "tagline": "Privacy-friendly analytics in one script tag",
  "category": "Analytics",
  "pricing": "$9/mo"
}}</code></pre>
                </li>
                <li>
                    <strong>Agent Citation Tracking</strong> &mdash;
                    Every time an agent recommends a tool, we log it. Makers see
                    &ldquo;Recommended by AI agents X times this week&rdquo; on their dashboard.
                    This is the flywheel: makers see real agent traffic, get excited, share their
                    listing, and more tools come in.
                </li>
                <li>
                    <strong>Dual-Audience Messaging</strong> &mdash;
                    Our MCP server and <code>llms.txt</code> now explicitly frame IndieStack as
                    &ldquo;the procurement layer for AI agents.&rdquo; When an AI crawler reads
                    our <code>llms.txt</code>, it sees clear instructions to check IndieStack
                    before writing boilerplate.
                </li>
                <li>
                    <strong>Stack Builder API</strong> &mdash;
                    Tell us what you need, we tell you what to use. Returns the best developer tool
                    for each requirement, matches Vibe Stacks if they cover the needs, and
                    reports total tokens saved. Also available as a <code>build_stack</code>
                    MCP tool.
                    <pre><code>curl "https://indiestack.ai/api/stack-builder?needs=auth,payments,analytics"
{{
  "stack": [
    {{"need": "auth", "tool": "clerk", "tokens_saved": 47000}},
    {{"need": "payments", "tool": "lemon-squeezy", "tokens_saved": 52000}},
    {{"need": "analytics", "tool": "simple-analytics", "tokens_saved": 31000}}
  ],
  "total_tokens_saved": 130000
}}</code></pre>
                </li>
                <li>
                    <strong>Use Case Pages</strong> &mdash;
                    <a href="/use-cases">/use-cases/auth</a>, <a href="/use-cases">/use-cases/payments</a>,
                    and more. Human-readable comparison tables with build-vs-buy analysis. Each
                    page has JSON-LD for agents to parse. 18 curated use cases with category
                    fallback for the rest.
                </li>
            </ol>

            <h2>Why This Matters</h2>
            <p>
                Moltbook proved that 1.6 million agents will show up if you build infrastructure
                for them. We are doing the same thing but for tool procurement. When an agent
                needs auth, it should check IndieStack before generating 50,000 tokens of code.
            </p>
            <blockquote>
                The future of software procurement is not a human browsing a comparison site.
                It is an AI agent querying a structured index of vetted tools and making a
                recommendation in under a second.
            </blockquote>
            <p>
                Every major coding assistant &mdash; Claude Code, Cursor, Windsurf, Copilot &mdash;
                is adding tool-use capabilities. MCP servers are becoming the standard way
                agents interact with external services. We have had an MCP server since day
                one. Now it is not just a nice-to-have; it is the primary distribution channel
                for reaching agents.
            </p>

            <h2>For Makers</h2>
            <p>
                Your tools are now discoverable by AI coding assistants. Every recommendation
                is tracked. You can see exactly how often agents suggest your tool on your
                <a href="/dashboard">maker dashboard</a>. This is a new distribution channel
                that did not exist a week ago.
            </p>
            <p>
                If your tool is not on IndieStack yet, <a href="/submit">submit it now</a>.
                It takes two minutes. Once it is listed, every AI agent with access to our
                MCP server or prompt cache can recommend it to developers.
            </p>

            <h2>Try It</h2>
            <p>
                Install the MCP server:
            </p>
            <pre><code>claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</code></pre>
            <p>
                Or hit the Stack Builder API directly:
            </p>
            <pre><code>curl "https://indiestack.ai/api/stack-builder?needs=auth,payments"</code></pre>
            <p>
                Browse the use case pages to see what agents see when they evaluate tools:
            </p>
        </div>

        <footer style="margin-top:48px;padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <a href="/use-cases"
               class="btn btn-primary" style="padding:12px 24px;border-radius:999px;text-decoration:none;">
                Browse Use Cases
            </a>
            <a href="https://twitter.com/intent/tweet?text={tweet_text}"
               target="_blank" rel="noopener"
               class="btn btn-primary" style="padding:12px 24px;border-radius:999px;text-decoration:none;">
                Share on X
            </a>
            <a href="/blog" style="color:var(--ink-muted);font-size:14px;">&#8592; Back to blog</a>
        </footer>
    </article>
    """

    return HTMLResponse(page_shell(
        post['title'], body,
        user=request.state.user,
        description=post['excerpt'],
        canonical="/blog/agent-infrastructure",
        extra_head=extra_head,
    ))


@router.get("/blog/marketplace-launch", response_class=HTMLResponse)
async def blog_marketplace_launch(request: Request):
    post = _BLOG_POSTS[1]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "IndieStack Marketplace is Live — Sell Your Tools, Keep 95%",
        "datePublished": "2026-03-02",
        "dateModified": "2026-03-02",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "_BASE_URL_PLACEHOLDER_"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "_BASE_URL_PLACEHOLDER_/logo.png"
            }
        },
        "description": "Indie developers can now sell their tools directly on IndieStack. 5% platform fee, Stripe payouts to your bank, and a curated audience of developers who want alternatives to big SaaS.",
        "mainEntityOfPage": "_BASE_URL_PLACEHOLDER_/blog/marketplace-launch",
        "wordCount": 850
    }""".replace("_BASE_URL_PLACEHOLDER_", BASE_URL)

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-03-02">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{
            font-family: var(--font-display);
            font-size: 24px;
            color: var(--ink);
            margin: 40px 0 16px;
        }}
        .blog-article p {{
            margin-bottom: 24px;
        }}
        .blog-article blockquote {{
            border-left: 4px solid var(--slate);
            margin: 32px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}
        .blog-article pre {{
            background: var(--terracotta);
            color: var(--border);
            border-radius: var(--radius-sm);
            padding: 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}
        .blog-article pre code {{
            color: var(--border);
        }}
        .blog-article code {{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .blog-article a {{
            color: var(--slate-dark);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}
        .blog-article a:hover {{
            color: var(--terracotta);
        }}
        .blog-article ol {{
            padding-left: 24px;
            margin: 24px 0;
        }}
        .blog-article ol li {{
            margin-bottom: 12px;
        }}
        .blog-article ul {{
            padding-left: 24px;
            margin: 24px 0;
        }}
        .blog-article ul li {{
            margin-bottom: 8px;
        }}
    </style>
    """

    tweet_text = "IndieStack%20Marketplace%20is%20live.%20Sell%20your%20indie%20tools%2C%20keep%2095%25.%205%25%20platform%20fee%2C%20Stripe%20payouts%20to%20your%20bank.%0A%0Ahttps%3A%2F%2Findiestack.ai%2Fblog%2Fmarketplace-launch%0A%0A%40indiestack_dev"

    body = f"""
    <article class="blog-article" {_BLOG_CONTAINER}>
        <header style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h1 {_BLOG_TITLE}>{post['title']}</h1>
            <p style="font-size:17px;color:var(--ink-muted);line-height:1.6;margin-top:12px;">{post['excerpt']}</p>
        </header>

        <div {_BLOG_BODY}>

            <div style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);padding:16px;margin-bottom:24px;font-size:14px;color:var(--ink-muted);">
                <strong>Update:</strong> Direct selling is paused while we focus on the dependency guardrail and migration intelligence. The marketplace infrastructure is built and will return.
            </div>

            <p>
                Today we are launching the IndieStack Marketplace. Indie developers can now sell
                their tools directly to other developers &mdash; with a 5% platform fee and direct
                Stripe payouts to your bank account. No gatekeepers. No 30% cuts. Just your tool,
                your price, and a curated audience of developers who want alternatives to big SaaS.
            </p>

            <h2>Why We Built This</h2>
            <p>
                Indie devs build incredible tools. Auth libraries, analytics dashboards, deployment
                platforms, monitoring services &mdash; focused software that does one thing brilliantly.
                But distribution is the bottleneck. Building the tool is the easy part. Getting it
                found is where most indie makers hit a wall.
            </p>
            <p>
                App stores take 30%. Gumroad takes 10%. And discovery on those platforms is still
                broken &mdash; your tool gets buried under a thousand Notion templates and AI wrapper
                courses. The developers who would love your product never find it.
            </p>
            <p>
                We built IndieStack to fix the discovery problem. We have over 130 curated indie
                tools, MCP integration so AI assistants can search the catalogue, and a community
                of makers and buyers who care about craft over scale. Now we are fixing the revenue
                problem too.
            </p>

            {{{{ tool: govlink }}}}

            <h2>How It Works</h2>
            <ol>
                <li><strong>List your tool</strong> &mdash; free, takes about two minutes. Add your
                description, pricing, screenshots, and tags.</li>
                <li><strong>Connect Stripe</strong> &mdash; Express onboarding walks you through it.
                Enter your bank details and you are set up to receive payouts.</li>
                <li><strong>Set your price</strong> &mdash; buyers pay via Stripe Checkout. Clean,
                secure, no card details touch our servers.</li>
                <li><strong>You get 95%</strong> &mdash; money goes directly to your bank via Stripe
                payouts. We take a 5% platform fee (3% for Pro makers). Stripe's processing fee
                is separate, roughly 1.4% + 20p for UK cards.</li>
            </ol>

            <h2>What Makes This Different</h2>
            <p>
                There are a lot of places to sell software. Here is why we think IndieStack is
                worth your attention:
            </p>
            <ul>
                <li><strong>5% commission</strong> (3% for Pro makers) &mdash; compare that to the
                App Store's 30% or Gumroad's 10%. We take less because we believe the maker
                should keep most of what they earn.</li>
                <li><strong>Curated marketplace</strong> &mdash; every tool is reviewed before it
                goes live. We award Verified and Ejectable trust badges so buyers know what
                they are getting. No spam, no vapourware, no AI wrapper courses.</li>
                <li><strong>Built for developers</strong> &mdash; our MCP integration means AI
                coding tools like Claude Code and Cursor can discover your product automatically.
                When a developer asks their AI for an analytics tool, yours shows up.</li>
                <li><strong>Indie Ring</strong> &mdash; makers on the platform get 50% off each
                other's tools. It is community cross-pollination: you use mine, I use yours,
                we all ship faster.</li>
            </ul>

            {{{{ tool: simple-analytics }}}}

            <blockquote>
                We did not build IndieStack to compete with Gumroad or Lemon Squeezy. We built
                it because indie developers deserve a marketplace where the audience already
                cares about developer tools &mdash; and where the AI agents
                actually find them.
            </blockquote>

            <h2>What You Can Sell</h2>
            <p>
                Anything that helps developers build, ship, or run software. SaaS subscriptions,
                one-time licence purchases, open-core tools with paid tiers, API services, dev
                utilities. If you built it and other developers would pay for it, it belongs here.
            </p>
            <p>
                We are not interested in hosting courses, e-books, or Notion templates. IndieStack
                is a tools marketplace. The tools are the point.
            </p>

            <h2>Get Started</h2>
            <p>
                If you have built something worth selling, <a href="/submit">list it on IndieStack</a>.
                It is free to list, takes two minutes, and your tool goes live after a quick review.
                Connect Stripe when you are ready to start accepting payments.
            </p>
            <p>
                If you are a developer looking for focused, high-quality alternatives to bloated
                enterprise software, <a href="/explore">browse the catalogue</a>. Every tool on
                IndieStack is built by an indie maker who cares about getting the details right.
            </p>
            <p>
                We have been building toward this for months. The directory, the trust badges,
                the MCP server, the maker profiles, the community &mdash; all of it was leading
                here. Today the marketplace is live. Let us see what indie developers can do
                when distribution is no longer the bottleneck.
            </p>
        </div>

        <footer style="margin-top:48px;padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <a href="https://twitter.com/intent/tweet?text={tweet_text}"
               target="_blank" rel="noopener"
               class="btn btn-primary" style="padding:12px 24px;border-radius:999px;text-decoration:none;">
                Share on X
            </a>
            <a href="/blog" style="color:var(--ink-muted);font-size:14px;">&#8592; Back to blog</a>
        </footer>
    </article>
    """

    body = await _inject_tool_cards(request.state.db, body)

    return HTMLResponse(page_shell(
        post['title'], body,
        user=request.state.user,
        description=post['excerpt'],
        canonical="/blog/marketplace-launch",
        extra_head=extra_head,
    ))


@router.get("/blog/tokens-saved", response_class=HTMLResponse)
async def blog_tokens_saved(request: Request):
    post = _BLOG_POSTS[2]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "I asked Claude to build analytics from scratch. It cost 47,000 tokens. The alternative cost 2 lines.",
        "datePublished": "2026-02-23",
        "dateModified": "2026-02-23",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "_BASE_URL_PLACEHOLDER_"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "_BASE_URL_PLACEHOLDER_/logo.png"
            }
        },
        "description": "A real comparison: 47,000 tokens and three hours of back-and-forth versus 700 tokens and four minutes. The MCP server that makes the difference.",
        "mainEntityOfPage": "_BASE_URL_PLACEHOLDER_/blog/tokens-saved",
        "wordCount": 1100
    }""".replace("_BASE_URL_PLACEHOLDER_", BASE_URL)

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-02-23">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{{{
            font-family: var(--font-display);
            font-size: 24px;
            color: var(--ink);
            margin: 40px 0 16px;
        }}}}
        .blog-article p {{{{
            margin-bottom: 24px;
        }}}}
        .blog-article blockquote {{{{
            border-left: 4px solid var(--slate);
            margin: 32px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}}}
        .blog-article pre {{{{
            background: var(--terracotta);
            color: var(--border);
            border-radius: var(--radius-sm);
            padding: 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}}}
        .blog-article pre code {{{{
            color: var(--border);
        }}}}
        .blog-article code {{{{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 8px;
            border-radius: 4px;
        }}}}
        .blog-article a {{{{
            color: var(--slate-dark);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}}}
        .blog-article a:hover {{{{
            color: var(--terracotta);
        }}}}
    </style>
    """

    tweet_text = "I%20asked%20Claude%20to%20build%20analytics%20from%20scratch.%2047%2C000%20tokens.%20The%20alternative%3F%20700%20tokens%20and%204%20minutes.%0A%0Ahttps%3A%2F%2Findiestack.ai%2Fblog%2Ftokens-saved%0A%0A%40indiestack_dev"

    body = f"""
    <article class="blog-article" {_BLOG_CONTAINER}>
        <header style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h1 {_BLOG_TITLE}>{post['title']}</h1>
            <p style="font-size:17px;color:var(--ink-muted);line-height:1.6;margin-top:12px;">{post['excerpt']}</p>
        </header>

        <div {_BLOG_BODY}>

            <p>
                I was building a SaaS dashboard and asked Claude to add analytics. Here is what happened.
            </p>

            <h2>The Waste</h2>
            <p>
                It started innocently. I had a FastAPI backend, a halfway-decent frontend, and I wanted
                to know which features users were actually clicking. Standard stuff. So I typed something
                like "add analytics tracking to my app" and hit enter.
            </p>
            <p>
                Claude got to work.
            </p>
            <p>
                First prompt: database schema. Tables for events, sessions, page views, user properties.
                Foreign keys. Indexes. Migration scripts. About 15,000 tokens of perfectly reasonable
                SQLite DDL that I would need to maintain forever.
            </p>
            <p>
                Second prompt: the event tracking layer. Middleware to capture requests, a utility function
                to fire custom events, a queue so I was not hammering the DB on every click. Another
                18,000 tokens. Still not wired up to the frontend.
            </p>
            <p>
                Third prompt: the dashboard. Charts. A little bar graph for daily active users. A funnel.
                Retention cohorts, because I got ambitious. Vanilla JS canvas rendering because I was not
                about to pull in Chart.js for a side project. This one took two follow-up messages to fix
                a timezone bug and another to make it actually render on mobile.
            </p>
            <p>
                Token count at this point: somewhere around <strong>47,000</strong>. Three hours of
                back-and-forth. And I had something that technically worked but that I would never trust
                in production. No data retention policy. No GDPR story. No way to actually understand
                the data without staring at raw numbers in a table I had built myself.
            </p>
            <p>
                I had reinvented a wheel that hundreds of people had already reinvented, and done it
                worse than all of them.
            </p>

            <h2>The Discovery</h2>
            <p>
                A few weeks later I was setting up a new project and stumbled on
                <a href="/">IndieStack</a>. The pitch was simple: it is a catalog of developer tools
                &mdash; small SaaS products built by solo founders and tiny teams &mdash; plus an
                MCP server that lets your AI assistant search the directory before it starts building
                something from scratch.
            </p>
            <p>
                Two commands:
            </p>
<pre><code>claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</code></pre>
            <p>
                That is it. Now when I work in Claude, it has access to a curated index of tools:
                what they do, what they cost, how they are installed, whether the founder is still
                actively maintaining them.
            </p>

            <h2>The Result</h2>
            <p>
                Next project. Same situation: I wanted analytics. This time I just asked Claude
                normally &mdash; "I need to add analytics to this app."
            </p>
            <p>
                Instead of immediately generating schema files, Claude paused and checked IndieStack
                first. It came back with a suggestion: Simple Analytics. Privacy-first, no cookies,
                no GDPR headaches. The integration is a single script tag. If I wanted server-side
                event tracking, that is one more line.
            </p>
            <p>
                The token count for that entire interaction: around 500 for the suggestion, maybe
                200 more when I asked it to show me the integration snippet. Call it <strong>700
                tokens</strong> total.
            </p>
            <p>
                I had it running in about four minutes. The dashboard looked better than anything
                I had built, the data was accurate from day one, and I did not have to think about
                it again.
            </p>

            <h2>The Math</h2>
            <p>
                <strong>47,000 tokens versus 700 tokens.</strong>
            </p>
            <p>
                That is not a made-up comparison. A full analytics feature &mdash; schema, event
                tracking, dashboard UI, charts, bug fixes &mdash; will realistically run you 40,000
                to 60,000 tokens with any capable LLM. It might be spread across multiple sessions,
                but the cost accumulates. On Claude Pro you have a context window and a rate limit.
                Every thousand tokens you spend regenerating infrastructure that already exists in a
                better form is a thousand tokens you are not spending on the thing that is actually
                different about your app.
            </p>
            <p>
                The 47,000-token version also needs maintenance. The 700-token version does not.
            </p>

            <h2>The Broader Point</h2>
            <p>
                Analytics is just one example. Auth. Payments. Transactional email. PDF invoices.
                Uptime monitoring. Background job queues. Every one of these has at least one indie
                tool &mdash; often several &mdash; that a single founder spent years building and is
                actively supporting. The tools are good. They are usually cheaper than the big-brand
                alternatives. They often have better documentation because the person who wrote the
                code also wrote the docs.
            </p>
            <p>
                The problem is that your AI does not know they exist. Without a way to search for
                them, it defaults to building the thing from scratch. Not because building is better
                &mdash; it is almost never better &mdash; but because building is what it knows how
                to do.
            </p>
            <p>
                Give it the tool. Let it search first.
            </p>
<pre><code>claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</code></pre>
            <p>
                Thirty seconds to install. The next time you ask your AI to add a feature, it will
                check what has already been built before it starts writing boilerplate.
            </p>
            <p>
                I wish I had had it three hours earlier.
            </p>
        </div>

        <footer style="margin-top:48px;padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <a href="https://twitter.com/intent/tweet?text={tweet_text}"
               target="_blank" rel="noopener"
               class="btn btn-primary" style="padding:12px 24px;border-radius:999px;text-decoration:none;">
                Share on X
            </a>
            <a href="/blog" style="color:var(--ink-muted);font-size:14px;">&#8592; Back to blog</a>
        </footer>
    </article>
    """

    return HTMLResponse(page_shell(
        post['title'], body,
        user=request.state.user,
        description=post['excerpt'],
        canonical="/blog/tokens-saved",
        extra_head=extra_head,
    ))


@router.get("/blog/stop-wasting-tokens", response_class=HTMLResponse)
async def blog_stop_wasting_tokens(request: Request):
    post = _BLOG_POSTS[4]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "Why Your AI Assistant Wastes Tokens Rebuilding Tools That Already Exist",
        "datePublished": "2026-02-20",
        "dateModified": "2026-02-20",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "_BASE_URL_PLACEHOLDER_"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "_BASE_URL_PLACEHOLDER_/logo.png"
            }
        },
        "description": "Every day, developers burn thousands of tokens asking AI to build invoicing, analytics, and feedback widgets from scratch — when battle-tested developer tools already exist.",
        "mainEntityOfPage": "_BASE_URL_PLACEHOLDER_/blog/stop-wasting-tokens",
        "wordCount": 950
    }""".replace("_BASE_URL_PLACEHOLDER_", BASE_URL)

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-02-20">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{
            font-family: var(--font-display);
            font-size: 24px;
            color: var(--ink);
            margin: 40px 0 16px;
        }}
        .blog-article p {{
            margin-bottom: 24px;
        }}
        .blog-article blockquote {{
            border-left: 4px solid var(--slate);
            margin: 32px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}
        .blog-article pre {{
            background: var(--terracotta);
            color: var(--border);
            border-radius: var(--radius-sm);
            padding: 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}
        .blog-article pre code {{
            color: var(--border);
        }}
        .blog-article code {{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .blog-article a {{
            color: var(--slate-dark);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}
        .blog-article a:hover {{
            color: var(--terracotta);
        }}
    </style>
    """

    tweet_text = "Stop%20burning%20tokens%20rebuilding%20tools%20that%20already%20exist.%20Your%20AI%20assistant%20needs%20a%20curated%20index%20of%20indie%20tools.%0A%0Ahttps%3A%2F%2Findiestack.ai%2Fblog%2Fstop-wasting-tokens%0A%0A%40indiestack_dev"

    body = f"""
    <article class="blog-article" {_BLOG_CONTAINER}>
        <header style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h1 {_BLOG_TITLE}>{post['title']}</h1>
            <p style="font-size:17px;color:var(--ink-muted);line-height:1.6;margin-top:12px;">{post['excerpt']}</p>
        </header>

        <div {_BLOG_BODY}>

            <h2>The Scene</h2>
            <p>
                It is 11pm on a Tuesday. You are three hours deep into a side project, riding that
                beautiful vibe-coding flow. You turn to your AI assistant and type: <em>"Build me a
                simple analytics dashboard — page views, referrers, top pages."</em>
            </p>
            <p>
                The AI obliges. It generates a database schema, a tracking pixel, an ingestion
                endpoint, a dashboard UI with charts, and a batch aggregation job. Five hundred
                lines of code. Beautiful, functional, and completely unnecessary — because
                <a href="/explore">Plausible Analytics</a> already does all of this for about
                nine pounds a month, is privacy-focused, and has been battle-tested by thousands
                of production sites.
            </p>
            <p>
                Your AI did not know. It was never taught to check.
            </p>

            {{{{ tool: simple-analytics }}}}

            <h2>The Problem</h2>
            <p>
                AI coding assistants are extraordinary at <em>generating</em> code. They can scaffold
                an entire application in minutes. But they are shockingly bad at knowing what
                already exists. They have no curated, up-to-date index of tools. They do not
                know that there is a solo developer in Berlin who built exactly the feedback widget
                you need, or that a two-person team in Lisbon ships the best uptime monitor on the
                market for a fraction of what Datadog charges.
            </p>
            <p>
                Every single day, thousands of developers burn tokens rebuilding invoicing systems,
                feedback forms, uptime monitors, email senders, feature flags, and analytics
                dashboards. All solved problems. All available as polished, maintained software
                from independent makers who have dedicated their livelihoods to getting these
                things right.
            </p>
            <p>
                The big tool directories — G2, Capterra, Product Hunt — are not built for this
                workflow. They are SEO-optimised for enterprise buyers clicking through Google,
                not for developers asking their AI <em>"find me a simple, affordable analytics tool
                that respects privacy."</em>
            </p>

            <h2>The Hidden Cost</h2>
            <p>
                It is not just about tokens. When your AI generates a custom analytics dashboard,
                you inherit a maintenance burden that compounds forever. That dashboard needs
                hosting. It needs security patches. It needs to handle edge cases you have not
                thought of yet — time zones, bot filtering, GDPR compliance, data retention
                policies. Every hour you spend maintaining your homegrown solution is an hour
                you are not spending on the thing that makes your project unique.
            </p>

            <blockquote>
                A vibe-coded analytics dashboard is something you maintain forever.
                A nine-pound-a-month SaaS tool is maintained by someone whose entire
                livelihood depends on it being excellent.
            </blockquote>

            <p>
                The opportunity cost is staggering. If you are building a marketplace, your
                competitive advantage is not your analytics pipeline — it is your curation,
                your community, your unique value proposition. Every token and every hour spent
                rebuilding commodity infrastructure is stolen from the work that actually matters.
            </p>

            <h2>The Indie Alternative</h2>
            <p>
                Here is what most developers do not realise: there is an entire ecosystem of
                indie SaaS tools built by solo developers and small teams that solve these
                exact problems. They are often cheaper, more focused, and better maintained than
                their enterprise counterparts. They respect your data because their reputation
                depends on it. They ship faster because there is no committee.
            </p>
            <p>
                A solo developer building an uptime monitor does not have a marketing department,
                a sales team, or a bloated feature roadmap driven by enterprise procurement checklists.
                They have a tight, focused product that does one thing brilliantly. And they tend to
                price it fairly because they are competing on quality, not on brand recognition.
            </p>
            <p>
                But these tools are invisible to AI assistants. They are scattered across personal
                websites, indie directories, and Twitter threads. There is no structured, searchable
                index that an AI can query before it starts generating boilerplate. Until now.
            </p>

            <h2>The Solution: MCP</h2>
            <p>
                We built an <a href="https://modelcontextprotocol.io">MCP server</a> that plugs
                directly into Claude Code, Cursor, and Windsurf. Before your AI writes a single
                line of boilerplate, it can search over 100 vetted developer tools and suggest an
                existing solution. It returns pricing, integration snippets, and an estimate of
                how many tokens you would burn building it yourself.
            </p>
            <p>
                Setting it up takes one command:
            </p>
<pre><code># Add IndieStack to your AI assistant
claude mcp add indiestack -- python -m indiestack.mcp_server

# Now when you ask "build me analytics", your AI checks IndieStack first:
# "Before you spend 50,000 tokens, there's Plausible Analytics
#  on IndieStack for &pound;9/mo — privacy-focused, no cookie banner needed."</code></pre>
            <p>
                The MCP server exposes two tools: <code>search_indie_tools</code> to find relevant
                software by keyword or category, and <code>get_tool_details</code> to pull pricing,
                reviews, and ready-to-paste integration code. Your AI becomes aware of the indie
                ecosystem — and it can make informed build-vs-buy recommendations before you waste
                a single token.
            </p>

            <h2>Stop Rebuilding. Start Discovering.</h2>
            <p>
                The best developers are not the ones who can build everything from scratch. They are
                the ones who know when to build and when to buy. Your AI assistant should have that
                same instinct — but it needs the right data.
            </p>
            <p>
                <a href="/explore">Browse the IndieStack catalogue</a> to see what is already out
                there. Or plug in the MCP server and let your AI do the searching for you. Either
                way, stop burning tokens on solved problems. Save them for the parts that make your
                project truly yours.
            </p>
        </div>

        <footer style="margin-top:48px;padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <a href="https://twitter.com/intent/tweet?text={tweet_text}"
               target="_blank" rel="noopener"
               class="btn btn-primary" style="padding:12px 24px;border-radius:999px;text-decoration:none;">
                Share on X
            </a>
            <a href="/blog" style="color:var(--ink-muted);font-size:14px;">&#8592; Back to blog</a>
        </footer>
    </article>
    """

    body = await _inject_tool_cards(request.state.db, body)

    return HTMLResponse(page_shell(
        post['title'], body,
        user=request.state.user,
        description=post['excerpt'],
        canonical="/blog/stop-wasting-tokens",
        extra_head=extra_head,
    ))


@router.get("/blog/zero-js-frameworks", response_class=HTMLResponse)
async def blog_zero_js_frameworks(request: Request):
    post = _BLOG_POSTS[3]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "How We Built a Full Marketplace With Python, SQLite, and Zero JS Frameworks",
        "datePublished": "2026-02-20",
        "dateModified": "2026-02-20",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "_BASE_URL_PLACEHOLDER_"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "_BASE_URL_PLACEHOLDER_/logo.png"
            }
        },
        "description": "No React. No Vue. No build step. Just Python f-strings, SQLite with WAL mode, and a single Fly.io machine serving 100+ tools.",
        "mainEntityOfPage": "_BASE_URL_PLACEHOLDER_/blog/zero-js-frameworks",
        "wordCount": 1050
    }""".replace("_BASE_URL_PLACEHOLDER_", BASE_URL)

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-02-20">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{
            font-family: var(--font-display);
            font-size: 24px;
            color: var(--ink);
            margin: 40px 0 16px;
        }}
        .blog-article p {{
            margin-bottom: 24px;
        }}
        .blog-article blockquote {{
            border-left: 4px solid var(--slate);
            margin: 32px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}
        .blog-article pre {{
            background: var(--terracotta);
            color: var(--border);
            border-radius: var(--radius-sm);
            padding: 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}
        .blog-article pre code {{
            color: var(--border);
        }}
        .blog-article code {{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .blog-article a {{
            color: var(--slate-dark);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}
        .blog-article a:hover {{
            color: var(--terracotta);
        }}
    </style>
    """

    tweet_text = "We%20built%20a%20full%20marketplace%20with%20Python%2C%20SQLite%2C%20and%20zero%20JS%20frameworks.%20No%20React.%20No%20build%20step.%20Here%27s%20how.%0A%0Ahttps%3A%2F%2Findiestack.ai%2Fblog%2Fzero-js-frameworks%0A%0A%40indiestack_dev"

    body = f"""
    <article class="blog-article" {_BLOG_CONTAINER}>
        <header style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h1 {_BLOG_TITLE}>{post['title']}</h1>
            <p style="font-size:17px;color:var(--ink-muted);line-height:1.6;margin-top:12px;">{post['excerpt']}</p>
        </header>

        <div {_BLOG_BODY}>

            <h2>The Contrarian Choice</h2>
            <p>
                Everyone told us we needed React. Or at the very least Vue, Svelte, something
                with a virtual DOM and a build pipeline. We were building IndieStack &mdash; a
                full marketplace with authentication, Stripe Connect payments, full-text search,
                an admin dashboard, maker profiles, bookmarks, reviews, and an MCP server that
                plugs into AI coding assistants. Not a todo app. A real product with real money
                flowing through it.
            </p>
            <p>
                We built the entire thing with Python f-strings, SQLite, and zero JavaScript
                frameworks. No React. No Vue. No Next.js. No build step. No <code>node_modules</code>.
                And after six rounds of development, we are more convinced than ever that this
                was the right call.
            </p>
            <p>
                This is not a contrarian take for the sake of being contrarian. It is a practical
                report from two university students who needed to ship fast, iterate faster, and
                not lose entire weekends debugging webpack configurations.
            </p>

            <h2>Why Python String Templates</h2>
            <p>
                Every route in IndieStack is a Python function that returns an HTML string. No
                Jinja2. No template engine. No special syntax to learn. You import
                <code>page_shell()</code> from a shared components module, compose your HTML
                inline using f-strings, and return it. That is the entire rendering model.
            </p>
            <p>
                Here is a simplified version of what a route looks like:
            </p>
<pre><code>from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from indiestack.routes.components import page_shell

router = APIRouter()

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    body = f\"\"\"
    &lt;div style="max-width:800px; margin:40px auto;"&gt;
      &lt;h1&gt;About IndieStack&lt;/h1&gt;
      &lt;p&gt;A curated marketplace for indie SaaS tools.&lt;/p&gt;
    &lt;/div&gt;
    \"\"\"
    return HTMLResponse(page_shell("About", body,
                                    user=request.state.user))</code></pre>
            <p>
                The benefits are surprisingly significant. There is zero build step &mdash; you
                edit a Python file, save it, and the change is live on the next request. The
                template <em>is</em> the code, so there is no context-switching between a
                templating language and your application logic. There is no template inheritance
                to debug, no partial rendering quirks, no cache invalidation headaches. If you
                can read Python, you can read every template in the application.
            </p>
            <p>
                The <code>page_shell()</code> function handles the HTML boilerplate: the
                <code>&lt;head&gt;</code> tag with fonts and CSS custom properties, the navigation
                bar, the footer, dark mode support, and meta tags. Every route just provides a
                title and a body string. Shared components like <code>tool_card()</code> are
                regular Python functions that return HTML strings. Composition is just string
                concatenation.
            </p>

            <h2>The SQLite Bet</h2>
            <p>
                IndieStack runs on a single SQLite database file with WAL mode enabled. Twenty-nine
                tables. FTS5 for full-text search across tool names, descriptions, and tags. The
                entire database sits on the same Fly.io machine that serves the application.
            </p>
            <p>
                This gives us properties that are genuinely difficult to replicate with Postgres
                or MySQL in a typical deployment. There is no connection pooling to configure. No
                separate database server to provision, monitor, or pay for. Backup is literally
                <code>cp database.db database.backup.db</code>. Reads are fast because there is
                zero network latency &mdash; the data is on the same disk as the application.
            </p>
            <p>
                WAL mode means readers never block writers and writers never block readers, which
                is the main concurrency bottleneck people worry about with SQLite in web applications.
                For our workload &mdash; a marketplace with modest write volume and heavier read
                traffic &mdash; it is more than sufficient.
            </p>
            <p>
                We are honest about the limits. SQLite will not scale to millions of concurrent
                writes. If we ever need to shard data across regions or handle thousands of
                simultaneous write transactions, we will need to migrate to Postgres. But that is
                not the problem we have today. The problem we had today was shipping a working
                marketplace, and SQLite let us do that in a weekend instead of a week.
            </p>

            <h2>What We Actually Use JavaScript For</h2>
            <p>
                We are not JavaScript puritans. We use inline vanilla JS for exactly four things:
                the dark mode toggle (reads a <code>localStorage</code> key, toggles a class on
                <code>&lt;html&gt;</code>), the mobile navigation hamburger menu (toggles visibility
                on a div), hover effects on interactive cards (inline <code>onmouseover</code> /
                <code>onmouseout</code> handlers), and auto-refresh on the <code>/live</code> page
                (a single <code>&lt;meta http-equiv="refresh"&gt;</code> tag).
            </p>
            <p>
                Every piece of JavaScript in the application is under twenty lines. There is no
                npm. No <code>node_modules</code>. No webpack, Vite, esbuild, or Turbopack. No
                <code>package.json</code>. The entire client-side behaviour is vanilla JS inlined
                in the HTML, and it works in every browser without transpilation.
            </p>

            <h2>The DX Wins</h2>
            <p>
                Deploying IndieStack is one command: <code>flyctl deploy</code>. No CI/CD pipeline
                to configure. No Docker Compose orchestration. No 47 microservices to health-check.
                The Dockerfile installs Python dependencies, copies the source tree, and runs
                <code>uvicorn</code>. That is the entire infrastructure.
            </p>
            <p>
                The entire application is roughly 6,000 lines of Python across 21 route files plus
                a handful of supporting modules for auth, email, payments, and the database layer.
                A new developer can read every line of code in an afternoon. Not skim it &mdash;
                actually read it, understand the data model, trace a request from URL to HTML
                response, and start making changes.
            </p>
            <p>
                When something breaks, the stack trace points to a Python function that returns
                an HTML string. There is no hydration mismatch to debug. No stale client-side
                state. No race condition between server-rendered markup and client-side JavaScript
                that tries to take over the DOM. The server renders HTML. The browser displays it.
                That is the entire mental model.
            </p>

            <h2>When This Breaks</h2>
            <p>
                We would be dishonest if we did not talk about the failure modes. If IndieStack
                hits 10,000 concurrent users, SQLite writes will bottleneck. The single-writer
                lock in WAL mode means write transactions queue up, and at high enough volume that
                queue becomes the limiting factor. We would need to migrate to Postgres or
                Turso at that point.
            </p>
            <p>
                If we need real-time collaborative features &mdash; live comments, presence
                indicators, collaborative editing &mdash; we will need WebSockets. Our current
                architecture is pure request-response. The <code>/live</code> page fakes
                real-time by refreshing every 15 seconds with a meta tag. That is not going to
                cut it for genuine real-time experiences.
            </p>
            <p>
                If we want client-side navigation (instant page transitions without full reloads),
                we would need to either adopt HTMX or build a proper SPA. Our current approach
                means every navigation is a full page load. It is fast because the pages are
                small, but it is not as slick as a well-built React app with optimistic updates
                and prefetching.
            </p>
            <p>
                But here is the thing: we do not have these problems. We have zero users. The
                marketplace is live, the tools are listed, and the infrastructure can handle
                orders of magnitude more traffic than we currently receive. The framework that
                ships is better than the framework that is perfect.
            </p>

            <blockquote>
                Premature optimisation is the root of all evil. Premature architecture is
                its quieter, more expensive cousin.
            </blockquote>

            <h2>The Takeaway</h2>
            <p>
                The best stack is the one that lets you ship. Ours happens to be Python f-strings,
                SQLite, and a single Fly.io machine. No framework orthodoxy. No build toolchain
                theology. Just the simplest thing that works for the problem in front of us.
            </p>
            <p>
                If you are a solo developer or a small team and you are spending more time
                configuring your toolchain than building your product, consider whether you
                actually need all that machinery. Maybe you do. But maybe &mdash; like us &mdash;
                you do not.
            </p>
            <p>
                <a href="/explore">Browse IndieStack</a> to see the result. Or check out
                <a href="/about">who we are</a> &mdash; two uni students in Cardiff who
                refuse to overcomplicate things.
            </p>
        </div>

        <footer style="margin-top:48px;padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <a href="https://twitter.com/intent/tweet?text={tweet_text}"
               target="_blank" rel="noopener"
               class="btn btn-primary" style="padding:12px 24px;border-radius:999px;text-decoration:none;">
                Share on X
            </a>
            <a href="/blog" style="color:var(--ink-muted);font-size:14px;">&#8592; Back to blog</a>
        </footer>
    </article>
    """

    body = await _inject_tool_cards(request.state.db, body)

    return HTMLResponse(page_shell(
        post['title'], body,
        user=request.state.user,
        description=post['excerpt'],
        canonical="/blog/zero-js-frameworks",
        extra_head=extra_head,
    ))


@router.get("/blog/indiestack-vs-stackshare", response_class=HTMLResponse)
async def blog_indiestack_vs_stackshare(request: Request):
    post = _BLOG_POSTS[5]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "IndieStack vs StackShare: Why Developers Are Switching in 2026",
        "datePublished": "2026-03-19",
        "dateModified": "2026-03-19",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "_BASE_URL_PLACEHOLDER_"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "_BASE_URL_PLACEHOLDER_/logo.png"
            }
        },
        "description": "StackShare showed what developers said they used. IndieStack shows what actually works — verified by AI agents, updated daily, and free to query via MCP.",
        "mainEntityOfPage": "_BASE_URL_PLACEHOLDER_/blog/indiestack-vs-stackshare",
        "keywords": ["stackshare alternative", "stackshare alternative 2026", "indiestack vs stackshare", "better than stackshare", "stackshare open source alternative"],
        "wordCount": 1100
    }""".replace("_BASE_URL_PLACEHOLDER_", BASE_URL)

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-03-19">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{
            font-family: var(--font-display);
            font-size: 24px;
            color: var(--ink);
            margin: 40px 0 16px;
        }}
        .blog-article p {{
            margin-bottom: 24px;
        }}
        .blog-article blockquote {{
            border-left: 4px solid var(--slate);
            margin: 32px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}
        .blog-article pre {{
            background: var(--terracotta);
            color: var(--border);
            border-radius: var(--radius-sm);
            padding: 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}
        .blog-article pre code {{
            color: var(--border);
        }}
        .blog-article code {{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .blog-article a {{
            color: var(--slate-dark);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}
        .blog-article a:hover {{
            color: var(--terracotta);
        }}
    </style>
    """

    tweet_text = "StackShare%20showed%20what%20devs%20said%20they%20used.%20IndieStack%20shows%20what%20actually%20works%20%E2%80%94%20verified%20by%20AI%20agents%2C%20updated%20daily.%0A%0Ahttps%3A%2F%2Findiestack.ai%2Fblog%2Findiestack-vs-stackshare"

    body = f"""
    <article class="blog-article" {_BLOG_CONTAINER}>
        <header style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h1 {_BLOG_TITLE}>{post['title']}</h1>
            <p style="font-size:17px;color:var(--ink-muted);line-height:1.6;margin-top:12px;">{post['excerpt']}</p>
        </header>

        <div {_BLOG_BODY}>

            <p>
                For years, <strong>StackShare</strong> was the default answer when someone asked
                &ldquo;what tools is this company using?&rdquo; It pioneered the idea of public
                tech stacks and built a community around sharing infrastructure decisions. That
                contribution matters and deserves acknowledgment.
            </p>
            <p>
                But the developer tooling landscape in 2026 looks nothing like it did when
                StackShare launched. AI coding agents now write a significant share of production
                code. Tools get created, forked, and abandoned faster than any human-curated
                directory can track. And the way developers discover tools has fundamentally
                shifted &mdash; from browsing directories to asking an AI assistant mid-session.
            </p>
            <p>
                StackShare was not designed for this world. <a href="/explore">IndieStack</a> was.
            </p>

            <h2>The Stale Data Problem</h2>
            <p>
                StackShare relies on self-reported data. A company creates a profile, lists the
                tools they use, and that profile sits there indefinitely. Nobody is required to
                update it when they migrate off a tool, swap out a database, or shut down entirely.
                The result is a directory where a significant portion of the listed stacks are
                months or years out of date.
            </p>
            <p>
                IndieStack takes a different approach. Every tool in the catalog has automated
                health monitoring: we check GitHub activity, archive status, last commit date,
                and maintenance signals on a rolling basis. Tools are flagged as
                <strong>Active</strong>, <strong>Stale</strong>, or <strong>Archived</strong>
                based on real signals, not self-reported claims. When you find a tool on
                IndieStack, you know whether it is actually maintained &mdash; not whether
                someone remembered to update a profile page two years ago.
            </p>

            <h2>AI Agents Cannot Use StackShare</h2>
            <p>
                This is the fundamental gap. When a developer asks Claude, Cursor, or Windsurf
                to &ldquo;add analytics to my app,&rdquo; the agent needs to find the right tool
                programmatically. StackShare has no API that AI agents can query. Their API was
                listed at $99/month in a closed beta that, as of early 2026, appears to be
                inactive.
            </p>
            <p>
                IndieStack ships a free
                <a href="https://pypi.org/project/indiestack/">MCP server</a> that any AI
                coding agent can install in one command. The agent searches 6,500+ tools across
                29 categories, gets structured data back (pricing, API type, SDK packages,
                environment variables, compatible tools), and can recommend the right tool
                in-context. No tab switching. No copy-pasting from a browser. The recommendation
                happens inside the coding session, exactly where it is useful.
            </p>
<pre><code>claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</code></pre>
            <p>
                That one line gives your AI assistant access to the entire catalog. StackShare
                has no equivalent.
            </p>

            <h2>Compatibility Data That Is Actually Verified</h2>
            <p>
                StackShare shows lists of tools grouped by category. It does not tell you whether
                two tools work well together. If you pick an auth provider and a database from
                StackShare, you are on your own to figure out whether they integrate cleanly.
            </p>
            <p>
                IndieStack tracks <strong>compatibility pairs</strong> &mdash; which tools have
                been verified to work together in real projects. This data comes from AI agent
                sessions: when an agent successfully integrates two tools in a project, it
                reports the pairing back. Over time, this builds a compatibility graph that no
                self-reported directory can replicate, because it is based on what actually
                worked in production code, not what someone listed on a profile.
            </p>

            <h2>Curation vs. Volume</h2>
            <p>
                StackShare lists roughly 7,000 tools and services, including enterprise
                platforms, legacy infrastructure, and tools that have not been updated in years.
                Volume is the strategy &mdash; list everything, let users sort it out.
            </p>
            <p>
                IndieStack catalogs 6,500+ tools across 29 categories with an explicit curation
                filter: focused, lean, actively maintained, and honestly priced. We are not
                trying to list every tool that has ever existed. We are trying to list the tools
                that a developer should actually consider using today. That means excluding
                abandoned projects, tools with deceptive pricing, and enterprise platforms that
                require a sales call to get started.
            </p>
            <p>
                For AI agents, this curation is not a nice-to-have &mdash; it is essential. An
                agent recommending a dead tool wastes tokens and erodes trust. Every tool in
                IndieStack has a health status that the agent can check before recommending it.
            </p>

            <h2>What Happened to StackShare</h2>
            <p>
                StackShare was acquired by FOSSA in 2022. Since the acquisition, the platform
                has received minimal visible updates. The community features that made it
                valuable &mdash; stack decisions, trending tools, active discussions &mdash;
                have largely gone quiet. The data that was current in 2021 is still what you
                see today.
            </p>
            <p>
                This is not a criticism of the team. Acquisitions change priorities, and FOSSA
                has its own product to focus on. But for developers looking for a
                <strong>StackShare alternative in 2026</strong>, the practical reality is that
                the platform is no longer actively maintained as a discovery tool.
            </p>

            <h2>Free to Use, Pro When You Need It</h2>
            <p>
                IndieStack is free. Browse the catalog, search by category, install the MCP
                server, get recommendations &mdash; all without paying anything. The
                <a href="/pricing">Pro tier</a> adds citation tracking (see when AI agents
                recommend your tool), market gap reports, and priority placement. But the core
                discovery experience is and will remain free.
            </p>
            <p>
                StackShare&rsquo;s free tier was limited, and their paid plans were oriented
                toward enterprise teams managing internal stack documentation. For an individual
                developer or a small team trying to find the right tool for a project, the value
                proposition was unclear.
            </p>

            <h2>Side-by-Side Comparison</h2>
            <p>
                For a detailed feature comparison table, see our
                <a href="/alternatives/stackshare">IndieStack vs StackShare comparison page</a>.
                The short version: IndieStack offers agent-verified data, a free MCP server,
                daily health monitoring, compatibility tracking, and active development. StackShare
                offers a large but increasingly stale directory with no AI integration.
            </p>

            <h2>The Bottom Line</h2>
            <p>
                StackShare solved the right problem at the right time: making tech stack decisions
                visible and shareable. But developer tooling discovery in 2026 requires live
                data, AI-native interfaces, and health-aware recommendations. Developers are not
                browsing directories anymore &mdash; they are asking their AI assistant to find
                the right tool while they are building.
            </p>
            <p>
                If you are looking for a <strong>StackShare alternative</strong> that is built for
                how developers actually work today, <a href="/explore">explore IndieStack</a>.
                Install the MCP server. Let your AI agent do the searching.
            </p>

            <blockquote>
                StackShare showed what developers said they used. IndieStack shows what
                actually works.
            </blockquote>
        </div>

        <footer style="margin-top:48px;padding-top:32px;border-top:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <a href="https://twitter.com/intent/tweet?text={tweet_text}"
               target="_blank" rel="noopener"
               class="btn btn-primary" style="padding:12px 24px;border-radius:999px;text-decoration:none;">
                Share on X
            </a>
            <a href="/blog" style="color:var(--ink-muted);font-size:14px;">&#8592; Back to blog</a>
        </footer>
    </article>
    """

    return HTMLResponse(page_shell(
        post['title'], body,
        user=request.state.user,
        description="Looking for a StackShare alternative? IndieStack offers agent-verified data, a free MCP server, and daily health monitoring for 3,099 developer tools.",
        canonical="/blog/indiestack-vs-stackshare",
        extra_head=extra_head,
    ))


# ── Best Of (Programmatic SEO) ──────────────────────────────────────────

_CATEGORY_INTROS = {
    "analytics-metrics": ("Analytics & Metrics", "Track what matters without the enterprise bloat. These indie analytics tools respect privacy, load fast, and give you the insights you need — not a hundred dashboards you'll never open."),
    "authentication-identity": ("Authentication & Identity", "Auth is a solved problem — don't burn tokens rebuilding it. These indie auth tools handle logins, sessions, and user management so you can focus on your actual product."),
    "automation-workflows": ("Automation & Workflows", "Automate repetitive tasks without enterprise pricing. These tools connect your apps, schedule jobs, and orchestrate workflows at a fraction of what Zapier charges."),
    "cms-content": ("CMS & Content", "Manage content without the WordPress tax. These indie CMS tools are headless, fast, and developer-friendly — built for modern stacks, not committee-driven roadmaps."),
    "communication-chat": ("Communication & Chat", "Add real-time messaging, notifications, and chat to your app. Built by focused teams who ship fast and price fairly."),
    "crm-sales": ("CRM & Sales", "Track leads and close deals without a bloated Salesforce instance. These indie CRMs are built for small teams who want clarity, not complexity."),
    "customer-support": ("Customer Support", "Help your users without Zendesk pricing. These support tools offer live chat, help desks, and knowledge bases built for lean teams."),
    "databases-backend": ("Databases & Backend", "Backend infrastructure built for indie developers. Managed databases, serverless functions, and API platforms that scale from zero to production."),
    "deployment-hosting": ("Deployment & Hosting", "Ship code without DevOps complexity. These hosting and deployment tools get your app live in minutes — no Kubernetes required."),
    "design-ui": ("Design & UI", "Design tools and component libraries built for developers who ship. No Figma license needed — just clean, functional UI."),
    "developer-tools": ("Developer Tools", "Tools built by developers, for developers. Debug faster, test better, and write cleaner code with these focused utilities."),
    "ecommerce-payments": ("E-commerce & Payments", "Sell online without Shopify's cut. These indie payment and e-commerce tools handle checkout, subscriptions, and invoicing with transparent pricing."),
    "email-marketing": ("Email & Marketing", "Send newsletters, drip campaigns, and transactional emails without the Mailchimp markup. Built for makers who care about deliverability, not dashboards."),
    "feedback-surveys": ("Feedback & Surveys", "Collect user feedback without building a custom widget. These tools handle NPS, surveys, feature requests, and bug reports out of the box."),
    "monitoring-logging": ("Monitoring & Logging", "Know when things break before your users do. Uptime monitors, error tracking, and log management at indie-friendly prices."),
    "productivity-project-management": ("Productivity & Project Management", "Plan, track, and ship without Jira's complexity. These project tools are opinionated in the right ways — simple enough for solo devs, powerful enough for small teams."),
    "scheduling-booking": ("Scheduling & Booking", "Handle appointments, meetings, and calendar integrations. No Calendly Pro required — these tools do the job at a fraction of the cost."),
    "security-compliance": ("Security & Compliance", "Secure your app without a dedicated security team. Vulnerability scanning, compliance checks, and secrets management from focused indie builders."),
    "seo-web-performance": ("SEO & Web Performance", "Optimise your site speed and search rankings. Lightweight tools that measure what matters without slowing you down."),
    "storage-file-management": ("Storage & File Management", "Upload, store, and serve files without AWS complexity. S3-compatible storage, CDNs, and media processing tools priced for indie budgets."),
}


@router.get("/best", response_class=HTMLResponse)
async def best_index(request: Request):
    """Index of all 'best indie X tools' category pages."""
    d = request.state.db
    categories = await _db.get_all_categories(d)

    cards = ""
    for cat in categories:
        count = cat['tool_count']
        slug = escape(cat['slug'])
        name = escape(cat['name'])
        cards += f"""
        <a href="/best/{slug}" class="card"
           style="text-decoration:none;color:inherit;padding:24px;display:flex;align-items:center;gap:16px;">
            <span style="color:var(--slate);display:flex;align-items:center;flex-shrink:0;">{category_icon(cat['slug'], size=28)}</span>
            <div>
                <div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">Best {name} Tools</div>
                <div style="font-size:13px;color:var(--ink-muted);">{count} developer tool{'s' if count != 1 else ''}</div>
            </div>
        </a>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);">
                Best Developer Tools in 2026
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:12px;max-width:600px;margin-left:auto;margin-right:auto;">
                Curated lists of the best developer tools across {len(categories)} categories.
                Built by independent makers, priced fairly, and battle-tested in production.
            </p>
        </div>
        <div class="card-grid">{cards}</div>
    </div>
    """
    return HTMLResponse(page_shell(
        "Best Developer Tools in 2026", body,
        user=request.state.user,
        description="Curated lists of the best developer tools across 29+ categories. Built by independent makers, priced fairly.",
        canonical="/best",
    ))


@router.get("/best/{category_slug}", response_class=HTMLResponse)
async def best_category(request: Request, category_slug: str):
    """Best developer tools page for a specific category."""
    d = request.state.db
    cat = await _db.get_category_by_slug(d, category_slug)
    if not cat:
        return HTMLResponse(page_shell("Not Found", '<div class="container" style="text-align:center;padding:80px 24px;"><h1>Category not found</h1></div>', user=request.state.user), status_code=404)

    tools, total = await _db.get_tools_by_category(d, cat['id'], page=1, per_page=50)

    # Get category-specific intro or generate a generic one
    cat_info = _CATEGORY_INTROS.get(category_slug, (cat['name'], f"Discover the best indie {cat['name'].lower()} tools built by independent developers. Focused functionality, fair pricing, and real human support."))
    display_name, intro_text = cat_info

    tool_cards = ""
    for i, tool in enumerate(tools):
        rank = i + 1
        badge = ""
        if rank <= 3:
            colours = {1: ("var(--gold)", '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26z"/></svg>'), 2: ("var(--ink-muted)", '<span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#94A3B8;color:#fff;font-size:11px;font-weight:700;">2</span>'), 3: ("var(--accent)", '<span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#CD7F32;color:#fff;font-size:11px;font-weight:700;">3</span>')}
            colour, emoji = colours[rank]
            badge = f'<div style="position:absolute;top:-8px;left:-8px;width:32px;height:32px;background:{colour};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 8px rgba(0,0,0,0.15);">{emoji}</div>'

        tool_cards += f'<div style="position:relative;">{badge}{tool_card(tool)}</div>'

    empty_cta = ""
    if not tools:
        empty_cta = """
        <div class="card" style="text-align:center;padding:48px 24px;border:2px dashed var(--border);">
            <div style="margin-bottom:12px;"><svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg></div>
            <h3 style="font-family:var(--font-display);color:var(--ink);">No tools listed yet</h3>
            <p style="color:var(--ink-muted);margin:8px 0 24px;">Be the first to list your tool in this category.</p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool</a>
        </div>
        """

    cat_name = cat['name']
    page_name = f"Best Indie {cat_name}{'' if 'tool' in cat_name.lower() else ' Tools'} in 2026"
    json_ld = (
        json.dumps({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": page_name,
            "description": intro_text,
            "url": f"{BASE_URL}/best/{category_slug}",
            "numberOfItems": total,
            "provider": {"@type": "Organization", "name": "IndieStack", "url": BASE_URL},
        }, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )

    extra_head = f'<script type="application/ld+json">{json_ld}</script>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="margin-bottom:40px;">
            <div style="font-size:13px;color:var(--ink-muted);margin-bottom:12px;">
                <a href="/best" style="color:var(--ink-muted);text-decoration:none;">Best Tools</a>
                <span style="margin:0 8px;">&#8250;</span>
                {cat_name_esc}
            </div>
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,38px);color:var(--ink);margin-bottom:12px;">
                Best Indie {cat_name_esc}{'' if 'tool' in cat_name_esc.lower() else ' Tools'} in 2026
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;line-height:1.6;max-width:700px;">
                {escape(intro_text)}
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-top:12px;">
                {total} tool{'s' if total != 1 else ''} &middot; Updated daily &middot;
                <a href="/category/{escape(category_slug)}" style="color:var(--slate-dark);">Browse full category &#8594;</a>
            </p>
        </div>
        <div class="card-grid">{tool_cards}{empty_cta}</div>
    </div>
    """
    return HTMLResponse(page_shell(
        f"Best Indie {cat_name_esc}{'' if 'tool' in cat_name_esc.lower() else ' Tools'} in 2026", body,
        user=request.state.user,
        description=f"The best indie {cat['name'].lower()} creations in 2026, curated by IndieStack. Built by independent makers, priced fairly.",
        canonical=f"/best/{category_slug}",
        extra_head=extra_head,
    ))


