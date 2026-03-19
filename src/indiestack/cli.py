"""IndieStack CLI — search 3,100+ developer tools from your terminal."""

import json
import os
import sys
from pathlib import Path

import httpx

# ── Config ────────────────────────────────────────────────────────────────

BASE_URL = os.environ.get("INDIESTACK_BASE_URL", "https://indiestack.ai")
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "indiestack"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    """Load config from ~/.config/indiestack/config.json."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_config(config: dict):
    """Save config to ~/.config/indiestack/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")


def _get_api_key() -> str:
    """Get API key: env var first, then config file."""
    key = os.environ.get("INDIESTACK_API_KEY", "")
    if key:
        return key
    config = _load_config()
    return config.get("api_key", "")


# ── Colours ───────────────────────────────────────────────────────────────

_NO_COLOR = os.environ.get("NO_COLOR") is not None or not sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _bold(t: str) -> str: return _c("1", t)
def _dim(t: str) -> str: return _c("2", t)
def _cyan(t: str) -> str: return _c("36", t)
def _green(t: str) -> str: return _c("32", t)
def _yellow(t: str) -> str: return _c("33", t)
def _red(t: str) -> str: return _c("31", t)


# ── API ───────────────────────────────────────────────────────────────────

def _api_get(path: str, params: dict = None) -> dict:
    """Sync GET request to IndieStack API."""
    if params is None:
        params = {}
    params["source"] = "cli"
    key = _get_api_key()
    if key:
        params["key"] = key
    params = {k: v for k, v in params.items() if v is not None and v != ""}

    try:
        resp = httpx.get(f"{BASE_URL}{path}", params=params, timeout=15.0)
        if resp.status_code == 429:
            data = resp.json()
            error = data.get("error", "Rate limit exceeded.")
            print(_red(f"Error: {error}"))
            if not key:
                print()
                print(f"  Set a key:  indiestack config set-key <your-key>")
                print(f"  Get one at: {_cyan('https://indiestack.ai/developer')}")
            sys.exit(1)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        print(_red("Error: Could not connect to IndieStack API."))
        sys.exit(1)
    except httpx.TimeoutException:
        print(_red("Error: Request timed out."))
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(_red(f"Error: HTTP {e.response.status_code}"))
        sys.exit(1)


# ── Formatters ────────────────────────────────────────────────────────────

def _format_tool_row(t: dict, idx: int = 0) -> str:
    """Format a single tool for terminal display."""
    name = _bold(t.get("name", "?"))
    tagline = t.get("tagline", "")
    category = _dim(t.get("category", ""))
    price = t.get("price", "Free")
    price_str = _green(price) if price == "Free" else _yellow(price)
    slug = _dim(t.get("slug", ""))
    stars = t.get("github_stars")
    stars_str = f" {_dim(f'★{stars}')} " if stars else " "
    health = t.get("health_status", "")
    health_str = ""
    if health == "healthy":
        health_str = _green("●")
    elif health == "stale":
        health_str = _yellow("●")
    elif health == "archived":
        health_str = _red("●")

    line1 = f"  {_dim(str(idx + 1) + '.')} {name} {price_str}{stars_str}{health_str}"
    line2 = f"     {tagline}"
    line3 = f"     {category} · {slug}"
    return f"{line1}\n{line2}\n{line3}"


