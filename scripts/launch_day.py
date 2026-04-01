#!/usr/bin/env python3
"""
IndieStack Launch Day Mission Control
=====================================
Pre-launch checks, post-launch monitoring, and health dashboard.

Usage:
    python3 launch_day.py check       Pre-launch validation suite
    python3 launch_day.py monitor     Post-launch monitoring (10 min)
    python3 launch_day.py status      Quick health dashboard
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

# ── ANSI Color Codes ──────────────────────────────────────────────────────

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[97m"
BG_RED  = "\033[41m"
BG_GREEN = "\033[42m"
BG_BLUE = "\033[44m"
BG_CYAN = "\033[46m"

CONFIG = {"base_url": "https://indiestack.ai"}


def base_url():
    return CONFIG["base_url"]

# ── Same endpoints as smoke_test.py ───────────────────────────────────────

SMOKE_TESTS = [
    ("GET", "/", 200, "Landing"),
    ("GET", "/explore", 200, "Explore"),
    ("GET", "/new", 200, "New tools"),
    ("GET", "/search?q=analytics", 200, "Search"),
    ("GET", "/makers", 200, "Makers"),
    ("GET", "/collections", [200, 301], "Collections"),
    ("GET", "/updates", 200, "Updates"),
    ("GET", "/tags", 200, "Tags"),
    ("GET", "/alternatives", 200, "Alternatives"),
    ("GET", "/stacks", 200, "Stacks"),
    ("GET", "/stacks/community", 200, "Community stacks"),
    ("GET", "/live", 200, "Live Wire"),
    ("GET", "/plugins", 200, "Plugins"),
    ("GET", "/about", 200, "About"),
    ("GET", "/faq", 200, "FAQ"),
    ("GET", "/terms", 200, "Terms"),
    ("GET", "/privacy", 200, "Privacy"),
    ("GET", "/pricing", [200, 303], "Pricing"),
    ("GET", "/blog", 200, "Blog"),
    ("GET", "/blog/stop-wasting-tokens", 200, "Blog post"),
    ("GET", "/best", 200, "Best Indie"),
    ("GET", "/best/analytics-metrics", 200, "Best: Analytics"),
    ("GET", "/best/developer-tools", 200, "Best: Dev Tools"),
    ("GET", "/login", 200, "Login"),
    ("GET", "/signup", 200, "Signup"),
    ("GET", "/dashboard", [200, 303], "Dashboard"),
    ("GET", "/submit", [200, 303], "Submit"),
    ("GET", "/api/tools/search?q=email", 200, "API search"),
    ("GET", "/api/tools/simple-analytics", 200, "API tool detail"),
    ("GET", "/health", 200, "Health check"),
    ("GET", "/robots.txt", 200, "Robots.txt"),
    ("GET", "/sitemap.xml", 200, "Sitemap"),
    ("GET", "/feed/rss", 200, "RSS feed"),
    ("GET", "/api/badge/simple-analytics.svg", 200, "Badge SVG"),
    ("GET", "/api/milestone/simple-analytics.svg?type=first-tool", 200, "Milestone SVG"),
    ("GET", "/tool/simple-analytics", 200, "Tool page"),
    ("GET", "/tag/open-source", 200, "Tag page"),
    ("GET", "/alternatives/google-analytics", 200, "Alternatives page"),
    ("GET", "/demand", 200, "Demand Pro"),
]


# ── Helpers ───────────────────────────────────────────────────────────────

def banner(title):
    """Print a section banner."""
    width = 60
    print()
    print(f"{BOLD}{BG_BLUE}{WHITE} {'=' * width} {RESET}")
    print(f"{BOLD}{BG_BLUE}{WHITE}  {title.center(width)}{RESET}")
    print(f"{BOLD}{BG_BLUE}{WHITE} {'=' * width} {RESET}")
    print()


def sub_banner(title):
    """Print a subsection header."""
    print(f"\n{BOLD}{CYAN}--- {title} ---{RESET}\n")


def ok(msg):
    print(f"  {GREEN}{BOLD}PASS{RESET}  {msg}")


def fail(msg):
    print(f"  {RED}{BOLD}FAIL{RESET}  {msg}")


def warn(msg):
    print(f"  {YELLOW}{BOLD}WARN{RESET}  {msg}")


def info(msg):
    print(f"  {DIM}{msg}{RESET}")


def alert(msg):
    """Print a loud red alert."""
    print(f"  {BG_RED}{WHITE}{BOLD} ALERT {RESET} {RED}{BOLD}{msg}{RESET}")


def fetch(path, timeout=15):
    """Fetch a URL, return (status, body, elapsed_seconds).

    Does not follow redirects so we can detect 303s.
    """
    url = base_url().rstrip("/") + path

    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise urllib.error.HTTPError(newurl, code, msg, headers, fp)

    opener = urllib.request.build_opener(NoRedirectHandler)
    start = time.time()
    try:
        req = urllib.request.Request(url, method="GET")
        resp = opener.open(req, timeout=timeout)
        body = resp.read().decode("utf-8", errors="replace")
        headers = dict(resp.headers)
        return resp.status, body, time.time() - start, headers
    except urllib.error.HTTPError as e:
        body = ""
        headers = dict(e.headers) if e.headers else {}
        if e.fp:
            try:
                body = e.fp.read().decode("utf-8", errors="replace")
            except Exception:
                pass
        return e.code, body, time.time() - start, headers
    except Exception as e:
        return 0, str(e), time.time() - start, {}


def check_status(actual, expected):
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


# ── Subcommand: check ────────────────────────────────────────────────────

def cmd_check(args):
    banner("INDIESTACK LAUNCH DAY -- PRE-LAUNCH CHECKS")
    print(f"  {DIM}Target: {base_url()}{RESET}")
    print(f"  {DIM}Time:   {time.strftime('%Y-%m-%d %H:%M:%S %Z')}{RESET}")

    total_pass = 0
    total_fail = 0

    # ── 1. Smoke Tests ────────────────────────────────────────────────
    sub_banner("1/6  Smoke Tests ({} endpoints)".format(len(SMOKE_TESTS)))

    smoke_pass = 0
    smoke_fail = 0
    slow_endpoints = []

    for method, path, expected, label in SMOKE_TESTS:
        status, body, elapsed, headers = fetch(path)
        passed = check_status(status, expected)

        if elapsed > 2.0:
            slow_endpoints.append((path, elapsed))

        if passed:
            smoke_pass += 1
            icon = f"{GREEN}P{RESET}"
        else:
            smoke_fail += 1
            icon = f"{RED}F{RESET}"

        status_str = str(status) if status else "ERR"
        timing_color = RED if elapsed > 3.0 else YELLOW if elapsed > 2.0 else DIM
        print(f"  [{icon}] {label:<22} {status_str:>3}  {timing_color}{elapsed:.2f}s{RESET}")

    if smoke_fail == 0:
        ok(f"All {smoke_pass} smoke tests passed")
    else:
        fail(f"{smoke_fail} smoke tests failed out of {smoke_pass + smoke_fail}")

    total_pass += smoke_pass
    total_fail += smoke_fail

    # ── 2. Admin Password Check ───────────────────────────────────────
    sub_banner("2/6  Admin Password")

    # We can't directly check the env var on Fly, but we can check that
    # /admin redirects (requires auth) rather than being wide open
    status, body, elapsed, headers = fetch("/admin")
    if status in (303, 401, 403):
        ok("Admin route is protected (redirects to login)")
        total_pass += 1
    elif status == 200 and "login" in body.lower():
        ok("Admin route shows login form")
        total_pass += 1
    else:
        warn(f"Admin route returned {status} -- verify INDIESTACK_ADMIN_PASSWORD is set")
        total_fail += 1

    # ── 3. Response Time Check ────────────────────────────────────────
    sub_banner("3/6  Response Time (landing page < 2s)")

    status, body, elapsed, headers = fetch("/")
    if elapsed < 2.0:
        ok(f"Landing page loaded in {elapsed:.2f}s")
        total_pass += 1
    else:
        fail(f"Landing page took {elapsed:.2f}s (target: < 2.0s)")
        total_fail += 1

    if slow_endpoints:
        warn(f"{len(slow_endpoints)} endpoint(s) above 2s during smoke tests:")
        for path, t in slow_endpoints:
            info(f"  {path} -- {t:.2f}s")

    # ── 4. CSP Header ─────────────────────────────────────────────────
    sub_banner("4/6  Security Headers (CSP)")

    csp = headers.get("Content-Security-Policy", headers.get("content-security-policy", ""))
    if csp:
        ok(f"CSP header present ({len(csp)} chars)")
        total_pass += 1
    else:
        fail("Content-Security-Policy header missing on landing page")
        total_fail += 1

    sts = headers.get("Strict-Transport-Security", headers.get("strict-transport-security", ""))
    if sts:
        ok(f"HSTS header present")
    else:
        warn("Strict-Transport-Security header missing")

    # ── 5. OG Tags ────────────────────────────────────────────────────
    sub_banner("5/6  OG Tags (landing page)")

    og_checks = [
        ('og:title', 'property="og:title"' in body or "property=\"og:title\"" in body),
        ('og:description', 'og:description' in body),
        ('og:image', 'og:image' in body),
        ('og:url', 'og:url' in body),
    ]
    og_pass = sum(1 for _, found in og_checks if found)
    for tag, found in og_checks:
        if found:
            ok(f"{tag} present")
            total_pass += 1
        else:
            fail(f"{tag} missing")
            total_fail += 1

    # ── 6. Live Stats ─────────────────────────────────────────────────
    sub_banner("6/6  Live Stats from API")

    # Tool count
    status, body, elapsed, _ = fetch("/api/tools/search?q=&limit=1")
    if status == 200:
        try:
            data = json.loads(body)
            tool_count = data.get("total", data.get("count", "?"))
            print(f"  {CYAN}{BOLD}Tools:{RESET}      {tool_count}")
        except Exception:
            print(f"  {DIM}Tools:      (could not parse response){RESET}")
    else:
        print(f"  {DIM}Tools:      (search endpoint returned {status}){RESET}")

    # Categories
    status, body, elapsed, _ = fetch("/api/tools/index.json")
    if status == 200:
        try:
            data = json.loads(body)
            cats = data.get("categories", [])
            cat_count = len(cats) if isinstance(cats, list) else "?"
            total_tools = data.get("total_tools", "?")
            print(f"  {CYAN}{BOLD}Categories:{RESET} {cat_count}")
            print(f"  {CYAN}{BOLD}Index tools:{RESET} {total_tools}")
        except Exception:
            pass

    # Maker count via landing page scraping (look for the stats in the HTML)
    status, body, elapsed, _ = fetch("/")
    if status == 200:
        # Landing page embeds stats like "633 makers" in the stats pills
        import re
        maker_match = re.search(r'(\d[\d,]+)\+?\s*makers', body, re.IGNORECASE)
        if maker_match:
            print(f"  {CYAN}{BOLD}Makers:{RESET}     {maker_match.group(1)}")

        rec_match = re.search(r'([\d,]+)\+?\s*AI recommendations', body)
        if rec_match:
            print(f"  {CYAN}{BOLD}AI recs:{RESET}    {rec_match.group(1)}")

    # ── Summary ───────────────────────────────────────────────────────
    total = total_pass + total_fail
    print()
    print(f"{'=' * 62}")
    if total_fail == 0:
        print(f"  {BG_GREEN}{WHITE}{BOLD} ALL CLEAR {RESET}  {GREEN}{total_pass}/{total} checks passed. Ready to launch.{RESET}")
    else:
        print(f"  {BG_RED}{WHITE}{BOLD} ISSUES FOUND {RESET}  {RED}{total_fail} failed{RESET}, {GREEN}{total_pass} passed{RESET} / {total} total")
    print(f"{'=' * 62}")

    # ── Video Toggle Helper ───────────────────────────────────────────
    sub_banner("Video Toggle Helper")
    print(f"  To enable the demo video on the landing page, run:")
    print()
    print(f"    {YELLOW}~/.fly/bin/flyctl secrets set DEMO_VIDEO_URL=\"<paste-youtube-url-here>\"{RESET}")
    print()
    print(f"  {DIM}Note: This requires a redeploy to take effect.{RESET}")
    print(f"  {DIM}To redeploy: cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only{RESET}")
    print()
    print(f"  To disable the video:")
    print()
    print(f"    {YELLOW}~/.fly/bin/flyctl secrets unset DEMO_VIDEO_URL{RESET}")
    print()

    return 1 if total_fail else 0


# ── Subcommand: monitor ──────────────────────────────────────────────────

def cmd_monitor(args):
    banner("INDIESTACK LAUNCH DAY -- POST-LAUNCH MONITOR")
    print(f"  {DIM}Target: {base_url()}{RESET}")
    print(f"  {DIM}Monitoring landing page every 30s for 10 minutes{RESET}")
    print(f"  {DIM}Started: {time.strftime('%H:%M:%S %Z')}{RESET}")
    print()

    duration = 600  # 10 minutes
    interval = 30
    iterations = duration // interval

    times = []
    errors = 0

    print(f"  {'#':>3}  {'Status':>6}  {'Time':>8}  {'Bar'}")
    print(f"  {'---':>3}  {'------':>6}  {'--------':>8}  {'---'}")

    for i in range(1, iterations + 1):
        status, body, elapsed, headers = fetch("/", timeout=10)
        times.append(elapsed)

        # Status coloring
        if status == 200:
            status_str = f"{GREEN}{status}{RESET}"
        else:
            status_str = f"{RED}{status}{RESET}"
            errors += 1

        # Time coloring and bar
        bar_len = min(int(elapsed * 10), 50)
        if elapsed > 3.0:
            time_str = f"{RED}{BOLD}{elapsed:.3f}s{RESET}"
            bar_color = RED
            alert(f"Request #{i} took {elapsed:.3f}s (> 3s threshold)")
        elif elapsed > 2.0:
            time_str = f"{YELLOW}{elapsed:.3f}s{RESET}"
            bar_color = YELLOW
        else:
            time_str = f"{GREEN}{elapsed:.3f}s{RESET}"
            bar_color = GREEN

        bar = f"{bar_color}{'|' * bar_len}{RESET}"

        if status != 200:
            alert(f"Request #{i} returned status {status}")

        print(f"  {i:>3}  {status_str:>6}  {time_str:>8}  {bar}")

        # Don't sleep after the last iteration
        if i < iterations:
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                print(f"\n  {YELLOW}Monitoring stopped by user after {i} requests.{RESET}")
                break

    # ── Summary ───────────────────────────────────────────────────────
    if not times:
        print(f"\n  {RED}No requests completed.{RESET}")
        return 1

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    p95_idx = int(len(times) * 0.95)
    sorted_times = sorted(times)
    p95_time = sorted_times[min(p95_idx, len(sorted_times) - 1)]

    print()
    print(f"  {'=' * 50}")
    print(f"  {BOLD}Monitoring Summary{RESET}")
    print(f"  {'=' * 50}")
    print(f"  {CYAN}Requests:{RESET}   {len(times)}")
    print(f"  {CYAN}Errors:{RESET}     {RED if errors else GREEN}{errors}{RESET}")
    print(f"  {CYAN}Avg time:{RESET}   {avg_time:.3f}s")
    print(f"  {CYAN}Min time:{RESET}   {min_time:.3f}s")
    print(f"  {CYAN}Max time:{RESET}   {RED if max_time > 3.0 else GREEN}{max_time:.3f}s{RESET}")
    print(f"  {CYAN}P95 time:{RESET}   {p95_time:.3f}s")

    if errors == 0 and max_time < 3.0:
        print(f"\n  {BG_GREEN}{WHITE}{BOLD} STABLE {RESET}  {GREEN}All requests healthy.{RESET}")
    elif errors > 0:
        print(f"\n  {BG_RED}{WHITE}{BOLD} DEGRADED {RESET}  {RED}{errors} error(s) detected.{RESET}")
    else:
        print(f"\n  {YELLOW}{BOLD}SLOW{RESET}  Some requests exceeded 3s threshold.")

    print()
    return 1 if errors else 0


# ── Subcommand: status ───────────────────────────────────────────────────

def cmd_status(args):
    banner("INDIESTACK LAUNCH DAY -- HEALTH DASHBOARD")
    print(f"  {DIM}Target: {base_url()}{RESET}")
    print(f"  {DIM}Time:   {time.strftime('%Y-%m-%d %H:%M:%S %Z')}{RESET}")

    checks = [
        ("/health", "Health endpoint", lambda s, b: s == 200 and json.loads(b).get("status") == "ok"),
        ("/api/pulse", "Pulse feed", lambda s, b: s == 200),
        ("/api/tools/search?q=auth", "Search API (q=auth)", lambda s, b: s == 200 and "tools" in json.loads(b)),
        ("/", "Landing page", lambda s, b: s == 200 and "IndieStack" in b),
    ]

    all_ok = True

    for path, label, validator in checks:
        status, body, elapsed, headers = fetch(path)
        try:
            passed = validator(status, body)
        except Exception:
            passed = False

        if passed:
            ok(f"{label:<30} {status:>3}  {DIM}{elapsed:.2f}s{RESET}")
        else:
            fail(f"{label:<30} {status:>3}  {DIM}{elapsed:.2f}s{RESET}")
            all_ok = False

        # Extra details for certain endpoints
        if path == "/health" and status == 200:
            try:
                data = json.loads(body)
                for k, v in data.items():
                    info(f"    {k}: {v}")
            except Exception:
                pass

        if path == "/api/pulse" and status == 200:
            try:
                data = json.loads(body)
                events = data.get("events", [])
                info(f"    {len(events)} recent events in feed")
                if events:
                    latest = events[0]
                    info(f"    Latest: [{latest.get('type', '?')}] {latest.get('query', latest.get('tool_name', '?'))}")
            except Exception:
                pass

        if path == "/api/tools/search?q=auth" and status == 200:
            try:
                data = json.loads(body)
                tools = data.get("tools", [])
                info(f"    {len(tools)} results for 'auth'")
                for t in tools[:3]:
                    info(f"    - {t.get('name', '?')}: {t.get('tagline', '')[:60]}")
            except Exception:
                pass

    # ── Quick vitals ──────────────────────────────────────────────────
    sub_banner("Vitals")

    status, body, elapsed, _ = fetch("/api/tools/index.json")
    if status == 200:
        try:
            data = json.loads(body)
            print(f"  {CYAN}Total tools:{RESET}  {data.get('total_tools', '?')}")
            cats = data.get("categories", [])
            print(f"  {CYAN}Categories:{RESET}   {len(cats) if isinstance(cats, list) else '?'}")
        except Exception:
            pass

    status, body, _, _ = fetch("/")
    if status == 200:
        import re
        for pattern, label in [
            (r'([\d,]+)\+?\s*tools', "Tools"),
            (r'([\d,]+)\+?\s*AI recommendations', "AI recs"),
        ]:
            m = re.search(pattern, body)
            if m:
                print(f"  {CYAN}{label}:{RESET}{' ' * (14 - len(label))}{m.group(1)}")

    # ── Final status ──────────────────────────────────────────────────
    print()
    if all_ok:
        print(f"  {BG_GREEN}{WHITE}{BOLD} ALL SYSTEMS GO {RESET}")
    else:
        print(f"  {BG_RED}{WHITE}{BOLD} ISSUES DETECTED {RESET}")
    print()

    return 0 if all_ok else 1


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IndieStack Launch Day Mission Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Commands:\n"
            "  check     Run full pre-launch validation suite\n"
            "  monitor   Monitor landing page every 30s for 10 minutes\n"
            "  status    Quick health dashboard\n"
        ),
    )
    parser.add_argument(
        "--url",
        default=CONFIG["base_url"],
        help=f"Base URL to test (default: {CONFIG['base_url']})",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("check", help="Pre-launch validation suite")
    subparsers.add_parser("monitor", help="Post-launch monitoring (10 min)")
    subparsers.add_parser("status", help="Quick health dashboard")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Allow overriding the base URL
    CONFIG["base_url"] = args.url.rstrip("/")

    commands = {
        "check": cmd_check,
        "monitor": cmd_monitor,
        "status": cmd_status,
    }

    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()
