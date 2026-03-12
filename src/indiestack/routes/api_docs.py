"""REST API documentation page for non-MCP agents and developers."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request):
    user = request.state.user
    try:
        db = request.state.db
        row = await (await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")).fetchone()
        tool_count = row['cnt'] if row else 880
    except Exception:
        tool_count = 880

    body = f'''
    <div class="container" style="padding:48px 24px;max-width:900px;margin:0 auto;">
        <div style="margin-bottom:48px;">
            <h1 style="font-family:var(--font-display);font-size:42px;color:var(--ink);margin-bottom:12px;">REST API</h1>
            <p style="color:var(--ink-muted);font-size:18px;max-width:700px;line-height:1.6;">
                Query IndieStack from any agent, script, or application. No API key required for read endpoints.
                All responses are JSON.
            </p>
            <div style="display:flex;gap:12px;margin-top:16px;flex-wrap:wrap;">
                <span style="font-size:13px;padding:6px 12px;background:rgba(34,197,94,0.1);color:var(--success, #22C55E);border-radius:999px;font-weight:600;">Base URL: https://indiestack.ai</span>
                <span style="font-size:13px;padding:6px 12px;background:rgba(0,212,245,0.1);color:var(--accent);border-radius:999px;font-weight:600;">JSON responses</span>
                <span style="font-size:13px;padding:6px 12px;background:var(--cream-dark);color:var(--ink-muted);border-radius:999px;font-weight:600;">No auth for reads</span>
            </div>
        </div>

        <!-- Search -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/tools/search</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">Search {tool_count}+ indie creations by keyword. Returns matching tools with metadata.</p>
                <table style="width:100%;font-size:13px;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">q</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Search query (required)</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">limit</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Max results (default: 20, max: 50)</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">offset</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Pagination offset (default: 0)</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">source_type</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Filter: "code" or "saas"</td>
                    </tr>
                </table>
                <div style="margin-top:12px;background:var(--cream-dark);border-radius:8px;padding:12px 16px;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--ink-light);">curl "https://indiestack.ai/api/tools/search?q=auth&limit=5"</code>
                </div>
            </div>
        </div>

        <!-- Tool Detail -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/tools/{{slug}}</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">Full details for a specific creation including integration snippets, similar tools, and companion suggestions.</p>
                <div style="margin-top:12px;background:var(--cream-dark);border-radius:8px;padding:12px 16px;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--ink-light);">curl "https://indiestack.ai/api/tools/simple-analytics"</code>
                </div>
            </div>
        </div>

        <!-- Categories -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/categories</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;">All 25 categories with slugs, descriptions, and tool counts.</p>
                <div style="margin-top:12px;background:var(--cream-dark);border-radius:8px;padding:12px 16px;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--ink-light);">curl "https://indiestack.ai/api/categories"</code>
                </div>
            </div>
        </div>

        <!-- New -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/new</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;">Recently added creations, newest first. Supports <code style="font-family:var(--font-mono);">limit</code> and <code style="font-family:var(--font-mono);">offset</code> params.</p>
            </div>
        </div>

        <!-- Tags -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/tags</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;">All tags sorted by popularity with tool counts.</p>
            </div>
        </div>

        <!-- Stacks -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/stacks</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;">Curated stacks for common use cases (SaaS starter, content platform, etc.).</p>
            </div>
        </div>

        <!-- Stack Builder -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/stack-builder</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">Build a complete indie stack from building blocks. Describe what you need and get matched creations.</p>
                <table style="width:100%;font-size:13px;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">needs</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Comma-separated needs: "auth,payments,analytics"</td>
                    </tr>
                </table>
                <div style="margin-top:12px;background:var(--cream-dark);border-radius:8px;padding:12px 16px;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--ink-light);">curl "https://indiestack.ai/api/stack-builder?needs=auth,payments,email"</code>
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/recommendations</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">Personalized recommendations based on search history. Requires API key.</p>
                <table style="width:100%;font-size:13px;border-collapse:collapse;">
                    <tr>
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">X-API-Key</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Your IndieStack API key (header)</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Tools Index -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:rgba(34,197,94,0.15);color:var(--success, #22C55E);border-radius:4px;">GET</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/tools/index.json</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;">Complete catalog index for prompt caching. Include once in your agent's context, reference forever.</p>
            </div>
        </div>

        <!-- Submit -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:var(--info-bg);color:var(--info-text);border-radius:4px;">POST</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/tools/submit</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">Submit a new creation programmatically. Requires API key.</p>
                <table style="width:100%;font-size:13px;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">name</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Creation name (required)</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">url</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Homepage URL (required)</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">tagline</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Short description</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">category</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Category slug</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:var(--ink-light);font-weight:600;">tags</td>
                        <td style="padding:8px 0;color:var(--ink-muted);">Comma-separated tags</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Citation Tracking -->
        <div style="margin-bottom:32px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
                <span style="font-size:12px;font-weight:700;padding:4px 8px;background:var(--info-bg);color:var(--info-text);border-radius:4px;">POST</span>
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">/api/cite</code>
            </div>
            <div style="padding:16px 20px;">
                <p style="color:var(--ink-muted);font-size:14px;">Track when an AI agent recommends a creation. Used by the MCP server automatically.</p>
            </div>
        </div>

        <!-- Agent Discovery -->
        <div style="margin-bottom:32px;padding:24px;background:var(--cream-dark);border-radius:var(--radius);">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:12px;">Agent Discovery</h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">Standard endpoints for AI agent integration.</p>
            <div style="display:flex;flex-direction:column;gap:12px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--accent);">/.well-known/agent-card.json</code>
                    <span style="color:var(--ink-muted);font-size:13px;">A2A agent discovery card</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--accent);">/llms.txt</code>
                    <span style="color:var(--ink-muted);font-size:13px;">Concise LLM context file</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--accent);">/llms-full.txt</code>
                    <span style="color:var(--ink-muted);font-size:13px;">Full catalog for LLM ingestion</span>
                </div>
            </div>
        </div>

        <!-- MCP CTA -->
        <div style="text-align:center;padding:32px 0;border-top:1px solid var(--border);margin-top:16px;">
            <h3 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">Want richer integration?</h3>
            <p style="color:var(--ink-muted);font-size:15px;margin-bottom:20px;">
                The MCP server gives AI agents 12 tools, 3 resources, and 5 prompts &mdash; much more than REST.
            </p>
            <div style="background:var(--cream-dark);border-radius:8px;padding:16px;max-width:600px;margin:0 auto 20px;">
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);">claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</code>
            </div>
            <a href="/what-is-indiestack" class="btn btn-secondary" style="padding:10px 20px;">Learn More</a>
        </div>
    </div>
    '''

    return HTMLResponse(page_shell(
        title="REST API Documentation | IndieStack",
        body=body,
        description=f"Query IndieStack's catalog of {tool_count}+ indie creations from any agent, script, or application. Search, browse, and submit via JSON API.",
        user=user,
        canonical="/api",
    ))
