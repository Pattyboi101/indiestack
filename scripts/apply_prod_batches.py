#!/usr/bin/env python3
"""
Apply recategorisation to production in batches via flyctl SSH.

Encodes SQL as base64 to avoid shell quoting issues with flyctl ssh -C.

Usage:
    python3 scripts/apply_prod_batches.py              # dry run
    python3 scripts/apply_prod_batches.py --execute     # apply on production
"""

import json
import base64
import subprocess
import sys
import time

MOVES_FILE = "scripts/moves.json"
BATCH_SIZE = 25  # tools per batch (keep commands short)
FLYCTL = "/home/patty/.fly/bin/flyctl"

with open(MOVES_FILE) as f:
    moves = json.load(f)

print(f"Loaded {len(moves)} moves from {MOVES_FILE}")

# Build batches
batches = []
for i in range(0, len(moves), BATCH_SIZE):
    chunk = moves[i:i + BATCH_SIZE]
    # Build a Python script that will run on production
    script_lines = [
        "import sqlite3",
        "c=sqlite3.connect('/data/indiestack.db')",
        "n=0",
    ]
    for m in chunk:
        t, cat = m["id"], m["new_category_id"]
        script_lines.append(f"c.execute('UPDATE tools SET category_id={cat} WHERE id={t} AND upvote_count=0')")
        # Delete old primary, then insert new one (avoids UNIQUE constraint if tool already has this category as secondary)
        script_lines.append(f"c.execute('DELETE FROM tool_categories WHERE tool_id={t} AND is_primary=1')")
        script_lines.append(f"c.execute('INSERT OR REPLACE INTO tool_categories (tool_id,category_id,is_primary) VALUES ({t},{cat},1)')")
        script_lines.append("n+=1")
    script_lines.append("c.commit()")
    script_lines.append("c.close()")
    script_lines.append(f"print('batch {i // BATCH_SIZE + 1}: ' + str(n) + ' tools updated')")

    script = "\n".join(script_lines)
    encoded = base64.b64encode(script.encode()).decode()
    batches.append((i // BATCH_SIZE + 1, len(chunk), encoded))

print(f"Split into {len(batches)} batches of ~{BATCH_SIZE} tools each\n")

if "--execute" not in sys.argv:
    print("Dry run. Add --execute to apply on production.")
    for num, count, enc in batches:
        print(f"  Batch {num}: {count} tools, encoded={len(enc)} chars")
    sys.exit(0)

total_ok = 0
for num, count, encoded in batches:
    # The remote command: decode base64, exec the Python script
    remote_cmd = f"python3 -c 'import base64;exec(base64.b64decode(\"{encoded}\").decode())'"

    cmd = [FLYCTL, "ssh", "console", "--app", "indiestack", "-C", remote_cmd]

    print(f"Batch {num}/{len(batches)} ({count} tools)...", end=" ", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        err = result.stderr.strip()
        # Filter out the "Connecting..." and "Warning:" noise
        output_lines = [l for l in output.split("\n") if l and not l.startswith("Connecting")]
        err_lines = [l for l in err.split("\n") if l and "Warning:" not in l and "Metrics" not in l]
        clean_out = " ".join(output_lines)
        clean_err = " ".join(err_lines)

        if result.returncode == 0:
            print(clean_out or "OK")
            total_ok += count
        else:
            print(f"FAILED: {clean_out} | {clean_err}")
    except Exception as e:
        print(f"ERROR: {e}")
    time.sleep(1)

print(f"\nDone. {total_ok}/{len(moves)} tools processed on production.")
