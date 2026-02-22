"""Static content pages — about, terms, privacy, FAQ, blog, best-of."""

import re
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card
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

_CONTAINER = 'style="max-width:800px; margin:40px auto; padding:0 20px; line-height:1.8;"'
_HEADING = 'style="color:var(--terracotta);"'
_TEXT = 'style="color:var(--ink);"'


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    body = f"""
    <div {_CONTAINER}>
      <h1 {_HEADING}>About IndieStack</h1>
      <p {_TEXT}>
        IndieStack is a curated marketplace for indie SaaS tools — built by solo developers
        and small teams who pour their creativity into software that solves real problems.
      </p>
      <p {_TEXT}>
        We started IndieStack because we noticed something broken: incredible tools built by
        independent makers were getting buried beneath big-budget SaaS products with massive
        marketing spend. Discovery was the bottleneck, not quality.
      </p>

      <h2 {_HEADING}>Our Mission</h2>
      <p {_TEXT}>
        We believe indie tools deserve visibility alongside the giants. Our mission is to help
        solo developers and small teams get discovered by the people who need their products most.
        Every listing on IndieStack is a real product built by a real maker — no vapourware, no
        enterprise bloat, just focused software that does its job well.
      </p>

      <h2 {_HEADING}>Who We Are</h2>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:24px 0;">
        <div class="card" style="text-align:center;padding:28px;">
          <div style="width:64px;height:64px;border-radius:50%;background:var(--terracotta);color:white;
                      display:flex;align-items:center;justify-content:center;font-size:24px;
                      font-family:var(--font-display);margin:0 auto 12px;">P</div>
          <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);">Patrick</h3>
          <p style="color:var(--ink-muted);font-size:14px;margin:8px 0;">Co-founder. Full-time CS student, indie builder, and AI enthusiast.</p>
          <p style="color:var(--ink-muted);font-size:12px;margin:4px 0 0;">Shipped GovLink &middot; Building IndieStack</p>
          <div style="display:flex;gap:12px;justify-content:center;margin-top:12px;">
            <a href="https://x.com/indiestack_dev" style="color:var(--ink-muted);font-size:13px;">Twitter/X</a>
            <a href="https://github.com/pattyboi101" style="color:var(--ink-muted);font-size:13px;">GitHub</a>
          </div>
        </div>
        <div class="card" style="text-align:center;padding:28px;">
          <div style="width:64px;height:64px;border-radius:50%;background:var(--terracotta);color:white;
                      display:flex;align-items:center;justify-content:center;font-size:24px;
                      font-family:var(--font-display);margin:0 auto 12px;">E</div>
          <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);">Ed</h3>
          <p style="color:var(--ink-muted);font-size:14px;margin:8px 0;">Co-founder. Full-time CS student, indie builder, and AI enthusiast.</p>
          <p style="color:var(--ink-muted);font-size:12px;margin:4px 0 0;">Building IndieStack</p>
          <div style="display:flex;gap:12px;justify-content:center;margin-top:12px;">
            <a href="https://x.com/indiestack_dev" style="color:var(--ink-muted);font-size:13px;">Twitter/X</a>
          </div>
        </div>
      </div>
      <p {_TEXT} style="margin-top:8px;">
        We met at school in Cardiff, bonded over code, and never stopped building. Now we're
        full-time uni students who spend our evenings and weekends shipping indie tools. We started
        IndieStack because we kept finding amazing software buried under big-budget products &mdash;
        and we knew indie makers deserved better distribution. A few months in, we're more
        convinced than ever.
      </p>

      <h2 {_HEADING}>Why IndieStack?</h2>
      <p {_TEXT}>
        Big SaaS directories charge extortionate listing fees or bury indie tools in favour of
        paying sponsors. IndieStack is different. We keep fees fair (makers keep ~92% of every sale (94% on Pro)), we verify every listing, and we actively champion indie makers through
        curated collections, maker profiles, and a community that cares about craft over scale.
      </p>
      <p {_TEXT}>
        If you're a maker with a tool worth sharing, or a buyer looking for focused, high-quality
        software — you're in the right place.
      </p>

      <h2 {_HEADING}>How We Compare</h2>
      <div style="overflow-x:auto;margin:24px 0;">
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <thead>
            <tr style="border-bottom:2px solid var(--border);text-align:left;">
              <th style="padding:12px;">Platform</th>
              <th style="padding:12px;">Fee</th>
              <th style="padding:12px;">Indie Focus</th>
              <th style="padding:12px;">Curation</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid var(--border);background:var(--cream-dark);">
              <td style="padding:12px;font-weight:600;">IndieStack</td>
              <td style="padding:12px;">5% (3% Pro)</td>
              <td style="padding:12px;color:#16a34a;font-weight:600;">Yes &mdash; verified indie</td>
              <td style="padding:12px;">Manual review</td>
            </tr>
            <tr style="border-bottom:1px solid var(--border);">
              <td style="padding:12px;">Gumroad</td>
              <td style="padding:12px;">10%</td>
              <td style="padding:12px;color:var(--ink-muted);">No</td>
              <td style="padding:12px;color:var(--ink-muted);">No</td>
            </tr>
            <tr style="border-bottom:1px solid var(--border);">
              <td style="padding:12px;">Lemon Squeezy</td>
              <td style="padding:12px;">5% + 50p</td>
              <td style="padding:12px;color:var(--ink-muted);">No</td>
              <td style="padding:12px;color:var(--ink-muted);">No</td>
            </tr>
            <tr style="border-bottom:1px solid var(--border);">
              <td style="padding:12px;">AppSumo</td>
              <td style="padding:12px;">70%+</td>
              <td style="padding:12px;color:var(--ink-muted);">No</td>
              <td style="padding:12px;">Editorial</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    """
    return HTMLResponse(page_shell("About", body, user=request.state.user))


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
          <h2 {_HEADING}>Payments &amp; Refunds</h2>
          <p>All payments are processed securely through Stripe. IndieStack does not store
          your card details. Purchases on the Platform are for digital goods (software tools
          and licences). Due to the nature of digital goods, refunds are handled on a
          case-by-case basis at the discretion of the tool maker. Platform fees are
          non-refundable. All prices are displayed inclusive of applicable taxes where
          required.</p>
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
          <p>You agree not to: submit false or misleading listings; attempt to circumvent
          Platform fees; scrape or harvest data from the Platform; interfere with the
          Platform's operation; impersonate another user or maker; or use the Platform
          for any unlawful purpose.</p>
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
    return HTMLResponse(page_shell("Terms of Service", body, user=request.state.user))


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    body = f"""
    <div {_CONTAINER}>
      <h1 {_HEADING}>Privacy Policy</h1>
      <p {_TEXT}>Last updated: February 2026</p>

      <h2 {_HEADING}>Data We Collect</h2>
      <p {_TEXT}>We collect the following information:</p>
      <ul {_TEXT}>
        <li><strong>Account information:</strong> your email address and name when you create an account.</li>
        <li><strong>IP address:</strong> used for analytics, rate limiting, and abuse prevention.</li>
        <li><strong>Payment information:</strong> processed securely by Stripe. We do not store your card
        details on our servers — all payment data is handled directly by Stripe in accordance with
        PCI-DSS standards.</li>
      </ul>

      <h2 {_HEADING}>How We Use Your Data</h2>
      <p {_TEXT}>Your data is used to: provide and maintain your account, process transactions,
      send transactional emails (e.g. purchase confirmations), improve the Platform, and prevent
      abuse or fraud.</p>

      <h2 {_HEADING}>Third-Party Data Sharing</h2>
      <p {_TEXT}>We do not sell or share your personal data with third parties, with one exception:
      payment information is shared with <strong>Stripe</strong> solely for the purpose of processing
      transactions. Stripe's privacy policy governs their handling of your data.</p>

      <h2 {_HEADING}>Cookies</h2>
      <p {_TEXT}>IndieStack uses a single session cookie to keep you logged in. We do not use
      tracking cookies, advertising cookies, or any third-party cookie-based analytics. No cookie
      consent banner is needed because we only use strictly necessary cookies.</p>

      <h2 {_HEADING}>Data Retention</h2>
      <p {_TEXT}>Account data is retained for as long as your account is active. If you delete your
      account, your personal data will be removed within 30 days. Anonymised analytics data (page
      views, aggregated usage statistics) may be retained indefinitely.</p>

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
      <a href="mailto:privacy@indiestack.dev">privacy@indiestack.dev</a>.</p>
    </div>
    """
    return HTMLResponse(page_shell("Privacy Policy", body, user=request.state.user))


