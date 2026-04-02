#!/usr/bin/env python3
"""Provocation Engine — creative stimulus for autonomous agents.

Called by the cron agent when all structured tasks are exhausted. Generates
a random provocation to force novel thinking about IndieStack improvements.

Five provocation types:
1. Live GitHub trending — what's gaining stars in the dev tools space?
2. Random tool roleplay — step into a maker's shoes via our own API
3. Constraint challenge — artificial pressure reveals real priorities
4. Inversion / destruction — what should we tear down?
5. Cross-domain steal — borrow ideas from unrelated successful projects

Usage:
    python3 scripts/provoke.py              # random provocation
    python3 scripts/provoke.py --type 3     # specific type (1-5)
    python3 scripts/provoke.py --dry-run    # show type without fetching
"""

import json
import random
import sys
import urllib.request
import urllib.error
from datetime import datetime


# ---------------------------------------------------------------------------
# Provocation type 1: GitHub trending dev tools queries (rotated)
# ---------------------------------------------------------------------------
GITHUB_QUERIES = [
    "mcp server",
    "developer tools",
    "devtools cli",
    "ai coding",
    "developer platform",
    "open source saas",
    "api framework",
    "dev productivity",
    "code generation",
    "infrastructure as code",
]


# ---------------------------------------------------------------------------
# Provocation type 2: Categories to search on IndieStack's own API
# ---------------------------------------------------------------------------
INDIESTACK_CATEGORIES = [
    "authentication", "payments", "analytics", "email", "database",
    "monitoring", "cms", "search", "storage", "testing",
    "deployment", "messaging", "scheduling", "forms", "logging",
    "security", "api", "notifications", "billing", "backend",
    "feature-flags", "ci-cd", "documentation", "error-tracking",
]


# ---------------------------------------------------------------------------
# Provocation type 3: Constraint challenges (20+ entries)
# ---------------------------------------------------------------------------
CONSTRAINTS = [
    "What if IndieStack had to make $100 by Friday? What's the fastest path?",

    "A developer just installed the MCP server and searched for 'auth'. "
    "They uninstalled it 30 seconds later. Why?",

    "What if we could only keep 3 pages on the site — which 3 and why?",

    "Someone just tweeted 'IndieStack search is broken'. What did they search for?",

    "What would IndieStack look like if it was built for mobile-first?",

    "What feature would make Ed's outreach emails 10x more effective?",

    "A VC just asked 'what's your moat?' — what's the honest answer?",

    "What would a clone of IndieStack need to beat us? What can't they copy?",

    "What's the one number on the admin dashboard that matters most? Is it there?",

    "If we deleted the MCP server tomorrow, would anyone notice? "
    "How do we make sure they would?",

    "A developer with 50k GitHub followers just searched IndieStack and "
    "found nothing useful. What were they looking for?",

    "What if every tool listing had to earn its place monthly? "
    "What metric would we use? How many tools would we remove?",

    "A competitor just launched with 500 tools and a better UI. "
    "What do we do in the first 24 hours?",

    "What if the MCP server could only return 1 tool per query? "
    "How good would that one result need to be?",

    "What's the one email we could send to a tool maker that would "
    "guarantee they claim their listing?",

    "Stripe just added a 'find tools' feature to their dashboard. "
    "How does IndieStack survive?",

    "A developer needs to ship auth + payments + email in 48 hours. "
    "Can IndieStack get them there? What's missing?",

    "What if we had to explain IndieStack to a non-technical person "
    "in one sentence? What would we say?",

    "An AI agent just recommended the wrong tool and the developer "
    "wasted 3 hours integrating it. What went wrong in our data?",

    "What if we charged tool makers $5/month instead of $49? "
    "Would volume make up for it? What changes?",

    "The top 10 MCP server searches this week all returned 0 results. "
    "What were they, and how do we fix that?",

    "A university professor wants to use IndieStack in a course about "
    "software architecture. What would we need to add?",

    "What's the one thing we're doing that feels busy but produces "
    "zero user value? Stop doing it.",

    "If IndieStack had a public API that developers could build on, "
    "what would they build? Would anyone actually use it?",

    "A tool maker just said 'I get more leads from Google than IndieStack.' "
    "Are they right? What would change their mind?",
]


