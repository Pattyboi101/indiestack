# Command Hub Query

Query the IndieStack Command Hub. Uses `$ARGUMENTS` to determine what to do.

## Setup

```
HUB_URL: https://govlink.fly.dev
HUB_SECRET: HnbKA_OOFY_3Efx3YKRZHFvcyVsWEYkpja5ECiAtAhA
```

All requests need the header: `X-Hub-Secret: $HUB_SECRET`

The current user is "patrick".

## Parse $ARGUMENTS

| Input | Action |
|-------|--------|
| (empty) or "tasks" | GET /tasks?assignee=patrick — show open tasks |
| "all tasks" | GET /tasks — show all tasks |
| "activity" | GET /activity?limit=10 — recent activity |
| "search QUERY" | GET /search?q=QUERY — search across everything |
| "ideas" | GET /ideas — list ideas |
| "decisions" | GET /decisions — list decisions |
| "messages" | GET /messages?for=patrick&unread=true — unread messages |
| "add task TITLE" | POST /tasks with {"title":"TITLE","assignee":"patrick","created_by":"patrick"} |
| "add idea TITLE" | POST /ideas with {"title":"TITLE","created_by":"patrick"} |
| "log DESCRIPTION" | POST /activity with {"actor":"patrick","action":"DESCRIPTION"} |
| "send ED_MESSAGE" | POST /messages with {"from_dev":"patrick","to_dev":"ed","text":"ED_MESSAGE"} |
| "summary" | GET /tasks/summary — sprint progress |

## Display

Format results readably:
- **Tasks**: title, assignee, priority, status, due date
- **Activity**: actor, action, timestamp
- **Ideas**: title, category, status, who posted
- **Decisions**: title, rationale
- **Messages**: sender, text, timestamp
- **Search**: grouped by type

## Example curl

```bash
curl -s -H "X-Hub-Secret: HnbKA_OOFY_3Efx3YKRZHFvcyVsWEYkpja5ECiAtAhA" \
  "https://govlink.fly.dev/tasks?assignee=patrick" | python3 -m json.tool
```
