"""GitHub micro-tool hunter — finds small utility repos + their makers."""
import json
import subprocess
import re
import time

# Search queries targeting micro-tools across different niches
SEARCHES = [
    # File converters & CLI utilities
    "csv to json cli tool",
    "markdown to pdf converter",
    "image optimizer cli",
    "svg to png converter",
    "yaml to json cli",
    "log parser cli tool",
    "json formatter cli",
    "color palette generator cli",
    "qr code generator cli",
    "screenshot tool cli",
    # Dev utilities
    "env file manager",
    "git hooks manager",
    "localhost tunnel",
    "cron job monitor",
    "database migration tool lightweight",
    "sql formatter cli",
    "regex tester cli",
    "port scanner lightweight",
    "ssl certificate checker",
    "dns lookup cli tool",
    # Self-hosted micro SaaS
    "self-hosted url shortener",
    "self-hosted paste bin",
    "self-hosted file sharing",
    "self-hosted bookmarks",
    "self-hosted wiki lightweight",
    "self-hosted RSS reader",
    "self-hosted link aggregator",
    "self-hosted changelog",
    "self-hosted waitlist",
    "self-hosted feature flags",
]

CATEGORY_MAP = {
    # Keywords -> category slug
    "csv": "file-management", "json": "file-management", "yaml": "file-management",
    "converter": "file-management", "formatter": "file-management", "image": "file-management",
    "svg": "file-management", "pdf": "file-management", "markdown": "file-management",
    "optimizer": "file-management", "log parser": "file-management",
    "url shortener": "developer-tools", "paste": "developer-tools",
    "git": "developer-tools", "env": "developer-tools", "regex": "developer-tools",
    "sql": "developer-tools", "port": "developer-tools", "dns": "developer-tools",
    "ssl": "developer-tools", "localhost": "developer-tools", "tunnel": "developer-tools",
    "cron": "monitoring-uptime", "monitor": "monitoring-uptime",
    "screenshot": "developer-tools", "qr": "developer-tools", "color": "design-creative",
    "rss": "developer-tools", "wiki": "developer-tools", "bookmark": "developer-tools",
    "changelog": "developer-tools", "waitlist": "landing-pages",
    "feature flag": "developer-tools", "file shar": "file-management",
    "link": "developer-tools", "migration": "developer-tools",
}


def guess_category(name, desc, query):
    """Guess category from name, description, and search query."""
    text = f"{name} {desc} {query}".lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in text:
            return cat
    return "developer-tools"


def guess_tags(name, desc, lang, query):
    """Generate tags from repo metadata."""
    tags = set()
    text = f"{name} {desc} {query}".lower()

    if lang:
        tags.add(lang.lower())
    tags.add("open-source")

    tag_keywords = [
        "cli", "self-hosted", "converter", "formatter", "generator",
        "monitor", "lightweight", "api", "docker", "serverless",
    ]
    for kw in tag_keywords:
        if kw in text:
            tags.add(kw)

    return ",".join(sorted(tags)[:6])


def search_github(query, per_page=5):
    """Search GitHub repos via gh CLI."""
    try:
        import urllib.parse
        q = urllib.parse.quote(f"{query} stars:>5 stars:<5000")
        endpoint = f"search/repositories?q={q}&sort=stars&order=desc&per_page={per_page}"
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        return data.get("items", [])
    except Exception as e:
        print(f"  Error searching '{query}': {e}")
        return []


def get_user_info(username):
    """Get GitHub user info including email."""
    try:
        result = subprocess.run(
            ["gh", "api", f"users/{username}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {}
        return json.loads(result.stdout)
    except Exception:
        return {}


def main():
    all_tools = []
    seen_repos = set()
    seen_owners = set()

    for query in SEARCHES:
        print(f"Searching: {query}")
        repos = search_github(query, per_page=3)
        time.sleep(0.5)  # Rate limit

        for repo in repos:
            repo_name = repo["full_name"]
            if repo_name in seen_repos:
                continue
            seen_repos.add(repo_name)

            # Skip huge projects
            if repo.get("stargazers_count", 0) > 5000:
                continue
            # Skip forks
            if repo.get("fork"):
                continue

            owner_login = repo["owner"]["login"]

            # Get owner details if we haven't already
            owner_info = {}
            if owner_login not in seen_owners:
                owner_info = get_user_info(owner_login)
                seen_owners.add(owner_login)
                time.sleep(0.3)

            tool = {
                "name": repo["name"],
                "full_name": repo_name,
                "url": repo["html_url"],
                "description": (repo.get("description") or "")[:200],
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language") or "",
                "topics": repo.get("topics", []),
                "category_slug": guess_category(
                    repo["name"], repo.get("description") or "", query
                ),
                "tags": guess_tags(
                    repo["name"], repo.get("description") or "",
                    repo.get("language"), query
                ),
                "maker": {
                    "login": owner_login,
                    "name": owner_info.get("name") or owner_login,
                    "email": owner_info.get("email") or "",
                    "bio": (owner_info.get("bio") or "")[:300],
                    "url": owner_info.get("blog") or owner_info.get("html_url") or "",
                    "avatar": owner_info.get("avatar_url") or "",
                },
            }
            all_tools.append(tool)
            print(f"  Found: {repo_name} ({repo.get('stargazers_count', 0)} stars) - maker: {tool['maker']['name']} ({tool['maker']['email'] or 'no email'})")

    # Write results to JSON for the insert script
    output_path = "/home/patty/indiestack/github_tools_found.json"
    with open(output_path, "w") as f:
        json.dump(all_tools, f, indent=2)

    total = len(all_tools)
    with_email = sum(1 for t in all_tools if t["maker"]["email"])
    print(f"\nTotal tools found: {total}")
    print(f"Makers with email: {with_email}")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
