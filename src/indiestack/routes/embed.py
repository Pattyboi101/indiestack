"""Embeddable comparison widget for bloggers — iframe + JS snippet."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from indiestack import db

router = APIRouter()


def _indie_score(t: dict) -> int:
    """Simple indie score from upvotes."""
    score = int(t.get('upvote_count', 0))
    return score


def _price_label(t: dict) -> str:
    pp = t.get('price_pence')
    if pp and pp > 0:
        return f"\u00a3{pp / 100:.2f}"
    return "Free"


# ── Endpoint 3: Embed docs/preview page (must be before {category_slug}) ──

@router.get("/embed", response_class=HTMLResponse)
async def embed_docs(request: Request):
    """Docs page showing bloggers how to embed the widget."""
    d = request.state.db
    categories = await db.get_all_categories(d)

    options = ""
    for c in categories:
        cslug = escape(c['slug'])
        cname = escape(c['name'])
        count = int(c.get('tool_count', 0))
        sel = ' selected' if cslug == 'analytics' else ''
        options += f'<option value="{cslug}"{sel}>{cname} ({count} tools)</option>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);">
                Embed IndieStack
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:12px;max-width:600px;margin-left:auto;margin-right:auto;">
                Add a curated comparison widget to your blog or docs.
                Each embed links back to IndieStack &mdash; free backlinks for us, useful content for your readers.
            </p>
        </div>

        <!-- Category picker -->
        <div style="margin-bottom:24px;">
            <label for="cat-select" style="font-weight:600;font-size:14px;color:var(--ink);display:block;margin-bottom:8px;">
                Choose a category
            </label>
            <select id="cat-select" style="
                width:100%;max-width:360px;padding:12px 16px;font-size:15px;
                border:1px solid var(--border);border-radius:var(--radius-sm);background:#fff;
                font-family:inherit;color:var(--ink);
            ">
                {options}
            </select>
        </div>

        <!-- Option 1: Script tag -->
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:8px;">
                Option 1: JavaScript Widget
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Drop this single script tag anywhere in your page.
                It renders inside a Shadow DOM so it won&rsquo;t conflict with your styles.
            </p>
            <div style="position:relative;">
                <pre id="script-code" style="
                    background:var(--terracotta);color:var(--border);padding:16px 20px;border-radius:var(--radius-sm);
                    font-family:var(--font-mono);font-size:13px;
                    overflow-x:auto;white-space:pre-wrap;word-break:break-all;
                "></pre>
                <button id="copy-script" data-copy="" style="
                    position:absolute;top:8px;right:8px;background:var(--slate);color:#fff;
                    border:none;border-radius:var(--radius-sm);padding:8px 16px;font-size:12px;
                    font-weight:600;cursor:pointer;
                ">Copy</button>
            </div>
        </div>

        <!-- Option 2: iframe -->
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:8px;">
                Option 2: iframe Embed
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                If you prefer an iframe, paste this snippet. Works everywhere, including Medium and Substack.
            </p>
            <div style="position:relative;">
                <pre id="iframe-code" style="
                    background:var(--terracotta);color:var(--border);padding:16px 20px;border-radius:var(--radius-sm);
                    font-family:var(--font-mono);font-size:13px;
                    overflow-x:auto;white-space:pre-wrap;word-break:break-all;
                "></pre>
                <button id="copy-iframe" data-copy="" style="
                    position:absolute;top:8px;right:8px;background:var(--slate);color:#fff;
                    border:none;border-radius:var(--radius-sm);padding:8px 16px;font-size:12px;
                    font-weight:600;cursor:pointer;
                ">Copy</button>
            </div>
        </div>

        <!-- Live preview -->
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                Live Preview
            </h2>
            <div id="preview-wrap" style="
                border:2px dashed var(--border);border-radius:var(--radius);padding:24px;
                background:#fff;min-height:200px;
            ">
                <iframe id="preview-iframe" style="
                    width:100%;border:none;border-radius:var(--radius-sm);min-height:400px;
                " src="{BASE_URL}/embed/analytics"></iframe>
            </div>
        </div>

        <!-- Search Widget -->
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:8px;">
                Option 3: Search Widget
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                A self-contained search box with confidence indicators. Top 5 results, dark/light mode, &lt;50KB.
            </p>
            <div style="display:flex;gap:8px;margin-bottom:16px;">
                <button id="theme-light" onclick="setSearchTheme('light')" style="padding:6px 14px;font-size:13px;border:1px solid var(--accent);border-radius:var(--radius-sm);background:var(--accent);color:white;cursor:pointer;font-weight:600;">Light</button>
                <button id="theme-dark" onclick="setSearchTheme('dark')" style="padding:6px 14px;font-size:13px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--card-bg);color:var(--ink);cursor:pointer;">Dark</button>
            </div>
            <div style="position:relative;">
                <pre id="search-widget-code" style="
                    background:var(--terracotta);color:var(--border);padding:16px 20px;border-radius:var(--radius-sm);
                    font-family:var(--font-mono);font-size:13px;
                    overflow-x:auto;white-space:pre-wrap;word-break:break-all;
                "></pre>
                <button id="copy-search" data-copy="" style="
                    position:absolute;top:8px;right:8px;background:var(--slate);color:#fff;
                    border:none;border-radius:var(--radius-sm);padding:8px 16px;font-size:12px;
                    font-weight:600;cursor:pointer;
                ">Copy</button>
            </div>
        </div>

        <!-- Search Widget Preview -->
        <div style="margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                Search Widget Preview
            </h2>
            <div id="search-preview-wrap" style="
                border:2px dashed var(--border);border-radius:var(--radius);padding:24px;
                background:#fff;min-height:120px;
            ">
                <div id="search-widget-container"></div>
            </div>
        </div>

        <!-- Error States -->
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:8px;">
                Error Handling
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;line-height:1.7;">
                Both widgets handle errors gracefully. If the IndieStack API is unreachable, the category widget shows
                &ldquo;Failed to load IndieStack widget&rdquo; and the search widget shows &ldquo;Search failed. Try again.&rdquo;
                No uncaught exceptions, no blank spaces. Widgets render inside Shadow DOM so they never conflict with your page styles.
            </p>
        </div>

        <div style="text-align:center;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Want your tool featured in embeds?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Verified tools rank higher in every widget. Claim yours today.
            </p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool &rarr;</a>
        </div>
    </div>

    <script>
    var BASE = "{BASE_URL}";
    var catSelect = document.getElementById("cat-select");
    var scriptCode = document.getElementById("script-code");
    var iframeCode = document.getElementById("iframe-code");
    var previewIframe = document.getElementById("preview-iframe");

    var copyScriptBtn = document.getElementById("copy-script");
    var copyIframeBtn = document.getElementById("copy-iframe");

    function updateSnippets() {{
        var cat = catSelect.value;
        var scriptSnippet = '<script src="' + BASE + '/embed/widget.js" data-category="' + cat + '"></' + 'script>';
        var iframeSnippet = '<iframe src="' + BASE + '/embed/' + cat + '" style="width:100%;border:none;min-height:400px;" loading="lazy"></iframe>';
        scriptCode.textContent = scriptSnippet;
        iframeCode.textContent = iframeSnippet;
        copyScriptBtn.setAttribute("data-copy", scriptSnippet);
        copyIframeBtn.setAttribute("data-copy", iframeSnippet);
        previewIframe.src = BASE + '/embed/' + cat;
    }}

    catSelect.addEventListener("change", updateSnippets);
    updateSnippets();

    // Search widget
    var searchCode = document.getElementById("search-widget-code");
    var copySearchBtn = document.getElementById("copy-search");
    var searchTheme = "light";

    function setSearchTheme(theme) {{
        searchTheme = theme;
        document.getElementById("theme-light").style.background = theme === "light" ? "var(--accent)" : "var(--card-bg)";
        document.getElementById("theme-light").style.color = theme === "light" ? "white" : "var(--ink)";
        document.getElementById("theme-light").style.borderColor = theme === "light" ? "var(--accent)" : "var(--border)";
        document.getElementById("theme-dark").style.background = theme === "dark" ? "var(--accent)" : "var(--card-bg)";
        document.getElementById("theme-dark").style.color = theme === "dark" ? "white" : "var(--ink)";
        document.getElementById("theme-dark").style.borderColor = theme === "dark" ? "var(--accent)" : "var(--border)";
        updateSearchSnippet();
        // Reload preview
        var wrap = document.getElementById("search-preview-wrap");
        wrap.style.background = theme === "dark" ? "#0a0e1a" : "#fff";
        var container = document.getElementById("search-widget-container");
        container.innerHTML = "";
        var s = document.createElement("script");
        s.src = BASE + "/embed/search-widget.js";
        s.setAttribute("data-theme", theme);
        s.setAttribute("data-limit", "5");
        container.appendChild(s);
    }}

    function updateSearchSnippet() {{
        var snippet = '<script src="' + BASE + '/embed/search-widget.js" data-theme="' + searchTheme + '" data-limit="5"></' + 'script>';
        searchCode.textContent = snippet;
        copySearchBtn.setAttribute("data-copy", snippet);
    }}
    updateSearchSnippet();
    // Load initial preview
    setSearchTheme("light");

    // Generic copy handler for all copy buttons
    document.querySelectorAll("[data-copy]").forEach(function(btn) {{
        btn.addEventListener("click", function() {{
            var text = this.getAttribute("data-copy");
            if (!text) return;
            navigator.clipboard.writeText(text).then(function() {{
                btn.textContent = "Copied!";
                setTimeout(function() {{ btn.textContent = "Copy"; }}, 2000);
            }});
        }});
    }});
    </script>
    """

    return HTMLResponse(page_shell(
        "Embed IndieStack — Comparison Widget for Bloggers",
        body,
        description="Add a curated developer tools comparison widget to your blog. Free backlinks, useful content.",
        user=request.state.user,
        canonical="/embed",
    ))


