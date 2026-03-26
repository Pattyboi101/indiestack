#!/usr/bin/env python3
"""
Pre-seed top npm/pip packages as reference tools so first-run
analyses are instant instead of 12s.

Usage:
    python3 scripts/preseed_packages.py
"""

import asyncio
import json
import os
import sys
import glob

import aiosqlite
import httpx

DB_PATH = os.environ.get("DB_PATH", "")

# Top npm packages by usage — these appear in almost every package.json
TOP_NPM = [
    "react", "react-dom", "next", "vue", "svelte", "angular",
    "typescript", "eslint", "prettier", "jest", "vitest", "mocha",
    "express", "fastify", "koa", "hono",
    "tailwindcss", "postcss", "autoprefixer", "sass",
    "axios", "node-fetch", "got",
    "lodash", "underscore", "ramda",
    "zod", "yup", "joi",
    "prisma", "@prisma/client", "drizzle-orm", "typeorm", "sequelize", "mongoose", "knex",
    "stripe", "@stripe/stripe-js",
    "dotenv", "cross-env",
    "webpack", "vite", "esbuild", "rollup", "parcel", "turbo",
    "framer-motion", "gsap",
    "zustand", "redux", "@reduxjs/toolkit", "jotai", "recoil",
    "react-query", "@tanstack/react-query", "swr",
    "react-hook-form", "formik",
    "react-router-dom", "next-auth", "@auth/core",
    "date-fns", "dayjs", "moment", "luxon",
    "uuid", "nanoid",
    "commander", "yargs", "inquirer", "chalk", "ora",
    "nodemon", "ts-node", "tsx",
    "cors", "helmet", "morgan", "compression",
    "socket.io", "ws",
    "sharp", "jimp",
    "nodemailer", "resend",
    "pino", "winston", "bunyan",
    "supertest", "playwright", "@playwright/test", "cypress",
    "storybook", "@storybook/react",
    "husky", "lint-staged", "commitlint",
    "@clerk/nextjs", "@supabase/supabase-js",
    "lucide-react", "react-icons", "@heroicons/react",
    "clsx", "class-variance-authority", "tailwind-merge",
    "contentlayer", "next-mdx-remote", "gray-matter",
    "uploadthing", "@uploadthing/react",
    "trpc", "@trpc/server", "@trpc/client",
]

# Top pip packages
TOP_PIP = [
    "django", "flask", "fastapi", "starlette", "uvicorn", "gunicorn",
    "requests", "httpx", "aiohttp", "urllib3",
    "sqlalchemy", "alembic", "psycopg2-binary", "asyncpg",
    "celery", "redis", "rq",
    "pydantic", "marshmallow", "attrs",
    "pytest", "pytest-asyncio", "pytest-cov", "tox", "nox",
    "black", "ruff", "flake8", "mypy", "isort",
    "boto3", "google-cloud-storage",
    "pillow", "numpy", "pandas", "scipy",
    "jinja2", "mako",
    "click", "typer", "rich", "tqdm",
    "sentry-sdk", "loguru",
    "python-dotenv", "pyyaml", "toml",
    "cryptography", "pyjwt", "passlib", "bcrypt",
    "stripe", "paypalrestsdk",
    "aiosqlite", "databases",
    "python-multipart", "python-jose",
    "dramatiq", "huey",
]


async def preseed(packages: list[str], manifest_type: str, db, client: httpx.AsyncClient):
    """Pre-ingest packages from registry."""
    pkg_key = "npm" if manifest_type == "package.json" else "pip"
    created = 0
    skipped = 0

    for pkg in packages:
        # Check if already exists
        if manifest_type == "package.json":
            slug = f"npm-{pkg.replace('/', '-').replace('@', '')}"
        else:
            slug = f"pypi-{pkg.replace('-', '_')}"

        c = await db.execute("SELECT id FROM tools WHERE slug = ? OR sdk_packages LIKE ?", (slug, f'%"{pkg}"%'))
        if await c.fetchone():
            skipped += 1
            continue

        # Also check by exact slug match (non-prefixed)
        c = await db.execute("SELECT id FROM tools WHERE slug = ?", (pkg.replace("@", "").replace("/", "-"),))
        if await c.fetchone():
            skipped += 1
            continue

        # Fetch from registry
        try:
            if manifest_type == "package.json":
                resp = await client.get(f"https://registry.npmjs.org/{pkg}",
                                       headers={"Accept": "application/json"})
            else:
                resp = await client.get(f"https://pypi.org/pypi/{pkg}/json")

            if resp.status_code != 200:
                continue

            data = resp.json()

            if manifest_type == "package.json":
                name = data.get("name", pkg)
                desc = (data.get("description") or "")[:200]
                last_modified = (data.get("time") or {}).get("modified")
                sdk_json = json.dumps({"npm": pkg})
                repo = data.get("repository", {})
                github_url = ""
                if isinstance(repo, dict):
                    github_url = (repo.get("url") or "").replace("git+", "").replace("git://", "https://").rstrip(".git")
                if "github.com" not in github_url:
                    github_url = ""
            else:
                info = data.get("info", {})
                name = info.get("name", pkg)
                desc = (info.get("summary") or "")[:200]
                urls_list = data.get("urls") or []
                last_modified = urls_list[-1]["upload_time"] if urls_list else None
                sdk_json = json.dumps({"pip": pkg})
                github_url = ""
                for key in ("Source", "Source Code", "Repository", "GitHub", "Homepage"):
                    url = (info.get("project_urls") or {}).get(key, "")
                    if "github.com" in url:
                        github_url = url
                        break

            await db.execute("""
                INSERT OR IGNORE INTO tools
                (name, slug, tagline, description, url, github_url,
                 github_last_commit, is_reference, sdk_packages, status,
                 category_id, source_type, health_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'approved', 18, 'code', 'alive')
            """, (name, slug, desc[:100], desc, github_url or "", github_url, last_modified, sdk_json))
            created += 1

        except Exception as e:
            print(f"  Error fetching {pkg}: {e}")

        if (created + skipped) % 20 == 0:
            await db.commit()
            await asyncio.sleep(0.3)

    await db.commit()
    return created, skipped


async def main():
    db_path = DB_PATH
    if not db_path:
        backups = sorted(glob.glob("backups/indiestack-*.db"))
        db_path = backups[-1] if backups else "indiestack.db"

    def _dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    print(f"Pre-seeding top packages (db: {db_path})")

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = _dict_factory
        await db.execute("PRAGMA journal_mode=WAL")

        try:
            await db.execute("ALTER TABLE tools ADD COLUMN is_reference INTEGER DEFAULT 0")
        except Exception:
            pass
        await db.commit()

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            print(f"\nSeeding {len(TOP_NPM)} npm packages...")
            npm_created, npm_skipped = await preseed(TOP_NPM, "package.json", db, client)
            print(f"  Created: {npm_created}, Skipped (already exist): {npm_skipped}")

            print(f"\nSeeding {len(TOP_PIP)} pip packages...")
            pip_created, pip_skipped = await preseed(TOP_PIP, "requirements.txt", db, client)
            print(f"  Created: {pip_created}, Skipped (already exist): {pip_skipped}")

        c = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE is_reference = 1")
        row = await c.fetchone()
        print(f"\nTotal reference tools in DB: {row['cnt']}")


if __name__ == "__main__":
    asyncio.run(main())