@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    questions = [
        (
            "How do I list my tool on IndieStack?",
            "Click <strong>Submit a Tool</strong> in the navigation bar. Fill out the form with "
            "your tool's name, description, pricing, and a link to your website. Once submitted, "
            "our team will review your listing and approve it — usually within 24-48 hours."
        ),
        (
            "How do I get paid?",
            "Payments are processed through Stripe Connect. When you set up your maker profile, "
            "you'll connect your Stripe account. Revenue from sales is deposited directly into your "
            "Stripe balance, minus the platform fee."
        ),
        (
            "What's the platform fee?",
            "The platform fee is 5% (or 3% on Pro), plus Stripe's ~3%. That means makers keep roughly "
            "<strong>92-94%</strong> of every sale. We believe that's the fairest deal in the indie "
            "marketplace space."
        ),
        (
            "Can I list a free tool?",
            "Absolutely. Free tools are welcome on IndieStack. Many makers list a free version "
            "alongside a paid tier. Free listings help you build visibility and gain upvotes from "
            "the community."
        ),
        (
            "How does tool verification work?",
            "Every listing is manually reviewed by our team before it goes live. We check that the "
            "tool is a real, functional product, that the description is accurate, and that it meets "
            "our quality standards. Verified tools display a badge on their listing."
        ),
        (
            "How long does approval take?",
            "Most submissions are reviewed and approved within <strong>24-48 hours</strong>. If we "
            "need more information or spot an issue, we'll email you with feedback."
        ),
        (
            "Can I edit my listing after it's published?",
            "Yes. Log in to your maker dashboard and you can update your tool's description, pricing, "
            "images, and other details at any time. Major changes may trigger a brief re-review."
        ),
        (
            "What payment methods do buyers have?",
            "Buyers can pay with any major credit or debit card via Stripe. We support Visa, "
            "Mastercard, American Express, and more. All transactions are secured with SSL encryption."
        ),
        (
            "Is there a free tier for makers?",
            "Listing your tool on IndieStack is completely free. You only pay the platform fee when "
            "you make a sale. There are no monthly charges or upfront listing fees."
        ),
        (
            "How do upvotes and wishlists work?",
            "Anyone can upvote a tool to show support — it helps surface the best tools in our "
            "rankings. Logged-in users can also save tools to their wishlist for easy access later. "
            "Makers can see upvote and wishlist counts in their dashboard."
        ),
        (
            "Why should I buy an indie tool instead of building it myself with AI?",
            "You <em>could</em> vibe-code anything &mdash; but should you? Every tool you build from "
            "scratch is tokens burned, bugs to fix, and features to maintain forever. A polished indie "
            "tool saves you thousands of tokens and gives you something battle-tested from day one. "
            "Save your tokens for the parts that make your project unique."
        ),
    ]

    details_html = "\n".join(
        f'<details style="border-bottom:1px solid var(--border, #e2e0dc); padding:16px 0;">'
        f'<summary style="cursor:pointer; font-weight:600; font-size:1.1rem; color:var(--ink);">{q}</summary>'
        f'<p style="margin-top:12px; color:var(--ink);">{a}</p>'
        f'</details>'
        for q, a in questions
    )

    body = f"""
    <div {_CONTAINER}>
      <h1 {_HEADING}>Frequently Asked Questions</h1>
      <p {_TEXT}>Got questions? We've got answers. If you can't find what you're looking for,
      drop us an email at <a href="mailto:hello@indiestack.dev">hello@indiestack.dev</a>.</p>
      {details_html}
    </div>
    """
    return HTMLResponse(page_shell("FAQ", body, user=request.state.user))


