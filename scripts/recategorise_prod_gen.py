#!/usr/bin/env python3
"""
Generate a Python one-liner for applying recategorisation on production via flyctl ssh.

Usage:
    # Preview the SQL
    python3 scripts/recategorise_prod_gen.py

    # Execute on production (all in one command)
    python3 scripts/recategorise_prod_gen.py --execute

    # Execute in batches (safer for large sets)
    python3 scripts/recategorise_prod_gen.py --execute --batches
"""

import json
import subprocess
import sys
import os

MOVES_FILE = "scripts/moves.json"
BATCH_SIZE = 40  # tools per batch
FLYCTL = os.path.expanduser("~/.fly/bin/flyctl")

with open(MOVES_FILE) as f:
    moves = json.load(f)

print(f"Loaded {len(moves)} moves")

execute = "--execute" in sys.argv
use_batches = "--batches" in sys.argv

# Build all SQL statements
all_stmts = []
for m in moves:
    tid = m['id']
    new_cat = m['new_category_id']
    all_stmts.append(f"UPDATE tools SET category_id={new_cat} WHERE id={tid} AND upvote_count=0")
    all_stmts.append(f"UPDATE tool_categories SET category_id={new_cat} WHERE tool_id={tid} AND is_primary=1")

print(f"Total SQL statements: {len(all_stmts)} ({len(moves)} tools x 2)")

if not execute:
    print("\nDry run. Add --execute to apply on production.")
    print("Add --batches to execute in smaller chunks.\n")
    # Print first few
    for s in all_stmts[:10]:
        print(f"  {s}")
    print(f"  ... ({len(all_stmts) - 10} more)")
    sys.exit(0)

def run_batch(stmts, batch_label=""):
    """Run a batch of SQL statements on production."""
    sql_joined = ";".join(stmts)
    # Use a simple python3 -c that opens DB, executes, commits
    py_code = (
        f"import sqlite3; "
        f"c=sqlite3.connect('/data/indiestack.db'); "
        f"[c.execute(s) for s in \"{sql_joined}\".split(';') if s.strip()]; "
        f"c.commit(); "
        f"print('OK: {len(stmts)} stmts')"
    )
    cmd = [FLYCTL, "ssh", "console", "--app", "indiestack", "-C", f"python3 -c \"{py_code}\""]

    print(f"  Running {batch_label} ({len(stmts)} statements)...", end=" ", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    out = (result.stdout.strip() + " " + result.stderr.strip()).strip()
    print(out)
    return result.returncode == 0


if use_batches:
    # Split into batches
    success = 0
    for i in range(0, len(all_stmts), BATCH_SIZE * 2):
        batch = all_stmts[i:i + BATCH_SIZE * 2]
        label = f"batch {i // (BATCH_SIZE * 2) + 1}"
        if run_batch(batch, label):
            success += len(batch) // 2
    print(f"\nDone. {success} tools processed.")
else:
    # All at once
    run_batch(all_stmts, "all")
    print("Done.")
