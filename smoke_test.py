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
    ("GET", "/new", 200, "New tools"),
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
    ("GET", "/best", 200, "Best Indie"),
    ("GET", "/best/analytics-metrics", 200, "Best: Analytics"),
    ("GET", "/best/developer-tools", 200, "Best: Developer Tools"),

    # Auth pages (200)
    ("GET", "/login", 200, "Login"),
    ("GET", "/signup", 200, "Signup"),

    # Protected pages (redirect or login page)
    ("GET", "/dashboard", [200, 303], "Dashboard"),
    ("GET", "/submit", [200, 303], "Submit"),

    # API endpoints (200)
    ("GET", "/api/tools/search?q=email", 200, "API search"),
    ("GET", "/api/tools/simple-analytics", 200, "API tool detail"),
    ("GET", "/health", 200, "Health check"),
    ("GET", "/robots.txt", 200, "Robots.txt"),
    ("GET", "/sitemap.xml", 200, "Sitemap"),
    ("GET", "/feed/rss", 200, "RSS feed"),

    # SVG endpoints (200)
    ("GET", "/api/badge/simple-analytics.svg", 200, "Badge SVG"),
    ("GET", "/api/milestone/simple-analytics.svg?type=first-tool", 200, "Milestone SVG"),

    # Sample content pages (200) - using known slugs
    ("GET", "/tool/simple-analytics", 200, "Tool page"),
    ("GET", "/tag/open-source", 200, "Tag page"),
    ("GET", "/alternatives/google-analytics", 200, "Alternatives page"),
]

# Content checks: path -> (substring or callable, description)
CONTENT_CHECKS = {
    "/": ("IndieStack", "page contains 'IndieStack'"),
    "/health": (lambda body: json.loads(body).get("status") == "ok", "returns {\"status\": \"ok\"}"),
    "/sitemap.xml": ("<urlset", "contains <urlset"),
    "/api/tools/search?q=email": (lambda body: "tools" in json.loads(body), "JSON has 'tools' key"),
    "/best": ("Best Indie", "contains 'Best Indie'"),
}


def fetch(base_url, method, path):
    """Fetch a URL and return (status_code, body_text).

    Handles redirects manually so we can detect 303s.
    """
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, method=method)
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
