---
name: meeting
description: Facilitate a structured CONVERSATIONAL meeting between Patrick and all orchestra agents — named phases (Diverge → Challenge → Build → Stress Test) with state machine navigation. Agents push back on each other, build on each other's ideas, and the chair navigates phases autonomously. Early exit only after Stress Test completes.
argument-hint: "[topic] OR 'close' to end the current meeting"
---

# Meeting Skill

Run a real meeting — a state machine, not a survey. Agents diverge ideas, challenge each other, build on what survives, and stress test before anything becomes an action. The chair navigates phases, can skip optional ones, repeat phases still generating value, or loop back when a later phase reveals something that needs earlier work.

---

## Detecting Intent

- `$ARGUMENTS` is `close` → run **Close Meeting**
- `$ARGUMENTS` is empty → ask Patrick for the topic
- Otherwise → run **Start Meeting**

---

## Phase System

| Phase | Purpose | Mandatory? |
|-------|---------|-----------|
| **Diverge** | All ideas on the table — no criticism yet | **Yes** |
| **Clarify** | Surface assumptions, define terms, resolve ambiguity | Optional |
| **Challenge** | Push back, expose tensions, stress-test assumptions | **Yes** |
| **Build** | Develop the strongest ideas that survived Challenge | **Yes** |
| **Stress Test** | Attack the emerging consensus — try to break it | **Yes** |
| **Converge** | Find genuine agreement, surface remaining gaps | Optional |
| **Decide** | CEO resolves anything still genuinely unresolved | Only if unresolved |

**Minimum required path:** Diverge → Challenge → Build → Stress Test

**`[SATISFIED]` and `[CLOSE MEETING]` flags are ignored until Stress Test completes.** Collect them, note them, do not act on them.

---

## Agent Flags

Agents write these in their responses to signal navigation needs:

| Flag | Meaning | Chair Action |
|------|---------|-------------|
| `[NEEDS CLARIFY: X]` | X needs defining before I can contribute fully | Insert Clarify phase |
| `[BACK TO CHALLENGE: reason]` | Build surfaced a new tension that needs challenging | Loop to Challenge with the new tension |
| `[BACK TO BUILD: reason]` | Stress Test revealed a better approach worth developing | Loop to Build with refined idea |
| `[SATISFIED]` | Nothing more to add — happy with direction | Count; close if all satisfied (after Stress Test) |
| `[CLOSE MEETING: reason]` | CEO: meeting has run its course | Close immediately (only after Stress Test) |

---

## State Machine

```
Diverge (mandatory)
  → [Clarify]? — insert if [NEEDS CLARIFY] flags or agents talking past each other
  → Challenge (mandatory)
       ↑ ← loop back if Build surfaces [BACK TO CHALLENGE]
  → Build (mandatory)
       ↑ ← loop back if Stress Test surfaces [BACK TO BUILD]
  → Stress Test (mandatory)
  → [Converge]? — insert if unresolved disagreements remain
  → [Decide]? — insert if Converge still has unresolved conflict
  → Close
```

**Navigation decisions are the chair's to make** — do NOT stop to ask Patrick between phases. Only surface to Patrick when the meeting closes.

---

## Research Integration

| When | What | How |
|------|------|-----|
| **R0 — Pre-meeting** | Chair researches topic before Diverge | WebSearch/WebFetch, 3-5 bullets, included in every agent's prompt |
| **In-phase** | Agents search before writing | Tell agents: "Search before writing if you need current data" |
| **Between-phase sprint** | Chair runs searches from `[NEEDS RESEARCH: X]` flags | Prepend findings to next phase prompt |

Use R0 for: new model releases, competitor moves, partnership targets, market data — anything agents might have stale knowledge on.

---

## Start Meeting

### Step 1 — Create the Meeting File

Filename: `.orchestra/meetings/YYYY-MM-DD-[topic-slug].md`

```markdown
# Meeting: [Topic]
**Date:** YYYY-MM-DD HH:MM
**Status:** Diverge
**Phases run:** []
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Agenda

[Topic + the specific question or decision to resolve]

---

## Phase: Diverge

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

## [Further phases added dynamically]

---

## Patrick's Notes

_(chair observations, navigation decisions, calls to make)_

---

## Action Items

_(populated at close)_
```

### Step 1b — R0: Pre-Meeting Research (recommended for external topics)

Do 3-5 searches before sending Diverge. Include a brief in every agent's prompt:

```
**Research brief:**
- [Finding 1]
- [Finding 2]
- [Finding 3]
Shared context — you may also search before writing.
```

---

### Step 2 — Phase: Diverge (mandatory)

Call `list_peers` first. Send to **ALL** available agents simultaneously.

