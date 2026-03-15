#!/usr/bin/env bash
# IndieStack Dependency Audit — scans package.json/requirements.txt for indie alternatives
set -euo pipefail

API_BASE="https://indiestack.ai/api"

# ── Find dependency files ────────────────────────────────────────────────

dep_files=()
if [ -n "${INPUT_FILES:-}" ]; then
  IFS=',' read -ra dep_files <<< "$INPUT_FILES"
else
  [ -f "package.json" ] && dep_files+=("package.json")
  [ -f "requirements.txt" ] && dep_files+=("requirements.txt")
  [ -f "Pipfile" ] && dep_files+=("Pipfile")
  [ -f "pyproject.toml" ] && dep_files+=("pyproject.toml")
fi

if [ ${#dep_files[@]} -eq 0 ]; then
  echo "No dependency files found. Skipping audit."
  echo "count=0" >> "$GITHUB_OUTPUT"
  echo "findings=[]" >> "$GITHUB_OUTPUT"
  exit 0
fi

echo "Scanning: ${dep_files[*]}"

# ── Run the full audit in Python ─────────────────────────────────────────
# Single Python script handles: parse deps, match mappings, call API, format output

export INDIESTACK_API_KEY="${INDIESTACK_API_KEY:-}"

python3 - "${dep_files[@]}" <<'PYEOF'
import json, os, sys
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError

API_BASE = "https://indiestack.ai/api"
API_KEY = os.environ.get("INDIESTACK_API_KEY", "")

# Dependency-to-category mappings (synced with mcp_server.py DEPENDENCY_MAPPINGS)
DEP_MAP = {
    # JavaScript — auth
    "passport": "auth", "jsonwebtoken": "auth", "next-auth": "auth",
    "lucia": "auth", "@auth/core": "auth", "@clerk/nextjs": "auth",
    "supertokens": "auth",
    # JavaScript — payments
    "stripe": "payments", "@lemonsqueezy": "payments", "paddle-sdk": "payments",
    # JavaScript — email
    "nodemailer": "email", "resend": "email", "@sendgrid/mail": "email",
    "mailgun": "email", "postmark": "email",
    # JavaScript — analytics & monitoring
    "posthog-js": "analytics", "mixpanel": "analytics", "amplitude": "analytics",
    "@sentry/node": "monitoring", "@sentry/react": "monitoring",
    "newrelic": "monitoring", "datadog": "monitoring",
    # JavaScript — database & ORM
    "pg": "database", "mongoose": "database", "sequelize": "database",
    "prisma": "database", "drizzle-orm": "database", "knex": "database",
    "typeorm": "database",
    # JavaScript — infrastructure
    "aws-sdk": "cloud infrastructure", "firebase": "backend as a service",
    "@supabase/supabase-js": "backend as a service",
    "socket.io": "websockets", "bull": "job queue", "bullmq": "job queue",
    "agenda": "job queue",
    # JavaScript — misc
    "winston": "logging", "morgan": "logging", "pino": "logging",
    "multer": "file upload", "sharp": "image processing",
    "puppeteer": "browser automation", "playwright": "browser automation",
    # Python
    "celery": "job queue", "boto3": "cloud infrastructure",
    "sqlalchemy": "database", "sentry-sdk": "monitoring",
    "python-jose": "auth", "authlib": "auth",
    # Ruby
    "devise": "auth", "sidekiq": "job queue", "pundit": "auth",
}

# ── Parse dependency files ───────────────────────────────────────────────

def parse_package_json(path):
    deps = []
    try:
        pkg = json.load(open(path))
        for section in ("dependencies", "devDependencies"):
            for name in pkg.get(section, {}):
                deps.append(name.lower())
    except Exception as e:
        print(f"Warning: could not parse {path}: {e}", file=sys.stderr)
    return deps

def parse_requirements_txt(path):
    deps = []
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
            line = line.split(sep)[0]
        dep = line.strip().lower()
        if dep:
            deps.append(dep)
    return deps

def parse_pyproject_toml(path):
    deps = []
    in_deps = False
    for line in open(path):
        stripped = line.strip()
        if stripped == "dependencies = [":
            in_deps = True
            continue
        if in_deps:
            if stripped == "]":
                break
            dep = stripped.strip(' ",')
            for sep in (">=", "==", "<", "["):
                dep = dep.split(sep)[0]
            dep = dep.strip().lower()
            if dep:
                deps.append(dep)
    return deps

files = sys.argv[1:]
all_deps = []
for f in files:
    if not os.path.exists(f):
        print(f"Warning: {f} not found", file=sys.stderr)
        continue
    if f.endswith("package.json"):
        all_deps.extend(parse_package_json(f))
    elif f.endswith("requirements.txt"):
        all_deps.extend(parse_requirements_txt(f))
    elif f.endswith("pyproject.toml"):
        all_deps.extend(parse_pyproject_toml(f))
    else:
        all_deps.extend(parse_requirements_txt(f))  # fallback: line-per-dep

all_deps = list(set(all_deps))
print(f"Found {len(all_deps)} unique dependencies")

# ── Match against mappings ───────────────────────────────────────────────

matched = {}  # dep_name -> category
for dep in all_deps:
    for pattern, category in DEP_MAP.items():
        if pattern in dep:
            matched[dep] = category
            break

print(f"Matched {len(matched)} dependencies to IndieStack categories")

if not matched:
    gh_output = os.environ.get("GITHUB_OUTPUT", "")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write("count=0\n")
            f.write("findings=[]\n")
    print("No replaceable dependencies found.")
    sys.exit(0)

# ── Search IndieStack API ────────────────────────────────────────────────

categories = list(set(matched.values()))
search_results = {}

for cat in categories:
    url = f"{API_BASE}/tools/search?q={quote(cat)}&limit=3&source_type=code"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    try:
        req = Request(url, headers=headers)
        resp = urlopen(req, timeout=10)
        data = json.loads(resp.read())
        search_results[cat] = data.get("tools", [])
    except (URLError, Exception) as e:
        print(f"Warning: API search for '{cat}' failed: {e}", file=sys.stderr)
        search_results[cat] = []

# ── Build markdown report ────────────────────────────────────────────────

findings = []
lines = [
    "<!-- indiestack-audit -->",
    "## IndieStack Dependency Audit",
    "",
    f"Found **{len(matched)}** dependencies with indie alternatives.",
    "",
]

for dep, category in sorted(matched.items()):
    tools = search_results.get(category, [])
    if not tools:
        continue

    lines.append(f"### `{dep}` ({category})")
    lines.append("")
    lines.append("| Tool | Type | Description |")
    lines.append("|------|------|-------------|")

    for t in tools[:3]:
        name = t.get("name", "")
        slug = t.get("slug", "")
        tagline = t.get("tagline", "")
        source = "Code" if t.get("source_type") == "code" else "SaaS"
        link = f"[{name}](https://indiestack.ai/tool/{slug})"
        lines.append(f"| {link} | {source} | {tagline} |")

        findings.append({
            "dependency": dep,
            "category": category,
            "alternative": name,
            "slug": slug,
            "source_type": t.get("source_type", ""),
        })

    lines.append("")

lines.extend([
    "---",
    "*Powered by [IndieStack](https://indiestack.ai) — 3,100+ developer tools your AI should know about.*",
    "*Want this in your editor? `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`*",
])

md = "\n".join(lines)

# Write markdown to temp file for PR comment step
with open("/tmp/indiestack-audit.md", "w") as f:
    f.write(md)

# Write GitHub Action outputs
gh_output = os.environ.get("GITHUB_OUTPUT", "")
if gh_output:
    with open(gh_output, "a") as f:
        f.write(f"count={len(findings)}\n")
        f.write(f"findings={json.dumps(findings)}\n")

# Print summary to console
print(md)
PYEOF

echo "Audit complete."
