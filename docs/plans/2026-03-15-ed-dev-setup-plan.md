# Ed's Claude Code Architecture — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up Ed with a full Claude Code development environment via a shared private GitHub repo, command hub on Fly, and cleaned project knowledge files.

**Architecture:** Private `indiestack-dev-setup` repo with symlinked skills/memory, a `bootstrap.md` for Ed's Claude to self-install, and a FastAPI command hub deployed to the existing GovLink Fly app. Communication via email skills + shared Telegram + command hub messaging.

**Tech Stack:** Python/FastAPI, SQLite, Fly.io, GitHub, Telegram Bot API

**Design doc:** `docs/plans/2026-03-15-ed-dev-setup-design.md`

---

## Phase 1: File Cleanup (parallelizable — all independent)

### Task 1: Clean workflow-ideas.md

**Files:**
- Modify: `/home/patty/.claude/projects/-home-patty/memory/workflow-ideas.md`

**Step 1: Read current file and identify DONE items**

Everything marked DONE or "Implemented" gets stripped. Keep only:
- Open ideas that haven't been built
- Section headers for context

**Step 2: Rewrite file — keep only open items**

Target ~30 lines. Keep:
- Deploy-on-Push (GitHub Actions) — not yet done
- Maker Outreach Tracker — not yet done
- Content Calendar — not yet done
- Staging Environment — future
- Performance Dashboard — future
- SEO Monitoring — future
- Periodic Maintenance Tasks (re-run indexer/enricher/health/pairs)

Remove all "Implemented" sections, R-numbered history, "Next Session Candidates" that are done, the strategic pivot recap.

**Step 3: Verify file reads clean**

Read the file back, confirm no orphaned headers or references to deleted content.

**Step 4: Commit**

```bash
cd ~/indiestack && git add -p && git commit -m "clean: strip done items from workflow-ideas.md for shared dev setup"
```

---

### Task 2: Clean indiestack-project.md

**Files:**
- Modify: `/home/patty/.claude/projects/-home-patty/memory/indiestack-project.md`

**Step 1: Update outdated information**

- MCP version: v1.5.0 -> v1.7.0
- Tool count: verify current number
- Update MCP feature list to include trust tiers, agent cards, citation milestones (v1.6.0-v1.7.0)

**Step 2: Strip historical noise**

