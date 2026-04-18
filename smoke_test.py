#!/usr/bin/env python3
"""IndieStack smoke test — hits every critical endpoint and verifies responses."""

import json
import sys
import time
import urllib.request
import urllib.error

# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

TESTS = [
    # Core pages (200)
    ("GET", "/", 200, "Landing"),
    ("GET", "/explore", 200, "Explore"),
    ("GET", "/new", 302, "New tools redirect"),
    ("GET", "/search?q=analytics", 200, "Search"),
    ("GET", "/makers", 200, "Makers"),
    ("GET", "/collections", [200, 301], "Collections redirect"),
    ("GET", "/updates", 200, "Updates"),
    ("GET", "/tags", 200, "Tags"),
    ("GET", "/alternatives", 200, "Alternatives"),
    ("GET", "/stacks", 200, "Stacks"),
    ("GET", "/stacks/community", 200, "Community stacks"),
    ("GET", "/live", 200, "Live Wire"),
    ("GET", "/plugins", 200, "Plugins"),

    # Static pages (200)
    ("GET", "/about", 200, "About"),
    ("GET", "/faq", 200, "FAQ"),
    ("GET", "/terms", 200, "Terms"),
    ("GET", "/privacy", 200, "Privacy"),
    ("GET", "/pricing", [200, 303], "Pricing"),

    # Blog pages (200)
    ("GET", "/blog", 200, "Blog"),
    ("GET", "/blog/stop-wasting-tokens", 200, "Blog post"),

    # Best & curated pages (200)
    ("GET", "/best", 200, "Best Developer Tools"),
    ("GET", "/best/analytics-metrics", 200, "Best: Analytics"),
    ("GET", "/best/developer-tools", 200, "Best: Developer Tools"),

    # Auth pages (200)
    ("GET", "/login", 200, "Login"),
    ("GET", "/signup", 200, "Signup"),

    # Protected pages (redirect or login page)
    ("GET", "/dashboard", [200, 303], "Dashboard"),
    ("GET", "/submit", [200, 303], "Submit"),

    # API endpoints (200)
    ("GET", "/api/validate?name=express&ecosystem=npm", 200, "Validate package (real)"),
    ("GET", "/api/validate?name=&ecosystem=npm", 400, "Validate package (empty name)"),
    ("GET", "/api/tools/search?q=email", 200, "API search"),
    ("GET", "/api/tools/simple-analytics", 200, "API tool detail"),
    ("GET", "/health", 200, "Health check"),
    ("GET", "/robots.txt", 200, "Robots.txt"),
    ("GET", "/sitemap.xml", 200, "Sitemap"),
    ("GET", "/feed/rss", 200, "RSS feed"),
    ("GET", "/cards/index.json", 200, "Cards index"),
    ("GET", "/geo", 200, "GEO lead magnet"),
    ("GET", "/changelog", 200, "Changelog"),

    # SVG endpoints (200)
    ("GET", "/api/badge/simple-analytics.svg", 200, "Badge SVG"),
    ("GET", "/api/badge/ai-recs/simple-analytics.svg", 200, "AI recs badge SVG"),
    ("GET", "/api/milestone/simple-analytics.svg?type=first-tool", 200, "Milestone SVG"),

    # Sample content pages (200) - using known slugs
    ("GET", "/tool/simple-analytics", 200, "Tool page"),
    # Compatibility Graph (Phase 2)
    ("POST", "/tool/simple-analytics/compatible", 403, "Compat auth guard"),
    ("GET", "/explore?compatible_with=supabase", 200, "Explore compat filter"),
    ("GET", "/tag/open-source", 302, "Tag page redirect"),
    ("GET", "/alternatives/google-analytics", 200, "Alternatives page"),

    # Agent action endpoints (require API key — expect 401 without)
    ("POST", "/api/agent/recommend", 401, "Agent recommend auth guard"),
    ("POST", "/api/agent/shortlist", 401, "Agent shortlist auth guard"),
    ("POST", "/api/agent/outcome", 400, "Agent outcome (keyless allowed, empty body = 400)"),
    ("POST", "/api/agent/integration", 401, "Agent integration auth guard"),
    # Analyze
    ("GET", "/analyze", 200, "Stack Health Check"),

    # Compare endpoint (critical for user feature)
    ("GET", "/compare/next-auth-vs-authgate", 200, "Compare tools"),

    # Market gaps page (data-driven discovery)
    ("GET", "/gaps", 200, "Market gaps"),

    # Leaderboard (ranking + stats)
    ("GET", "/leaderboard", 200, "Maker leaderboard"),

    # API pulse endpoint (real-time data)
    ("GET", "/api/pulse", 200, "API pulse"),

    # Trending stacks (ranking algorithm)
    ("GET", "/trending-stacks", 200, "Trending stacks"),

    # Additional pages added since initial smoke tests
    ("GET", "/what-is-indiestack", 200, "What is IndieStack"),
    ("GET", "/setup", 200, "Setup / Claude.md"),
    ("GET", "/setup/agents.md", 200, "AGENTS.md download"),
    ("GET", "/api/tool-trust?limit=5", 200, "Tool trust leaderboard"),
    ("GET", "/calculator", 200, "Cost calculator"),
    ("GET", "/embed", 200, "Embed landing"),

    # Status and ops pages (Apr 7)
    ("GET", "/api/status", 200, "Public status API"),
    ("GET", "/trust/incidents", 200, "Incident response protocol"),

    # Agent registry (Phase A)
    ("GET", "/agents", 200, "Agent registry"),
    ("GET", "/api/agents/search?capability=seo", 200, "Agent search API"),

    # Oracle API (x402) — data endpoints return 402 (payment required) on production
    ("GET", "/v1/compatibility/nextjs/supabase", [200, 402], "Oracle compatibility"),
    ("GET", "/v1/migration/jest/vitest", [200, 402], "Oracle migration"),
    ("POST", "/v1/stack/architect", [200, 400, 402, 403], "Oracle stack architect"),
    ("GET", "/v1/.well-known/x402-resources", 200, "Oracle x402 metadata"),
]