def _format_detail(t: dict) -> str:
    """Format full tool details for terminal display."""
    lines = []
    lines.append("")
    lines.append(f"  {_bold(t.get('name', '?'))}")
    lines.append(f"  {t.get('tagline', '')}")
    lines.append("")

    # Key info
    price = t.get("price", "Free")
    lines.append(f"  {_dim('Price:')}     {_green(price) if price == 'Free' else _yellow(price)}")
    lines.append(f"  {_dim('Category:')}  {t.get('category', '?')}")
    lines.append(f"  {_dim('URL:')}       {_cyan(t.get('url', ''))}")
    lines.append(f"  {_dim('Page:')}      {_cyan(t.get('indiestack_url', ''))}")

    if t.get("maker_name"):
        lines.append(f"  {_dim('Maker:')}     {t['maker_name']}")

    # Health
    health = t.get("health_status", "")
    if health:
        stars = t.get("github_stars", 0)
        commit = t.get("github_last_commit", "?")
        health_color = _green if health == "healthy" else (_yellow if health == "stale" else _red)
        lines.append(f"  {_dim('Health:')}    {health_color(health)}  ★{stars}  last commit: {commit}")

    # Ratings
    if t.get("avg_rating"):
        lines.append(f"  {_dim('Rating:')}    {t['avg_rating']}/5 ({t.get('review_count', 0)} reviews)")

    # Tags
    tags = t.get("tags", "")
    if tags:
        lines.append(f"  {_dim('Tags:')}      {tags}")

    # Install
    if t.get("install_command"):
        lines.append("")
        lines.append(f"  {_bold('Install:')}")
        lines.append(f"  {_cyan(t['install_command'])}")

    # Integration
    if t.get("integration_curl"):
        lines.append("")
        lines.append(f"  {_bold('Quick start:')}")
        lines.append(f"  {_dim(t['integration_curl'])}")

    # Compatible tools
    compat = t.get("compatible_tools", [])
    if compat:
        lines.append("")
        lines.append(f"  {_bold('Works with:')}")
        for c in compat[:5]:
            verified = _green("✓") if c.get("verified") else _dim("○")
            lines.append(f"    {verified} {c['slug']} ({c.get('success_count', 0)} reports)")

    # Pro enrichment
    if t.get("pro_enriched"):
        lines.append("")
        lines.append(f"  {_yellow('━━ Pro Insights ━━')}")
        cs = t.get("citation_stats", {})
        if cs:
            lines.append(f"  {_dim('Citations:')}  {cs.get('citations_7d', 0)} (7d) / {cs.get('citations_30d', 0)} (30d)")
            agents = cs.get("agents", [])
            if agents:
                agent_str = ", ".join(f"{a['name']}({a['count']})" for a in agents[:3])
                lines.append(f"  {_dim('Agents:')}    {agent_str}")
        pct = t.get("category_percentile")
        if pct is not None:
            lines.append(f"  {_dim('Percentile:')} Top {100 - pct}% in category")
        demand = t.get("demand_context", [])
        if demand:
            lines.append(f"  {_dim('Demand:')}    " + ", ".join(f'"{d["query"]}"({d["search_count"]})' for d in demand[:3]))

    lines.append("")
    return "\n".join(lines)


# ── Commands ──────────────────────────────────────────────────────────────

def cmd_search(args: list[str], use_json: bool = False):
    """Search for indie tools."""
    if not args:
        print(_red("Usage: indiestack search <query>"))
        sys.exit(1)

    query = " ".join(args)
    data = _api_get("/api/tools/search", {"q": query, "limit": "10"})
    tools = data.get("tools", [])

    if use_json:
        print(json.dumps(data, indent=2))
        return

    pro = data.get("pro_enriched", False)
    title = _bold('Search: "' + query + '"') + "  " + _dim("(" + str(len(tools)) + " results)")
    if pro:
        title += _yellow(" [Pro]")
    print("\n  " + title)
    print()

    if not tools:
        gap = data.get("market_gap", {})
        if gap:
            print(f"  {_yellow('Market gap detected!')} No tools found for \"{query}\".")
            print(f"  Submit yours: {_cyan(gap.get('submit_url', 'https://indiestack.ai/submit'))}")
        else:
            print(_dim("  No results found."))
        print()
        return

    for i, t in enumerate(tools):
        print(_format_tool_row(t, i))
        # Show Pro enrichment inline if available
        if t.get("citation_count_7d"):
            extras = []
            extras.append(f"cited {t['citation_count_7d']}x (7d)")
            if t.get("compatible_with"):
                extras.append(f"works with: {', '.join(t['compatible_with'][:3])}")
            print(f"     {_yellow(' · '.join(extras))}")
        print()

    print(f"  {_dim('Details:')} indiestack details <slug>")
    print()


def cmd_details(args: list[str], use_json: bool = False):
    """Get full details for a tool."""
    if not args:
        print(_red("Usage: indiestack details <slug>"))
        sys.exit(1)

    slug = args[0]
    data = _api_get(f"/api/tools/{slug}")
    tool = data.get("tool", data)

    if use_json:
        print(json.dumps(data, indent=2))
        return

    print(_format_detail(tool))


def cmd_categories(args: list[str], use_json: bool = False):
    """List all categories."""
    data = _api_get("/api/categories")
    cats = data.get("categories", [])

    if use_json:
        print(json.dumps(data, indent=2))
        return

    print(f"\n  {_bold('Categories')}  {_dim(f'({len(cats)} total)')}\n")
    for c in cats:
        count = c.get("tool_count", 0)
        icon = c.get("icon", "")
        print(f"  {icon}  {_bold(c['name'])} {_dim(f'({count})')}")
    print()
    print(f"  {_dim('Browse:')} indiestack search --category <slug>")
    print()


