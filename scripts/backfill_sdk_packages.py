#!/usr/bin/env python3
"""Backfill sdk_packages column from KNOWN_PACKAGE_MAP.

Run on production: python3 /app/scripts/backfill_sdk_packages.py
Or with --dry-run to just print what would change.
"""
import sqlite3
import sys

# Inverted from mine_github_compatibility.py KNOWN_PACKAGE_MAP
# slug -> set of package names
SLUG_TO_PACKAGES = {}

KNOWN_PACKAGE_MAP = {
    # npm packages
    "@supabase/supabase-js": "supabase",
    "@supabase/ssr": "supabase",
    "@supabase/auth-helpers-nextjs": "supabase",
    "supabase": "supabase",
    "@auth0/auth0-react": "auth0",
    "@auth0/nextjs-auth0": "auth0",
    "auth0": "auth0",
    "auth0-lock": "auth0",
    "stripe": "stripe",
    "@stripe/stripe-js": "stripe",
    "@stripe/react-stripe-js": "stripe",
    "posthog-js": "posthog",
    "@posthog/react": "posthog",
    "posthog-node": "posthog",
    "@sentry/node": "sentry",
    "@sentry/react": "sentry",
    "@sentry/nextjs": "sentry",
    "@sentry/browser": "sentry",
    "sentry": "sentry",
    "@clerk/nextjs": "clerk",
    "@clerk/clerk-react": "clerk",
    "@clerk/backend": "clerk",
    "@clerk/themes": "clerk",
    "next-auth": "next-auth",
    "@prisma/client": "prisma",
    "prisma": "prisma",
    "@planetscale/database": "planetscale",
    "drizzle-orm": "drizzle-orm",
    "resend": "resend",
    "@react-email/components": "resend",
    "appwrite": "appwrite",
    "@novu/node": "novu",
    "@novu/notification-center": "novu",
    "pocketbase": "pocketbase",
    "firebase": "firebase",
    "firebase-admin": "firebase",
    "@firebase/app": "firebase",
    "convex": "convex",
    "@convex-dev/auth": "convex",
    "@upstash/redis": "upstash",
    "@upstash/ratelimit": "upstash",
    "bullmq": "bullmq",
    "bull": "bullmq",
    "@lemonsqueezy/lemonsqueezy.js": "lemon-squeezy",
    "@polar-sh/sdk": "polar",
    "@paddle/paddle-js": "paddle",
    "paddle-sdk": "paddle",
    "@kinde-oss/kinde-auth-nextjs": "kinde",
    "@logto/next": "logto",
    "@logto/node": "logto",
    "lucia": "lucia-auth",
    "@hanko/elements": "hanko",
    "hanko-elements": "hanko",
    "payload": "payload",
    "tinacms": "tina",
    "@directus/sdk": "directus",
    "@strapi/strapi": "strapi",
    "@tryghost/content-api": "ghost",
    "@sanity/client": "sanity",
    "next-sanity": "sanity",
    "contentful": "contentful",
    "@contentful/rich-text-react-renderer": "contentful",
    "meilisearch": "meilisearch",
    "typesense": "typesense",
    "algolia": "algolia",
    "algoliasearch": "algolia",
    "@algolia/client-search": "algolia",
    "flagsmith": "flagsmith",
    "@growthbook/growthbook-react": "growthbook",
    "@growthbook/growthbook": "growthbook",
    "unleash-client": "unleash",
    "@calcom/embed-react": "cal-com",
    "plausible-tracker": "plausible-analytics",
    "simple-analytics-script": "simple-analytics",
    "@umami/node": "umami",
    "fathom-client": "fathom-analytics",
    "pirsch-sdk": "pirsch",
    "@aptabase/web": "aptabase",
    "@aptabase/react": "aptabase",
    "matomo-tracker": "matomo",
    "countly-sdk-web": "countly",
    "cloudinary": "cloudinary",
    "@uploadthing/react": "npm-uploadthing",
    "uploadthing": "npm-uploadthing",
    "minio": "minio",
    "@plunk/node": "plunk",
    "postmark": "postmark",
    "nodemailer": "nodemailer",
    "@sendgrid/mail": "sendgrid",
    "mailgun.js": "mailgun",
    "@ory/client": "ory",
    "@zitadel/node": "zitadel",
    "keycloak-js": "keycloak",
    "redis": "redis",
    "ioredis": "redis",
    "@libsql/client": "turso",
    "@neondatabase/serverless": "neon",
    "mongoose": "mongodb",
    "mongodb": "mongodb",
    "@vercel/analytics": "vercel-analytics",
    "@vercel/speed-insights": "vercel-analytics",
    "tailwindcss": "tailwind-css",
    "daisyui": "daisyui",
    "@radix-ui/react-dialog": "radix-ui",
    "@radix-ui/themes": "radix-ui",
    "@shadcn/ui": "shadcn-ui",
    "framer-motion": "framer-motion",
    "@headlessui/react": "headless-ui",
    "zod": "zod",
    "trpc": "trpc",
    "@trpc/server": "trpc",
    "@trpc/client": "trpc",
    "inngest": "inngest",
    "trigger.dev": "trigger-dev",
    "@trigger.dev/sdk": "trigger-dev",
    "highlight.io": "highlight",
    "@highlight-run/next": "highlight",
    "axiom": "axiom",
    "@axiomhq/js": "axiom",
    "@logtail/node": "better-stack",
    "graphql-yoga": "graphql-yoga",
    "nextra": "nextra",
    "mintlify": "mintlify",
    "docusaurus": "docusaurus",
    "@docusaurus/core": "docusaurus",
    "storybook": "storybook",
    "@storybook/react": "storybook",
    "chromatic": "chromatic",
    "cypress": "cypress",
    "playwright": "playwright",
    "@playwright/test": "playwright",
    "vitest": "vitest",
    "jest": "jest",
    # pip packages
    "posthog": "posthog",
    "sentry-sdk": "sentry",
    "sentry_sdk": "sentry",
    # "stripe": "stripe",  # duplicate
    # "supabase": "supabase",  # duplicate
    # "appwrite": "appwrite",  # duplicate
    # "resend": "resend",  # duplicate
    # "meilisearch": "meilisearch",  # duplicate
    # "typesense": "typesense",  # duplicate
    # "flagsmith": "flagsmith",  # duplicate
    "UnleashClient": "unleash",
    "qdrant-client": "qdrant",
    "weaviate-client": "weaviate",
    # "minio": "minio",  # duplicate
    # "cloudinary": "cloudinary",  # duplicate
    "firecrawl-py": "firecrawl",
    "lago-python-client": "lago",
    "killbill": "kill-bill",
    "polar-python": "polar",
    "paddle-billing": "paddle",
    "clerk-backend-api": "clerk",
    "novu": "novu",
    "ntfy-wrapper": "ntfy",
    "dify-client": "dify",
    "hanko-python": "hanko",
    "supertokens-python": "supertokens",
    "ory-client": "ory",
    # "redis": "redis",  # duplicate
    "celery": "celery",
    "dramatiq": "dramatiq",
    "boto3": "aws-s3",
    "django-allauth": "django-allauth",
    "authlib": "authlib",
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "sqlalchemy": "sqlalchemy",
    # "prisma": "prisma",  # duplicate
    "psycopg2": "postgresql",
    "psycopg2-binary": "postgresql",
    "pymongo": "mongodb",
    "motor": "mongodb",
    "httpx": "httpx",
    "pydantic": "pydantic",
    "alembic": "pypi-alembic",
    "pytest": "pytest",
    "pirsch-api": "pirsch",
    # "plausible-tracker": "plausible-analytics",  # duplicate
}

