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
                <button onclick="copyCode('script-code')" style="
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
                <button onclick="copyCode('iframe-code')" style="
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

        <div style="text-align:center;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Want your tool featured in embeds?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Verified tools rank higher in every widget. Claim yours today.
            </p>
            <a href="/submit" class="btn btn-primary">Submit Your Creation &rarr;</a>
        </div>
    </div>

    <script>
    var BASE = "{BASE_URL}";
    var catSelect = document.getElementById("cat-select");
    var scriptCode = document.getElementById("script-code");
    var iframeCode = document.getElementById("iframe-code");
    var previewIframe = document.getElementById("preview-iframe");

    function updateSnippets() {{
        var cat = catSelect.value;
        scriptCode.textContent = '<script src="' + BASE + '/embed/widget.js" data-category="' + cat + '"></' + 'script>';
        iframeCode.textContent = '<iframe src="' + BASE + '/embed/' + cat + '" style="width:100%;border:none;min-height:400px;" loading="lazy"></iframe>';
        previewIframe.src = BASE + '/embed/' + cat;
    }}

    catSelect.addEventListener("change", updateSnippets);
    updateSnippets();

    function copyCode(id) {{
        var el = document.getElementById(id);
        navigator.clipboard.writeText(el.textContent).then(function() {{
            var btn = el.parentNode.querySelector("button");
            btn.textContent = "Copied!";
            setTimeout(function() {{ btn.textContent = "Copy"; }}, 2000);
        }});
    }}
    </script>
    """

    return HTMLResponse(page_shell(
        "Embed IndieStack — Comparison Widget for Bloggers",
        body,
        description="Add a curated indie creations comparison widget to your blog. Free backlinks, useful content.",
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
        + '<div class="is-foot">Powered by <a href="' + BASE + '?ref=embed" target="_blank" rel="noopener">IndieStack</a> &mdash; Curated indie creations</div>'
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
  &mdash; Curated indie creations
</div>
</body>
</html>"""
    return HTMLResponse(html)


