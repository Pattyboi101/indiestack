# Review Checklist — Strategy & QA Skill

Structured review framework for every task that comes through S&QA.

## Quick Assessment (under 30 seconds)
1. Does this task have a SPECIFIC outcome? If vague, challenge.
2. Has this already been done this session? Check the playbook. If yes, veto.
3. Does this need production access? If SSH is down, flag as blocked.

## Revenue Path Check
- Does this task move us toward revenue? (even indirectly)
- If not, is it maintenance/security? (acceptable)
- If neither, is it busywork? (veto)

## Input Validation
- Do referenced files exist? (Caught /tmp/ files missing after restart — major save)
- Are the tool slugs correct? (Caught wrong install commands on maker pages)
- Are the email addresses real? (Verify before sending)

## Overconfidence Flags
- Is Master calling something a "moat"? Challenge.
- Are we inventing revenue numbers? Challenge.
- Are we doing the same audit for the third time? Veto.
- Are we building features for users who don't exist yet? Challenge.

## When to Approve Quickly
- Smoke test / health check — always approve
- Data push to production — always approve
- Bug fix for something users will hit — approve with "verify after"
- Outreach prep — approve if targets are specific

## When to Slow Down
- Changes to pricing, auth, payments — scrutinize
- "Let's redesign X" — challenge scope
- "Let's add a new feature" — who asked for it?
- Strategy pivots — has enough time passed since the last one?

## Lessons Learned (2026-03-30)
- The claim link URLs were broken in ALL 13 outreach emails — caught before any maker clicked
- /tmp files don't survive session restarts — caught before dispatching agents to work on missing files
- Third code review in same session was correctly vetoed as busywork
- "Do nothing and wait for signal" was the right call after distribution was complete
