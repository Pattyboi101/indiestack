---
name: meeting
description: Facilitate a structured CONVERSATIONAL meeting between Patrick and all orchestra agents — up to 7 rounds of debate with cross-examination, idea building, and devil's advocate. Agents push back on each other, not just answer questions. Early exit when consensus is reached. Produces persistent notes and writes action items to briefing files.
argument-hint: "[topic] OR 'close' to end the current meeting"
---

# Meeting Skill

Run a real meeting — not a survey. Agents stake positions in Round 1, push back on each other in Round 2, build on the best ideas in Round 3, attack the consensus in Round 4, refine in Round 5, converge in Round 6, synthesize in Round 7. Stop as soon as the group is satisfied — don't grind through rounds for the sake of it.

---

## Detecting Intent

- `$ARGUMENTS` is `close` → run **Close Meeting**
- `$ARGUMENTS` is empty → ask Patrick for the topic
- Otherwise → run **Start Meeting**

---

## Round Types

| Round | Name | Purpose | Who |
|-------|------|---------|-----|
| **R1** | Opening positions | Stake honest takes — no hedging | All |
| **R2** | Cross-examination | Respond to specific tensions between positions | Targeted |
| **R3** | Idea building | Develop the strongest ideas from R1–R2 | All or targeted |
| **R4** | Devil's advocate | Attack the emerging consensus — find the holes | All |
| **R5** | Refinement | Respond to R4 attacks, strengthen or concede | Targeted |
| **R6** | Convergence | Find genuine agreement; surface remaining gaps | All |
| **R7** | Synthesis | CEO resolves anything still unresolved | CEO only |

**Minimum: R1–R4.** R3 and R4 are mandatory, not optional. Ideas proposed in R1 must be developed (R3) and attacked (R4) before the meeting can close. **Standard:** R1–R4. **Deep strategy:** R1–R6 or R1–R7.

**Why 4 minimum:** 2 rounds means ideas get challenged once but never refined or stress-tested — they go into actions without anyone pushing back on them. R3 develops the strongest ideas from the debate; R4 attacks the emerging consensus before it hardens into decisions. Without both, the meeting is just a structured brainstorm.

**Early exit is ignored before R4 completes.** `[SATISFIED]` and `[CLOSE MEETING]` flags are collected but not acted on until R4 is done. After R4, if CEO flags `[CLOSE MEETING]` or all agents flag `[SATISFIED]`, close immediately.

---

## Research Integration

Research can happen at three points — use whichever the topic needs:

| When | What | How |
|------|------|-----|
| **R0 — Pre-meeting brief** | Chair researches the topic before R1; key findings go in every agent's R1 prompt | Use WebSearch/WebFetch, summarise in 3-5 bullets, include inline |
| **In-round** | Agents research before writing their position | Tell agents in the round prompt: "Search before writing if you need current data" |
| **Between-round sprint** | Chair runs targeted searches surfaced by agent flags | Agents write `[NEEDS RESEARCH: X]` in their response; chair searches X and includes findings in the next round prompt |

**When to use R0:** Any time the topic involves recent events, competitor moves, new model releases, market data, or anything agents might have stale knowledge on. Always do R0 for external partnership/outreach meetings.

**[NEEDS RESEARCH: X] protocol:** When an agent writes this flag, collect all flags after the round, run the searches, and prepend findings to the next round's message: "Research from last round: [findings]. Now respond to..."

---

## Start Meeting

### Step 1 — Create the Meeting File

Filename: `.orchestra/meetings/YYYY-MM-DD-[topic-slug].md`

```markdown
# Meeting: [Topic]
**Date:** YYYY-MM-DD HH:MM
**Status:** Round 1
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Agenda

[Topic + the specific decision or question to resolve]

---

## Round 1 — Opening Positions

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

## Round 2 — Cross-Examination

_Populated by chair after Round 1_

---

## [Further rounds added as needed]

---

## Patrick's Notes

_(add observations, decisions, calls to make here)_

---

## Action Items

_(populated at close)_
```

### Step 1b — R0: Pre-Meeting Research (optional but recommended for external topics)

Before sending R1, do 3-5 web searches on the topic. Include a research brief in every R1 message:

```
**Research brief (pre-meeting):**
- [Finding 1]
- [Finding 2]
- [Finding 3]
Use this as shared context. You may also search for more before writing your position.
```

