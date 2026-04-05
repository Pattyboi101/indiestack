---
name: meeting
description: Facilitate a structured meeting between Patrick and all orchestra agents — agenda, discussion, notes, action items written to briefing files
argument-hint: "[topic] OR 'close' to end the current meeting"
---

# Meeting Skill

Orchestrate a structured meeting between Patrick and the IndieStack orchestra (CEO + 5 departments) via claude-peers. Produces persistent notes and writes action items directly to department briefing files.

## Detecting Intent

- `$ARGUMENTS` is `close` → run **Close Meeting**
- `$ARGUMENTS` is empty → ask Patrick for the topic
- Otherwise → run **Start Meeting**

---

## Start Meeting

### Step 1 — Create the Notes File

Pick a filename from the topic: lowercase, hyphens, max 4 words.
Create `.orchestra/meetings/YYYY-MM-DD-[slug].md`:

```markdown
# Meeting: [Topic]
**Date:** YYYY-MM-DD HH:MM
**Status:** In Progress
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Agenda
[Topic description from $ARGUMENTS]

---

## Discussion

### CEO
_Awaiting response_

### Frontend
_Awaiting response_

### Backend
_Awaiting response_

### DevOps
_Awaiting response_

### Content
_Awaiting response_

### MCP
_Awaiting response_

---

## Patrick's Notes
_(add observations, decisions, follow-up questions here)_

---

## Action Items
_(populated at close)_
```

### Step 2 — Send Invites via claude-peers

First call `list_peers` to see who's online.

**To CEO** (strategic framing, not tasks):
```
[MEETING] Topic: [topic] | Agenda: [description] | As CEO, please share: strategic priority of this, risks, what success looks like, and your verdict (pursue/challenge/pass). Reply when ready.
```

**To each department** (Frontend, Backend, DevOps, Content, MCP):
```
[MEETING] Topic: [topic] | Agenda: [description] | Please share: (1) your dept's perspective and concerns, (2) opportunities you see in your area, (3) specific tasks you're willing to own. Use [MEETING RESPONSE] format from your CLAUDE.md. Reply when ready.
```

Tell Patrick: "Invites sent. Agents are thinking — check back in a few minutes. I'll check for replies when you're ready, or you can watch the tmux windows directly."

### Step 3 — Collect Responses

When Patrick says responses are in (or after a few minutes), call `check_messages` to pull replies.

For each reply received:
- Paste it into the notes file under the correct department heading
- Replace `_Awaiting response_` with their actual response
- Note any follow-up questions needed

If an agent is offline, leave `_Unavailable this session_` under their heading.

### Step 4 — Facilitate

Once initial responses are in, read for:
- **Conflicts** — departments disagreeing → flag under Patrick's Notes, ask follow-up
- **Gaps** — nobody addressed something important → prompt a specific agent
- **Decisions needed** — Patrick needs to make a call → surface it clearly

You can message specific agents for follow-ups:
```
[MEETING FOLLOW-UP] Question from Patrick: [question]
```

---

## Close Meeting

### Step 1 — Extract Action Items

Read all responses. Extract concrete tasks. Format each as:
```
- [ ] [Task description] | Owner: [dept] | Priority: [high/med/low] | By: [next session / YYYY-MM-DD]
```

Group by department. Keep unowned discussion points as "Patrick to decide."

### Step 2 — Write to Briefing Files

For each department that has tasks, append to `.orchestra/departments/[dept]/briefing.md`:
```markdown
## Meeting: [topic] — [date]
[tasks for this dept]
```

Don't overwrite existing tasks. Append.

### Step 3 — Update Notes File

- Change `**Status:** In Progress` → `**Status:** Complete`
- Fill in the `## Action Items` section with the final grouped list

### Step 4 — Send Close Summary

Via claude-peers to all agents:
```
[MEETING CLOSE] Topic: [topic] | Summary: [2-3 sentences] | Your tasks have been written to your briefing.md — check and acknowledge. Full notes: .orchestra/meetings/[filename]
```

### Step 5 — Report to Patrick

```
Meeting closed. Notes: .orchestra/meetings/[filename]

Action items assigned:
  Frontend : [n tasks]
  Backend  : [n tasks]
  DevOps   : [n tasks]
  Content  : [n tasks]
  MCP      : [n tasks]

Written to each dept's briefing.md.
```

---

## Meeting Types

| Type | Good for | Tip |
|------|----------|-----|
| **Sprint planning** | Start of a work session | "What should we build next?" |
| **Feature design** | Before building something new | "Design: [feature] — how should it work?" |
| **Strategy** | Big picture direction | "Strategy: [area] — where should we focus?" |
| **Post-mortem** | After something broke | "Post-mortem: [incident] — cause + prevention" |
| **Bug triage** | Multiple issues to prioritize | "Triage: [list] — what to fix first?" |
| **Brainstorm** | Open-ended ideas | "Ideas for [area]: what could we do?" |

---

## Tips

- **Not all agents may be online** — that's fine, proceed without them.
- **CEO is strategic gate** — always wait for CEO input before closing strategy meetings.
- **Follow-ups are normal** — don't rush to close if the discussion is still useful.
- **Meeting files are permanent** — stored in `.orchestra/meetings/` as a record.
- **Keep it focused** — if a new topic comes up mid-meeting, note it and schedule a separate meeting.
