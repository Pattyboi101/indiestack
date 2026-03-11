"""GitHub micro-tool hunter round 2 — different niches."""
import json
import subprocess
import re
import time
import urllib.parse

SEARCHES = [
    # Data & science
    "bioinformatics cli tool",
    "csv cleanup tool",
    "data validation cli",
    "json schema validator cli",
    "geojson tool cli",
    # Media & content
    "podcast rss generator",
    "static blog generator minimal",
    "ebook converter cli",
    "video thumbnail generator",
    "audio waveform generator",
    "favicon generator cli",
    "placeholder image generator",
    # Privacy & security
    "password generator cli",
    "secret scanner",
    "license checker cli",
    "privacy policy generator",
    "cookie consent self-hosted",
    # DevOps micro tools
    "dockerfile linter",
    "docker compose validator",
    "terraform linter",
    "kubernetes yaml validator",
    "nginx config generator",
    "systemd service generator",
    "github action linter",
    # Web tools
    "meta tag generator",
    "robots txt generator",
    "sitemap generator cli",
    "web accessibility checker cli",
    "lighthouse cli alternative",
    "open graph preview tool",
    # Productivity
    "pomodoro timer cli",
    "time tracker cli",
    "invoice generator cli",
    "receipt ocr tool",
    "habit tracker self-hosted",
    "self-hosted note taking",
    # Communication
    "self-hosted newsletter",
    "webhook tester self-hosted",
    "self-hosted notification server",
    "push notification self-hosted",
]

CATEGORY_MAP = {
    "bioinformatics": "developer-tools", "csv": "file-management",
    "json": "file-management", "geojson": "file-management",
    "validation": "developer-tools", "validator": "developer-tools",
    "podcast": "developer-tools", "blog": "landing-pages",
    "ebook": "file-management", "video": "design-creative",
    "audio": "design-creative", "favicon": "design-creative",
    "image": "design-creative", "placeholder": "design-creative",
    "password": "authentication", "secret": "developer-tools",
    "license": "developer-tools", "privacy": "developer-tools",
    "cookie": "developer-tools", "consent": "developer-tools",
    "docker": "developer-tools", "terraform": "developer-tools",
    "kubernetes": "developer-tools", "nginx": "developer-tools",
    "systemd": "developer-tools", "github action": "developer-tools",
    "meta tag": "seo-tools", "robots": "seo-tools",
    "sitemap": "seo-tools", "accessibility": "developer-tools",
    "lighthouse": "monitoring-uptime", "open graph": "seo-tools",
    "pomodoro": "project-management", "time track": "project-management",
    "invoice": "invoicing-billing", "receipt": "invoicing-billing",
    "habit": "project-management", "note": "project-management",
    "newsletter": "email-marketing", "webhook": "api-tools",
    "notification": "developer-tools", "push": "developer-tools",
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

    output_path = "/home/patty/indiestack/github_tools_found2.json"
    with open(output_path, "w") as f:
        json.dump(all_tools, f, indent=2)

    total = len(all_tools)
    with_email = sum(1 for t in all_tools if t["maker"]["email"])
    print(f"\nTotal: {total}, With email: {with_email}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
