"""Design system and shared components for IndieStack."""

from html import escape

# ── Design Tokens ─────────────────────────────────────────────────────────

def design_tokens() -> str:
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --amber: #F59E0B;
            --amber-light: #FDE68A;
            --amber-dark: #D97706;
            --violet: #7C3AED;
            --violet-light: #C4B5FD;
            --violet-dark: #6D28D9;
            --stone-50: #FAFAF9;
            --stone-100: #F5F5F4;
            --stone-200: #E7E5E4;
            --stone-300: #D6D3D1;
            --stone-400: #A8A29E;
            --stone-500: #78716C;
            --stone-600: #57534E;
            --stone-700: #44403C;
            --stone-800: #292524;
            --stone-900: #1C1917;
            --font-display: 'Space Grotesk', sans-serif;
            --font-body: 'Inter', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --max-w: 1100px;
            --radius: 12px;
            --radius-sm: 8px;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: var(--font-body);
            background: var(--stone-50);
            color: var(--stone-800);
            line-height: 1.6;
            min-height: 100vh;
        }

        a { color: var(--amber-dark); text-decoration: none; }
        a:hover { color: var(--amber); }

        .container { max-width: var(--max-w); margin: 0 auto; padding: 0 24px; }

        /* ── Cards ─────────────────── */
        .card {
            background: white;
            border: 1px solid var(--stone-200);
            border-radius: var(--radius);
            padding: 24px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }

        .card-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        @media (max-width: 900px) { .card-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 600px) { .card-grid { grid-template-columns: 1fr; } }

        /* ── Buttons ───────────────── */
        .btn {
            display: inline-flex; align-items: center; gap: 8px;
            font-family: var(--font-body);
            font-weight: 600; font-size: 14px;
            padding: 10px 20px;
            border-radius: var(--radius-sm);
            border: none; cursor: pointer;
            transition: all 0.15s ease;
        }
        .btn-primary { background: var(--amber); color: white; }
        .btn-primary:hover { background: var(--amber-dark); color: white; }
        .btn-secondary { background: var(--stone-100); color: var(--stone-700); border: 1px solid var(--stone-200); }
        .btn-secondary:hover { background: var(--stone-200); }
        .btn-violet { background: var(--violet); color: white; }
        .btn-violet:hover { background: var(--violet-dark); color: white; }

        /* ── Tags ──────────────────── */
        .tag {
            display: inline-block;
            font-family: var(--font-mono);
            font-size: 12px; font-weight: 500;
            padding: 3px 10px;
            background: var(--stone-100);
            color: var(--stone-600);
            border-radius: 999px;
        }

        /* ── Upvote button ─────────── */
        .upvote-btn {
            display: inline-flex; flex-direction: column; align-items: center;
            gap: 2px; padding: 8px 14px;
            background: var(--stone-100); border: 1px solid var(--stone-200);
            border-radius: var(--radius-sm);
            cursor: pointer; transition: all 0.15s ease;
            font-family: var(--font-body); font-size: 13px; font-weight: 600;
            color: var(--stone-600);
        }
        .upvote-btn:hover, .upvote-btn.active {
            border-color: var(--violet);
            color: var(--violet);
            background: #F5F3FF;
        }
        .upvote-btn .arrow { font-size: 16px; line-height: 1; }

        /* ── Form elements ─────────── */
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block; font-weight: 600; font-size: 14px;
            color: var(--stone-700); margin-bottom: 6px;
        }
        .form-input, .form-textarea, .form-select {
            width: 100%; padding: 10px 14px;
            font-family: var(--font-body); font-size: 15px;
            border: 1px solid var(--stone-300); border-radius: var(--radius-sm);
            background: white; color: var(--stone-800);
            transition: border-color 0.15s ease;
        }
        .form-input:focus, .form-textarea:focus, .form-select:focus {
            outline: none; border-color: var(--amber);
            box-shadow: 0 0 0 3px rgba(245,158,11,0.15);
        }
        .form-textarea { resize: vertical; min-height: 100px; }

        /* ── Search ────────────────── */
        .search-box {
            position: relative; max-width: 600px; margin: 0 auto;
        }
        .search-box input {
            width: 100%; padding: 14px 20px 14px 48px;
            font-size: 16px; font-family: var(--font-body);
            border: 2px solid var(--stone-200); border-radius: 999px;
            background: white;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .search-box input:focus {
            outline: none; border-color: var(--amber);
            box-shadow: 0 0 0 4px rgba(245,158,11,0.12);
        }
        .search-box .search-icon {
            position: absolute; left: 18px; top: 50%; transform: translateY(-50%);
            font-size: 18px; color: var(--stone-400);
        }

        /* ── Alert / Flash ─────────── */
        .alert {
            padding: 14px 20px; border-radius: var(--radius-sm);
            font-size: 14px; font-weight: 500; margin-bottom: 20px;
        }
        .alert-success { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
        .alert-error { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
        .alert-info { background: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }

        /* ── Pagination ────────────── */
        .pagination {
            display: flex; gap: 8px; justify-content: center;
            margin-top: 32px;
        }
        .pagination a, .pagination span {
            display: inline-flex; align-items: center; justify-content: center;
            width: 40px; height: 40px; border-radius: var(--radius-sm);
            font-weight: 600; font-size: 14px;
            border: 1px solid var(--stone-200); color: var(--stone-600);
        }
        .pagination a:hover { background: var(--stone-100); }
        .pagination .active {
            background: var(--amber); color: white; border-color: var(--amber);
        }

        /* ── Utility ───────────────── */
        .text-center { text-align: center; }
        .mt-2 { margin-top: 8px; } .mt-4 { margin-top: 16px; } .mt-8 { margin-top: 32px; }
        .mb-2 { margin-bottom: 8px; } .mb-4 { margin-bottom: 16px; } .mb-8 { margin-bottom: 32px; }
        .text-muted { color: var(--stone-500); }
        .text-sm { font-size: 14px; }

        /* ── Verified Badge ────────── */
        .verified-badge {
            display: inline-flex; align-items: center; gap: 4px;
            font-size: 12px; font-weight: 600;
            color: var(--amber-dark);
            background: linear-gradient(135deg, #FEF3C7, #FDE68A);
            padding: 2px 10px; border-radius: 999px;
            border: 1px solid var(--amber);
        }
        .verified-badge svg { width: 14px; height: 14px; fill: var(--amber-dark); }
        .verified-card { border-color: var(--amber-light); background: linear-gradient(180deg, #FFFBEB 0%, white 40%); }
    </style>
    """


# ── Nav ───────────────────────────────────────────────────────────────────

def nav_html() -> str:
    return """
    <nav style="position:sticky;top:0;z-index:100;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
                background:rgba(250,250,249,0.82);border-bottom:1px solid var(--stone-200);">
        <div class="container" style="display:flex;align-items:center;justify-content:space-between;height:64px;">
            <a href="/" style="font-family:var(--font-display);font-size:22px;font-weight:700;color:var(--stone-900);
                              display:flex;align-items:center;gap:8px;">
                <span style="background:var(--amber);color:white;width:32px;height:32px;border-radius:8px;
                             display:inline-flex;align-items:center;justify-content:center;font-size:16px;">⚡</span>
                IndieStack
            </a>
            <div style="display:flex;align-items:center;gap:24px;font-size:14px;font-weight:500;">
                <a href="/" style="color:var(--stone-600);">Browse</a>
                <a href="/submit" style="color:var(--stone-600);">Submit Tool</a>
                <a href="/submit" class="btn btn-primary" style="padding:8px 16px;font-size:13px;">+ Add Your Tool</a>
            </div>
        </div>
    </nav>
    """


# ── Footer ────────────────────────────────────────────────────────────────

def footer_html() -> str:
    return """
    <footer style="margin-top:80px;padding:40px 0;border-top:1px solid var(--stone-200);
                   background:var(--stone-100);">
        <div class="container" style="display:flex;justify-content:space-between;align-items:center;
                                      flex-wrap:wrap;gap:16px;">
            <div>
                <span style="font-family:var(--font-display);font-weight:700;font-size:16px;
                             color:var(--stone-700);">⚡ IndieStack</span>
                <span style="color:var(--stone-400);font-size:14px;margin-left:12px;">
                    Discover indie SaaS tools built by solo developers
                </span>
            </div>
            <div style="font-size:13px;color:var(--stone-400);">
                Made with ☕ for the indie maker community
            </div>
        </div>
    </footer>
    """


# ── Tool Card ─────────────────────────────────────────────────────────────

def verified_badge_html() -> str:
    return """<span class="verified-badge"><svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>Verified</span>"""


def tool_card(tool: dict) -> str:
    name = escape(str(tool['name']))
    tagline = escape(str(tool['tagline']))
    slug = escape(str(tool['slug']))
    cat_name = escape(str(tool.get('category_name', '')))
    cat_slug = escape(str(tool.get('category_slug', '')))
    upvotes = int(tool.get('upvote_count', 0))
    tags = str(tool.get('tags', ''))
    is_verified = bool(tool.get('is_verified', 0))

    tag_html = ''
    if tags.strip():
        tag_list = [t.strip() for t in tags.split(',') if t.strip()][:3]
        tag_html = '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px;">'
        for t in tag_list:
            tag_html += f'<span class="tag">{escape(t)}</span>'
        tag_html += '</div>'

    badge = verified_badge_html() if is_verified else ''
    card_class = 'card verified-card' if is_verified else 'card'

    return f"""
    <div class="{card_class}" style="display:flex;gap:16px;">
        <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                <a href="/tool/{slug}" style="font-family:var(--font-display);font-size:17px;font-weight:600;
                                              color:var(--stone-900);">{name}</a>
                {badge}
            </div>
            <p style="color:var(--stone-500);font-size:14px;margin-top:4px;
                      overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{tagline}</p>
            <a href="/category/{cat_slug}" class="tag" style="margin-top:10px;display:inline-block;
                                                              font-family:var(--font-mono);">{cat_name}</a>
            {tag_html}
        </div>
        <button class="upvote-btn" onclick="upvote({tool['id']})" id="upvote-{tool['id']}">
            <span class="arrow">▲</span>
            <span id="count-{tool['id']}">{upvotes}</span>
        </button>
    </div>
    """


# ── Upvote Script ─────────────────────────────────────────────────────────

def upvote_js() -> str:
    return """
    <script>
    async function upvote(toolId) {
        const btn = document.getElementById('upvote-' + toolId);
        const countEl = document.getElementById('count-' + toolId);
        try {
            const res = await fetch('/api/upvote', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({tool_id: toolId})
            });
            const data = await res.json();
            if (data.ok) {
                countEl.textContent = data.count;
                btn.classList.toggle('active', data.upvoted);
            }
        } catch(e) { console.error(e); }
    }
    </script>
    """


# ── Page Shell ────────────────────────────────────────────────────────────

def page_shell(title: str, body: str, *, description: str = "", extra_head: str = "") -> str:
    desc = escape(description) if description else "Discover indie SaaS tools built by solo developers."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)} — IndieStack</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <meta name="description" content="{desc}">
    <meta property="og:title" content="{escape(title)} — IndieStack">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="website">
    {design_tokens()}
    {extra_head}
</head>
<body>
    {nav_html()}
    {body}
    {footer_html()}
    {upvote_js()}
</body>
</html>"""


# ── Pagination Helper ─────────────────────────────────────────────────────

def pagination_html(current: int, total_pages: int, base_url: str) -> str:
    if total_pages <= 1:
        return ""
    parts = ['<div class="pagination">']
    for p in range(1, total_pages + 1):
        if p == current:
            parts.append(f'<span class="active">{p}</span>')
        else:
            sep = "&amp;" if "?" in base_url else "?"
            parts.append(f'<a href="{base_url}{sep}page={p}">{p}</a>')
    parts.append('</div>')
    return ''.join(parts)