Use R0 for: new model releases, competitor moves, partnership targets, market data, anything agents might have stale knowledge on.

---

### Step 2 — Send Round 1

Call `list_peers` first. Send to ALL available agents simultaneously.

**To CEO:**
```
[MEETING R1] Topic: [topic]

Opening position only. Answer:
1. Strategic read: pursue / challenge / pass, and why
2. The one thing you'd fight for in this discussion
3. The assumption most likely to be wrong
4. The risk nobody's talking about

Write directly into the meeting file under "### CEO" (replacing _Awaiting response_). Stake a real position — other agents will push back in R2. After writing, check_messages immediately.

If you're satisfied with the discussion at any point, add [SATISFIED] to your response.
```

**To each department:**
```
[MEETING R1] Topic: [topic]

Opening position only. Answer:
1. Your honest take — what's right and wrong about this
2. One thing you'd push back on if anyone proposed it
3. What you'd volunteer to own
4. What another department is underestimating

Write directly into the meeting file under "### [Dept]" (replacing _Awaiting response_). Stake a real position — other agents respond to yours in R2. After writing, check_messages immediately.

If you're satisfied with the discussion at any point, add [SATISFIED] to your response.
```

Tell Patrick: "Round 1 sent. Give agents 2-3 minutes. I'll read for tensions when you're ready."

---

### Step 2b — Between-Round Research Sprint (optional)

After collecting any round, scan for `[NEEDS RESEARCH: X]` flags. If any exist:
1. Run the searches (WebSearch/WebFetch)
2. Prepend findings to the next round's message: "**Research from last round:** [findings]. Now..."
3. Clear the flags — don't carry them forward

This keeps research demand-driven — it happens when the debate surfaces a gap, not on a fixed schedule.

---

### Step 3 — Round 2: Cross-Examination

Read all R1 responses. Find 3-5 **genuine tensions** — where agents contradict each other, make incompatible assumptions, or dismiss something another flagged as critical. Don't manufacture conflict; don't smooth over real disagreement.

Add section to meeting file:
```markdown
## Round 2 — Cross-Examination

**Tensions identified:**

**T1: [Label]** — [Dept A] says [X], [Dept B] says [Y]. Incompatible.
**T2: [Label]** — CEO assumes [A] but [Dept C] read is [B].
**T3: [Label]** — [Dept D] flagged [Z] but nobody else addressed it.

### [Dept A] + [Dept B] respond to T1
_Awaiting response_

### CEO + [Dept C] respond to T2
_Awaiting response_
```

Send **targeted** messages — only agents whose positions are in tension:
```
[MEETING R2] Topic: [topic]

You need to respond to these tensions:

**T1: [Label]**
[Dept B] said: "[quote]"
Your position was: "[quote]"
These are incompatible. Who's right and why? Be direct.

Write under "### [your dept] responds to T1" in the meeting file. One paragraph per tension. After writing, check_messages immediately.

Add [SATISFIED] if you're happy with where the discussion is heading.
```

Report tensions to Patrick before sending.

---

### Step 4 — Round 3: Idea Building (optional)

Use when R1–R2 surfaced promising ideas that need development, not just debate.

```
[MEETING R3] Topic: [topic]

R2 is done. Here are the strongest ideas that emerged:
- [Idea A from Dept X]
- [Idea B from Dept Y]

Your job this round: develop one of these further, or propose how to combine them. Don't critique — build.

Write under "## Round 3 — Idea Building / ### [your dept]" in the meeting file. After writing, check_messages immediately.

Add [SATISFIED] if you're happy with the direction.
```

---

### Step 5 — Round 4: Devil's Advocate (optional)

Use when a consensus is forming and you want to stress-test it before committing.

```
[MEETING R4] Topic: [topic]

A consensus is forming around: [description]

Your job this round: attack it. Find the holes, the bad assumptions, the things that will go wrong. Don't defend it — find what breaks it.

Write under "## Round 4 — Devil's Advocate / ### [your dept]" in the meeting file. After writing, check_messages immediately.

Add [SATISFIED] if you think the consensus is actually solid and you're happy to proceed.
```

---

### Step 6 — Rounds 5 & 6: Refinement + Convergence (optional)

