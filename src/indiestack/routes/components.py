"""Design system and shared components for IndieStack."""

import json
from html import escape

from indiestack.category_icons import category_icon


# ---------------------------------------------------------------------------
# Design tokens — single source of truth
# ---------------------------------------------------------------------------


def design_tokens() -> str:
    return """
    <style>
    :root {
      /* Brand colors */
      --navy:       #1A2D4A;
      --cyan:       #00D4F5;
      --gold:       #E2B764;

      /* Semantic colors — light mode */
      --bg:         #FFFFFF;
      --bg-alt:     #F8F9FA;
      --bg-card:    #FFFFFF;
      --surface:    #F1F3F5;
      --border:     #E2E8F0;
      --border-subtle: #F0F4F8;
      --text:       #0F172A;
      --text-muted: #64748B;
      --text-faint: #94A3B8;
      --accent:     #0EA5E9;
      --accent-hover: #0284C7;
      --success:    #16A34A;
      --warning:    #D97706;
      --danger:     #991B1B;
      --tag-bg:     #EFF6FF;
      --tag-text:   #1D4ED8;

      /* Shadows */
      --shadow-sm:  0 1px 2px rgba(0,0,0,.06);
      --shadow-md:  0 4px 12px rgba(0,0,0,.08);
      --shadow-lg:  0 8px 24px rgba(0,0,0,.12);

      /* Radius */
      --r-sm:  6px;
      --r-md:  10px;
      --r-lg:  14px;
      --r-xl:  20px;
      --r-pill: 999px;

      /* Typography */
      --font-sans:  'DM Sans', system-ui, sans-serif;
      --font-serif: 'DM Serif Display', Georgia, serif;
      --font-mono:  'JetBrains Mono', 'Fira Code', monospace;
    }

    [data-theme="dark"] {
      --bg:         #0B1120;
      --bg-alt:     #111827;
      --bg-card:    #131D2E;
      --surface:    #1E2D42;
      --border:     #1E2D42;
      --border-subtle: #1A2840;
      --text:       #F0F4F8;
      --text-muted: #94A3B8;
      --text-faint: #64748B;
      --accent:     #38BDF8;
      --accent-hover: #7DD3FC;
      --success:    #4ADE80;
      --warning:    #FCD34D;
      --danger:     #FCA5A5;
      --tag-bg:     #1E2D42;
      --tag-text:   #7DD3FC;
    }

    *, *::before, *::after { box-sizing: border-box; }

    body {
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      margin: 0;
      line-height: 1.6;
    }

    h1, h2, h3 { font-family: var(--font-serif); }

    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    button, .btn {
      font-family: var(--font-sans);
      cursor: pointer;
    }

    input, textarea, select {
      font-family: var(--font-sans);
      background: var(--bg-card);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: var(--r-sm);
      padding: 8px 12px;
    }

    code, pre {
      font-family: var(--font-mono);
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px;
    }
    </style>
    """


# ---------------------------------------------------------------------------
# Google Fonts loader
# ---------------------------------------------------------------------------


def google_fonts() -> str:
    return """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Serif+Display:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">"""


# ---------------------------------------------------------------------------
# 7×7 pixel-art avatar
# ---------------------------------------------------------------------------


def pixel_icon_svg(seed: str = "indie", size: int = 32) -> str:
    """Generate a deterministic 7x7 pixel-art avatar SVG from a seed string."""
    import hashlib

    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    # Palette: 4 colors per icon (background + 3 foreground)
    palette_fg = [
        "#00D4F5", "#E2B764", "#4ADE80", "#F472B6", "#A78BFA",
        "#FB923C", "#34D399", "#60A5FA", "#F87171", "#FBBF24",
    ]
    bg_color = f"#{(h >> 80) % 0xFFFFFF:06x}"
    fg1 = palette_fg[(h >> 60) % len(palette_fg)]
    fg2 = palette_fg[(h >> 40) % len(palette_fg)]
    fg3 = palette_fg[(h >> 20) % len(palette_fg)]
    colors = [bg_color, fg1, fg2, fg3]

    # Generate 4×7 grid (left half), mirror for symmetry
    cell = size // 7
    pixels = []
    for row in range(7):
        for col in range(4):  # left half
            color_idx = (h >> (row * 4 + col)) % 4
            color = colors[color_idx]
            x = col * cell
            y = row * cell
            pixels.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}"/>')
            if col < 3:  # mirror (skip centre column)
                mirror_col = 6 - col
                mx = mirror_col * cell
                pixels.append(f'<rect x="{mx}" y="{y}" width="{cell}" height="{cell}" fill="{color}"/>')

    total = cell * 7
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {total} {total}" shape-rendering="crispEdges">'
        + "".join(pixels)
        + "</svg>"
    )


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


def nav_html(user=None, dark: bool = False) -> str:
    """Shared top navigation bar."""
    login_link = ""
    if user:
        username = escape(user.get("username") or user.get("name") or "Account")
        login_link = f"""
        <a href="/dashboard" style="color:var(--text-muted);font-size:14px;">{username}</a>
        <a href="/logout" class="btn-nav">Sign out</a>
        """
    else:
        login_link = '<a href="/login" class="btn-nav">Sign in with GitHub</a>'

    return f"""
    <nav style="border-bottom:1px solid var(--border);padding:12px 0;">
      <div class="container" style="display:flex;align-items:center;gap:24px;">
        <a href="/" style="font-family:var(--font-serif);font-size:20px;font-weight:700;
                           color:var(--text);text-decoration:none;">
          IndieStack
        </a>
        <div style="flex:1;"></div>
        <a href="/explore" style="color:var(--text-muted);font-size:14px;">Explore</a>
        <a href="/stacks" style="color:var(--text-muted);font-size:14px;">Stacks</a>
        <a href="/submit" style="color:var(--text-muted);font-size:14px;">Submit</a>
        <a href="/pricing" style="color:var(--text-muted);font-size:14px;">Pricing</a>
        {login_link}
      </div>
    </nav>
    """


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------


