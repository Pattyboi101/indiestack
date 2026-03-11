"""GitHub micro-tool hunter round 3 — database, API, git, testing, design, ops niches."""
import json
import subprocess
import re
import time
import urllib.parse

SEARCHES = [
    # Database & data
    "sqlite viewer cli",
    "database migration tool lightweight",
    "schema visualizer cli",
    "csv to json converter cli",
    "sql formatter cli",
    "database backup tool self-hosted",
    # API & backend
    "api mock server lightweight",
    "rest api testing cli",
    "graphql playground self-hosted",
    "openapi generator cli",
    "api rate limiter self-hosted",
    "grpc tool cli",
    # Git & version control
    "changelog generator cli",
    "git hooks manager",
    "commit message generator",
    "git stats cli",
    "monorepo tool lightweight",
    "git worktree tool",
    # Testing & quality
    "load testing tool lightweight",
    "screenshot testing cli",
    "code coverage tool lightweight",
    "mutation testing tool",
    "api fuzzer cli",
    # Design & frontend
    "color palette generator cli",
    "css minifier cli",
    "svg optimizer cli",
    "icon set generator",
    "font subsetting tool",
    "tailwind component library indie",
    # File & storage
    "file sharing self-hosted",
    "s3 browser self-hosted",
    "backup tool self-hosted lightweight",
    "file converter cli lightweight",
    "pdf tool cli",
    # Monitoring & ops
    "status page self-hosted",
    "log viewer self-hosted",
    "error tracking self-hosted",
    "health check tool self-hosted",
    "cron job manager self-hosted",
    # Communication & social
    "rss reader self-hosted lightweight",
    "chat bot framework lightweight",
    "form builder self-hosted",
    "survey tool self-hosted",
    "feedback widget self-hosted",
    # Finance & business
    "budget tracker self-hosted",
    "expense tracker cli",
    "url shortener self-hosted",
]

CATEGORY_MAP = {
    "sqlite": "developer-tools", "database": "developer-tools",
    "schema": "developer-tools", "csv": "file-management",
    "sql": "developer-tools", "backup": "file-management",
    "api": "api-tools", "rest": "api-tools", "mock": "api-tools",
    "graphql": "api-tools", "openapi": "api-tools",
    "rate limit": "api-tools", "grpc": "api-tools",
    "changelog": "developer-tools", "git": "developer-tools",
    "commit": "developer-tools", "monorepo": "developer-tools",
    "worktree": "developer-tools",
    "load test": "monitoring-uptime", "screenshot": "developer-tools",
    "coverage": "developer-tools", "mutation": "developer-tools",
    "fuzzer": "developer-tools",
    "color": "design-creative", "css": "design-creative",
    "svg": "design-creative", "icon": "design-creative",
    "font": "design-creative", "tailwind": "design-creative",
    "file shar": "file-management", "s3": "file-management",
    "converter": "file-management", "pdf": "file-management",
    "status page": "monitoring-uptime", "log": "monitoring-uptime",
    "error track": "monitoring-uptime", "health check": "monitoring-uptime",
    "cron": "developer-tools",
    "rss": "developer-tools", "chat": "developer-tools",
    "form": "developer-tools", "survey": "developer-tools",
    "feedback": "developer-tools",
    "budget": "invoicing-billing", "expense": "invoicing-billing",
    "url short": "developer-tools",
}


def guess_category(name, desc, query):
    text = f"{name} {desc} {query}".lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in text:
            return cat
    return "developer-tools"


def guess_tags(name, desc, lang, query):
    tags = set()
    text = f"{name} {desc} {query}".lower()
    if lang:
        tags.add(lang.lower())
    tags.add("open-source")
    for kw in ["cli", "self-hosted", "converter", "generator", "linter", "docker", "api", "lightweight", "privacy"]:
        if kw in text:
            tags.add(kw)
    return ",".join(sorted(tags)[:6])


def search_github(query, per_page=3):
    try:
        q = urllib.parse.quote(f"{query} stars:>3 stars:<5000")
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
        print(f"  Error: {e}")
        return []


def get_user_info(username):
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
        time.sleep(0.5)

        for repo in repos:
            repo_name = repo["full_name"]
            if repo_name in seen_repos:
                continue
            seen_repos.add(repo_name)

            if repo.get("stargazers_count", 0) > 5000:
                continue
            if repo.get("fork"):
                continue

            owner_login = repo["owner"]["login"]
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
                "category_slug": guess_category(repo["name"], repo.get("description") or "", query),
                "tags": guess_tags(repo["name"], repo.get("description") or "", repo.get("language"), query),
                "maker": {
                    "login": owner_login,
                    "name": owner_info.get("name") or owner_login,
                    "email": owner_info.get("email") or "",
                    "bio": (owner_info.get("bio") or "")[:300],
                    "url": owner_info.get("blog") or owner_info.get("html_url") or "",
                },
            }
            all_tools.append(tool)
            print(f"  Found: {repo_name} ({repo.get('stargazers_count', 0)}*) - {tool['maker']['name']} ({tool['maker']['email'] or 'no email'})")

    output_path = "/home/patty/indiestack/github_tools_found3.json"
    with open(output_path, "w") as f:
        json.dump(all_tools, f, indent=2)

    total = len(all_tools)
    with_email = sum(1 for t in all_tools if t["maker"]["email"])
    print(f"\nTotal: {total}, With email: {with_email}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
