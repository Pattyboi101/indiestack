# IndieStack Dependency Audit

Scan your `package.json`, `requirements.txt`, or `pyproject.toml` for indie alternatives. Finds lighter, maintained developer tools you might be missing.

## Usage

Add to `.github/workflows/indiestack-audit.yml`:

```yaml
name: IndieStack Audit
on:
  pull_request:
    paths:
      - 'package.json'
      - 'requirements.txt'
      - 'pyproject.toml'

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: indiestack/audit-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## What it does

When dependencies change in a PR, the action:

1. Parses your dependency files
2. Matches dependencies against 40+ known patterns (auth, payments, analytics, monitoring, etc.)
3. Searches IndieStack's catalog for indie alternatives
4. Posts a PR comment with results

Example output:

### `@sentry/node` (monitoring)

| Tool | Type | Description |
|------|------|-------------|
| [GlitchTip](https://indiestack.ai/tool/glitchtip) | Code | Open-source error tracking |
| [Highlight](https://indiestack.ai/tool/highlight) | Code | Session replay and error monitoring |

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `github-token` | GitHub token for PR comments | `${{ github.token }}` |
| `indiestack-api-key` | Optional API key for higher rate limits | (none) |
| `files` | Comma-separated files to scan | auto-detected |
| `comment` | Post results as PR comment | `true` |

## Outputs

| Output | Description |
|--------|-------------|
| `findings` | JSON array of findings |
| `count` | Number of dependencies with alternatives |

## Supported files

- `package.json` (npm/yarn/pnpm)
- `requirements.txt` (pip)
- `pyproject.toml` (Python)

## Links

- [IndieStack](https://indiestack.ai) — 3,100+ developer tools
- [MCP Server](https://pypi.org/project/indiestack/) — Get recommendations in Claude Code, Cursor, and Windsurf