# ── widget.js source ─────────────────────────────────────────────────────

WIDGET_JS = '(function(){\n  var BASE = "' + BASE_URL + '";\n' + r"""
  var script = document.currentScript;
  var category = script.getAttribute("data-category") || "analytics";
  var limit = parseInt(script.getAttribute("data-limit") || "10", 10);
  if (limit < 1) limit = 1;
  if (limit > 20) limit = 20;

  var container = document.createElement("div");
  script.parentNode.insertBefore(container, script);

  var shadow = container.attachShadow({mode: "open"});

  shadow.innerHTML = '<div style="font-family:system-ui,sans-serif;color:#6b7a8d;padding:16px;font-size:14px;">Loading tools...</div>';

  fetch(BASE + "/api/tools/search?category=" + encodeURIComponent(category) + "&limit=" + limit)
    .then(function(r){ return r.json(); })
    .then(function(data){
      var tools = data.tools || [];
      if (!tools.length) {
        shadow.innerHTML = '<div style="font-family:system-ui,sans-serif;color:#888;padding:16px;">No tools found for this category.</div>';
        return;
      }

      var rows = "";
      for (var i = 0; i < tools.length; i++) {
        var t = tools[i];
        var alt = i % 2 === 1 ? ' style="background:#fafbfd;"' : '';
        rows += '<tr' + alt + '>'
          + '<td style="padding:10px 12px;border-bottom:1px solid #eef0f4;vertical-align:top;">'
          + '<a href="' + t.indiestack_url + '?ref=embed" target="_blank" rel="noopener" style="color:#1A2D4A;text-decoration:none;font-weight:600;font-size:14px;">' + esc(t.name) + '</a>'
          + '<div style="color:#6b7a8d;font-size:12px;margin-top:2px;">' + esc(t.tagline) + '</div>'
          + '</td>'
          + '<td style="padding:10px 8px;border-bottom:1px solid #eef0f4;text-align:center;font-size:13px;font-weight:500;white-space:nowrap;">' + t.upvote_count + '</td>'
          + '<td style="padding:10px 8px;border-bottom:1px solid #eef0f4;text-align:center;font-size:13px;font-weight:500;white-space:nowrap;">' + esc(t.price) + '</td>'
          + '<td style="padding:10px 12px;border-bottom:1px solid #eef0f4;text-align:right;white-space:nowrap;">'
          + '<a href="' + t.indiestack_url + '?ref=embed" target="_blank" rel="noopener" style="color:#00D4F5;text-decoration:none;font-weight:600;font-size:12px;">View &rarr;</a>'
          + '</td></tr>';
      }

      shadow.innerHTML = ''
        + '<style>'
        + '@import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap");'
        + '*{box-sizing:border-box;margin:0;padding:0;}'
        + 'a:hover{color:#00D4F5!important;}'
        + '.is-wrap{font-family:"DM Sans",system-ui,sans-serif;color:#1A2D4A;background:#F7F9FC;border:1px solid #e2e6ec;border-radius:10px;overflow:hidden;max-width:680px;}'
        + '.is-head{font-family:"DM Serif Display",serif;font-size:18px;padding:16px 18px 12px;}'
        + '.is-head span{color:#00D4F5;}'
        + 'table{width:100%;border-collapse:collapse;}'
        + 'th{background:#1A2D4A;color:#fff;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;padding:8px 12px;text-align:left;}'
        + 'th:nth-child(2),th:nth-child(3){text-align:center;}'
        + 'tr:last-child td{border-bottom:none;}'
        + '.is-foot{text-align:center;padding:10px;font-size:11px;color:#8b99ab;border-top:1px solid #eef0f4;}'
        + '.is-foot a{color:#00D4F5;text-decoration:none;font-weight:500;}'
        + '@media(max-width:540px){th:nth-child(2),th:nth-child(3),td:nth-child(2),td:nth-child(3){display:none;}}'
        + '</style>'
        + '<div class="is-wrap">'
        + '<div class="is-head">Best <span>' + esc(category.replace(/-/g, " ").replace(/\b\w/g, function(l){return l.toUpperCase();})) + '</span> Tools</div>'
        + '<table><thead><tr><th>Tool</th><th>Score</th><th>Price</th><th></th></tr></thead>'
        + '<tbody>' + rows + '</tbody></table>'
        + '<div class="is-foot">Powered by <a href="' + BASE + '?ref=embed" target="_blank" rel="noopener">IndieStack</a> &mdash; Curated developer tools</div>'
        + '</div>';
    })
    .catch(function(){
      shadow.innerHTML = '<div style="font-family:system-ui,sans-serif;color:#c44;padding:16px;font-size:13px;">Failed to load IndieStack widget.</div>';
    });

  function esc(s) {
    if (!s) return "";
    var d = document.createElement("div");
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }
})();"""


