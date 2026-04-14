---
description: Backup Production Database
---

Working directory: `~/indiestack`

## 1. Create backup directory

```bash
mkdir -p ~/indiestack/backups
```

## 2. Download database from Fly

```bash
cd ~/indiestack && ~/.fly/bin/flyctl ssh console -C "cat /data/indiestack.db" > backups/indiestack-$(date +%Y%m%d-%H%M%S).db
```

## 3. Verify backup

```bash
LATEST=$(ls -t ~/indiestack/backups/*.db | head -1)
SIZE=$(du -h "$LATEST" | cut -f1)
echo "Backup: $LATEST ($SIZE)"
sqlite3 "$LATEST" "SELECT COUNT(*) || ' tools' FROM tools; SELECT COUNT(*) || ' makers' FROM makers; SELECT COUNT(*) || ' categories' FROM categories;"
```

If the file is 0 bytes or sqlite3 fails, the backup is bad — alert the user.

## 4. Clean old backups (keep last 5)

```bash
cd ~/indiestack/backups && ls -t *.db | tail -n +6 | xargs rm -f 2>/dev/null
```

## 5. Report

Tell the user:
- Backup filename and size
- Tool/maker/category counts as sanity check
- Number of backups stored locally
- Reminder: these are local-only backups

## 6. Log to hub (best effort)

Skip if HUB_URL is not set.

```bash
curl -s -X POST -H "X-Hub-Secret: $HUB_SECRET" -H "Content-Type: application/json" \
  "$HUB_URL/activity" -d '{"actor":"patrick","action":"backed up database","detail":"SIZE"}'
```

Replace SIZE with the backup file size.
