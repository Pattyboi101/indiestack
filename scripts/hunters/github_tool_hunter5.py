"""GitHub micro-tool hunter round 5 — different niches."""
import json
import subprocess
import re
import time
import urllib.parse

SEARCHES = [
    "shopping cart self-hosted",
    "product catalog self-hosted",
    "inventory management self-hosted lightweight",
    "storefront self-hosted lightweight",
    "dns server lightweight self-hosted",
    "domain monitoring tool",
    "whois lookup cli",
    "api documentation generator cli",
    "readme generator cli",
    "man page generator",
    "code formatter cli",
    "dead code detector",
    "complexity analyzer cli",
    "dependency checker cli",
    "bundle size analyzer",
    "web scraper lightweight cli",
    "rss to json",
    "price tracker self-hosted",
    "web archive self-hosted",
    "reverse proxy lightweight",
    "vpn server self-hosted lightweight",
    "tunnel tool self-hosted",
    "port scanner cli lightweight",
    "chart generator cli",
    "ascii chart cli",
    "diagram generator cli text",
    "gantt chart generator",
    "yaml to json cli",
    "pastebin self-hosted",
    "code snippet sharing self-hosted",
    "file drop self-hosted",
    "clipboard sync self-hosted",
    "photo gallery self-hosted lightweight",
    "image hosting self-hosted",
    "music player self-hosted",
    "spotify alternative self-hosted",
    "link shortener self-hosted",
    "bookmark manager self-hosted",
    "link checker cli",
    "uptime monitor self-hosted lightweight",
    "screen recorder cli",
    "terminal recorder",
    "gif recorder cli",
    "project template generator",
    "boilerplate generator cli",
]

CATEGORY_MAP = {
    "shopping": "invoicing-billing", "cart": "invoicing-billing",
    "product": "invoicing-billing", "inventory": "invoicing-billing",
    "storefront": "invoicing-billing",
    "dns": "developer-tools", "domain": "developer-tools",
    "whois": "developer-tools",
    "documentation": "developer-tools", "readme": "developer-tools",
    "man page": "developer-tools",
    "formatter": "developer-tools", "dead code": "developer-tools",
    "complexity": "developer-tools", "dependency": "developer-tools",
    "bundle": "developer-tools",
    "scraper": "developer-tools", "rss": "developer-tools",
    "price track": "monitoring-uptime",
    "archive": "file-management",
    "proxy": "developer-tools", "vpn": "developer-tools",
    "tunnel": "developer-tools", "port scan": "developer-tools",
    "chart": "design-creative", "ascii": "developer-tools",
    "diagram": "design-creative", "gantt": "project-management",
    "yaml": "developer-tools",
    "pastebin": "developer-tools", "snippet": "developer-tools",
    "file drop": "file-management", "clipboard": "developer-tools",
    "photo": "design-creative", "gallery": "design-creative",
    "image host": "design-creative",
    "music": "design-creative", "spotify": "design-creative",
    "link short": "developer-tools", "bookmark": "project-management",
    "link check": "seo-tools",
    "uptime": "monitoring-uptime",
    "screen record": "design-creative", "terminal record": "developer-tools",
    "gif": "design-creative",
    "template": "developer-tools", "boilerplate": "developer-tools",
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

    output_path = "/home/patty/indiestack/github_tools_found5.json"
    with open(output_path, "w") as f:
        json.dump(all_tools, f, indent=2)

    total = len(all_tools)
    with_email = sum(1 for t in all_tools if t["maker"]["email"])
    print(f"\nTotal: {total}, With email: {with_email}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
