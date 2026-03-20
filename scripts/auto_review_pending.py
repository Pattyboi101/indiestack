#!/usr/bin/env python3
"""Auto-review pending tools — approve real tools, reject libraries/low-quality.

Uses heuristics to classify pending tools:
- APPROVE: standalone tools/services/platforms with good descriptions
- REJECT: tiny libraries, algorithm implementations, bindings, wrappers
- SKIP: uncertain — left for manual review

Usage:
    python3 scripts/auto_review_pending.py --dry-run
    python3 scripts/auto_review_pending.py
"""

import os
import re
import sqlite3
import argparse

# ── Heuristics ───────────────────────────────────────────────────────────

# Descriptions containing these suggest a REAL TOOL (standalone product/service)
TOOL_SIGNALS = [
    'platform', 'service', 'server', 'dashboard', 'monitor', 'framework',
    'tool for', 'app for', 'application', 'system for', 'engine',
    'manager', 'management', 'interface', 'ide ', 'editor', 'cli ',
    'command-line', 'self-hosted', 'open source alternative',
    'alternative to', 'replacement for', 'drop-in replacement',
    'saas', 'api for', 'rest api', 'graphql', 'web app',
    'desktop app', 'mobile app', 'browser extension',
    'automation', 'orchestr', 'deploy', 'hosting',
    'analytics', 'tracking', 'logging', 'alerting',
    'authentication', 'authorization', 'oauth', 'sso',
    'payment', 'billing', 'invoice', 'subscription',
    'email', 'newsletter', 'smtp', 'transactional',
    'monitoring', 'uptime', 'status page', 'health check',
    'database', 'sql', 'nosql', 'key-value store',
    'search engine', 'full-text search', 'indexing',
    'proxy', 'load balancer', 'reverse proxy', 'gateway',
    'container', 'docker', 'kubernetes', 'k8s',
    'ci/cd', 'continuous integration', 'continuous delivery',
    'cms', 'content management', 'headless cms',
    'crm', 'customer relationship',
    'project management', 'task management', 'kanban',
    'file sharing', 'file transfer', 'storage',
    'chat', 'messaging', 'communication',
    'form builder', 'survey', 'feedback',
    'seo', 'crawler', 'scraper',
    'code review', 'linter', 'formatter',
    'testing framework', 'test runner', 'e2e test',
    'security scanner', 'vulnerability', 'penetration',
    'backup', 'sync', 'replication',
    'scheduler', 'cron', 'job queue', 'task queue',
    'notification', 'push notification', 'webhook',
    'pdf', 'document', 'report generator',
    'chart', 'visualization', 'graph',
]

# Descriptions containing these suggest a LIBRARY (not a standalone tool)
LIBRARY_SIGNALS = [
    'library for', 'package for', 'module for',
    'go implementation of', 'rust implementation of', 'python implementation of',
    'implementation of the', 'implementation in',
    'bindings for', 'binding for', 'wrapper for', 'wrapper around',
    'helper for', 'helpers for', 'utility for', 'utilities for',
    'collection of functions', 'set of functions', 'set of utilities',
    'algorithm', 'data structure', 'sorting', 'linked list', 'binary tree',
    'encoding', 'decoding', 'serialization library', 'deserialization',
    'parser for', 'parsing library',
    'provides a way to', 'provides an interface to',
    'thin wrapper', 'lightweight wrapper', 'simple wrapper',
    'port of', 'fork of',
    'types for', 'type definitions',
    'provides functions', 'provides methods',
    'codec', 'encoder', 'decoder',
]

# Names that suggest low-quality/non-tool entries
REJECT_NAME_PATTERNS = [
    r'^go-',  # go-xxx packages are usually libraries
    r'^rust-',
    r'^py-',
    r'^node-',
    r'^lib',
    r'-rs$',  # Rust crate suffix
    r'-go$',  # Go package suffix
    r'-js$',  # JS package suffix
    r'-py$',
]