# ---------------------------------------------------------------------------
# Provocation type 4: Inversions / destruction (20+ entries)
# ---------------------------------------------------------------------------
INVERSIONS = [
    "What's the single worst thing about IndieStack right now? Be brutal.",

    "What feature should we delete? What are we maintaining that nobody uses?",

    "What would make a maker actively angry about their IndieStack listing?",

    "What promise does the site make that we can't actually deliver?",

    "What's the most embarrassing page on the site? Go find it.",

    "Search for the 5 most common developer needs. How many does IndieStack "
    "answer perfectly?",

    "What data are we collecting but never showing to anyone?",

    "What if we deleted every page except search? Would the product be better?",

    "What tool categories on IndieStack have the worst data quality? "
    "Go check the actual listings.",

    "Read the last 20 search logs. How many returned genuinely useful results?",

    "What would a brutally honest review of IndieStack on Hacker News say?",

    "Which tools in our database are dead, abandoned, or have broken links? "
    "How many? Check a random sample of 10.",

    "What's our bounce rate telling us that we're ignoring?",

    "If a developer Googles 'best auth tool 2026', does IndieStack appear? "
    "Should it? What would it take?",

    "What part of the codebase are we most afraid to touch? Why?",

    "What would happen if we stopped the autonomous cron entirely? "
    "Would anyone notice?",

    "Pick a random tool page. Is the description accurate? Is the pricing "
    "current? Is the GitHub link alive?",

    "What's the gap between what Ed promises in outreach emails and what "
    "a maker actually sees when they visit?",

    "How many of our 8,000+ tools would a developer actually consider using? "
    "What percentage is filler?",

    "What would a user who visited once and never came back say if we "
    "asked them why?",

    "What's the most complex piece of code in the codebase that could be "
    "replaced with something simpler?",

    "Are our quality scores actually measuring quality, or just GitHub "
    "popularity? Check the formula.",

    "What assumptions baked into the ranking algorithm have never been "
    "validated with real user behavior?",
]


