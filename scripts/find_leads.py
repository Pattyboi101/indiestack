#!/usr/bin/env python3
"""Find warm leads from GitHub stargazers of popular repos.

Scans stargazers of a given repo, checks their profiles for signals
that they're dev tool makers (bio keywords, company, repos), and
outputs a prioritised lead list for Ed.

Usage:
    python3 scripts/find_leads.py hesreallyhim/awesome-claude-code --pages 5
    python3 scripts/find_leads.py hesreallyhim/awesome-claude-code --pages 10 --output /tmp/leads.csv
"""

import argparse
import csv
import json
import sys
import time
import urllib.request
import urllib.error

MAKER_KEYWORDS = [
    "founder", "co-founder", "building", "maker", "built",
    "ceo", "cto", "developer tools", "devtools", "open source",
    "indie", "saas", "startup", "launched", "shipping",
    "cli", "sdk", "api", "framework", "mcp",
]

SKIP_KEYWORDS = ["student", "learning", "beginner", "intern"]


def get_stargazers(repo: str, page: int = 1, per_page: int = 100) -> list:
    url = f"https://api.github.com/repos/{repo}/stargazers?per_page={per_page}&page={page}"
    headers = {"Accept": "application/vnd.github.star+json"}
    token = None
    try:
        import os
        token = os.environ.get("GITHUB_TOKEN")
    except Exception:
        pass
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"Rate limited. Use GITHUB_TOKEN env var for 5000 req/hr.", file=sys.stderr)
        return []


def get_profile(username: str) -> dict:
    url = f"https://api.github.com/users/{username}"
    headers = {"Accept": "application/json"}
    try:
        import os
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
    except Exception:
        pass

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}


def score_profile(profile: dict) -> tuple:
    """Score a profile for likelihood of being a dev tool maker. Returns (score, reasons)."""
    score = 0
    reasons = []

    bio = (profile.get("bio") or "").lower()
    company = (profile.get("company") or "").lower()
    repos = profile.get("public_repos", 0)

    # Bio keyword matching
    for kw in MAKER_KEYWORDS:
        if kw in bio:
            score += 10
            reasons.append(f"bio:{kw}")

    # Skip students/beginners
    for kw in SKIP_KEYWORDS:
        if kw in bio:
            score -= 20
            reasons.append(f"skip:{kw}")

    # Has company
    if company and company not in ("@", "none", "n/a"):
        score += 5
        reasons.append("has_company")

    # Active developer
    if repos >= 20:
        score += 5
    if repos >= 50:
        score += 5

    # Has Twitter (reachable)
    if profile.get("twitter_username"):
        score += 5
        reasons.append("has_twitter")

    # Has blog/website (likely a maker)
    if profile.get("blog"):
        score += 5
        reasons.append("has_website")

    # Has email (contactable)
    if profile.get("email"):
        score += 3
        reasons.append("has_email")

    return score, reasons


def main():
    parser = argparse.ArgumentParser(description="Find warm leads from GitHub stargazers")
    parser.add_argument("repo", help="GitHub repo (owner/name)")
    parser.add_argument("--pages", type=int, default=3, help="Pages to scan (100 per page)")
    parser.add_argument("--min-score", type=int, default=15, help="Minimum score to include")
    parser.add_argument("--output", help="Output CSV path")
    args = parser.parse_args()

    leads = []
    total_scanned = 0

    for page in range(1, args.pages + 1):
        print(f"Scanning page {page}...", file=sys.stderr)
        stargazers = get_stargazers(args.repo, page=page)
        if not stargazers:
            break

        for sg in stargazers:
            user = sg.get("user", sg)
            username = user.get("login", "")
            if not username:
                continue

            total_scanned += 1
            profile = get_profile(username)
            if not profile:
                continue

            score, reasons = score_profile(profile)
            if score >= args.min_score:
                leads.append({
                    "username": username,
                    "score": score,
                    "name": profile.get("name") or "",
                    "bio": (profile.get("bio") or "")[:100],
                    "company": profile.get("company") or "",
                    "twitter": profile.get("twitter_username") or "",
                    "website": profile.get("blog") or "",
                    "email": profile.get("email") or "",
                    "repos": profile.get("public_repos", 0),
                    "reasons": ", ".join(reasons),
                    "github": f"https://github.com/{username}",
                })

            # Rate limit: ~0.5s per profile to stay under 60 req/min unauthenticated
            time.sleep(0.5)

        time.sleep(1)  # Between pages

    # Sort by score
    leads.sort(key=lambda x: x["score"], reverse=True)

    print(f"\nScanned {total_scanned} profiles, found {len(leads)} leads (score >= {args.min_score})\n",
          file=sys.stderr)

    # Output
    if args.output:
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=leads[0].keys() if leads else [])
            writer.writeheader()
            writer.writerows(leads)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        for lead in leads[:20]:
            print(f"  [{lead['score']:3d}] @{lead['username']:20s} {lead['bio'][:50]}")
            if lead["twitter"]:
                print(f"        Twitter: @{lead['twitter']}")
            if lead["website"]:
                print(f"        Web: {lead['website']}")


if __name__ == "__main__":
    main()