# ── Endpoint 2: widget.js (must be before {category_slug}) ──────────────

@router.get("/embed/widget.js")
async def embed_widget_js():
    """JavaScript embed snippet for bloggers."""
    return Response(
        content=WIDGET_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600", "Access-Control-Allow-Origin": "*"},
    )


# ── Search widget — self-contained search box with results ───────────────

SEARCH_WIDGET_JS = '(function(){\n  var BASE = "' + BASE_URL + '";\n' + r"""
  var script = document.currentScript;
  var limit = parseInt(script.getAttribute("data-limit") || "5", 10);
  if (limit < 1) limit = 1;
  if (limit > 10) limit = 10;
  var theme = script.getAttribute("data-theme") || "light";

  var container = document.createElement("div");
  script.parentNode.insertBefore(container, script);
  var shadow = container.attachShadow({mode: "open"});

  var bg = theme === "dark" ? "#0a0e1a" : "#F7F9FC";
  var ink = theme === "dark" ? "#e8eaf0" : "#1A2D4A";
  var muted = theme === "dark" ? "#8b99ab" : "#6b7a8d";
  var border = theme === "dark" ? "#2a3040" : "#e2e6ec";
  var cardBg = theme === "dark" ? "#141822" : "#fff";

  shadow.innerHTML = '<style>'
    + '@import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap");'
    + '*{box-sizing:border-box;margin:0;padding:0;}'
    + '.is-search-wrap{font-family:"DM Sans",system-ui,sans-serif;background:' + bg + ';border:1px solid ' + border + ';border-radius:12px;padding:20px;max-width:420px;color:' + ink + ';}'
    + '.is-search-head{font-family:"DM Serif Display",serif;font-size:16px;margin-bottom:12px;}'
    + '.is-search-head span{color:#00D4F5;}'
    + '.is-search-input{width:100%;padding:10px 14px;border:1px solid ' + border + ';border-radius:8px;font-size:14px;font-family:inherit;background:' + cardBg + ';color:' + ink + ';outline:none;}'
    + '.is-search-input:focus{border-color:#00D4F5;}'
    + '.is-search-input::placeholder{color:' + muted + ';}'
    + '.is-results{margin-top:12px;}'
    + '.is-result{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:8px;text-decoration:none;color:inherit;transition:background 0.15s;}'
    + '.is-result:hover{background:' + (theme === "dark" ? "#1e2330" : "#eef1f5") + ';}'
    + '.is-result-info{flex:1;min-width:0;}'
    + '.is-result-name{font-weight:600;font-size:14px;color:' + ink + ';}'
    + '.is-result-tag{font-size:12px;color:' + muted + ';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
    + '.is-conf{flex-shrink:0;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;}'
    + '.is-conf-high{background:rgba(39,201,63,0.12);color:#27C93F;}'
    + '.is-conf-med{background:rgba(226,183,100,0.12);color:#E2B764;}'
    + '.is-conf-low{background:rgba(196,68,68,0.12);color:#c44;}'
    + '.is-empty{padding:16px;text-align:center;font-size:13px;color:' + muted + ';}'
    + '.is-foot{margin-top:10px;text-align:center;font-size:11px;color:' + muted + ';}'
    + '.is-foot a{color:#00D4F5;text-decoration:none;font-weight:500;}'
    + '</style>'
    + '<div class="is-search-wrap">'
    + '<div class="is-search-head">Find <span>Developer Tools</span></div>'
    + '<input class="is-search-input" type="text" placeholder="Search 8,000+ tools..." />'
    + '<div class="is-results"></div>'
    + '<div class="is-foot">Powered by <a href="' + BASE + '?ref=search-widget" target="_blank" rel="noopener">IndieStack</a></div>'
    + '</div>';

  var input = shadow.querySelector(".is-search-input");
  var resultsDiv = shadow.querySelector(".is-results");
  var debounce = null;

  input.addEventListener("input", function() {
    clearTimeout(debounce);
    var q = input.value.trim();
    if (q.length < 2) { resultsDiv.innerHTML = ""; return; }
    debounce = setTimeout(function() { doSearch(q); }, 300);
  });

  function doSearch(q) {
    resultsDiv.innerHTML = '<div class="is-empty">Searching...</div>';
    fetch(BASE + "/api/tools/search?q=" + encodeURIComponent(q) + "&limit=" + limit)
      .then(function(r){ return r.json(); })
      .then(function(data){
        var tools = data.tools || [];
        if (!tools.length) {
          resultsDiv.innerHTML = '<div class="is-empty">No tools found for &ldquo;' + esc(q) + '&rdquo;</div>';
          return;
        }
        var html = "";
        for (var i = 0; i < tools.length; i++) {
          var t = tools[i];
          var conf = calcConf(t);
          html += '<a class="is-result" href="' + t.indiestack_url + '?ref=search-widget" target="_blank" rel="noopener">'
            + '<div class="is-conf ' + conf.cls + '">' + conf.pct + '</div>'
            + '<div class="is-result-info">'
            + '<div class="is-result-name">' + esc(t.name) + '</div>'
            + '<div class="is-result-tag">' + esc(t.tagline) + '</div>'
            + '</div></a>';
        }
        resultsDiv.innerHTML = html;
      })
      .catch(function(){
        resultsDiv.innerHTML = '<div class="is-empty">Search failed. Try again.</div>';
      });
  }

  function calcConf(t) {
    var score = 0;
    if (t.health_status === "alive") score += 30;
    if (t.github_stars > 100) score += 20;
    if (t.github_stars > 1000) score += 10;
    if (t.install_command) score += 15;
    if (t.github_last_commit) {
      var d = new Date(t.github_last_commit);
      var months = (Date.now() - d.getTime()) / (1000*60*60*24*30);
      if (months < 6) score += 25;
      else if (months < 12) score += 15;
    }
    var pct = Math.min(score, 100);
    var cls = pct >= 70 ? "is-conf-high" : pct >= 40 ? "is-conf-med" : "is-conf-low";
    return {pct: pct + "%", cls: cls};
  }

  function esc(s) {
    if (!s) return "";
    var d = document.createElement("div");
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }
})();"""