# ---------------------------------------------------------------------------
# Provocation type 5: Cross-domain GitHub queries (non-dev-tools)
# ---------------------------------------------------------------------------
CROSS_DOMAIN_QUERIES = [
    "stars:>5000 pushed:>2026-03-01 topic:education",
    "stars:>5000 pushed:>2026-03-01 topic:health",
    "stars:>3000 pushed:>2026-03-01 topic:music",
    "stars:>3000 pushed:>2026-03-01 topic:design",
    "stars:>3000 pushed:>2026-03-01 topic:gaming",
    "stars:>2000 pushed:>2026-03-01 topic:finance",
    "stars:>2000 pushed:>2026-03-01 topic:community",
    "stars:>2000 pushed:>2026-03-01 topic:productivity",
    "stars:>5000 pushed:>2026-03-01 topic:science",
    "stars:>3000 pushed:>2026-03-01 topic:automation",
]


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
def _fetch_json(url: str, timeout: int = 15) -> dict | None:
    """Fetch JSON from a URL. Returns None on any failure."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "IndieStack-Provoke/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            OSError, TimeoutError):
        return None


# ---------------------------------------------------------------------------
# Provocation generators
# ---------------------------------------------------------------------------

def provoke_github_trending() -> tuple[str, str]:
    """Type 1: Find a trending dev tools repo and ask what we can learn."""
    query = random.choice(GITHUB_QUERIES)
    url = (
        "https://api.github.com/search/repositories"
        f"?q={urllib.request.quote(query)}&sort=stars&order=desc&per_page=10"
    )
    data = _fetch_json(url)

    if not data or not data.get("items"):
        # Fallback if GitHub API is unavailable
        return ("GitHub Trending", _github_fallback())

    repo = random.choice(data["items"][:10])
    name = repo.get("full_name", "unknown")
    desc = repo.get("description", "No description") or "No description"
    stars = repo.get("stargazers_count", 0)
    html_url = repo.get("html_url", "")
    lang = repo.get("language", "unknown")

    text = (
        f'This project just got {stars:,} stars: {name} — "{desc}"\n'
        f"Language: {lang}. URL: {html_url}\n"
        f"Query that found it: \"{query}\"\n"
        f"\n"
        f"How is this relevant to IndieStack? Is this tool in our catalog?\n"
        f"What can we learn, steal, or do differently because this exists?\n"
        f"Should we be indexing projects like this automatically?"
    )
    return ("GitHub Trending", text)


def _github_fallback() -> str:
    """Static fallback when GitHub API is unreachable."""
    return (
        "GitHub API is rate-limited or unreachable right now.\n"
        "\n"
        "Alternative provocation: go to https://github.com/trending and "
        "find one project that surprises you. Ask yourself:\n"
        "- Is it in IndieStack's catalog?\n"
        "- If not, should it be?\n"
        "- What does its popularity say about what developers need right now?"
    )


def provoke_tool_roleplay() -> tuple[str, str]:
    """Type 2: Pick a random tool from IndieStack and roleplay as its maker."""
    category = random.choice(INDIESTACK_CATEGORIES)
    offset = random.randint(0, 40)
    url = (
        f"https://indiestack.ai/api/tools/search"
        f"?q={urllib.request.quote(category)}&limit=20&offset={offset}"
    )
    data = _fetch_json(url)

    tools = []
    if data and isinstance(data, dict):
        tools = data.get("tools", data.get("results", []))
    elif data and isinstance(data, list):
        tools = data

    if not tools:
        # Fallback with a generic roleplay
        return ("Tool Roleplay", _roleplay_fallback(category))

    tool = random.choice(tools)
    name = tool.get("name", "Unknown Tool")
    slug = tool.get("slug", "")
    desc = tool.get("description", "No description")[:200]
    listing_url = f"https://indiestack.ai/tool/{slug}" if slug else ""

    text = (
        f"You are the maker of {name}.\n"
        f"Description: \"{desc}\"\n"
    )
    if listing_url:
        text += f"Listing: {listing_url}\n"
    text += (
        f"\n"
        f"You just discovered your tool is listed on IndieStack.\n"
        f"\n"
        f"Answer as this maker:\n"
        f"- What would make you think 'wow, I need to claim this listing'?\n"
        f"- What's missing from the listing page that you'd want to add?\n"
        f"- What data would you pay $49/mo for?\n"
        f"- What would make you share your IndieStack listing on Twitter?\n"
        f"- What would annoy you about how your tool is presented?"
    )
    return ("Tool Roleplay", text)


def _roleplay_fallback(category: str) -> str:
    """Static fallback when IndieStack API is unreachable."""
    return (
        f"IndieStack API is unreachable. Imagine a maker of a popular {category} tool.\n"
        f"\n"
        f"They just discovered their tool on IndieStack. What would:\n"
        f"- Make them claim their listing immediately?\n"
        f"- Make them pay $49/mo for Maker Pro?\n"
        f"- Make them share the listing publicly?\n"
        f"- Annoy them about how their tool is presented?\n"
        f"\n"
        f"Go visit a real {category} tool listing page and answer honestly."
    )


def provoke_constraint() -> tuple[str, str]:
    """Type 3: Random constraint challenge."""
    constraint = random.choice(CONSTRAINTS)
    text = (
        f"{constraint}\n"
        f"\n"
        f"Don't just think about it — do something concrete.\n"
        f"Check the actual site, database, search logs, or codebase.\n"
        f"If the answer reveals a real problem, fix it or file a task."
    )
    return ("Constraint Challenge", text)


def provoke_inversion() -> tuple[str, str]:
    """Type 4: Inversion / destruction — tear something down."""
    inversion = random.choice(INVERSIONS)
    text = (
        f"{inversion}\n"
        f"\n"
        f"This is not rhetorical. Go look. Check production.\n"
        f"If you find something genuinely broken or useless, act on it.\n"
        f"The uncomfortable answer is usually the right one."
    )
    return ("Inversion", text)


def provoke_cross_domain() -> tuple[str, str]:
    """Type 5: Steal ideas from a non-dev-tools project."""
    query = random.choice(CROSS_DOMAIN_QUERIES)
    url = (
        "https://api.github.com/search/repositories"
        f"?q={urllib.request.quote(query)}&sort=stars&order=desc&per_page=15"
    )
    data = _fetch_json(url)

    if not data or not data.get("items"):
        return ("Cross-Domain Steal", _cross_domain_fallback())

    # Filter out anything that looks like a dev tool
    dev_keywords = {"api", "sdk", "cli", "framework", "library", "devtool",
                    "developer", "coding", "compiler", "linter", "debugger"}
    candidates = [
        r for r in data["items"]
        if not any(kw in (r.get("description") or "").lower() for kw in dev_keywords)
    ]

    if not candidates:
        candidates = data["items"][:5]

    repo = random.choice(candidates)
    name = repo.get("full_name", "unknown")
    desc = repo.get("description", "No description") or "No description"
    stars = repo.get("stargazers_count", 0)
    html_url = repo.get("html_url", "")
    topics = ", ".join(repo.get("topics", [])[:5]) or "none listed"

    text = (
        f"This NON-dev-tool project has {stars:,} stars: {name}\n"
        f'Description: "{desc}"\n'
        f"Topics: {topics}. URL: {html_url}\n"
        f"\n"
        f"What idea from their approach could IndieStack steal?\n"
        f"Think about:\n"
        f"- How do they onboard new users?\n"
        f"- What's their value proposition in one line?\n"
        f"- How do they build community?\n"
        f"- What makes people star this repo?\n"
        f"- What's the IndieStack equivalent of whatever makes this project work?"
    )
    return ("Cross-Domain Steal", text)


def _cross_domain_fallback() -> str:
    """Static fallback when GitHub API is unreachable."""
    domains = [
        "a popular recipe-sharing platform",
        "a fitness tracking app with millions of users",
        "a language-learning tool",
        "a citizen science project",
        "a community-driven music platform",
    ]
    domain = random.choice(domains)
    return (
        f"GitHub API is unreachable. Think about {domain}.\n"
        f"\n"
        f"- What's the one thing they do brilliantly that IndieStack doesn't?\n"
        f"- How do they onboard users? How do they retain them?\n"
        f"- What's their equivalent of our MCP server — the thing that\n"
        f"  embeds them into their users' workflow?\n"
        f"- What idea could we literally steal and adapt?"
    )


# ---------------------------------------------------------------------------
# Output formatter
# ---------------------------------------------------------------------------

PROVOCATION_TYPES = {
    1: provoke_github_trending,
    2: provoke_tool_roleplay,
    3: provoke_constraint,
    4: provoke_inversion,
    5: provoke_cross_domain,
}

TYPE_NAMES = {
    1: "GitHub Trending",
    2: "Tool Roleplay",
    3: "Constraint Challenge",
    4: "Inversion",
    5: "Cross-Domain Steal",
}


def format_output(ptype: str, text: str) -> str:
    """Format the final provocation output."""
    date = datetime.now().strftime("%Y-%m-%d")
    return (
        f"=== PROVOCATION ({ptype}) ===\n"
        f"\n"
        f"{text}\n"
        f"\n"
        f"If this sparks a genuinely useful idea, act on it.\n"
        f"If not, write what you thought about to "
        f".orchestra/logs/{date}-thought.md and move on.\n"
        f"The point is the thinking, not the output."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Provocation Engine — creative stimulus for IndieStack agents"
    )
    parser.add_argument(
        "--type", type=int, choices=[1, 2, 3, 4, 5], default=None,
        help="Force a specific provocation type (1-5). Random if omitted."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show which type would be picked without making HTTP requests."
    )
    args = parser.parse_args()

    chosen_type = args.type or random.randint(1, 5)

    if args.dry_run:
        print(f"Would run provocation type {chosen_type}: {TYPE_NAMES[chosen_type]}")
        return

    generator = PROVOCATION_TYPES[chosen_type]
    ptype, text = generator()
    print(format_output(ptype, text))


if __name__ == "__main__":
    main()