# Names that suggest real products (override library signals)
PRODUCT_NAME_SIGNALS = [
    # Well-known tool patterns
    r'^[A-Z]',  # Starts with capital = branded product name
]


def classify_tool(name: str, description: str, url: str) -> str:
    """Classify a pending tool as 'approve', 'reject', or 'skip'."""
    desc_lower = description.lower() if description else ''
    name_lower = name.lower()

    # Too short description — likely junk
    if len(desc_lower) < 15:
        return 'reject'

    # Check for library signals first
    library_score = 0
    for signal in LIBRARY_SIGNALS:
        if signal in desc_lower:
            library_score += 1

    # Check for tool signals
    tool_score = 0
    for signal in TOOL_SIGNALS:
        if signal in desc_lower:
            tool_score += 1

    # Check name patterns
    for pattern in REJECT_NAME_PATTERNS:
        if re.search(pattern, name_lower):
            library_score += 1

    # Branded name (starts with capital, not just "Go-xxx")
    if name[0].isupper() and not name_lower.startswith(('go-', 'rust-', 'py-', 'node-')):
        tool_score += 0.5

    # Has its own website (not just GitHub)
    if url and 'github.com' not in url and 'gitlab.com' not in url:
        tool_score += 1

    # Decision
    if library_score >= 2 and tool_score == 0:
        return 'reject'
    if library_score > tool_score and library_score >= 1:
        return 'reject'
    if tool_score >= 2:
        return 'approve'
    if tool_score >= 1 and library_score == 0:
        return 'approve'

    # Uncertain — leave for manual review
    return 'skip'


def main():
    parser = argparse.ArgumentParser(description="Auto-review pending tools")
    _default_db = os.environ.get('INDIESTACK_DB_PATH',
                                  '/data/indiestack.db' if os.path.exists('/data/indiestack.db') else 'data/indiestack.db')
    parser.add_argument('--db', default=_default_db, help='Path to SQLite database')
    parser.add_argument('--dry-run', action='store_true', help='Preview without changing DB')
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    pending = conn.execute("SELECT id, name, slug, tagline, url FROM tools WHERE status='pending'").fetchall()
    print(f"Pending tools to review: {len(pending)}\n")

    approved = 0
    rejected = 0
    skipped = 0

    for tool in pending:
        verdict = classify_tool(tool['name'], tool['tagline'] or '', tool['url'] or '')

        if verdict == 'approve':
            if not args.dry_run:
                conn.execute("UPDATE tools SET status='approved' WHERE id=?", (tool['id'],))
            approved += 1
        elif verdict == 'reject':
            if not args.dry_run:
                conn.execute("UPDATE tools SET status='rejected' WHERE id=?", (tool['id'],))
            rejected += 1
        else:
            skipped += 1

    if not args.dry_run:
        conn.commit()

    total_approved = conn.execute("SELECT COUNT(*) FROM tools WHERE status='approved'").fetchone()[0]
    total_pending = conn.execute("SELECT COUNT(*) FROM tools WHERE status='pending'").fetchone()[0]
    total_rejected = conn.execute("SELECT COUNT(*) FROM tools WHERE status='rejected'").fetchone()[0]

    print(f"Results{' (dry run)' if args.dry_run else ''}:")
    print(f"  Auto-approved:  {approved}")
    print(f"  Auto-rejected:  {rejected}")
    print(f"  Needs review:   {skipped}")
    print(f"\nDB totals:")
    print(f"  Approved: {total_approved}")
    print(f"  Pending:  {total_pending}")
    print(f"  Rejected: {total_rejected}")

    # Show some examples of what was skipped (for manual review)
    if skipped > 0:
        uncertain = [t for t in pending if classify_tool(t['name'], t['tagline'] or '', t['url'] or '') == 'skip']
        print(f"\nSample uncertain tools (first 20):")
        for t in uncertain[:20]:
            print(f"  {t['name']}: {(t['tagline'] or '')[:80]}")

    conn.close()


if __name__ == "__main__":
    main()
