"""GitHub micro-tool hunter round 4 — education, writing, calendar, email, analytics, search, auth, automation, maps, media, compliance, misc dev."""
import json
import subprocess
import re
import time
import urllib.parse

SEARCHES = [
    # Education & learning
    "flashcard app self-hosted",
    "quiz generator cli",
    "spaced repetition self-hosted",
    "language learning tool open-source",
    # Writing & content
    "grammar checker cli",
    "spell checker cli",
    "readability score cli",
    "text diff tool cli",
    "plagiarism checker self-hosted",
    # Calendar & scheduling
    "calendar self-hosted lightweight",
    "booking system self-hosted",
    "appointment scheduler self-hosted",
    # Email & messaging
    "email template builder self-hosted",
    "transactional email self-hosted",
    "smtp testing tool",
    "email validation cli",
    # Analytics & metrics
    "web analytics self-hosted lightweight",
    "event tracking self-hosted",
    "ab testing self-hosted",
    "funnel analytics self-hosted",
    # Search
    "search engine self-hosted lightweight",
    "full text search tool",
    "elasticsearch alternative lightweight",
    # Authentication
    "oauth server lightweight",
    "two factor authentication cli",
    "jwt tool cli",
    "single sign on self-hosted",
    # Automation & workflow
    "task queue lightweight self-hosted",
    "workflow engine self-hosted",
    "webhook relay self-hosted",
    "zapier alternative self-hosted",
    # Maps & location
    "geocoding tool cli",
    "map tile server self-hosted",
    "ip geolocation self-hosted",
    # Media processing
    "image compression cli",
    "image resize cli",
    "watermark tool cli",
    "video compression cli",
    "audio transcription self-hosted",
    # Compliance & legal
    "gdpr compliance tool",
    "terms of service generator",
    "accessibility audit cli",
    # Miscellaneous dev
    "env file manager cli",
    "dotfile manager",
    "terminal dashboard",
    "regex tester cli",
    "codemod tool",
]

CATEGORY_MAP = {
    "flashcard": "project-management", "quiz": "project-management",
    "spaced": "project-management", "language learn": "project-management",
    "grammar": "developer-tools", "spell": "developer-tools",
    "readability": "developer-tools", "diff": "developer-tools",
    "plagiarism": "developer-tools",
    "calendar": "project-management", "booking": "project-management",
    "appointment": "project-management", "scheduler": "project-management",
    "email template": "email-marketing", "transactional": "email-marketing",
    "smtp": "email-marketing", "email valid": "email-marketing",
    "analytics": "monitoring-uptime", "event track": "monitoring-uptime",
    "ab test": "monitoring-uptime", "funnel": "monitoring-uptime",
    "search engine": "developer-tools", "full text": "developer-tools",
    "elasticsearch": "developer-tools",
    "oauth": "authentication", "two factor": "authentication",
    "jwt": "authentication", "sign on": "authentication",
    "task queue": "developer-tools", "workflow": "developer-tools",
    "webhook relay": "api-tools", "zapier": "developer-tools",
    "geocod": "developer-tools", "map tile": "developer-tools",
    "geolocation": "developer-tools",
    "image compress": "design-creative", "image resize": "design-creative",
    "watermark": "design-creative", "video compress": "design-creative",
    "transcription": "developer-tools",
    "gdpr": "developer-tools", "terms of service": "developer-tools",
    "accessibility": "developer-tools",
    "env file": "developer-tools", "dotfile": "developer-tools",
    "terminal": "developer-tools", "regex": "developer-tools",
    "codemod": "developer-tools",
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

    output_path = "/home/patty/indiestack/github_tools_found4.json"
    with open(output_path, "w") as f:
        json.dump(all_tools, f, indent=2)

    total = len(all_tools)
    with_email = sum(1 for t in all_tools if t["maker"]["email"])
    print(f"\nTotal: {total}, With email: {with_email}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
