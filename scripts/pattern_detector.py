#!/usr/bin/env python3
"""Phase 4 — Proactive pattern detection over 7-day windows.

Analyzes production data to surface repeating patterns:
  1. Search queries with high zero-result rates
  2. Categories with declining adoption week-over-week
  3. Autoloop commits thrashing the same files
  4. Tools shown frequently but never adopted

Runs daily (24h cooldown). Called from autonomous_loop.sh after the 6 iterations.

Usage:
    python3 scripts/pattern_detector.py                # run with cooldown
    python3 scripts/pattern_detector.py --force         # bypass cooldown
    python3 scripts/pattern_detector.py --from-autoloop # called by autoloop
    python3 scripts/pattern_detector.py --create-directives  # also create directives
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---

STATE_FILE = Path(".orchestra/pattern_state.json")
LOG_DIR = Path(".orchestra/logs")
DIRECTIVES_PENDING = Path(".orchestra/directives/pending")
DIRECTIVES_TEMPLATES = Path(".orchestra/directives/templates")

# Thresholds (tune these as we learn signal quality)
MIN_SEARCHES_FOR_GAP = 5         # Minimum searches to flag a query
GAP_RATE_THRESHOLD = 0.4         # 40% zero-result rate
MIN_ADOPTIONS_FOR_DECLINE = 5    # Minimum last-week adoptions to flag decline
DECLINE_THRESHOLD = 0.5          # 50% week-over-week drop
THRASH_COMMIT_THRESHOLD = 3      # Commits to same area in 7 days
MIN_SHOWN_FOR_ADOPTION = 10      # Minimum times shown to flag non-adoption
COOLDOWN_HOURS = 24              # Hours between runs


# --- SSH Query (same pattern as event_reactor.py) ---

def query_prod(sql: str) -> str:
    """Run a HARDCODED SQL query against production via Fly SSH.

    WARNING: Only pass string literals. Never interpolate user/external data.
    """
    escaped_sql = sql.replace('"', '\\"').replace("'", "'\\''")
    cmd = f"""~/.fly/bin/fly ssh console -a indiestack -C 'python3 -c "
import sqlite3
conn = sqlite3.connect(\\"/data/indiestack.db\\")
for r in conn.execute(\\"{escaped_sql}\\").fetchall():
    print(\\"|\\".join(str(x) for x in r))
conn.close()
"'"""
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True, timeout=30
        )
        lines = [l for l in result.stdout.strip().split("\n")
                 if l and not l.startswith(("Warning:", "Connecting", "Error:"))]
        return "\n".join(lines)
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"  SSH error: {e}")
        return ""


# --- State Management ---

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {"last_run": None}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def should_run(state: dict, force: bool) -> bool:
    if force:
        return True
    last_run = state.get("last_run")
    if not last_run:
        return True
    try:
        last_dt = datetime.fromisoformat(last_run)
        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
        return elapsed >= COOLDOWN_HOURS
    except (ValueError, TypeError):
        return True


# --- Detector 1: Low-Confidence Search Queries ---

def detect_low_confidence() -> list:
    """Find queries with high zero-result rates over 7 days."""
    print("  [1/4] Checking low-confidence search queries...")
    result = query_prod(
        "SELECT normalized_query, COUNT(*) as searches, "
        "SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) as zero_results, "
        "ROUND(AVG(result_count), 1) as avg_results "
        "FROM search_logs "
        "WHERE created_at >= datetime('now', '-7 days') "
        "AND normalized_query IS NOT NULL AND normalized_query != '' "
        "GROUP BY normalized_query "
        f"HAVING searches >= {MIN_SEARCHES_FOR_GAP} "
        "ORDER BY (zero_results * 1.0 / searches) DESC "
        "LIMIT 20"
    )
    findings = []
    for line in result.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 4:
            query = parts[0]
            searches = int(parts[1])
            zero_results = int(parts[2])
            avg_results = parts[3]
            gap_rate = zero_results / searches if searches > 0 else 0
            if gap_rate >= GAP_RATE_THRESHOLD:
                findings.append({
                    "query": query,
                    "searches": searches,
                    "zero_results": zero_results,
                    "gap_rate": round(gap_rate * 100, 1),
                    "avg_results": avg_results,
                })
    print(f"    Found {len(findings)} low-confidence queries")
    return findings


# --- Detector 2: Category Adoption Decline ---

