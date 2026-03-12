"""What is IndieStack — explains the open-source supply chain for agentic workflows."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/what-is-indiestack", response_class=HTMLResponse)
async def what_is_page(request: Request):
    user = request.state.user
    db = request.state.db

    # Pull real stats
    _tc = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    tool_count = (await _tc.fetchone())['cnt']
    _cc = await db.execute("SELECT COUNT(*) as cnt FROM categories")
    cat_count = (await _cc.fetchone())['cnt']
    _mcp = await db.execute("SELECT COALESCE(SUM(mcp_view_count), 0) as cnt FROM tools")
    mcp_views = (await _mcp.fetchone())['cnt']
    _sl = await db.execute("SELECT COUNT(*) as cnt FROM search_logs")
    search_count = (await _sl.fetchone())['cnt']
    _ac = await db.execute("SELECT COUNT(*) as cnt FROM agent_citations")
    citation_count = (await _ac.fetchone())['cnt']
    ai_recs = mcp_views + search_count + citation_count
    _code = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND source_type='code'")
    code_count = (await _code.fetchone())['cnt']
    _saas = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND source_type='saas'")
    saas_count = (await _saas.fetchone())['cnt']

    # Format ai_recs nicely
    if ai_recs >= 1000:
        ai_recs_display = f"{ai_recs / 1000:.1f}k"
    else:
        ai_recs_display = str(ai_recs)

    body = f'''
    <div style="max-width:800px;margin:0 auto;padding:80px 24px 0;">

        <!-- ===== HERO ===== -->
        <div style="text-align:center;margin-bottom:64px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(32px,5vw,48px);color:var(--ink);line-height:1.15;margin-bottom:16px;">
                The Open-Source Supply Chain for Agentic Workflows
            </h1>
            <p style="font-size:clamp(16px,2.5vw,20px);color:var(--ink-muted);line-height:1.6;max-width:640px;margin:0 auto 32px;">
                AI agents shouldn&rsquo;t build from scratch when indie creators have already built the pieces.
                IndieStack is the supply chain &mdash; agents assemble from existing building blocks instead of reinventing them.
            </p>
            <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:8px 24px;font-size:15px;color:var(--ink-light);">
                <span style="font-weight:600;color:var(--ink);">{tool_count}+ creations</span>
                <span style="opacity:0.4;">|</span>
                <span>{code_count} open-source</span>
                <span style="opacity:0.4;">|</span>
                <span>{saas_count} SaaS</span>
                <span style="opacity:0.4;">|</span>
                <span>{cat_count} categories</span>
            </div>
        </div>

        <!-- ===== THE SHIFT ===== -->
        <div style="margin-bottom:56px;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3.5vw,30px);color:var(--ink);margin-bottom:16px;">
                Creation is exploding. Discovery hasn&rsquo;t caught up.
            </h2>
            <div style="color:var(--ink-light);line-height:1.8;font-size:16px;">
                <p style="margin-bottom:12px;">
                    A teacher builds a flashcard app. A musician ships a beat sequencer. A developer releases
                    an auth library. A designer launches a vector editor. AI is turning everyone into a creator.
                </p>
                <p style="margin-bottom:12px;">
                    But the AI helping the <em>next</em> person build a flashcard app doesn&rsquo;t know the first one exists.
                    It starts from scratch, every time. Thousands of tokens, thousands of duplicated efforts.
                    The problem isn&rsquo;t a lack of tools &mdash; it&rsquo;s that AI agents don&rsquo;t know they exist.
                </p>
                <p>
                    G2 and Capterra serve enterprise procurement teams, not agents assembling workflows mid-build.
                    IndieStack is the supply chain that connects AI agents to indie-built components &mdash; so they assemble instead of reinvent.
                </p>
            </div>
        </div>

        <!-- ===== WHAT BELONGS HERE ===== -->
        <div style="margin-bottom:56px;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3.5vw,30px);color:var(--ink);margin-bottom:8px;">
                If someone made it, it belongs here
            </h2>
            <p style="color:var(--ink-muted);font-size:16px;line-height:1.6;margin-bottom:24px;">
                The only constraint is &ldquo;indie-built.&rdquo; Not &ldquo;developer tool.&rdquo; Not &ldquo;SaaS.&rdquo; Anything an independent creator has shipped becomes a building block in the supply chain.
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(230px, 1fr));gap:16px;">

                <div class="card" style="padding:20px;cursor:default;transition:all 0.2s ease;"
                     onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)'"
                     onmouseleave="this.style.transform='';this.style.boxShadow=''">
                    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--accent);font-weight:700;margin-bottom:8px;">Authentication</div>
                    <div style="font-weight:700;color:var(--ink);margin-bottom:4px;">Hanko</div>
                    <div style="font-size:14px;color:var(--ink-light);margin-bottom:8px;">Passkey-first auth, open source</div>
                    <span style="font-size:12px;padding:2px 8px;border-radius:999px;background:rgba(0,212,245,0.12);color:var(--accent);font-weight:600;">SaaS</span>
                </div>

                <div class="card" style="padding:20px;cursor:default;transition:all 0.2s ease;"
                     onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)'"
                     onmouseleave="this.style.transform='';this.style.boxShadow=''">
                    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#e06c75;font-weight:700;margin-bottom:8px;">Games</div>
                    <div style="font-weight:700;color:var(--ink);margin-bottom:4px;">Veloren</div>
                    <div style="font-size:14px;color:var(--ink-light);margin-bottom:8px;">Open-world multiplayer RPG in Rust</div>
                    <span style="font-size:12px;padding:2px 8px;border-radius:999px;background:var(--success-bg);color:var(--success-text);font-weight:600;">Code</span>
                </div>

                <div class="card" style="padding:20px;cursor:default;transition:all 0.2s ease;"
                     onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)'"
                     onmouseleave="this.style.transform='';this.style.boxShadow=''">
                    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--gold);font-weight:700;margin-bottom:8px;">Newsletters</div>
                    <div style="font-weight:700;color:var(--ink);margin-bottom:4px;">Buttondown</div>
                    <div style="font-size:14px;color:var(--ink-light);margin-bottom:8px;">The easiest way to run a newsletter</div>
                    <span style="font-size:12px;padding:2px 8px;border-radius:999px;background:rgba(0,212,245,0.12);color:var(--accent);font-weight:600;">SaaS</span>
                </div>

                <div class="card" style="padding:20px;cursor:default;transition:all 0.2s ease;"
                     onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)'"
                     onmouseleave="this.style.transform='';this.style.boxShadow=''">
                    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#c678dd;font-weight:700;margin-bottom:8px;">Creative Tools</div>
                    <div style="font-weight:700;color:var(--ink);margin-bottom:4px;">Penpot</div>
                    <div style="font-size:14px;color:var(--ink-light);margin-bottom:8px;">Open-source design and prototyping</div>
                    <span style="font-size:12px;padding:2px 8px;border-radius:999px;background:var(--success-bg);color:var(--success-text);font-weight:600;">Code</span>
                </div>

                <div class="card" style="padding:20px;cursor:default;transition:all 0.2s ease;"
                     onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)'"
                     onmouseleave="this.style.transform='';this.style.boxShadow=''">
                    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--accent);font-weight:700;margin-bottom:8px;">Analytics</div>
                    <div style="font-weight:700;color:var(--ink);margin-bottom:4px;">Plausible Analytics</div>
                    <div style="font-size:14px;color:var(--ink-light);margin-bottom:8px;">Privacy-friendly analytics without cookies</div>
                    <span style="font-size:12px;padding:2px 8px;border-radius:999px;background:rgba(0,212,245,0.12);color:var(--accent);font-weight:600;">SaaS</span>
                </div>

                <div class="card" style="padding:20px;cursor:default;transition:all 0.2s ease;"
                     onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)'"
                     onmouseleave="this.style.transform='';this.style.boxShadow=''">
                    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--gold);font-weight:700;margin-bottom:8px;">Learning</div>
                    <div style="font-weight:700;color:var(--ink);margin-bottom:4px;">Exercism</div>
                    <div style="font-size:14px;color:var(--ink-light);margin-bottom:8px;">Learn programming with mentored exercises</div>
                    <span style="font-size:12px;padding:2px 8px;border-radius:999px;background:rgba(0,212,245,0.12);color:var(--accent);font-weight:600;">SaaS</span>
                </div>

            </div>
        </div>

    </div>

    <!-- ===== HOW IT WORKS (dark) ===== -->
    <div style="background:#1A2D4A;padding:64px 24px;margin-bottom:0;">
        <div style="max-width:800px;margin:0 auto;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3.5vw,30px);color:#fff;text-align:center;margin-bottom:24px;">
                One command. Your AI knows what exists.
            </h2>

            <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:var(--radius);padding:20px 24px;margin-bottom:16px;text-align:center;">
                <code style="font-family:var(--font-mono);font-size:clamp(13px,2vw,15px);color:var(--accent);word-break:break-all;">
                    claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
                </code>
            </div>

            <div style="text-align:center;margin-bottom:32px;">
                <p style="color:rgba(255,255,255,0.5);font-size:14px;margin-bottom:8px;">Or for Cursor / Windsurf:</p>
                <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:var(--radius);padding:16px 20px;display:inline-block;text-align:left;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:rgba(255,255,255,0.7);">
                        {{"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}}
                    </code>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));gap:20px;">
                <div style="padding:20px;border-radius:var(--radius);background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
                    <div style="font-weight:700;color:#fff;margin-bottom:6px;">Search the supply chain</div>
                    <div style="font-size:14px;color:rgba(255,255,255,0.55);line-height:1.5;">Your AI searches {tool_count}+ creations across {cat_count} categories. Every tool has an Agent Card with structured metadata at <code style="font-size:12px;color:var(--accent);">/cards/slug.json</code></div>
                </div>
                <div style="padding:20px;border-radius:var(--radius);background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
                    <div style="font-weight:700;color:#fff;margin-bottom:6px;">Build vs. buy analysis</div>
                    <div style="font-size:14px;color:rgba(255,255,255,0.55);line-height:1.5;">Should you build this or use what someone already made? AI-assisted evaluation with compatibility pairs that show what works together</div>
                </div>
                <div style="padding:20px;border-radius:var(--radius);background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
                    <div style="font-weight:700;color:#fff;margin-bottom:6px;">Dependency-aware</div>
                    <div style="font-size:14px;color:rgba(255,255,255,0.55);line-height:1.5;">Agents see how tools connect &mdash; compatibility pairs, stack analysis, and dependency graphs built in</div>
                </div>
                <div style="padding:20px;border-radius:var(--radius);background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
                    <div style="font-weight:700;color:#fff;margin-bottom:6px;">Works everywhere</div>
                    <div style="font-size:14px;color:rgba(255,255,255,0.55);line-height:1.5;">Claude Code, Cursor, Windsurf, VS Code Copilot. One install, every agent</div>
                </div>
            </div>
        </div>
    </div>

    <div style="max-width:800px;margin:0 auto;padding:0 24px;">

        <!-- ===== FOR EVERYONE ===== -->
        <div style="padding:56px 0;border-bottom:1px solid var(--border);">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3.5vw,30px);color:var(--ink);margin-bottom:24px;">
                For anyone looking for something
            </h2>
            <div style="display:flex;flex-direction:column;gap:20px;">
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">You don&rsquo;t have to build anything.</strong>
                    IndieStack isn&rsquo;t just for developers and makers. If you&rsquo;re looking for a flashcard app, a game engine,
                    a newsletter platform, invoicing software &mdash; the supply chain already has it. Browse and find something an indie creator has already shipped.
                </div>
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Ask your AI.</strong>
                    If you use Claude, Cursor, or any AI assistant with our MCP server, just tell it what you need.
                    &ldquo;Find me a privacy-friendly analytics tool.&rdquo; &ldquo;What indie games are built in Rust?&rdquo;
                    It searches IndieStack and brings back real options.
                </div>
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Support indie creators by using what they&rsquo;ve made.</strong>
                    Every click, every user, every recommendation tells the creator their work matters.
                    That&rsquo;s the whole point &mdash; connecting people with creations that deserve to be found.
                </div>
            </div>
        </div>

        <!-- ===== FOR PEOPLE WHO BUILD ===== -->
        <div style="padding:56px 0;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3.5vw,30px);color:var(--ink);margin-bottom:24px;">
                For people who build things
            </h2>
            <div style="display:flex;flex-direction:column;gap:20px;">
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Your AI checks what exists before building from scratch.</strong>
                    {tool_count}+ indie creations in the supply chain. Your agent queries it automatically &mdash;
                    if someone already built it, you&rsquo;ll know before you write a line of code.
                </div>
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Better than generated.</strong>
                    A creation maintained by someone who cares about the problem
                    beats AI-generated code with no maintenance plan.
                </div>
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Assembly at the right moment.</strong>
                    Not browsing a directory. Your AI finds the right component at the exact moment
                    you need it &mdash; mid-flow, mid-build &mdash; and shows you what pairs well with it.
                </div>
            </div>
        </div>

        <!-- ===== FOR PEOPLE WHO'VE BUILT SOMETHING ===== -->
        <div style="padding-bottom:56px;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3.5vw,30px);color:var(--ink);margin-bottom:24px;">
                For people who&rsquo;ve built something
            </h2>
            <div style="display:flex;flex-direction:column;gap:20px;">
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Become part of the supply chain.</strong>
                    Your creation gets recommended at the exact moment an agent needs a component &mdash;
                    assembled into workflows you never imagined.
                </div>
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Reach people you&rsquo;ll never meet.</strong>
                    12 GitHub stars or zero Twitter followers doesn&rsquo;t matter. If your creation
                    solves the problem, the AI recommends it.
                </div>
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">No algorithm to game.</strong>
                    No ads, no SEO, no pay-to-rank. List once, get recommended whenever
                    someone needs what you built.
                </div>
                <div style="line-height:1.7;color:var(--ink-light);font-size:16px;">
                    <strong style="color:var(--ink);">Your work outlives your marketing.</strong>
                    Recommended next month, next year, to agents you&rsquo;ll never interact with.
                    Your creation becomes a permanent building block in the indie supply chain.
                </div>
            </div>
        </div>

    </div>

    <!-- ===== WHERE THIS IS GOING ===== -->
    <div style="background:rgba(26,45,74,0.03);padding:64px 24px;">
        <div style="max-width:800px;margin:0 auto;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3.5vw,30px);color:var(--ink);margin-bottom:24px;">
                The creation explosion is coming
            </h2>
            <div style="color:var(--ink-light);font-size:16px;line-height:1.8;">
                <p style="margin-bottom:16px;">
                    AI is making creation accessible to everyone. A teacher who couldn&rsquo;t code last year
                    is shipping learning apps. A musician is building audio tools. A small business owner
                    is creating the exact software they need.
                </p>
                <p style="margin-bottom:16px;">
                    This explosion is just starting. As AI gets better, the number of indie creators
                    will grow by orders of magnitude. And every one of them will be using AI agents
                    that need a supply chain of existing components to build on.
                </p>
                <p style="margin-bottom:24px;">
                    IndieStack is building that supply chain now &mdash; {tool_count}+ creations indexed,
                    Agent Cards for every tool, compatibility pairs mapped. So when your agent starts a workflow,
                    it assembles from what exists instead of reinventing from scratch.
                </p>
                <p style="font-size:14px;color:var(--ink-muted);font-style:italic;">
                    Built by two uni students in Cardiff who see where this is going.
                </p>
            </div>
        </div>
    </div>

    <!-- ===== CTAs ===== -->
    <div style="max-width:800px;margin:0 auto;padding:56px 24px 80px;text-align:center;">
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:16px;">
            <a href="/#mcp-install" class="btn btn-lg btn-primary" style="font-size:16px;padding:14px 28px;">
                Install the MCP Server
            </a>
            <a href="/submit" class="btn btn-lg" style="font-size:16px;padding:14px 28px;border:2px solid var(--border);color:var(--ink);background:transparent;border-radius:var(--radius);text-decoration:none;font-weight:600;">
                Submit Your Creation
            </a>
            <a href="/explore" class="btn btn-lg" style="font-size:16px;padding:14px 28px;border:2px solid var(--border);color:var(--ink);background:transparent;border-radius:var(--radius);text-decoration:none;font-weight:600;">
                Browse the Catalog
            </a>
        </div>
    </div>
    '''

    # JSON-LD for agents and search engines
    json_ld = f'''<script type="application/ld+json">{{
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "What is IndieStack",
        "description": "IndieStack is the open-source supply chain for agentic workflows — {tool_count}+ indie creations with Agent Cards, discoverable via MCP server.",
        "url": "{BASE_URL}/what-is-indiestack",
        "mainEntity": {{
            "@type": "Organization",
            "name": "IndieStack",
            "url": "{BASE_URL}",
            "description": "Open-source supply chain for agentic workflows. {tool_count}+ indie creations with Agent Cards and compatibility pairs, discoverable via MCP server."
        }}
    }}</script>'''

    return HTMLResponse(page_shell(
        "What is IndieStack",
        body,
        user=user,
        description=f"IndieStack is the open-source supply chain for agentic workflows. {tool_count}+ indie creations — tools, games, utilities, newsletters — with Agent Cards, discoverable by Claude, Cursor, and Windsurf via MCP.",
        extra_head=json_ld,
        canonical="/what-is-indiestack",
    ))