def footer_html() -> str:
    return """
    <footer style="border-top:1px solid var(--border);padding:32px 0;margin-top:64px;">
      <div class="container">
        <div style="display:flex;flex-wrap:wrap;gap:32px;justify-content:space-between;">
          <div>
            <div style="font-family:var(--font-serif);font-size:18px;font-weight:700;
                        margin-bottom:8px;">IndieStack</div>
            <div style="color:var(--text-muted);font-size:14px;max-width:260px;">
              The discovery layer for developer tools.
              Used by AI agents and the developers who build with them.
            </div>
          </div>
          <div style="display:flex;gap:48px;">
            <div>
              <div style="font-weight:600;margin-bottom:12px;font-size:14px;">Product</div>
              <div style="display:flex;flex-direction:column;gap:8px;font-size:14px;
                          color:var(--text-muted);">
                <a href="/explore" style="color:inherit;">Explore Tools</a>
                <a href="/stacks" style="color:inherit;">Tech Stacks</a>
                <a href="/submit" style="color:inherit;">Submit a Tool</a>
                <a href="/pricing" style="color:inherit;">Pricing</a>
              </div>
            </div>
            <div>
              <div style="font-weight:600;margin-bottom:12px;font-size:14px;">Resources</div>
              <div style="display:flex;flex-direction:column;gap:8px;font-size:14px;
                          color:var(--text-muted);">
                <a href="/api" style="color:inherit;">API Docs</a>
                <a href="https://pypi.org/project/indiestack/" style="color:inherit;"
                   target="_blank">MCP Server</a>
                <a href="/changelog" style="color:inherit;">Changelog</a>
              </div>
            </div>
          </div>
        </div>
        <div style="margin-top:32px;padding-top:24px;border-top:1px solid var(--border);
                    color:var(--text-muted);font-size:13px;
                    display:flex;justify-content:space-between;align-items:center;">
          <span>© 2024 IndieStack. Built for developers.</span>
          <span>
            <a href="/privacy" style="color:inherit;">Privacy</a> ·
            <a href="/terms" style="color:inherit;">Terms</a>
          </span>
        </div>
      </div>
    </footer>
    """


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------


