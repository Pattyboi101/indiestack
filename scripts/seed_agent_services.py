#!/usr/bin/env python3
"""Seed example agent services for the agent-to-agent registry.

Run locally to populate the agent_services table with demo entries.
Run on prod via: flyctl ssh console -a indiestack -C 'python3 /app/scripts/seed_agent_services.py'

These are placeholder services to populate the registry at launch.
Real agent makers will submit their own services via /agents/submit.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from indiestack.db import get_db, init_db

SEED_AGENTS = [
    {
        "name": "SEO Audit Agent",
        "tagline": "Automated technical SEO audit with actionable recommendations",
        "description": "Analyzes your site for SEO issues: broken links, missing meta tags, slow pages, mobile usability, and structured data problems. Returns a prioritized report with fixes.",
        "capability_tags": "seo,audit,marketing,technical-seo",
        "input_schema": '{"type":"object","properties":{"target_url":{"type":"string"},"competitors":{"type":"array","items":{"type":"string"}}},"required":["target_url"]}',
        "output_schema": '{"type":"object","properties":{"report":{"type":"string"},"issues":{"type":"array"},"score":{"type":"integer"}}}',
        "estimated_sla_minutes": 30,
        "cost_estimate_cents": 500,
        "cost_unit": "per_task",
        "source_type": "saas",
        "delivery_types": "inline_json,github_pr",
    },
    {
        "name": "QA Testing Agent",
        "tagline": "Automated end-to-end testing and bug detection for web apps",
        "description": "Runs comprehensive E2E tests against your deployed app. Tests critical user flows, checks for visual regressions, and validates API responses. Returns a test report with screenshots.",
        "capability_tags": "qa,testing,e2e,bug-detection,automation",
        "input_schema": '{"type":"object","properties":{"app_url":{"type":"string"},"test_flows":{"type":"array","items":{"type":"string"}}},"required":["app_url"]}',
        "output_schema": '{"type":"object","properties":{"passed":{"type":"integer"},"failed":{"type":"integer"},"report_url":{"type":"string"}}}',
        "estimated_sla_minutes": 45,
        "cost_estimate_cents": 300,
        "cost_unit": "per_task",
        "source_type": "saas",
        "delivery_types": "inline_json,s3_url",
    },
    {
        "name": "UI Design Agent",
        "tagline": "Generate production-ready UI components from descriptions",
        "description": "Takes a natural language description of a UI component or page and generates production-ready HTML/CSS/JS. Supports React, Vue, Svelte, and plain HTML. Returns a PR to your repo.",
        "capability_tags": "ui,design,frontend,components,react,vue",
        "input_schema": '{"type":"object","properties":{"description":{"type":"string"},"framework":{"type":"string","enum":["react","vue","svelte","html"]},"repo_url":{"type":"string"}},"required":["description"]}',
        "output_schema": '{"type":"object","properties":{"pr_url":{"type":"string"},"preview_url":{"type":"string"}}}',
        "estimated_sla_minutes": 60,
        "cost_estimate_cents": 800,
        "cost_unit": "per_task",
        "source_type": "saas",
        "delivery_types": "github_pr",
    },
    {
        "name": "Security Scanner Agent",
        "tagline": "Automated security audit for codebases and deployed apps",
        "description": "Scans your codebase for OWASP Top 10 vulnerabilities, dependency CVEs, exposed secrets, and insecure configurations. Returns a severity-rated report with remediation steps.",
        "capability_tags": "security,audit,vulnerability,owasp,scanning",
        "input_schema": '{"type":"object","properties":{"repo_url":{"type":"string"},"branch":{"type":"string","default":"main"}},"required":["repo_url"]}',
        "output_schema": '{"type":"object","properties":{"vulnerabilities":{"type":"array"},"severity_summary":{"type":"object"},"report":{"type":"string"}}}',
        "estimated_sla_minutes": 20,
        "cost_estimate_cents": 400,
        "cost_unit": "per_task",
        "source_type": "code",
        "delivery_types": "inline_json,github_pr",
    },
    {
        "name": "Data Engineering Agent",
        "tagline": "Build and optimize data pipelines, ETL jobs, and SQL schemas",
        "description": "Designs data pipelines, writes ETL scripts, optimizes SQL queries, and builds schema migrations. Works with PostgreSQL, SQLite, BigQuery, and common Python data tools.",
        "capability_tags": "data,etl,sql,pipeline,database,analytics",
        "input_schema": '{"type":"object","properties":{"task_description":{"type":"string"},"database_type":{"type":"string"},"schema_context":{"type":"string"}},"required":["task_description"]}',
        "output_schema": '{"type":"object","properties":{"sql":{"type":"string"},"migration":{"type":"string"},"notes":{"type":"string"}}}',
        "estimated_sla_minutes": 40,
        "cost_estimate_cents": 600,
        "cost_unit": "per_task",
        "source_type": "saas",
        "delivery_types": "inline_json,github_pr",
    },
    {
        "name": "Docs Writer Agent",
        "tagline": "Generate API docs, README files, and developer guides from code",
        "description": "Reads your codebase and generates comprehensive documentation: API references, getting started guides, architecture overviews, and inline code comments. Outputs as Markdown or MDX.",
        "capability_tags": "documentation,api-docs,readme,technical-writing",
        "input_schema": '{"type":"object","properties":{"repo_url":{"type":"string"},"doc_type":{"type":"string","enum":["api-reference","readme","getting-started","architecture"]}},"required":["repo_url"]}',
        "output_schema": '{"type":"object","properties":{"markdown":{"type":"string"},"pr_url":{"type":"string"}}}',
        "estimated_sla_minutes": 30,
        "cost_estimate_cents": 200,
        "cost_unit": "per_task",
        "source_type": "saas",
        "delivery_types": "inline_json,github_pr",
    },
    {
        "name": "Performance Profiler Agent",
        "tagline": "Profile and optimize slow code paths and database queries",
        "description": "Analyzes your application for performance bottlenecks: slow API endpoints, N+1 queries, memory leaks, and bundle size issues. Returns a profiling report with specific optimization suggestions.",
        "capability_tags": "performance,profiling,optimization,speed,monitoring",
        "input_schema": '{"type":"object","properties":{"app_url":{"type":"string"},"repo_url":{"type":"string"},"focus_area":{"type":"string"}},"required":["app_url"]}',
        "output_schema": '{"type":"object","properties":{"bottlenecks":{"type":"array"},"recommendations":{"type":"array"},"score":{"type":"integer"}}}',
        "estimated_sla_minutes": 25,
        "cost_estimate_cents": 350,
        "cost_unit": "per_task",
        "source_type": "saas",
        "delivery_types": "inline_json",
    },
]


async def seed():
    db = await get_db()
    await init_db()

    # Check if already seeded
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM agent_services")
    count = (await cursor.fetchone())['cnt']
    if count > 0:
        print(f"Agent services table already has {count} entries. Skipping seed.")
        return

    from indiestack.db import slugify

    for agent in SEED_AGENTS:
        slug = slugify(agent["name"])
        await db.execute(
            """INSERT OR IGNORE INTO agent_services
               (slug, name, tagline, description, capability_tags, input_schema,
                output_schema, delivery_types, estimated_sla_minutes,
                cost_estimate_cents, cost_unit, source_type, status, quality_score)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'approved',60)""",
            (slug, agent["name"], agent["tagline"], agent["description"],
             agent["capability_tags"], agent["input_schema"], agent["output_schema"],
             agent["delivery_types"], agent["estimated_sla_minutes"],
             agent["cost_estimate_cents"], agent["cost_unit"], agent["source_type"]),
        )
    await db.commit()
    print(f"Seeded {len(SEED_AGENTS)} agent services.")


if __name__ == "__main__":
    asyncio.run(seed())
