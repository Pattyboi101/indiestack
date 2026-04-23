#!/usr/bin/env python3
"""
Validate _CAT_SYNONYMS in db.py.

Checks:
1. Duplicate keys — Python silently keeps the LAST value, breaking the earlier
   synonym. This caused the "rollout" bug (Apr 2026) where the correct mapping
   was silently overridden.
2. Coverage summary — count of synonyms per category short-name so thin areas
   are visible at a glance.
3. Invalid short-names — values that don't correspond to a known category alias.

Usage:
    python3 scripts/validate_synonyms.py
    python3 scripts/validate_synonyms.py --fix   # print corrected duplicates
"""

import ast
import re
import sys
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "src" / "indiestack" / "db.py"

# Known short-name → category slug mappings (from backend CLAUDE.md)
VALID_SHORT_NAMES = {
    "authentication", "payments", "analytics", "email", "invoicing",
    "monitoring", "forms", "scheduling", "cms", "support",
    "seo", "file", "crm", "developer", "ai", "design", "feedback",
    "social", "project", "landing", "api", "aidev", "games", "learning",
    "publishing", "creative", "database", "background", "hosting",
    "devops", "frontend", "caching", "mcp", "boilerplate", "featureflags",
    "logging", "notifications", "localization", "cli", "docs",
    "testing", "security", "search", "queue", "media", "maps",
    # short-name aliases (checked by LIKE on category name)
    "message",   # Message Queue category
    "newsletters",  # Newsletters & Content
    "customer",  # Customer Support (live chat tools)
    "feature",   # Feature Flags (LIKE '%feature%')
    "documentation",  # Documentation
}


def extract_cat_synonyms_raw(db_text: str) -> list[tuple[int, str, str]]:
    """Return (line_no, key, value) for every line inside _CAT_SYNONYMS."""
    in_dict = False
    results = []
    for i, line in enumerate(db_text.splitlines(), 1):
        stripped = line.strip()
        if "_CAT_SYNONYMS" in line and "dict[str, str]" in line:
            in_dict = True
            continue
        if in_dict:
            if stripped == "}":
                break
            # Match   "key": "value",  (with optional comment)
            m = re.match(r'^\s*"([^"]+)"\s*:\s*"([^"]+)"', line)
            if m:
                results.append((i, m.group(1), m.group(2)))
    return results


def main():
    fix_mode = "--fix" in sys.argv
    db_text = DB_PATH.read_text()
    entries = extract_cat_synonyms_raw(db_text)

    if not entries:
        print("ERROR: Could not parse _CAT_SYNONYMS — check regex or file path.")
        sys.exit(1)

    print(f"Parsed {len(entries)} _CAT_SYNONYMS entries from {DB_PATH.name}")

    # ── 1. Duplicate keys ─────────────────────────────────────────────────────
    seen: dict[str, tuple[int, str]] = {}
    duplicates: list[tuple[int, str, str, int, str]] = []
    for lineno, key, value in entries:
        if key in seen:
            first_lineno, first_value = seen[key]
            duplicates.append((lineno, key, value, first_lineno, first_value))
        seen[key] = (lineno, value)

    if duplicates:
        print(f"\n🔴  DUPLICATE KEYS ({len(duplicates)} found):")
        for lineno, key, value, first_lineno, first_value in duplicates:
            status = "SAME" if value == first_value else "DIFFERENT"
            print(f"  Line {lineno:5d}: \"{key}\" → \"{value}\"  "
                  f"[first at line {first_lineno}: \"{first_value}\"] — {status}")
        if fix_mode:
            print("\n💡 Fix: remove the earlier duplicate (keep last value).")
    else:
        print("✅  No duplicate keys found.")

    # ── 2. Invalid short-names ────────────────────────────────────────────────
    invalid = [(lineno, key, value) for lineno, key, value in entries
               if value not in VALID_SHORT_NAMES]
    if invalid:
        print(f"\n⚠️  POSSIBLY INVALID SHORT-NAMES ({len(invalid)} found):")
        for lineno, key, value in invalid[:20]:
            print(f"  Line {lineno:5d}: \"{key}\" → \"{value}\"")
        if len(invalid) > 20:
            print(f"  ... and {len(invalid) - 20} more")
    else:
        print("✅  All short-names are valid.")

    # ── 3. Coverage summary ───────────────────────────────────────────────────
    counts = Counter(value for _, _, value in entries)
    print(f"\n📊  Coverage by category short-name ({len(counts)} distinct):")
    for name, count in sorted(counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(count // 5, 40)
        print(f"  {name:20s} {count:4d}  {bar}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\nTotal synonyms: {len(entries)}  |  Duplicates: {len(duplicates)}  |  "
          f"Suspect values: {len(invalid)}")
    sys.exit(1 if duplicates else 0)


if __name__ == "__main__":
    main()