@router.get("/embed/search-widget.js")
async def embed_search_widget_js():
    """Self-contained search widget for embedding — Conway extension preview."""
    return Response(
        content=SEARCH_WIDGET_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600", "Access-Control-Allow-Origin": "*"},
    )


# ── Endpoint 1: Standalone embeddable HTML page ─────────────────────────

@router.get("/embed/{category_slug}", response_class=HTMLResponse)
async def embed_category(request: Request, category_slug: str):
    """Self-contained HTML comparison table for iframing."""
    d = request.state.db
    cat = await db.get_category_by_slug(d, category_slug)
    if not cat:
        return HTMLResponse(
            "<html><body style='font-family:sans-serif;padding:24px;color:#666;'>"
            "Category not found.</body></html>",
            status_code=404,
        )

    tools, _ = await db.get_tools_by_category(d, cat['id'], page=1, per_page=10)
    cat_name = escape(cat['name'])

    rows = ""
    for i, t in enumerate(tools):
        name = escape(t['name'])
        tagline = escape(t.get('tagline', ''))
        slug = escape(t['slug'])
        score = _indie_score(t)
        price = _price_label(t)
        zebra = ' class="alt"' if i % 2 == 1 else ''

        rows += f"""<tr{zebra}>
  <td class="name-cell">
    <a href="{BASE_URL}/tool/{slug}" target="_blank" rel="noopener">{name}</a>
    <div class="tagline">{tagline}</div>
  </td>
  <td class="score-cell">{score}</td>
  <td class="price-cell">{price}</td>
  <td class="link-cell">
    <a href="{BASE_URL}/tool/{slug}" target="_blank" rel="noopener">View &rarr;</a>
  </td>
</tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{cat_name} — IndieStack</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
body{{
  font-family:'DM Sans',system-ui,sans-serif;
  color:#1A2D4A;
  background:#F7F9FC;
  padding:20px;
  line-height:1.5;
}}
.widget-header{{
  font-family:'DM Serif Display',serif;
  font-size:clamp(18px,3vw,24px);
  margin-bottom:16px;
  color:#1A2D4A;
}}
.widget-header span{{color:#00D4F5;}}
table{{
  width:100%;
  border-collapse:collapse;
  border:1px solid #e2e6ec;
  border-radius:8px;
  overflow:hidden;
  background:#fff;
}}
th{{
  background:#1A2D4A;
  color:#fff;
  font-size:12px;
  font-weight:600;
  text-transform:uppercase;
  letter-spacing:0.5px;
  padding:10px 14px;
  text-align:left;
}}
th:nth-child(2),th:nth-child(3){{text-align:center;}}
td{{padding:12px 14px;border-bottom:1px solid #eef0f4;font-size:14px;vertical-align:top;}}
tr.alt td{{background:#fafbfd;}}
tr:last-child td{{border-bottom:none;}}
.name-cell a{{
  color:#1A2D4A;
  text-decoration:none;
  font-weight:600;
  font-size:15px;
}}
.name-cell a:hover{{color:#00D4F5;}}
.tagline{{color:#6b7a8d;font-size:13px;margin-top:2px;}}
.score-cell,.price-cell{{text-align:center;font-weight:500;white-space:nowrap;}}
.link-cell{{text-align:right;white-space:nowrap;}}
.link-cell a{{
  color:#00D4F5;
  text-decoration:none;
  font-weight:600;
  font-size:13px;
}}
.link-cell a:hover{{text-decoration:underline;}}
.footer{{
  margin-top:12px;
  text-align:center;
  font-size:12px;
  color:#8b99ab;
}}
.footer a{{color:#00D4F5;text-decoration:none;font-weight:500;}}
.footer a:hover{{text-decoration:underline;}}
@media(max-width:540px){{
  .score-cell,.price-cell{{display:none;}}
  th:nth-child(2),th:nth-child(3){{display:none;}}
  td{{padding:10px;}}
}}
</style>
</head>
<body>
<div class="widget-header">Best <span>{cat_name}</span> Tools</div>
<table>
<thead><tr>
  <th>Tool</th><th>Score</th><th>Price</th><th></th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="footer">
  Powered by <a href="{BASE_URL}?ref=embed" target="_blank" rel="noopener">IndieStack</a>
  &mdash; Curated developer tools
</div>
</body>
</html>"""
    return HTMLResponse(html)


