#!/usr/bin/env python3
"""Enrich top tools with install commands, env vars, and SDK packages.

Generates SQL UPDATE statements for the top tools that agents actually recommend.
Focuses on well-known dev tools, not reference/registry imports.

Usage:
    python3 scripts/enrich_top_tools.py --dry-run
    python3 scripts/enrich_top_tools.py | fly ssh console -a indiestack -C 'python3 -c "..."'
"""

# Hand-curated enrichment data for high-value tools.
# These are the tools agents should be able to give actionable advice on.

ENRICHMENTS = {
    # ── Auth ────────────────────────────────────────────────────
    "next-auth": {
        "install_command": "npm install next-auth",
        "env_vars": "NEXTAUTH_URL, NEXTAUTH_SECRET",
        "sdk_packages": "next-auth",
        "api_type": "SDK",
        "auth_method": "OAuth/Credentials",
    },
    "lucia-auth": {
        "install_command": "npm install lucia",
        "env_vars": "DATABASE_URL",
        "sdk_packages": "lucia",
        "api_type": "SDK",
        "auth_method": "session-based",
    },
    "devise": {
        "install_command": "gem install devise",
        "env_vars": "DEVISE_SECRET_KEY",
        "sdk_packages": "devise",
        "api_type": "SDK",
        "auth_method": "session-based",
    },
    "passport": {
        "install_command": "npm install passport",
        "env_vars": "SESSION_SECRET",
        "sdk_packages": "passport",
        "api_type": "SDK",
        "auth_method": "strategy-based",
    },
    "keycloak": {
        "install_command": "docker pull quay.io/keycloak/keycloak",
        "env_vars": "KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID",
        "sdk_packages": "keycloak-js,@keycloak/keycloak-admin-client",
        "api_type": "REST",
        "auth_method": "OIDC",
    },
    "authelia": {
        "install_command": "docker pull authelia/authelia",
        "env_vars": "AUTHELIA_JWT_SECRET, AUTHELIA_SESSION_SECRET",
        "sdk_packages": "",
        "api_type": "REST",
        "auth_method": "SSO/2FA",
    },
    "authentik": {
        "install_command": "docker compose up -d",
        "env_vars": "AUTHENTIK_SECRET_KEY, AUTHENTIK_POSTGRESQL__PASSWORD",
        "sdk_packages": "",
        "api_type": "REST",
        "auth_method": "OIDC/SAML",
    },
    # ── ORM / Database ──────────────────────────────────────────
    "prisma": {
        "install_command": "npm install prisma @prisma/client",
        "env_vars": "DATABASE_URL",
        "sdk_packages": "prisma,@prisma/client",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "drizzle": {
        "install_command": "npm install drizzle-orm",
        "env_vars": "DATABASE_URL",
        "sdk_packages": "drizzle-orm,drizzle-kit",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "typeorm": {
        "install_command": "npm install typeorm reflect-metadata",
        "env_vars": "DATABASE_URL",
        "sdk_packages": "typeorm",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "sequelize": {
        "install_command": "npm install sequelize",
        "env_vars": "DATABASE_URL",
        "sdk_packages": "sequelize",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "mongoose": {
        "install_command": "npm install mongoose",
        "env_vars": "MONGODB_URI",
        "sdk_packages": "mongoose",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "kysely": {
        "install_command": "npm install kysely",
        "env_vars": "DATABASE_URL",
        "sdk_packages": "kysely",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── HTTP / API ──────────────────────────────────────────────
    "axios": {
        "install_command": "npm install axios",
        "env_vars": "",
        "sdk_packages": "axios",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "hono": {
        "install_command": "npm install hono",
        "env_vars": "",
        "sdk_packages": "hono",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "fastify": {
        "install_command": "npm install fastify",
        "env_vars": "",
        "sdk_packages": "fastify",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── Testing ─────────────────────────────────────────────────
    "vitest": {
        "install_command": "npm install -D vitest",
        "env_vars": "",
        "sdk_packages": "vitest",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "jest": {
        "install_command": "npm install -D jest",
        "env_vars": "",
        "sdk_packages": "jest",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "playwright": {
        "install_command": "npm install -D @playwright/test",
        "env_vars": "",
        "sdk_packages": "@playwright/test,playwright",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "cypress": {
        "install_command": "npm install -D cypress",
        "env_vars": "",
        "sdk_packages": "cypress",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── Build ───────────────────────────────────────────────────
    "vite": {
        "install_command": "npm install -D vite",
        "env_vars": "",
        "sdk_packages": "vite",
        "api_type": "CLI",
        "auth_method": "none",
    },
    "webpack": {
        "install_command": "npm install -D webpack webpack-cli",
        "env_vars": "",
        "sdk_packages": "webpack,webpack-cli",
        "api_type": "CLI",
        "auth_method": "none",
    },
    "esbuild": {
        "install_command": "npm install -D esbuild",
        "env_vars": "",
        "sdk_packages": "esbuild",
        "api_type": "CLI",
        "auth_method": "none",
    },
    "turbo": {
        "install_command": "npm install -D turbo",
        "env_vars": "",
        "sdk_packages": "turbo",
        "api_type": "CLI",
        "auth_method": "none",
    },
    # ── CSS / UI ────────────────────────────────────────────────
    "tailwind-css": {
        "install_command": "npm install -D tailwindcss @tailwindcss/vite",
        "env_vars": "",
        "sdk_packages": "tailwindcss",
        "api_type": "CLI",
        "auth_method": "none",
    },
    "daisyui": {
        "install_command": "npm install daisyui",
        "env_vars": "",
        "sdk_packages": "daisyui",
        "api_type": "CSS",
        "auth_method": "none",
    },
    "radix-ui": {
        "install_command": "npm install @radix-ui/themes",
        "env_vars": "",
        "sdk_packages": "@radix-ui/themes,@radix-ui/react-dialog",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "shadcn-ui": {
        "install_command": "npx shadcn@latest init",
        "env_vars": "",
        "sdk_packages": "@shadcn/ui",
        "api_type": "CLI",
        "auth_method": "none",
    },
    # ── State ───────────────────────────────────────────────────
    "zustand": {
        "install_command": "npm install zustand",
        "env_vars": "",
        "sdk_packages": "zustand",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "redux": {
        "install_command": "npm install @reduxjs/toolkit react-redux",
        "env_vars": "",
        "sdk_packages": "redux,@reduxjs/toolkit,react-redux",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "jotai": {
        "install_command": "npm install jotai",
        "env_vars": "",
        "sdk_packages": "jotai",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── Validation ──────────────────────────────────────────────
    "zod": {
        "install_command": "npm install zod",
        "env_vars": "",
        "sdk_packages": "zod",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── Email ───────────────────────────────────────────────────
    "nodemailer": {
        "install_command": "npm install nodemailer",
        "env_vars": "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS",
        "sdk_packages": "nodemailer",
        "api_type": "SDK",
        "auth_method": "SMTP",
    },
    # ── Date ────────────────────────────────────────────────────
    "date-fns": {
        "install_command": "npm install date-fns",
        "env_vars": "",
        "sdk_packages": "date-fns",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "dayjs": {
        "install_command": "npm install dayjs",
        "env_vars": "",
        "sdk_packages": "dayjs",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── Logging ─────────────────────────────────────────────────
    "pino": {
        "install_command": "npm install pino",
        "env_vars": "LOG_LEVEL",
        "sdk_packages": "pino,pino-pretty",
        "api_type": "SDK",
        "auth_method": "none",
    },
    "winston": {
        "install_command": "npm install winston",
        "env_vars": "LOG_LEVEL",
        "sdk_packages": "winston",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── Background Jobs ─────────────────────────────────────────
    "bullmq": {
        "install_command": "npm install bullmq",
        "env_vars": "REDIS_URL",
        "sdk_packages": "bullmq",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── Frameworks ──────────────────────────────────────────────
    "astro": {
        "install_command": "npm create astro@latest",
        "env_vars": "",
        "sdk_packages": "astro",
        "api_type": "CLI",
        "auth_method": "none",
    },
    "nuxt": {
        "install_command": "npx nuxi@latest init",
        "env_vars": "",
        "sdk_packages": "nuxt",
        "api_type": "CLI",
        "auth_method": "none",
    },
    "remix": {
        "install_command": "npx create-remix@latest",
        "env_vars": "",
        "sdk_packages": "@remix-run/node,@remix-run/react",
        "api_type": "SDK",
        "auth_method": "none",
    },
    # ── CMS ─────────────────────────────────────────────────────
    "payload": {
        "install_command": "npx create-payload-app@latest",
        "env_vars": "DATABASE_URI, PAYLOAD_SECRET",
        "sdk_packages": "payload",
        "api_type": "REST/GraphQL",
        "auth_method": "API key",
    },
    "strapi": {
        "install_command": "npx create-strapi-app@latest",
        "env_vars": "DATABASE_URL, APP_KEYS, API_TOKEN_SALT",
        "sdk_packages": "@strapi/strapi",
        "api_type": "REST/GraphQL",
        "auth_method": "API key/JWT",
    },
    # ── Search ──────────────────────────────────────────────────
    "meilisearch": {
        "install_command": "docker pull getmeili/meilisearch",
        "env_vars": "MEILI_URL, MEILI_MASTER_KEY",
        "sdk_packages": "meilisearch",
        "api_type": "REST",
        "auth_method": "API key",
    },
    "typesense": {
        "install_command": "docker pull typesense/typesense",
        "env_vars": "TYPESENSE_HOST, TYPESENSE_API_KEY",
        "sdk_packages": "typesense",
        "api_type": "REST",
        "auth_method": "API key",
    },
    # ── Self-hosted ─────────────────────────────────────────────
    "immich": {
        "install_command": "docker compose up -d",
        "env_vars": "DB_PASSWORD, UPLOAD_LOCATION",
        "sdk_packages": "",
        "api_type": "REST",
        "auth_method": "API key",
    },
    "vaultwarden": {
        "install_command": "docker pull vaultwarden/server",
        "env_vars": "ADMIN_TOKEN, DOMAIN",
        "sdk_packages": "",
        "api_type": "REST",
        "auth_method": "API key",
    },
    "n8n": {
        "install_command": "npx n8n",
        "env_vars": "N8N_BASIC_AUTH_USER, N8N_BASIC_AUTH_PASSWORD",
        "sdk_packages": "n8n",
        "api_type": "REST",
        "auth_method": "basic auth",
    },
}


def generate_sql():
    """Generate UPDATE statements for production DB."""
    statements = []
    for slug, data in ENRICHMENTS.items():
        sets = []
        for field, value in data.items():
            if value:  # Only set non-empty values
                safe_value = value.replace("'", "''")
                sets.append(f"{field} = '{safe_value}'")
        if sets:
            # Only update fields that are currently empty
            conditions = " OR ".join(
                f"({field} IS NULL OR {field} = '')"
                for field in data.keys() if data[field]
            )
            sql = f"UPDATE tools SET {', '.join(sets)} WHERE slug = '{slug}' AND ({conditions});"
            statements.append(sql)
    return statements


if __name__ == "__main__":
    import sys
    stmts = generate_sql()
    if "--dry-run" in sys.argv:
        print(f"Would update {len(stmts)} tools:")
        for s in stmts:
            print(f"  {s[:100]}...")
    else:
        for s in stmts:
            print(s)
        print(f"\n-- {len(stmts)} tools enriched")