# ── Blog ─────────────────────────────────────────────────────────────────

_BLOG_POSTS = [
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
        "excerpt": "Every day, developers burn thousands of tokens asking AI to build invoicing, analytics, and feedback widgets from scratch — when battle-tested indie tools already exist.",
    },
]

_BLOG_CONTAINER = 'style="max-width:720px; margin:60px auto; padding:0 20px;"'
_BLOG_TITLE = 'style="font-family:var(--font-display); font-size:2.4rem; line-height:1.2; color:var(--ink); margin-bottom:16px;"'
_BLOG_BODY = 'style="font-size:17px; line-height:1.8; color:var(--ink);"'


@router.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    cards = ""
    for post in _BLOG_POSTS:
        cards += f"""
        <a href="/blog/{post['slug']}" style="display:block;text-decoration:none;color:inherit;
                  padding:28px;border:1px solid var(--border);border-radius:var(--radius);
                  background:var(--card-bg);transition:transform 0.15s ease,box-shadow 0.15s ease;margin-bottom:20px;"
           onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 12px 40px rgba(45,41,38,0.12)'"
           onmouseout="this.style.transform='none';this.style.boxShadow='none'">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);">{post['date']}</time>
                <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate-dark);">{post['reading_time']}</span>
            </div>
            <h2 style="font-family:var(--font-display);font-size:1.4rem;color:var(--ink);margin-bottom:8px;">{post['title']}</h2>
            <p style="color:var(--ink-muted);font-size:15px;line-height:1.6;">{post['excerpt']}</p>
        </a>
        """

    body = f"""
    <div {_BLOG_CONTAINER}>
        <h1 style="font-family:var(--font-display);font-size:2.2rem;color:var(--ink);margin-bottom:8px;">Blog</h1>
        <p style="color:var(--ink-muted);font-size:16px;margin-bottom:40px;">Thoughts on indie tools, AI workflows, and building in public.</p>
        {cards}
    </div>
    """
    return HTMLResponse(page_shell(
        "Blog", body,
        user=request.state.user,
        description="Thoughts on indie tools, AI workflows, and the future of software discovery.",
        canonical="/blog",
    ))