# Content checks: path -> (substring or callable, description)
CONTENT_CHECKS = {
    "/": ("IndieStack", "page contains 'IndieStack'"),
    "/health": (lambda body: json.loads(body).get("status") == "ok", "returns {\"status\": \"ok\"}"),
    "/sitemap.xml": ("<urlset", "contains <urlset"),
    "/api/tools/search?q=email": (lambda body: "tools" in json.loads(body), "JSON has 'tools' key"),
    "/best": ("Best Developer Tools", "contains 'Best Developer Tools'"),
    "/tool/simple-analytics": ("Confirmed Works With", "has compat section"),
    "/compare/next-auth-vs-authgate": ("Compare", "compare page shows comparison"),
    "/gaps": ("Gap", "gaps page shows market gaps data"),
    "/leaderboard": ("Maker", "leaderboard has maker data"),
    "/api/pulse": (lambda body: "html" in json.loads(body), "pulse API returns JSON with 'html' key"),
    "/trending-stacks": ("Stack", "trending page shows stack content"),
}


def fetch(base_url, method, path):
    """Fetch a URL and return (status_code, body_text).

    Handles redirects manually so we can detect 303s.
    """
    url = base_url.rstrip("/") + path
    data = None
    if method == "POST":
        data = b"pair_slug=test"
    req = urllib.request.Request(url, method=method, data=data)
    if data:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    # Build an opener that does NOT follow redirects automatically
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise urllib.error.HTTPError(newurl, code, msg, headers, fp)

    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        resp = opener.open(req, timeout=15)
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body
    except urllib.error.HTTPError as e:
        body = ""
        if e.fp:
            try:
                body = e.fp.read().decode("utf-8", errors="replace")
            except Exception:
                pass
        return e.code, body


def check_status(actual, expected):
    """Return True if actual status matches expected (int or list of ints)."""
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


def run_content_check(path, body):
    """Run content check for a path if one exists. Return (passed, description) or None."""
    if path not in CONTENT_CHECKS:
        return None
    check, desc = CONTENT_CHECKS[path]
    try:
        if callable(check):
            passed = check(body)
        else:
            passed = check in body
    except Exception:
        passed = False
    return passed, desc


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://indiestack.ai"

    print(f"\n{BOLD}IndieStack Smoke Test{RESET}")
    print(f"{DIM}Target: {base_url}{RESET}\n")

    passed = 0
    failed = 0
    results = []

    for method, path, expected, label in TESTS:
        start = time.time()
        try:
            status, body = fetch(base_url, method, path)
        except Exception as e:
            status = 0
            body = ""
            label_extra = f" (error: {e})"
        else:
            label_extra = ""

        elapsed = time.time() - start
        ok = check_status(status, expected)

        # Content check
        content_ok = True
        content_msg = ""
        if ok:
            result = run_content_check(path, body)
            if result is not None:
                content_ok, content_msg = result
                if not content_ok:
                    ok = False

        if ok:
            passed += 1
            icon = f"{GREEN}\u2713{RESET}"
        else:
            failed += 1
            icon = f"{RED}\u2717{RESET}"

        status_display = str(status) if status else "ERR"
        expected_display = str(expected)
        line = f"  {icon}  {label:<22} {method} {path:<45} {status_display:>3} (expect {expected_display}){DIM} {elapsed:.2f}s{RESET}{label_extra}"
        if content_msg and not content_ok:
            line += f"  {RED}content check failed: {content_msg}{RESET}"
        elif content_msg and content_ok:
            line += f"  {DIM}+ {content_msg}{RESET}"
        print(line)

    # Summary
    total = passed + failed
    print(f"\n{BOLD}Results: {GREEN}{passed} passed{RESET}{BOLD}, {RED if failed else ''}{failed} failed{RESET}{BOLD} / {total} total{RESET}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
