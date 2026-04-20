---
name: fact-check
description: Fact-check an email from Ed against the IndieStack codebase for hallucinations
argument-hint: "[paste email text]"
context: fork
agent: Explore
allowed-tools:
  - Read
  - Grep
  - Glob
  - "Bash(ls:*)"
---

# Fact-Check Ed's Email

Ed (co-founder) uses an AI assistant that frequently hallucinates. Your job is to verify every factual claim in his email against the actual IndieStack codebase.

## Input

The email text is provided in `$ARGUMENTS`. If empty, stop and ask for the email text.

## Email Text

```
$ARGUMENTS
```

## Procedure

### Step 1: Extract Claims

Read the email carefully and extract every factual claim that can be checked against code. Categories include:

- **File paths**: Any mention of a file or directory (e.g., "src/indiestack/routes/foo.py")
- **Feature status**: Claims that something is "done", "pending", "broken", "not yet built", "needs work"
- **Route names**: URL paths like /explore, /api/something, /dashboard
- **Script names**: References to Python scripts, shell scripts, CLI commands
- **Database fields/tables**: Column names, table names, schema details
- **Deployment status**: Claims about what's live, what's on Fly, environment variables
- **Function/class names**: References to specific code symbols
- **Configuration**: Claims about settings, environment variables, dependencies
- **URLs**: External URLs, API endpoints, webhook paths
- **Marketing/content**: Claims about content in marketing/ or other docs

Number each claim for the truth table.

### Step 2: Verify Each Claim

For each extracted claim, search the codebase methodically:

**Key locations to check:**
- Routes: `src/indiestack/routes/*.py`
- DB schema and queries: `src/indiestack/db.py`
- Main app wiring: `src/indiestack/main.py`
- Auth: `src/indiestack/auth.py`
- Payments: `src/indiestack/payments.py`
- Email: `src/indiestack/email.py`
- MCP server: `src/indiestack/mcp_server.py`
- Root-level scripts: `/home/patty/indiestack/*.py`
- Scripts directory: `/home/patty/indiestack/scripts/`
- Marketing docs: `/home/patty/indiestack/marketing/*.md`
- Static assets: `src/indiestack/static/`
- Config: `pyproject.toml`, `fly.toml`, `Dockerfile`, `server.json`
- Architecture doc: `/home/patty/indiestack/ARCHITECTURE.md`

**Verification strategies:**
- File exists? Use `Glob` for the exact path, then broader patterns if not found.
- Feature built? Use `Grep` to search for route decorators, function names, HTML content.
- DB field exists? Read `db.py` and search for the column/table name.
- Route exists? Grep for `@router.get("/<path>")` or `@router.post(...)` across route files.
- Script exists? Use `Glob` for `*.py` at root and in `scripts/`.
- Function exists? Grep for `def function_name` across the codebase.

Be thorough. If Ed says "the /foobar route is broken", first check if /foobar even exists before evaluating whether it's broken.

### Step 3: Output Truth Table

Present findings as a numbered truth table. Use exactly this format:

```
## Fact-Check Results

1. TRUE: [claim as stated] -- [file/line evidence proving it]
2. FALSE: [claim as stated] -- [what's actually the case, with file paths]
3. UNVERIFIABLE: [claim as stated] -- [why code alone can't confirm this]
```

Use these markers consistently:
- **TRUE** -- Claim is accurate per the codebase
- **FALSE** -- Claim is wrong; state what's actually true
- **UNVERIFIABLE** -- Can't confirm from code (e.g., runtime state, external service status, analytics numbers)

### Step 4: Action Summary

After the truth table, provide:

```
## Summary

**Already Done (Ed may not realize):**
- [list features/files that exist but Ed thinks are pending]

**Actually Needs Work:**
- [list things Ed correctly identified as incomplete]

**Hallucinated (ignore these):**
- [list files, features, or paths Ed mentioned that don't exist at all]

**Ambiguous / Needs Clarification:**
- [list claims where Ed might be right but the evidence is unclear]
```

## Rules

- Check EVERY factual claim, no matter how small. Ed's bot hallucinates details.
- Always show the actual file path or code snippet as evidence.
- If a file path is wrong but something similar exists, note the correct path.
- If Ed says something "needs to be added" but it already exists, flag it clearly.
- Don't trust Ed's path references -- always verify from scratch.
- Keep output concise but include enough evidence to be convincing.
- When in doubt, mark as UNVERIFIABLE rather than guessing.