def detect_category_decline() -> list:
    """Find categories with declining adoption week-over-week."""
    print("  [2/4] Checking category adoption trends...")

    # This week
    this_week = query_prod(
        "SELECT category, COUNT(*) as cnt "
        "FROM mcp_query_outcomes "
        "WHERE outcome = 'adopted' "
        "AND created_at >= strftime('%s', 'now', '-7 days') "
        "GROUP BY category"
    )
    # Last week
    last_week = query_prod(
        "SELECT category, COUNT(*) as cnt "
        "FROM mcp_query_outcomes "
        "WHERE outcome = 'adopted' "
        "AND created_at >= strftime('%s', 'now', '-14 days') "
        "AND created_at < strftime('%s', 'now', '-7 days') "
        "GROUP BY category"
    )

    def parse_counts(raw: str) -> dict:
        counts = {}
        for line in raw.split("\n"):
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) >= 2:
                cat = parts[0] or "(uncategorized)"
                try:
                    counts[cat] = int(parts[1])
                except ValueError:
                    pass
        return counts

    this_counts = parse_counts(this_week)
    last_counts = parse_counts(last_week)

    findings = []
    for cat, last_cnt in last_counts.items():
        if last_cnt < MIN_ADOPTIONS_FOR_DECLINE:
            continue
        this_cnt = this_counts.get(cat, 0)
        if last_cnt > 0:
            change = (this_cnt - last_cnt) / last_cnt
            if change <= -DECLINE_THRESHOLD:
                findings.append({
                    "category": cat,
                    "this_week": this_cnt,
                    "last_week": last_cnt,
                    "change_pct": round(change * 100, 1),
                })

    print(f"    Found {len(findings)} declining categories")
    return findings


# --- Detector 3: Autoloop Thrashing ---

def detect_thrashing() -> list:
    """Find files repeatedly modified with similar commit messages (local git, no SSH)."""
    print("  [3/4] Checking autoloop thrashing...")
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=7 days ago",
             "--", "src/indiestack/"],
            capture_output=True, text=True, timeout=15,
            cwd=str(Path.cwd())
        )
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
    except Exception as e:
        print(f"    Git error: {e}")
        return []

    # Group commits by file-path stem extracted from commit message
    # Pattern: "fix: improve search mappings for X" or "fix: update X"
    pattern_counts = {}
    for line in lines:
        # Remove commit hash
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue
        msg = parts[1].lower()
        # Extract the action prefix (first 4 words after fix:/feat:/chore:)
        match = re.match(r'(fix|feat|chore):\s+(.+)', msg)
        if match:
            action = match.group(2)
            # Normalize: take first 4 words as the "stem"
            words = action.split()[:4]
            stem = " ".join(words)
            pattern_counts.setdefault(stem, []).append(line)

    findings = []
    for stem, commits in pattern_counts.items():
        if len(commits) >= THRASH_COMMIT_THRESHOLD:
            findings.append({
                "pattern": stem,
                "commit_count": len(commits),
                "commits": commits[:5],  # cap at 5 examples
            })

    print(f"    Found {len(findings)} thrashing patterns")
    return findings


# --- Detector 4: High Views, Low Adoption ---

def detect_high_view_low_adopt() -> list:
    """Find tools frequently returned in search but never adopted."""
    print("  [4/4] Checking high-view/low-adoption tools...")

    # Get tools that appear in mcp_query_outcomes results
    # tools_returned is JSON array of slugs
    result = query_prod(
        "SELECT tools_returned, outcome, adopted_slug "
        "FROM mcp_query_outcomes "
        "WHERE created_at >= strftime('%s', 'now', '-7 days') "
        "AND tools_returned IS NOT NULL AND tools_returned != '[]'"
    )

    shown_counts = {}  # slug -> times shown
    adopted_set = set()  # slugs that were adopted

    for line in result.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            tools_json = parts[0]
            outcome = parts[1]
            adopted_slug = parts[2] if parts[2] != "None" else None

            try:
                slugs = json.loads(tools_json)
            except (json.JSONDecodeError, TypeError):
                continue

            for slug in slugs:
                shown_counts[slug] = shown_counts.get(slug, 0) + 1

            if outcome == "adopted" and adopted_slug:
                adopted_set.add(adopted_slug)

    findings = []
    for slug, shown in sorted(shown_counts.items(), key=lambda x: -x[1]):
        if shown >= MIN_SHOWN_FOR_ADOPTION and slug not in adopted_set:
            findings.append({
                "slug": slug,
                "times_shown": shown,
                "times_adopted": 0,
            })

    # Cap at top 15
    findings = findings[:15]
    print(f"    Found {len(findings)} high-view/low-adoption tools")
    return findings


# --- Report Writer ---