**To CEO:**
```
[MEETING — DIVERGE] Topic: [topic]

Generate ideas — no criticism yet. Answer:
1. Strategic read: what's the real opportunity or problem here?
2. Two or three concrete moves we could make
3. The thing nobody's said yet that we should be considering
4. One assumption you want to challenge in the next phase

Write under "### CEO" in the meeting file. Stake a real position — others push back in Challenge.
After writing, check_messages immediately.

Write [NEEDS CLARIFY: X] if something needs defining before you can contribute fully.
Write [SATISFIED] at any point if happy with the direction (noted, not acted on until after Stress Test).
```

**To each department:**
```
[MEETING — DIVERGE] Topic: [topic]

Generate ideas — no criticism yet. Answer:
1. Your honest take — what's the real problem or opportunity from your angle?
2. What you'd build, propose, or change
3. What another department is probably going to miss
4. One assumption you want to challenge later

Write under "### [Dept]" in the meeting file. Stake real positions — others respond to yours in Challenge.
After writing, check_messages immediately.

Write [NEEDS CLARIFY: X] if something needs defining before you can contribute fully.
Write [SATISFIED] at any point if happy with the direction (noted, not acted on until after Stress Test).
```

Tell Patrick: "Diverge sent. Give agents 2-3 minutes."

---

### Step 3 — Phase: Clarify (optional)

**Run if:** Diverge produced `[NEEDS CLARIFY]` flags, or agents are clearly using the same terms to mean different things.
**Skip if:** Diverge responses were clear and agents share a common frame.

Add section to meeting file:
```markdown
## Phase: Clarify

**Clarifications needed:**
- [X from Frontend]
- [Y from CEO]

### Chair clarifications
[Definitions or Patrick's decision on contested terms]
```

Send to agents who flagged clarifications:
```
[MEETING — CLARIFY] Topic: [topic]

Before Challenge, clarifying:
- [X]: [definition / Patrick's decision]
- [Y]: [definition / Patrick's decision]

Does this change your Diverge position? Update your section if needed, confirm you're clear.
After writing, check_messages immediately.
```

---

### Step 4 — Phase: Challenge (mandatory)

Read all Diverge (and Clarify) responses. Find 3-5 **genuine tensions** — direct contradictions, incompatible assumptions, things one agent flagged as critical that others ignored. Don't manufacture conflict; don't smooth over real disagreement.

Add section to meeting file:
```markdown
## Phase: Challenge

**Tensions identified:**

**T1: [Label]** — [Dept A] says [X], [Dept B] says [Y]. Incompatible.
**T2: [Label]** — CEO assumes [A] but [Dept C] read is [B].
**T3: [Label]** — [Dept D] flagged [Z] but nobody else addressed it.

### [Dept A] + [Dept B] respond to T1
_Awaiting response_
```

Send **targeted** messages — only agents in genuine conflict:
```
[MEETING — CHALLENGE] Topic: [topic]

Respond to these tensions directly:

**T1: [Label]**
[Dept B] said: "[exact quote]"
Your Diverge position was: "[exact quote]"
These are incompatible. Who's right and why? Be direct — "X is wrong because Y."

Write under "### [your dept] responds to T1". After writing, check_messages immediately.

Write [BACK TO CHALLENGE: reason] in a later phase if you hit a new tension that needs resolving.
Write [SATISFIED] if happy with where this is heading (noted, not acted on until after Stress Test).
```

Report tensions to Patrick before sending.

**Loop back:** If Build responses contain `[BACK TO CHALLENGE: reason]`, add a new Challenge section, route only the agents involved, resolve it, then continue to Build.

---

### Step 5 — Phase: Build (mandatory)

After Challenge resolves the main tensions, take the strongest surviving ideas and develop them.

Add section:
```markdown
## Phase: Build

**Surviving ideas to develop:**
- [Idea A from Dept X — survived T1/T2 challenge]
- [Idea B from CEO — unchallenged, needs development]
```

Send to all (or targeted if only specific ideas need development):
```
[MEETING — BUILD] Topic: [topic]

Challenge is done. Strongest surviving ideas:
- [Idea A]
- [Idea B]

Your job this phase: develop one further, or propose how to combine them. Don't critique — build.
Be concrete: what does this actually look like? What's the first step? What does it need to work?

Write under "## Phase: Build / ### [your dept]". After writing, check_messages immediately.

Write [BACK TO CHALLENGE: reason] if you hit a new tension that needs resolving first.
Write [SATISFIED] if happy with the direction (noted, not acted on until after Stress Test).
```

**Loop back:** If Build responses contain `[BACK TO CHALLENGE: reason]`, run a targeted Challenge on the new tension, then return to Build.