def cmd_stack(args: list[str], use_json: bool = False):
    """Build a stack from comma-separated needs."""
    if not args:
        print(_red("Usage: indiestack stack \"auth, payments, email\""))
        sys.exit(1)

    needs = " ".join(args)
    need_list = [n.strip() for n in needs.split(",") if n.strip()]

    if use_json:
        results = {}
        for need in need_list:
            data = _api_get("/api/tools/search", {"q": need, "limit": "1"})
            tools = data.get("tools", [])
            results[need] = tools[0] if tools else None
        print(json.dumps(results, indent=2))
        return

    print(f"\n  {_bold('Building stack:')} {', '.join(need_list)}\n")

    for need in need_list:
        data = _api_get("/api/tools/search", {"q": need, "limit": "3"})
        tools = data.get("tools", [])

        print(f"  {_cyan('▸')} {_bold(need)}")
        if tools:
            top = tools[0]
            alts = [t["name"] for t in tools[1:3]]
            price = top.get("price", "Free")
            price_str = _green(price) if price == "Free" else _yellow(price)
            print(f"    → {_bold(top['name'])} {price_str}  {_dim(top.get('tagline', ''))}")
            if alts:
                print(f"      {_dim('also: ' + ', '.join(alts))}")
        else:
            print(f"    {_dim('No matches — this is a market gap!')}")
        print()

    print(f"  {_dim('Details:')} indiestack details <slug>")
    print()


def cmd_config(args: list[str], use_json: bool = False):
    """Manage CLI configuration."""
    if not args:
        # Show current config
        config = _load_config()
        key = _get_api_key()

        print(f"\n  {_bold('IndieStack CLI Config')}\n")
        print(f"  {_dim('Config file:')}  {CONFIG_FILE}")
        if key:
            # Mask the key, show first 8 and last 4 chars
            masked = key[:8] + "..." + key[-4:] if len(key) > 12 else key
            print(f"  {_dim('API key:')}     {_green(masked)}")
            source = "env var" if os.environ.get("INDIESTACK_API_KEY") else "config file"
            print(f"  {_dim('Key source:')}  {source}")
        else:
            print(f"  {_dim('API key:')}     {_yellow('not set')} (using keyless tier: 3/day)")
            print(f"\n  Get a free key: {_cyan('https://indiestack.ai/developer')}")
        print()
        return

    subcmd = args[0]

    if subcmd == "set-key":
        if len(args) < 2:
            print(_red("Usage: indiestack config set-key <isk_...>"))
            sys.exit(1)
        key = args[1]
        if not key.startswith("isk_"):
            print(_red("Error: API keys start with 'isk_'"))
            sys.exit(1)
        config = _load_config()
        config["api_key"] = key
        _save_config(config)
        masked = key[:8] + "..." + key[-4:]
        print(_green(f"API key saved: {masked}"))
        print(f"Config: {CONFIG_FILE}")

    elif subcmd == "remove-key":
        config = _load_config()
        config.pop("api_key", None)
        _save_config(config)
        print(_green("API key removed."))

    else:
        print(_red(f"Unknown config command: {subcmd}"))
        print(_dim("Available: set-key, remove-key"))
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────

COMMANDS = {
    "search": cmd_search,
    "details": cmd_details,
    "categories": cmd_categories,
    "stack": cmd_stack,
    "config": cmd_config,
}

VERSION = "1.4.0"

HELP = f"""\
{_bold('indiestack')} — search 3,100+ developer tools from your terminal

{_bold('Usage:')}
  indiestack search <query>           Search for tools
  indiestack details <slug>           Full tool details
  indiestack categories               List all categories
  indiestack stack "auth, pay, email" Build a stack from needs
  indiestack config                   Show current config
  indiestack config set-key <key>     Save your API key
  indiestack --version                Show version

{_bold('Options:')}
  --json                              Output raw JSON (for piping)

{_bold('API Keys:')}
  No key needed to start (3 queries/day).
  Get a free key for 10/month: {_cyan('https://indiestack.ai/developer')}
  Upgrade to Pro for 1,000/month: {_cyan('https://indiestack.ai/pricing')}

{_bold('Examples:')}
  indiestack search "privacy analytics"
  indiestack details simple-analytics
  indiestack stack "auth, payments, email, analytics"
  indiestack search "email" --json | jq '.tools[0].slug'
"""


def main():
    """CLI entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(HELP)
        return

    if args[0] in ("-v", "--version", "version"):
        print(f"indiestack {VERSION}")
        return

    # Extract --json flag
    use_json = "--json" in args
    if use_json:
        args.remove("--json")

    cmd_name = args[0]
    cmd_args = args[1:]

    if cmd_name in COMMANDS:
        COMMANDS[cmd_name](cmd_args, use_json=use_json)
    else:
        print(_red(f"Unknown command: {cmd_name}"))
        print(f"Run {_bold('indiestack --help')} for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