def write_report(findings: dict) -> Path:
    """Write findings to .orchestra/logs/patterns-YYYY-MM-DD.md."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = LOG_DIR / f"patterns-{date_str}.md"

    low_conf = findings.get("low_confidence", [])
    decline = findings.get("category_decline", [])
    thrash = findings.get("thrashing", [])
    high_view = findings.get("high_view_low_adopt", [])

    total = len(low_conf) + len(decline) + len(thrash) + len(high_view)

    lines = [
        f"# Pattern Report -- {date_str}",
        "",
        "## Summary",
        f"- {len(low_conf)} low-confidence queries detected",
        f"- {len(decline)} categories declining",
        f"- {len(thrash)} thrashing areas",
        f"- {len(high_view)} high-view/low-adoption tools",
        "",
    ]

    # Low-confidence queries
    lines.append("## Low-Confidence Queries")
    if low_conf:
        lines.append("| Query | Searches | Gap Rate | Avg Results |")
        lines.append("|-------|----------|----------|-------------|")
        for f in low_conf:
            lines.append(f"| {f['query']} | {f['searches']} | {f['gap_rate']}% | {f['avg_results']} |")
    else:
        lines.append("(none detected)")
    lines.append("")

    # Category decline
    lines.append("## Category Decline")
    if decline:
        lines.append("| Category | This Week | Last Week | Change |")
        lines.append("|----------|-----------|-----------|--------|")
        for f in decline:
            lines.append(f"| {f['category']} | {f['this_week']} | {f['last_week']} | {f['change_pct']}% |")
    else:
        lines.append("(none detected)")
    lines.append("")

    # Thrashing
    lines.append("## Autoloop Thrashing")
    if thrash:
        for f in thrash:
            lines.append(f"### Pattern: \"{f['pattern']}\" ({f['commit_count']} commits)")
            for c in f["commits"]:
                lines.append(f"- `{c}`")
            lines.append("")
    else:
        lines.append("(none detected)")
    lines.append("")

    # High view / low adoption
    lines.append("## High View / Low Adoption Tools")
    if high_view:
        lines.append("| Tool | Times Shown | Adoptions |")
        lines.append("|------|-------------|-----------|")
        for f in high_view:
            lines.append(f"| {f['slug']} | {f['times_shown']} | {f['times_adopted']} |")
    else:
        lines.append("(none detected)")
    lines.append("")

    report_path.write_text("\n".join(lines))
    print(f"  Report written: {report_path}")
    return report_path


# --- Directive Creation (opt-in) ---

def sanitize_for_directive(val: str) -> str:
    """Strip characters that could influence agent command execution."""
    return re.sub(r'[`$\\{}\x00-\x1f]', '', str(val))[:200]


def create_directive(template_name: str, replacements: dict):
    """Instantiate a directive template into pending/."""
    template_path = DIRECTIVES_TEMPLATES / f"{template_name}.md"
    if not template_path.exists():
        print(f"  Directive template not found: {template_path}")
        return
    content = template_path.read_text()
    for key, val in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", str(val))
    DIRECTIVES_PENDING.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = DIRECTIVES_PENDING / f"{template_name}-{timestamp}.md"
    out_path.write_text(content)
    print(f"  Created directive: {out_path.name}")


def maybe_create_directives(findings: dict):
    """Create directives for high-signal findings."""
    # Low-confidence queries with >60% gap rate and >= 10 searches
    for f in findings.get("low_confidence", []):
        if f["gap_rate"] > 60 and f["searches"] >= 10:
            create_directive("gap_anomaly", {
                "gap_rate": str(f["gap_rate"]),
                "gap_count": str(f["zero_results"]),
                "total_queries": str(f["searches"]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Phase 4 -- Proactive pattern detection")
    parser.add_argument("--from-autoloop", action="store_true",
                        help="Called from autoloop (respects cooldown)")
    parser.add_argument("--force", action="store_true",
                        help="Bypass cooldown and run immediately")
    parser.add_argument("--create-directives", action="store_true",
                        help="Create directives for actionable findings")
    args = parser.parse_args()

    state = load_state()

    if not should_run(state, args.force):
        elapsed = "unknown"
        if state.get("last_run"):
            try:
                last_dt = datetime.fromisoformat(state["last_run"])
                hrs = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                elapsed = f"{hrs:.1f}h"
            except (ValueError, TypeError):
                pass
        print(f"  Pattern detector: skipping (last run {elapsed} ago, cooldown {COOLDOWN_HOURS}h)")
        return

    print("Pattern Detector -- Phase 4 Proactive Analysis")
    print(f"  Analyzing 7-day window...")

    findings = {}

    # Run all 4 detectors
    findings["low_confidence"] = detect_low_confidence()
    findings["category_decline"] = detect_category_decline()
    findings["thrashing"] = detect_thrashing()
    findings["high_view_low_adopt"] = detect_high_view_low_adopt()

    # Write report
    report_path = write_report(findings)

    # Optionally create directives
    if args.create_directives:
        maybe_create_directives(findings)

    # Update state
    total = sum(len(v) for v in findings.values())
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_report"] = str(report_path)
    state["last_findings_count"] = total
    save_state(state)

    print(f"  Done. {total} pattern(s) detected.")


if __name__ == "__main__":
    main()
