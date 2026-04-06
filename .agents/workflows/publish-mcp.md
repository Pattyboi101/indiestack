---
description: Publish MCP Server to PyPI
---

Working directory: `~/indiestack`

## 1. Check current version

```bash
cd ~/indiestack && grep 'version = ' pyproject.toml
```

```bash
pip3 index versions indiestack 2>/dev/null || echo "Could not check PyPI"
```

## 2. Determine version bump

Review recent changes to `src/indiestack/mcp_server.py` and related files since last publish. Suggest:
- **Patch** (X.Y.Z+1) for bug fixes
- **Minor** (X.Y+1.0) for new features/tools
- **Major** (X+1.0.0) for breaking changes

Ask the user to confirm the new version.

## 3. Update version

Edit `pyproject.toml` to set the new version number.

## 4. Update changelog

Check if `README_PYPI.md` needs a changelog entry for the new version. Add one if there are notable changes.

## 5. Build

```bash
cd ~/indiestack && python3 -m build
```

## 6. Upload to PyPI

```bash
cd ~/indiestack && python3 -m twine upload dist/indiestack-NEW_VERSION*
```

Replace NEW_VERSION with the version just set. PyPI token is in `~/.pypirc`.

## 7. Verify

```bash
pip3 index versions indiestack 2>/dev/null
```

Confirm the new version appears.

## 8. Update server.json

Update the version field in `server.json` to match the new version.

## 9. Commit and push

```bash
cd ~/indiestack && git add pyproject.toml README_PYPI.md server.json && git commit -m "chore: publish MCP server vNEW_VERSION to PyPI" && git push
```

## 10. Notify

```bash
bash ~/.claude/telegram.sh "IndieStack MCP server vNEW_VERSION published to PyPI"
```

## 11. Log to hub (best effort)

Skip if HUB_URL is not set.

```bash
curl -s -X POST -H "X-Hub-Secret: $HUB_SECRET" -H "Content-Type: application/json" \
  "$HUB_URL/activity" -d '{"actor":"patrick","action":"published MCP vNEW_VERSION","detail":"uploaded to PyPI"}'
```
