#!/usr/bin/env python3
"""
Patch script — apply synonym additions from improvement loop pass 172.

Applies to:
  src/indiestack/db.py         — remove 2 dead duplicate entries; add 12 new synonyms
  scripts/test_search_routing.py — add 12 corresponding test cases (total 126)

Run from repo root:
  python3 scripts/apply_synonyms_172.py

Safe to re-run (idempotent — checks before patching).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent

# ── db.py patches ──────────────────────────────────────────────────────────────────────────────

DB_PY = REPO / "src/indiestack/db.py"

# Lines to remove (dead duplicate entries overridden by correct values at pass 167)
DEAD_ENTRIES = [
    '    # AI — EleutherAI lm-evaluation-harness (canonical open LLM benchmark runner)\n',
    '    "lm-eval": "ai",                # lm-eval — EleutherAI LM evaluation harness; "lm-eval alternative" → AI & Automation\n',
    '    "lmeval": "ai",                 # compound form — "lmeval benchmarks", "lmeval harness" → AI & Automation\n',
]

# Block to insert before the closing `}` of _CAT_SYNONYMS
NEW_SYNONYMS = '''    # Testing — PR/CI code review automation
    "danger": "testing",            # DangerJS — codify PR review norms in CI; "danger alternative" → Testing Tools
    "dangerjs": "testing",          # explicit form — "dangerjs setup", "dangerjs alternative" → Testing Tools
    # DevOps — conventional commits bigram (hyphenated form already mapped; spaced form missed)
    "conventional commits": "devops",  # "conventional commits spec", "conventional commits tools" → DevOps
    # AI — computer use API (Anthropic/OpenAI computer-use; often searched as hyphenated)
    "computer-use": "ai",           # "computer-use api", "computer-use claude" → AI & Automation
    # Background Jobs — Temporal.io compact form (Temporal is mapped but not temporalio)
    "temporalio": "background",     # "temporalio setup", "temporalio alternative" → Background Jobs
    # AI — older AI agents still searched (hyphenated and variant forms)
    "auto-gpt": "ai",               # hyphenated — "auto-gpt alternative", "auto-gpt setup" → AI & Automation
    "babyagi": "ai",                # BabyAGI — early AI agent; "babyagi alternative" → AI & Automation
    "openai-swarm": "ai",           # OpenAI Swarm — experimental multi-agent; "openai-swarm setup" → AI & Automation
    # AI — local LLM runners (variant forms)
    "lm-studio": "ai",              # LM Studio hyphenated — "lm-studio download", "lm-studio vs ollama" → AI & Automation
    "gpt4all": "ai",                # GPT4All (Nomic AI) — "gpt4all alternative", "gpt4all setup" → AI & Automation
    # AI Dev Tools — Claude Code CLI (Anthropic; frequently searched by agents building tooling)
    "claude-code": "aidev",         # "claude-code alternative", "claude code mcp" → AI Dev Tools
    "claudecode": "aidev",          # compact — "claudecode setup", "claudecode hooks" → AI Dev Tools
'''

# Anchor: insert the new synonyms block before the last `}` of _CAT_SYNONYMS
INSERT_BEFORE = '    "smartlook": "analytics",       # Smartlook — session recording + event analytics; "smartlook alternative" → Analytics\n}'


# ── test_search_routing.py patches ──────────────────────────────────────────────────────────────────────────────

TEST_PY = REPO / "scripts/test_search_routing.py"

NEW_TEST_CASES = '''    # PR/CI automation (added May 2026)
    ("dangerjs setup", "testing"),
    ("danger alternative", "testing"),
    # Conventional commits (bigram form)
    ("conventional commits spec", "devops"),
    # Computer use
    ("computer-use api", "ai"),
    # Temporal.io compact form
    ("temporalio alternative", "background"),
    # Old AI agents (hyphenated/variant forms)
    ("auto-gpt setup", "ai"),
    ("babyagi alternative", "ai"),
    ("openai-swarm framework", "ai"),
    # Local LLM runners
    ("lm-studio vs ollama", "ai"),
    ("gpt4all download", "ai"),
    # Claude Code
    ("claude-code alternative", "aidev"),
    ("claudecode mcp setup", "aidev"),
'''

TEST_INSERT_BEFORE = '    # LLM cache bigrams (bigram lookup added db.py pass 170)\n    ("semantic cache llm", "caching"),\n    ("llm cache layer", "caching"),\n]'
TEST_NEW_ENDING = '    # LLM cache bigrams (bigram lookup added db.py pass 170)\n    ("semantic cache llm", "caching"),\n    ("llm cache layer", "caching"),\n' + NEW_TEST_CASES + ']'


def patch_db_py():
    content = DB_PY.read_text()

    # Check if already patched
    if '"danger": "testing"' in content:
        print("  db.py: already patched (danger synonym found) — skipping")
        return False

    # Remove dead entries
    for dead in DEAD_ENTRIES:
        if dead in content:
            content = content.replace(dead, "")
            print(f"  db.py: removed dead entry: {dead.strip()[:60]}")

    # Insert new synonyms before closing `}`
    if INSERT_BEFORE not in content:
        print("  db.py: ERROR — anchor not found, cannot insert synonyms")
        return False

    replacement = INSERT_BEFORE.replace(
        '}',
        NEW_SYNONYMS + '}'
    )
    content = content.replace(INSERT_BEFORE, replacement)
    DB_PY.write_text(content)
    print("  db.py: inserted 12 new synonyms ✓")
    return True


def patch_test_py():
    content = TEST_PY.read_text()

    # Check if already patched
    if '"dangerjs setup"' in content:
        print("  test_search_routing.py: already patched — skipping")
        return False

    if TEST_INSERT_BEFORE not in content:
        print("  test_search_routing.py: ERROR — anchor not found")
        return False

    content = content.replace(TEST_INSERT_BEFORE, TEST_NEW_ENDING)
    TEST_PY.write_text(content)
    print("  test_search_routing.py: added 12 test cases ✓")
    return True


def main():
    print("Applying synonym patch 172...")
    db_changed = patch_db_py()
    test_changed = patch_test_py()

    if db_changed or test_changed:
        print("\nPatch applied. Verify with:")
        print("  python3 -c \"import ast; ast.parse(open('src/indiestack/db.py').read()); print('syntax OK')\"")
        print("  python3 scripts/test_search_routing.py")
        print("\nThen commit:")
        print("  git add src/indiestack/db.py scripts/test_search_routing.py")
        print("  git commit -m 'fix: 14 _CAT_SYNONYMS gaps + routing tests (172nd pass)'")
    else:
        print("Nothing to patch.")


if __name__ == "__main__":
    main()