@router.get("/blog/stop-wasting-tokens", response_class=HTMLResponse)
async def blog_stop_wasting_tokens(request: Request):
    post = _BLOG_POSTS[1]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "Why Your AI Assistant Wastes Tokens Rebuilding Tools That Already Exist",
        "datePublished": "2026-02-20",
        "dateModified": "2026-02-20",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "https://indiestack.fly.dev"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "https://indiestack.fly.dev/logo.png"
            }
        },
        "description": "Every day, developers burn thousands of tokens asking AI to build invoicing, analytics, and feedback widgets from scratch — when battle-tested indie tools already exist.",
        "mainEntityOfPage": "https://indiestack.fly.dev/blog/stop-wasting-tokens",
        "wordCount": 950
    }"""

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-02-20">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{
            font-family: var(--font-display);
            font-size: 1.5rem;
            color: var(--ink);
            margin: 40px 0 16px;
        }}
        .blog-article p {{
            margin-bottom: 20px;
        }}
        .blog-article blockquote {{
            border-left: 4px solid var(--slate);
            margin: 28px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}
        .blog-article pre {{
            background: #1A2D4A;
            color: #E8ECF0;
            border-radius: var(--radius-sm);
            padding: 20px 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}
        .blog-article pre code {{
            color: #E8ECF0;
        }}
        .blog-article code {{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 6px;
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

    tweet_text = "Stop%20burning%20tokens%20rebuilding%20tools%20that%20already%20exist.%20Your%20AI%20assistant%20needs%20a%20curated%20index%20of%20indie%20tools.%0A%0Ahttps%3A%2F%2Findiestack.fly.dev%2Fblog%2Fstop-wasting-tokens%0A%0A%40indiestack_dev"

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
                line of boilerplate, it can search over 100 vetted indie tools and suggest an
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
               class="btn btn-primary" style="padding:10px 24px;border-radius:999px;text-decoration:none;">
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
    post = _BLOG_POSTS[0]

    json_ld = """{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "How We Built a Full Marketplace With Python, SQLite, and Zero JS Frameworks",
        "datePublished": "2026-02-20",
        "dateModified": "2026-02-20",
        "author": {
            "@type": "Organization",
            "name": "IndieStack",
            "url": "https://indiestack.fly.dev"
        },
        "publisher": {
            "@type": "Organization",
            "name": "IndieStack",
            "logo": {
                "@type": "ImageObject",
                "url": "https://indiestack.fly.dev/logo.png"
            }
        },
        "description": "No React. No Vue. No build step. Just Python f-strings, SQLite with WAL mode, and a single Fly.io machine serving 100+ tools.",
        "mainEntityOfPage": "https://indiestack.fly.dev/blog/zero-js-frameworks",
        "wordCount": 1050
    }"""

    extra_head = f"""
    <script type="application/ld+json">{json_ld}</script>
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-02-20">
    <meta property="article:author" content="IndieStack">
    <style>
        .blog-article h2 {{
            font-family: var(--font-display);
            font-size: 1.5rem;
            color: var(--ink);
            margin: 40px 0 16px;
        }}
        .blog-article p {{
            margin-bottom: 20px;
        }}
        .blog-article blockquote {{
            border-left: 4px solid var(--slate);
            margin: 28px 0;
            padding: 16px 24px;
            background: var(--cream-dark);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 17px;
            font-style: italic;
            color: var(--ink);
            line-height: 1.7;
        }}
        .blog-article pre {{
            background: #1A2D4A;
            color: #E8ECF0;
            border-radius: var(--radius-sm);
            padding: 20px 24px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.7;
            overflow-x: auto;
            margin: 24px 0;
        }}
        .blog-article pre code {{
            color: #E8ECF0;
        }}
        .blog-article code {{
            font-family: var(--font-mono);
            font-size: 0.9em;
            background: var(--cream-dark);
            padding: 2px 6px;
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

    tweet_text = "We%20built%20a%20full%20marketplace%20with%20Python%2C%20SQLite%2C%20and%20zero%20JS%20frameworks.%20No%20React.%20No%20build%20step.%20Here%27s%20how.%0A%0Ahttps%3A%2F%2Findiestack.fly.dev%2Fblog%2Fzero-js-frameworks%0A%0A%40indiestack_dev"

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
                an admin dashboard, maker profiles, wishlists, reviews, and an MCP server that
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
               class="btn btn-primary" style="padding:10px 24px;border-radius:999px;text-decoration:none;">
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
        icon = cat['icon'] or "&#128640;"
        count = cat['tool_count']
        slug = escape(cat['slug'])
        name = escape(cat['name'])
        cards += f"""
        <a href="/best/{slug}" class="card"
           style="text-decoration:none;color:inherit;padding:20px 24px;display:flex;align-items:center;gap:14px;
                  transition:transform 0.15s ease,box-shadow 0.15s ease;"
           onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 12px 40px rgba(26,45,74,0.12)'"
           onmouseout="this.style.transform='none';this.style.boxShadow='none'">
            <span style="font-size:28px;">{icon}</span>
            <div>
                <div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">Best {name} Tools</div>
                <div style="font-size:13px;color:var(--ink-muted);">{count} indie tool{'s' if count != 1 else ''}</div>
            </div>
        </a>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);">
                Best Indie SaaS Tools in 2026
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:12px;max-width:600px;margin-left:auto;margin-right:auto;">
                Curated lists of the best indie developer tools across {len(categories)} categories.
                Built by solo makers, priced fairly, and battle-tested in production.
            </p>
        </div>
        <div class="card-grid">{cards}</div>
    </div>
    """
    return HTMLResponse(page_shell(
        "Best Indie SaaS Tools in 2026", body,
        user=request.state.user,
        description="Curated lists of the best indie developer tools across 20 categories. Built by solo makers, priced fairly.",
        canonical="/best",
    ))


@router.get("/best/{category_slug}", response_class=HTMLResponse)
async def best_category(request: Request, category_slug: str):
    """Best indie tools page for a specific category."""
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
            colours = {1: ("#FFD700", "&#127942;"), 2: ("#C0C0C0", "&#129352;"), 3: ("#CD7F32", "&#129353;")}
            colour, emoji = colours[rank]
            badge = f'<div style="position:absolute;top:-8px;left:-8px;width:32px;height:32px;background:{colour};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 8px rgba(0,0,0,0.15);">{emoji}</div>'

        tool_cards += f'<div style="position:relative;">{badge}{tool_card(tool)}</div>'

    empty_cta = ""
    if not tools:
        empty_cta = """
        <div class="card" style="text-align:center;padding:48px 24px;border:2px dashed var(--border);">
            <p style="font-size:32px;margin-bottom:12px;">&#128640;</p>
            <h3 style="font-family:var(--font-display);color:var(--ink);">No tools listed yet</h3>
            <p style="color:var(--ink-muted);margin:8px 0 20px;">Be the first to list your tool in this category.</p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool</a>
        </div>
        """

    cat_name_esc = escape(cat['name'])
    json_ld = f"""{{"@context":"https://schema.org","@type":"CollectionPage","name":"Best Indie {cat_name_esc} Tools in 2026","description":"{escape(intro_text)}","url":"https://indiestack.fly.dev/best/{escape(category_slug)}","numberOfItems":{total},"provider":{{"@type":"Organization","name":"IndieStack","url":"https://indiestack.fly.dev"}}}}"""

    extra_head = f'<script type="application/ld+json">{json_ld}</script>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="margin-bottom:40px;">
            <div style="font-size:13px;color:var(--ink-muted);margin-bottom:12px;">
                <a href="/best" style="color:var(--ink-muted);text-decoration:none;">Best Tools</a>
                <span style="margin:0 6px;">&#8250;</span>
                {cat_name_esc}
            </div>
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,38px);color:var(--ink);margin-bottom:12px;">
                Best Indie {cat_name_esc} Tools in 2026
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
        f"Best Indie {cat_name_esc} Tools in 2026", body,
        user=request.state.user,
        description=f"The best indie {cat['name'].lower()} tools in 2026, curated by IndieStack. Built by solo developers, priced fairly.",
        canonical=f"/best/{category_slug}",
        extra_head=extra_head,
    ))
