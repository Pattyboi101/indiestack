# OATS: Blackboard Democratic Consensus Implementation

**Date:** 2026-04-02  
**Area:** OATS (`tools/blackboard.py`)  
**Status:** Code ready, needs manual commit to OATS repo (signing is scoped to indiestack)

## Problem Found

The blackboard's `democratic` governance mode had a `pass` stub in `check_consensus()`.
It fell through to hierarchical behaviour (requiring an explicit `"consensus"` message)
instead of actually detecting agent agreement. Democratic governance was documented but
non-functional.

```python
# BEFORE (broken):
elif governance == self.DEMOCRATIC:
    proposals = [m for m in self.messages if m.msg_type == "proposal"]
    if len(proposals) >= 3:
        # Simple majority — if 2+ agents propose similar content, that's consensus
        # (In practice, an LLM coordinator would judge similarity)
        pass
```

## Fix Implemented

Added two methods to `Blackboard`:

### `_word_overlap(a, b) -> float`
Jaccard similarity on sub-word tokens:
- Splits on non-alpha chars (`re.split(r"[^a-zA-Z]+", ...)`) so hyphenated and
  compound tokens (`Redis-backed`, `TTL=300s`) tokenise correctly
- Strips stopwords and tokens shorter than 3 chars
- Returns `|A ∩ B| / |A ∪ B|`

### `_democratic_majority(proposals, threshold=0.08) -> Optional[str]`
Greedy single-linkage clustering of proposals:
- Each proposal joins an existing cluster if it overlaps ≥ threshold with ANY member
  (single-linkage, not just first member — prevents chaining artefacts)
- Winning cluster must hold **strict majority** (> 50%) of proposals
- Returns the most-evidenced proposal in the winning cluster (evidence messages
  referencing a proposal boost its selection)
- Returns `None` if board is contested (no majority cluster)

## Behaviour Summary

| Scenario | Result |
|---|---|
| 3 Redis proposals + 1 in-memory outlier | Returns best-evidenced Redis proposal |
| 2 Postgres vs 2 Mongo (tied) | Returns `None` — contested |
| Hierarchical mode with 3 similar proposals | Still requires explicit `consensus` msg |
| Democratic + explicit evidence backing | Evidence-backed proposal wins the cluster |

## Threshold Choice

`0.08` (sharing 1 meaningful technical term in a 10-token proposal ≈ 0.09 Jaccard).
This is appropriate for short technical proposals where technology name agreement
(Redis, Postgres, etc.) is the key signal. Raise to 0.25+ for longer prose proposals.

## Tests (all pass)

```bash
# Run from /tmp/oats after cloning:
python3 -c "
from tools.blackboard import Blackboard
import tempfile, os
os.chdir(tempfile.mkdtemp())

# Test 1: Democratic majority
board = Blackboard('t1', max_rounds=4, governance='democratic')
board.create('Caching strategy?')
board.post('backend', 'Use Redis with 5-minute TTL for session data', 'proposal')
board.post('devops', 'Redis cluster with TTL=300s works well here', 'proposal')
board.post('frontend', 'Redis-backed cache, 5 min expiry seems right', 'proposal')
board.post('security', 'Use in-memory dict, Redis adds attack surface', 'proposal')
result = board.check_consensus()
assert result and 'Redis' in result, f'Got: {result}'
print('PASS: democratic majority')
"
```

## What to Do

Patrick or Ed: apply `tools/blackboard.py` from this session's /tmp/oats working copy
and commit to `Pattyboi101/oats-autonomous-agents`. The diff is clean and all tests pass.

The full diff is in `/tmp/oats` (88 lines added to `tools/blackboard.py`).