Remove/condense:
- "Terracotta naming is legacy" — just delete
- "was `indiestack.fly.dev`" — just say domain is indiestack.ai
- "PH banner fully removed" — delete (it's removed, done)
- "Upvote threshold lowered from 5 to 3" — delete
- "changed from 301 to prevent browser caching if .ai goes down" — condense to "302 redirect from .fly.dev"
- Marketplace selling details — condense to one line: "Stripe Connect infrastructure built, direct selling paused"
- UI polish minutiae — keep design-relevant items, strip changelog-style notes

**Step 3: Verify no broken references**

Check that MEMORY.md links still work, no orphaned "See also" references.

**Step 4: Commit**

```bash
git commit -m "clean: update indiestack-project.md — v1.7.0, strip historical notes"
```

---

### Task 3: Merge indiestack-details.md into project.md

**Files:**
- Modify: `/home/patty/.claude/projects/-home-patty/memory/indiestack-project.md`
- Delete: `/home/patty/.claude/projects/-home-patty/memory/indiestack-details.md`
- Modify: `/home/patty/.claude/projects/-home-patty/memory/MEMORY.md` (remove details.md link)

**Step 1: Read indiestack-details.md and identify what's still useful**

Keep:
- Auth & Identity section (GitHub OAuth, email verification) — if not already in project.md
- Design System token consolidation summary (useful reference)
- Growth Features that aren't already covered

Delete:
- Feature History R17-R21 (changelog, not reference)
- Marketplace Details (already condensed in project.md from Task 2)
- Reddit & Marketing (just reference `marketing/` directory)
- MCP section (duplicates project.md)
- Misc Details (too specific, not useful for day-to-day)

**Step 2: Merge useful sections into indiestack-project.md**

Add under appropriate headers. Don't duplicate.

**Step 3: Delete indiestack-details.md**

```bash
rm /home/patty/.claude/projects/-home-patty/memory/indiestack-details.md
```

**Step 4: Update MEMORY.md — remove the link to deleted file**

Remove the line: `- [IndieStack Details](indiestack-details.md) — marketplace internals, auth, growth features, Reddit playbook, MCP distribution`

**Step 5: Commit**

```bash
git commit -m "clean: merge indiestack-details.md into project.md, remove duplicate file"
```

---

### Task 4: Clean pro-subscription-architecture.md

**Files:**
- Modify: `/home/patty/.claude/projects/-home-patty/memory/pro-subscription-architecture.md`

**Step 1: Strip sensitive data**

Remove:
- All personal email addresses from "Warmest Leads" section (Marie Martens, Jack Arturo, etc.)
- Stripe price IDs (these are in code, not needed in memory)
- Webhook endpoint IDs

Keep:
- Architecture decisions (Pro $19/mo, Founder $99/yr, 50 seats)
- Research findings (the 7 key insights)
- Strategic next steps
- Lead TIER descriptions (without emails) — e.g., "6 Tier 1 claim requests, 4 Tier 2 registered users"

**Step 2: Verify the file still makes strategic sense without the stripped data**

Read back, confirm it conveys the architecture and strategy without exposing personal info.

**Step 3: Commit**

```bash
git commit -m "clean: strip personal emails and Stripe IDs from pro-subscription-architecture.md"
```

---

### Task 5: Update IndieStack repo CLAUDE.md with technical patterns

**Files:**
- Modify: `/home/patty/indiestack/CLAUDE.md`

**Step 1: Read current CLAUDE.md**

It currently has design context only (brand, tokens, fonts, constraints). No technical patterns.

**Step 2: Add Technical Patterns section below existing content**

```markdown
## Technical Patterns

### Stack
- Python 3 / FastAPI / SQLite (WAL mode) / Fly.io
- Use `python3` not `python` on all systems
- Pure Python string HTML templates (f-strings in route files)
- All CSS in components.py :root block or inline

### Auth
- Always use `request.state.user` (populated by middleware via sessions table)
- Never query users table by session_token — that column doesn't exist
- Use `d = request.state.db` to avoid shadowing the db module import

### Database
- Parameterized queries always: `await db.execute("...WHERE x=?", (val,))`
- Never f-string user input into SQL
- aiosqlite Row objects are dict-like: use `row['col']` not `row[0]`
- ALTER TABLE ADD COLUMN can't have UNIQUE — add column first, then CREATE UNIQUE INDEX separately

### Deploy
- `cd ~/indiestack && ~/.fly/bin/flyctl deploy --remote-only`
- Always run `python3 smoke_test.py` before deploying
- Use `--buildkit` flag if depot builder times out
- Commit before deploying — never deploy uncommitted work
- Deploy with background execution (builds take 2-4 minutes)

### Code Style
- Route files return HTMLResponse with f-string templates
- Shared components live in components.py (page_shell, tool_card, etc.)
- Design tokens are CSS variables in :root — never hardcode hex colors
- Touch targets >= 44px for mobile
- New routes: create file in src/indiestack/routes/, add router in main.py
```

**Step 3: Verify file parses correctly, no broken markdown**

**Step 4: Commit**

```bash
cd ~/indiestack && git add CLAUDE.md && git commit -m "docs: add technical patterns to CLAUDE.md for multi-dev workflow"
```

---

## Phase 2: Create Dev Setup Repo

### Task 6: Create GitHub repo and base structure

**Step 1: Create the private repo on GitHub**

```bash
gh repo create Pattyboi101/indiestack-dev-setup --private --description "Shared Claude Code dev setup for IndieStack team" --clone
```

**Step 2: Create directory structure**

```bash
cd ~/indiestack-dev-setup
mkdir -p shared-skills/{status,backup,brainstorm,publish-mcp,deep-research,humanizer,email-pat,email-ed,hub}
mkdir -p shared-memory
mkdir -p templates
mkdir -p command-hub
```

**Step 3: Create README.md**

Content: What this repo is, who it's for, how to use it (point to bootstrap.md).

**Step 4: Commit and push**

```bash
git add -A && git commit -m "init: dev setup repo structure" && git push
```

---

### Task 7: Copy cleaned memory files to shared-memory/

**Depends on:** Tasks 1-4 (cleanup complete)

**Step 1: Copy files**

```bash
cp ~/.claude/projects/-home-patty/memory/indiestack-project.md ~/indiestack-dev-setup/shared-memory/
cp ~/.claude/projects/-home-patty/memory/dev-patterns.md ~/indiestack-dev-setup/shared-memory/
cp ~/.claude/projects/-home-patty/memory/api-keys.md ~/indiestack-dev-setup/shared-memory/
cp ~/.claude/projects/-home-patty/memory/feedback-auth-pattern.md ~/indiestack-dev-setup/shared-memory/
cp ~/.claude/projects/-home-patty/memory/pro-subscription-architecture.md ~/indiestack-dev-setup/shared-memory/
cp ~/.claude/projects/-home-patty/memory/github-token-setup.md ~/indiestack-dev-setup/shared-memory/
cp ~/.claude/projects/-home-patty/memory/workflow-ideas.md ~/indiestack-dev-setup/shared-memory/
```

**Step 2: Replace Patrick's local files with symlinks**

```bash
cd ~/.claude/projects/-home-patty/memory
for f in indiestack-project.md dev-patterns.md api-keys.md feedback-auth-pattern.md pro-subscription-architecture.md github-token-setup.md workflow-ideas.md; do
  rm "$f"
  ln -s ~/indiestack-dev-setup/shared-memory/"$f" "$f"
done
```

**Step 3: Verify symlinks work**

```bash
ls -la ~/.claude/projects/-home-patty/memory/*.md | grep "^l"
# Should show 7 symlinks pointing to ~/indiestack-dev-setup/shared-memory/
```

Read one file to confirm content is accessible.

**Step 4: Commit dev-setup repo**

```bash
cd ~/indiestack-dev-setup && git add shared-memory/ && git commit -m "add cleaned shared memory files"
```

---

### Task 8: Create shared skills (adapt paths)

**Files:**
- Create: `~/indiestack-dev-setup/shared-skills/{status,backup,brainstorm,publish-mcp,deep-research}/SKILL.md`
- Create: `~/indiestack-dev-setup/shared-skills/humanizer/SKILL.md`

**Step 1: Copy and adapt each skill**

For each skill, read the original from `~/.claude/skills/X/SKILL.md`, then write to `~/indiestack-dev-setup/shared-skills/X/SKILL.md` with these changes:
- Replace all `/home/patty/` with `~/` (tilde is portable)
- Replace all `/home/patty/indiestack` with `~/indiestack`
- Replace "Patrick" with "the user" where it refers to approval/interaction (keep "Patrick" where it refers to him as a person, e.g., co-founder names)
- For humanizer: copy only SKILL.md, not the .git directory

**Step 2: Copy email-ed skill to shared repo**

Read `~/.claude/skills/email-ed/SKILL.md`, write to `~/indiestack-dev-setup/shared-skills/email-ed/SKILL.md` with path changes.

**Step 3: Replace Patrick's local skill directories with symlinks**

For skills that moved to shared repo:
```bash
cd ~/.claude/skills
for skill in status backup brainstorm publish-mcp deep-research humanizer email-ed; do
  rm -rf "$skill"
  ln -s ~/indiestack-dev-setup/shared-skills/"$skill" "$skill"
done
```

**Step 4: Verify symlinks**

```bash
ls -la ~/.claude/skills/ | grep "^l"
```

**Step 5: Commit dev-setup repo**

```bash
cd ~/indiestack-dev-setup && git add shared-skills/ && git commit -m "add shared skills with portable paths"
```

---

### Task 9: Create email-pat skill

**Files:**
- Create: `~/indiestack-dev-setup/shared-skills/email-pat/SKILL.md`

**Step 1: Write the skill**

Mirror of email-ed with these differences:
- Sends to Patrick's email (pajebay1@gmail.com)
- Description: "Send a quick update email to Patrick (co-founder)"
- Triggers: "email pat" or "update pat" or "tell pat"
- Signs off as "Ed" not "Pat"
- Same Fly SSH SMTP pattern
- Same approval-before-send flow

**Step 2: Commit**

```bash
cd ~/indiestack-dev-setup && git add shared-skills/email-pat/ && git commit -m "feat: add email-pat skill — Ed emails Patrick"
```

---

### Task 10: Create Ed's CLAUDE.md template

**Files:**
- Create: `~/indiestack-dev-setup/templates/personal-claude.md`

**Step 1: Write the template (~35 lines)**

Use the approved design from the brainstorming session. Include:
- Who Ed is (3 lines)
- Commands table (status, email-pat, brainstorm, what's next, deploy, explain, backup)
- Working style (push back on ideas, brand guardian, quality over speed — condensed)
- Response style (educational, casual, explain errors)
- Key paths (with ~ for portability)

Use `{{NAME}}`, `{{EMAIL}}`, `{{GITHUB}}` placeholders where the bootstrap will substitute.

**Step 2: Commit**

```bash
cd ~/indiestack-dev-setup && git add templates/ && git commit -m "add Ed's CLAUDE.md template"
```

---

### Task 11: Create MEMORY.md template

**Files:**
- Create: `~/indiestack-dev-setup/templates/memory-index.md`

**Step 1: Write template**

Simplified version of Patrick's MEMORY.md — project index pointing to shared memory files. Include:
- System section (python3 not python)
- Projects section (link to shared indiestack-project.md)
- Dev Workflow section (links to shared dev-patterns.md, api-keys.md, etc.)
- Personal section (link to own profile file, created by bootstrap)

**Step 2: Commit**

```bash
cd ~/indiestack-dev-setup && git add templates/ && git commit -m "add MEMORY.md template"
```

---

### Task 12: Write bootstrap.md

**Files:**
- Create: `~/indiestack-dev-setup/bootstrap.md`

**Step 1: Write Part 1 — manual prerequisites**

Human-readable checklist Ed follows before involving Claude:
1. Clone both repos (indiestack + indiestack-dev-setup)
2. Install flyctl
3. Accept Fly.io org invite
4. Create Telegram bot (BotFather steps)
5. Get chat ID (getUpdates URL)
6. Start Claude Code with token + chat ID

**Step 2: Write Part 2 — Claude automation**

Step-by-step instructions for Claude to execute:
1. Detect OS/username/home (`uname`, `whoami`, `echo $HOME`)
2. Create ~/CLAUDE.md from template (substitute placeholders)
3. Create ~/.claude/skills/ symlinks to shared-skills/
4. Create ~/.claude/projects/ memory directory with symlinks + personal files
5. Write ~/.claude/telegram.sh with provided token/chat ID
6. Guide GitHub token creation
7. Set up IndieStack MCP server in Claude config: `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`
8. Verify everything works (status, telegram test, git access)
9. Run orientation: `explain ~/indiestack/src/indiestack/routes/components.py`

**Step 3: Commit**

```bash
cd ~/indiestack-dev-setup && git add bootstrap.md && git commit -m "add bootstrap.md — self-installing dev setup guide"
```

---

## Phase 3: Command Hub

### Task 13: Build command hub server

**Files:**
- Create: `~/indiestack-dev-setup/command-hub/server.py`

**Step 1: Write the FastAPI app (~300 lines)**

Endpoints:

```python
# --- Messages ---
# POST /messages  {from_dev, to_dev, text}  -> 201 + Telegram ping
# GET  /messages?for=ed&unread=true          -> list of messages
# POST /messages/{id}/read                   -> mark read

# --- Tasks ---
# GET    /tasks?assignee=ed&status=open      -> list of tasks
# POST   /tasks  {title, description, assignee}  -> 201
# PATCH  /tasks/{id}  {status, assignee}     -> 200

# --- Dashboard ---
# GET /dashboard                              -> HTML status page

# --- Cron info ---
# GET /cron                                   -> list scheduled jobs + last run times

# --- Health ---
# GET /health                                 -> 200 OK
```

Auth: `X-Hub-Secret` header checked against `HUB_SECRET` env var. Dashboard is the only public endpoint (or also behind auth — Patrick to decide during implementation).

SQLite schema:
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    from_dev TEXT NOT NULL,
    to_dev TEXT NOT NULL,
    text TEXT NOT NULL,
    read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    assignee TEXT,
    status TEXT DEFAULT 'open' CHECK(status IN ('open','in_progress','done')),
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cron_log (
    id INTEGER PRIMARY KEY,
    job_name TEXT NOT NULL,
    last_run TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result TEXT
);
```

Background cron tasks (asyncio):
- `_daily_status_ping()` — 9am UTC, hits IndieStack /health, sends summary to both Telegrams
- `_check_unread_messages()` — every 4 hours, pings dev if they have unread messages
- `_backup_staleness_check()` — daily, alerts if no backup in 48 hours (checks via message or file timestamp)

Telegram helper:
```python
async def _ping_telegram(dev: str, text: str):
    """Send Telegram message to a dev. Reads BOT_TOKEN_PAT, CHAT_ID_PAT, BOT_TOKEN_ED, CHAT_ID_ED from env."""
```

**Step 2: Write basic smoke test**

```python
# command-hub/test_hub.py
import httpx, pytest

BASE = "http://localhost:8000"
SECRET = "test-secret"
HEADERS = {"X-Hub-Secret": SECRET}

def test_health():
    r = httpx.get(f"{BASE}/health")
    assert r.status_code == 200

def test_create_and_read_message():
    r = httpx.post(f"{BASE}/messages", json={"from_dev": "patrick", "to_dev": "ed", "text": "test"}, headers=HEADERS)
    assert r.status_code == 201
    r = httpx.get(f"{BASE}/messages?for=ed", headers=HEADERS)
    assert len(r.json()) >= 1

def test_create_and_list_tasks():
    r = httpx.post(f"{BASE}/tasks", json={"title": "Fix navbar", "assignee": "ed", "created_by": "patrick"}, headers=HEADERS)
    assert r.status_code == 201
    r = httpx.get(f"{BASE}/tasks?assignee=ed", headers=HEADERS)
    assert len(r.json()) >= 1

def test_auth_required():
    r = httpx.post(f"{BASE}/messages", json={"from_dev": "a", "to_dev": "b", "text": "c"})
    assert r.status_code == 401
```

**Step 3: Run smoke test locally**

```bash
cd ~/indiestack-dev-setup/command-hub
HUB_SECRET=test-secret python3 -m uvicorn server:app --port 8000 &
sleep 2
HUB_SECRET=test-secret python3 -m pytest test_hub.py -v
kill %1
```

**Step 4: Commit**

```bash
cd ~/indiestack-dev-setup && git add command-hub/server.py command-hub/test_hub.py && git commit -m "feat: command hub — messages, tasks, cron, dashboard"
```

---

### Task 14: Create deployment config

**Files:**
- Create: `~/indiestack-dev-setup/command-hub/fly.toml`
- Create: `~/indiestack-dev-setup/command-hub/Dockerfile`
- Create: `~/indiestack-dev-setup/command-hub/requirements.txt`

**Step 1: Write requirements.txt**

```
fastapi
uvicorn[standard]
aiosqlite
httpx
```

**Step 2: Write Dockerfile**

Standard Python Fly setup — copy code, pip install, run uvicorn.

**Step 3: Write fly.toml**

Reuse existing GovLink app name. Point to SQLite on volume. Set `min_machines_running = 1`.

**Step 4: Commit**

```bash
cd ~/indiestack-dev-setup && git add command-hub/ && git commit -m "add command hub deployment config"
```

---

### Task 15: Create hub skill

**Files:**
- Create: `~/indiestack-dev-setup/shared-skills/hub/SKILL.md`

**Step 1: Write the skill**

```markdown
---
name: hub
description: Query the IndieStack Command Hub — check messages, view tasks, post updates. Use when either dev says "hub", "check hub", "messages", or "tasks".
---

# Command Hub

Query the shared command hub for cross-dev coordination.

## Check messages
curl -s -H "X-Hub-Secret: $HUB_SECRET" "$HUB_URL/messages?for=$DEV_NAME&unread=true"

## View tasks
curl -s -H "X-Hub-Secret: $HUB_SECRET" "$HUB_URL/tasks?assignee=$DEV_NAME"

## Post message
curl -s -X POST -H "X-Hub-Secret: $HUB_SECRET" -H "Content-Type: application/json" \
  "$HUB_URL/messages" -d '{"from_dev":"$DEV_NAME","to_dev":"$OTHER_DEV","text":"MESSAGE"}'

## Create task
curl -s -X POST -H "X-Hub-Secret: $HUB_SECRET" -H "Content-Type: application/json" \
  "$HUB_URL/tasks" -d '{"title":"TITLE","assignee":"ASSIGNEE","created_by":"$DEV_NAME"}'

## Environment
- HUB_URL and HUB_SECRET must be set in ~/.bashrc
- DEV_NAME is "patrick" or "ed"
```

**Step 2: Commit**

```bash
cd ~/indiestack-dev-setup && git add shared-skills/hub/ && git commit -m "feat: add hub skill — query command hub"
```

---

### Task 16: Deploy command hub to Fly

**Step 1: Set Fly secrets**

```bash
cd ~/indiestack-dev-setup/command-hub
~/.fly/bin/flyctl secrets set \
  HUB_SECRET="<generate-secure-secret>" \
  BOT_TOKEN_PAT="8708141998:AAFpYobIr3BCvuEQTat_pnwTwbOu_qVIHz0" \
  CHAT_ID_PAT="8406588975" \
  BOT_TOKEN_ED="<ed-provides-after-botfather>" \
  CHAT_ID_ED="<ed-provides-after-botfather>" \
  -a govlink
```

**Step 2: Deploy**

```bash
cd ~/indiestack-dev-setup/command-hub && ~/.fly/bin/flyctl deploy --remote-only -a govlink
```

**Step 3: Verify**

```bash
curl -s https://govlink.fly.dev/health
```

**Step 4: Set HUB_URL and HUB_SECRET in Patrick's ~/.bashrc**

```bash
echo 'export HUB_URL="https://govlink.fly.dev"' >> ~/.bashrc
echo 'export HUB_SECRET="<the-secret>"' >> ~/.bashrc
source ~/.bashrc
```

**Step 5: Test hub skill**

Run `/hub` in Claude Code — should return empty messages/tasks.

---

## Phase 4: Finalize & Ship

### Task 17: Send Fly.io org invite to Ed

**Step 1: Invite Ed**

```bash
~/.fly/bin/flyctl orgs invite toedgamings@gmail.com --org personal
```

**Step 2: Verify invite sent**

```bash
~/.fly/bin/flyctl orgs list
```

---

### Task 18: Push dev-setup repo and verify

**Step 1: Final review of all files in repo**

```bash
cd ~/indiestack-dev-setup && find . -not -path './.git/*' -type f | sort
```

Verify structure matches design doc.

**Step 2: Push to GitHub**

```bash
cd ~/indiestack-dev-setup && git push -u origin main
```

**Step 3: Verify Ed has access**

```bash
gh repo view Pattyboi101/indiestack-dev-setup --json collaborators
```

If Ed isn't listed, add him:
```bash
gh api repos/Pattyboi101/indiestack-dev-setup/collaborators/rupert61622-blip -X PUT -f permission=push
```

---

### Task 19: Test bootstrap flow (dry run)

**Step 1: Read bootstrap.md end-to-end**

Verify all paths, commands, and instructions are correct and complete.

**Step 2: Simulate Part 2 on Patrick's machine**

Run the detection commands:
```bash
uname && whoami && echo $HOME
```

Verify the symlink commands would work (don't re-run — already done in Tasks 7-8).

**Step 3: Verify the full skill list works**

Run each skill command in Claude Code:
- `/status` — should work via symlink
- `/backup` — should work via symlink
- `/brainstorm` — should work via symlink
- `/hub` — should connect to command hub

---

### Task 20: Update memory files

**Step 1: Update ed-dev-setup.md status**

Change status from "IN PROGRESS" to "COMPLETE" with summary of what was built.

**Step 2: Update MEMORY.md**

Add entry for the dev-setup repo and command hub.

**Step 3: Update indiestack-project.md**

Add note about command hub and multi-dev workflow.

**Step 4: Commit all memory updates**

```bash
cd ~/indiestack-dev-setup && git add shared-memory/ && git commit -m "update memory files — dev setup complete"
```

---

## Execution Order & Dependencies

```
Phase 1 (all parallel):
  Task 1: Clean workflow-ideas.md
  Task 2: Clean indiestack-project.md
  Task 3: Merge indiestack-details.md
  Task 4: Clean pro-subscription-architecture.md
  Task 5: Update repo CLAUDE.md

Phase 2 (sequential, depends on Phase 1):
  Task 6:  Create GitHub repo
  Task 7:  Copy memory files + symlinks  (depends on 1-4)
  Task 8:  Create shared skills
  Task 9:  Create email-pat skill
  Task 10: Create Ed's CLAUDE.md template
  Task 11: Create MEMORY.md template
  Task 12: Write bootstrap.md

Phase 3 (parallel with Phase 2):
  Task 13: Build command hub server
  Task 14: Create deployment config
  Task 15: Create hub skill
  Task 16: Deploy to Fly

Phase 4 (depends on 2 + 3):
  Task 17: Fly.io org invite
  Task 18: Push repo + verify access
  Task 19: Test bootstrap flow
  Task 20: Update memory files
```

**Estimated tasks:** 20
**Parallelizable groups:** Phase 1 (5 tasks), Phase 2 + Phase 3 (partially parallel)