**R5 — Refinement:** Send to agents whose ideas were attacked in R4. "Here's what R4 said about your proposal. Respond — defend, concede, or revise."

**R6 — Convergence:** Broadcast to all. "Here's where we are. What do you actually agree on? What's still genuinely unresolved? Flag [SATISFIED] if you're done."

Add new sections to meeting file for each round.

---

### Step 7 — Round 7: Synthesis (optional)

Only if R6 still has genuine unresolved conflict. Send to CEO only:

```
[MEETING R7 — SYNTHESIS] Topic: [topic]

Unresolved after R6:
- [T1: still open]
- [T2: still open]

Read the full meeting file. Give a verdict:
1. On T1: the right call is [X] because [Y]
2. On T2: the right call is [X] because [Y]
3. What Patrick needs to decide (if anything)

Write under "## Round 7 — Synthesis". This is a verdict, not a summary. After writing, check_messages immediately.
```

---

## Auto-Progression

Rounds run automatically — do NOT stop to ask Patrick between rounds. The mandatory flow is:

1. R1 completes → identify tensions → **R2 fires automatically**
2. R2 completes → take strongest ideas from R1+R2 → **R3 fires automatically**
3. R3 completes → identify forming consensus → **R4 fires automatically**
4. R4 completes → genuine unresolved conflict? → R5+ if yes, close if no

**R1–R4 are mandatory. R3 and R4 cannot be skipped.** Ideas must be developed (R3) and attacked (R4) before any exit condition is honoured. A meeting that closes at R2 has only challenged ideas once — they've never been stress-tested.

**The CEO is the meeting closer — but only from R4 onwards.** After R4 completes, the CEO can write `[CLOSE MEETING: reason]` to signal diminishing returns. Close immediately when seen. `[SATISFIED]` and `[CLOSE MEETING]` flags received before R4 completes are noted but ignored.

**Exit conditions (only honoured after R4):**
- CEO writes `[CLOSE MEETING: reason]` → close immediately
- All agents flag `[SATISFIED]` → close
- Patrick says "close" → close
- 7 rounds completed → close regardless

**Only surface to Patrick when the meeting closes.**

---

## Close Meeting

### Step 1 — Extract Actions

Concrete tasks only — no maybes, no "we should consider":
```
- [ ] [Task] | Owner: [Dept] | Priority: high/med/low | By: [date or "next session"]
```

### Step 2 — Write to Briefing Files

Append per department — don't overwrite:
```markdown
## Meeting: [topic] — [date]
- [ ] [task]
```

### Step 3 — Update Meeting File

- Status → `Closed`
- Fill `## Action Items`

### Step 4 — Broadcast Close

```
[MEETING CLOSE] [topic] | Decided: [2-3 sentences] | Your tasks are in briefing.md | Notes: .orchestra/meetings/[file]
```

### Step 5 — Report to Patrick

```
Meeting closed. [N] rounds.

Decided: [key decisions]
Unresolved (your call): [anything left open]

Actions: CEO [n] | Frontend [n] | Backend [n] | DevOps [n] | Content [n] | MCP [n]
Written to each dept's briefing.md.
```

---

## Tips

- **R2 is the whole point** — R1 without R2 is a survey.
- **R3–R6 are where ideas develop** — use them for complex topics, skip for simple ones.
- **[SATISFIED] saves tokens** — encourage agents to flag when they're done pushing.
- **Route sparingly in R2** — only agents in genuine conflict. Don't spam everyone.
- **CEO always gets R7** if there's real unresolved conflict. Skip if there isn't.
- **Not all agents need to be online** — proceed with who's there.
- **Meeting files are permanent** — stored in `.orchestra/meetings/` as institutional memory.

---

## Meeting Type → Suggested Rounds

| Type | Rounds | Notes |
|------|--------|-------|
| Sprint planning | R1–R4 | R4 attacks the prioritisation before it's locked |
| Feature design | R1–R4 | R3 builds the design, R4 finds what breaks it |
| Strategy | R1–R4 to R1–R6 | R4 devil's advocate is critical for big bets |
| Post-mortem | R1–R4 | R3 develops fixes, R4 attacks them — root cause may differ |
| Build prioritization | R1–R4 | R3 develops the sequence, R4 challenges the assumptions |
| Partnership / outreach | R1–R4 | R4 attacks the pitch before it goes out |
