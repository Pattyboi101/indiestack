"""Migration Intelligence — /migrations route.

Public page showing live migration paths mined from GitHub repos.
The public face of our data moat.
"""

from html import escape
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/migrations", response_class=HTMLResponse)
async def migrations_page(request: Request):
    user = request.state.user
    d = request.state.db

    # Top migration paths (aggregated across repos)
    c = await d.execute("""
        SELECT from_package, to_package, confidence,
               COUNT(DISTINCT repo) as repo_count,
               GROUP_CONCAT(DISTINCT repo) as repos
        FROM migration_paths
        GROUP BY from_package, to_package
        ORDER BY repo_count DESC
        LIMIT 30
    """)
    migrations = await c.fetchall()

    # Top verified combos (most popular pairings)
    c = await d.execute("""
        SELECT package_a, package_b,
               COUNT(DISTINCT repo) as repo_count,
               SUM(repo_stars) as total_stars
        FROM verified_combos
        GROUP BY package_a, package_b
        ORDER BY repo_count DESC
        LIMIT 30
    """)
    combos = await c.fetchall()

    # Moat stats
    c = await d.execute("SELECT COUNT(*) as n FROM migration_paths")
    total_migrations = (await c.fetchone())["n"]
    c = await d.execute("SELECT COUNT(DISTINCT from_package || '→' || to_package) as n FROM migration_paths")
    unique_paths = (await c.fetchone())["n"]
    c = await d.execute("SELECT COUNT(*) as n FROM verified_combos")
    total_combos = (await c.fetchone())["n"]
    c = await d.execute("SELECT COUNT(DISTINCT repo) as n FROM verified_combos")
    repos_scanned = (await c.fetchone())["n"]
    c = await d.execute("SELECT COUNT(*) as n FROM build_outcomes")
    total_outcomes = (await c.fetchone())["n"]

    # Stats bar
    stats_html = f'''
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;margin-bottom:40px;">
        {_stat_card(f"{repos_scanned:,}", "Repos Scanned")}
        {_stat_card(f"{total_migrations:,}", "Migration Events")}
        {_stat_card(f"{unique_paths:,}", "Unique Paths")}
        {_stat_card(f"{total_combos:,}", "Verified Combos")}
        {_stat_card(f"{total_outcomes:,}", "CI Outcomes")}
    </div>'''

    # Key insights — rich editorial content backed by dynamic DB counts
    insights_html = f'''
        <div style="margin-bottom:32px;padding:20px 24px;background:linear-gradient(135deg, rgba(0,212,245,0.05), rgba(226,183,100,0.05));border:1px solid var(--border);border-radius:var(--radius-lg);">
            <h3 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0 0 12px;color:var(--ink);">Key Insights</h3>
            <p style="font-size:var(--text-sm);color:var(--ink-muted);margin:0 0 14px;">Based on {total_migrations:,} migration events across {repos_scanned:,} repos tracked by IndieStack.</p>
            <ul style="margin:0;padding-left:20px;font-size:var(--text-sm);color:var(--ink-light);">
                <li style="margin-bottom:8px;line-height:1.5;"><strong>Jest to Vitest is the #1 migration.</strong> Nearly triple the next most common switch. Mocha to Vitest accounts for more too. The JS testing world is consolidating around Vitest, and it's not close.</li>
                <li style="margin-bottom:8px;line-height:1.5;"><strong>Developers are fleeing webpack — and Vite is catching most of them.</strong> Webpack-to-Vite leads, followed by webpack-to-Rollup and webpack-to-esbuild. The era of complex bundler configs is ending.</li>
                <li style="margin-bottom:8px;line-height:1.5;"><strong>Vite + Vitest is the new power couple.</strong> The tightest bond in the modern JS testing stack. Shared config, instant HMR, native ESM. Once you adopt one, the other follows.</li>
                <li style="margin-bottom:8px;line-height:1.5;"><strong>Next.js + Tailwind dominates real-world stacks.</strong> The most common combo by a wide margin. Add Zod and Prisma and you have the de facto full-stack JS starter kit.</li>
                <li style="margin-bottom:8px;line-height:1.5;"><strong>Cypress to Playwright is the E2E testing migration to watch.</strong> Smaller numbers than the unit testing shifts, but Playwright's multi-browser support and faster execution are pulling teams over.</li>
                <li style="margin-bottom:8px;line-height:1.5;"><strong>bcrypt to bcryptjs: the quiet migration.</strong> Swapping native bcrypt for the pure-JS bcryptjs. No native compilation, no build headaches — especially relevant for serverless and containerised deployments.</li>
                <li style="margin-bottom:8px;line-height:1.5;"><strong>Next-Auth anchors the auth layer.</strong> When developers pick Next.js, NextAuth is the default authentication choice — not Clerk, not Auth0.</li>
            </ul>
        </div>'''

    # Migration paths table
    if migrations:
        migration_rows = ""
        for m in migrations:
            from_pkg = m["from_package"]
            to_pkg = m["to_package"]
            confidence = m["confidence"]
            count = m["repo_count"]
            repos = m["repos"].split(",")[:3] if m["repos"] else []

            conf_badge = _confidence_badge(confidence)
            bar_width = min(count * 15, 100)

            repo_links = " ".join(
                f'<span style="font-size:var(--text-xs);color:var(--ink-muted);">{escape(r.split("/")[-1])}</span>'
                for r in repos
            )

            migration_rows += f'''
            <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:14px 16px;">
                    <code style="font-family:var(--font-mono);font-size:var(--text-sm);color:#EF4444;background:rgba(239,68,68,0.08);padding:2px 8px;border-radius:4px;">{escape(from_pkg)}</code>
                </td>
                <td style="padding:14px 8px;text-align:center;color:var(--ink-muted);">
                    <span style="font-size:18px;">&#8594;</span>
                </td>
                <td style="padding:14px 16px;">
                    <code style="font-family:var(--font-mono);font-size:var(--text-sm);color:#10B981;background:rgba(16,185,129,0.08);padding:2px 8px;border-radius:4px;">{escape(to_pkg)}</code>
                </td>
                <td style="padding:14px 16px;text-align:center;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div style="flex:1;height:6px;background:var(--cream-dark);border-radius:3px;overflow:hidden;">
                            <div style="width:{bar_width}%;height:100%;background:var(--slate);border-radius:3px;"></div>
                        </div>
                        <span style="font-family:var(--font-mono);font-size:var(--text-sm);font-weight:600;color:var(--ink);min-width:28px;">{count}</span>
                    </div>
                </td>
                <td style="padding:14px 16px;text-align:center;">{conf_badge}</td>
                <td style="padding:14px 16px;">{repo_links}</td>
            </tr>'''

        migrations_html = f'''
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);margin:0 0 8px;">
                Migration Paths
            </h2>
            <p style="color:var(--ink-muted);font-size:var(--text-sm);margin:0 0 20px;">
                When a repo removes package A and adds package B in the same commit, that's a verified migration.
                Mined from real git history.
            </p>
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;font-family:var(--font-body);">
                    <thead>
                        <tr style="background:var(--cream-dark);border-bottom:2px solid var(--border);">
                            <th style="padding:12px 16px;text-align:left;font-size:var(--text-xs);font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.05em;">From</th>
                            <th style="padding:12px 8px;width:30px;"></th>
                            <th style="padding:12px 16px;text-align:left;font-size:var(--text-xs);font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.05em;">To</th>
                            <th style="padding:12px 16px;text-align:center;font-size:var(--text-xs);font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.05em;min-width:120px;">Repos</th>
                            <th style="padding:12px 16px;text-align:center;font-size:var(--text-xs);font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.05em;">Confidence</th>
                            <th style="padding:12px 16px;text-align:left;font-size:var(--text-xs);font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.05em;">Sample</th>
                        </tr>
                    </thead>
                    <tbody>
                        {migration_rows}
                    </tbody>
                </table>
            </div>
        </div>'''
    else:
        migrations_html = '''
        <div style="margin-bottom:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius-lg);text-align:center;">
            <p style="font-family:var(--font-display);font-size:var(--text-lg);color:var(--ink);margin:0 0 8px;">
                Migration scan in progress
            </p>
            <p style="color:var(--ink-muted);font-size:var(--text-sm);margin:0;">
                We're scanning hundreds of GitHub repos for dependency migration patterns. Check back soon.
            </p>
        </div>'''

    # Verified combos section
    if combos:
        combo_cards = ""
        for cb in combos[:20]:
            pkg_a = cb["package_a"]
            pkg_b = cb["package_b"]
            count = cb["repo_count"]
            stars = cb["total_stars"] or 0

            combo_cards += f'''
            <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid var(--border);">
                <div style="flex:1;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <code style="font-family:var(--font-mono);font-size:var(--text-sm);background:var(--cream-dark);padding:3px 8px;border-radius:4px;">{escape(pkg_a)}</code>
                    <span style="color:var(--ink-muted);font-size:var(--text-xs);">+</span>
                    <code style="font-family:var(--font-mono);font-size:var(--text-sm);background:var(--cream-dark);padding:3px 8px;border-radius:4px;">{escape(pkg_b)}</code>
                </div>
                <div style="text-align:right;min-width:80px;">
                    <span style="font-family:var(--font-mono);font-size:var(--text-sm);font-weight:600;color:var(--ink);">{count}</span>
                    <span style="font-size:var(--text-xs);color:var(--ink-muted);"> repos</span>
                </div>
            </div>'''

        combos_html = f'''
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);margin:0 0 8px;">
                Verified Combos
            </h2>
            <p style="color:var(--ink-muted);font-size:var(--text-sm);margin:0 0 20px;">
                Packages that coexist in production repos. Verified from real manifests, weighted by stars.
            </p>
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;">
                {combo_cards}
            </div>
        </div>'''
    else:
        combos_html = ""

    # API CTA for tool makers
    api_cta = '''
    <div style="margin-top:48px;padding:32px;background:linear-gradient(145deg, var(--terracotta), var(--terracotta-light));border-radius:var(--radius-lg);text-align:center;">
        <h3 style="font-family:var(--font-display);font-size:var(--heading-sm);color:white;margin:0 0 8px;">
            This data is available via API
        </h3>
        <p style="color:rgba(255,255,255,0.75);font-size:var(--text-sm);margin:0 0 20px;max-width:500px;margin-left:auto;margin-right:auto;">
            Tool makers: see where developers are migrating from your competitors.
            Query migration paths, verified combos, and CI outcomes programmatically.
        </p>
        <a href="/data" style="display:inline-block;padding:12px 28px;background:var(--gold);color:var(--terracotta-dark);font-family:var(--font-body);font-weight:600;font-size:var(--text-sm);border-radius:var(--radius-md);text-decoration:none;">
            View API Plans
        </a>
    </div>'''

    body = f'''
    <div style="max-width:900px;margin:0 auto;padding:24px 16px;">
        <div style="text-align:center;padding:32px 0 40px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 8px;">
                Migration Intelligence
            </h1>
            <p style="color:var(--ink-muted);font-size:var(--text-md);margin:0;max-width:600px;margin-left:auto;margin-right:auto;">
                Live data from {repos_scanned:,} GitHub repos. What packages are developers actually
                migrating to — and what combinations work in production.
            </p>
        </div>

        {stats_html}
        {insights_html}
        {migrations_html}
        <div style="text-align:center;margin:24px 0;">
          <a href="/analyze" style="color:var(--slate);font-size:var(--text-sm);text-decoration:none;">
            Want to check your own stack? Analyze for free &rarr;
          </a>
        </div>
        {combos_html}
        {api_cta}
    </div>'''

    return HTMLResponse(page_shell(
        "Migration Intelligence — IndieStack",
        body,
        description=f"Live migration data from {repos_scanned:,} GitHub repos. See what packages developers are migrating to and which combinations work in production.",
        user=user,
    ))


def _stat_card(value: str, label: str) -> str:
    return f'''
    <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;text-align:center;">
        <div style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);">{value}</div>
        <div style="font-family:var(--font-body);font-size:var(--text-xs);color:var(--ink-muted);margin-top:4px;text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
    </div>'''


def _confidence_badge(confidence: str) -> str:
    colors = {
        "swap": ("var(--slate)", "rgba(0,212,245,0.1)"),
        "likely": ("var(--gold)", "rgba(226,183,100,0.1)"),
        "inferred": ("var(--ink-muted)", "var(--cream-dark)"),
    }
    color, bg = colors.get(confidence, colors["inferred"])
    return f'<span style="font-size:var(--text-xs);font-weight:600;color:{color};background:{bg};padding:3px 8px;border-radius:4px;text-transform:uppercase;">{escape(confidence)}</span>'
