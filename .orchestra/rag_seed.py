"""
IndieStack RAG Seed Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Indexes existing knowledge files into the LightRAG knowledge base.

Usage:
    python3 .orchestra/rag_seed.py              # index everything
    python3 .orchestra/rag_seed.py --minimal    # index only 5 critical files (fast)
    python3 .orchestra/rag_seed.py --dry-run    # list files without indexing
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import os
import pathlib
import sys

# ---------------------------------------------------------------------------
# Reuse the exact same RAG config from rag_server.py
# ---------------------------------------------------------------------------

# Ensure the orchestra dir is importable
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from rag_server import _build_rag  # noqa: E402


# ---------------------------------------------------------------------------
# File manifest — (path, tags) pairs
# ---------------------------------------------------------------------------

HOME = str(pathlib.Path.home())
PROJECT = os.path.join(HOME, "indiestack")
MEMORY_DIR = os.path.join(HOME, ".claude/projects/-home-patty-indiestack/memory")

MANIFEST: list[tuple[str, str]] = [
    # Core knowledge
    (f"{PROJECT}/.orchestra/memory/playbook.md", "playbook,shared"),
    (f"{PROJECT}/.claude/rules/gotchas.md", "gotcha,shared"),
    (f"{MEMORY_DIR}/sprint.md", "sprint,shared"),
    (f"{MEMORY_DIR}/decisions.md", "decision,shared"),
    (f"{MEMORY_DIR}/ed.md", "project,co-founder"),
    # Department memories
    (f"{PROJECT}/.orchestra/departments/frontend/memory.md", "department:frontend,memory"),
    (f"{PROJECT}/.orchestra/departments/backend/memory.md", "department:backend,memory"),
    (f"{PROJECT}/.orchestra/departments/devops/memory.md", "department:devops,memory"),
    (f"{PROJECT}/.orchestra/departments/content/memory.md", "department:content,memory"),
    (f"{PROJECT}/.orchestra/departments/mcp/memory.md", "department:mcp,memory"),
    # Orchestrator summaries
    (f"{PROJECT}/.orchestra/memory/frontend.md", "department:frontend,orchestrator"),
    (f"{PROJECT}/.orchestra/memory/backend.md", "department:backend,orchestrator"),
    (f"{PROJECT}/.orchestra/memory/devops.md", "department:devops,orchestrator"),
    (f"{PROJECT}/.orchestra/memory/content.md", "department:content,orchestrator"),
    (f"{PROJECT}/.orchestra/memory/mcp.md", "department:mcp,orchestrator"),
    # Directives
    (f"{PROJECT}/.orchestra/directives/done/awesome-claude-code-prep.md", "directive,project"),
    (f"{PROJECT}/.orchestra/directives/done/github-stars-action-plan.md", "directive,project"),
    # Research
    (f"{PROJECT}/.orchestra/logs/2026-04-03-research.md", "competitive,research"),
    (f"{PROJECT}/.orchestra/logs/2026-04-02-competitive-scan.md", "competitive,research"),
]


def _discover_feedback_files() -> list[tuple[str, str]]:
    """Glob for feedback memory files and assign tags."""
    pattern = os.path.join(MEMORY_DIR, "feedback_*.md")
    entries: list[tuple[str, str]] = []
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path).lower()
        # Gotcha-flavoured feedback files
        if any(kw in name for kw in ("gotcha", "clock", "email", "gate", "api")):
            tags = "feedback,gotcha"
        else:
            tags = "feedback,decision"
        entries.append((path, tags))
    return entries


def _build_full_manifest() -> list[tuple[str, str]]:
    """Return the complete list of (path, tags) to process."""
    return MANIFEST + _discover_feedback_files()


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


async def seed(dry_run: bool = False) -> None:
    manifest = _build_full_manifest()

    print(f"RAG seed: {len(manifest)} files in manifest\n")

    rag = _build_rag()

    if not dry_run:
        print("Initialising RAG storages...")
        await rag.initialize_storages()
        print()

    ok_count = 0
    skip_count = 0

    for filepath, tags in manifest:
        p = pathlib.Path(filepath)
        name = p.name

        # --- Skip checks ---
        if not p.exists():
            print(f"SKIP: {name} (file not found)")
            skip_count += 1
            continue

        text = p.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            print(f"SKIP: {name} (empty)")
            skip_count += 1
            continue

        char_count = len(text)

        if dry_run:
            print(f"  OK: {name} ({char_count} chars) [{tags}]")
            ok_count += 1
            continue

        # --- Prepend metadata header ---
        tag_list = ", ".join(t.strip() for t in tags.split(",") if t.strip())
        document = f"[Source: {name}] [Tags: {tag_list}]\n\n{text}"

        try:
            await rag.ainsert(document)
            print(f"  OK: {name} ({char_count} chars) [{tags}]")
            ok_count += 1
        except Exception as exc:
            print(f"SKIP: {name} (error: {type(exc).__name__}: {exc})")
            skip_count += 1

    if not dry_run:
        print("\nFinalising RAG storages...")
        await rag.finalize_storages()

    print(f"\nDone. OK: {ok_count}  Skipped: {skip_count}  Total: {ok_count + skip_count}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the IndieStack LightRAG knowledge base with existing files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files and sizes without actually indexing.",
    )
    args = parser.parse_args()
    asyncio.run(seed(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
