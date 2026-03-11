"""GitHub micro-tool hunter round 6 — different niches."""
import json
import subprocess
import re
import time
import urllib.parse

SEARCHES = [
    "translation tool cli",
    "i18n tool cli",
    "locale file manager",
    "diff viewer cli",
    "hex editor cli",
    "hash generator cli",
    "uuid generator cli",
    "barcode generator cli",
    "ascii art generator cli",
    "figlet alternative",
    "cowsay alternative",
    "presentation tool markdown cli",
    "slide deck generator markdown",
    "terminal presentation tool",
    "incident management self-hosted",
    "alerting tool self-hosted lightweight",
    "ping monitor self-hosted",
    "dependency update tool",
    "package vulnerability scanner",
    "npm audit alternative",
    "crud generator cli",
    "code scaffolding tool",
    "kanban board self-hosted",
    "todo app self-hosted",
    "project management self-hosted lightweight",
    "password manager self-hosted",
    "secrets manager self-hosted",
    "vault alternative self-hosted",
    "comment system self-hosted",
    "disqus alternative self-hosted",
    "captcha alternative self-hosted",
    "font awesome alternative",
    "icon pack open source",
    "emoji picker tool",
    "markdown editor self-hosted",
    "knowledge base self-hosted",
    "documentation site generator",
    "api gateway lightweight self-hosted",
    "service mesh lightweight",
    "container registry self-hosted",
    "ci cd self-hosted lightweight",
    "release management tool",
    "feature toggle self-hosted",
    "database gui self-hosted",
    "redis gui self-hosted",
]

CATEGORY_MAP = {
    "translat": "developer-tools", "i18n": "developer-tools",
    "locale": "developer-tools",
    "diff": "developer-tools", "hex": "developer-tools",
    "hash": "developer-tools", "uuid": "developer-tools",
    "barcode": "developer-tools", "ascii art": "design-creative",
    "figlet": "design-creative", "cowsay": "design-creative",
    "presentation": "design-creative", "slide": "design-creative",
    "terminal present": "developer-tools",
    "incident": "monitoring-uptime", "alert": "monitoring-uptime",
    "ping": "monitoring-uptime",
    "dependency": "developer-tools", "vulnerability": "developer-tools",
    "npm": "developer-tools",
    "crud": "developer-tools", "scaffold": "developer-tools",
    "kanban": "project-management", "todo": "project-management",
    "project manage": "project-management",
    "password manage": "authentication", "secret": "authentication",
    "vault": "authentication",
    "comment": "developer-tools", "disqus": "developer-tools",
    "captcha": "developer-tools",
    "font": "design-creative", "icon": "design-creative",
    "emoji": "design-creative",
    "markdown editor": "developer-tools", "knowledge": "developer-tools",
    "documentation site": "developer-tools",
    "api gateway": "api-tools", "service mesh": "developer-tools",
    "container": "developer-tools", "registry": "developer-tools",
    "ci cd": "developer-tools", "release": "developer-tools",
    "feature toggle": "developer-tools",
    "database gui": "developer-tools", "redis": "developer-tools",
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

    output_path = "/home/patty/indiestack/github_tools_found6.json"
    with open(output_path, "w") as f:
        json.dump(all_tools, f, indent=2)

    total = len(all_tools)
    with_email = sum(1 for t in all_tools if t["maker"]["email"])
    print(f"\nTotal: {total}, With email: {with_email}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
