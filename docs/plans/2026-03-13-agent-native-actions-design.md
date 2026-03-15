# Agent-Native Actions — Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:writing-plans to create the implementation plan from this design.

**Goal:** Give AI agents their own action vocabulary on IndieStack — recommend, shortlist, report outcomes, confirm integrations, submit tools — producing agent-native data that's more valuable than simulated human actions.

**Architecture:** Extend existing API key system with scopes (read/write). New `agent_actions` table logs all agent behaviour. Five new MCP tools. Dashboard section shows agent activity. Existing MCP tools gain personalisation when authenticated.

**Date:** 2026-03-13

---

## Core Principle

Agents don't review tools — they report outcomes. Agents don't upvote — they report recommendations. The data model captures what agents actually do, not what humans do.

| Human action | Agent equivalent | Signal produced |
|-------------|-----------------|-----------------|
| Upvote | `recommend` | "AI recommended this tool" — distribution signal |
| Review | `report_outcome` | "User successfully used this" — quality signal |
| Report compat | `confirm_integration` | "Agent connected A + B in a project" — verified compat |
| Bookmark | `shortlist` | "Agent considered this" — demand signal |
| Submit tool | `submit_tool` | "User built this, list it" — goes to review queue |

---

## Database Changes

### New table: `agent_actions`

```sql
CREATE TABLE IF NOT EXISTS agent_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- recommend | shortlist | report_outcome | confirm_integration | submit_tool
    tool_slug TEXT NOT NULL,
    tool_b_slug TEXT,  -- for integration pairs
    success INTEGER,  -- for report_outcome: 1 = success, 0 = failure
    notes TEXT,
    query_context TEXT,  -- what the agent was searching for when it took this action
    created_at TIMESTAMP DEFAULT (datetime('now'))
);

CREATE INDEX idx_agent_actions_key ON agent_actions(api_key_id);
CREATE INDEX idx_agent_actions_user ON agent_actions(user_id);
CREATE INDEX idx_agent_actions_tool ON agent_actions(tool_slug);
CREATE INDEX idx_agent_actions_action ON agent_actions(action);
CREATE INDEX idx_agent_actions_date ON agent_actions(created_at);
```

### Extend `api_keys` table

```sql
ALTER TABLE api_keys ADD COLUMN scopes TEXT DEFAULT 'read';
```

Values: `"read"` (default) or `"read,write"`.

---

## New MCP Tools

### 1. `recommend(tool_slug, query_context?)`

- **Scope:** read
- **Rate limit:** 50/day per key
- **What it does:** Records that the agent recommended this tool to its user
- **Dedup:** One recommendation per tool per user per day
- **Returns:** Confirmation + tool's total recommendation count

### 2. `shortlist(tool_slugs[], query_context?)`

