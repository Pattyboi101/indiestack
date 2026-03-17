# IndieStack Status Dashboard

Working directory: `~/indiestack`

Run all checks in parallel where possible, then present as a compact dashboard.

## Checks

### 1. Fly machine status

```bash
cd ~/indiestack && ~/.fly/bin/flyctl status 2>&1 | head -15
```

### 2. Production health

```bash
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" https://indiestack.fly.dev/health
```

### 3. Key pages (expect 200)

```bash
for path in / /explore /gaps /submit; do
  echo "$path $(curl -sL -o /dev/null -w '%{http_code}' https://indiestack.fly.dev$path)"
done
```

### 4. Recent deploys

```bash
cd ~/indiestack && ~/.fly/bin/flyctl releases -n 3
```

### 5. Git status

```bash
cd ~/indiestack && git status --short && echo "---" && git log --oneline -5
```

### 6. PyPI vs local version

```bash
cd ~/indiestack && echo "Local: $(grep 'version = ' pyproject.toml)" && echo "PyPI: $(pip3 index versions indiestack 2>/dev/null || echo 'unknown')"
```

## Output format

```
INDIESTACK STATUS
─────────────────
Health:    [200 OK / DOWN] (response time)
Machine:   [running / stopped] (region)
Pages:     / ✓  /explore ✓  /gaps ✓  /submit ✓
Git:       [X uncommitted] last: "commit msg"
MCP:       local vX.Y.Z / PyPI vA.B.C
Deploys:   (last 3 releases)
```

Flag anything non-200 or unexpected prominently.