# Invert: slug -> sorted list of packages
for pkg, slug in KNOWN_PACKAGE_MAP.items():
    SLUG_TO_PACKAGES.setdefault(slug, set()).add(pkg)


def main():
    dry_run = "--dry-run" in sys.argv
    db_path = "/data/indiestack.db"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get current sdk_packages for all relevant slugs
    slugs = list(SLUG_TO_PACKAGES.keys())
    placeholders = ",".join("?" for _ in slugs)
    rows = conn.execute(
        f"SELECT slug, sdk_packages FROM tools WHERE slug IN ({placeholders})",
        slugs,
    ).fetchall()

    found_slugs = {r["slug"]: r["sdk_packages"] for r in rows}

    updated = 0
    skipped_existing = 0
    skipped_missing = 0

    for slug in sorted(SLUG_TO_PACKAGES.keys()):
        packages = ",".join(sorted(SLUG_TO_PACKAGES[slug]))

        if slug not in found_slugs:
            print(f"SKIP (no tool): {slug}")
            skipped_missing += 1
            continue

        current = found_slugs[slug]
        if current and current.strip():
            print(f"SKIP (has data): {slug} -> {current}")
            skipped_existing += 1
            continue

        print(f"UPDATE: {slug} -> {packages}")
        if not dry_run:
            conn.execute(
                "UPDATE tools SET sdk_packages = ? WHERE slug = ?",
                (packages, slug),
            )
        updated += 1

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n--- Summary ---")
    print(f"Updated: {updated}")
    print(f"Skipped (already has data): {skipped_existing}")
    print(f"Skipped (slug not found): {skipped_missing}")


if __name__ == "__main__":
    main()