---

### Step 6 — Phase: Stress Test (mandatory)

When Build has produced a concrete direction or proposal, attack it before committing.

Add section:
```markdown
## Phase: Stress Test

**Direction/proposal under attack:** [specific description]
```

Send to all:
```
[MEETING — STRESS TEST] Topic: [topic]

A direction is forming: [description]

Your job this phase: attack it. Find the holes, the bad assumptions, the things that will go wrong in practice. Don't defend it — break it.
If you've tried and it held up, say why and flag [SATISFIED].

Write under "## Phase: Stress Test / ### [your dept]". After writing, check_messages immediately.

Write [BACK TO BUILD: reason] if Stress Test reveals a genuinely better approach worth developing.
Write [CLOSE MEETING: reason] (CEO only) if the meeting has run its course.
Write [SATISFIED] if the direction survived your scrutiny.
```

**Loop back:** If Stress Test responses contain `[BACK TO BUILD: reason]`, add a new Build section, develop the refined idea, then run Stress Test again.

**Close triggers now active:**
- CEO writes `[CLOSE MEETING: reason]` → close immediately
- All agents write `[SATISFIED]` → close immediately
- Patrick says "close" → close immediately
- Otherwise → assess: Converge if unresolved, close if clear consensus

---

### Step 7 — Phase: Converge (optional)

**Run if:** Stress Test ended with remaining genuine disagreements worth resolving explicitly.
**Skip if:** Stress Test ended with clear consensus and all (or most) agents satisfied.

```
[MEETING — CONVERGE] Topic: [topic]

Here's where we are after Stress Test: [summary of what held up and what didn't]

What do you actually agree on? What's still genuinely unresolved — be specific.

Write under "## Phase: Converge / ### [your dept]". After writing, check_messages immediately.
Flag [SATISFIED] when done. CEO: flag [CLOSE MEETING: reason] to close now.
```

---

### Step 8 — Phase: Decide (only if unresolved)

Only if Converge (or Stress Test) still has genuine unresolved conflict. Send to CEO only:

```
[MEETING — DECIDE] Topic: [topic]

Still genuinely unresolved:
- [Item 1: what's the disagreement]
- [Item 2: what's the disagreement]

Read the full meeting file. Give a verdict:
1. On [Item 1]: the right call is [X] because [Y]
2. On [Item 2]: the right call is [X] because [Y]
3. What Patrick needs to decide (if anything you can't call)

Write under "## Phase: Decide". Verdict, not summary. After writing, check_messages immediately.
```

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
- Phases run → fill the list (e.g., `[Diverge, Challenge, Build, Stress Test]`)
- Fill `## Action Items`

### Step 4 — Broadcast Close

```
[MEETING CLOSE] [topic] | Decided: [2-3 sentences] | Your tasks are in briefing.md | Notes: .orchestra/meetings/[file]
```

### Step 5 — Report to Patrick

```
Meeting closed. Phases: [Diverge → Challenge → Build → Stress Test → ...]

Decided: [key decisions]
Unresolved (your call): [anything left open]

Actions: CEO [n] | Frontend [n] | Backend [n] | DevOps [n] | Content [n] | MCP [n]
Written to each dept's briefing.md.
```

---

## Meeting Type → Suggested Phase Path

| Type | Phase Path | Notes |
|------|-----------|-------|
| Sprint planning | Diverge → Challenge → Build → Stress Test | Full minimum path |
| Feature design | Diverge → Challenge → Build → Stress Test | Build designs it, Stress Test breaks it |
| Strategy / big bets | All phases | Converge + Decide critical for major calls |
| Post-mortem | Diverge → Challenge → Build → Stress Test | Build develops fixes, Stress Test attacks them |
| Partnership pitch | Diverge → Challenge → Build → Stress Test | Stress Test attacks the pitch before it goes out |
| Quick align | Diverge → Challenge | Only if topic is narrow and consensus forms fast |

---

## Tips

- **Challenge is the pivot** — Diverge without Challenge is a brainstorm.
- **Build before Stress Test** — ideas need development before they can be meaningfully attacked.
- **Loop back liberally** — Build reveals tensions → loop to Challenge. Stress Test reveals better ideas → loop to Build. This is the point of the state machine.
- **Clarify early** — if agents are using the same terms differently, run Clarify before Challenge, not after.
- **Decide sparingly** — most meetings shouldn't need it. Clear Stress Test → just close.
- **CEO closes after Stress Test** — `[CLOSE MEETING: reason]` signals diminishing returns.
- **Meeting files are permanent** — stored in `.orchestra/meetings/` as institutional memory.