- **Scope:** read
- **Rate limit:** 100/day per key
- **What it does:** Records that the agent considered these tools for a query (even if it didn't recommend them)
- **Max slugs per call:** 10
- **Returns:** Confirmation

### 3. `report_outcome(tool_slug, success, notes?)`

- **Scope:** write
- **Rate limit:** 20/day per key
- **What it does:** Records whether the user successfully used the recommended tool
- **Validation:** Tool must have been previously recommended by this agent
- **Returns:** Confirmation + tool's success rate
- **Side effect:** Updates tool's agent success rate metric

### 4. `confirm_integration(tool_a_slug, tool_b_slug, notes?)`

- **Scope:** write
- **Rate limit:** 10/day per key
- **What it does:** Records that the agent successfully connected two tools in a project
- **Validation:** Both tools must exist, can't self-pair
- **Returns:** Confirmation
- **Side effect:** Feeds into `tool_pairs` table with `source: "agent"` (lower weight than `source: "verified"`)

### 5. `submit_tool(name, url, description, category)`

- **Scope:** write
- **Rate limit:** 3/day per key
- **What it does:** Submits a tool for human review, same as the web form
- **Validation:** Same as web submission (name, url, description required)
- **Returns:** Confirmation that submission is pending review
- **Side effect:** Enters existing review queue, tagged as `source: "agent"`

---

## Existing MCP Tool Enhancements

When an API key is present, existing tools gain personalisation:

- **`get_recommendations`** — Uses agent's action history. Factors in previously recommended tools, successful outcomes, and category affinity.
- **`find_tools`** — Results subtly ranked by user's demonstrated preferences (category affinity from past actions, source_type preference). Anonymous results unchanged.
- **`build_stack`** — Suggests tool combinations with high `confirm_integration` counts across all agents.

Personalisation is additive — it improves results, never removes them. Anonymous experience stays identical.

---

## API Endpoints

All agent action endpoints use the existing API key authentication:

```
POST /api/agent/recommend    — { tool_slug, query_context? }
POST /api/agent/shortlist    — { tool_slugs: [...], query_context? }
POST /api/agent/outcome      — { tool_slug, success, notes? }
POST /api/agent/integration  — { tool_a_slug, tool_b_slug, notes? }
POST /api/agent/submit       — { name, url, description, category }
```

All require `key=ISK_xxx` parameter or `Authorization: Bearer ISK_xxx` header.

Write-scope endpoints (`outcome`, `integration`, `submit`) return 403 if the key only has `read` scope.

---

## Scope Management

- New API keys default to `read` scope
- Users enable write scope from `/developer` or `/dashboard` with a toggle
- Scope change is instant, no re-generation needed
- Dashboard shows current scope with explanation of what each enables

---

## Dashboard: Agent Activity Section

New section on the user dashboard (below API keys):

```
Agent Activity (last 30 days)
─────────────────────────────
Recommendations:  47 tools recommended
Shortlisted:      128 tools considered
Outcomes:         12 reported (10 successful, 2 failed)
Integrations:     3 tool pairs confirmed
Submissions:      1 tool submitted

[View full activity log]
```

Activity log: sortable table with timestamp, action type, tool(s), context, notes.

---

## Notifications

- **Immediate** for submissions: "Your agent submitted 'CoolTool' to IndieStack"
- **Daily digest** (optional, off by default) for other write actions
- Read actions (recommend, shortlist) — no notifications, dashboard only

---

## Rate Limiting

Agent actions have their own rate limits, separate from search/API rate limits:

| Action | Limit per key per day |
|--------|----------------------|
| recommend | 50 |
| shortlist | 100 |
| report_outcome | 20 |
| confirm_integration | 10 |
| submit_tool | 3 |

Additional dedup rules:
- One `recommend` per tool per user per day
- One `report_outcome` per tool per user (ever — you can update it but not spam it)
- One `confirm_integration` per tool pair per user (ever)

---

## Abuse Prevention

1. `submit_tool` goes through existing human review queue — no auto-approval
2. `confirm_integration` creates `tool_pairs` entries with `source: "agent"` — weighted lower than `source: "verified"` or `source: "user"`
3. All actions tagged with `api_key_id` — one compromised key can be revoked without affecting other users
4. `report_outcome` requires the tool to have been previously recommended by this agent — can't report outcomes for tools you didn't recommend
5. Users can see all agent actions on dashboard — transparency prevents surprise

---

## Value Created

**For makers (Pro feature):**
- "Your tool was recommended by AI agents 340 times this month"
- "85% success rate from agent-assisted integrations"
- Agent recommendation count as a new social proof metric on tool pages

**For users:**
- Agent gets smarter over time — personalised recommendations based on past outcomes
- "Your agent saved ~40,000 tokens this week by recommending existing tools"

**For IndieStack:**
- Recommendation → outcome conversion data (the moat)
- Real demand signals from agent behaviour, not anonymous searches
- Reason for makers to subscribe to Pro (see agent recommendation data)

---

## What We're NOT Building (YAGNI)

- `register_agent` MCP tool — users create accounts on the website
- Moltbook integration — future optional layer, not in v1
- Public agent profiles — agent data visible only to owner
- Agent-to-agent interaction — future vision
- Agent reviews/ratings — agents report outcomes, not opinions

---

## Success Metrics

- Number of API keys with write scope enabled (target: 5 within first month)
- Agent actions per day (target: 50+ within first month)
- Recommendation → outcome conversion rate (any data = success)
- New Pro subscriptions driven by "agent recommendation" data (even 1 = validated)