def page_shell(
    content: str,
    title: str = "IndieStack — Developer Tool Discovery",
    description: str = "Discover the best developer tools, APIs, and libraries. Used by AI agents and developers building modern software.",
    user=None,
    dark: bool = False,
    og_image: str = "",
    canonical: str = "",
    extra_head: str = "",
    no_nav: bool = False,
    no_footer: bool = False,
    theme: str = "",
) -> str:
    """Wrap content in full HTML page with nav, footer, and design tokens."""
    theme_attr = f' data-theme="{escape(theme)}"' if theme else (
        ' data-theme="dark"' if dark else ""
    )
    og_img_tag = f'<meta property="og:image" content="{escape(og_image)}">\n' if og_image else ""
    canonical_tag = f'<link rel="canonical" href="{escape(canonical)}">\n' if canonical else ""

    nav = nav_html(user, dark=dark) if not no_nav else ""
    footer = footer_html() if not no_footer else ""

    return f"""<!DOCTYPE html>
<html lang="en"{theme_attr}>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:type" content="website">
  {og_img_tag}{canonical_tag}{google_fonts()}
  {design_tokens()}
  {extra_head}
</head>
<body>
  {nav}
  <main>
    {content}
  </main>
  {footer}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Upvote JS helpers
# ---------------------------------------------------------------------------


def upvote_js() -> str:
    """Inline JS for tool upvote button."""
    return """
    <script>
    async function upvoteTool(toolSlug, btn) {
      btn.disabled = true;
      try {
        const r = await fetch(`/api/upvote/${toolSlug}`, {method: 'POST'});
        const d = await r.json();
        if (d.upvoted !== undefined) {
          btn.classList.toggle('upvoted', d.upvoted);
          const countEl = btn.querySelector('.upvote-count');
          if (countEl) countEl.textContent = d.count;
        }
      } catch(e) { console.error(e); }
      finally { btn.disabled = false; }
    }
    </script>
    """


def stack_upvote_js() -> str:
    """Inline JS for stack upvote button."""
    return """
    <script>
    async function upvoteStack(stackId, btn) {
      btn.disabled = true;
      try {
        const r = await fetch(`/api/stacks/${stackId}/upvote`, {method: 'POST'});
        const d = await r.json();
        if (d.upvoted !== undefined) {
          btn.classList.toggle('upvoted', d.upvoted);
          const countEl = btn.querySelector('.upvote-count');
          if (countEl) countEl.textContent = d.count;
        }
      } catch(e) { console.error(e); }
      finally { btn.disabled = false; }
    }
    </script>
    """


# ---------------------------------------------------------------------------
# Tool card
# ---------------------------------------------------------------------------


def tool_card(
    tool: dict,
    show_category: bool = True,
    compact: bool = False,
    show_upvote: bool = True,
) -> str:
    """Render a tool card for use in grids and lists."""
    slug = escape(tool.get("slug", ""))
    name = escape(tool.get("name", "Unknown"))
    tagline = escape(tool.get("tagline") or "")
    tags_raw = (tool.get("tags") or "").split(",")
    tags = [escape(t.strip()) for t in tags_raw if t.strip()][:4]
    upvotes = tool.get("upvotes") or 0
    stars = tool.get("github_stars") or 0
    cat_name = escape(tool.get("category_name") or tool.get("cat_name") or "")
    cat_slug = tool.get("category_slug") or tool.get("cat_slug") or ""
    url = escape(tool.get("url") or "")
    source_type = tool.get("source_type") or "saas"
    pixel_icon = tool.get("pixel_icon") or ""
    is_verified = tool.get("is_verified") or False

    # Avatar: pixel icon > google favicon > fallback letter
    if pixel_icon:
        avatar = pixel_icon_svg(pixel_icon, size=36)
    elif url:
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        avatar = f'<img src="https://www.google.com/s2/favicons?domain={domain}&sz=32" width="28" height="28" style="border-radius:4px;" alt="">'
    else:
        avatar = f'<div style="width:28px;height:28px;background:var(--surface);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:var(--text-muted);">{name[0].upper() if name else "?"}</div>'

    # Tags HTML
    tags_html = "".join(
        f'<span style="display:inline-flex;align-items:center;padding:2px 8px;'
        f'border-radius:var(--r-pill);background:var(--tag-bg);color:var(--tag-text);'
        f'font-size:11px;font-family:var(--font-mono);">{t}</span>'
        for t in tags
    )

    # Stars/forks display
    stats_parts = []
    if stars >= 100:
        k_stars = f"{stars/1000:.1f}k" if stars >= 1000 else str(stars)
        stats_parts.append(f'<span style="color:var(--text-faint);font-size:12px;">★ {k_stars}</span>')
    if upvotes > 0:
        stats_parts.append(f'<span style="color:var(--text-faint);font-size:12px;">▲ {upvotes}</span>')
    stats_html = " · ".join(stats_parts)

    # Category badge
    cat_badge = ""
    if show_category and cat_name:
        icon = category_icon(cat_slug, 14)
        cat_badge = f"""
        <a href="/explore/{escape(cat_slug)}" style="display:inline-flex;align-items:center;
          gap:4px;padding:2px 8px;border-radius:var(--r-pill);
          background:var(--surface);color:var(--text-muted);
          font-size:11px;text-decoration:none;">
          {icon}{cat_name}
        </a>"""

    # Verified badge
    verified_badge = ""
    if is_verified:
        verified_badge = '<span title="Verified" style="color:var(--accent);font-size:12px;">✓</span>'

    # Source type pill
    source_pill = ""
    if source_type == "code":
        source_pill = '<span style="font-size:10px;padding:1px 6px;border-radius:var(--r-pill);background:var(--surface);color:var(--text-faint);">OSS</span>'

    padding = "16px" if compact else "20px"

    return f"""
    <a href="/tool/{slug}" style="display:block;text-decoration:none;
       background:var(--bg-card);border:1px solid var(--border);
       border-radius:var(--r-lg);padding:{padding};
       transition:box-shadow .15s,border-color .15s;
       box-shadow:var(--shadow-sm);"
       onmouseover="this.style.boxShadow='var(--shadow-md)';this.style.borderColor='var(--accent)';"
       onmouseout="this.style.boxShadow='var(--shadow-sm)';this.style.borderColor='var(--border)';">
      <div style="display:flex;align-items:flex-start;gap:12px;">
        <div style="flex-shrink:0;">{avatar}</div>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
            <span style="font-weight:600;color:var(--text);font-size:15px;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</span>
            {verified_badge}
            {source_pill}
          </div>
          <div style="color:var(--text-muted);font-size:13px;margin-bottom:8px;
                      display:-webkit-box;-webkit-line-clamp:2;
                      -webkit-box-orient:vertical;overflow:hidden;">{tagline}</div>
          <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;">
            {tags_html}
            {cat_badge}
            {stats_html}
          </div>
        </div>
      </div>
    </a>
    """


# ---------------------------------------------------------------------------
# Stack card
# ---------------------------------------------------------------------------


def stack_card(stack: dict, show_upvote: bool = True) -> str:
    """Render a tech stack card."""
    stack_id = stack.get("id", "")
    name = escape(stack.get("name") or "Untitled Stack")
    description = escape(stack.get("description") or "")
    tool_count = stack.get("tool_count") or 0
    upvotes = stack.get("upvotes") or 0
    author = escape(stack.get("author_name") or stack.get("username") or "Anonymous")

    upvote_btn = ""
    if show_upvote:
        upvote_btn = f"""
        <button onclick="upvoteStack('{stack_id}', this); event.preventDefault();"
                class="upvote-btn"
                style="display:inline-flex;align-items:center;gap:4px;
                       padding:4px 10px;border-radius:var(--r-pill);
                       border:1px solid var(--border);background:var(--bg-card);
                       color:var(--text-muted);font-size:13px;cursor:pointer;
                       transition:all .15s;">
          ▲ <span class="upvote-count">{upvotes}</span>
        </button>"""

    return f"""
    <a href="/stacks/{stack_id}" style="display:block;text-decoration:none;
       background:var(--bg-card);border:1px solid var(--border);
       border-radius:var(--r-lg);padding:20px;
       transition:box-shadow .15s,border-color .15s;box-shadow:var(--shadow-sm);"
       onmouseover="this.style.boxShadow='var(--shadow-md)';this.style.borderColor='var(--accent)';"
       onmouseout="this.style.boxShadow='var(--shadow-sm)';this.style.borderColor='var(--border)';">
      <div style="font-weight:600;font-size:16px;margin-bottom:6px;color:var(--text);">{name}</div>
      <div style="color:var(--text-muted);font-size:13px;margin-bottom:12px;
                  display:-webkit-box;-webkit-line-clamp:2;
                  -webkit-box-orient:vertical;overflow:hidden;">{description}</div>
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <div style="color:var(--text-faint);font-size:12px;">
          {tool_count} tools · by {author}
        </div>
        {upvote_btn}
      </div>
    </a>
    """


# ---------------------------------------------------------------------------
# Maker card
# ---------------------------------------------------------------------------


def maker_card(maker: dict) -> str:
    """Render a maker profile card."""
    slug = escape(maker.get("slug") or "")
    name = escape(maker.get("name") or "Unknown Maker")
    tagline = escape(maker.get("tagline") or "")
    tool_count = maker.get("tool_count") or 0
    is_pro = maker.get("is_pro") or False
    url = escape(maker.get("url") or "")

    pro_badge = ""
    if is_pro:
        pro_badge = '<span style="font-size:10px;padding:2px 7px;border-radius:var(--r-pill);background:var(--gold);color:#000;font-weight:600;">PRO</span>'

    favicon = ""
    if url:
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        favicon = f'<img src="https://www.google.com/s2/favicons?domain={domain}&sz=32" width="24" height="24" style="border-radius:4px;" alt="">'

    return f"""
    <a href="/maker/{slug}" style="display:block;text-decoration:none;
       background:var(--bg-card);border:1px solid var(--border);
       border-radius:var(--r-lg);padding:20px;
       transition:box-shadow .15s;box-shadow:var(--shadow-sm);"
       onmouseover="this.style.boxShadow='var(--shadow-md)';"
       onmouseout="this.style.boxShadow='var(--shadow-sm)';">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        {favicon}
        <span style="font-weight:600;font-size:15px;color:var(--text);">{name}</span>
        {pro_badge}
      </div>
      <div style="color:var(--text-muted);font-size:13px;margin-bottom:10px;">{tagline}</div>
      <div style="color:var(--text-faint);font-size:12px;">{tool_count} tools listed</div>
    </a>
    """


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


def pagination_html(page: int, total_pages: int, base_url: str, params: dict = None) -> str:
    """Render prev/next pagination controls."""
    if total_pages <= 1:
        return ""

    def page_url(p):
        q = {**(params or {}), "page": p}
        qs = "&".join(f"{k}={escape(str(v))}" for k, v in q.items())
        return f"{base_url}?{qs}"

    prev_btn = ""
    if page > 1:
        prev_btn = f'<a href="{page_url(page-1)}" class="btn-page">← Previous</a>'

    next_btn = ""
    if page < total_pages:
        next_btn = f'<a href="{page_url(page+1)}" class="btn-page">Next →</a>'

    page_info = f"Page {page} of {total_pages}"

    return f"""
    <div style="display:flex;align-items:center;justify-content:center;
                gap:16px;margin:32px 0;">
      <style>
      .btn-page {{
        display:inline-flex;align-items:center;padding:8px 16px;
        border-radius:var(--r-md);border:1px solid var(--border);
        background:var(--bg-card);color:var(--text-muted);
        font-size:14px;text-decoration:none;transition:all .15s;
      }}
      .btn-page:hover {{
        border-color:var(--accent);color:var(--accent);
        text-decoration:none;
      }}
      </style>
      {prev_btn}
      <span style="color:var(--text-faint);font-size:14px;">{page_info}</span>
      {next_btn}
    </div>
    """


# ---------------------------------------------------------------------------
# Search bar
# ---------------------------------------------------------------------------


def search_bar(query: str = "", placeholder: str = "Search developer tools...") -> str:
    """Render the main search bar."""
    q = escape(query)
    ph = escape(placeholder)
    return f"""
    <form method="get" action="/search" style="width:100%;">
      <div style="display:flex;gap:8px;">
        <input type="text" name="q" value="{q}" placeholder="{ph}"
               style="flex:1;padding:10px 16px;border-radius:var(--r-md);
                      border:1px solid var(--border);font-size:15px;
                      background:var(--bg-card);color:var(--text);"
               autocomplete="off">
        <button type="submit"
                style="padding:10px 20px;border-radius:var(--r-md);
                       background:var(--accent);color:#fff;
                       border:none;font-size:15px;font-weight:500;
                       cursor:pointer;transition:background .15s;"
                onmouseover="this.style.background='var(--accent-hover)'"
                onmouseout="this.style.background='var(--accent)'">
          Search
        </button>
      </div>
    </form>
    """


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------


def empty_state(title: str, subtitle: str = "", action_html: str = "") -> str:
    """Render a centered empty state block."""
    sub = f'<p style="color:var(--text-muted);margin:8px 0 0;">{escape(subtitle)}</p>' if subtitle else ""
    return f"""
    <div style="text-align:center;padding:64px 24px;">
      <div style="font-size:40px;margin-bottom:16px;">🔍</div>
      <h3 style="font-family:var(--font-serif);font-size:24px;margin:0;">{escape(title)}</h3>
      {sub}
      {action_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Alert / Banner
# ---------------------------------------------------------------------------


def alert_html(message: str, kind: str = "info") -> str:
    """Render an inline alert banner. kind: info | success | warning | error"""
    color_map = {
        "info":    ("#EFF6FF", "#1D4ED8", "#BFDBFE"),
        "success": ("#F0FDF4", "#15803D", "#BBF7D0"),
        "warning": ("#FFFBEB", "#92400E", "#FDE68A"),
        "error":   ("#FEF2F2", "#991B1B", "#FECACA"),
    }
    bg, text_color, border_color = color_map.get(kind, color_map["info"])
    return f"""
    <div style="padding:12px 16px;border-radius:var(--r-md);
                background:{bg};color:{text_color};border:1px solid {border_color};
                font-size:14px;margin-bottom:16px;">
      {escape(message)}
    </div>
    """


# ---------------------------------------------------------------------------
# Loading skeleton
# ---------------------------------------------------------------------------


def skeleton_cards(count: int = 6) -> str:
    """Render placeholder skeleton cards for loading states."""
    card = """
    <div style="background:var(--bg-card);border:1px solid var(--border);
                border-radius:var(--r-lg);padding:20px;">
      <div style="display:flex;gap:12px;">
        <div style="width:36px;height:36px;border-radius:6px;
                    background:var(--surface);flex-shrink:0;
                    animation:pulse 1.5s ease-in-out infinite;"></div>
        <div style="flex:1;">
          <div style="height:14px;background:var(--surface);border-radius:4px;
                      width:60%;margin-bottom:8px;
                      animation:pulse 1.5s ease-in-out infinite;"></div>
          <div style="height:12px;background:var(--surface);border-radius:4px;
                      width:90%;margin-bottom:4px;
                      animation:pulse 1.5s ease-in-out infinite;"></div>
          <div style="height:12px;background:var(--surface);border-radius:4px;
                      width:75%;animation:pulse 1.5s ease-in-out infinite;"></div>
        </div>
      </div>
    </div>"""
    style = "<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}</style>"
    return style + "".join(card for _ in range(count))


# ---------------------------------------------------------------------------
# Analytics wall (claim-to-reveal)
# ---------------------------------------------------------------------------


def analytics_wall_blurred(
    total_queries: int,
    unique_platforms: int,
    queries_7d: int,
    tool_slug: str,
    is_maker: bool = False,
) -> str:
    """Render the blurred analytics teaser for unclaimed tools."""
    total = total_queries or 0
    plats = unique_platforms or 0
    q7d = queries_7d or 0

    if is_maker:
        cta = f"""
        <a href="/dashboard"
           style="display:inline-flex;align-items:center;gap:8px;
                  padding:10px 20px;border-radius:var(--r-md);
                  background:var(--accent);color:#fff;
                  font-size:14px;font-weight:500;text-decoration:none;
                  transition:background .15s;"
           onmouseover="this.style.background='var(--accent-hover)'"
           onmouseout="this.style.background='var(--accent)'">
          View Full Analytics
        </a>"""
    else:
        cta = f"""
        <a href="/maker/claim/{escape(tool_slug)}"
           style="display:inline-flex;align-items:center;gap:8px;
                  padding:10px 20px;border-radius:var(--r-md);
                  background:var(--accent);color:#fff;
                  font-size:14px;font-weight:500;text-decoration:none;
                  transition:background .15s;"
           onmouseover="this.style.background='var(--accent-hover)'"
           onmouseout="this.style.background='var(--accent)'">
          Claim this tool to see full analytics
        </a>"""

    return f"""
    <div style="position:relative;border-radius:var(--r-lg);
                border:1px solid var(--border);overflow:hidden;">
      <!-- Blurred stats preview -->
      <div style="padding:24px;filter:blur(4px);user-select:none;pointer-events:none;">
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
          <div style="text-align:center;">
            <div style="font-size:28px;font-weight:700;color:var(--accent);">{total}</div>
            <div style="font-size:12px;color:var(--text-muted);">total agent queries</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:28px;font-weight:700;color:var(--accent);">{plats}</div>
            <div style="font-size:12px;color:var(--text-muted);">platforms</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:28px;font-weight:700;color:var(--accent);">{q7d}</div>
            <div style="font-size:12px;color:var(--text-muted);">queries last 7d</div>
          </div>
        </div>
      </div>
      <!-- Overlay CTA -->
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;
                  align-items:center;justify-content:center;
                  background:rgba(var(--bg-card-rgb, 255,255,255),.85);
                  backdrop-filter:blur(2px);gap:12px;">
        <div style="font-weight:600;font-size:15px;">AI agents are recommending this tool</div>
        <div style="color:var(--text-muted);font-size:13px;">
          See which agents, what queries, and how often
        </div>
        {cta}
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Breadcrumb
# ---------------------------------------------------------------------------


def breadcrumb(crumbs: list[tuple[str, str]]) -> str:
    """Render a breadcrumb trail. crumbs = [(label, url), ...] last item has no link."""
    parts = []
    for i, (label, url) in enumerate(crumbs):
        if i < len(crumbs) - 1:
            parts.append(f'<a href="{escape(url)}" style="color:var(--text-muted);">{escape(label)}</a>')
        else:
            parts.append(f'<span style="color:var(--text-faint);">{escape(label)}</span>')
    sep = ' <span style="color:var(--border);">›</span> '
    return f'<nav style="font-size:13px;margin-bottom:16px;">{sep.join(parts)}</nav>'


# ---------------------------------------------------------------------------
# Tag cloud
# ---------------------------------------------------------------------------


def tag_cloud(tags: list[str], base_url: str = "/search") -> str:
    """Render a tag cloud with links."""
    if not tags:
        return ""
    items = "".join(
        f'<a href="{base_url}?q={escape(t)}" '
        f'style="display:inline-flex;align-items:center;padding:4px 10px;'
        f'border-radius:var(--r-pill);background:var(--tag-bg);color:var(--tag-text);'
        f'font-size:12px;font-family:var(--font-mono);text-decoration:none;'
        f'transition:opacity .15s;" onmouseover="this.style.opacity=\'0.8\'" '
        f'onmouseout="this.style.opacity=\'1\'">#{escape(t)}</a>'
        for t in tags
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{items}</div>'


# ---------------------------------------------------------------------------
# Stat badge
# ---------------------------------------------------------------------------


def stat_badge(label: str, value, icon: str = "") -> str:
    """Render a single stat badge (label + value)."""
    icon_html = f'<span style="margin-right:4px;">{icon}</span>' if icon else ""
    return f"""
    <div style="display:inline-flex;flex-direction:column;align-items:center;
                padding:12px 20px;border-radius:var(--r-md);
                background:var(--surface);border:1px solid var(--border);">
      <div style="font-size:22px;font-weight:700;color:var(--accent);">
        {icon_html}{escape(str(value))}
      </div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">{escape(label)}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Modal helper
# ---------------------------------------------------------------------------


def modal_html(modal_id: str, title: str, body: str, footer: str = "") -> str:
    """Render a hidden modal dialog with open/close JS."""
    footer_html_inner = f'<div style="padding:16px 24px;border-top:1px solid var(--border);">{footer}</div>' if footer else ""
    return f"""
    <div id="{escape(modal_id)}" style="display:none;position:fixed;inset:0;z-index:9999;
         background:rgba(0,0,0,.5);align-items:center;justify-content:center;">
      <div style="background:var(--bg-card);border-radius:var(--r-lg);
                  border:1px solid var(--border);max-width:520px;width:90%;">
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:16px 24px;border-bottom:1px solid var(--border);">
          <h3 style="margin:0;font-size:18px;">{escape(title)}</h3>
          <button onclick="document.getElementById('{escape(modal_id)}').style.display='none'"
                  style="background:none;border:none;font-size:20px;cursor:pointer;
                         color:var(--text-muted);padding:0;line-height:1;">×</button>
        </div>
        <div style="padding:24px;">{body}</div>
        {footer_html_inner}
      </div>
    </div>
    <script>
    function openModal_{escape(modal_id.replace('-','_'))}() {{
      document.getElementById('{escape(modal_id)}').style.display='flex';
    }}
    function closeModal_{escape(modal_id.replace('-','_'))}() {{
      document.getElementById('{escape(modal_id)}').style.display='none';
    }}
    </script>
    """


# ---------------------------------------------------------------------------
# Copy-to-clipboard button
# ---------------------------------------------------------------------------


def copy_btn(text: str, label: str = "Copy") -> str:
    """Render a copy-to-clipboard button."""
    safe_text = text.replace('"', '&quot;').replace("'", "\\'").replace("\n", "\\n")
    return f"""
    <button onclick="
      navigator.clipboard.writeText('{safe_text}').then(() => {{
        this.textContent = 'Copied!';
        setTimeout(() => this.textContent = '{escape(label)}', 1500);
      }});
    " style="padding:6px 12px;border-radius:var(--r-sm);
             border:1px solid var(--border);background:var(--bg-card);
             color:var(--text-muted);font-size:12px;cursor:pointer;
             font-family:var(--font-mono);transition:all .15s;"
       onmouseover="this.style.borderColor='var(--accent)'"
       onmouseout="this.style.borderColor='var(--border)'">
      {escape(label)}
    </button>
    """


# ---------------------------------------------------------------------------
# Install block (code + copy)
# ---------------------------------------------------------------------------


def install_block(command: str, label: str = "Install") -> str:
    """Render a styled install command block with copy button."""
    if not command:
        return ""
    safe_cmd = escape(command)
    return f"""
    <div style="border-radius:var(--r-md);border:1px solid var(--border);
                background:var(--surface);overflow:hidden;">
      <div style="padding:8px 12px;border-bottom:1px solid var(--border);
                  font-size:12px;color:var(--text-faint);font-family:var(--font-mono);">
        {escape(label)}
      </div>
      <div style="display:flex;align-items:center;gap:8px;padding:10px 12px;min-width:0;">
        <code style="flex:1;min-width:0;font-size:13px;font-family:var(--font-mono);
                     color:var(--text);overflow-x:auto;white-space:nowrap;
                     scrollbar-width:thin;">{safe_cmd}</code>
        {copy_btn(command)}
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Pro upgrade CTA
# ---------------------------------------------------------------------------


def pro_upgrade_cta(feature_name: str = "this feature") -> str:
    """Render a Pro upgrade prompt."""
    return f"""
    <div style="border-radius:var(--r-lg);border:1px solid var(--gold);
                background:linear-gradient(135deg,rgba(226,183,100,.08),rgba(226,183,100,.02));
                padding:24px;text-align:center;">
      <div style="font-size:24px;margin-bottom:12px;">⚡</div>
      <h3 style="margin:0 0 8px;font-size:18px;">Unlock {escape(feature_name)}</h3>
      <p style="color:var(--text-muted);font-size:14px;margin:0 0 16px;">
        Get agent citation analytics, search query data, verified badge,
        and priority placement for $19/mo.
      </p>
      <a href="/pricing"
         style="display:inline-flex;align-items:center;padding:10px 24px;
                border-radius:var(--r-md);background:var(--gold);color:#000;
                font-weight:600;font-size:14px;text-decoration:none;
                transition:opacity .15s;"
         onmouseover="this.style.opacity='0.85'"
         onmouseout="this.style.opacity='1'">
        Upgrade to Pro — $19/mo
      </a>
    </div>
    """


# ---------------------------------------------------------------------------
# Section header
# ---------------------------------------------------------------------------


def section_header(title: str, subtitle: str = "", action_html: str = "") -> str:
    """Render a section heading with optional subtitle and action."""
    sub = f'<p style="color:var(--text-muted);margin:8px 0 0;font-size:15px;">{escape(subtitle)}</p>' if subtitle else ""
    action = f'<div>{action_html}</div>' if action_html else ""
    return f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;
                margin-bottom:24px;">
      <div>
        <h2 style="font-family:var(--font-serif);font-size:26px;margin:0;">{escape(title)}</h2>
        {sub}
      </div>
      {action}
    </div>
    """


# ---------------------------------------------------------------------------
# Category grid
# ---------------------------------------------------------------------------


def category_grid(categories: list[dict], cols: int = 4) -> str:
    """Render a grid of category cards."""
    cards = ""
    for cat in categories:
        slug = escape(cat.get("slug") or "")
        name = escape(cat.get("name") or "")
        count = cat.get("tool_count") or 0
        icon = category_icon(cat.get("slug") or "", 20)
        cards += f"""
        <a href="/explore/{slug}" style="display:flex;align-items:center;gap:10px;
           padding:14px 16px;border-radius:var(--r-md);
           background:var(--bg-card);border:1px solid var(--border);
           text-decoration:none;transition:all .15s;"
           onmouseover="this.style.borderColor='var(--accent)';this.style.boxShadow='var(--shadow-sm)';"
           onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow='none';">
          <span style="color:var(--accent);">{icon}</span>
          <div>
            <div style="font-weight:500;font-size:14px;color:var(--text);">{name}</div>
            <div style="font-size:12px;color:var(--text-faint);">{count} tools</div>
          </div>
        </a>"""

    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:12px;">{cards}</div>'


# ---------------------------------------------------------------------------
# Comparison table helper
# ---------------------------------------------------------------------------


def comparison_table(tools: list[dict], fields: list[tuple[str, str]]) -> str:
    """Render a comparison table. fields = [(key, label), ...]."""
    header_cells = "".join(
        f'<th style="padding:10px 16px;text-align:left;font-weight:600;
           font-size:13px;color:var(--text-muted);border-bottom:1px solid var(--border);
           background:var(--surface);">\n          {escape(label)}\n        </th>'
        for _, label in fields
    )
    rows = ""
    for tool in tools:
        cells = "".join(
            f'<td style="padding:10px 16px;font-size:14px;border-bottom:1px solid var(--border-subtle);">{escape(str(tool.get(key) or "—"))}</td>'
            for key, _ in fields
        )
        rows += f"<tr>{cells}</tr>"

    return f"""
    <div style="overflow-x:auto;border-radius:var(--r-lg);border:1px solid var(--border);">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


# ---------------------------------------------------------------------------
# Inline toast notification
# ---------------------------------------------------------------------------


def toast_js() -> str:
    """Include once per page. Provides window.showToast(message, kind)."""
    return """
    <div id="toast-container" style="position:fixed;bottom:24px;right:24px;
         z-index:99999;display:flex;flex-direction:column;gap:8px;
         pointer-events:none;"></div>
    <script>
    function showToast(message, kind='info') {
      const colors = {
        info:    {bg:'#1D4ED8', text:'#fff'},
        success: {bg:'#16A34A', text:'#fff'},
        warning: {bg:'#D97706', text:'#fff'},
        error:   {bg:'#DC2626', text:'#fff'},
      };
      const c = colors[kind] || colors.info;
      const el = document.createElement('div');
      el.style.cssText = `
        padding:10px 16px;border-radius:8px;
        background:${c.bg};color:${c.text};
        font-size:14px;font-family:var(--font-sans,sans-serif);
        box-shadow:0 4px 12px rgba(0,0,0,.2);
        opacity:0;transition:opacity .2s;pointer-events:none;
      `;
      el.textContent = message;
      document.getElementById('toast-container').appendChild(el);
      requestAnimationFrame(() => { el.style.opacity = '1'; });
      setTimeout(() => {
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 200);
      }, 3000);
    }
    </script>
    """


# ---------------------------------------------------------------------------
# Dark mode toggle
# ---------------------------------------------------------------------------


def dark_mode_toggle() -> str:
    """Render a dark/light mode toggle button with persistent localStorage."""
    return """
    <button id="theme-toggle" onclick="toggleTheme()"
            style="background:none;border:1px solid var(--border);
                   border-radius:var(--r-pill);padding:6px 12px;
                   color:var(--text-muted);font-size:13px;cursor:pointer;
                   transition:all .15s;
                   display:flex;align-items:center;gap:6px;"
            onmouseover="this.style.borderColor='var(--accent)'"
            onmouseout="this.style.borderColor='var(--border)'">
      <span id="theme-icon">🌙</span>
      <span id="theme-label">Dark</span>
    </button>
    <script>
    (function() {
      const saved = localStorage.getItem('theme');
      if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
        updateToggleUI(saved);
      }
    })();
    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      updateToggleUI(next);
    }
    function updateToggleUI(theme) {
      const icon = document.getElementById('theme-icon');
      const label = document.getElementById('theme-label');
      if (!icon || !label) return;
      if (theme === 'dark') {
        icon.textContent = '☀️';
        label.textContent = 'Light';
      } else {
        icon.textContent = '🌙';
        label.textContent = 'Dark';
      }
    }
    </script>
    """


# ---------------------------------------------------------------------------
# JSON-LD structured data helpers
# ---------------------------------------------------------------------------


def jsonld_software_app(tool: dict) -> str:
    """Emit JSON-LD SoftwareApplication schema for a tool."""
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": tool.get("name") or "",
        "description": tool.get("description") or tool.get("tagline") or "",
        "url": tool.get("url") or "",
        "applicationCategory": "DeveloperApplication",
    }
    if tool.get("github_stars"):
        data["interactionStatistic"] = {
            "@type": "InteractionCounter",
            "interactionType": "https://schema.org/LikeAction",
            "userInteractionCount": tool["github_stars"],
        }
    raw = json.dumps(data)
    safe = raw.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return f'<script type="application/ld+json">{safe}</script>'


def jsonld_breadcrumb(crumbs: list[tuple[str, str]], base_url: str = "https://indiestack.ai") -> str:
    """Emit JSON-LD BreadcrumbList schema."""
    items = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "name": label,
            "item": base_url + url,
        }
        for i, (label, url) in enumerate(crumbs)
    ]
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    raw = json.dumps(data)
    safe = raw.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return f'<script type="application/ld+json">{safe}</script>'


# ---------------------------------------------------------------------------
# Responsive grid helper
# ---------------------------------------------------------------------------


def responsive_grid(items_html: list[str], min_col_width: str = "280px") -> str:
    """Wrap items in a CSS grid that auto-fills columns."""
    items = "".join(items_html)
    return f"""
    <div style="display:grid;
                grid-template-columns:repeat(auto-fill,minmax({min_col_width},1fr));
                gap:16px;">
      {items}
    </div>
    """


# ---------------------------------------------------------------------------
# Tabs component
# ---------------------------------------------------------------------------


def tabs_html(tabs: list[tuple[str, str, str]], active_id: str) -> str:
    """Render tab navigation. tabs = [(id, label, href), ...]"""
    items = ""
    for tab_id, label, href in tabs:
        is_active = tab_id == active_id
        style = (
            "padding:8px 16px;border-radius:var(--r-md);font-size:14px;"
            "font-weight:500;text-decoration:none;transition:all .15s;"
        )
        if is_active:
            style += "background:var(--accent);color:#fff;"
        else:
            style += "color:var(--text-muted);"
        items += f'<a href="{escape(href)}" style="{style}">{escape(label)}</a>'

    return f'<div style="display:flex;gap:4px;padding:4px;background:var(--surface);border-radius:var(--r-lg);margin-bottom:24px;">{items}</div>'


# ---------------------------------------------------------------------------
# Pill / badge
# ---------------------------------------------------------------------------


def pill(text: str, color: str = "accent") -> str:
    """Render a status pill/badge."""
    color_map = {
        "accent":  ("var(--tag-bg)",   "var(--tag-text)"),
        "success": ("#F0FDF4",          "#16A34A"),
        "warning": ("#FFFBEB",          "#D97706"),
        "error":   ("#FEF2F2",          "#DC2626"),
        "muted":   ("var(--surface)",   "var(--text-muted)"),
        "gold":    ("rgba(226,183,100,.15)", "#E2B764"),
    }
    bg, tc = color_map.get(color, color_map["accent"])
    return (
        f'<span style="display:inline-flex;align-items:center;padding:2px 8px;'
        f'border-radius:var(--r-pill);background:{bg};color:{tc};'
        f'font-size:11px;font-weight:500;">{escape(text)}</span>'
    )


# ---------------------------------------------------------------------------
# Vertical stack / row helpers
# ---------------------------------------------------------------------------


def vstack(*items: str, gap: int = 16) -> str:
    """Vertically stack HTML blocks with a gap."""
    return f'<div style="display:flex;flex-direction:column;gap:{gap}px;">{" ".join(items)}</div>'


def hstack(*items: str, gap: int = 16, align: str = "center") -> str:
    """Horizontally stack HTML blocks."""
    return f'<div style="display:flex;align-items:{align};gap:{gap}px;">{" ".join(items)}</div>'


# ---------------------------------------------------------------------------
# Divider
# ---------------------------------------------------------------------------


def divider(margin: str = "24px 0") -> str:
    return f'<hr style="border:none;border-top:1px solid var(--border);margin:{margin};">'


# ---------------------------------------------------------------------------
# Avatar (user)
# ---------------------------------------------------------------------------


def user_avatar(user: dict, size: int = 32) -> str:
    """Render a user avatar: GitHub avatar or pixel art fallback."""
    name = user.get("name") or user.get("username") or "?"
    avatar_url = user.get("avatar_url") or ""
    if avatar_url:
        return f'<img src="{escape(avatar_url)}" width="{size}" height="{size}" style="border-radius:50%;" alt="{escape(name)}">'
    return pixel_icon_svg(name, size=size)


# ---------------------------------------------------------------------------
# Keyboard shortcut hint
# ---------------------------------------------------------------------------


def kbd(key: str) -> str:
    """Render a keyboard shortcut badge."""
    return (
        f'<kbd style="display:inline-flex;align-items:center;padding:2px 6px;'
        f'border-radius:4px;border:1px solid var(--border);'
        f'background:var(--surface);font-family:var(--font-mono);'
        f'font-size:11px;color:var(--text-muted);">{escape(key)}</kbd>'
    )


# ---------------------------------------------------------------------------
# Tool grid (convenience wrapper)
# ---------------------------------------------------------------------------


def tool_grid(tools: list[dict], cols: int = 3, **card_kwargs) -> str:
    """Render a responsive grid of tool cards."""
    if not tools:
        return empty_state("No tools found", "Try a different search or category.")
    cards = "".join(tool_card(t, **card_kwargs) for t in tools)
    return f"""
    <div style="display:grid;
                grid-template-columns:repeat({cols},1fr);
                gap:16px;
                @media(max-width:900px){{grid-template-columns:repeat(2,1fr);}}
                @media(max-width:600px){{grid-template-columns:1fr;}}">
      {cards}
    </div>
    """


# ---------------------------------------------------------------------------
# Notification dot
# ---------------------------------------------------------------------------


def notification_dot(count: int = 0) -> str:
    """Render a red notification dot, optionally with a count."""
    if count <= 0:
        return ""
    label = str(count) if count < 100 else "99+"
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'min-width:18px;height:18px;padding:0 4px;'
        f'border-radius:var(--r-pill);background:#DC2626;color:#fff;'
        f'font-size:10px;font-weight:700;">{label}</span>'
    )


# ---------------------------------------------------------------------------
# Spinner
# ---------------------------------------------------------------------------


def spinner(size: int = 20, color: str = "var(--accent)") -> str:
    """Render a CSS spinner."""
    return f"""
    <div style="width:{size}px;height:{size}px;border-radius:50%;
                border:2px solid {color};border-top-color:transparent;
                animation:spin .7s linear infinite;
                display:inline-block;"
         aria-label="Loading">
    </div>
    <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
    """


# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------


def progress_bar(value: float, max_val: float = 100, color: str = "var(--accent)",
                 height: int = 6, label: str = "") -> str:
    """Render a horizontal progress bar."""
    pct = min(max(value / max_val * 100 if max_val else 0, 0), 100)
    label_html = f'<span style="font-size:12px;color:var(--text-muted);margin-left:8px;">{escape(label)}</span>' if label else ""
    return f"""
    <div style="display:flex;align-items:center;">
      <div style="flex:1;height:{height}px;background:var(--surface);border-radius:var(--r-pill);overflow:hidden;">
        <div style="height:100%;width:{pct:.1f}%;background:{color};border-radius:var(--r-pill);
                    transition:width .3s ease;"></div>
      </div>
      {label_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Inline code snippet
# ---------------------------------------------------------------------------


def code_block(code: str, language: str = "") -> str:
    """Render a styled code block."""
    lang_label = f'<div style="padding:6px 12px;border-bottom:1px solid var(--border);font-size:11px;color:var(--text-faint);font-family:var(--font-mono);">\n      {escape(language)}\n    </div>' if language else ""
    return f"""
    <div style="border-radius:var(--r-md);border:1px solid var(--border);
                background:var(--surface);overflow:hidden;">
      {lang_label}
      <pre style="margin:0;padding:16px;overflow-x:auto;
                  font-family:var(--font-mono);font-size:13px;
                  color:var(--text);line-height:1.6;"><code>{escape(code)}</code></pre>
    </div>
    """


# ---------------------------------------------------------------------------
# Feature list
# ---------------------------------------------------------------------------


def feature_list(features: list[str], icon: str = "✓", color: str = "var(--success)") -> str:
    """Render a bulleted feature list."""
    items = "".join(
        f'<li style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;">'
        f'<span style="color:{color};font-weight:600;flex-shrink:0;">{icon}</span>'
        f'<span style="color:var(--text-muted);font-size:14px;">{escape(f)}</span></li>'
        for f in features
    )
    return f'<ul style="list-style:none;margin:0;padding:0;">{items}</ul>'


# ---------------------------------------------------------------------------
# Hoverable tooltip
# ---------------------------------------------------------------------------


def tooltip(text: str, tip: str) -> str:
    """Wrap text in a CSS-only tooltip."""
    return (
        f'<span style="position:relative;display:inline-block;cursor:help;'
        f'border-bottom:1px dashed var(--border);" '
        f'title="{escape(tip)}">{text}</span>'
    )


# ---------------------------------------------------------------------------
# Card wrapper
# ---------------------------------------------------------------------------


def card(content: str, padding: str = "20px", hover: bool = True) -> str:
    """Generic card wrapper."""
    hover_js = (
        'onmouseover="this.style.boxShadow=\'var(--shadow-md)\'" '
        'onmouseout="this.style.boxShadow=\'var(--shadow-sm)\'"'
        if hover else ""
    )
    return f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);
                border-radius:var(--r-lg);padding:{padding};
                box-shadow:var(--shadow-sm);transition:box-shadow .15s;"
         {hover_js}>
      {content}
    </div>
    """


# ---------------------------------------------------------------------------
# Form field
# ---------------------------------------------------------------------------


def form_field(
    label: str,
    input_html: str,
    hint: str = "",
    error: str = "",
    required: bool = False,
) -> str:
    """Wrap an input with label, hint, and error."""
    req = '<span style="color:var(--danger);">*</span>' if required else ""
    hint_html = f'<p style="font-size:12px;color:var(--text-faint);margin:4px 0 0;">{escape(hint)}</p>' if hint else ""
    error_html = f'<p style="font-size:12px;color:var(--danger);margin:4px 0 0;">{escape(error)}</p>' if error else ""
    return f"""
    <div style="margin-bottom:16px;">
      <label style="display:block;font-weight:500;font-size:14px;margin-bottom:6px;">
        {escape(label)} {req}
      </label>
      {input_html}
      {hint_html}
      {error_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Table helper
# ---------------------------------------------------------------------------


def data_table(
    headers: list[str],
    rows: list[list],
    empty_message: str = "No data",
) -> str:
    """Render a simple data table."""
    if not rows:
        return f'<p style="color:var(--text-muted);text-align:center;padding:24px;">{escape(empty_message)}</p>'

    header_cells = "".join(
        f'<th style="padding:10px 16px;text-align:left;font-size:13px;'
        f'color:var(--text-muted);font-weight:600;'
        f'border-bottom:2px solid var(--border);">{escape(h)}</th>'
        for h in headers
    )
    body_rows = ""
    for i, row in enumerate(rows):
        bg = "" if i % 2 == 0 else "background:var(--bg-alt);"
        cells = "".join(
            f'<td style="padding:10px 16px;font-size:14px;'
            f'border-bottom:1px solid var(--border-subtle);">{escape(str(c)) if c is not None else "—"}</td>'
            for c in row
        )
        body_rows += f'<tr style="{bg}">{cells}</tr>'

    return f"""
    <div style="overflow-x:auto;border-radius:var(--r-lg);border:1px solid var(--border);">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{body_rows}</tbody>
      </table>
    </div>
    """


# ---------------------------------------------------------------------------
# Inline SVG icons (minimal set)
# ---------------------------------------------------------------------------


def icon_check(size: int = 16, color: str = "currentColor") -> str:
    return f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" fill="none" stroke="{color}" stroke-width="2"><polyline points="2,8 6,12 14,4"/></svg>'


def icon_x(size: int = 16, color: str = "currentColor") -> str:
    return f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" fill="none" stroke="{color}" stroke-width="2"><line x1="2" y1="2" x2="14" y2="14"/><line x1="14" y1="2" x2="2" y2="14"/></svg>'


def icon_arrow_right(size: int = 16, color: str = "currentColor") -> str:
    return f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" fill="none" stroke="{color}" stroke-width="2"><line x1="2" y1="8" x2="14" y2="8"/><polyline points="9,3 14,8 9,13"/></svg>'


def icon_external(size: int = 16, color: str = "currentColor") -> str:
    return f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" fill="none" stroke="{color}" stroke-width="2"><path d="M6 3H3v10h10v-3M9 2h5v5M9 7l5-5"/></svg>'


def icon_github(size: int = 16, color: str = "currentColor") -> str:
    return f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" fill="{color}"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'


# ---------------------------------------------------------------------------
# Star rating display
# ---------------------------------------------------------------------------


def star_rating(value: float, max_val: float = 5.0, count: int = 0) -> str:
    """Render a star rating display."""
    pct = min(max(value / max_val * 100 if max_val else 0, 0), 100)
    count_html = f' <span style="color:var(--text-faint);font-size:12px;">({count})</span>' if count else ""
    return f"""
    <div style="display:inline-flex;align-items:center;gap:4px;">
      <div style="position:relative;display:inline-block;font-size:16px;">
        <span style="color:var(--surface);letter-spacing:2px;">★★★★★</span>
        <span style="position:absolute;left:0;top:0;overflow:hidden;width:{pct:.0f}%;color:var(--gold);letter-spacing:2px;">★★★★★</span>
      </div>
      <span style="font-size:13px;color:var(--text-muted);">{value:.1f}</span>
      {count_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Collapsible / disclosure
# ---------------------------------------------------------------------------


def collapsible(summary: str, content: str, open_by_default: bool = False) -> str:
    """Render an HTML <details> collapsible."""
    open_attr = " open" if open_by_default else ""
    return f"""
    <details{open_attr} style="border:1px solid var(--border);border-radius:var(--r-md);
              background:var(--bg-card);">
      <summary style="padding:12px 16px;cursor:pointer;font-weight:500;
                      font-size:14px;list-style:none;display:flex;
                      align-items:center;justify-content:space-between;">
        {escape(summary)}
        <span style="color:var(--text-faint);font-size:12px;">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <path d="M2 4l4 4 4-4"/>
          </svg>
        </span>
      </summary>
      <div style="padding:0 16px 16px;">{content}</div>
    </details>
    """


# ---------------------------------------------------------------------------
# Highlighted search result
# ---------------------------------------------------------------------------


def highlight_query(text: str, query: str) -> str:
    """Wrap query terms in <mark> tags within text (safe, no injection)."""
    if not query or not text:
        return escape(text)
    parts = re.split(r"(" + re.escape(query) + r")", text, flags=re.IGNORECASE)
    result = ""
    for part in parts:
        if part.lower() == query.lower():
            result += f'<mark style="background:rgba(0,212,245,.2);border-radius:2px;padding:0 2px;">{escape(part)}</mark>'
        else:
            result += escape(part)
    return result


import re  # noqa: E402 — imported here to avoid circular at module top
