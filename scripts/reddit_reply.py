#!/usr/bin/env python3
"""
Reddit auto-reply tool using session cookie + old.reddit.com API.
No Reddit API app needed — just your browser session cookie.

Usage:
    # Fetch comments on a post
    python3 scripts/reddit_reply.py fetch <post_url>

    # Reply to a specific comment
    python3 scripts/reddit_reply.py reply <comment_id> "Your reply text"

    # List unreplied comments on a post
    python3 scripts/reddit_reply.py unreplied <post_url>

Setup:
    1. Log into Reddit in your browser
    2. Open dev tools (Ctrl+Shift+I) > Console
    3. Paste: document.cookie.split(';').find(c => c.includes('reddit_session'))
    4. Copy the value after reddit_session=
    5. Set it: export REDDIT_SESSION="your_token_here"

IMPORTANT: Never use em dashes in Reddit text -- they render as garbled characters.
           Use -- instead.

NOTE: Reddit blocks requests from cloud/datacenter IPs (403 Blocked).
      This script must be run from a residential network (your home WiFi),
      NOT from Fly.io, AWS, or similar cloud environments.
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse

SESSION_TOKEN = os.environ.get("REDDIT_SESSION", "")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _headers(with_auth=False):
    h = {"User-Agent": USER_AGENT}
    if with_auth and SESSION_TOKEN:
        h["Cookie"] = f"reddit_session={SESSION_TOKEN}"
    return h


def _get_json(url, auth=False):
    """Fetch JSON from a URL."""
    req = urllib.request.Request(url, headers=_headers(with_auth=auth))
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _get_modhash():
    """Get the modhash needed for POST requests."""
    data = _get_json("https://old.reddit.com/api/me.json", auth=True)
    return data.get("data", {}).get("modhash", "")


def _extract_post_id(url):
    """Extract the post ID from a Reddit URL."""
    # Handles: reddit.com/r/sub/comments/POST_ID/...
    m = re.search(r'/comments/([a-z0-9]+)', url)
    if m:
        return m.group(1)
    return None


def _flatten_comments(node, depth=0):
    """Recursively flatten the comment tree."""
    comments = []
    if isinstance(node, dict) and node.get("kind") == "t1":
        d = node["data"]
        comments.append({
            "id": d["id"],
            "fullname": d["name"],  # t1_xxxxx
            "author": d.get("author", "[deleted]"),
            "body": d.get("body", ""),
            "score": d.get("score", 0),
            "created": d.get("created_utc", 0),
            "depth": depth,
            "parent_id": d.get("parent_id", ""),
        })
        # Recurse into replies
        replies = d.get("replies")
        if isinstance(replies, dict):
            children = replies.get("data", {}).get("children", [])
            for child in children:
                comments.extend(_flatten_comments(child, depth + 1))
    elif isinstance(node, dict) and node.get("kind") == "Listing":
        for child in node.get("data", {}).get("children", []):
            comments.extend(_flatten_comments(child, depth))
    return comments


def fetch_comments(post_url):
    """Fetch all comments on a post. No auth needed."""
    post_id = _extract_post_id(post_url)
    if not post_id:
        print(f"Could not extract post ID from: {post_url}")
        return []

    # old.reddit.com JSON endpoint
    url = f"https://old.reddit.com/comments/{post_id}/.json?limit=500&sort=new"
    data = _get_json(url)

    if not isinstance(data, list) or len(data) < 2:
        print("Unexpected response format")
        return []

    # data[0] = post, data[1] = comments
    comments = _flatten_comments(data[1])
    return comments


def post_reply(comment_id, text):
    """Reply to a comment. Requires REDDIT_SESSION."""
    if not SESSION_TOKEN:
        print("ERROR: Set REDDIT_SESSION environment variable first.")
        print("See script header for instructions.")
        return False

    modhash = _get_modhash()
    if not modhash:
        print("ERROR: Could not get modhash. Session token may be expired.")
        return False

    # The thing_id needs the t1_ prefix for comments, t3_ for posts
    thing_id = comment_id if comment_id.startswith("t1_") or comment_id.startswith("t3_") else f"t1_{comment_id}"

    form_data = urllib.parse.urlencode({
        "thing_id": thing_id,
        "text": text,
        "uh": modhash,
        "api_type": "json",
    }).encode()

    req = urllib.request.Request(
        "https://old.reddit.com/api/comment",
        data=form_data,
        headers={**_headers(with_auth=True), "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            errors = result.get("json", {}).get("errors", [])
            if errors:
                print(f"Reddit API errors: {errors}")
                return False
            print("Reply posted successfully!")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()[:200]}")
        return False


def show_unreplied(post_url, our_username=None):
    """Show comments that haven't been replied to by us."""
    comments = fetch_comments(post_url)
    if not comments:
        print("No comments found.")
        return

    # Find comment IDs that have been replied to by our account
    our_reply_parents = set()
    if our_username:
        for c in comments:
            if c["author"].lower() == our_username.lower():
                our_reply_parents.add(c["parent_id"])

    # Show top-level comments we haven't replied to
    unreplied = [c for c in comments if c["depth"] == 0 and c["fullname"] not in our_reply_parents and c["author"] != "[deleted]"]

    if not unreplied:
        print("All comments have been replied to!")
        return

    print(f"\n{len(unreplied)} unreplied comments:\n")
    for c in unreplied:
        age = ""
        if c["created"]:
            mins = int((time.time() - c["created"]) / 60)
            if mins < 60:
                age = f"{mins}m ago"
            elif mins < 1440:
                age = f"{mins // 60}h ago"
            else:
                age = f"{mins // 1440}d ago"

        preview = c["body"][:120].replace("\n", " ")
        print(f"  [{c['id']}] u/{c['author']} ({c['score']}pts, {age})")
        print(f"    {preview}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "fetch":
        if len(sys.argv) < 3:
            print("Usage: python3 reddit_reply.py fetch <post_url>")
            return
        comments = fetch_comments(sys.argv[2])
        print(f"\n{len(comments)} comments found:\n")
        for c in comments:
            indent = "  " * c["depth"]
            preview = c["body"][:100].replace("\n", " ")
            print(f"{indent}[{c['id']}] u/{c['author']} ({c['score']}pts): {preview}")

    elif cmd == "reply":
        if len(sys.argv) < 4:
            print("Usage: python3 reddit_reply.py reply <comment_id> \"Your reply text\"")
            return
        post_reply(sys.argv[2], sys.argv[3])

    elif cmd == "unreplied":
        if len(sys.argv) < 3:
            print("Usage: python3 reddit_reply.py unreplied <post_url> [your_username]")
            return
        username = sys.argv[3] if len(sys.argv) > 3 else None
        show_unreplied(sys.argv[2], username)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
