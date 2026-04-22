"""Database schema, migrations, seed data, and all query functions."""

import aiosqlite
import os
import hashlib
import secrets
import re
from typing import Optional
from datetime import datetime, timedelta, timezone
import time as _time

DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")
_UPVOTE_SALT = os.environ.get("INDIESTACK_UPVOTE_SALT", "indiestack-default-salt-change-me")

_SEARCH_STOP_WORDS = {"tool", "tools", "for", "best", "top", "the", "a", "an", "and", "or", "with", "in", "to"}

def normalize_search_query(query: str) -> str:
    """Normalize a search query for grouping: lowercase, strip punctuation, remove stop words."""
    q = query.lower().strip()
    q = re.sub(r'[^a-z0-9\s]', ' ', q)
    q = re.sub(r'\s+', ' ', q).strip()
    words = [w for w in q.split() if w not in _SEARCH_STOP_WORDS]
    return " ".join(words) if words else q

# ── Schema ────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS makers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    avatar_url TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    tagline TEXT NOT NULL DEFAULT '',
    description TEXT,
    maker_id INTEGER REFERENCES makers(id),
    capability_tags TEXT NOT NULL DEFAULT '',
    category_id INTEGER REFERENCES categories(id),
    input_schema TEXT NOT NULL DEFAULT '{}',
    output_schema TEXT NOT NULL DEFAULT '{}',
    delivery_types TEXT NOT NULL DEFAULT 'inline_json',
    estimated_sla_minutes INTEGER NOT NULL DEFAULT 5,
    cost_estimate_cents INTEGER,
    cost_unit TEXT DEFAULT 'per_task',
    execution_endpoint TEXT,
    auth_token_hash TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    timeout_rate REAL DEFAULT 0.0,
    success_count INTEGER DEFAULT 0,
    timeout_count INTEGER DEFAULT 0,
    quality_score INTEGER DEFAULT 50,
    url TEXT,
    github_url TEXT,
    source_type TEXT DEFAULT 'saas',
    example_input TEXT DEFAULT '{}',
    example_output TEXT DEFAULT '{}',
    useful_count INTEGER DEFAULT 0,
    not_useful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_agent_services_status ON agent_services(status);
CREATE INDEX IF NOT EXISTS idx_agent_services_capability ON agent_services(capability_tags);

CREATE TABLE IF NOT EXISTS agent_contracts (
    id TEXT PRIMARY KEY,
    host_user_id INTEGER REFERENCES users(id),
    host_session_id TEXT,
    host_api_key_id INTEGER REFERENCES api_keys(id),
    hired_agent_slug TEXT NOT NULL,
    input_payload TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    status_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_type TEXT,
    delivery_ref TEXT,
    delivery_metadata TEXT DEFAULT '{}',
    ttl_expires_at TIMESTAMP,
    sla_deadline_at TIMESTAMP,
    extended BOOLEAN DEFAULT 0,
    cost_estimate_cents INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    delivery_summary TEXT,
    outcome_useful INTEGER,
    outcome_notes TEXT,
    stripe_payment_intent_id TEXT,
    escrow_status TEXT
);
CREATE INDEX IF NOT EXISTS idx_agent_contracts_status ON agent_contracts(status);
CREATE INDEX IF NOT EXISTS idx_agent_contracts_host ON agent_contracts(host_user_id);
CREATE INDEX IF NOT EXISTS idx_agent_contracts_session ON agent_contracts(host_session_id);
CREATE INDEX IF NOT EXISTS idx_agent_contracts_agent ON agent_contracts(hired_agent_slug);

CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    tagline TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    maker_name TEXT NOT NULL DEFAULT '',
    maker_url TEXT NOT NULL DEFAULT '',
    category_id INTEGER NOT NULL REFERENCES categories(id),
    tags TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
    is_verified INTEGER NOT NULL DEFAULT 0,
    upvote_count INTEGER NOT NULL DEFAULT 0,
    price_pence INTEGER,
    delivery_type TEXT NOT NULL DEFAULT 'link' CHECK(delivery_type IN ('link','download','license_key')),
    delivery_url TEXT NOT NULL DEFAULT '',
    stripe_account_id TEXT NOT NULL DEFAULT '',
    verified_at TIMESTAMP,
    verified_until TIMESTAMP,
    maker_id INTEGER REFERENCES makers(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_instructions TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS upvotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    ip_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_id, ip_hash)
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    buyer_email TEXT NOT NULL,
    stripe_session_id TEXT NOT NULL DEFAULT '',
    amount_pence INTEGER NOT NULL,
    commission_pence INTEGER NOT NULL,
    purchase_token TEXT NOT NULL UNIQUE,
    delivered INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS featured_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    featured_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    headline TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cover_emoji TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL REFERENCES collections(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    position INTEGER NOT NULL DEFAULT 0,
    UNIQUE(collection_id, tool_id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'buyer' CHECK(role IN ('buyer','maker','admin')),
    maker_id INTEGER REFERENCES makers(id),
    email_verified INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    is_verified_purchase INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_id, user_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    stripe_subscription_id TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'pro',
    status TEXT NOT NULL DEFAULT 'active',
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tool_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    ip_hash TEXT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tool_id)
);

CREATE TABLE IF NOT EXISTS maker_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maker_id INTEGER NOT NULL REFERENCES makers(id),
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    update_type TEXT NOT NULL DEFAULT 'update'
        CHECK(update_type IN ('update','launch','milestone','changelog')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT NOT NULL DEFAULT '',
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category_id);
CREATE INDEX IF NOT EXISTS idx_tools_upvotes ON tools(upvote_count DESC);
CREATE INDEX IF NOT EXISTS idx_purchases_token ON purchases(purchase_token);
CREATE INDEX IF NOT EXISTS idx_purchases_tool ON purchases(tool_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_purchases_stripe_session ON purchases(stripe_session_id) WHERE stripe_session_id != '';
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_collection_tools_coll ON collection_tools(collection_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_tool ON reviews(tool_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_tool_views_tool ON tool_views(tool_id);
CREATE INDEX IF NOT EXISTS idx_wishlists_user ON wishlists(user_id);
CREATE INDEX IF NOT EXISTS idx_wishlists_tool ON wishlists(tool_id);
CREATE INDEX IF NOT EXISTS idx_maker_updates_maker ON maker_updates(maker_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_tools_maker_id ON tools(maker_id);
CREATE INDEX IF NOT EXISTS idx_makers_slug ON makers(slug);
CREATE INDEX IF NOT EXISTS idx_collections_slug ON collections(slug);
CREATE INDEX IF NOT EXISTS idx_stacks_slug ON stacks(slug);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS page_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    page TEXT NOT NULL,
    visitor_id TEXT,
    referrer TEXT
);
CREATE INDEX IF NOT EXISTS idx_page_views_timestamp ON page_views(timestamp);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS magic_link_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    unsubscribe_token TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_optouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cover_emoji TEXT NOT NULL DEFAULT '',
    discount_percent INTEGER NOT NULL DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stack_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id INTEGER NOT NULL REFERENCES stacks(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    position INTEGER NOT NULL DEFAULT 0,
    UNIQUE(stack_id, tool_id)
);

CREATE TABLE IF NOT EXISTS stack_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id INTEGER NOT NULL REFERENCES stacks(id),
    buyer_email TEXT NOT NULL,
    stripe_session_id TEXT NOT NULL DEFAULT '',
    total_amount_pence INTEGER NOT NULL,
    discount_pence INTEGER NOT NULL DEFAULT 0,
    purchase_token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stack_tools_stack ON stack_tools(stack_id);
CREATE INDEX IF NOT EXISTS idx_stack_purchases_token ON stack_purchases(purchase_token);
CREATE INDEX IF NOT EXISTS idx_tools_tags ON tools(tags);
CREATE INDEX IF NOT EXISTS idx_tools_verified ON tools(is_verified);
CREATE INDEX IF NOT EXISTS idx_tools_ejectable ON tools(is_ejectable);

CREATE TABLE IF NOT EXISTS claim_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_claim_tokens_token ON claim_tokens(token);

CREATE TABLE IF NOT EXISTS claim_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_claim_requests_status ON claim_requests(status);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL DEFAULT 'Default',
    tier TEXT NOT NULL DEFAULT 'free' CHECK(tier IN ('free','pro')),
    is_active INTEGER NOT NULL DEFAULT 1,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

CREATE TABLE IF NOT EXISTS api_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id INTEGER NOT NULL REFERENCES api_keys(id),
    endpoint TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_usage_key ON api_usage_logs(key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created ON api_usage_logs(created_at);

CREATE TABLE IF NOT EXISTS tool_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    user_id INTEGER REFERENCES users(id),
    session_id TEXT,
    reaction TEXT NOT NULL CHECK(reaction IN ('use_this','bookmark')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_id, user_id, reaction),
    UNIQUE(tool_id, session_id, reaction)
);
CREATE INDEX IF NOT EXISTS idx_reactions_tool ON tool_reactions(tool_id);

CREATE TABLE IF NOT EXISTS user_stacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL DEFAULT 'My Stack',
    description TEXT NOT NULL DEFAULT '',
    is_public INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS user_stack_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id INTEGER NOT NULL REFERENCES user_stacks(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    position INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    UNIQUE(stack_id, tool_id)
);
CREATE INDEX IF NOT EXISTS idx_user_stack_tools_stack ON user_stack_tools(stack_id);

CREATE TABLE IF NOT EXISTS search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'web',
    result_count INTEGER NOT NULL DEFAULT 0,
    top_result_slug TEXT,
    top_result_name TEXT,
    api_key_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_search_logs_created ON search_logs(created_at);

CREATE TABLE IF NOT EXISTS developer_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL UNIQUE REFERENCES api_keys(id),
    interests TEXT NOT NULL DEFAULT '{}',
    tech_stack TEXT NOT NULL DEFAULT '[]',
    favorite_tools TEXT NOT NULL DEFAULT '[]',
    search_count INTEGER NOT NULL DEFAULT 0,
    personalization_enabled INTEGER NOT NULL DEFAULT 1,
    notice_shown INTEGER NOT NULL DEFAULT 0,
    last_rebuilt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    tool_id INTEGER REFERENCES tools(id),
    milestone_type TEXT NOT NULL,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shared INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, tool_id, milestone_type)
);
CREATE INDEX IF NOT EXISTS idx_milestones_user ON milestones(user_id);

CREATE TABLE IF NOT EXISTS magic_claim_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_magic_claim_token ON magic_claim_tokens(token);

CREATE TABLE IF NOT EXISTS sponsored_placements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    competitor_slug TEXT NOT NULL,
    label TEXT DEFAULT 'Sponsored',
    started_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_sponsored_competitor ON sponsored_placements(competitor_slug, is_active);
CREATE TABLE IF NOT EXISTS outbound_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    url TEXT NOT NULL,
    ip_hash TEXT NOT NULL,
    referrer TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_outbound_clicks_tool ON outbound_clicks(tool_id, created_at);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    visitor_id TEXT,
    user_id INTEGER,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_event ON events(event);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE TABLE IF NOT EXISTS agent_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER REFERENCES api_keys(id),
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('recommend','shortlist','report_outcome','confirm_integration','submit_tool')),
    tool_slug TEXT NOT NULL,
    tool_b_slug TEXT,
    success INTEGER,
    notes TEXT,
    query_context TEXT,
    created_at TIMESTAMP DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_agent_actions_key ON agent_actions(api_key_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_user ON agent_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_tool ON agent_actions(tool_slug);
CREATE INDEX IF NOT EXISTS idx_agent_actions_action ON agent_actions(action);
CREATE INDEX IF NOT EXISTS idx_agent_actions_date ON agent_actions(created_at);

CREATE TABLE IF NOT EXISTS stack_roasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stack_name TEXT NOT NULL,
    stack_json TEXT NOT NULL,
    ai_roast_text TEXT,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS roast_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roast_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(roast_id) REFERENCES stack_roasts(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS roast_upvotes (
    user_id INTEGER NOT NULL,
    roast_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, roast_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(roast_id) REFERENCES stack_roasts(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_roast_comments_roast ON roast_comments(roast_id);
CREATE INDEX IF NOT EXISTS idx_stack_roasts_upvotes ON stack_roasts(upvotes DESC);

CREATE TABLE IF NOT EXISTS dependency_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    session_id TEXT,
    share_uuid TEXT UNIQUE,
    manifest_type TEXT NOT NULL CHECK(manifest_type IN ('package.json', 'requirements.txt')),
    package_count INTEGER NOT NULL,
    score_freshness INTEGER NOT NULL,
    score_cohesion INTEGER NOT NULL,
    score_modernity INTEGER NOT NULL,
    score_total INTEGER NOT NULL,
    results_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dep_analyses_session ON dependency_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_dep_analyses_user ON dependency_analyses(user_id);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS tools_fts USING fts5(
    name, tagline, description, tags,
    content='tools',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS tools_ai AFTER INSERT ON tools BEGIN
    INSERT INTO tools_fts(rowid, name, tagline, description, tags)
    VALUES (new.id, new.name, new.tagline, new.description, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS tools_ad AFTER DELETE ON tools BEGIN
    INSERT INTO tools_fts(tools_fts, rowid, name, tagline, description, tags)
    VALUES ('delete', old.id, old.name, old.tagline, old.description, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS tools_au AFTER UPDATE ON tools BEGIN
    INSERT INTO tools_fts(tools_fts, rowid, name, tagline, description, tags)
    VALUES ('delete', old.id, old.name, old.tagline, old.description, old.tags);
    INSERT INTO tools_fts(rowid, name, tagline, description, tags)
    VALUES (new.id, new.name, new.tagline, new.description, new.tags);
END;

CREATE VIRTUAL TABLE IF NOT EXISTS makers_fts USING fts5(
    name, bio,
    content='makers',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS makers_ai AFTER INSERT ON makers BEGIN
    INSERT INTO makers_fts(rowid, name, bio)
    VALUES (new.id, new.name, new.bio);
END;

CREATE TRIGGER IF NOT EXISTS makers_ad AFTER DELETE ON makers BEGIN
    INSERT INTO makers_fts(makers_fts, rowid, name, bio)
    VALUES ('delete', old.id, old.name, old.bio);
END;

CREATE TRIGGER IF NOT EXISTS makers_au AFTER UPDATE ON makers BEGIN
    INSERT INTO makers_fts(makers_fts, rowid, name, bio)
    VALUES ('delete', old.id, old.name, old.bio);
    INSERT INTO makers_fts(rowid, name, bio)
    VALUES (new.id, new.name, new.bio);
END;
"""

# ── Seed categories ───────────────────────────────────────────────────────

SEED_CATEGORIES = [
    ("Invoicing & Billing", "invoicing-billing", "Send invoices and get paid", "💰"),
    ("Email Marketing", "email-marketing", "Newsletters and email campaigns", "📧"),
    ("Analytics & Metrics", "analytics-metrics", "Track what matters", "📊"),
    ("Project Management", "project-management", "Organize tasks and projects", "📋"),
    ("Customer Support", "customer-support", "Help desks and live chat", "🎧"),
    ("Scheduling & Booking", "scheduling-booking", "Appointments and calendars", "📅"),
    ("Social Media", "social-media", "Scheduling and management", "📱"),
    ("Landing Pages", "landing-pages", "Build and ship pages fast", "🚀"),
    ("Forms & Surveys", "forms-surveys", "Collect data and feedback", "📝"),
    ("CRM & Sales", "crm-sales", "Manage leads and deals", "🤝"),
    ("File Management", "file-management", "Storage and sharing", "📁"),
    ("Authentication", "authentication", "Login, SSO, and user management", "🔐"),
    ("Payments", "payments", "Accept and process payments", "💳"),
    ("SEO Tools", "seo-tools", "Rank higher and get found", "🔍"),
    ("Monitoring & Uptime", "monitoring-uptime", "Stay online and get alerted", "🟢"),
    ("API Tools", "api-tools", "Build and manage APIs", "⚡"),
    ("Design & Creative", "design-creative", "Graphics, video, and branding", "🎨"),
    ("Developer Tools", "developer-tools", "Ship code faster", "🛠️"),
    ("AI & Automation", "ai-automation", "Smart workflows and bots", "🤖"),
    ("Feedback & Reviews", "feedback-reviews", "Collect and display testimonials", "⭐"),
    ("AI Dev Tools", "ai-dev-tools", "MCP servers, AI coding assistants, and dev agent tools", "🧠"),
    ("Games & Entertainment", "games-entertainment", "Indie games, game engines, and interactive experiences", "🎮"),
    ("Learning & Education", "learning-education", "Flashcards, courses, and educational tools", "📚"),
    ("Newsletters & Content", "newsletters-content", "Publishing platforms, newsletters, and content tools", "📰"),
    ("Creative Tools", "creative-tools", "Music, art, video, and creative software", "🎭"),
    ("Database", "database", "Databases, ORMs, and data storage tools", ""),
    ("Headless CMS", "headless-cms", "API-first content management systems", ""),
    ("Media Server", "media-server", "Streaming, transcoding, and media management", ""),
    ("DevOps & Infrastructure", "devops-infrastructure", "CI/CD, containers, and infrastructure tools", ""),
    ("Security Tools", "security-tools", "Security scanning, encryption, and compliance", ""),
    ("Search Engine", "search-engine", "Full-text search, vector search, and indexing", ""),
    ("Message Queue", "message-queue", "Message brokers, event streaming, and async communication", ""),
    ("Testing Tools", "testing-tools", "Test automation, mocking, and QA tools", ""),
    ("Documentation", "documentation", "API docs, wikis, and knowledge bases", ""),
    ("CLI Tools", "cli-tools", "Command-line utilities and terminal tools", ""),
    ("Logging", "logging", "Log aggregation, analysis, and management", ""),
    ("Feature Flags", "feature-flags", "Feature toggles, A/B testing, and gradual rollouts", ""),
    ("Notifications", "notifications", "Push notifications, in-app messaging, and alerts", ""),
    ("Background Jobs", "background-jobs", "Task queues, cron jobs, and workflow orchestration", ""),
    ("Localization", "localization", "Translation, i18n, and multilingual content", ""),
]

# ── Token cost estimates per category ────────────────────────────────────
CATEGORY_TOKEN_COSTS = {
    "invoicing-billing": 80_000,
    "email-marketing": 60_000,
    "analytics-metrics": 50_000,
    "project-management": 100_000,
    "customer-support": 70_000,
    "scheduling-booking": 45_000,
    "social-media": 55_000,
    "landing-pages": 30_000,
    "forms-surveys": 35_000,
    "crm-sales": 90_000,
    "file-management": 40_000,
    "authentication": 50_000,
    "payments": 60_000,
    "seo-tools": 40_000,
    "monitoring-uptime": 45_000,
    "api-tools": 55_000,
    "design-creative": 70_000,
    "developer-tools": 50_000,
    "ai-automation": 80_000,
    "feedback-reviews": 35_000,
    "ai-dev-tools": 120_000,
    "games-entertainment": 120_000,
    "learning-education": 80_000,
    "newsletters-content": 60_000,
    "creative-tools": 100_000,
    "database": 60_000,
    "headless-cms": 50_000,
    "media-server": 80_000,
    "devops-infrastructure": 70_000,
    "security-tools": 60_000,
    "search-engine": 50_000,
    "message-queue": 40_000,
    "testing-tools": 45_000,
    "documentation": 30_000,
    "cli-tools": 35_000,
    "logging": 40_000,
    "feature-flags": 30_000,
    "notifications": 35_000,
    "background-jobs": 40_000,
    "localization": 30_000,
    # v3 categories
    "frontend-frameworks": 80_000,
    "caching": 35_000,
    "mcp-servers": 50_000,
    "boilerplates": 30_000,
    "maps-location": 25_000,
}

# Maps common need keywords to category slugs, search terms, and competitors.
# Used by Stack Builder API and Use Case pages.
NEED_MAPPINGS = {
    "auth": {"category": "authentication", "terms": ["auth", "login", "SSO", "identity"], "competitors": ["Auth0", "Firebase Auth", "Okta", "Cognito"], "title": "Authentication", "description": "Add login, signup, SSO, and session management without building from scratch.", "build_estimate": "2-3 weeks", "icon": "\U0001f510"},
    "payments": {"category": "payments", "terms": ["payments", "billing", "checkout", "subscriptions"], "competitors": ["Stripe", "PayPal", "Square"], "title": "Payments", "description": "Accept payments, manage subscriptions, and handle checkouts.", "build_estimate": "3-4 weeks", "icon": "\U0001f4b3"},
    "analytics": {"category": "analytics-metrics", "terms": ["analytics", "metrics", "tracking", "dashboards"], "competitors": ["Google Analytics", "Mixpanel", "Amplitude"], "title": "Analytics & Metrics", "description": "Track user behavior, measure funnels, and build dashboards.", "build_estimate": "2-3 weeks", "icon": "\U0001f4ca"},
    "email": {"category": "email-marketing", "terms": ["email", "newsletter", "drip", "marketing"], "competitors": ["Mailchimp", "SendGrid", "ConvertKit"], "title": "Email Marketing", "description": "Send newsletters, drip campaigns, and transactional emails.", "build_estimate": "2-3 weeks", "icon": "\U0001f4e7"},
    "invoicing": {"category": "invoicing-billing", "terms": ["invoicing", "billing", "receipts", "accounting"], "competitors": ["FreshBooks", "QuickBooks", "Xero"], "title": "Invoicing & Billing", "description": "Generate invoices, track payments, and manage billing workflows.", "build_estimate": "3-4 weeks", "icon": "\U0001f9fe"},
    "monitoring": {"category": "monitoring-uptime", "terms": ["monitoring", "uptime", "alerting", "observability"], "competitors": ["Datadog", "PagerDuty", "Pingdom"], "title": "Monitoring & Uptime", "description": "Monitor uptime, get alerts, and track application health.", "build_estimate": "2-3 weeks", "icon": "\U0001f6a8"},
    "forms": {"category": "forms-surveys", "terms": ["forms", "surveys", "feedback", "questionnaires"], "competitors": ["Typeform", "Google Forms", "SurveyMonkey"], "title": "Forms & Surveys", "description": "Build forms, collect responses, and run surveys.", "build_estimate": "1-2 weeks", "icon": "\U0001f4cb"},
    "scheduling": {"category": "scheduling-booking", "terms": ["scheduling", "booking", "calendar", "appointments"], "competitors": ["Calendly", "Acuity", "Cal.com"], "title": "Scheduling & Booking", "description": "Let users book meetings, schedule appointments, and manage availability.", "build_estimate": "2-3 weeks", "icon": "\U0001f4c5"},
    "cms": {"category": "headless-cms", "terms": ["cms", "content", "blog", "headless"], "competitors": ["WordPress", "Contentful", "Sanity"], "title": "CMS & Content", "description": "Manage content, run blogs, and build headless CMS backends.", "build_estimate": "3-5 weeks", "icon": "\U0001f4dd"},
    "support": {"category": "customer-support", "terms": ["support", "helpdesk", "chat", "ticketing"], "competitors": ["Zendesk", "Intercom", "Freshdesk"], "title": "Customer Support", "description": "Add helpdesks, live chat, and ticketing systems.", "build_estimate": "3-4 weeks", "icon": "\U0001f3a7"},
    "seo": {"category": "seo-tools", "terms": ["seo", "search", "ranking", "keywords"], "competitors": ["Ahrefs", "SEMrush", "Moz"], "title": "SEO Tools", "description": "Track rankings, audit sites, and optimize for search engines.", "build_estimate": "2-3 weeks", "icon": "\U0001f50d"},
    "storage": {"category": "file-management", "terms": ["storage", "files", "upload", "media"], "competitors": ["AWS S3", "Dropbox", "Cloudinary"], "title": "File Storage", "description": "Upload files, manage media assets, and serve content.", "build_estimate": "1-2 weeks", "icon": "\U0001f4c1"},
    "crm": {"category": "crm-sales", "terms": ["crm", "sales", "leads", "pipeline"], "competitors": ["Salesforce", "HubSpot", "Pipedrive"], "title": "CRM & Sales", "description": "Manage contacts, track deals, and automate sales pipelines.", "build_estimate": "4-6 weeks", "icon": "\U0001f91d"},
    "devtools": {"category": "developer-tools", "terms": ["developer", "tools", "sdk", "api"], "competitors": ["Postman", "Ngrok"], "title": "Developer Tools", "description": "Debug, test, and ship faster with indie developer tools.", "build_estimate": "varies", "icon": "\U0001f6e0\ufe0f"},
    "ai": {"category": "ai-automation", "terms": ["ai", "automation", "ml", "llm"], "competitors": ["OpenAI", "AWS AI", "Google AI"], "title": "AI & Automation", "description": "Add AI features, automate workflows, and integrate LLMs.", "build_estimate": "3-5 weeks", "icon": "\U0001f916"},
    "design": {"category": "design-creative", "terms": ["design", "ui", "creative", "graphics"], "competitors": ["Figma", "Canva", "Adobe"], "title": "Design & Creative", "description": "Create designs, generate graphics, and build UI components.", "build_estimate": "varies", "icon": "\U0001f3a8"},
    "feedback": {"category": "feedback-reviews", "terms": ["feedback", "reviews", "nps", "ratings"], "competitors": ["Hotjar", "UserTesting", "Typeform"], "title": "Feedback & Reviews", "description": "Collect user feedback, run NPS surveys, and manage reviews.", "build_estimate": "1-2 weeks", "icon": "\U0001f4ac"},
    "social": {"category": "social-media", "terms": ["social", "community", "social media"], "competitors": ["Buffer", "Hootsuite"], "title": "Social Media", "description": "Schedule posts, manage social accounts, and grow communities.", "build_estimate": "2-3 weeks", "icon": "\U0001f4f1"},
    "project": {"category": "project-management", "terms": ["project management", "kanban", "tasks", "todo", "scrum", "sprint", "agile"], "competitors": ["Jira", "Asana", "Monday.com", "Trello", "Linear"], "title": "Project Management", "description": "Organize tasks, run sprints, and manage projects without enterprise bloat.", "build_estimate": "4-6 weeks", "icon": "\U0001f4cb"},
    "landing": {"category": "landing-pages", "terms": ["landing page", "website builder", "static site", "portfolio", "one-page"], "competitors": ["Webflow", "Squarespace", "Wix", "Carrd"], "title": "Landing Pages", "description": "Build and ship landing pages, portfolios, and static sites.", "build_estimate": "1-2 weeks", "icon": "\U0001f680"},
    "api": {"category": "api-tools", "terms": ["api gateway", "rest client", "webhook", "endpoint", "openapi", "rate limiting", "rate limiter", "realtime", "real-time", "websocket"], "competitors": ["Postman", "Swagger", "Kong", "Insomnia"], "title": "API Tools", "description": "Build, test, and manage APIs with indie developer tools.", "build_estimate": "2-4 weeks", "icon": "\u26a1"},
    "aidev": {"category": "ai-dev-tools", "terms": ["mcp server", "ai coding", "agent", "copilot", "code assistant", "llm tool"], "competitors": ["GitHub Copilot", "Cursor", "Windsurf", "Cody"], "title": "AI Dev Tools", "description": "MCP servers, AI coding assistants, and agent tools built by indie creators.", "build_estimate": "varies", "icon": "\U0001f9e0"},
    "games": {"category": "games-entertainment", "terms": ["game engine", "indie game", "gaming", "interactive", "game dev"], "competitors": ["Unity", "Unreal Engine", "GameMaker", "Godot"], "title": "Games & Entertainment", "description": "Game engines, indie games, and interactive experiences from independent creators.", "build_estimate": "varies", "icon": "\U0001f3ae"},
    "learning": {"category": "learning-education", "terms": ["learning", "education", "flashcards", "course", "quiz", "tutorial"], "competitors": ["Coursera", "Udemy", "Anki", "Duolingo"], "title": "Learning & Education", "description": "Flashcard apps, course platforms, and educational tools.", "build_estimate": "3-5 weeks", "icon": "\U0001f4da"},
    "publishing": {"category": "newsletters-content", "terms": ["publishing platform", "blog platform", "newsletter platform", "writer tool", "substack alternative"], "competitors": ["Substack", "Ghost", "Medium", "Hashnode"], "title": "Publishing & Newsletters", "description": "Run newsletters, publish blogs, and build writing platforms.", "build_estimate": "3-4 weeks", "icon": "\U0001f4f0"},
    "creative": {"category": "creative-tools", "terms": ["music production", "video editor", "audio tool", "3d modeling", "pixel art", "creative software"], "competitors": ["Adobe Creative Suite", "DaVinci Resolve", "Blender", "Logic Pro"], "title": "Creative Tools", "description": "Music, video, art, and creative software from indie makers.", "build_estimate": "varies", "icon": "\U0001f3ad"},
    "database": {"category": "database", "terms": ["database", "orm", "sql", "nosql", "postgres", "mysql", "sqlite", "migration", "vector database", "vector db", "vector store"], "competitors": ["PlanetScale", "Supabase", "MongoDB Atlas", "Neon"], "title": "Databases", "description": "Indie databases, ORMs, and data storage tools for your app.", "build_estimate": "1-2 weeks", "icon": "\U0001f5c4\ufe0f"},
    "background": {"category": "background-jobs", "terms": ["cron job", "task queue", "background job", "job scheduler", "workflow", "queue worker"], "competitors": ["Celery", "Bull", "Sidekiq", "AWS SQS"], "title": "Background Jobs", "description": "Schedule cron jobs, run task queues, and orchestrate workflows.", "build_estimate": "1-2 weeks", "icon": "\u2699\ufe0f"},
    "hosting": {"category": "devops-infrastructure", "terms": ["hosting", "deployment", "vps", "cloud", "infrastructure", "paas", "containers", "docker"], "competitors": ["AWS", "Heroku", "Vercel", "Railway", "Render"], "title": "Hosting & Infrastructure", "description": "Deploy apps, manage servers, and scale infrastructure without enterprise overhead.", "build_estimate": "1-2 weeks", "icon": "\U0001f30d"},
    "frontend": {"category": "frontend-frameworks", "terms": ["react", "vue", "svelte", "angular", "nextjs", "nuxt", "astro", "remix", "frontend framework", "javascript framework", "ui framework", "bundler", "build tool", "state management"], "competitors": ["React", "Vue", "Angular", "Svelte", "Next.js", "Vite", "Webpack"], "title": "Frontend Frameworks", "description": "JavaScript frameworks, UI libraries, bundlers, and state management tools for building modern web apps.", "build_estimate": "varies", "icon": "\U0001f5a5\ufe0f"},
    "caching": {"category": "caching", "terms": ["cache", "caching", "redis", "memcached", "in-memory", "key-value store", "edge cache", "cdn cache"], "competitors": ["Redis", "Memcached", "Upstash", "Cloudflare"], "title": "Caching & In-Memory", "description": "In-memory stores, caching layers, and key-value databases for high-performance apps.", "build_estimate": "1 week", "icon": "\u26a1"},
    "mcp": {"category": "mcp-servers", "terms": ["mcp server", "model context protocol", "mcp tool", "claude tool", "claude integration", "agent tool", "agent integration"], "competitors": ["Zapier MCP", "Make MCP", "Custom MCP servers"], "title": "MCP Servers", "description": "MCP server implementations that give AI agents access to tools, data, and services.", "build_estimate": "varies", "icon": "\U0001f9e9"},
    "boilerplate": {"category": "boilerplates", "terms": ["boilerplate", "starter kit", "starter template", "scaffold", "nextjs boilerplate", "saas starter", "app template"], "competitors": ["create-next-app", "T3 Stack", "create-t3-app", "Vercel templates"], "title": "Boilerplates & Starters", "description": "Starter kits, scaffold templates, and opinionated project starters to ship faster.", "build_estimate": "ready to use", "icon": "\U0001f4e6"},
    "featureflags": {"category": "feature-flags", "terms": ["feature flag", "feature toggle", "a/b test", "ab test", "experiment", "gradual rollout", "canary release"], "competitors": ["LaunchDarkly", "Split.io", "Unleash", "Flagsmith"], "title": "Feature Flags", "description": "Ship features safely with toggles, A/B tests, and gradual rollouts.", "build_estimate": "1-2 weeks", "icon": "\U0001f6a9"},
    "logging": {"category": "logging", "terms": ["logging", "log management", "log aggregation", "structured logs", "log drain", "log analysis", "audit log"], "competitors": ["Datadog Logs", "Logtail", "Papertrail", "Grafana Loki"], "title": "Logging", "description": "Aggregate, search, and analyse logs from your applications and infrastructure.", "build_estimate": "1 week", "icon": "\U0001f4dc"},
    "notifications": {"category": "notifications", "terms": ["push notification", "in-app notification", "notification service", "sms notification", "mobile push", "alert", "broadcast"], "competitors": ["OneSignal", "Firebase FCM", "Novu", "Knock", "Pusher Beams"], "title": "Notifications", "description": "Send push notifications, in-app messages, and SMS alerts to your users.", "build_estimate": "1-2 weeks", "icon": "\U0001f514"},
    "localization": {"category": "localization", "terms": ["i18n", "l10n", "localization", "internationalization", "translation", "locale", "multilingual"], "competitors": ["Crowdin", "Lokalise", "Phrase", "Transifex"], "title": "Localization", "description": "Translate your app and manage multilingual content with indie-friendly i18n tools.", "build_estimate": "1-2 weeks", "icon": "\U0001f310"},
    "cli": {"category": "cli-tools", "terms": ["cli", "command-line", "terminal tool", "shell script", "tui", "command line interface"], "competitors": ["Homebrew", "Oh My Zsh", "Fig"], "title": "CLI Tools", "description": "Command-line utilities, terminal apps, and TUI tools for developer workflows.", "build_estimate": "1-2 weeks", "icon": "\U0001f4bb"},
    "docs": {"category": "documentation", "terms": ["documentation", "api docs", "docs site", "wiki", "knowledge base", "readme"], "competitors": ["Docusaurus", "GitBook", "Mintlify", "ReadMe"], "title": "Documentation", "description": "Build docs sites, API references, wikis, and knowledge bases.", "build_estimate": "1-2 weeks", "icon": "\U0001f4da"},
    "testing": {"category": "testing-tools", "terms": ["testing", "unit test", "e2e test", "test automation", "mocking", "QA", "test runner", "code coverage"], "competitors": ["Jest", "Playwright", "Cypress", "Vitest", "pytest"], "title": "Testing Tools", "description": "Automate tests, mock dependencies, and ship with confidence.", "build_estimate": "1-2 weeks", "icon": "\U0001f9ea"},
    "security": {"category": "security-tools", "terms": ["security", "vulnerability scanning", "pentest", "compliance", "encryption", "secrets management", "SAST", "DAST"], "competitors": ["Snyk", "OWASP ZAP", "HashiCorp Vault", "SonarQube"], "title": "Security Tools", "description": "Scan for vulnerabilities, manage secrets, and enforce compliance.", "build_estimate": "2-3 weeks", "icon": "\U0001f6e1\ufe0f"},
    "search": {"category": "search-engine", "terms": ["full-text search", "vector search", "search index", "search API", "semantic search", "fuzzy search", "typo-tolerant"], "competitors": ["Algolia", "Elasticsearch", "Typesense", "Meilisearch"], "title": "Search Engines", "description": "Add fast, typo-tolerant full-text and semantic search to your app.", "build_estimate": "1-2 weeks", "icon": "\U0001f50d"},
    "queue": {"category": "message-queue", "terms": ["message queue", "message broker", "event streaming", "pubsub", "pub/sub", "kafka", "rabbitmq", "async messaging"], "competitors": ["Apache Kafka", "RabbitMQ", "AWS SQS", "NATS", "Redis Streams"], "title": "Message Queues", "description": "Decouple services with message brokers, event streaming, and pub/sub.", "build_estimate": "1-2 weeks", "icon": "\U0001f4ec"},
    "media": {"category": "media-server", "terms": ["video streaming", "transcoding", "media server", "audio streaming", "HLS", "video encoding", "adaptive bitrate"], "competitors": ["Mux", "Cloudinary Video", "Plex", "Jellyfin", "Bunny Stream"], "title": "Media Servers", "description": "Stream, transcode, and manage video and audio content.", "build_estimate": "2-4 weeks", "icon": "\U0001f3ac"},
    "maps": {"category": "maps-location", "terms": ["maps", "geolocation", "geocoding", "mapping", "location api", "map tiles", "leaflet", "mapbox"], "competitors": ["Google Maps", "Mapbox", "HERE Maps", "OpenLayers"], "title": "Maps & Location", "description": "Add maps, geolocation, geocoding, and location-based features to your app.", "build_estimate": "1-2 weeks", "icon": "\U0001f5fa\ufe0f"},
}

TECH_KEYWORDS = {
    "react", "nextjs", "next.js", "vue", "nuxt", "svelte", "sveltekit", "angular",
    "django", "flask", "fastapi", "rails", "laravel", "express", "nestjs",
    "supabase", "firebase", "postgres", "postgresql", "mongodb", "mysql", "redis",
    "tailwind", "bootstrap", "chakra",
    "vercel", "netlify", "cloudflare", "aws", "gcp", "azure", "fly.io",
    "docker", "kubernetes",
    "stripe", "paddle", "lemon squeezy",
    "typescript", "python", "go", "rust", "ruby", "php", "java",
    "graphql", "rest", "trpc",
    "prisma", "drizzle", "sqlalchemy",
    "playwright", "cypress", "jest", "vitest",
    "openai", "anthropic", "claude", "gpt",
    # AI/Agent
    "cursor", "windsurf", "cody", "copilot", "mcp", "langchain", "llamaindex", "crewai",
    # Modern runtimes & frameworks
    "deno", "bun", "htmx", "alpine.js", "astro", "remix", "solid", "qwik", "hono",
    # Modern databases
    "turso", "libsql", "neon", "planetscale", "pocketbase", "surrealdb", "convex",
    # UI & deployment
    "shadcn", "radix", "coolify", "railway", "render", "kamal",
    # Fundamentals
    "sqlite", "nginx", "caddy",
}

# ── Database init ─────────────────────────────────────────────────────────

def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = _dict_factory
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    await db.execute("PRAGMA busy_timeout=5000")
    await db.execute("PRAGMA synchronous=NORMAL")
    await db.execute("PRAGMA cache_size=-8000")
    await db.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
    await db.execute("PRAGMA temp_store=MEMORY")     # temp tables in RAM
    return db


async def _enrich_tool_metadata(db):
    """One-time enrichment of structured metadata for well-known tools.
    Only sets values where the field is currently empty — won't overwrite manual edits."""

    ENRICHMENTS = [
        # Authentication
        {"slug": "hanko", "api_type": "REST", "auth_method": "none", "install_command": "npm install @hanko/elements", "sdk_packages": '{"npm": "@hanko/elements", "pip": "hanko-python"}', "env_vars": '["HANKO_API_URL"]', "frameworks_tested": "nextjs,react,vue,svelte"},
        {"slug": "lucia", "api_type": "SDK", "auth_method": "none", "install_command": "npm install lucia", "sdk_packages": '{"npm": "lucia"}', "env_vars": '[]', "frameworks_tested": "nextjs,sveltekit,astro,nuxt"},
        {"slug": "supertokens", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install supertokens-auth-react", "sdk_packages": '{"npm": "supertokens-auth-react", "pip": "supertokens-python"}', "env_vars": '["SUPERTOKENS_CONNECTION_URI", "SUPERTOKENS_API_KEY"]', "frameworks_tested": "nextjs,react,fastapi,flask,django"},
        {"slug": "logto", "api_type": "REST", "auth_method": "oauth2", "install_command": "npm install @logto/next", "sdk_packages": '{"npm": "@logto/next"}', "env_vars": '["LOGTO_ENDPOINT", "LOGTO_APP_ID", "LOGTO_APP_SECRET"]', "frameworks_tested": "nextjs,react,vue,express"},
        {"slug": "ory", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install @ory/client", "sdk_packages": '{"npm": "@ory/client", "pip": "ory-client"}', "env_vars": '["ORY_SDK_URL", "ORY_API_KEY"]', "frameworks_tested": "nextjs,react,express,fastapi"},
        {"slug": "zitadel", "api_type": "REST", "auth_method": "oauth2", "install_command": "npm install @zitadel/node", "sdk_packages": '{"npm": "@zitadel/node"}', "env_vars": '["ZITADEL_DOMAIN", "ZITADEL_CLIENT_ID"]', "frameworks_tested": "nextjs,react,angular"},
        {"slug": "keycloak", "api_type": "REST", "auth_method": "oauth2", "install_command": "docker pull quay.io/keycloak/keycloak", "sdk_packages": '{"npm": "keycloak-js"}', "env_vars": '["KEYCLOAK_URL", "KEYCLOAK_REALM", "KEYCLOAK_CLIENT_ID"]', "frameworks_tested": "nextjs,react,angular,spring"},

        # Analytics
        {"slug": "simple-analytics", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install simple-analytics-script", "sdk_packages": '{"npm": "simple-analytics-script"}', "env_vars": '["SA_API_KEY"]', "frameworks_tested": "nextjs,react,vue,svelte,astro"},
        {"slug": "plausible-analytics", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install plausible-tracker", "sdk_packages": '{"npm": "plausible-tracker"}', "env_vars": '["PLAUSIBLE_API_KEY", "PLAUSIBLE_DOMAIN"]', "frameworks_tested": "nextjs,react,vue,gatsby"},
        {"slug": "umami", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install @umami/node", "sdk_packages": '{"npm": "@umami/node"}', "env_vars": '["UMAMI_API_KEY", "UMAMI_URL"]', "frameworks_tested": "nextjs,react,vue"},
        {"slug": "countly", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install countly-sdk-web", "sdk_packages": '{"npm": "countly-sdk-web"}', "env_vars": '["COUNTLY_APP_KEY", "COUNTLY_URL"]', "frameworks_tested": "react,vue,angular"},
        {"slug": "matomo", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install matomo-tracker", "sdk_packages": '{"npm": "matomo-tracker"}', "env_vars": '["MATOMO_URL", "MATOMO_SITE_ID"]', "frameworks_tested": "react,vue,nextjs"},
        {"slug": "posthog", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install posthog-js", "sdk_packages": '{"npm": "posthog-js", "pip": "posthog"}', "env_vars": '["POSTHOG_API_KEY", "POSTHOG_HOST"]', "frameworks_tested": "nextjs,react,vue,django,flask"},
        {"slug": "aptabase", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @aptabase/web", "sdk_packages": '{"npm": "@aptabase/web"}', "env_vars": '["APTABASE_APP_KEY"]', "frameworks_tested": "react,vue,svelte,tauri,electron"},

        # Payments
        {"slug": "polar", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install @polar-sh/sdk", "sdk_packages": '{"npm": "@polar-sh/sdk", "pip": "polar-python"}', "env_vars": '["POLAR_ACCESS_TOKEN"]', "frameworks_tested": "nextjs,fastapi"},
        {"slug": "lemon-squeezy", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @lemonsqueezy/lemonsqueezy.js", "sdk_packages": '{"npm": "@lemonsqueezy/lemonsqueezy.js"}', "env_vars": '["LEMONSQUEEZY_API_KEY"]', "frameworks_tested": "nextjs,react,vue"},
        {"slug": "lago", "api_type": "REST", "auth_method": "bearer", "install_command": "pip install lago-python-client", "sdk_packages": '{"pip": "lago-python-client", "npm": "lago-javascript-client"}', "env_vars": '["LAGO_API_KEY", "LAGO_URL"]', "frameworks_tested": "fastapi,rails"},
        {"slug": "kill-bill", "api_type": "REST", "auth_method": "api_key", "install_command": "pip install killbill", "sdk_packages": '{"pip": "killbill"}', "env_vars": '["KILLBILL_API_KEY", "KILLBILL_URL"]', "frameworks_tested": "django,rails,spring"},

        # Email
        {"slug": "listmonk", "api_type": "REST", "auth_method": "api_key", "install_command": "docker pull listmonk/listmonk", "sdk_packages": '{}', "env_vars": '["LISTMONK_HOST", "LISTMONK_USER", "LISTMONK_PASSWORD"]', "frameworks_tested": ""},
        {"slug": "resend", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install resend", "sdk_packages": '{"npm": "resend", "pip": "resend"}', "env_vars": '["RESEND_API_KEY"]', "frameworks_tested": "nextjs,react,fastapi,express"},
        {"slug": "plunk", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @plunk/node", "sdk_packages": '{"npm": "@plunk/node"}', "env_vars": '["PLUNK_API_KEY"]', "frameworks_tested": "nextjs,express"},
        {"slug": "mailpit", "api_type": "REST", "auth_method": "none", "install_command": "docker pull axllent/mailpit", "sdk_packages": '{}', "env_vars": '["MAILPIT_HOST"]', "frameworks_tested": ""},

        # CMS
        {"slug": "ghost", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @tryghost/content-api", "sdk_packages": '{"npm": "@tryghost/content-api"}', "env_vars": '["GHOST_API_KEY", "GHOST_URL"]', "frameworks_tested": "nextjs,gatsby,react"},
        {"slug": "strapi", "api_type": "REST", "auth_method": "bearer", "install_command": "npx create-strapi-app@latest", "sdk_packages": '{"npm": "@strapi/strapi"}', "env_vars": '["STRAPI_URL", "STRAPI_TOKEN"]', "frameworks_tested": "nextjs,react,vue,nuxt"},
        {"slug": "directus", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install @directus/sdk", "sdk_packages": '{"npm": "@directus/sdk"}', "env_vars": '["DIRECTUS_URL", "DIRECTUS_TOKEN"]', "frameworks_tested": "nextjs,react,vue,nuxt"},
        {"slug": "payload", "api_type": "REST", "auth_method": "bearer", "install_command": "npx create-payload-app@latest", "sdk_packages": '{"npm": "payload"}', "env_vars": '["PAYLOAD_SECRET", "DATABASE_URI"]', "frameworks_tested": "nextjs,react"},
        {"slug": "tina", "api_type": "GraphQL", "auth_method": "bearer", "install_command": "npx @tinacms/cli@latest init", "sdk_packages": '{"npm": "tinacms"}', "env_vars": '["TINA_CLIENT_ID", "TINA_TOKEN"]', "frameworks_tested": "nextjs,astro"},

        # Database / Backend
        {"slug": "pocketbase", "api_type": "REST", "auth_method": "bearer", "install_command": "go install github.com/pocketbase/pocketbase", "sdk_packages": '{"npm": "pocketbase"}', "env_vars": '["PB_URL"]', "frameworks_tested": "nextjs,react,svelte,vue"},
        {"slug": "supabase", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @supabase/supabase-js", "sdk_packages": '{"npm": "@supabase/supabase-js", "pip": "supabase"}', "env_vars": '["SUPABASE_URL", "SUPABASE_ANON_KEY"]', "frameworks_tested": "nextjs,react,vue,svelte,flutter"},
        {"slug": "appwrite", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install appwrite", "sdk_packages": '{"npm": "appwrite", "pip": "appwrite"}', "env_vars": '["APPWRITE_ENDPOINT", "APPWRITE_PROJECT_ID", "APPWRITE_API_KEY"]', "frameworks_tested": "nextjs,react,vue,flutter"},
        {"slug": "turso", "api_type": "SDK", "auth_method": "bearer", "install_command": "npm install @libsql/client", "sdk_packages": '{"npm": "@libsql/client", "pip": "libsql-experimental"}', "env_vars": '["TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"]', "frameworks_tested": "nextjs,fastapi,rails,django"},
        {"slug": "neon", "api_type": "SDK", "auth_method": "bearer", "install_command": "npm install @neondatabase/serverless", "sdk_packages": '{"npm": "@neondatabase/serverless"}', "env_vars": '["DATABASE_URL"]', "frameworks_tested": "nextjs,remix,astro"},
        {"slug": "convex", "api_type": "SDK", "auth_method": "bearer", "install_command": "npm install convex", "sdk_packages": '{"npm": "convex"}', "env_vars": '["CONVEX_URL"]', "frameworks_tested": "nextjs,react"},

        # Monitoring / Uptime
        {"slug": "uptime-kuma", "api_type": "REST", "auth_method": "api_key", "install_command": "docker pull louislam/uptime-kuma", "sdk_packages": '{}', "env_vars": '["UPTIME_KUMA_URL"]', "frameworks_tested": ""},
        {"slug": "sentry", "api_type": "SDK", "auth_method": "api_key", "install_command": "npm install @sentry/node", "sdk_packages": '{"npm": "@sentry/node", "pip": "sentry-sdk"}', "env_vars": '["SENTRY_DSN"]', "frameworks_tested": "nextjs,react,vue,django,flask,fastapi,express"},
        {"slug": "highlight-io", "api_type": "SDK", "auth_method": "api_key", "install_command": "npm install @highlight-run/node", "sdk_packages": '{"npm": "@highlight-run/node", "pip": "highlight-io"}', "env_vars": '["HIGHLIGHT_PROJECT_ID"]', "frameworks_tested": "nextjs,react,django,flask"},
        {"slug": "glitchtip", "api_type": "REST", "auth_method": "api_key", "install_command": "pip install sentry-sdk", "sdk_packages": '{"pip": "sentry-sdk"}', "env_vars": '["GLITCHTIP_DSN"]', "frameworks_tested": "django,flask,fastapi"},

        # Forms / Surveys
        {"slug": "formbricks", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @formbricks/js", "sdk_packages": '{"npm": "@formbricks/js"}', "env_vars": '["FORMBRICKS_API_HOST", "FORMBRICKS_ENVIRONMENT_ID"]', "frameworks_tested": "nextjs,react"},
        {"slug": "heyform", "api_type": "REST", "auth_method": "bearer", "install_command": "docker pull heyform/community", "sdk_packages": '{}', "env_vars": '["HEYFORM_URL"]', "frameworks_tested": ""},

        # Search
        {"slug": "meilisearch", "api_type": "REST", "auth_method": "api_key", "install_command": "docker pull getmeili/meilisearch", "sdk_packages": '{"npm": "meilisearch", "pip": "meilisearch"}', "env_vars": '["MEILI_HOST", "MEILI_MASTER_KEY"]', "frameworks_tested": "nextjs,react,vue,rails,django"},
        {"slug": "typesense", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install typesense", "sdk_packages": '{"npm": "typesense", "pip": "typesense"}', "env_vars": '["TYPESENSE_HOST", "TYPESENSE_API_KEY"]', "frameworks_tested": "nextjs,react,vue,rails"},

        # Feature Flags / Config
        {"slug": "flagsmith", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install flagsmith", "sdk_packages": '{"npm": "flagsmith", "pip": "flagsmith"}', "env_vars": '["FLAGSMITH_ENVIRONMENT_KEY"]', "frameworks_tested": "nextjs,react,django,flask"},
        {"slug": "growthbook", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @growthbook/growthbook-react", "sdk_packages": '{"npm": "@growthbook/growthbook-react"}', "env_vars": '["GROWTHBOOK_API_HOST", "GROWTHBOOK_CLIENT_KEY"]', "frameworks_tested": "nextjs,react"},
        {"slug": "unleash", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install unleash-client", "sdk_packages": '{"npm": "unleash-client", "pip": "UnleashClient"}', "env_vars": '["UNLEASH_URL", "UNLEASH_API_TOKEN"]', "frameworks_tested": "nextjs,express,django,fastapi"},

        # Scheduling
        {"slug": "cal-com", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @calcom/embed-react", "sdk_packages": '{"npm": "@calcom/embed-react"}', "env_vars": '["CAL_API_KEY"]', "frameworks_tested": "nextjs,react"},

        # Notifications
        {"slug": "novu", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @novu/node", "sdk_packages": '{"npm": "@novu/node", "pip": "novu"}', "env_vars": '["NOVU_API_KEY"]', "frameworks_tested": "nextjs,react,express,fastapi"},
        {"slug": "ntfy", "api_type": "REST", "auth_method": "none", "install_command": "pip install ntfy-wrapper", "sdk_packages": '{"pip": "ntfy-wrapper"}', "env_vars": '["NTFY_TOPIC"]', "frameworks_tested": ""},

        # File Storage
        {"slug": "minio", "api_type": "REST", "auth_method": "api_key", "install_command": "pip install minio", "sdk_packages": '{"npm": "minio", "pip": "minio"}', "env_vars": '["MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY"]', "frameworks_tested": "nextjs,django,fastapi,express"},

        # Deployment
        {"slug": "coolify", "api_type": "REST", "auth_method": "bearer", "install_command": "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash", "sdk_packages": '{}', "env_vars": '["COOLIFY_URL", "COOLIFY_TOKEN"]', "frameworks_tested": ""},
        {"slug": "dokku", "api_type": "CLI", "auth_method": "none", "install_command": "wget -NP . https://dokku.com/bootstrap.sh && sudo bash bootstrap.sh", "sdk_packages": '{}', "env_vars": '[]', "frameworks_tested": ""},
        {"slug": "caprover", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install -g caprover", "sdk_packages": '{"npm": "caprover"}', "env_vars": '["CAPROVER_URL", "CAPROVER_PASSWORD"]', "frameworks_tested": ""},

        # Analytics (additional)
        {"slug": "fathom-analytics", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install fathom-client", "sdk_packages": '{"npm": "fathom-client"}', "env_vars": '["FATHOM_SITE_ID"]', "frameworks_tested": "nextjs,react,vue,gatsby"},
        {"slug": "pirsch", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install pirsch-sdk", "sdk_packages": '{"npm": "pirsch-sdk", "pip": "pirsch-api"}', "env_vars": '["PIRSCH_ACCESS_TOKEN"]', "frameworks_tested": "nextjs,react,vue"},

        # Auth (additional)
        {"slug": "clerk", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @clerk/nextjs", "sdk_packages": '{"npm": "@clerk/nextjs", "pip": "clerk-backend-api"}', "env_vars": '["CLERK_PUBLISHABLE_KEY", "CLERK_SECRET_KEY"]', "frameworks_tested": "nextjs,react,remix,expo"},
        {"slug": "kinde", "api_type": "REST", "auth_method": "oauth2", "install_command": "npm install @kinde-oss/kinde-auth-nextjs", "sdk_packages": '{"npm": "@kinde-oss/kinde-auth-nextjs"}', "env_vars": '["KINDE_CLIENT_ID", "KINDE_CLIENT_SECRET", "KINDE_ISSUER_URL"]', "frameworks_tested": "nextjs,react,express"},
        {"slug": "authentik", "api_type": "REST", "auth_method": "oauth2", "install_command": "docker pull ghcr.io/goauthentik/server", "sdk_packages": '{}', "env_vars": '["AUTHENTIK_SECRET_KEY", "AUTHENTIK_HOST"]', "frameworks_tested": ""},
        {"slug": "ssoready", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install ssoready", "sdk_packages": '{"npm": "ssoready", "pip": "ssoready"}', "env_vars": '["SSOREADY_API_KEY"]', "frameworks_tested": "nextjs,express,fastapi"},

        # Databases & ORMs
        {"slug": "prisma", "api_type": "SDK", "auth_method": "none", "install_command": "npm install prisma @prisma/client", "sdk_packages": '{"npm": "@prisma/client"}', "env_vars": '["DATABASE_URL"]', "frameworks_tested": "nextjs,express,fastapi,nestjs"},
        {"slug": "redis", "api_type": "SDK", "auth_method": "none", "install_command": "npm install redis", "sdk_packages": '{"npm": "redis", "pip": "redis"}', "env_vars": '["REDIS_URL"]', "frameworks_tested": "nextjs,express,django,flask,fastapi"},
        {"slug": "qdrant", "api_type": "REST", "auth_method": "api_key", "install_command": "pip install qdrant-client", "sdk_packages": '{"pip": "qdrant-client", "npm": "@qdrant/js-client-rest"}', "env_vars": '["QDRANT_URL", "QDRANT_API_KEY"]', "frameworks_tested": "fastapi,express,nextjs"},
        {"slug": "weaviate", "api_type": "REST", "auth_method": "api_key", "install_command": "pip install weaviate-client", "sdk_packages": '{"pip": "weaviate-client", "npm": "weaviate-client"}', "env_vars": '["WEAVIATE_URL", "WEAVIATE_API_KEY"]', "frameworks_tested": "fastapi,nextjs,express"},

        # CMS & Content
        {"slug": "wiki-js", "api_type": "GraphQL", "auth_method": "bearer", "install_command": "docker pull ghcr.io/requarks/wiki", "sdk_packages": '{}', "env_vars": '["WIKI_DB_HOST", "WIKI_DB_USER", "WIKI_DB_PASS"]', "frameworks_tested": ""},

        # Media & Files
        {"slug": "cloudinary", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install cloudinary", "sdk_packages": '{"npm": "cloudinary", "pip": "cloudinary"}', "env_vars": '["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"]', "frameworks_tested": "nextjs,react,vue,django,express"},
        {"slug": "paperless-ngx", "api_type": "REST", "auth_method": "bearer", "install_command": "docker pull ghcr.io/paperless-ngx/paperless-ngx", "sdk_packages": '{}', "env_vars": '["PAPERLESS_URL", "PAPERLESS_TOKEN"]', "frameworks_tested": ""},

        # AI & ML
        {"slug": "dify", "api_type": "REST", "auth_method": "api_key", "install_command": "docker compose up -d", "sdk_packages": '{"pip": "dify-client"}', "env_vars": '["DIFY_API_KEY", "DIFY_API_URL"]', "frameworks_tested": "nextjs,fastapi"},
        {"slug": "firecrawl", "api_type": "REST", "auth_method": "api_key", "install_command": "pip install firecrawl-py", "sdk_packages": '{"pip": "firecrawl-py", "npm": "@mendable/firecrawl-js"}', "env_vars": '["FIRECRAWL_API_KEY"]', "frameworks_tested": "nextjs,fastapi,express"},

        # Payments (additional)
        {"slug": "paddle", "api_type": "REST", "auth_method": "api_key", "install_command": "npm install @paddle/paddle-js", "sdk_packages": '{"npm": "@paddle/paddle-js", "pip": "paddle-billing"}', "env_vars": '["PADDLE_API_KEY", "PADDLE_CLIENT_TOKEN"]', "frameworks_tested": "nextjs,react,vue"},

        # DevOps & Hosting
        {"slug": "render", "api_type": "REST", "auth_method": "bearer", "install_command": "", "sdk_packages": '{}', "env_vars": '["RENDER_API_KEY"]', "frameworks_tested": ""},
        {"slug": "rancher", "api_type": "REST", "auth_method": "bearer", "install_command": "docker pull rancher/rancher", "sdk_packages": '{}', "env_vars": '["RANCHER_URL", "RANCHER_ACCESS_KEY", "RANCHER_SECRET_KEY"]', "frameworks_tested": ""},

        # Documentation
        {"slug": "mintlify", "api_type": "CLI", "auth_method": "api_key", "install_command": "npx mintlify dev", "sdk_packages": '{"npm": "mintlify"}', "env_vars": '["MINTLIFY_TOKEN"]', "frameworks_tested": ""},

        # Job Queues
        {"slug": "bullmq", "api_type": "SDK", "auth_method": "none", "install_command": "npm install bullmq", "sdk_packages": '{"npm": "bullmq"}', "env_vars": '["REDIS_URL"]', "frameworks_tested": "nextjs,express,nestjs"},

        # Search
        {"slug": "searxng", "api_type": "REST", "auth_method": "none", "install_command": "docker pull searxng/searxng", "sdk_packages": '{}', "env_vars": '["SEARXNG_URL"]', "frameworks_tested": ""},

        # BI & Reporting
        {"slug": "metabase", "api_type": "REST", "auth_method": "api_key", "install_command": "docker pull metabase/metabase", "sdk_packages": '{}', "env_vars": '["METABASE_URL", "METABASE_API_KEY"]', "frameworks_tested": ""},

        # Landing Pages
        {"slug": "carrd", "api_type": "REST", "auth_method": "api_key", "install_command": "", "sdk_packages": '{}', "env_vars": '[]', "frameworks_tested": ""},

        # CRM
        {"slug": "atomic-crm", "api_type": "REST", "auth_method": "bearer", "install_command": "npm install", "sdk_packages": '{}', "env_vars": '["VITE_API_URL"]', "frameworks_tested": "react"},
    ]

    for tool_data in ENRICHMENTS:
        slug = tool_data.get("slug")
        if not slug:
            continue
        # Build SET clause only for fields that are currently empty
        set_parts = []
        params = []
        for field, value in tool_data.items():
            if field == "slug":
                continue
            if value:  # skip empty values
                set_parts.append(f"{field} = CASE WHEN ({field} IS NULL OR {field} = '') THEN ? ELSE {field} END")
                params.append(value)

        if set_parts:
            params.append(slug)
            query = f"UPDATE tools SET {', '.join(set_parts)} WHERE slug = ? AND status = 'approved'"
            try:
                await db.execute(query, params)
            except Exception:
                pass  # tool might not exist — that's fine

    await db.commit()

    # Seed verified compatibility pairs (idempotent via ON CONFLICT)
    SEED_PAIRS = [
        # Auth + Payments
        ("hanko", "polar"), ("hanko", "lemon-squeezy"), ("clerk", "polar"),
        ("supertokens", "polar"), ("lucia", "polar"), ("kinde", "polar"),
        # Auth + Database
        ("hanko", "supabase"), ("clerk", "supabase"), ("lucia", "pocketbase"),
        ("lucia", "turso"), ("hanko", "pocketbase"), ("supertokens", "supabase"),
        # Auth + Email
        ("hanko", "resend"), ("clerk", "resend"), ("supertokens", "resend"),
        # Database + Analytics
        ("supabase", "posthog"), ("supabase", "plausible-analytics"),
        ("pocketbase", "umami"), ("turso", "simple-analytics"),
        # Database + CMS
        ("supabase", "strapi"), ("supabase", "directus"), ("supabase", "payload"),
        # Database + Search
        ("supabase", "meilisearch"), ("pocketbase", "typesense"),
        # Payments + Email
        ("polar", "resend"), ("lemon-squeezy", "resend"), ("polar", "plunk"),
        # Monitoring + Database
        ("sentry", "supabase"), ("sentry", "pocketbase"), ("sentry", "turso"),
        # Monitoring + Auth
        ("sentry", "hanko"), ("sentry", "clerk"),
        # Hosting + Database
        ("coolify", "supabase"), ("coolify", "pocketbase"),
        ("dokku", "pocketbase"), ("caprover", "supabase"),
        # Feature Flags + Analytics
        ("flagsmith", "posthog"), ("growthbook", "posthog"),
        # Notifications + Payments
        ("novu", "polar"), ("ntfy", "polar"),
    ]
    for slug_a, slug_b in SEED_PAIRS:
        a, b = sorted([slug_a, slug_b])
        try:
            await db.execute("""
                INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source, verified, success_count)
                VALUES (?, ?, 'seed', 1, 5)
                ON CONFLICT(tool_a_slug, tool_b_slug) DO NOTHING
            """, (a, b))
        except Exception:
            pass
    await db.commit()

    # Bulk category-default enrichment for tools with NO metadata at all
    # Sets reasonable defaults so agents always get at least api_type and auth_method
    await db.execute("""
        UPDATE tools SET api_type = CASE
            WHEN source_type = 'code' THEN 'SDK'
            ELSE 'REST'
        END
        WHERE status = 'approved' AND (api_type IS NULL OR api_type = '')
    """)
    await db.execute("""
        UPDATE tools SET auth_method = CASE
            WHEN source_type = 'code' THEN 'none'
            ELSE 'api_key'
        END
        WHERE status = 'approved' AND (auth_method IS NULL OR auth_method = '')
    """)
    await db.commit()


async def init_db():
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.executescript(FTS_SCHEMA)
        # Migration: add is_verified column if missing (for existing DBs)
        try:
            await db.execute("SELECT is_verified FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")
        # Migration: add columns if missing (for existing DBs)
        for col, ddl in [
            ("price_pence", "ALTER TABLE tools ADD COLUMN price_pence INTEGER"),
            ("delivery_type", "ALTER TABLE tools ADD COLUMN delivery_type TEXT NOT NULL DEFAULT 'link'"),
            ("delivery_url", "ALTER TABLE tools ADD COLUMN delivery_url TEXT NOT NULL DEFAULT ''"),
            ("stripe_account_id", "ALTER TABLE tools ADD COLUMN stripe_account_id TEXT NOT NULL DEFAULT ''"),
            ("verified_at", "ALTER TABLE tools ADD COLUMN verified_at TIMESTAMP"),
            ("verified_until", "ALTER TABLE tools ADD COLUMN verified_until TIMESTAMP"),
            ("maker_id", "ALTER TABLE tools ADD COLUMN maker_id INTEGER REFERENCES makers(id)"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        # Migration: add is_ejectable column if missing
        try:
            await db.execute("SELECT is_ejectable FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN is_ejectable INTEGER NOT NULL DEFAULT 0")
        # Migration: add replaces column if missing (competitors this tool replaces)
        try:
            await db.execute("SELECT replaces FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN replaces TEXT NOT NULL DEFAULT ''")
        # Migration: add plugin metadata columns if missing
        for col, sql in [
            ("tool_type", "ALTER TABLE tools ADD COLUMN tool_type TEXT DEFAULT NULL"),
            ("platforms", "ALTER TABLE tools ADD COLUMN platforms TEXT NOT NULL DEFAULT ''"),
            ("install_command", "ALTER TABLE tools ADD COLUMN install_command TEXT NOT NULL DEFAULT ''"),
        ]:
            try:
                await db.execute(sql)
            except Exception:
                pass  # Column already exists
        # ── boosted_competitor migration ──────────────────────────────────────
        try:
            await db.execute("SELECT boosted_competitor FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN boosted_competitor TEXT NOT NULL DEFAULT ''")
            await db.commit()
        # Create indexes that depend on migrated columns
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tools_maker ON tools(maker_id)")
        # Migration: add tool_id to maker_updates if missing
        try:
            await db.execute("ALTER TABLE maker_updates ADD COLUMN tool_id INTEGER REFERENCES tools(id)")
        except Exception:
            pass
        # Migration: add indie_status to makers if missing
        try:
            await db.execute("SELECT indie_status FROM makers LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE makers ADD COLUMN indie_status TEXT NOT NULL DEFAULT ''")
        # Migration: add stripe_account_id to makers if missing
        try:
            await db.execute("ALTER TABLE makers ADD COLUMN stripe_account_id TEXT")
        except Exception:
            pass
        # Migration: add discount_pence to purchases
        try:
            await db.execute("SELECT discount_pence FROM purchases LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE purchases ADD COLUMN discount_pence INTEGER NOT NULL DEFAULT 0")
        # Migration: add badge_token to users
        try:
            await db.execute("SELECT badge_token FROM users LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE users ADD COLUMN badge_token TEXT")
        # Platform boost columns
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN is_boosted INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN boost_expires_at TEXT DEFAULT NULL")
        except Exception:
            pass
        # Referral system columns
        for col, ddl in [
            ("referral_code", "ALTER TABLE users ADD COLUMN referral_code TEXT"),
            ("referred_by", "ALTER TABLE users ADD COLUMN referred_by INTEGER REFERENCES users(id)"),
            ("referral_boost_days", "ALTER TABLE users ADD COLUMN referral_boost_days INTEGER NOT NULL DEFAULT 0"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM users LIMIT 1")
            except Exception:
                await db.execute(ddl)
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)")
        # Public submission columns (Ed's PR)
        for col, ddl in [
            ("submitter_email", "ALTER TABLE tools ADD COLUMN submitter_email TEXT"),
            ("submitted_from_ip", "ALTER TABLE tools ADD COLUMN submitted_from_ip TEXT"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tools_submitter_email ON tools(submitter_email)")
        # Migration: add claimed_at to tools for tracking when tools are claimed
        try:
            await db.execute("SELECT claimed_at FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN claimed_at TIMESTAMP")
            # Backfill: approximate claimed_at from created_at for already-claimed tools
            await db.execute("UPDATE tools SET claimed_at = created_at WHERE maker_id IS NOT NULL AND claimed_at IS NULL")
        # Migration: add integration_python column for custom Python snippets
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN integration_python TEXT DEFAULT ''")
        except Exception:
            pass
        # Migration: add integration_curl column for custom curl snippets
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN integration_curl TEXT DEFAULT ''")
        except Exception:
            pass
        # Migration: add mcp_view_count for tracking AI agent tool lookups
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN mcp_view_count INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        # Migration: GitHub OAuth fields on users
        for col, ddl in [
            ("github_id", "ALTER TABLE users ADD COLUMN github_id INTEGER"),
            ("github_username", "ALTER TABLE users ADD COLUMN github_username TEXT"),
            ("github_avatar_url", "ALTER TABLE users ADD COLUMN github_avatar_url TEXT"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM users LIMIT 1")
            except Exception:
                await db.execute(ddl)
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id)")
        # Migration: add pixel_avatar column for user pixel art avatars
        try:
            await db.execute("SELECT pixel_avatar FROM users LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE users ADD COLUMN pixel_avatar TEXT")
        # Migration: add pixel_avatar_approved column
        try:
            await db.execute("SELECT pixel_avatar_approved FROM users LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE users ADD COLUMN pixel_avatar_approved INTEGER NOT NULL DEFAULT 0")
        # Migration: maker story questionnaire
        for col, ddl in [
            ("story_motivation", "ALTER TABLE makers ADD COLUMN story_motivation TEXT DEFAULT ''"),
            ("story_challenge", "ALTER TABLE makers ADD COLUMN story_challenge TEXT DEFAULT ''"),
            ("story_advice", "ALTER TABLE makers ADD COLUMN story_advice TEXT DEFAULT ''"),
            ("story_fun_fact", "ALTER TABLE makers ADD COLUMN story_fun_fact TEXT DEFAULT ''"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM makers LIMIT 1")
            except Exception:
                await db.execute(ddl)
        # Migration: GitHub fields on tools
        for col, ddl in [
            ("github_url", "ALTER TABLE tools ADD COLUMN github_url TEXT DEFAULT ''"),
            ("github_stars", "ALTER TABLE tools ADD COLUMN github_stars INTEGER DEFAULT 0"),
            ("github_language", "ALTER TABLE tools ADD COLUMN github_language TEXT DEFAULT ''"),
            ("last_github_commit", "ALTER TABLE tools ADD COLUMN last_github_commit TIMESTAMP"),
            ("github_freshness", "ALTER TABLE tools ADD COLUMN github_freshness TEXT"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        # Migration: add source and tool_slug columns to subscribers for tracking
        for col, ddl in [
            ("source", "ALTER TABLE subscribers ADD COLUMN source TEXT NOT NULL DEFAULT ''"),
            ("tool_slug", "ALTER TABLE subscribers ADD COLUMN tool_slug TEXT NOT NULL DEFAULT ''"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM subscribers LIMIT 1")
            except Exception:
                await db.execute(ddl)
        # Migration: add unsubscribe_token to subscribers
        try:
            await db.execute("SELECT unsubscribe_token FROM subscribers LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE subscribers ADD COLUMN unsubscribe_token TEXT")
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_unsub_token ON subscribers(unsubscribe_token)")
        # Backfill tokens for existing subscribers that don't have one
        import uuid as _uuid
        cursor = await db.execute("SELECT id FROM subscribers WHERE unsubscribe_token IS NULL")
        rows = await cursor.fetchall()
        for row in rows:
            await db.execute(
                "UPDATE subscribers SET unsubscribe_token = ? WHERE id = ?",
                (str(_uuid.uuid4()), row["id"]),
            )
        if rows:
            await db.commit()
        # Migration: add badge_nudge_sent to tools
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN badge_nudge_sent INTEGER DEFAULT 0")
            await db.commit()
        except Exception:
            pass
        # Migration: add email_opt_out to users
        try:
            await db.execute("ALTER TABLE users ADD COLUMN email_opt_out INTEGER DEFAULT 0")
            await db.commit()
        except Exception:
            pass
        # Migration: add trial_ends_at to users (7-day free Pro trial)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN trial_ends_at TIMESTAMP DEFAULT NULL")
            await db.commit()
        except Exception:
            pass
        # Migration: add tool_of_the_week to tools
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN tool_of_the_week INTEGER DEFAULT 0")
            await db.commit()
        except Exception:
            pass
        # Migration: track when a tool last won TOTW (4-week cooldown)
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN totw_last_won TIMESTAMP")
            await db.commit()
        except Exception:
            pass
        # Migration: tool_of_week_history — permanent record of every TOTW winner
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_of_week_history (
                id INTEGER PRIMARY KEY,
                tool_id INTEGER NOT NULL REFERENCES tools(id),
                featured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        # Migration: quality gate enrichment columns
        for col, ddl in [
            ("domain_age_days", "ALTER TABLE tools ADD COLUMN domain_age_days INTEGER DEFAULT NULL"),
            ("has_free_tier", "ALTER TABLE tools ADD COLUMN has_free_tier INTEGER DEFAULT NULL"),
            ("social_mentions_count", "ALTER TABLE tools ADD COLUMN social_mentions_count INTEGER DEFAULT NULL"),
            ("rejection_reason", "ALTER TABLE tools ADD COLUMN rejection_reason TEXT DEFAULT NULL"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        # Migration: add AI Dev Tools category if missing
        cursor = await db.execute("SELECT id FROM categories WHERE slug = 'ai-dev-tools'")
        if not await cursor.fetchone():
            await db.execute(
                "INSERT INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
                ("AI Dev Tools", "ai-dev-tools", "MCP servers, AI coding assistants, and dev agent tools", "🧠")
            )
        # Seed categories if empty
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM categories")
        count = (await cursor.fetchone())['cnt']
        if count == 0:
            await db.executemany(
                "INSERT INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
                SEED_CATEGORIES,
            )
        # Migration: add expanded categories if missing
        for _cat_name, _cat_slug, _cat_desc, _cat_icon in [
            ("Games & Entertainment", "games-entertainment", "Indie games, game engines, and interactive experiences", "🎮"),
            ("Learning & Education", "learning-education", "Flashcards, courses, and educational tools", "📚"),
            ("Newsletters & Content", "newsletters-content", "Publishing platforms, newsletters, and content tools", "📰"),
            ("Creative Tools", "creative-tools", "Music, art, video, and creative software", "🎭"),
        ]:
            cursor = await db.execute("SELECT id FROM categories WHERE slug = ?", (_cat_slug,))
            if not await cursor.fetchone():
                await db.execute(
                    "INSERT INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
                    (_cat_name, _cat_slug, _cat_desc, _cat_icon)
                )
        await db.commit()

        # Migration: seed non-dev indie creations
        _new_cat_cache = {}
        async def _get_cat_id(_s):
            if _s not in _new_cat_cache:
                cur = await db.execute("SELECT id FROM categories WHERE slug = ?", (_s,))
                row = await cur.fetchone()
                _new_cat_cache[_s] = row['id'] if row else None
            return _new_cat_cache[_s]

        _seed_creations = [
            # Games & Entertainment
            ("Lichess", "lichess", "Free, open-source chess server powering millions of games daily", "https://lichess.org", "https://github.com/lichess-org/lila", "games-entertainment", "open-source,chess,multiplayer", "code"),
            ("Mindustry", "mindustry", "Open-source factory-building tower defense game", "https://mindustrygame.github.io", "https://github.com/Anuken/Mindustry", "games-entertainment", "open-source,game,tower-defense", "code"),
            ("Minetest", "minetest", "Open-source voxel game engine — build your own block worlds", "https://www.minetest.net", "https://github.com/minetest/minetest", "games-entertainment", "open-source,game-engine,voxel", "code"),
            ("OpenTTD", "openttd", "Open-source transport tycoon simulation", "https://www.openttd.org", "https://github.com/OpenTTD/OpenTTD", "games-entertainment", "open-source,simulation,strategy", "code"),
            ("Veloren", "veloren", "Open-source multiplayer RPG inspired by Cube World", "https://veloren.net", "https://gitlab.com/veloren/veloren", "games-entertainment", "open-source,rpg,multiplayer", "code"),
            ("SuperTuxKart", "supertuxkart", "Open-source kart racer with online multiplayer", "https://supertuxkart.net", "https://github.com/supertuxkart/stk-code", "games-entertainment", "open-source,racing,multiplayer", "code"),
            ("Wesnoth", "wesnoth", "Open-source turn-based strategy with fantasy setting", "https://www.wesnoth.org", "https://github.com/wesnoth/wesnoth", "games-entertainment", "open-source,strategy,turn-based", "code"),
            # Newsletters & Content
            ("Buttondown", "buttondown", "The easiest way to run a newsletter — built by one developer", "https://buttondown.email", "", "newsletters-content", "newsletter,email,writing", "saas"),
            ("WriteFreely", "writefreely", "Minimalist, federated blogging platform", "https://writefreely.org", "https://github.com/writefreely/writefreely", "newsletters-content", "open-source,blog,fediverse", "code"),
            ("Ghost", "ghost-cms", "Independent publishing platform for creators", "https://ghost.org", "https://github.com/TryGhost/Ghost", "newsletters-content", "open-source,publishing,newsletter", "code"),
            ("Audiobookshelf", "audiobookshelf", "Self-hosted audiobook and podcast server", "https://www.audiobookshelf.org", "https://github.com/advplyr/audiobookshelf", "newsletters-content", "open-source,audiobooks,self-hosted", "code"),
            ("Wallabag", "wallabag", "Self-hosted read-it-later app — save and classify articles", "https://wallabag.org", "https://github.com/wallabag/wallabag", "newsletters-content", "open-source,reading,self-hosted", "code"),
            # Learning & Education
            ("Anki", "anki", "Powerful spaced repetition flashcards — remember anything", "https://apps.ankiweb.net", "https://github.com/ankitects/anki", "learning-education", "open-source,flashcards,spaced-repetition", "code"),
            ("Exercism", "exercism", "Free code practice and mentoring across 70+ languages", "https://exercism.org", "https://github.com/exercism/exercism", "learning-education", "open-source,coding,mentoring", "code"),
            ("Logseq", "logseq", "Privacy-first knowledge management and note-taking", "https://logseq.com", "https://github.com/logseq/logseq", "learning-education", "open-source,notes,knowledge-graph", "code"),
            ("Zettlr", "zettlr", "Markdown editor built for researchers and academics", "https://www.zettlr.com", "https://github.com/Zettlr/Zettlr", "learning-education", "open-source,markdown,academic", "code"),
            ("LibreTexts", "libretexts", "Free, open textbook platform for higher education", "https://libretexts.org", "", "learning-education", "open-source,textbooks,education", "code"),
            ("OpenStax", "openstax", "Free, peer-reviewed textbooks by Rice University", "https://openstax.org", "", "learning-education", "free,textbooks,education", "saas"),
            # Creative Tools
            ("Penpot", "penpot", "Open-source design and prototyping platform", "https://penpot.app", "https://github.com/penpot/penpot", "creative-tools", "open-source,design,prototyping", "code"),
            ("Excalidraw", "excalidraw", "Virtual whiteboard for hand-drawn diagrams", "https://excalidraw.com", "https://github.com/excalidraw/excalidraw", "creative-tools", "open-source,whiteboard,diagrams", "code"),
            ("Tldraw", "tldraw", "Infinite canvas whiteboard SDK and app", "https://www.tldraw.com", "https://github.com/tldraw/tldraw", "creative-tools", "open-source,canvas,whiteboard", "code"),
            ("Pixelorama", "pixelorama", "Free pixel art editor made with Godot Engine", "https://orama-interactive.itch.io/pixelorama", "https://github.com/Orama-Interactive/Pixelorama", "creative-tools", "open-source,pixel-art,editor", "code"),
            ("Krita", "krita", "Professional free digital painting application", "https://krita.org", "https://github.com/KDE/krita", "creative-tools", "open-source,painting,digital-art", "code"),
            ("LMMS", "lmms", "Free cross-platform music production software", "https://lmms.io", "https://github.com/LMMS/lmms", "creative-tools", "open-source,music,production", "code"),
            ("Ardour", "ardour", "Professional-grade digital audio workstation", "https://ardour.org", "https://github.com/Ardour/ardour", "creative-tools", "open-source,audio,daw", "code"),
        ]

        for _name, _slug, _tagline, _url, _github_url, _cat_slug, _tags, _source_type in _seed_creations:
            existing = await db.execute("SELECT id FROM tools WHERE slug = ?", (_slug,))
            if await existing.fetchone():
                continue
            _cat_id = await _get_cat_id(_cat_slug)
            if not _cat_id:
                continue
            await db.execute(
                """INSERT INTO tools (name, slug, tagline, description, url, github_url, category_id, tags, status, source_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?)""",
                (_name, _slug, _tagline, _tagline, _url, _github_url or '', _cat_id, _tags, _source_type)
            )
        await db.commit()
        del _new_cat_cache, _seed_creations

        # Migration: agent citation tracking table
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_id INTEGER NOT NULL,
                    agent_name TEXT NOT NULL DEFAULT 'unknown',
                    context TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tool_id) REFERENCES tools(id)
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_citations_tool ON agent_citations(tool_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_citations_created ON agent_citations(created_at)")
        except Exception:
            pass
        await db.commit()

        # Agent Memory: add api_key_id to search_logs + create developer_profiles
        try:
            await db.execute("SELECT api_key_id FROM search_logs LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE search_logs ADD COLUMN api_key_id INTEGER")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_api_key ON search_logs(api_key_id)")
            await db.commit()

        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_query ON search_logs(query)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_source ON search_logs(source)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_created ON search_logs(created_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_top_slug ON search_logs(top_result_slug)")

        await db.execute("""CREATE TABLE IF NOT EXISTS developer_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL UNIQUE REFERENCES api_keys(id),
            interests TEXT NOT NULL DEFAULT '{}',
            tech_stack TEXT NOT NULL DEFAULT '[]',
            favorite_tools TEXT NOT NULL DEFAULT '[]',
            search_count INTEGER NOT NULL DEFAULT 0,
            personalization_enabled INTEGER NOT NULL DEFAULT 1,
            notice_shown INTEGER NOT NULL DEFAULT 0,
            last_rebuilt_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.commit()

        # Source type: classify tools as 'code' (open-source/installable) vs 'saas' (hosted service)
        try:
            await db.execute("SELECT source_type FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN source_type VARCHAR DEFAULT 'saas'")
            await db.execute("""
                UPDATE tools SET source_type = 'code'
                WHERE url LIKE '%github.com%' OR url LIKE '%gitlab.com%' OR url LIKE '%codeberg.org%'
            """)
            await db.commit()

        # Migration: add pixel_icon column for maker pixel art
        try:
            await db.execute("SELECT pixel_icon FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN pixel_icon TEXT")
        # Migration: add landing_position for curated landing page showcase
        try:
            await db.execute("SELECT landing_position FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN landing_position INTEGER")

        # Migration: add quality score columns
        for col, ddl in [
            ("quality_score", "ALTER TABLE tools ADD COLUMN quality_score REAL DEFAULT 0.0"),
            ("last_health_check", "ALTER TABLE tools ADD COLUMN last_health_check TIMESTAMP"),
            ("health_status", "ALTER TABLE tools ADD COLUMN health_status TEXT DEFAULT 'unknown'"),
            ("first_dead_at", "ALTER TABLE tools ADD COLUMN first_dead_at TIMESTAMP"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        await db.commit()

        # Migration: GitHub maintenance signal columns
        for col, ddl in [
            ("github_last_commit", "ALTER TABLE tools ADD COLUMN github_last_commit TEXT"),
            ("github_open_issues", "ALTER TABLE tools ADD COLUMN github_open_issues INTEGER DEFAULT 0"),
            ("github_is_archived", "ALTER TABLE tools ADD COLUMN github_is_archived INTEGER DEFAULT 0"),
            ("github_last_check", "ALTER TABLE tools ADD COLUMN github_last_check TIMESTAMP"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        await db.commit()

        # ── Agentic Package Manager metadata ──
        for col, typedef in [
            ("api_type", "TEXT DEFAULT ''"),
            ("auth_method", "TEXT DEFAULT ''"),
            ("sdk_packages", "TEXT DEFAULT ''"),
            ("env_vars", "TEXT DEFAULT ''"),
            ("frameworks_tested", "TEXT DEFAULT ''"),
            ("verified_pairs", "TEXT DEFAULT ''"),
        ]:
            try:
                await db.execute(f"ALTER TABLE tools ADD COLUMN {col} {typedef}")
            except Exception:
                pass
        await db.commit()

        try:
            await db.execute("ALTER TABLE tools ADD COLUMN agent_instructions TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        await db.commit()

        # Performance indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_views_viewed ON tool_views(viewed_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_maker_updates_tool ON maker_updates(tool_id, created_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tools_status_source ON tools(status, source_type)")
        await db.commit()

        # ── Tool pairs table (Agentic Package Manager) ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_a_slug TEXT NOT NULL,
                tool_b_slug TEXT NOT NULL,
                verified INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tool_a_slug, tool_b_slug)
            )
        """)
        await db.commit()

        # ── User tool pair reports (deduplication for community compatibility) ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_tool_pair_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tool_a_slug TEXT NOT NULL,
                tool_b_slug TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, tool_a_slug, tool_b_slug)
            )
        """)
        # Performance indexes on tool_pairs
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_pairs_a ON tool_pairs(tool_a_slug)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_pairs_b ON tool_pairs(tool_b_slug)")
        # Composite indexes for OR + success_count queries (find_compatible, get_verified_pairs)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_pairs_a_success ON tool_pairs(tool_a_slug, success_count DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_pairs_b_success ON tool_pairs(tool_b_slug, success_count DESC)")
        await db.commit()

        # Migration: add scopes column to api_keys
        try:
            await db.execute("SELECT scopes FROM api_keys LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE api_keys ADD COLUMN scopes TEXT NOT NULL DEFAULT 'read'")
            await db.commit()

        # Migration: make agent_actions.api_key_id nullable for keyless outcome reporting
        try:
            row = await db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='agent_actions'")
            schema = await row.fetchone()
            if schema and 'api_key_id INTEGER NOT NULL' in (schema[0] or ''):
                await db.execute("""CREATE TABLE agent_actions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key_id INTEGER REFERENCES api_keys(id),
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('recommend','shortlist','report_outcome','confirm_integration','submit_tool')),
                    tool_slug TEXT NOT NULL,
                    tool_b_slug TEXT,
                    success INTEGER,
                    notes TEXT,
                    query_context TEXT,
                    created_at TIMESTAMP DEFAULT (datetime('now'))
                )""")
                await db.execute("INSERT INTO agent_actions_new SELECT * FROM agent_actions")
                await db.execute("DROP TABLE agent_actions")
                await db.execute("ALTER TABLE agent_actions_new RENAME TO agent_actions")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_key ON agent_actions(api_key_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_user ON agent_actions(user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_tool ON agent_actions(tool_slug)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_action ON agent_actions(action)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_date ON agent_actions(created_at)")
                await db.commit()
        except Exception:
            pass

        # Migration: add agent_client to search_logs for cross-platform tracking
        try:
            await db.execute("ALTER TABLE search_logs ADD COLUMN agent_client TEXT")
            await db.commit()
        except Exception:
            pass

        # Migration: add normalized_query to search_logs for gap detection
        try:
            await db.execute("ALTER TABLE search_logs ADD COLUMN normalized_query TEXT")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_normalized ON search_logs(normalized_query)")
            await db.execute("UPDATE search_logs SET normalized_query = LOWER(TRIM(query)) WHERE normalized_query IS NULL")
            await db.commit()
        except Exception:
            pass

        # Migration: add quality_flags column to tools for pre-screening results
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN quality_flags TEXT DEFAULT ''")
            await db.commit()
        except Exception:
            pass

        # Migration: create tool_flags table for community reports
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id INTEGER NOT NULL REFERENCES tools(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                flag_type TEXT NOT NULL CHECK(flag_type IN ('abandoned', 'misleading', 'not_indie', 'spam', 'other')),
                note TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tool_id, user_id, flag_type)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_flags_tool ON tool_flags(tool_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_flags_user ON tool_flags(user_id)")
        await db.commit()

        # ── Verified stacks table (Agentic Package Manager) ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS verified_stacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_slugs TEXT NOT NULL,
                use_case TEXT,
                success_count INTEGER NOT NULL DEFAULT 1,
                source TEXT NOT NULL DEFAULT 'agent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tool_slugs)
            )
        """)
        await db.commit()

        # ── Tool conflicts table (Agentic Package Manager) ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_a_slug TEXT NOT NULL,
                tool_b_slug TEXT NOT NULL,
                reason TEXT,
                report_count INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tool_a_slug, tool_b_slug)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_conflicts_a ON tool_conflicts(tool_a_slug)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_conflicts_b ON tool_conflicts(tool_b_slug)")
        await db.commit()

        # ── Normalize tool_pairs: ensure tool_a_slug < tool_b_slug alphabetically ──
        try:
            cursor = await db.execute(
                "SELECT id, tool_a_slug, tool_b_slug, success_count FROM tool_pairs WHERE tool_a_slug > tool_b_slug"
            )
            bad_rows = await cursor.fetchall()
            for row in bad_rows:
                existing = await db.execute(
                    "SELECT id, success_count FROM tool_pairs WHERE tool_a_slug = ? AND tool_b_slug = ?",
                    (row['tool_b_slug'], row['tool_a_slug']),
                )
                existing_row = await existing.fetchone()
                if existing_row:
                    await db.execute(
                        "UPDATE tool_pairs SET success_count = success_count + ? WHERE id = ?",
                        (row['success_count'], existing_row['id']),
                    )
                    await db.execute("DELETE FROM tool_pairs WHERE id = ?", (row['id'],))
                else:
                    await db.execute(
                        "UPDATE tool_pairs SET tool_a_slug = ?, tool_b_slug = ? WHERE id = ?",
                        (row['tool_b_slug'], row['tool_a_slug'], row['id']),
                    )
            if bad_rows:
                await db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Pair normalization migration: %s", e)

        # ── Stacks intelligence columns ──
        for col_sql in [
            "ALTER TABLE stacks ADD COLUMN source TEXT NOT NULL DEFAULT 'curated'",
            "ALTER TABLE stacks ADD COLUMN framework TEXT",
            "ALTER TABLE stacks ADD COLUMN use_case TEXT",
            "ALTER TABLE stacks ADD COLUMN replaces_json TEXT",
            "ALTER TABLE stacks ADD COLUMN confidence_score REAL NOT NULL DEFAULT 0",
            "ALTER TABLE stacks ADD COLUMN total_tokens_saved INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE stacks ADD COLUMN tool_count_cached INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE stacks ADD COLUMN generated_at TIMESTAMP",
            "ALTER TABLE stacks ADD COLUMN upvote_count INTEGER NOT NULL DEFAULT 0",
        ]:
            try:
                await db.execute(col_sql)
            except Exception:
                pass
        # Stack upvotes tracking table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stack_upvotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stack_id INTEGER NOT NULL REFERENCES stacks(id),
                ip_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stack_id, ip_hash)
            )
        """)
        await db.commit()

        # ── Multi-category junction table ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_categories (
                tool_id INTEGER NOT NULL REFERENCES tools(id),
                category_id INTEGER NOT NULL REFERENCES categories(id),
                is_primary INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (tool_id, category_id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_categories_category ON tool_categories(category_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tool_categories_tool ON tool_categories(tool_id)")
        await db.commit()

        # Migration: backfill tool_categories from tools.category_id
        try:
            cursor = await db.execute("SELECT COUNT(*) as cnt FROM tool_categories")
            count = (await cursor.fetchone())['cnt']
            if count == 0:
                await db.execute("""
                    INSERT OR IGNORE INTO tool_categories (tool_id, category_id, is_primary)
                    SELECT id, category_id, 1 FROM tools WHERE category_id IS NOT NULL
                """)
                await db.commit()
        except Exception:
            pass

        # Migration: add expanded v2 categories if missing
        for _cat_name, _cat_slug, _cat_desc, _cat_icon in [
            ("Database", "database", "Databases, ORMs, and data storage tools", ""),
            ("Headless CMS", "headless-cms", "API-first content management systems", ""),
            ("Media Server", "media-server", "Streaming, transcoding, and media management", ""),
            ("DevOps & Infrastructure", "devops-infrastructure", "CI/CD, containers, and infrastructure tools", ""),
            ("Security Tools", "security-tools", "Security scanning, encryption, and compliance", ""),
            ("Search Engine", "search-engine", "Full-text search, vector search, and indexing", ""),
            ("Message Queue", "message-queue", "Message brokers, event streaming, and async communication", ""),
            ("Testing Tools", "testing-tools", "Test automation, mocking, and QA tools", ""),
            ("Documentation", "documentation", "API docs, wikis, and knowledge bases", ""),
            ("CLI Tools", "cli-tools", "Command-line utilities and terminal tools", ""),
            ("Logging", "logging", "Log aggregation, analysis, and management", ""),
            ("Feature Flags", "feature-flags", "Feature toggles, A/B testing, and gradual rollouts", ""),
            ("Notifications", "notifications", "Push notifications, in-app messaging, and alerts", ""),
            ("Background Jobs", "background-jobs", "Task queues, cron jobs, and workflow orchestration", ""),
            ("Localization", "localization", "Translation, i18n, and multilingual content", ""),
        ]:
            try:
                await db.execute(
                    "INSERT INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
                    (_cat_name, _cat_slug, _cat_desc, _cat_icon),
                )
            except Exception:
                pass  # already exists
        await db.commit()

        # Migration: add v3 categories (frontend-frameworks, caching, mcp-servers, boilerplates, maps-location)
        for _cat_name, _cat_slug, _cat_desc, _cat_icon in [
            ("Frontend Frameworks", "frontend-frameworks", "JavaScript frameworks, UI libraries, bundlers, and state management tools", "🖥️"),
            ("Caching", "caching", "In-memory stores, caching layers, and key-value databases for high-performance apps", "⚡"),
            ("MCP Servers", "mcp-servers", "MCP server implementations that give AI agents access to tools, data, and services", "🧩"),
            ("Boilerplates", "boilerplates", "Starter kits, scaffold templates, and opinionated project starters to ship faster", "📦"),
            ("Maps & Location", "maps-location", "Maps, geolocation, geocoding, and location-based APIs", "🗺️"),
        ]:
            try:
                await db.execute(
                    "INSERT INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
                    (_cat_name, _cat_slug, _cat_desc, _cat_icon),
                )
            except Exception:
                pass  # already exists
        await db.commit()

        # Migration: add share_uuid to dependency_analyses
        try:
            await db.execute("ALTER TABLE dependency_analyses ADD COLUMN share_uuid TEXT")
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dep_analyses_uuid ON dependency_analyses(share_uuid)")
            await db.commit()
        except Exception:
            pass

        # Migration: add is_reference flag to tools (reference tools = registry-ingested, not shown in browse)
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN is_reference INTEGER DEFAULT 0")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tools_reference ON tools(is_reference)")
            await db.commit()
        except Exception:
            pass

        # Migration: visitor_id on search_logs for anonymous personalisation
        try:
            await db.execute("ALTER TABLE search_logs ADD COLUMN visitor_id TEXT")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_visitor ON search_logs(visitor_id)")
            await db.commit()
        except Exception:
            pass

        # Anonymous visitor profiles for silent personalisation
        await db.execute("""
            CREATE TABLE IF NOT EXISTS visitor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT NOT NULL UNIQUE,
                interests TEXT NOT NULL DEFAULT '{}',
                tech_stack TEXT NOT NULL DEFAULT '[]',
                favorite_tools TEXT NOT NULL DEFAULT '[]',
                search_count INTEGER NOT NULL DEFAULT 0,
                last_rebuilt_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_visitor_profiles_vid ON visitor_profiles(visitor_id)")
        await db.commit()

        # Manifest cooccurrence mining table (implicit compatibility pairs)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS manifest_cooccurrences (
                tool_a_slug TEXT NOT NULL,
                tool_b_slug TEXT NOT NULL,
                cooccurrence_count INTEGER DEFAULT 1,
                PRIMARY KEY (tool_a_slug, tool_b_slug)
            )
        """)
        await db.commit()

        # Migration paths mined from git history (GitHub Autopsy)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS migration_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_package TEXT NOT NULL,
                to_package TEXT NOT NULL,
                repo TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                committed_at TIMESTAMP,
                confidence TEXT NOT NULL DEFAULT 'swap'
                    CHECK(confidence IN ('swap', 'likely', 'inferred')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_package, to_package, repo, commit_sha)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_migration_from ON migration_paths(from_package)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_migration_to ON migration_paths(to_package)")

        # Verified package combinations (packages coexisting in real repos)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS verified_combos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_a TEXT NOT NULL,
                package_b TEXT NOT NULL,
                repo TEXT NOT NULL,
                repo_stars INTEGER DEFAULT 0,
                last_seen_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(package_a, package_b, repo)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_combos_a ON verified_combos(package_a)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_combos_b ON verified_combos(package_b)")

        # CI build outcomes reported by GitHub Action
        await db.execute("""
            CREATE TABLE IF NOT EXISTS build_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo TEXT NOT NULL,
                manifest_hash TEXT NOT NULL,
                packages_json TEXT NOT NULL,
                ci_passed INTEGER NOT NULL,
                action_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_repo ON build_outcomes(repo)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_hash ON build_outcomes(manifest_hash)")

        # Oracle API call log (x402 pay-per-call analytics)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS oracle_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                slug_a TEXT NOT NULL,
                slug_b TEXT NOT NULL,
                had_data INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_oracle_calls_created ON oracle_calls(created_at)")
        await db.commit()

        # Migration: track mid-trial citation nudge email (avoids duplicate sends)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN citation_trial_nudge_sent INTEGER DEFAULT 0")
            await db.commit()
        except Exception:
            pass

        # Migration: agent_services table for agent-to-agent procurement
        try:
            await db.execute("SELECT id FROM agent_services LIMIT 1")
        except Exception:
            await db.execute("""CREATE TABLE IF NOT EXISTS agent_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                tagline TEXT NOT NULL DEFAULT '',
                description TEXT,
                maker_id INTEGER REFERENCES makers(id),
                capability_tags TEXT NOT NULL DEFAULT '',
                category_id INTEGER REFERENCES categories(id),
                input_schema TEXT NOT NULL DEFAULT '{}',
                output_schema TEXT NOT NULL DEFAULT '{}',
                delivery_types TEXT NOT NULL DEFAULT 'inline_json',
                estimated_sla_minutes INTEGER NOT NULL DEFAULT 5,
                cost_estimate_cents INTEGER,
                cost_unit TEXT DEFAULT 'per_task',
                execution_endpoint TEXT,
                auth_token_hash TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                timeout_rate REAL DEFAULT 0.0,
                success_count INTEGER DEFAULT 0,
                timeout_count INTEGER DEFAULT 0,
                quality_score INTEGER DEFAULT 50,
                url TEXT,
                github_url TEXT,
                source_type TEXT DEFAULT 'saas',
                example_input TEXT DEFAULT '{}',
                example_output TEXT DEFAULT '{}',
                useful_count INTEGER DEFAULT 0,
                not_useful_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_services_status ON agent_services(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_services_capability ON agent_services(capability_tags)")

        # Migration: add new columns to agent_services if missing
        for _col, _ddl in [
            ("example_input", "ALTER TABLE agent_services ADD COLUMN example_input TEXT DEFAULT '{}'"),
            ("example_output", "ALTER TABLE agent_services ADD COLUMN example_output TEXT DEFAULT '{}'"),
            ("useful_count", "ALTER TABLE agent_services ADD COLUMN useful_count INTEGER DEFAULT 0"),
            ("not_useful_count", "ALTER TABLE agent_services ADD COLUMN not_useful_count INTEGER DEFAULT 0"),
        ]:
            try:
                await db.execute(f"SELECT {_col} FROM agent_services LIMIT 1")
            except Exception:
                await db.execute(_ddl)

        # Migration: agent_contracts table for agent-to-agent procurement
        try:
            await db.execute("SELECT id FROM agent_contracts LIMIT 1")
        except Exception:
            await db.execute("""CREATE TABLE IF NOT EXISTS agent_contracts (
                id TEXT PRIMARY KEY, host_user_id INTEGER, host_session_id TEXT,
                host_api_key_id INTEGER, hired_agent_slug TEXT NOT NULL,
                input_payload TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'pending',
                status_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivery_type TEXT, delivery_ref TEXT, delivery_metadata TEXT DEFAULT '{}',
                ttl_expires_at TIMESTAMP, sla_deadline_at TIMESTAMP,
                extended BOOLEAN DEFAULT 0, cost_estimate_cents INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, delivered_at TIMESTAMP,
                delivery_summary TEXT, outcome_useful INTEGER, outcome_notes TEXT,
                stripe_payment_intent_id TEXT, escrow_status TEXT
            )""")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_contracts_status ON agent_contracts(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_contracts_host ON agent_contracts(host_user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_contracts_session ON agent_contracts(host_session_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_contracts_agent ON agent_contracts(hired_agent_slug)")

        # Migration: add new columns to agent_contracts if missing
        for _col, _ddl in [
            ("delivery_summary", "ALTER TABLE agent_contracts ADD COLUMN delivery_summary TEXT"),
            ("outcome_useful", "ALTER TABLE agent_contracts ADD COLUMN outcome_useful INTEGER"),
            ("outcome_notes", "ALTER TABLE agent_contracts ADD COLUMN outcome_notes TEXT"),
        ]:
            try:
                await db.execute(f"SELECT {_col} FROM agent_contracts LIMIT 1")
            except Exception:
                await db.execute(_ddl)

        # Validation logs for guardrail endpoint
        await db.execute("""
            CREATE TABLE IF NOT EXISTS validation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package TEXT NOT NULL,
                ecosystem TEXT NOT NULL DEFAULT 'npm',
                pkg_exists BOOLEAN,
                is_typosquat BOOLEAN DEFAULT 0,
                risk_level TEXT DEFAULT 'unknown',
                source TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_validation_pkg ON validation_logs(package)")

        # Enrich well-known tools with structured metadata
        await _enrich_tool_metadata(db)

    finally:
        await db.close()


# ── Slug helper ───────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ── Event tracking ────────────────────────────────────────────────────────

async def track_event(db, event: str, visitor_id: str = None, user_id: int = None, metadata: dict = None):
    """Track a conversion/funnel event."""
    import json
    meta_str = json.dumps(metadata) if metadata else None
    await db.execute(
        "INSERT INTO events (event, visitor_id, user_id, metadata) VALUES (?, ?, ?, ?)",
        (event, visitor_id, user_id, meta_str)
    )
    await db.commit()


# ── Category queries ──────────────────────────────────────────────────────

_categories_cache: dict = {'data': None, 'expires': 0}
_tags_cache: dict = {'data': None, 'expires': 0}

async def get_all_categories(db: aiosqlite.Connection):
    now = _time.time()
    if _categories_cache['data'] is not None and now < _categories_cache['expires']:
        return _categories_cache['data']
    cursor = await db.execute(
        """SELECT c.*, (
               SELECT COUNT(*)
               FROM tools t
               WHERE t.category_id = c.id AND t.status = 'approved'
           ) as tool_count
           FROM categories c ORDER BY c.name"""
    )
    result = await cursor.fetchall()
    _categories_cache['data'] = result
    _categories_cache['expires'] = now + 300  # 5 min TTL
    return result


async def get_category_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute("SELECT * FROM categories WHERE slug = ?", (slug,))
    return await cursor.fetchone()


# ── Multi-category helpers ───────────────────────────────────────────────

async def get_tool_categories(db: aiosqlite.Connection, tool_id: int) -> list:
    """Get all categories for a tool (primary first, then secondary)."""
    cursor = await db.execute("""
        SELECT c.id, c.name, c.slug, tc.is_primary
        FROM tool_categories tc
        JOIN categories c ON c.id = tc.category_id
        WHERE tc.tool_id = ?
        ORDER BY tc.is_primary DESC, c.name
    """, (tool_id,))
    return await cursor.fetchall()


async def get_tool_categories_bulk(db: aiosqlite.Connection, tool_ids: list) -> dict:
    """Get all categories for multiple tools. Returns {tool_id: [category_rows]}."""
    if not tool_ids:
        return {}
    placeholders = ','.join('?' for _ in tool_ids)
    cursor = await db.execute(f"""
        SELECT tc.tool_id, c.id, c.name, c.slug, tc.is_primary
        FROM tool_categories tc
        JOIN categories c ON c.id = tc.category_id
        WHERE tc.tool_id IN ({placeholders})
        ORDER BY tc.is_primary DESC, c.name
    """, tool_ids)
    rows = await cursor.fetchall()
    result = {}
    for r in rows:
        result.setdefault(r['tool_id'], []).append(r)
    return result


async def set_tool_categories(db: aiosqlite.Connection, tool_id: int, primary_category_id: int,
                              secondary_category_ids: list = None):
    """Set all categories for a tool. Replaces existing entries."""
    await db.execute("DELETE FROM tool_categories WHERE tool_id = ?", (tool_id,))
    await db.execute(
        "INSERT INTO tool_categories (tool_id, category_id, is_primary) VALUES (?, ?, 1)",
        (tool_id, primary_category_id))
    for cat_id in (secondary_category_ids or []):
        if cat_id != primary_category_id:
            await db.execute(
                "INSERT OR IGNORE INTO tool_categories (tool_id, category_id, is_primary) VALUES (?, ?, 0)",
                (tool_id, cat_id))
    # Keep tools.category_id in sync
    await db.execute("UPDATE tools SET category_id = ? WHERE id = ?", (primary_category_id, tool_id))
    await db.commit()
    _categories_cache['data'] = None  # bust cache


async def add_secondary_category(db: aiosqlite.Connection, tool_id: int, category_id: int):
    """Add a secondary category to a tool."""
    await db.execute(
        "INSERT OR IGNORE INTO tool_categories (tool_id, category_id, is_primary) VALUES (?, ?, 0)",
        (tool_id, category_id))
    await db.commit()
    _categories_cache['data'] = None


# ── Tool queries ──────────────────────────────────────────────────────────

async def get_trending_tools(db: aiosqlite.Connection, limit: int = 6):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  (t.upvote_count) as rank_score,
                  EXISTS(SELECT 1 FROM maker_updates mu WHERE mu.tool_id = t.id AND mu.created_at >= datetime('now', '-14 days')) as has_changelog_14d,
                  CASE WHEN EXISTS(
                      SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                      WHERE u.maker_id = t.maker_id AND s.status = 'active'
                  ) THEN 1 ELSE 0 END AS maker_is_pro
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY t.quality_score DESC, t.created_at DESC LIMIT ?""",
        (limit,),
    )
    return await cursor.fetchall()


async def get_tools_by_category(db: aiosqlite.Connection, category_id: int, page: int = 1, per_page: int = 12):
    offset = (page - 1) * per_page
    cursor = await db.execute(
        """SELECT DISTINCT t.*, c.name as category_name, c.slug as category_slug,
                  CASE WHEN EXISTS(
                      SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                      WHERE u.maker_id = t.maker_id AND s.status = 'active'
                  ) THEN 1 ELSE 0 END AS maker_is_pro,
                  tc_match.is_primary as is_primary_in_category
           FROM tools t
           JOIN categories c ON t.category_id = c.id
           JOIN tool_categories tc_match ON tc_match.tool_id = t.id AND tc_match.category_id = ?
           WHERE t.status = 'approved'
           ORDER BY tc_match.is_primary DESC, t.quality_score DESC, t.github_stars DESC, t.upvote_count DESC
           LIMIT ? OFFSET ?""",
        (category_id, per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute(
        """SELECT COUNT(DISTINCT t.id) as cnt
           FROM tools t
           JOIN tool_categories tc ON tc.tool_id = t.id AND tc.category_id = ?
           WHERE t.status = 'approved'""", (category_id,)
    )
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


async def get_tool_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  m.indie_status, m.slug as maker_slug,
                  m.story_motivation, m.story_challenge, m.story_advice, m.story_fun_fact,
                  CASE WHEN EXISTS(
                      SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                      WHERE u.maker_id = t.maker_id AND s.status = 'active'
                  ) THEN 1 ELSE 0 END AS maker_is_pro
           FROM tools t JOIN categories c ON t.category_id = c.id
           LEFT JOIN makers m ON t.maker_id = m.id
           WHERE t.slug = ?
        """,
        (slug,),
    )
    return await cursor.fetchone()


async def get_tool_by_name_exact(db: aiosqlite.Connection, slug: str):
    """Case-insensitive exact name lookup — converts slug hyphens to spaces.

    Used as a last-resort fallback in slug resolution. Only returns approved tools.
    e.g. 'tailwind-css' → looks for name 'Tailwind CSS' (exact, case-insensitive).
    """
    name_guess = slug.replace("-", " ")
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  m.indie_status, m.slug as maker_slug,
                  m.story_motivation, m.story_challenge, m.story_advice, m.story_fun_fact,
                  CASE WHEN EXISTS(
                      SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                      WHERE u.maker_id = t.maker_id AND s.status = 'active'
                  ) THEN 1 ELSE 0 END AS maker_is_pro
           FROM tools t JOIN categories c ON t.category_id = c.id
           LEFT JOIN makers m ON t.maker_id = m.id
           WHERE LOWER(t.name) = LOWER(?) AND t.status = 'approved'
        """,
        (name_guess,),
    )
    return await cursor.fetchone()


async def get_related_tools(db: aiosqlite.Connection, tool_id: int, category_id: int, limit: int = 3):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  CASE WHEN EXISTS(
                      SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                      WHERE u.maker_id = t.maker_id AND s.status = 'active'
                  ) THEN 1 ELSE 0 END AS maker_is_pro
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.category_id = ? AND t.id != ? AND t.status = 'approved'
           ORDER BY t.upvote_count DESC LIMIT ?""",
        (category_id, tool_id, limit),
    )
    return await cursor.fetchall()


# ── Quality Score ─────────────────────────────────────────────────────────

def compute_quality_score(tool: dict) -> float:
    """Compute quality score (0–100) for a tool using multiplicative formula.
    Formula: completeness * (1 + engagement_boost) * health * 100
    """
    # Completeness (0.0–1.0)
    completeness = 0.0
    if len(str(tool.get('description') or '')) > 100:
        completeness += 0.25
    if str(tool.get('tags') or '').strip():
        completeness += 0.15
    if tool.get('maker_id') is not None:
        completeness += 0.25
    if len(str(tool.get('tagline') or '')) > 20:
        completeness += 0.10
    if str(tool.get('source_type') or '') in ('code', 'saas'):
        completeness += 0.10
    if str(tool.get('integration_python') or '').strip():
        completeness += 0.15

    # Engagement Boost (0.0–1.0)
    # Uses real usage signals: tool page views, outbound clicks, MCP agent views,
    # upvotes, and reviews. Views and clicks are the primary drivers since
    # upvotes and reviews are near-zero across the catalog.
    upvotes = int(tool.get('upvote_count') or 0)
    mcp_views = int(tool.get('mcp_view_count') or 0)
    review_count = int(tool.get('review_count') or 0)
    click_count = int(tool.get('click_count') or 0)
    view_count = int(tool.get('view_count') or 0)
    engagement = 0.0
    engagement += min(view_count / 200, 0.25)    # tool page views (78k total)
    engagement += min(click_count / 100, 0.25)    # outbound clicks (60k total)
    engagement += min(mcp_views / 50, 0.2)        # agent detail lookups
    engagement += min(upvotes / 10, 0.15)         # human upvotes
    engagement += min(review_count / 3, 0.15)     # reviews

    # Health (multiplier)
    health_status = str(tool.get('health_status') or 'unknown')
    if health_status == 'dead':
        dead_days = int(tool.get('dead_days') or 0)
        health = 0.0 if dead_days >= 7 else 1.0
    elif health_status == 'degraded':
        health = 0.3
    else:
        health = 1.0

    score = completeness * (1 + engagement) * health * 100
    return round(min(score, 100.0), 2)


async def recompute_all_quality_scores(db: aiosqlite.Connection) -> dict:
    """Recompute quality_score for all approved tools. Returns stats dict."""
    cursor = await db.execute("""
        SELECT t.*,
               COALESCE(r.review_count, 0) as review_count,
               COALESCE(oc.click_count, 0) as click_count,
               COALESCE(tv.view_count, 0) as view_count,
               CASE
                   WHEN t.health_status = 'dead' AND t.first_dead_at IS NOT NULL THEN
                       CAST(julianday('now') - julianday(t.first_dead_at) AS INTEGER)
                   ELSE 0
               END as dead_days
        FROM tools t
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as review_count FROM reviews GROUP BY tool_id
        ) r ON r.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as click_count FROM outbound_clicks GROUP BY tool_id
        ) oc ON oc.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as view_count FROM tool_views GROUP BY tool_id
        ) tv ON tv.tool_id = t.id
        WHERE t.status = 'approved'
    """)
    tools = await cursor.fetchall()

    total_score = 0.0
    updates = []
    for tool in tools:
        score = compute_quality_score(dict(tool))
        updates.append((score, tool['id']))
        total_score += score

    await db.executemany("UPDATE tools SET quality_score = ? WHERE id = ?", updates)
    await db.commit()

    count = len(updates)
    return {
        'updated': count,
        'avg_score': round(total_score / count, 1) if count else 0,
    }


async def auto_archive_dead_tools(db: aiosqlite.Connection) -> int:
    """Archive tools that have been dead for 30+ consecutive days. Returns count archived."""
    cursor = await db.execute("""
        UPDATE tools SET status = 'archived'
        WHERE status = 'approved'
          AND health_status = 'dead'
          AND first_dead_at IS NOT NULL
          AND first_dead_at < datetime('now', '-30 days')
    """)
    await db.commit()
    return cursor.rowcount


async def check_outcome_demotion(db: aiosqlite.Connection) -> int:
    """Demote tools with high agent failure rates to 'degraded' status. Returns count demoted."""
    # Check which outcome table exists
    cursor = await db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE '%outcome%'
        LIMIT 1
    """)
    table_row = await cursor.fetchone()
    if not table_row:
        return 0
    table_name = table_row[0]

    cursor = await db.execute(f"""
        SELECT tool_id,
               COUNT(*) as total_signals,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
        FROM [{table_name}]
        GROUP BY tool_id
        HAVING total_signals >= 10
    """)
    rows = await cursor.fetchall()
    demoted = 0
    for row in rows:
        success_rate = row['successes'] / row['total_signals'] if row['total_signals'] else 0
        if success_rate < 0.2:
            await db.execute(
                "UPDATE tools SET health_status = 'degraded' WHERE id = ? AND health_status != 'degraded'",
                (row['tool_id'],),
            )
            demoted += 1
    if demoted:
        await db.commit()
    return demoted


async def run_health_checks(db: aiosqlite.Connection, batch_size: int = 100) -> dict:
    """HTTP HEAD check on tools not checked in 24+ hours. Returns stats dict."""
    import httpx

    cursor = await db.execute("""
        SELECT id, url, health_status FROM tools
        WHERE status = 'approved'
          AND (last_health_check IS NULL OR last_health_check < datetime('now', '-24 hours'))
        ORDER BY last_health_check ASC NULLS FIRST
        LIMIT ?
    """, (batch_size,))
    tools = await cursor.fetchall()

    alive = 0
    dead = 0
    async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
        for tool in tools:
            new_status = 'dead'
            try:
                resp = await client.head(str(tool['url']))
                if resp.status_code < 400:
                    new_status = 'alive'
            except Exception:
                new_status = 'dead'

            if new_status == 'alive':
                alive += 1
                await db.execute(
                    "UPDATE tools SET health_status = 'alive', last_health_check = datetime('now'), first_dead_at = NULL WHERE id = ?",
                    (tool['id'],),
                )
            else:
                dead += 1
                # Set first_dead_at only on transition to dead (preserves consecutive dead tracking)
                await db.execute(
                    """UPDATE tools SET health_status = 'dead', last_health_check = datetime('now'),
                       first_dead_at = COALESCE(first_dead_at, datetime('now'))
                       WHERE id = ?""",
                    (tool['id'],),
                )

    await db.commit()
    return {'checked': len(tools), 'alive': alive, 'dead': dead}


async def run_github_health_checks(db_conn: aiosqlite.Connection, batch_size: int = 50) -> dict:
    """Check GitHub repos for maintenance signals: last commit, issues, archive status."""
    import httpx
    import os

    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # Get tools with GitHub URLs that haven't been checked recently
    cursor = await db_conn.execute("""
        SELECT id, github_url FROM tools
        WHERE status = 'approved'
          AND github_url IS NOT NULL AND github_url != ''
          AND (github_last_check IS NULL OR github_last_check < datetime('now', '-7 days'))
        ORDER BY github_last_check ASC NULLS FIRST
        LIMIT ?
    """, (batch_size,))
    tools = await cursor.fetchall()

    stats = {"checked": 0, "updated": 0, "errors": 0, "rate_limited": False}

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for tool in tools:
            tool_id = tool['id']
            github_url = tool['github_url']

            # Parse owner/repo from GitHub URL
            match = re.match(r'https?://github\.com/([^/]+)/([^/?#]+)', github_url)
            if not match:
                stats["errors"] += 1
                continue

            owner, repo = match.group(1), match.group(2).rstrip('.git')
            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            try:
                resp = await client.get(api_url, headers=headers)

                if resp.status_code == 403:
                    # Rate limited
                    stats["rate_limited"] = True
                    break

                if resp.status_code == 404:
                    # Repo deleted or renamed
                    await db_conn.execute(
                        "UPDATE tools SET github_last_check = datetime('now'), health_status = 'dead' WHERE id = ?",
                        (tool_id,),
                    )
                    stats["checked"] += 1
                    continue

                if resp.status_code != 200:
                    stats["errors"] += 1
                    continue

                data = resp.json()

                stars = data.get("stargazers_count", 0)
                open_issues = data.get("open_issues_count", 0)
                is_archived = 1 if data.get("archived", False) else 0
                language = data.get("language", "") or ""
                pushed_at = data.get("pushed_at", "")  # ISO 8601 timestamp

                await db_conn.execute("""
                    UPDATE tools SET
                        github_stars = ?,
                        github_open_issues = ?,
                        github_is_archived = ?,
                        github_language = ?,
                        github_last_commit = ?,
                        github_last_check = datetime('now')
                    WHERE id = ?
                """, (stars, open_issues, is_archived, language, pushed_at, tool_id))

                stats["updated"] += 1
                stats["checked"] += 1

            except Exception:
                stats["errors"] += 1

    await db_conn.commit()
    return stats


# ── Search ────────────────────────────────────────────────────────────────

# Maps query terms → category name fragment for engagement scoring boost.
# Needed because category names don't always contain the search term:
# "cron" → "background" matches "Background Jobs"; "checkout" → "payments" etc.
_CAT_SYNONYMS: dict[str, str] = {
    # Background jobs / task queues
    "cron": "background",
    "queue": "background",
    "worker": "background",
    "scheduler": "background",
    "scheduled": "background",
    "job": "background",
    "jobs": "background",
    "background": "background",     # "background jobs" direct term → LIKE '%background%' ✓
    "celery": "background",
    "sidekiq": "background",
    "bullmq": "background",
    # Auth synonyms
    "oauth": "authentication",
    "saml": "authentication",
    "sso": "authentication",
    "mfa": "authentication",
    "2fa": "authentication",
    "login": "authentication",
    "signup": "authentication",
    "session": "authentication",
    "jwt": "authentication",
    "passkey": "authentication",
    "passwordless": "authentication",
    # Payment synonyms
    "checkout": "payments",
    "billing": "payments",
    "subscription": "payments",
    "invoice": "invoicing",
    "receipt": "invoicing",
    # Email synonyms
    "smtp": "email",
    "newsletter": "email",
    "drip": "email",
    "transactional": "email",
    "sending": "email",
    "sendgrid": "email",
    "resend": "email",
    "mailgun": "email",
    # Database synonyms
    "db": "database",
    "postgres": "database",
    "mysql": "database",
    "mongodb": "database",
    "sqlite": "database",
    "orm": "database",
    "migration": "database",
    "prisma": "database",
    "drizzle": "database",
    # Monitoring synonyms
    "uptime": "monitoring",
    "alerting": "monitoring",
    # "logging"/"logs" → "logging" matches "Logging" category (not "Monitoring & Uptime")
    # Logging is a separate category with tools like Fluentd, Logrus, lnav
    "logging": "logging",
    "logs": "logging",
    "log": "logging",       # "log management", "log aggregation" → Logging category (not "Blog")
    "loki": "logging",
    "logtail": "logging",
    "logrus": "logging",
    "fluentd": "logging",
    "papertrail": "logging",
    "observability": "monitoring",
    "tracing": "monitoring",
    "apm": "monitoring",
    "sentry": "monitoring",
    "datadog": "monitoring",
    # Scheduling synonyms
    "booking": "scheduling",
    "calendar": "scheduling",
    "appointment": "scheduling",
    "availability": "scheduling",
    # File / storage synonyms
    "upload": "file",
    "s3": "file",
    "cdn": "devops",    # CDN → DevOps & Infrastructure (Cloudflare, BunnyCDN, Fastly live there)
    "media": "file",
    "assets": "file",
    # CMS synonyms
    "blog": "cms",
    "headless": "cms",
    "content": "cms",
    # Project management synonyms
    "kanban": "project",
    "todo": "project",
    "sprint": "project",
    "agile": "project",
    "scrum": "project",
    # API synonyms
    "webhook": "api",
    "webhooks": "api",   # plural form
    "rest": "api",
    "graphql": "api",
    "openapi": "api",
    "sdk": "api",
    "rate": "api",       # "rate limiting" → API Tools category
    # Message queue synonyms — "message" self-maps so "message queue" query gets correct boost
    # ("queue" singular stays mapped to "background" above for job queue queries)
    # "event" → "message" so "event streaming queue" gets Message Queue boost, not Media Server
    # (scan order: "event" is checked before "streaming" → "media")
    "event": "message",
    "events": "message",
    "message": "message",
    "queues": "message",
    "pubsub": "message",
    "kafka": "message",
    "rabbitmq": "message",
    "nats": "message",
    "websocket": "message",  # WebSocket servers (Soketi, Centrifugo) live in Message Queue
    "websockets": "message",
    # AI synonyms
    "llm": "ai",
    "gpt": "ai",
    "claude": "ai",
    "openai": "ai",
    "langchain": "ai",
    "agent": "ai",
    "mcp": "mcp",       # "mcp server", "mcp tool" → "MCP Servers" category (LIKE '%mcp%')
    "rag": "ai",
    "embedding": "ai",
    "embeddings": "ai",
    # Vector databases (stored under database category)
    "vector": "database",
    # Direct category name fragments (for non-first-position terms like "self hosted auth")
    "auth": "authentication",
    "authentication": "authentication",
    "payment": "payments",
    "pay": "payments",
    "email": "email",
    "emails": "email",
    "monitor": "monitoring",
    "monitoring": "monitoring",
    "analytics": "analytics",
    "database": "database",
    "storage": "file",
    # "search" is now a valid FTS term (removed from _FTS_STOP_WORDS).
    # The category "Search Engine" contains "search" so LIKE matching works directly.
    "search": "search",
    "notification": "notifications",
    "notifications": "notifications",
    "push": "notifications",
    "sms": "notifications",
    "otp": "authentication",
    "totp": "authentication",
    # "chat" has no dedicated category — map to "customer" for Customer Support boost
    # (live chat tools like Crisp, Tawk.to, Chatwoot live there)
    "chat": "customer",
    "cms": "cms",
    "testing": "testing",
    "test": "testing",
    "qa": "testing",
    "e2e": "testing",
    "coverage": "testing",
    "mock": "testing",
    "mocking": "testing",
    "cypress": "testing",
    "playwright": "testing",
    "jest": "testing",
    "vitest": "testing",
    "selenium": "testing",
    "storybook": "testing",     # component testing / UI development
    "ci": "devops",
    "cicd": "devops",
    "deploy": "devops",
    "deployment": "devops",
    "hosting": "devops",
    "form": "forms",
    "forms": "forms",
    "survey": "forms",
    "surveys": "forms",
    "typeform": "forms",
    "tally": "forms",
    # Customer support
    "helpdesk": "support",
    "ticketing": "support",
    "support": "support",
    "intercom": "support",
    "zendesk": "support",
    "freshdesk": "support",
    "crisp": "support",
    # "feature-flags" won't LIKE-match "Feature Flags" category name — use "feature" instead
    "feature": "feature",
    "flags": "feature",
    "flag": "feature",
    "toggle": "feature",        # "feature toggle" queries
    "toggles": "feature",
    "experiment": "feature",    # "a/b experiment" / "experimentation platform"
    "error": "monitoring",
    "errors": "monitoring",
    "video": "media",
    "maps": "maps",
    "map": "maps",
    "geo": "maps",
    "location": "maps",
    "serverless": "devops",
    # Caching → moved to dedicated section below (caching category now exists)
    # Named tools → their primary category (fixes "[tool] alternative" queries so
    # the category/tag boost targets the RIGHT category instead of tools tagged
    # with the target tool name, which are complements not alternatives)
    # Payment processors
    "stripe": "payments",
    "paddle": "payments",
    "paypal": "payments",
    "lemonsqueezy": "payments",
    "gumroad": "payments",
    "braintree": "payments",
    # Auth providers
    "clerk": "authentication",
    "auth0": "authentication",
    "okta": "authentication",
    "keycloak": "authentication",
    "supertokens": "authentication",
    "zitadel": "authentication",
    # Databases / BaaS
    "supabase": "database",
    "firebase": "database",
    "neon": "database",
    "planetscale": "database",
    "cockroachdb": "database",
    "dynamodb": "database",
    # Hosting / DevOps
    "vercel": "devops",
    "netlify": "devops",
    "railway": "devops",
    "render": "devops",
    "heroku": "devops",
    "fly.io": "devops",
    # Email / messaging
    "mailchimp": "email",
    "postmark": "email",
    "mailerlite": "email",
    "convertkit": "email",
    "twilio": "notifications",
    "vonage": "notifications",
    "novu": "notifications",         # Novu — open-source multi-channel notification platform
    "knock": "notifications",        # Knock — notification infrastructure API
    "onesignal": "notifications",    # OneSignal — push + in-app + email notifications
    "courier": "notifications",      # Courier — multi-channel notification routing
    "fcm": "notifications",          # Firebase Cloud Messaging — Android/web push
    "apns": "notifications",         # Apple Push Notification Service — iOS push
    # WebRTC — real-time video/audio, routes to api-tools (Livekit, Partykit, Daily.co)
    "webrtc": "api",                 # WebRTC queries — real-time video/audio API tools
    # Monitoring / observability
    "newrelic": "monitoring",
    "pagerduty": "monitoring",
    # Search
    "algolia": "search",
    "elasticsearch": "search",
    "meilisearch": "search",
    # Search query modifiers — "semantic search", "fuzzy search", "faceted search"
    # all have "search" stripped as stop word; the remaining term must still map to Search category
    "semantic": "search",
    "fuzzy": "search",
    "faceted": "search",
    "indexing": "search",
    "fulltext": "search",
    # CMS
    "contentful": "cms",
    "strapi": "cms",
    "sanity": "cms",
    "directus": "cms",
    # Analytics — "metrics dashboard", "metrics tracking" etc.
    "mixpanel": "analytics",
    "amplitude": "analytics",
    "segment": "analytics",
    "posthog": "analytics",
    "plausible": "analytics",
    "fathom": "analytics",
    "metrics": "analytics",
    "dashboard": "analytics",
    "dashboards": "analytics",
    # DevOps/Infrastructure — docker/k8s queries get category boost
    "docker": "devops",
    "kubernetes": "devops",
    "k8s": "devops",
    "container": "devops",
    "containers": "devops",
    "vpc": "devops",
    # Monitoring extras — crash reporting, exception tracking
    "crash": "monitoring",
    "exception": "monitoring",
    "exceptions": "monitoring",
    # Vector databases
    "qdrant": "database",
    "weaviate": "database",
    "chroma": "database",
    "pinecone": "database",
    "milvus": "database",
    # AI dev tools
    "cursor": "ai",
    "windsurf": "ai",
    "copilot": "ai",
    "linear": "project",
    # Background job tools
    "trigger.dev": "background",
    # Code quality / linting — ESLint, Biome, Prettier live in testing-tools category
    "lint": "testing",          # "linting tool", "js linter" → Testing Tools
    "linting": "testing",
    "eslint": "testing",        # ESLint — most popular JS/TS linter
    "biome": "testing",         # Biome — fast linter + formatter (Rome successor)
    "prettier": "testing",      # Prettier — opinionated code formatter
    # Observability — OpenTelemetry is the dominant standard
    "opentelemetry": "monitoring",   # full name
    "otel": "monitoring",            # short form used in queries
    "jaeger": "monitoring",          # Jaeger — distributed tracing (OTel-compatible)
    "zipkin": "monitoring",          # Zipkin — distributed tracing system
    # Data visualization / charting
    "charting": "analytics",    # "charting library" → Analytics & Metrics
    "charts": "analytics",      # "charts library", "charts component"
    "chart": "analytics",       # "chart.js", "chart library"
    "recharts": "analytics",    # Recharts — React charting library
    "plotly": "analytics",      # Plotly — interactive scientific charts
    "chartjs": "analytics",     # Chart.js — simple canvas charts
    # PDF generation / processing
    "pdf": "file",              # PDFKit, Puppeteer PDF, WeasyPrint → file-management
    # Markdown processing — editors, renderers, parsers
    "markdown": "documentation", # markdown editors/renderers → Documentation category
    # Security tools — "security" as raw term already LIKE-matches "Security Tools",
    # but named tools and non-obvious terms need explicit mapping
    "security": "security",
    "vulnerability": "security",
    "pentest": "security",
    "firewall": "security",
    "waf": "security",
    "snyk": "security",
    "sonarqube": "security",
    "vault": "security",        # HashiCorp Vault — secrets management
    "secrets": "security",
    "secret": "security",       # singular form — "secret management", "secret store"
    "envvars": "security",      # "envvars management" → same
    "dotenv": "developer",      # dotenv — .env file loader library → Developer Tools category
    # Invoicing — "invoice"/"receipt" already mapped above (line ~2295); add named tools + new terms
    "invoicing": "invoicing",
    "accounting": "invoicing",
    "freshbooks": "invoicing",
    "xero": "invoicing",
    "wave": "invoicing",
    # Media/uploads — image and audio are common queries beyond just "video"
    "image": "media",
    "audio": "media",
    "cloudinary": "media",
    "transcoding": "media",
    "streaming": "media",
    # Frontend frameworks / bundlers / state management / CSS
    # "state management" → first meaningful term is "state" → frontend-frameworks category
    # "react framework" → "react" is also in _FRAMEWORK_QUERY_TERMS but falls back to _meaningful
    # when stripped list is empty, so this synonym still fires correctly.
    "react": "frontend",
    "reactjs": "frontend",
    "vue": "frontend",
    "vuejs": "frontend",
    "svelte": "frontend",
    "sveltekit": "frontend",
    "angular": "frontend",
    "nextjs": "frontend",
    "nuxt": "frontend",
    "astro": "frontend",
    "remix": "frontend",
    "state": "frontend",
    "manager": "frontend",     # "state manager" → "state" or "manager" both map to frontend
    "bundler": "frontend",
    "build": "frontend",           # "build tool" → first term "build" → frontend-frameworks
    "vite": "frontend",
    # CSS frameworks/libraries
    "css": "frontend",
    "tailwind": "frontend",
    "tailwindcss": "frontend",
    "bootstrap": "frontend",
    "shadcn": "frontend",
    "daisyui": "frontend",
    "bulma": "frontend",
    "styling": "frontend",
    "stylesheet": "frontend",
    "rollup": "frontend",
    "parcel": "frontend",
    "turbopack": "frontend",
    "esbuild": "frontend",
    "webpack": "frontend",
    "zustand": "frontend",
    "mobx": "frontend",
    "jotai": "frontend",
    "redux": "frontend",
    "recoil": "frontend",
    "xstate": "frontend",       # State machines
    "nanostores": "frontend",
    "htmx": "frontend",         # HTMX — HTML-first interactivity
    "alpine": "frontend",       # Alpine.js — lightweight JS framework
    "alpinejs": "frontend",
    "preact": "frontend",       # Preact — lightweight React alternative
    "lit": "frontend",          # Lit — web components library
    "solidjs": "frontend",      # SolidJS — reactive UI library
    "stencil": "frontend",      # Stencil — web components compiler
    "ember": "frontend",        # Ember.js
    # API tools — routing, RPC, gateways
    "trpc": "api",              # tRPC — type-safe API layer
    "gateway": "api",           # API gateway queries
    # Realtime / WebSockets — typically API-layer tools (Pusher, Ably, PartyKit)
    "realtime": "api",
    "real": "api",              # "real-time" → hyphen stripped → "real" + "time" → catches realtime queries
    "time": "api",              # "real-time" hyphen-split → "time" reinforces realtime→api routing
    "limiting": "api",          # "rate limiting" → "rate" already maps to api, "limiting" reinforces it
    "limiter": "api",           # "rate limiter" → both "rate" and "limiter" map to api
    # websocket→message (moved from "api": WebSocket servers like Soketi/Centrifugo
    # are message queue tools; Message Queue cat match outranks API testing tools)
    # "websocket": "api" was previously here — removed to fix ranking
    "sse": "api",               # Server-Sent Events
    "pusher": "api",
    "ably": "api",
    "livekit": "api",           # WebRTC / realtime video
    "partykit": "api",
    # Caching — dedicated category now exists
    "caching": "caching",
    "cache": "caching",
    "memcached": "caching",
    "upstash": "caching",
    "dragonfly": "caching",     # Redis-compatible, faster
    "keydb": "caching",
    "redis": "caching",         # Redis is the canonical caching tool (overrides earlier "database" entry)
    # Boilerplates / starter kits
    "boilerplate": "boilerplate",
    "starter": "boilerplate",
    "scaffold": "boilerplate",
    "template": "boilerplate",
    # MCP servers — dedicated category
    "protocol": "mcp",          # "model context protocol" → first term after stop words
    # Frontend frameworks — named tools missing from earlier pass
    "tanstack": "frontend",     # TanStack Query, TanStack Router, TanStack Table
    "radix": "frontend",        # Radix UI primitives
    # UI components / design systems
    "ui": "frontend",           # "UI component library", "UI kit", "UI framework"
    "component": "frontend",    # "component library" — library is a stop word, component stays
    "components": "frontend",   # plural form
    # Animation libraries
    "animation": "frontend",    # Framer Motion, GSAP, Motion.dev, Anime.js
    "animate": "frontend",      # "animate.css", "animate on scroll"
    # Icon libraries
    "icon": "frontend",         # "icon library" — Lucide Icons, Heroicons, Phosphor
    "icons": "frontend",        # plural form
    # Access control (RBAC, fine-grained permissions)
    "rbac": "authentication",   # role-based access control
    "permission": "authentication",   # "permissions management", "fine-grained permission"
    "permissions": "authentication",  # plural
    "access": "authentication",       # "access control", "access management"
    # Internationalisation / localisation — dedicated "Localization" category exists
    # LIKE '%localization%' matches category name "Localization" ✓
    "i18n": "localization",
    "l10n": "localization",
    "translate": "localization",
    "translation": "localization",      # "translation library", "translation API"
    "locale": "localization",           # "locale formatting", "locale config"
    "locales": "localization",
    "localization": "localization",
    "internationalization": "localization",
    "crowdin": "localization",          # Crowdin — i18n platform
    "weblate": "localization",          # Weblate — self-hosted translation
    # CLI tools — "CLI Tools" category name, LIKE '%cli%' matches ✓
    "commandline": "cli",
    "terminal": "cli",
    "shell": "cli",
    "tui": "cli",                       # Terminal UI tools
    # Documentation — "Documentation" category, LIKE '%documentation%' matches ✓
    "docs": "documentation",
    "wiki": "documentation",
    "readme": "documentation",
    "docusaurus": "documentation",
    "mkdocs": "documentation",
    "gitbook": "documentation",
    "swagger": "documentation",
    "mintlify": "documentation",
    # Workflow / automation (n8n, Make.com, Zapier)
    "workflow": "ai",           # "workflow automation" — n8n, Make, Zapier live in ai-automation
    # JS/TS build ecosystem — transpilers and runtimes
    "babel": "frontend",        # Babel — JS transpiler (legacy + modern)
    "transpiler": "frontend",   # generic transpiler queries
    "swc": "frontend",          # SWC — Rust-based JS/TS transpiler (used by Next.js, Vite)
    "bun": "frontend",          # Bun — fast JS runtime + bundler + test runner
    "deno": "frontend",         # Deno — secure JS/TS runtime (Deno 2)
    # "management" catches "state management" where "state" is not the first meaningful term
    "management": "frontend",   # "state management tool"
    # Node.js / edge web frameworks — for "[framework] alternative" queries
    "hono": "api",              # Hono — ultrafast edge web framework (Cloudflare, Deno, Bun)
    "express": "api",           # Express.js — classic Node.js web framework
    "nestjs": "api",            # NestJS — TypeScript enterprise Node.js framework
    "koa": "api",               # Koa — minimalist Node.js middleware framework
    # DevOps / tunneling / IaC
    "tunnel": "devops",         # "dev tunnel", "local tunnel" (ngrok, cloudflare tunnel)
    "tunneling": "devops",      # explicit form
    "ngrok": "devops",          # ngrok — localhost tunneling tool
    "terraform": "devops",      # Terraform — infrastructure as code
    "pulumi": "devops",         # Pulumi — IaC with real programming languages
    "ansible": "devops",        # Ansible — configuration management
    # Database — BaaS / cloud tools in TECH_KEYWORDS but missing category synonym boost
    "turso": "database",        # Turso — distributed libSQL (serverless SQLite)
    "convex": "database",       # Convex — real-time BaaS with reactive queries
    "pocketbase": "database",   # PocketBase — SQLite-based open-source BaaS
    "appwrite": "database",     # Appwrite — self-hosted Firebase alternative
    "libsql": "database",       # libSQL — open-source fork of SQLite (powers Turso)
    "surrealdb": "database",    # SurrealDB — multi-model DB (SQL + graph + document + KV)
    "webauthn": "authentication",   # WebAuthn — W3C passkey standard
    "fido2": "authentication",      # FIDO2 — underlying passkey protocol
    # Security — compliance, encryption, certificates
    "compliance": "security",   # GDPR/SOC2 compliance tooling
    "gdpr": "security",         # GDPR compliance tools
    "encryption": "security",   # encryption libraries and key management
    "ssl": "security",          # SSL certificate management
    "tls": "security",          # TLS configuration tools
    # Frontend rendering patterns — SSR/SSG/PWA/SPA (common agent query terms)
    "ssr": "frontend",          # Server-Side Rendering (Next.js, SvelteKit, Nuxt)
    "ssg": "frontend",          # Static Site Generation (Astro, Eleventy, Jekyll)
    "pwa": "frontend",          # Progressive Web Apps (Workbox, Vite PWA plugin)
    "spa": "frontend",          # Single Page Applications (React, Vue, Angular)
    # Reverse proxy / web server / load balancer tools
    "proxy": "devops",          # "reverse proxy" → DevOps & Infrastructure
    "reverse": "devops",        # "reverse proxy" — "reverse" not a common stop-word here
    "nginx": "devops",          # Nginx — most popular web server / reverse proxy
    "traefik": "devops",        # Traefik — cloud-native reverse proxy
    "caddy": "devops",          # Caddy — automatic HTTPS web server
    "loadbalancer": "devops",   # load balancer tools
    "haproxy": "devops",        # HAProxy — high-availability load balancer
    # API layer — CORS and middleware
    "cors": "api",              # "CORS middleware", "CORS header" → API Tools
    "middleware": "api",        # "API middleware", "Express middleware" → API Tools
    # Package managers — JS ecosystem
    "yarn": "frontend",         # Yarn — fast npm-compatible package manager
    "pnpm": "frontend",         # pnpm — efficient disk-space-saving package manager
    # Monorepo tooling
    "monorepo": "developer",    # "monorepo build" → Developer Tools (Turborepo, Nx, Lerna)
    # Database — SQL / NoSQL query patterns
    "nosql": "database",        # "nosql database", "nosql store" queries
    "sql": "database",          # raw "sql" queries (not ORM-specific)
    # Frontend — WebAssembly
    "wasm": "frontend",         # WebAssembly queries (wasm-pack, wasm-bindgen)
    "webassembly": "frontend",  # full form of WebAssembly
    # Frontend — reactivity signals pattern (Angular, SolidJS, Vue)
    "signal": "frontend",       # "signal-based reactivity", "signal state"
    "signals": "frontend",      # plural form — common in Angular 17+ / SolidJS docs
    # Testing — additional patterns
    "fixture": "testing",       # "test fixture" — pytest fixtures, testing factory patterns
    "snapshot": "testing",      # "snapshot testing" — Jest / Vitest snapshots
    "benchmark": "testing",     # "benchmark tool" — k6, Vitest bench, hyperfine
    "benchmarking": "testing",  # explicit form
    # Auth libraries (named tools missing from earlier pass)
    "lucia": "authentication",        # Lucia Auth — lightweight auth library
    "betterauth": "authentication",   # Better Auth — modern TypeScript auth framework
    "oidc": "authentication",         # OpenID Connect — identity protocol (Zitadel, Keycloak)
    "oauth2": "authentication",       # explicit OAuth 2.0 queries
    "nextauth": "authentication",     # NextAuth.js — most popular Next.js auth library (26k★)
    "next-auth": "authentication",    # hyphenated canonical package name (@auth/nextjs)
    "passport": "authentication",     # Passport.js — classic Node.js auth middleware (23k★)
    "passportjs": "authentication",   # compound form used in queries like "passportjs alternative"
    # CMS — popular tools not yet mapped
    "payload": "cms",                 # PayloadCMS — TypeScript headless CMS (32k stars)
    "ghost": "cms",                   # Ghost — open-source publishing/CMS
    "wordpress": "cms",               # WordPress — headless WP queries
    "keystonejs": "cms",              # KeystoneJS — Node.js headless CMS
    # Database — OLAP, graph, time-series
    "clickhouse": "database",         # ClickHouse — fast OLAP database
    "neo4j": "database",              # Neo4j — graph database
    "graph": "database",              # "graph database" queries (Neo4j, Amazon Neptune)
    "timescale": "database",          # TimescaleDB — time-series PostgreSQL extension
    "timescaledb": "database",        # explicit form
    # Caching — Redis fork/alternatives
    "valkey": "caching",              # Valkey — Linux Foundation Redis fork
    # Testing — headless browser + load testing + mocking
    "puppeteer": "testing",           # Puppeteer — headless Chrome automation
    "k6": "testing",                  # k6 — load testing tool (Grafana)
    "webdriverio": "testing",         # WebdriverIO — cross-browser test automation
    # DevOps — deployment / self-hosting tools
    "kamal": "devops",                # Kamal — Rails/Docker deployment (by Basecamp)
    "coolify": "devops",              # Coolify — self-hosted Heroku/Netlify alternative
    "fly": "devops",                  # short form of "fly.io" in queries
    # Frontend — modern frameworks not yet covered
    "qwik": "frontend",               # Qwik — resumable JavaScript framework
    "million": "frontend",            # Million.js — React performance compiler
    # Security — static/dynamic analysis
    "sast": "security",               # static application security testing
    "dast": "security",               # dynamic application security testing
    "owasp": "security",              # OWASP tooling (OWASP ZAP, OWASP Top 10)
    # Rate limiting — complement to "rate"→"api", "limiting"→"api", "limiter"→"api"
    "limit": "api",              # "rate limit" → both "rate" and "limit" reinforce api routing
    # Headless browser / browser automation
    "browser": "testing",        # "headless browser", "browser automation" → Testing Tools
    # Microservices — common query pattern for API/service layer tools
    "microservice": "api",       # "microservice framework" → API Tools (Hono, Express, Fastify)
    "microservices": "api",      # plural form — "microservices architecture", "microservices pattern"
    # SolidJS — "solid" alone commonly used ("solid alternative", "solid vs react")
    "solid": "frontend",         # SolidJS — fine-grained reactivity UI library
    # Rich text editors / WYSIWYG — Tiptap, Quill, Slate.js, Lexical, ProseMirror, CodeMirror
    "wysiwyg": "frontend",       # "wysiwyg editor" queries
    "tiptap": "frontend",        # Tiptap — ProseMirror-based rich text editor for Vue/React
    "lexical": "frontend",       # Lexical — Meta's extensible text editor framework
    "codemirror": "frontend",    # CodeMirror — browser-based code editor widget
    "monaco": "frontend",        # Monaco Editor — VS Code's editor (used in browser IDEs)
    "prosemirror": "frontend",   # ProseMirror — toolkit for rich text editors (Tiptap base)
    "quill": "frontend",         # Quill.js — popular open-source rich text editor
    # CAPTCHA / bot protection — hCaptcha, reCAPTCHA, Cloudflare Turnstile, Arkose
    "captcha": "security",       # "captcha widget", "captcha alternative" queries
    "recaptcha": "security",     # Google reCAPTCHA queries
    "hcaptcha": "security",      # hCaptcha — privacy-friendly reCAPTCHA alternative
    "turnstile": "security",     # Cloudflare Turnstile — invisible bot protection
    # Client-side routing libraries (React Router, TanStack Router, Vue Router)
    "routing": "frontend",       # "routing library", "client-side routing", "file-based routing"
    "router": "frontend",        # "react router", "client router", "frontend router"
    # Rails/Laravel server-rendered JS frameworks
    "livewire": "frontend",      # Laravel Livewire — reactive PHP components
    "hotwire": "frontend",       # Rails Hotwire — HTML-over-the-wire framework
    "stimulus": "frontend",      # Stimulus.js — modest JS framework (Hotwire)
    # Drag and drop libraries (dnd-kit, react-beautiful-dnd, Sortable.js)
    "drag": "frontend",          # "drag and drop", "drag to reorder" → Frontend Frameworks
    "dnd": "frontend",           # dnd-kit abbreviation — common in React drag-and-drop queries
    # Backend web frameworks — "fastapi alternative", "django orm", "rails framework" etc.
    # All route to api-tools where backend frameworks and their indie alternatives live
    "fastapi": "api",       # FastAPI — high-performance Python async web framework
    "django": "api",        # Django — batteries-included Python web framework
    "flask": "api",         # Flask — lightweight Python WSGI micro-framework
    "rails": "api",         # Ruby on Rails — full-stack MVC framework
    "laravel": "api",       # Laravel — PHP MVC web framework
    "gin": "api",           # Gin — high-performance Go HTTP framework
    "axum": "api",          # Axum — modular Rust web framework (Tokio team)
    # Monorepo tooling
    "turborepo": "developer",   # Turborepo — Vercel high-performance monorepo build system
    "nx": "developer",          # Nx — monorepo platform from Nrwl
    # Schema validation — Zod, Yup, Valibot all live in developer-tools category
    "validation": "developer",  # "schema validation", "runtime validation", "form validation"
    "zod": "developer",          # Zod — TypeScript-first schema validation (34k stars)
    "yup": "developer",          # Yup — popular JS/TS schema validation (22k stars)
    "valibot": "developer",      # Valibot — lightweight modular Zod alternative
    # Additional backend web frameworks (new Apr 2026)
    "gorilla": "api",           # Gorilla Mux — Go HTTP router
    "fastify": "api",           # Fastify — fast Node.js web framework
    # Realtime — Socket.io is the most-searched realtime tool, "socket" alone commonly used
    "socket": "api",            # "socket server", "socket.io alternative" → API Tools
    "socketio": "api",          # explicit Socket.io queries
    # Frontend — theming / dark mode libraries (next-themes, theme-ui, Arco Design)
    "theme": "frontend",        # "theme provider", "theming library", "theme switcher"
    "dark": "frontend",         # "dark mode library", "dark mode toggle" — next-themes, shadcn
    # Email — MJML and React Email are common template-layer tools
    "mjml": "email",            # MJML — responsive email template language
    "react-email": "email",     # React Email — React components for email templates
    # Frontend — Formik (popular React form library, Zod/RHF complement)
    "formik": "frontend",       # Formik — React form library (pre-RHF era, still widely used)
    # Database — connection pooling (PgBouncer, PgCat, pgpool)
    "pgbouncer": "database",    # PgBouncer — lightweight PostgreSQL connection pooler
    "pgcat": "database",        # PgCat — high-performance Postgres pooler + router
    "pooling": "database",      # "connection pooling", "db pooling" → Database category
    # API — GraphQL engines (Hasura, PostGraphile auto-generate APIs from database schemas)
    "hasura": "api",            # Hasura — instant GraphQL API over PostgreSQL/MySQL
    "postgraphile": "api",      # PostGraphile — GraphQL from PostgreSQL schema
    # Search — Typesense is a common Algolia alternative query term
    "typesense": "search",      # Typesense — typo-tolerant open-source search engine
    # DevOps — IaC abbreviation (often used standalone in queries)
    "iac": "devops",                 # Infrastructure as Code — Terraform, Pulumi, Ansible
    # File storage — object/blob storage queries (Cloudflare R2, Azure Blob, Vercel Blob)
    "blob": "file",                  # "blob storage", "Azure Blob" → File Management
    "r2": "file",                    # Cloudflare R2 — S3-compatible object storage
    "object": "file",                # "object storage" — R2, MinIO, Tigris, Backblaze B2
    # Auth — enterprise directory / SSO providers not yet mapped
    "workos": "authentication",      # WorkOS — enterprise SSO, SCIM, and Directory Sync
    # Security — secrets management (Infisical, Doppler, Bitwarden)
    "infisical": "security",         # Infisical — open-source secrets manager
    "doppler": "security",           # Doppler — env and secrets management platform
    "bitwarden": "security",         # Bitwarden — open-source password/secrets manager
    # API / Realtime — collaborative realtime (CRDT-based)
    "liveblocks": "api",             # Liveblocks — collaborative realtime infrastructure
    "yjs": "api",                    # Y.js — CRDT-based collaborative realtime framework
    # Forms — React Hook Form abbreviation
    "rhf": "forms",                  # RHF — shorthand for React Hook Form in queries
    # Database — local-first / WebAssembly database tools
    "electric": "database",          # ElectricSQL — local-first Postgres sync (electric-sql)
    "electricsql": "database",       # explicit form of ElectricSQL
    "pglite": "database",            # PGlite — Postgres compiled to WASM (runs in browser)
    # Feature flags — named tools in DB but missing from synonyms
    "unleash": "feature",            # Unleash — open-source feature management platform
    "flagsmith": "feature",          # Flagsmith — open-source feature flags + remote config
    "flipt": "feature",              # Flipt — open-source, git-backed feature flags
    "growthbook": "feature",         # GrowthBook — open-source A/B testing + feature flags
    # Frontend — Rspack (Rust webpack replacement by ByteDance/Web Infra team)
    "rspack": "frontend",            # Rspack — Rust-based webpack-compatible bundler
    # DevOps — dependency update automation
    "renovate": "devops",            # Renovate — automated dependency update PRs
    # Testing — visual regression for Storybook CI
    "chromatic": "testing",          # Chromatic — visual testing and review tool for Storybook
    # AI dev tools — Google's open Agent-to-Agent protocol
    "a2a": "ai",                     # A2A (Agent2Agent) — Google's open agent interop protocol
    # DevOps — monorepo release and changelog management
    "changesets": "devops",          # Changesets — monorepo versioning and changelog automation
    # Frontend — Angular meta-framework (file-based routing + SSR for Angular)
    "analog": "frontend",            # Analog — Angular meta-framework (Next.js for Angular)
    # AI agent frameworks — increasingly common in developer queries
    "llamaindex": "ai",              # LlamaIndex — RAG + data framework for LLM apps
    "litellm": "ai",                 # LiteLLM — unified proxy for 100+ LLM providers
    "crewai": "ai",                  # CrewAI — multi-agent role-based framework
    "autogen": "ai",                 # AutoGen (Microsoft) — conversational multi-agent
    "dspy": "ai",                    # DSPy (Stanford) — programming model for LM pipelines
    "smolagents": "ai",              # SmolAgents (HuggingFace) — minimal agentic framework
    # DevOps — Kubernetes ecosystem tools
    "helm": "devops",               # Helm — Kubernetes package manager (charts)
    "argocd": "devops",             # Argo CD — GitOps continuous delivery for Kubernetes
    "fluxcd": "devops",             # Flux CD — GitOps operator for Kubernetes
    # Background / workflow orchestration
    "dagster": "background",         # Dagster — data pipeline + asset-based orchestration
    "prefect": "background",         # Prefect — modern Python workflow orchestration
    "airflow": "background",         # Apache Airflow — DAG-based workflow scheduler
    # API protocol — gRPC / Protobuf
    "grpc": "api",                   # gRPC — high-performance RPC framework
    "protobuf": "api",               # Protocol Buffers — binary serialization by Google
    # Programming language routing — "python web framework", "go http framework" etc.
    # These route generic language queries to the category where indie frameworks live.
    "python": "api",           # Python framework queries → api-tools (FastAPI, Django, Flask)
    "go": "api",               # Go HTTP framework queries → api-tools (Gin, Fiber, Echo)
    "golang": "api",           # explicit form — "golang web framework"
    "rust": "api",             # Rust web framework queries → api-tools (Axum, Actix-web)
    "actix": "api",            # Actix-web — most popular Rust HTTP framework
    "echo": "api",             # Echo — fast Go web framework (2nd after Gin)
    "chi": "api",              # Chi — lightweight Go HTTP router
    "fiber": "api",            # Fiber — Express-inspired Go web framework
    "ruby": "api",             # Ruby framework queries → api-tools (Rails, Sinatra, Hanami)
    "java": "api",             # Java framework queries → api-tools (Spring Boot alternatives)
    "spring": "api",           # Spring Boot — in _FRAMEWORK_QUERY_TERMS but missing here
    "php": "api",              # PHP framework queries (Laravel, Slim, Lumen)
    "slim": "api",             # Slim — PHP micro-framework
    # Environment / secrets management
    "env": "security",         # "env management", "env secrets", ".env variables" → Security Tools
    "environment": "security", # "environment variables", "environment config" → secrets management
    # NOTE: "dotenv" must map to "developer" — it's the .env loader library (Developer Tools), NOT secrets
    # management. Gotchas.md: "Always use developer (matches 'Developer Tools'). Previously broken: dotenv".
    # "env secrets" / "environment secrets" queries already route via "env"→security above.
    # Data pipeline / ETL
    "etl": "background",       # ETL pipeline tools → background-jobs (Dagster, Prefect, Airflow)
    "elt": "background",       # ELT — modern variant of ETL (dbt, Airbyte pattern)
    "pipeline": "background",  # "data pipeline" → background-jobs orchestration
    "orchestration": "background",  # "workflow orchestration", "data orchestration"
    "dbt": "background",       # dbt (data build tool) — SQL-based data transformation
    "airbyte": "background",   # Airbyte — open-source ELT data integration platform
    # Edge functions / serverless compute
    "edge": "devops",          # "edge function", "edge computing" → devops-infrastructure
    "lambda": "devops",        # "AWS Lambda alternative", "lambda function" → devops
    "workers": "devops",       # "Cloudflare Workers", "edge workers" → devops
    # JavaScript / TypeScript generic language queries
    "javascript": "frontend",  # "javascript framework", "js library" → frontend-frameworks
    "js": "frontend",          # abbreviation — "js bundler", "js state management"
    # Temporal / workflow tools — named tools for routing "[tool] alternative" queries
    "temporal": "background",  # Temporal.io — durable workflow execution engine
    "inngest": "background",   # Inngest — event-driven background jobs for Next.js/Node
    "trigger": "background",   # Trigger.dev — open-source background jobs with SDK
    # Database — ORM / query builder named tools (very common agent queries)
    "typeorm": "database",          # TypeORM — TypeScript/JS ORM supporting many databases
    "sequelize": "database",        # Sequelize — classic Node.js ORM (PostgreSQL, MySQL, SQLite)
    "mongoose": "database",         # Mongoose — MongoDB object modelling for Node.js
    "sqlalchemy": "database",       # SQLAlchemy — Python SQL toolkit and ORM (Flask, FastAPI)
    "gorm": "database",             # GORM — Go ORM with full-featured query builder
    "kysely": "database",           # Kysely — TypeScript SQL query builder (type-safe)
    "knex": "database",             # Knex.js — SQL query builder for Node.js
    "mikro-orm": "database",        # MikroORM — TypeScript ORM based on Data Mapper pattern
    "mikroorm": "database",         # alternate spelling (no hyphen)
    # Email — sending library / testing tool named tools
    "nodemailer": "email",          # Nodemailer — Node.js email sending library (SMTP/SES)
    "mailtrap": "email",            # Mailtrap — email testing + delivery platform
    # Monitoring — session replay + error tracking named tools
    "bugsnag": "monitoring",        # Bugsnag — stability and error monitoring platform
    "rollbar": "monitoring",        # Rollbar — real-time error tracking for production apps
    "logrocket": "monitoring",      # LogRocket — session replay + error tracking
    "highlight": "monitoring",      # Highlight.io — open-source full-stack session replay
    "uptimerobot": "monitoring",    # UptimeRobot — uptime monitoring with alerts
    "betterstack": "monitoring",    # Better Stack (ex-Logtail + Uptime) — monitoring platform
    # Password / cryptography — security libraries ("bcrypt alternative", "password hashing")
    "password": "security",         # "password hashing", "password manager" → Security Tools
    "hashing": "security",          # "password hashing library", "hashing algorithm" → Security
    "bcrypt": "security",           # bcrypt — adaptive password hashing function
    "argon2": "security",           # Argon2 — memory-hard password hashing (PHC winner)
    "crypto": "security",           # "crypto library", "node:crypto" queries → Security Tools
    # CI/CD — common pipeline and build-automation tool queries
    "circleci": "devops",           # CircleCI — cloud CI/CD platform
    "jenkins": "devops",            # Jenkins — open-source automation server
    "buildkite": "devops",          # Buildkite — hybrid CI/CD (agents run in your infra)
    "dagger": "devops",             # Dagger — portable CI/CD pipelines as code
    "woodpecker": "devops",         # Woodpecker CI — community fork of Drone CI
    "drone": "devops",              # Drone CI — container-native CI/CD platform
    "github": "devops",             # "github actions alternative" → DevOps & Infrastructure
    # AI — structured output / LLM guardrail tools
    "instructor": "ai",             # Instructor — structured LLM outputs with Pydantic
    "outlines": "ai",               # Outlines — guided text generation (structured sampling)
    "guardrails": "ai",             # Guardrails AI — LLM output validation and correction
    "mirascope": "ai",              # Mirascope — clean Python LLM abstractions
    # Vue state management
    "pinia": "frontend",            # Pinia — official Vue 3 state management library
    # React hooks libraries ("react hooks library", "custom hooks", "useHooks")
    "hooks": "frontend",            # React hooks / hooks libraries → Frontend Frameworks
    # SaaS starters / boilerplates ("saas boilerplate", "saas starter kit")
    "saas": "boilerplate",          # SaaS starter queries → Boilerplates category
    # Micro-frontends architecture (module federation, single-spa, qiankun)
    "microfrontend": "frontend",    # "micro-frontend framework" → Frontend Frameworks
    "microfrontends": "frontend",   # plural form — module federation, single-spa queries
    # Headless UI / accessibility component libraries
    "headlessui": "frontend",       # Headless UI (Tailwind Labs) — unstyled accessible components
    "aria": "frontend",             # React Aria (Adobe) — accessibility primitives
    # Client-side data fetching / server state (beyond TanStack Query)
    "swr": "frontend",              # SWR (Vercel) — stale-while-revalidate data fetching hook
    # AI agent frameworks — additional tools growing in adoption
    "mastra": "ai",                 # Mastra — TypeScript AI agent framework
    "pydantic-ai": "ai",            # Pydantic AI — production-grade agent framework
    "phidata": "ai",                # Phidata — multi-modal agent framework with memory
    # TypeScript — very common query prefix ("typescript orm", "typescript testing", "ts library")
    "typescript": "frontend",       # TypeScript — typed JS superset; TS tools live in frontend-frameworks
    "ts": "frontend",               # abbreviation — "ts config", "ts utils", "ts bundler"
    # Web scraping / crawling — Scrapy, Crawlee, Cheerio, Colly live in developer-tools
    "scraping": "developer",        # "web scraping library", "scraping framework" → Developer Tools
    "scraper": "developer",         # "html scraper", "page scraper" → Developer Tools
    "crawler": "developer",         # "web crawler", "link crawler" → Developer Tools
    "crawling": "developer",        # "web crawling tool" → Developer Tools
    "cheerio": "developer",         # Cheerio — jQuery-like server-side HTML parsing for scraping
    "crawlee": "developer",         # Crawlee — Apify's open-source web scraping/crawling library
    # RPC — generic query term (beyond gRPC)
    "rpc": "api",                   # "rpc framework", "rpc protocol" → API Tools (Hono, tRPC, gRPC)
    # DNS — DNS tools and providers live in DevOps & Infrastructure
    "dns": "devops",                # "DNS provider", "DNS management", "DNS server" → DevOps
    # Code formatter — Prettier, Biome, dprint live in testing-tools alongside linters
    "formatter": "testing",         # "code formatter", "js formatter" → Testing Tools
    "format": "testing",            # "code format", "auto-format" → Testing Tools (Biome, Prettier)
    # HTTP clients — Axios, Got, Ky, node-fetch live in api-tools
    "axios": "api",                 # Axios — most popular promise-based HTTP client for JS/TS
    "httpclient": "api",            # explicit compound form
    "httpx": "api",                 # HTTPX — async-first Python HTTP client
    "got": "api",                   # Got — modern Node.js HTTP request library
    "ky": "api",                    # Ky — tiny fetch-based HTTP client
    # GitOps — ArgoCD, FluxCD live in DevOps & Infrastructure
    "gitops": "devops",             # "gitops workflow", "gitops deployment" → DevOps
    # AI model providers — very common in "[provider] alternative" queries
    "ollama": "ai",                 # Ollama — local LLM runner (Llama, Mistral, Gemma)
    "anthropic": "ai",              # Anthropic API / Claude SDK queries
    "gemini": "ai",                 # Google Gemini API queries
    "mistral": "ai",                # Mistral AI — efficient open-weight LLMs
    "huggingface": "ai",            # Hugging Face — ML model hub and inference APIs
    "groq": "ai",                   # Groq — ultra-fast LLM inference hardware/API
    "together": "ai",               # Together.ai — open-source LLM inference cloud
    "perplexity": "ai",             # Perplexity AI — search-augmented LLM
    # Mobile / cross-platform frameworks (React Native ecosystem)
    "reactnative": "frontend",      # React Native — cross-platform mobile with React
    "react-native": "frontend",     # hyphenated form common in queries
    "expo": "frontend",             # Expo — managed React Native toolchain
    "capacitor": "frontend",        # Capacitor — native runtime for web apps (Ionic)
    "ionic": "frontend",            # Ionic — hybrid mobile app framework
    "nativewind": "frontend",       # NativeWind — Tailwind CSS for React Native
    "flutter": "frontend",          # Flutter — Dart cross-platform UI framework
    # Frontend — data tables and grids (AG Grid, TanStack Table, Handsontable)
    "datagrid": "frontend",         # "datagrid library", "data grid component" → Frontend Frameworks
    # Frontend — date/time pickers (very common UI component query)
    "datepicker": "frontend",       # "date picker component", "calendar picker" → Frontend Frameworks
    # Database — data warehouse / analytics DB
    "duckdb": "database",           # DuckDB — in-process analytical database (OLAP)
    "bigquery": "database",         # BigQuery — Google serverless data warehouse
    "snowflake": "database",        # Snowflake — cloud data platform/warehouse
    # DevOps — secret scanning / Git hooks
    "gitleaks": "security",         # Gitleaks — secret scanning for git repos
    "trufflehog": "security",       # TruffleHog — secret detection in git history
    "husky": "devops",              # Husky — Git hooks made easy for Node.js projects
    "lefthook": "devops",           # Lefthook — fast polyglot Git hooks manager
    # AI — vector / embedding databases for RAG pipelines
    "pgvector": "database",         # pgvector — open-source vector similarity for Postgres
    # Monitoring — real user monitoring / performance
    "rum": "monitoring",            # RUM (Real User Monitoring) — frontend performance tracking
    "vitals": "monitoring",         # Core Web Vitals monitoring tools
    "speedlify": "monitoring",      # Speedlify — automated performance benchmarking
    # AI agent frameworks — graph-based orchestration
    "langgraph": "ai",              # LangGraph — LangChain's graph-based multi-agent framework
    "composio": "ai",               # Composio — tool integrations for AI agents (GitHub, Slack, etc.)
    # API / Backend — Bun-native TypeScript framework
    "elysia": "api",                # Elysia — Bun-native TypeScript web framework with end-to-end type safety
    "elysiajs": "api",              # compound form without separator
    # API / Backend — UnJS universal server and TypeScript backend framework
    "nitro": "api",                 # Nitro — UnJS universal server engine (powers Nuxt)
    "encore": "api",                # Encore.ts/Go — backend framework with built-in infra (queues, caches, auth)
    # API / Backend — Rust async runtime (foundational for Axum/Actix)
    "tokio": "api",                 # Tokio — async runtime for Rust, base of Axum and Actix-web
    # Testing — load / performance testing
    "artillery": "testing",         # Artillery — load testing and performance testing framework
    "locust": "testing",            # Locust — scalable Python load testing (write tests in Python)
    # Developer Tools — web scraping optimised for LLMs
    "firecrawl": "developer",       # Firecrawl — LLM-ready web scraping API (Markdown output)
    # Developer Tools — TypeScript runtime validation (Zod alternatives)
    "arktype": "developer",         # ArkType — TypeScript-first runtime type validation (fast, concise)
    # Frontend — form state management and validation
    "reacthookform": "frontend",    # React Hook Form — dominant React form library (40k stars)
    "react-hook-form": "frontend",  # hyphenated form used in queries like "react-hook-form alternative"
    "conform": "frontend",          # Conform — progressive form validation for Remix/Next.js with Zod
    # Frontend — Go desktop app framework using web tech
    "wails": "frontend",            # Wails — build desktop apps with Go + HTML/CSS/JS frontend
    # A/B testing — feature flags category (Split.io, GrowthBook, LaunchDarkly)
    "ab": "feature",                # "a/b test", "a/b testing" → Feature Flags (GrowthBook, Unleash)
    "split": "feature",             # "split testing", "Split.io alternative" → Feature Flags
    # Email — generic mail queries (mail relay, mailer libraries)
    "mail": "email",                # "mail sender", "mail relay", "Laravel mail", "Go mailer"
    "mailer": "email",              # "Ruby mailer", "action mailer", "Node.js mailer"
    # Contract testing — Pact, Dredd (consumer-driven contract tests)
    "pact": "testing",              # Pact — consumer-driven contract testing framework
    "contract": "testing",          # "contract testing", "consumer-driven contracts"
    # Release / changelog automation — semantic-release, Changesets, release-it
    "release": "devops",            # "release automation", "semantic release", "release management"
    # Desktop app frameworks — Electron, Tauri, Wails
    "electron": "frontend",         # Electron — Node.js + Chromium desktop app framework
    "tauri": "frontend",            # Tauri — Rust + WebView2/WebKit desktop app framework
    "desktop": "frontend",          # "desktop app framework", "desktop GUI" queries
    # Mobile / cross-platform (complement to react-native, expo, flutter mappings)
    "native": "frontend",           # "react native", "nativescript" — mobile/native queries
    "mobile": "frontend",           # "mobile app framework", "mobile development" queries
    # Accessibility (a11y) tooling — axe, React Aria, Radix UI
    "accessibility": "frontend",    # "accessibility library", "a11y component" → Frontend Frameworks
    "a11y": "frontend",             # short-form — "a11y testing", "a11y linting", "a11y audit"
    # Hot Module Replacement — Vite HMR, webpack HMR
    "hmr": "frontend",              # Hot Module Replacement — Vite/webpack feature query term
    # Polyfills / browser compatibility shims — core-js, polyfill.io
    "polyfill": "frontend",         # "polyfill library", "browser polyfill" → Frontend Frameworks
    "polyfills": "frontend",        # plural form
    # PWA / service workers — Workbox (Google)
    "workbox": "frontend",          # Google Workbox — service worker and PWA caching library
    "serviceworker": "frontend",    # "service worker library", "service worker caching" → Frontend
    # Rate throttling (complement to rate/limiting/limiter/limit → api)
    "throttle": "api",              # "throttle requests", "api throttle" → API Tools
    "throttling": "api",            # "request throttling", "api throttling" → API Tools
    # Circuit breaker / resilience patterns
    "circuit": "api",               # "circuit breaker", "circuit pattern" → API Tools
    "resilience": "monitoring",     # "resilience engineering", "resiliency" → Monitoring & Uptime
    # Durable execution / workflow engines (Temporal, Inngest, Trigger.dev)
    "durable": "background",        # "durable execution", "durable workflow" → Background Jobs
    # Notification inbox UI component (Novu, Knock, Courier)
    "inbox": "notifications",       # "notification inbox", "inbox component" → Notifications
    # Audit logging (audit trail, compliance audit log)
    "audit": "logging",             # "audit log", "audit trail" → Logging
    # Health checks (health-check endpoint monitoring)
    "healthcheck": "monitoring",    # "healthcheck endpoint", "health check tool" → Monitoring
    # API codegen (openapi-generator, swagger-codegen, Speakeasy)
    "codegen": "api",               # "api codegen", "openapi codegen" → API Tools
    # Multi-tenancy (multi-tenant SaaS auth, tenant isolation)
    "multitenancy": "authentication",  # "multi-tenancy", "tenant isolation" → Authentication
    "multitenant": "authentication",   # "multitenant auth", "multitenant saas" → Authentication
    # Web scraping (verb form, e.g. "scrape a website")
    "scrape": "developer",          # "scrape website", "scrape html" → Developer Tools
    # AI — chatbots, prompt engineering, fine-tuning
    "chatbot": "ai",                # "chatbot builder", "chatbot framework" → AI & Automation
    "prompt": "ai",                 # "prompt template", "prompt management", "prompt engineering" → AI
    "prompting": "ai",              # "chain-of-thought prompting", "few-shot prompting" → AI
    "finetuning": "ai",             # "llm finetuning", "model finetuning" → AI & Automation
    "finetune": "ai",               # "finetune llm", "finetune model" → AI & Automation
    "generative": "ai",             # "generative AI", "generative model" → AI & Automation
    "genai": "ai",                  # abbreviation for "generative AI" — growing query term
    # ML / deep learning — fix routing: "machine learning" and "deep learning" must NOT map to
    # Learning & Education (via "learning" synonym). Add explicit "machine"/"deep" → "ai" so the
    # synonym scanner picks up the first term and short-circuits before hitting "learning".
    "ml": "ai",                    # "ml framework", "ml model", "ml pipeline" → AI & Automation
    "machine": "ai",               # "machine learning" — "machine" fires before "learning"→education
    "neural": "ai",                # "neural network", "neural architecture" → AI & Automation
    "deep": "ai",                  # "deep learning" — "deep" fires before "learning"→education
    "inference": "ai",             # "llm inference", "model inference", "inference api" → AI & Automation
    "chatgpt": "ai",               # ChatGPT alternative queries → AI & Automation
    # AI observability — LLM tracing, evaluation, and proxy tools
    "langfuse": "ai",               # Langfuse — open-source LLM observability and evaluation
    "helicone": "ai",               # Helicone — LLM observability and proxy platform
    # Maps — geospatial and geocoding queries
    "geocoding": "maps",            # "geocoding API", "geocode address" → Maps & Location
    "geospatial": "maps",           # "geospatial data", "geospatial analysis" → Maps & Location
    # Frontend — popular React component libraries not yet mapped
    "mui": "frontend",              # Material UI (MUI) — most popular React UI component library
    "material": "frontend",         # "material UI", "material design" → Frontend Frameworks (MUI)
    "mantine": "frontend",          # Mantine — full-featured React component library
    "chakra": "frontend",           # Chakra UI — accessible React component library
    # DevOps — service mesh and Nix
    "mesh": "devops",               # "service mesh" — Istio, Linkerd, Consul Connect → DevOps
    "nix": "devops",                # Nix — reproducible builds and package management → DevOps
    "nixos": "devops",              # NixOS — declarative Linux OS with Nix → DevOps
    # Forms — multi-step wizards and stepped UIs
    "wizard": "forms",              # "form wizard", "multi-step wizard" → Forms & Surveys
    "multistep": "forms",           # "multi-step form", "multistep flow" → Forms & Surveys
    "stepper": "forms",             # "form stepper", "stepper component" → Forms & Surveys
    # Notifications — toast / snackbar UI components (react-hot-toast, Sonner, Toastify)
    "toast": "notifications",       # "toast notification", "toast component" → Notifications
    "toaster": "notifications",     # "toaster library", "react toaster" → Notifications
    "snackbar": "notifications",    # "snackbar notification" (MUI/Android term) → Notifications
    # Developer Tools — QR code generation and barcode libraries
    "qr": "developer",              # "qr code generator", "qr code library" → Developer Tools
    "barcode": "developer",         # "barcode scanner", "barcode generator" → Developer Tools
    # AI — LLM observability / evaluation platforms
    "langsmith": "ai",              # LangSmith — LangChain's LLM observability and tracing platform
    "evals": "ai",                  # "llm evals", "model evaluation harness" → AI & Automation
    "evaluation": "ai",             # "llm evaluation", "evaluation pipeline" → AI & Automation
    # Email — major providers/tools not yet mapped
    "brevo": "email",               # Brevo (formerly Sendinblue) — email marketing + transactional
    "plunk": "email",               # Plunk — open-source transactional email (3k★)
    # Schema validation / data modeling
    "schema": "developer",          # "json schema validator", "schema definition" → Developer Tools
    # Frontend — infinite scroll / virtual list patterns
    "infinite": "frontend",         # "infinite scroll", "infinite loading" → Frontend Frameworks
    "virtual": "frontend",          # "virtual list", "virtual scroll", "react-virtual" → Frontend Frameworks
    "virtualizer": "frontend",      # TanStack Virtual (formerly react-virtual) → Frontend Frameworks
    # Frontend — spreadsheet / Excel-like grid components (Handsontable, AG Grid, react-datasheet)
    "spreadsheet": "frontend",      # "spreadsheet component", "excel-like table" → Frontend Frameworks
    # Frontend — animation libraries (Framer Motion, GSAP)
    "framer": "frontend",           # Framer Motion — spring physics animation for React
    "gsap": "frontend",             # GreenSock Animation Platform — JS animation
    # Frontend — icon libraries (Lucide, Heroicons, Feather, Iconify)
    "lucide": "frontend",           # Lucide Icons — fork of Feather, beautiful open icons
    "heroicons": "frontend",        # Heroicons — by Tailwind Labs, SVG icon library
    "feather": "frontend",          # Feather Icons — minimal open-source icon set
    "iconify": "frontend",          # Iconify — unified icon framework (200k+ icons)
    "svgr": "frontend",             # SVGR — transforms SVG files into React components
    # Frontend — tooltip/popover positioning (Floating UI, Tippy.js, Popper.js)
    "floating": "frontend",         # Floating UI — tooltip/popover/dropdown positioning
    "popover": "frontend",          # "popover component", "popover library" → Frontend
    "tooltip": "frontend",          # "tooltip library", "react tooltip" → Frontend
    # Frontend — drag and drop (dnd-kit, react-beautiful-dnd, Pragmatic DnD)
    "drop": "frontend",             # "drop zone", "drop target", "drag and drop" → Frontend
    "gesture": "frontend",          # @use-gesture/react — gesture detection hooks → Frontend
    # Frontend — Inertia.js (SPA routing for Laravel/Rails without a full API)
    "inertia": "frontend",          # Inertia.js — build SPAs with server-side routing
    # Frontend — MDX and unified ecosystem (remark, rehype)
    "mdx": "documentation",         # MDX — Markdown with JSX for React docs
    "remark": "documentation",      # Remark — extensible Markdown processor (unified)
    "rehype": "documentation",      # Rehype — HTML processor (unified ecosystem)
    # API tools — HTTP clients / API testing alternatives to Postman
    "hoppscotch": "api",            # Hoppscotch — open-source Postman alternative (60k★)
    "httpie": "api",                # HTTPie — human-friendly HTTP client for the API era
    # Developer Tools — Wasp full-stack framework (Rails for React/Node)
    "wasp": "developer",            # Wasp — declarative full-stack web framework
    # Database — Xata (serverless Postgres + search + branching)
    "xata": "database",             # Xata — serverless Postgres + full-text search + branching
    # CMS — Keystatic (Git-based content management)
    "keystatic": "cms",             # Keystatic — Git-based CMS by Thinkmill
    # DevOps — self-hosted PaaS alternatives
    "dokku": "devops",              # Dokku — mini-Heroku on any server (self-hosted PaaS)
    "caprover": "devops",           # CapRover — Docker-based self-hosted PaaS
    # Static site generators (named tool queries beyond the generic "ssg" term)
    "hugo": "frontend",             # Hugo — fast Go static site generator (70k★)
    "jekyll": "frontend",           # Jekyll — Ruby SSG powering GitHub Pages (48k★)
    "eleventy": "frontend",         # Eleventy (11ty) — simple, fast SSG (17k★)
    "11ty": "frontend",             # shorthand for Eleventy
    "gatsby": "frontend",           # Gatsby — React-based SSG with GraphQL (55k★)
    "hexo": "frontend",             # Hexo — Node.js blog/SSG framework (39k★)
    "pelican": "frontend",          # Pelican — Python static site generator
    # Game engines / frameworks
    "godot": "games",               # Godot — open-source cross-platform game engine (90k★)
    "phaser": "games",              # Phaser — HTML5 / WebGL game framework (36k★)
    "pygame": "games",              # Pygame — Python 2D game development library
    "love2d": "games",              # LÖVE 2D — Lua game framework
    "love": "games",                # short form for LÖVE 2D queries
    "raylib": "games",              # raylib — simple C game programming library
    # Dependency injection / IoC containers
    "ioc": "developer",             # inversion of control — DI container queries
    "inversify": "developer",       # InversifyJS — powerful IoC container for JS/TS
    "tsyringe": "developer",        # tsyringe — lightweight TypeScript DI container (MS)
    "wire": "developer",            # Wire — compile-time DI for Go (Google)
    # Browser extension frameworks
    "plasmo": "developer",          # Plasmo — React-based browser extension framework (10k★)
    "wxt": "developer",             # WXT — Next.js-inspired browser extension framework (5k★)
    "webextension": "developer",    # generic web extension development queries
    # MLOps / ML experiment tracking
    "mlops": "ai",                  # ML operations tooling (MLflow, DVC, Kubeflow)
    "mlflow": "ai",                 # MLflow — open-source ML lifecycle management (18k★)
    "dvc": "ai",                    # DVC — data version control + ML pipelines (13k★)
    "kubeflow": "ai",               # Kubeflow — ML toolkit on Kubernetes
    # Self-hosted Git services
    "gitea": "devops",              # Gitea — self-hosted lightweight Git service (44k★)
    "forgejo": "devops",            # Forgejo — community fork of Gitea
    "gogs": "devops",               # Gogs — minimal self-hosted Git (44k★)
    # Feature flags — commercial platforms not yet mapped
    "launchdarkly": "feature",      # LaunchDarkly — enterprise feature management platform
    "optimizely": "feature",        # Optimizely — experimentation + feature flags (full-stack)
    # Diagramming and technical drawing
    "mermaid": "developer",         # Mermaid.js — diagrams in Markdown / code (72k★)
    "diagram": "developer",         # "diagram tool", "diagramming library" → Developer Tools
    "diagrams": "developer",        # plural form
    "drawio": "developer",          # draw.io / diagrams.net — free diagramming web app
    "plantuml": "developer",        # PlantUML — UML diagrams from plain text
    # AI — additional NLP/LLM evaluation and pipeline tools
    "haystack": "ai",               # Haystack — NLP + LLM pipeline framework (18k★)
    "deepeval": "ai",               # DeepEval — open-source LLM evaluation framework (5k★)
    "ragas": "ai",                  # RAGAS — RAG evaluation framework
    # Testing — TDD and mutation testing
    "tdd": "testing",               # test-driven development tooling queries
    "mutation": "testing",          # "mutation testing" — Stryker, Mutmut, PITest
    "stryker": "testing",           # Stryker — JavaScript/TypeScript mutation testing framework
    # Python testing framework + tooling — fast-growing segment of agent searches
    "pytest": "testing",            # pytest — dominant Python testing framework
    "unittest": "testing",          # unittest — Python stdlib test framework
    "hypothesis": "testing",        # Hypothesis — property-based testing for Python
    "factory": "testing",           # factory_boy / FactoryBot — test data factories
    # Python linters/formatters — Rust-powered tooling gaining fast adoption
    "ruff": "testing",              # Ruff — extremely fast Python linter + formatter (Rust)
    "pylint": "testing",            # Pylint — classic Python linter
    "flake8": "testing",            # Flake8 — Python linting wrapper (pyflakes + pep8)
    "black": "testing",             # Black — opinionated Python code formatter
    "mypy": "testing",              # mypy — optional static type checker for Python
    "pyright": "testing",           # Pyright — Microsoft's Python type checker (fast, VS Code)
    # Python schema validation / data modelling — Developer Tools category
    "pydantic": "developer",        # Pydantic — Python data validation with type hints (FastAPI foundation)
    "marshmallow": "developer",     # Marshmallow — Python object serialization / deserialization
    # Python ASGI / WSGI servers — API layer tools (Uvicorn, Gunicorn, Daphne, Hypercorn)
    "uvicorn": "api",               # Uvicorn — ASGI server for FastAPI / Starlette (lightning fast)
    "gunicorn": "api",              # Gunicorn — production WSGI server for Django / Flask
    "asgi": "api",                  # ASGI — Asynchronous Server Gateway Interface protocol
    "wsgi": "api",                  # WSGI — Python Web Server Gateway Interface protocol
    "starlette": "api",             # Starlette — lightweight ASGI framework (FastAPI foundation)
    "hypercorn": "api",             # Hypercorn — ASGI server with HTTP/2 support
    # Process management — production Node.js / Linux process control tools
    "pm2": "devops",                # PM2 — production process manager for Node.js apps
    "supervisor": "devops",         # Supervisor — process control system for Unix
    "systemd": "devops",            # systemd — init system and service manager for Linux
    "process": "devops",            # "process manager", "process supervisor" → DevOps
    # Caching — common pattern / protocol query terms
    "ttl": "caching",               # TTL (time-to-live) — caching expiry strategy term
    "eviction": "caching",          # "cache eviction", "eviction policy" → Caching
    "invalidation": "caching",      # "cache invalidation", "cache busting" → Caching
    # "distributed" removed — "distributed tracing" wrongly routed to Caching;
    # "distributed cache" is handled by "cache"/"caching" as the second meaningful term.
    "warmup": "caching",            # "cache warmup", "cache warming" → Caching
    # Memoization — in-process caching (memoizee, memize, lodash.memoize)
    "memoize": "caching",           # "memoize function", "memoize library" → Caching
    "memoization": "caching",       # "memoization pattern", "memoize results" → Caching
    # Database — replication, sharding, seeding
    "replication": "database",      # "database replication", "postgres replication" → Database
    "replica": "database",          # "read replica", "replica lag" → Database
    "sharding": "database",         # "database sharding", "horizontal sharding" → Database
    "seeding": "database",          # "database seeding", "seed data" → Database
    "seed": "database",             # "seed script", "seed database" → Database
    # DevOps — backup and disaster recovery tools (Litestream, Barman, pgBackRest)
    "backup": "devops",             # "database backup", "backup strategy" → DevOps & Infrastructure
    "restore": "devops",            # "backup restore", "point-in-time restore" → DevOps
    "litestream": "devops",         # Litestream — continuous SQLite replication to S3/GCS/Azure
    "pgbackrest": "devops",         # pgBackRest — reliable Postgres backup and restore
    "barman": "devops",             # Barman (EDB) — Postgres backup and recovery manager
    "disaster": "devops",           # "disaster recovery", "DR strategy" → DevOps
    # Analytics — BI and reporting tools (Metabase, Redash, Superset, Lightdash)
    "bi": "analytics",              # "BI tool", "business intelligence" → Analytics & Metrics
    "reporting": "analytics",       # "reporting tool", "sql report" → Analytics & Metrics
    "metabase": "analytics",        # Metabase — open-source BI and dashboards (38k★)
    "redash": "analytics",          # Redash — data visualization and dashboards (26k★)
    "superset": "analytics",        # Apache Superset — enterprise open-source BI (62k★)
    "lightdash": "analytics",       # Lightdash — open-source Looker alternative (9k★)
    "evidence": "analytics",        # Evidence — SQL-driven BI for data teams (5k★)
    # API — serialization protocols and resilience patterns
    "serialization": "api",         # "binary serialization", "data serialization" → API Tools
    "msgpack": "api",               # MessagePack — efficient binary serialization format
    "flatbuffers": "api",           # FlatBuffers — Google's memory-efficient binary serialization
    "retry": "api",                 # "retry library", "retry logic" → API Tools (resilience patterns)
    "retries": "api",               # plural form — "http retries", "retry strategy"
    "idempotency": "api",           # "idempotency key", "idempotent request" → API Tools
    # File/storage — upload patterns and cloud object storage
    "multipart": "file",            # "multipart upload", "multipart form data" → File Management
    "presigned": "file",            # "presigned URL", "presigned S3 URL" → File Management
    # Monitoring — profiling tools (pyspy, pprof, clinic.js, scalene, rbspy)
    "profiling": "monitoring",      # "cpu profiling", "memory profiling" → Monitoring & Uptime
    "profiler": "monitoring",       # "python profiler", "nodejs profiler" → Monitoring & Uptime
    # Message queue — generic "broker" queries
    "broker": "message",            # "message broker", "event broker" → Message Queue
    "brokers": "message",           # plural — "kafka brokers", "message brokers" → Message Queue
    # DevOps — linting, formatting CI action tools (pre-commit hooks, lint-staged)
    "lint-staged": "devops",        # lint-staged — run linters on staged git files
    "precommit": "devops",          # pre-commit — framework for managing pre-commit hooks
    "pre-commit": "devops",         # hyphenated form
    # Message queue protocols — AMQP (RabbitMQ) and MQTT (IoT pub/sub)
    "amqp": "message",              # AMQP — Advanced Message Queuing Protocol (RabbitMQ, ActiveMQ)
    "mqtt": "message",              # MQTT — lightweight pub/sub protocol for IoT (Mosquitto, EMQx, HiveMQ)
    "mosquitto": "message",         # Eclipse Mosquitto — open-source MQTT broker
    "emqx": "message",              # EMQX — scalable open-source MQTT broker (12k★)
    # Authorization (fine-grained) — OpenFGA, Casbin, Ory Keto live in auth category
    "authorization": "authentication",  # fine-grained authz tools (ReBAC, ABAC, RBAC engines)
    "authz": "authentication",      # shorthand for authorization in developer queries
    "openfga": "authentication",    # OpenFGA — Google's open-source fine-grained authorization
    "casbin": "authentication",     # Casbin — flexible authorization library (Go, Node, Python)
    "zanzibar": "authentication",   # Google Zanzibar-based authz ("zanzibar alternative" queries)
    # Developer Tools — Jupyter / notebook ecosystem
    "jupyter": "developer",         # Jupyter Notebook / JupyterLab — interactive computing
    "jupyterlab": "developer",      # JupyterLab — next-gen Jupyter UI
    "notebook": "developer",        # generic "notebook" queries → Developer Tools (Jupyter, Zed)
    "ipython": "developer",         # IPython — enhanced interactive Python shell
    # Testing — BDD (Behaviour-Driven Development)
    "bdd": "testing",               # BDD tooling: Cucumber, Behave, SpecFlow, Jasmine
    "cucumber": "testing",          # Cucumber — most popular BDD framework
    "behave": "testing",            # Behave — Python BDD framework
    "specflow": "testing",          # SpecFlow — .NET BDD framework
    "gherkin": "testing",           # Gherkin — BDD DSL used by Cucumber/Behave
    # DevOps — service discovery, config, and VM tooling
    "consul": "devops",             # HashiCorp Consul — service discovery + config + mesh
    "etcd": "devops",               # etcd — distributed key-value store (Kubernetes backbone)
    "vagrant": "devops",            # Vagrant — VM provisioning with declarative config
    "virtualbox": "devops",         # VirtualBox — open-source x86 VM hypervisor
    "hypervisor": "devops",         # generic hypervisor/VM queries → DevOps & Infrastructure
    "hashicorp": "devops",          # HashiCorp brand queries (Vault, Terraform, Consul, Nomad)
    # DevOps — monitoring: Prometheus + Grafana (canonical stack for metrics)
    "prometheus": "monitoring",     # Prometheus — open-source monitoring + alerting (52k★)
    "grafana": "monitoring",        # Grafana — observability dashboards + visualization (64k★)
    # File storage — object storage (MinIO, Backblaze B2, Tigris, Cloudflare R2)
    "minio": "file",                # MinIO — open-source S3-compatible object storage (47k★)
    "backblaze": "file",            # Backblaze B2 — cheap S3-alternative object storage
    "tigris": "file",               # Tigris — globally distributed S3-compatible object storage
    # AI — LLM inference engines (local and server-side)
    "vllm": "ai",                   # vLLM — fast LLM inference and serving engine (20k★)
    "llamacpp": "ai",               # llama.cpp — local LLM inference in C++ (70k★, most downloaded)
    "llamafile": "ai",              # llamafile — single-file local LLM deployment (Mozilla)
    # AI — ML frameworks (commonly searched as "pytorch alternative", "tensorflow vs")
    "pytorch": "ai",                # PyTorch — most popular ML research framework (Facebook)
    "tensorflow": "ai",             # TensorFlow — Google's ML framework for production/research
    "torch": "ai",                  # PyTorch alias — "torch model", "torch training"
    "keras": "ai",                  # Keras — high-level neural networks API (TF/JAX/PyTorch backends)
    # AI — ML experiment tracking and model management
    "wandb": "ai",                  # Weights & Biases — MLOps platform for experiment tracking (9k★)
    "weights": "ai",                # "Weights & Biases" — first term in full name queries
    "biases": "ai",                 # "Weights & Biases" — second term in queries
    # AI — RAG pipeline terminology (Retrieval-Augmented Generation)
    "retrieval": "ai",              # "retrieval augmented", "retrieval pipeline" → AI & Automation
    "chunking": "ai",               # "text chunking", "document chunking" → AI & Automation (RAG)
    "rerank": "ai",                 # "reranking model", "cross-encoder rerank" → AI & Automation
    "reranking": "ai",              # explicit form — "reranking in RAG"
    "embedder": "ai",               # "document embedder", "fast embedder" → AI & Automation
    # Payments — Polar.sh and Lemon Squeezy routing for "[tool] alternative" queries
    "polar": "payments",            # Polar.sh — open-source Stripe alternative for OSS devs (5k★)
    "lemon": "payments",            # Lemon Squeezy — first term: "lemon squeezy alternative"
    "squeezy": "payments",          # Lemon Squeezy — second term for direct "squeezy" queries
    # Workflow automation — n8n, Windmill, Activepieces, Pipedream (Zapier alternatives)
    "n8n": "background",            # n8n — self-hostable workflow automation (47k★)
    "windmill": "background",       # Windmill — fast workflow engine + script runner (12k★)
    "activepieces": "background",   # Activepieces — open-source Zapier alternative (12k★)
    "pipedream": "background",      # Pipedream — developer-focused workflow automation (8k★)
    "zapier": "background",         # Zapier — canonical automation brand for alternative queries
    # AI — visual flow builders (LangChain / LlamaIndex GUI environments)
    "flowise": "ai",                # FlowiseAI — drag-and-drop LangChain builder (34k★)
    "langflow": "ai",               # LangFlow — visual LangChain/LlamaIndex flow builder (48k★)
    # AI — emerging agent/orchestration frameworks not yet covered
    "baml": "ai",                   # BAML — structured LLM function language by BoundaryML
    "agno": "ai",                   # Agno (formerly Phidata) — multi-modal agent framework (4k★)
    "marvin": "ai",                 # Marvin — Prefect's Python AI toolkit for structured outputs
    "controlflow": "ai",            # ControlFlow — Python task orchestration for LLM workflows
    # Boilerplates — T3 Stack is the dominant Next.js starter ("t3 stack", "t3 boilerplate" queries)
    "t3": "boilerplate",            # T3 Stack — Next.js + TypeScript + tRPC + Tailwind + Prisma (25k★)
    "shipfast": "boilerplate",      # ShipFast — Next.js SaaS boilerplate with Stripe + auth
    "shipfa": "boilerplate",        # ShipFa.st — common shorthand used in queries
    # Frontend — Partytown (web worker script isolation from BuilderIO)
    "partytown": "frontend",        # Partytown — relocate 3rd-party scripts to web workers
    # Database — Nile (serverless multi-tenant Postgres)
    "nile": "database",             # Nile — serverless Postgres database built for multi-tenant SaaS
    # Developer Tools — Effect.ts (functional programming library for TypeScript)
    "effect": "developer",          # Effect.ts — functional programming library for complex TypeScript apps
    "effectts": "developer",        # compound form — "effect ts alternative" queries
    # Logging — Node.js and Go named loggers (common "[tool] alternative" queries)
    "winston": "logging",           # Winston — most popular Node.js multi-transport logger (22k★)
    "pino": "logging",              # Pino — fastest low-overhead JSON logger for Node.js (14k★)
    "bunyan": "logging",            # Bunyan — classic JSON structured logger for Node.js
    "morgan": "logging",            # Morgan — HTTP request logger middleware for Express/Node.js
    "zerolog": "logging",           # Zerolog — Go zero-allocation JSON logger
    "slog": "logging",              # Go standard library structured logging (Go 1.21+)
    # NOTE: "structured" removed — misrouted "structured output" LLM queries to Logging.
    # "structured logs/logging/log" already covered by "log"→logging, "logs"→logging, "logging"→logging.
    # Background jobs — additional named tools not yet covered
    "hatchet": "background",        # Hatchet — durable workflow orchestration engine (5k★)
    "oban": "background",           # Oban — reliable Elixir background jobs on PostgreSQL
    "faktory": "background",        # Faktory — language-agnostic background job system (6k★)
    "rq": "background",             # RQ (Redis Queue) — lightweight Python job queues (10k★)
    # DevOps — container runtimes (Docker alternatives)
    "podman": "devops",             # Podman — rootless daemonless Docker-compatible runtime
    "containerd": "devops",         # containerd — CNCF container runtime (powers Kubernetes nodes)
    # Distributed application runtime
    "dapr": "api",                  # Dapr — portable event-driven distributed runtime (24k★)
    # AI — model API providers and inference tools
    "openrouter": "ai",             # OpenRouter — unified LLM routing API (200+ models)
    "replicate": "ai",              # Replicate — run ML models via API (no GPU setup required)
    "modal": "ai",                  # Modal — serverless GPU compute for AI/ML workloads
    "whisper": "ai",                # OpenAI Whisper — open-source speech-to-text model
    # Testing — container-based integration testing and test data generation
    "testcontainers": "testing",    # Testcontainers — real service containers for integration tests
    "faker": "testing",             # Faker.js / Faker.py — realistic fake data for tests
    # Speech / Voice AI — growing segment of AI queries (TTS, STT, ASR tools)
    "tts": "ai",                    # text-to-speech — ElevenLabs, Cartesia, Coqui TTS
    "stt": "ai",                    # speech-to-text (STT abbreviation) — Deepgram, Whisper
    "asr": "ai",                    # automatic speech recognition — Deepgram, AssemblyAI
    "voice": "ai",                  # voice AI — ElevenLabs, Play.ht, Murf → AI & Automation
    "speech": "ai",                 # "speech recognition", "speech synthesis" → AI & Automation
    "elevenlabs": "ai",             # ElevenLabs — leading voice AI API for TTS (developer-focused)
    "deepgram": "ai",               # Deepgram — speech-to-text API for real-time + async transcription
    "cartesia": "ai",               # Cartesia — ultra-low latency real-time voice synthesis
    "assemblyai": "ai",             # AssemblyAI — transcription + audio intelligence API
    # Stream processing — Apache Flink, Kafka Streams, Spark Streaming
    "stream": "message",            # "stream processing", "event stream" → Message Queue
    "streams": "message",           # plural — "Redis Streams", "Kafka Streams" queries
    "flink": "message",             # Apache Flink — stateful distributed stream processing (37k★)
    "kinesis": "message",           # AWS Kinesis — event streaming (for alternative queries)
    "redpanda": "message",          # Redpanda — Kafka-compatible streaming, 10× faster (8k★)
    # Auth — SCIM provisioning and LDAP directory services
    "scim": "authentication",       # SCIM 2.0 — automated user provisioning (WorkOS, Okta, JumpCloud)
    "ldap": "authentication",       # LDAP — directory protocol (OpenLDAP, FreeIPA queries)
    "directory": "authentication",  # "directory service", "user directory" → Authentication
    "provisioning": "authentication",  # "user provisioning", "auto-provisioning" → Auth
    # Developer Tools — plugin and extension systems
    "plugin": "developer",          # "plugin system", "vite plugin" → Developer Tools
    "plugins": "developer",         # plural — "rollup plugins", "webpack plugins"
    # Logging — additional named tools not yet covered
    "loguru": "logging",            # Loguru — delightful Python logging with zero setup (18k★)
    "structlog": "logging",         # structlog — structured logging for Python (3k★)
    "fluentbit": "logging",         # Fluent Bit — lightweight log processor and forwarder (5k★)
    "fluent-bit": "logging",        # hyphenated form used in queries ("fluent-bit alternative")
    # Date/time libraries — very common "alternative" query segment for date-fns, dayjs, Moment
    "dayjs": "frontend",            # Day.js — lightweight 2kB Moment.js alternative (47k★)
    "moment": "frontend",           # Moment.js — most-searched legacy date library (48k★)
    "momentjs": "frontend",         # compound form — "momentjs alternative" queries
    "luxon": "frontend",            # Luxon — modern DateTime library from Moment.js team
    # UI component query terms — common frontend queries that don't match category name
    "editor": "frontend",           # "text editor", "rich text editor", "code editor" → Frontend
    "dialog": "frontend",           # "dialog component", "accessible dialog" → Frontend Frameworks
    "drawer": "frontend",           # "drawer component", "side drawer", "bottom sheet" → Frontend
    "carousel": "frontend",         # "image carousel", "carousel component" → Frontend Frameworks
    "slider": "frontend",           # "range slider", "image slider" → Frontend Frameworks
    "accordion": "frontend",        # "accordion component", "collapsible section" → Frontend
    "tabs": "frontend",             # "tab component", "tabbed navigation" → Frontend Frameworks
    "color": "frontend",            # "color picker", "color palette library" → Frontend Frameworks
    "font": "frontend",             # "web font", "font loader", "font optimizer" → Frontend
    # 3D / data visualization — Three.js and D3.js generate high query volume
    "three": "frontend",            # Three.js — 3D JavaScript / WebGL library (102k★)
    "threejs": "frontend",          # compound form — "threejs alternative", "three.js tutorial"
    "d3": "analytics",              # D3.js — data-driven documents, data visualization (108k★)
    # Auth patterns — cookie/token queries grow with SSR + edge-auth patterns
    "cookie": "authentication",     # "cookie session", "cookie-based auth", "iron-session" → Auth
    "token": "authentication",      # "jwt token", "access token", "token refresh" → Authentication
    "tokens": "authentication",     # plural — "oauth tokens", "refresh tokens" → Authentication
    # Payments — currency formatting/conversion queries
    "currency": "payments",         # "currency formatter", "currency conversion API" → Payments
    # File management — image processing beyond "upload" / "media"
    "sharp": "file",                # Sharp — high-performance Node.js image processing (27k★)
    "resize": "file",               # "image resize library", "image resizer" → File Management
    # Developer Tools — clipboard utilities (very common utility query)
    "clipboard": "developer",       # "clipboard API", "copy to clipboard" → Developer Tools
    # Database — analytical / data warehouse queries
    "warehouse": "database",        # "data warehouse", "analytical warehouse" → Database
    # Lazy loading / code splitting / island architecture patterns
    "lazy": "frontend",             # "lazy loading", "lazy image", "dynamic import" → Frontend
    "splitting": "frontend",        # "code splitting", "chunk splitting" (Vite/Webpack) → Frontend
    "island": "frontend",           # "island architecture" (Astro, Fresh) → Frontend Frameworks
    "hydration": "frontend",        # "SSR hydration", "partial hydration", "hydration mismatch" → Frontend
    # State machine / FSM (XState, Robot, MachineState)
    "fsm": "frontend",              # "FSM library", "finite state machine" → Frontend (XState)
    "statemachine": "frontend",     # "state machine library", "state machine alternative" → Frontend
    # Event emitter libraries (mitt, EventEmitter3, nanobus)
    "emitter": "api",               # "event emitter", "typed event emitter" → API Tools
    "eventemitter": "api",          # compound — "EventEmitter3 alternative", "event emitter lib"
    "mitt": "api",                  # mitt — 200b event emitter (specific named tool)
    # Concurrency / parallelism control (worker pools, async queues)
    "concurrency": "background",    # "concurrency control", "concurrent jobs" → Background Jobs
    "concurrent": "background",     # "concurrent tasks", "concurrent workers" → Background Jobs
    # Analytics — user behavior analysis
    "replay": "monitoring",         # "session replay" (LogRocket, Highlight.io, PostHog) → Monitoring
    "heatmap": "analytics",         # "click heatmap", "scroll heatmap" (Hotjar, Clarity) → Analytics
    "funnel": "analytics",          # "conversion funnel", "funnel analysis" → Analytics & Metrics
    "cohort": "analytics",          # "cohort analysis", "user cohorts" → Analytics & Metrics
    # Project management — Gantt charts (commonly searched feature)
    "gantt": "project",             # "Gantt chart", "Gantt timeline view" → Project Management
    # User onboarding / product tours (Intro.js, Shepherd.js, Driver.js)
    "tour": "frontend",             # "product tour", "interactive tour library" → Frontend Frameworks
    "onboarding": "frontend",       # "user onboarding flow", "onboarding wizard" → Frontend Frameworks
    # Vue utilities — VueUse is searched directly as a named tool
    "vueuse": "frontend",           # VueUse — Vue Composition API utility collection (21k★)
    # Debounce / rate-control hooks (use-debounce, xhook, lodash.debounce)
    "debounce": "frontend",         # "debounce library", "useDebounce hook" → Frontend Frameworks
    "usedebounce": "frontend",      # "useDebounce React hook" — explicit hook form
    # Syntax highlighting (used in documentation sites and markdown renderers)
    "shiki": "documentation",       # Shiki — TextMate-grammar syntax highlighter (Vite/Astro docs)
    "prismjs": "documentation",     # Prism.js — lightweight extensible syntax highlighter
    # Note: "highlight" → monitoring (Highlight.io); use "prismjs" not "prism" to avoid conflict
    # i18n / localization libraries (specific named tools)
    "lingui": "localization",       # Lingui — JS/React i18n with compile-time message extraction
    "paraglide": "localization",    # Paraglide.js — tree-shakeable i18n for SvelteKit/Astro/Next.js
    "react-intl": "localization",   # React-Intl (FormatJS) — React component i18n
    "formatjs": "localization",     # FormatJS ecosystem — react-intl, intl-messageformat, etc.
    # State management — proxy-based and reactive (not yet covered)
    "valtio": "frontend",           # Valtio — proxy-based mutable state for React (9k★)
    "effector": "frontend",         # Effector — reactive state management, framework-agnostic (4k★)
    "legendstate": "frontend",      # Legend State — high-performance proxy observables (4k★)
    "legend-state": "frontend",     # hyphenated form — "legend-state alternative", "legend-state react"
    # Environment variable validation / type-safe env (developer tooling)
    "t3-env": "developer",          # T3 Env — type-safe env vars with Zod (3.5k★, T3 stack)
    "t3env": "developer",           # compound form — "t3env nextjs", "t3env validation"
    "envalid": "developer",         # envalid — Node.js env variable validation (clean, typed)
    # Testing — classic JS test framework and assertion libraries
    "mocha": "testing",             # Mocha — classic Node.js test runner (22k★, very common "[tool] alternative")
    "jasmine": "testing",           # Jasmine — BDD testing framework for JS (16k★)
    "chai": "testing",              # Chai — BDD/TDD assertion library, pairs with Mocha
    "sinon": "testing",             # Sinon.js — test spies, stubs, and mocks for JS
    # Testing — Go and Ruby test frameworks
    "testify": "testing",           # Testify — Go testing toolkit with assertions and mocks (23k★)
    "rspec": "testing",             # RSpec — Ruby BDD testing framework
    "gomock": "testing",            # GoMock — Go interface mocking framework (Google)
    # Payments — additional subscription and enterprise payment providers
    "chargebee": "payments",        # Chargebee — subscription billing and management SaaS
    "adyen": "payments",            # Adyen — global enterprise payment processing
    "revenuecat": "payments",       # RevenueCat — mobile in-app purchase and subscription SDK
    "recurly": "payments",          # Recurly — subscription management platform
    # Database — FaunaDB
    "fauna": "database",            # Fauna — serverless document-relational database
    "faunadb": "database",          # explicit form — "faunadb alternative" queries
    # Security — static analysis and container scanning tools
    "trivy": "security",            # Trivy — container and IaC vulnerability scanner (Aqua, 22k★)
    "semgrep": "security",          # Semgrep — fast, open-source SAST (static analysis, 10k★)
    "grype": "security",            # Grype — container and filesystem vulnerability scanner (Anchore)
    # AI — cloud ML platforms (commonly queried as "[platform] alternative" or SDK queries)
    "cohere": "ai",                 # Cohere — enterprise LLM APIs (Rerank, Embed, Generate)
    "vertex": "ai",                 # Google Vertex AI — managed ML platform and LLM APIs
    "bedrock": "ai",                # AWS Bedrock — fully managed LLM service (Claude, Llama, Titan)
    "sagemaker": "ai",              # AWS SageMaker — ML training, deployment, and MLOps
    # Documentation — Next.js/Vite-based doc site frameworks
    "nextra": "documentation",      # Nextra — Next.js-based documentation framework (11k★)
    "vitepress": "documentation",   # VitePress — Vite-powered static site generator for docs (13k★)
    "docsify": "documentation",     # Docsify — no-build docs site generator from Markdown (28k★)
    # Frontend — React Router (direct named-tool query: "react-router alternative" is very common)
    "react-router": "frontend",     # React Router — most popular React routing library (52k★)
    "reactrouter": "frontend",      # compound form — "reactrouter alternative", "react router v7"
    # Frontend — mobile cross-platform
    "nativescript": "frontend",     # NativeScript — native mobile apps with JS/TS (Angular/React/Vue)
    # DevOps — mobile CI/CD and Kubernetes IaC
    "fastlane": "devops",           # Fastlane — automate iOS/Android builds and releases (40k★)
    "crossplane": "devops",         # Crossplane — Kubernetes-native IaC and control plane (9k★)
    # Data fetching hooks / server state (SWR, TanStack Query, Apollo Client)
    "fetching": "frontend",         # "data fetching library", "fetching hook" → Frontend Frameworks
    # SSL/TLS certificate management tools
    "certificate": "security",      # "ssl certificate", "certificate management", "cert-manager" → Security
    "cert": "security",             # short form — "cert renewal", "cert authority" → Security Tools
    # Full-stack framework queries (Next.js, SvelteKit, Remix live in frontend-frameworks)
    "fullstack": "frontend",        # "fullstack framework", "fullstack typescript" → Frontend Frameworks
    "full-stack": "frontend",       # hyphenated form — "full-stack web framework" → Frontend Frameworks
    # OpenAPI spec tooling (Scalar, Speakeasy, Redoc, openapi-ts)
    "spec": "api",                  # "openapi spec", "api specification", "json schema spec" → API Tools
    "specification": "api",         # long form — "api specification tool" → API Tools
    # Monorepo workspace tooling (Nx, Turborepo, pnpm workspaces, Yarn workspaces)
    "workspace": "developer",       # "nx workspace", "pnpm workspace", "yarn workspaces" → Developer Tools
    "workspaces": "developer",      # plural — "monorepo workspaces", "npm workspaces" → Developer Tools
    # Type-safe query/API patterns (tRPC, Kysely, Zod, Drizzle are all developer tools)
    "typesafe": "developer",        # "typesafe orm", "typesafe api client" → Developer Tools
    "type-safe": "developer",       # hyphenated form — "type-safe query builder" → Developer Tools
    # Singular devtool form (complement to existing "devtools" → "developer" mapping)
    "devtool": "developer",         # singular — "devtool extension", "devtool panel" → Developer Tools
    # Admin panel / internal tool builders — Appsmith, ToolJet, Budibase, Retool → Developer Tools
    "retool": "developer",          # Retool — leading internal tool builder (very common alternative query)
    "appsmith": "developer",        # Appsmith — open-source internal tools builder (31k★)
    "tooljet": "developer",         # ToolJet — open-source Retool alternative (28k★)
    "budibase": "developer",        # Budibase — open-source low-code app builder for teams (22k★)
    "admin": "developer",           # "admin panel builder", "admin dashboard" → Developer Tools
    # Ory open-source identity stack (Hydra, Kratos, Keto, Oathkeeper)
    "ory": "authentication",        # Ory — full open-source identity infrastructure platform
    "hydra": "authentication",      # Ory Hydra — certified OAuth 2.0 and OpenID Connect server
    "kratos": "authentication",     # Ory Kratos — headless self-service identity management
    # Static / client-side search (complement to Algolia/Typesense/Meilisearch synonyms)
    "orama": "search",              # Orama — edge-native TypeScript full-text + vector search (7k★)
    "pagefind": "search",           # Pagefind — Wasm-powered static full-text search for docs/blogs
    "lunr": "search",               # Lunr.js — Solr-inspired full-text search for browsers/Node (9k★)
    "fuse": "search",               # Fuse.js — lightweight fuzzy-search library for JS/TS (18k★)
    # Email — SaaS-focused transactional platforms not yet mapped
    "loops": "email",               # Loops.so — transactional + marketing email for modern SaaS
    # AI SDK — Vercel AI SDK is the most widely adopted unified provider SDK
    "vercel-ai": "ai",              # Vercel AI SDK — TypeScript SDK for Next.js AI apps (11k★)
    "aisdk": "ai",                  # short form — "ai sdk alternative", "ai sdk streaming" queries
    # CSS-in-JS styling libraries
    "styled-components": "frontend", # styled-components — CSS-in-JS with tagged templates (React)
    "styledcomponents": "frontend",  # compound form — "styledcomponents alternative" queries
    "emotion": "frontend",           # Emotion — performant CSS-in-JS, framework-agnostic
    "vanilla-extract": "frontend",   # vanilla-extract — zero-runtime TypeScript-first CSS
    "vanillaextract": "frontend",    # compound form — "vanilla-extract alternative" queries
    "stitches": "frontend",          # Stitches — near-zero runtime CSS-in-JS by WorkOS (8k★)
    # Monitoring — open-source APM and monitoring-as-code
    "signoz": "monitoring",         # SigNoz — open-source Datadog/NewRelic alternative (18k★)
    "hyperdx": "monitoring",        # HyperDX — open-source Datadog alt (logs + traces + sessions)
    "checkly": "monitoring",        # Checkly — monitoring as code (E2E + API checks in CI/CD)
    # Database — schema migration CLI and distributed MySQL/Postgres tools
    "atlas": "database",            # Atlas — Ariga's declarative database schema migration CLI (5k★)
    "vitess": "database",           # Vitess — MySQL horizontal scaling (powers YouTube/PlanetScale)
    "citus": "database",            # Citus — Postgres extension for horizontal sharding (Microsoft)
    # Background jobs — classic and additional Node.js schedulers
    "bull": "background",           # Bull — Redis-backed Node.js queue (classic; BullMQ successor)
    "agenda": "background",         # Agenda.js — MongoDB-backed job scheduler for Node.js (9k★)
    "bree": "background",           # Bree — worker thread-based JavaScript job scheduler (3k★)
    # SEO — sitemap generators and Open Graph / meta tag tools
    "sitemap": "seo",               # next-sitemap, @astrojs/sitemap, nuxt-simple-sitemap → SEO Tools
    "opengraph": "seo",             # Open Graph meta tag tools, og-image generators → SEO Tools
    "metatag": "seo",               # meta tag generators ("metatag alternative") → SEO Tools
    # Testing — visual regression and load testing tools not yet mapped
    "screenshot": "testing",        # visual regression: Percy, Chromatic, Playwright screenshots
    "percy": "testing",             # BrowserStack Percy — automated visual regression testing
    "gatling": "testing",           # Gatling — Scala/Java-based load + performance testing (10k★)
    "lighthouse": "monitoring",     # Google Lighthouse — web performance audit (run as CLI/CI)
    # GraphQL — client and server libraries
    "apollo": "api",                # Apollo Client + Server — dominant GraphQL ecosystem (22k★)
    "urql": "api",                  # urql — lightweight GraphQL client for React/Vue/Svelte (9k★)
    # Date utilities — normalized slug form (complement to dayjs/moment/luxon)
    "datefns": "frontend",          # "datefns alternative" query normalization → date-fns (34k★)
    # Frontend frameworks — Deno Fresh meta-framework and cross-framework compilers
    "fresh": "frontend",            # Deno Fresh — zero-JS-by-default island SSR meta-framework (12k★)
    "mitosis": "frontend",          # Mitosis — write once, compile to React/Vue/Svelte/Angular
    # Code editors — queries like "zed alternative", "neovim setup" → Developer Tools
    "zed": "developer",             # Zed — collaborative Rust code editor with AI features (65k★)
    "neovim": "developer",          # Neovim — hyperextensible Vim-fork; huge plugin ecosystem (82k★)
    "helix": "developer",           # Helix — post-modern modal text editor (Rust, kakoune-style) (35k★)
    "lapce": "developer",           # Lapce — GPU-accelerated code editor written in Rust (34k★)
    # Terminal emulators — queries like "ghostty alternative", "fast terminal" → Developer Tools
    "ghostty": "developer",         # Ghostty — fast GPU-native terminal by Mitchell Hashimoto (25k★)
    "alacritty": "developer",       # Alacritty — cross-platform OpenGL terminal emulator (56k★)
    "wezterm": "developer",         # WezTerm — GPU-accelerated terminal with Lua config (18k★)
    # Git clients — "gitbutler alternative" → Developer Tools
    "gitbutler": "developer",       # GitButler — branch-stacking git client for modern workflows (12k★)
    # AI code review — "coderabbit alternative", "ai code review" → AI Dev Tools
    "coderabbit": "ai",             # CodeRabbit — AI-powered code review (contextual PR feedback)
    # Billing/metering SaaS — routes "lago alternative", "usage based billing" → Invoicing & Billing
    "lago": "invoicing",            # Lago — open-source metering and billing API (6k★)
    "orb": "invoicing",             # Orb — usage-based billing platform (metered pricing SaaS)
    # Product-led pricing / feature access management
    "stigg": "payments",            # Stigg — pricing & entitlements infrastructure for SaaS
    # AI coding assistants — "aider alternative", "codeium vs copilot", "ai pair programmer"
    "aider": "ai",              # Aider — terminal AI pair programmer (Aider-AI/aider, 24k★)
    "continue": "ai",           # Continue.dev — open-source AI coding assistant (VS Code/JetBrains)
    "codeium": "ai",            # Codeium — AI code completion (now "Windsurf" brand, still widely searched)
    "tabnine": "ai",            # Tabnine — AI code completion with local model option (17k★)
    "cody": "ai",               # Sourcegraph Cody — AI coding assistant with codebase context
    "supermaven": "ai",         # Supermaven — ultrafast AI code completion (by Tabnine co-founder)
    "devin": "ai",              # Devin (Cognition) — AI software engineer for fully autonomous tasks
    # Cloud dev environments — "gitpod alternative", "dev container setup" → DevOps & Infrastructure
    "gitpod": "devops",         # Gitpod — cloud-based dev environments (instant workspace spin-up, 13k★)
    "devcontainer": "devops",   # Dev Containers (VS Code spec) — containerised reproducible dev envs
    "codespace": "devops",      # GitHub Codespaces — browser-based VS Code dev environments
    # JAMstack / static site architecture terms (complement to "ssg", "ssr", "pwa")
    "jamstack": "frontend",     # JAMstack — JavaScript + APIs + Markup architecture (Netlify coined)
    "static": "frontend",       # "static site generator", "static site framework" → Frontend Frameworks
    # Auth tools in DB but synonyms were missing
    "logto": "authentication",  # Logto — open-source CIAM and auth infrastructure (9k★)
    "hanko": "authentication",  # Hanko — passkey-first authentication SDK (7k★)
    "stytch": "authentication", # Stytch — auth API with passkeys, magic links, SSO (B2C-focused)
    "propelauth": "authentication",  # PropelAuth — hosted auth for B2B SaaS (RBAC, org management)
    # API key management — Unkey is the dominant OSS tool in this space
    "unkey": "api",             # Unkey — open-source API key management and rate limiting (5k★)
    # Analytics — Umami is in DB but was missing from synonyms
    "umami": "analytics",       # Umami — self-hosted privacy-friendly Google Analytics alternative (23k★)
    # Developer TUI tools — fast-growing category of CLI-native developer tooling
    "lazygit": "developer",     # Lazygit — simple terminal UI for Git commands (Golang, 53k★)
    "atuin": "developer",       # Atuin — magical shell history replacement in Rust (22k★)
    "zellij": "developer",      # Zellij — feature-rich terminal workspace / multiplexer (Rust, 23k★)
    # Local LLM inference tools — very high query volume as devs set up local AI
    # (llamacpp, llamafile already mapped above; adding the remaining high-volume terms)
    "llama": "ai",                  # LLaMA model queries — "run llama locally", "llama model" → AI
    "lmstudio": "ai",               # LM Studio — popular local LLM GUI with built-in model library
    "jan": "ai",                    # Jan.ai — open-source local-first LLM chat and inference server
    # AI image generation — Stable Diffusion ecosystem has enormous agent query volume
    "stable": "ai",                 # "stable diffusion", "stable video diffusion" → AI & Automation
    "diffusion": "ai",              # "diffusion model", "latent diffusion" → AI & Automation
    "comfyui": "ai",                # ComfyUI — node-based Stable Diffusion workflow UI (66k★)
    # Data visualization — chart libraries complement to recharts/d3/chartjs already mapped
    "echarts": "analytics",         # Apache ECharts — feature-rich chart library (60k★, enterprise/Asia)
    "nivo": "analytics",            # Nivo — React chart library built on D3, rich component set (13k★)
    "apexcharts": "analytics",      # ApexCharts — interactive SVG/canvas chart library (14k★)
    # API tools — open-source Postman alternatives and OpenAPI documentation
    "bruno": "api",                 # Bruno — offline-first open-source API testing tool (28k★)
    "scalar": "api",                # Scalar — modern interactive OpenAPI reference and playground (30k★)
    "redoc": "documentation",       # ReDoc — OpenAPI 3.x documentation renderer (23k★)
    # WebSocket / realtime servers — open-source push infrastructure
    "soketi": "message",            # soketi — open-source Pusher-compatible WebSocket server (5k★)
    "centrifugo": "message",        # Centrifugo — scalable open-source real-time messaging server (8k★)
    # Backend framework queries (complement to fastapi/django/flask/rails/spring mappings)
    "phoenix": "api",               # Phoenix — Elixir web framework famous for real-time channels (21k★)
    "elixir": "api",                # Elixir language queries → API frameworks (Phoenix, Plug, Bandit)
    # DevOps — cloud infrastructure providers with high "alternative" query volume
    "cloudflare": "devops",         # Cloudflare — CDN/DNS/Workers; common "alternative" query base
    # Payments — EU payment processors
    "mollie": "payments",           # Mollie — developer-friendly EU payment processor
    # Observability — OpenTelemetry terms (complement to "tracing"→monitoring, "otel"→monitoring)
    "telemetry": "monitoring",       # "telemetry data", "telemetry pipeline" → Monitoring & Uptime
    "trace": "monitoring",           # "distributed trace", "trace query" → Monitoring & Uptime
    "traces": "monitoring",          # plural — "view traces", "traces dashboard"
    "span": "monitoring",            # "span context", "trace span" → OpenTelemetry terminology
    # Performance — APM / performance monitoring (New Relic, DataDog APM, Scout APM, Elastic APM)
    "performance": "monitoring",     # "performance monitoring", "app performance" → Monitoring
    # Load balancer — HAProxy, Nginx, Traefik, Caddy live in DevOps & Infrastructure
    "balancer": "devops",            # "load balancer", "traffic balancer" → DevOps & Infrastructure
    # Auth — magic link authentication (Stytch, Auth0, Clerk magic links)
    "magic": "authentication",       # "magic link auth", "passwordless magic" → Authentication
    # Local-first / sync — ElectricSQL, PGlite, Automerge, Liveblocks CRDT
    "local-first": "database",       # "local-first app", "local-first database" → Database
    "localfirst": "database",        # compound form — "localfirst sync", "localfirst architecture"
    "sync": "database",              # "offline sync", "data sync", "realtime sync" → Database
    "crdt": "database",              # "CRDT sync", "conflict-free replicated data type" → Database
    # Security — XSS and CSRF protection tools (DOMPurify, sanitize-html, csurf, helmet)
    "xss": "security",               # XSS (cross-site scripting) prevention and sanitizer queries
    "csrf": "security",              # CSRF protection middleware ("csrf token", "csrf alternative")
    "sanitizer": "security",         # "html sanitizer", "input sanitizer" → Security Tools (DOMPurify)
    "sanitize": "security",          # verb form — "sanitize html input", "sanitize output" → Security
    "dompurify": "security",         # DOMPurify — fast, permissive XSS sanitizer for HTML (13k★)
    # Frontend — HTML template engines, parsers, and editors
    "html": "frontend",              # "html parser", "html template engine", "html-in-js" → Frontend
    # Auth — OpenID Connect standard (complement to "oidc"→authentication)
    "openid": "authentication",      # OpenID Connect — "openid provider", "openid connect library"
    # Developer Tools — dependency injection containers (InversifyJS, tsyringe, Wire)
    "injection": "developer",        # "dependency injection", "constructor injection" → Developer Tools
    "di": "developer",               # DI container shorthand — "di framework", "di library for ts"
    # Testing — code quality and regression testing patterns
    "quality": "testing",            # "code quality tool", "quality gate" → Testing Tools (SonarQube, Codacy)
    "regression": "testing",         # "regression testing", "visual regression suite" → Testing Tools
    # Analytics — generic reporting tool queries
    "report": "analytics",           # "reporting tool", "report builder", "sql report" → Analytics & Metrics
    # Developer Tools — dependency management and code review tooling
    "dependency": "developer",       # "dependency management", "dependency graph", "dep scanning" → Dev Tools
    "review": "developer",           # "code review tool", "automated code review" → Developer Tools
    "diff": "developer",             # "diff library", "json diff tool", "code diff" → Developer Tools
    # Database — query builders and ORMs ("sql query builder", "type-safe query")
    "query": "database",             # "query builder", "type-safe query", "sql query" → Database (Kysely, Knex, Drizzle)
    # Frontend — state stores ("global store", "state store", "redux store")
    "store": "frontend",             # "state store", "global store", "data store" → Frontend Frameworks (Zustand, Pinia, Redux)
    # Frontend — islands architecture (Astro, Fresh, Qwik use "islands" terminology)
    "islands": "frontend",           # "islands architecture", "islands framework" → Frontend Frameworks (Astro, Fresh)
    # Frontend — hydration (complement to existing "hydration" → "frontend")
    "hydrate": "frontend",           # "hydrate component", "client hydrate" → Frontend Frameworks
    # Database — NoSQL document stores ("document database", "document store")
    "document": "database",          # "document store", "document database" → Database (MongoDB, Firestore)
    # Frontend — React context API ("react context api", "context provider" queries)
    "context": "frontend",           # "react context", "context provider", "context api" → Frontend Frameworks
    # Frontend — virtual DOM queries (React, Preact, Inferno)
    "vdom": "frontend",              # "virtual dom library", "vdom alternative" → Frontend Frameworks
    "virtual-dom": "frontend",       # hyphenated form — "virtual-dom alternatives" → Frontend Frameworks
    # Testing — test stubs (complement to mock/mocking → testing)
    "stub": "testing",              # "test stub", "http stub", "stub server" → Testing Tools (MSW, WireMock)
    "stubbing": "testing",          # "stubbing http requests", "stubbing dependencies" → Testing Tools
    # Frontend — pagination and infinite scroll components
    "pagination": "frontend",       # "pagination component", "cursor pagination" → Frontend (TanStack Table)
    "paginate": "frontend",         # "paginate results", "paginate api response" → Frontend Frameworks
    # Developer Tools — debugging utilities (pdb, node --inspect, Chrome DevTools protocol)
    "debugger": "developer",        # "node debugger", "python debugger", "remote debugger" → Developer Tools
    "debugging": "developer",       # "debugging tool", "remote debugging", "debug middleware" → Developer Tools
    # AI — OCR and optical character recognition (Tesseract.js, PaddleOCR, pytesseract)
    "ocr": "ai",                    # "ocr library", "ocr api", "ocr tool" → AI & Automation
    # Developer Tools — phone number validation/formatting (libphonenumber-js, phone-fns)
    "phonenumber": "developer",     # "phonenumber library", "phone number validation" → Developer Tools
    "libphonenumber": "developer",  # explicit library name queries → Developer Tools
    # Developer Tools — data/file compression (pako, fflate, lz-string, zstd-wasm)
    "compress": "developer",        # "compress files", "compress data", "js compress" → Developer Tools
    "compression": "developer",     # "compression library", "lossless compression" → Developer Tools
    # Developer Tools — spell checking (cspell, nspell, hunspell bindings)
    "spell": "developer",           # "spell check", "spell checker library" → Developer Tools
    "spellcheck": "developer",      # "spellcheck library", "spellcheck api" → Developer Tools
    # Developer Tools — server-side template engines (Handlebars, Nunjucks, Mustache, EJS)
    "handlebars": "developer",      # Handlebars.js — minimal JS templating (18k★)
    "nunjucks": "developer",        # Nunjucks — Jinja2-inspired templates for Node.js
    "mustache": "developer",        # Mustache — logic-less templates for JS/Python/Ruby
    "jinja": "developer",           # Jinja2 — Python template engine (high search volume)
    "ejs": "developer",             # EJS — embedded JavaScript templating
    # Developer Tools — timezone handling (date-fns-tz, spacetime, temporal)
    "timezone": "developer",        # "timezone library", "timezone conversion" → Developer Tools
    # Note: "luxon" already maps to "frontend" at line 3777 — no duplicate here
    # Maps & Location — named mapping libraries (Leaflet is most-searched maps alternative)
    "leaflet": "maps",              # Leaflet.js — most popular open-source interactive map library (41k★)
    "mapbox": "maps",               # Mapbox GL JS — vector tile map rendering SDK (11k★)
    "openlayers": "maps",           # OpenLayers — full-featured maps in the browser (11k★)
    "gis": "maps",                  # GIS (Geographic Information System) generic queries → Maps & Location
    "cesium": "maps",               # CesiumJS — 3D globes and maps (Cesium ion, open-source, 13k★)
    # API clients / API testing — Postman is the canonical tool; "[tool] alternative" is high-volume
    "postman": "api",               # Postman — most-used API testing and documentation platform
    "insomnia": "api",              # Insomnia — Kong's open-source REST/GraphQL/gRPC client (34k★)
    # Database — SQL migration runners not yet mapped
    "flyway": "database",           # Flyway — SQL database migrations (popular in Java/Spring ecosystem, 8k★)
    "alembic": "database",          # Alembic — SQLAlchemy migration tool for Python (3k★)
    "liquibase": "database",        # Liquibase — database schema version control (13k★)
    "goose": "database",            # Goose — Go database migration tool (6k★)
    # Developer Tools — schema/data validation libraries very commonly searched
    "joi": "developer",             # Joi — most popular JS/TS object schema validation (20k★, pre-Zod era)
    "ajv": "developer",             # AJV — fastest JSON schema validator for Node.js/browser (14k★)
    # AI — image generation models (enormous query volume via stable diffusion synonyms + branded)
    "dalle": "ai",                  # DALL-E — OpenAI image generation; "dalle alternative" high-volume
    "midjourney": "ai",             # Midjourney — popular text-to-image AI; "midjourney alternative" queries
    "sora": "ai",                   # Sora — OpenAI text-to-video model; "sora alternative" growing queries
    # Frontend — WebGL (lower level than Three.js, but queried directly)
    "webgl": "frontend",            # WebGL — browser 3D graphics API; queries route to Three.js/Babylon.js
    "babylon": "frontend",          # Babylon.js — WebGL-based 3D engine (alternative to Three.js, 23k★)
    # Project management — named tools not yet mapped (very common alternative query targets)
    "jira": "project",              # Jira — most-searched PM tool; "jira alternative" is the canonical query
    "clickup": "project",           # ClickUp — all-in-one productivity platform; popular alternative queries
    "basecamp": "project",          # Basecamp — project management + team communication by 37signals
    "plane": "project",             # Plane.so — open-source Jira/Linear alternative (31k★)
    "appflowy": "project",          # AppFlowy — open-source Notion/Confluence alternative (61k★)
    "notion": "cms",                # Notion — used as headless CMS/content source; wiki + CMS queries
    "confluence": "project",        # Confluence — Atlassian wiki/knowledge base (very common alternative query)
    "trello": "project",            # Trello — kanban board; "trello alternative" is a high-volume query
    # DevOps — Git hosting platforms (most common alternative query targets)
    "gitlab": "devops",             # GitLab — self-hosted Git + CI/CD; "gitlab alternative" common query
    "bitbucket": "devops",          # Bitbucket — Atlassian Git hosting + CI/CD
    "gittea": "devops",             # common misspelling of Gitea — still routes correctly
    # API Tools — API gateway named tools not yet mapped
    "kong": "api",                  # Kong — open-source API gateway (38k★); "kong alternative" queries
    # Search — additional engines
    "opensearch": "search",         # OpenSearch — AWS fork of Elasticsearch (16k★)
    "solr": "search",               # Apache Solr — enterprise full-text search (Elasticsearch predecessor)
    # Caching — cluster topology terms (complement to removing "distributed")
    "cluster": "caching",           # "redis cluster", "cache cluster" → Caching
    # Caching — key-value store generic query terms (Upstash, Cloudflare KV, Redis)
    "kv": "caching",                # "KV store", "KV namespace", "Cloudflare KV" → Caching
    "keyvalue": "caching",          # compound — "key-value database", "key-value store" → Caching
    # Maps — geolocation (in NEED_MAPPINGS terms but missing as individual synonym)
    "geolocation": "maps",          # "geolocation API", "browser geolocation", "IP geolocation" → Maps & Location
    "geocode": "maps",              # verb form — "geocode address", "geocode API" (geocoding already mapped)
    "tile": "maps",                 # "map tile server", "tile provider", "vector tiles" → Maps & Location
    "tiles": "maps",                # plural form — "map tiles", "raster tiles", "MVT tiles"
    # Invoicing — usage-based / metered billing (Lago, Orb, Stripe Metering, Stigg)
    "metered": "invoicing",         # "metered billing", "pay-per-use model" → Invoicing & Billing
    "usage": "invoicing",           # "usage-based billing", "usage metering" → Invoicing & Billing
    # Payments — feature entitlements and content paywalls
    "entitlements": "payments",     # "entitlements management", "feature entitlements" (Stigg, Orb)
    "paywall": "payments",          # "paywall implementation", "content paywall" → Payments
    # Auth — passkeys (plural of passkey; singular already mapped at line ~2482)
    "passkeys": "authentication",   # plural — "passkeys support", "implement passkeys" → Authentication
    # API — Django REST Framework (very high query volume in Python ecosystem)
    "drf": "api",                   # DRF — Django REST Framework abbreviation (most common Python API)
    "djangorestframework": "api",   # full canonical package name form → API Tools
    # Database — async Python ORMs (FastAPI + MongoDB ecosystem tools)
    "sqlmodel": "database",         # SQLModel — Pydantic+SQLAlchemy ORM by FastAPI creator (14k★)
    "beanie": "database",           # Beanie — async MongoDB ODM for Python with Pydantic (4k★)
    "tortoise": "database",         # Tortoise ORM — Django-inspired async Python ORM (4k★)
    "tortoise-orm": "database",     # hyphenated form — "tortoise-orm alternative" queries
    # DevOps — OpenTofu (open-source Terraform fork, 22k★)
    "opentofu": "devops",           # OpenTofu — open-source Terraform fork by CNCF (22k★)
    "tofu": "devops",               # short form — "tofu deploy", "opentofu vs terraform" queries
    # Security — fraud detection and KYC/identity verification
    "fraud": "security",            # "fraud detection", "fraud prevention" (Fingerprint, SEON, Stripe Radar)
    "kyc": "security",              # KYC verification — "kyc tool", "know your customer" (Onfido, Persona)
    "spam": "security",             # "spam protection", "spam filter" (Akismet, Cleantalk, hCaptcha)
    # Invoicing — tax calculation for SaaS
    "tax": "invoicing",             # "sales tax API", "VAT compliance", "tax calculation" (Anrok, TaxJar, Avalara)
    # Database — analytical / OLAP query terms
    "timeseries": "database",       # "timeseries database" (compound, no hyphen) — TimescaleDB, InfluxDB, QuestDB
    "olap": "database",             # OLAP (Online Analytical Processing) — ClickHouse, DuckDB, Apache Druid
    "columnar": "database",         # "columnar database", "column-store" — ClickHouse, DuckDB, Redshift alternative queries
    "multimodel": "database",       # "multi-model database" — SurrealDB, ArangoDB, OrientDB queries
    # Low-code / no-code platforms — Retool, Budibase, Appsmith live in Developer Tools
    # compound forms without spaces/hyphens are the most commonly searched by AI agents
    "lowcode": "developer",         # "lowcode platform", "lowcode tool" → Developer Tools
    "nocode": "developer",          # "nocode builder", "nocode app" → Developer Tools
    # Payments — in-app purchase (mobile billing via Apple/Google)
    # "in-app purchase" → "in" and "app" are stop words, "purchase" is the meaningful term
    "iap": "payments",              # IAP (In-App Purchase) abbreviation — RevenueCat, Adapty, Glassfy
    "purchase": "payments",         # "in-app purchase", "one-time purchase" → Payments (RevenueCat, Stripe)
    # Background jobs — compound form without space
    "cronjob": "background",        # "cronjob scheduling", "cronjob service" (compound) → Background Jobs
    # Developer Tools — comment/discussion widgets embedded in websites
    "giscus": "developer",          # Giscus — GitHub Discussions-based comment widget (6k★)
    "disqus": "support",            # Disqus — hosted comment platform (customer-facing discussions)
    # AI — natural language processing (NLP tools live in ai-automation alongside LLM tools)
    "nlp": "ai",                    # "NLP library", "NLP pipeline", "nlp tool" → AI & Automation
    "sentiment": "ai",              # "sentiment analysis", "sentiment classifier" → AI & Automation
    # HTTP client / fetch wrapper libraries — Axios, Got, Ky, undici, node-fetch → api-tools
    "http": "api",                  # "http client", "http request library" → API Tools
    "fetch": "api",                 # "fetch wrapper", "node fetch alternative" → API Tools
    # Date/time utility libraries — date-fns, dayjs, Luxon, Temporal polyfill → frontend-frameworks
    "date": "frontend",             # "date library", "date utility", "date format" → Frontend Frameworks
    # Table and data-grid component libraries → frontend-frameworks
    "table": "frontend",            # "react table", "table component" → TanStack Table, AG Grid
    "grid": "frontend",             # "data grid", "ag grid alternative" → Frontend Frameworks
    # React Server Components — Next.js 13+ RSC pattern, very high query volume
    "rsc": "frontend",              # "RSC alternative", "react server component" → Frontend Frameworks
    "server-component": "frontend", # "server component", "server-component streaming" → Frontend Frameworks
    "server-components": "frontend",# plural — "server components pattern", "react server components"
    "server-actions": "frontend",   # "server actions nextjs", "server action form" → Frontend Frameworks
    # Version managers / JS toolchains — "nvm alternative", "node version manager", "mise setup"
    "nvm": "developer",             # nvm — Node Version Manager (bash, 80k★); most-used node switcher
    "fnm": "developer",             # fnm — Fast Node Manager (Rust, 17k★); faster nvm alternative
    "volta": "developer",           # Volta — JS toolchain manager (pin per-project, 11k★)
    "mise": "developer",            # mise-en-place — polyglot runtime version manager (asdf successor, 12k★)
    "asdf": "developer",            # asdf — multi-language version manager (Ruby, Node, Python, Go)
    # AI — multimodal and vision models (GPT-4V, Claude Vision, Gemini Pro Vision)
    "multimodal": "ai",             # "multimodal AI", "multimodal model", "vision + text model" → AI & Automation
    "computer-vision": "ai",        # "computer vision library", "cv model" → AI & Automation
    "cv": "ai",                     # "cv library", "cv pipeline" (computer vision context) → AI & Automation
    # Web Components — standard browser custom elements (Lit, Stencil, FAST, Shoelace)
    "webcomponent": "frontend",     # "web component library", "webcomponent framework" → Frontend Frameworks
    "webcomponents": "frontend",    # plural — "web components standard", "custom elements" → Frontend Frameworks
    "custom-element": "frontend",   # "custom element", "custom elements API" → Frontend Frameworks (Lit, FAST)
    "custom-elements": "frontend",  # plural form — Web Components Custom Elements spec
    # Testing — integration tests (complement to e2e, unit, bdd, coverage already mapped)
    "integration": "testing",       # "integration test", "integration testing library" → Testing Tools
    # Database — time-series databases not individually mapped
    "influxdb": "database",         # InfluxDB — most popular open-source time-series database (28k★)
    "questdb": "database",          # QuestDB — fast SQL time-series database (14k★)
    "cassandra": "database",        # Apache Cassandra — wide-column distributed NoSQL store
    "scylladb": "database",         # ScyllaDB — C++ Cassandra-compatible (10× faster, 13k★)
    # Security — Zero Trust architecture (growing segment in enterprise security queries)
    "zerotrust": "security",        # "zero trust model", "zerotrust network" → Security Tools
    "zero-trust": "security",       # hyphenated form — "zero-trust architecture", "zero-trust auth"
    # API — rate-limit compound form (complement to "rate"→api, "limit"→api, "limiting"→api)
    "ratelimit": "api",             # "rate-limit" normalised → Unkey, Kong, Upstash Rate Limiting → API Tools
    # Frontend — Web Workers (browser parallelism; Comlink, Partytown, workbox-background-sync)
    "webworker": "frontend",        # "web worker api", "webworker pool" → Frontend Frameworks
    "web-worker": "frontend",       # hyphenated — "web-worker library", "web-worker thread" → Frontend
    # Frontend — Module Federation (webpack/Rspack micro-frontend code splitting)
    "modulefederation": "frontend", # "module federation setup", "module federation plugin" → Frontend
    "module-federation": "frontend",# hyphenated — "module-federation webpack", "module-federation rspack"
    # Frontend — Lottie animation library (airbnb/lottie-web + DotLottie ecosystem)
    "lottie": "frontend",           # Lottie — JSON-based animation format by Airbnb (30k★) → Frontend
    # Frontend — Rive interactive animation (real-time state machine animations)
    "rive": "frontend",             # Rive — interactive real-time animation runtime (8k★) → Frontend
    # Authentication — two-factor auth long forms (complement to "2fa"→auth, "mfa"→auth, "totp"→auth)
    "twofactor": "authentication",  # "two-factor auth setup", "two-factor verification" → Authentication
    "two-factor": "authentication", # hyphenated — "two-factor authentication library" → Authentication
    # AI — AI gateway / LLM proxy tools (Portkey.ai, LiteLLM proxy, OpenRouter)
    "portkey": "ai",                # Portkey.ai — AI gateway: routing, fallbacks, observability (5k★) → AI
    # Developer Tools — JSON Schema tooling (AJV, JSON Schema Validator, openapi-schema-validator)
    "jsonschema": "developer",      # "json schema validator", "jsonschema library" → Developer Tools
    "json-schema": "developer",     # hyphenated — "json-schema validation", "json-schema spec" → Developer Tools
    # AI — data labeling / annotation platforms (Label Studio, Argilla, Prodigy, Scale AI alternatives)
    "labeling": "ai",               # "data labeling tool", "ml labeling platform" → AI & Automation
    "annotation": "ai",             # "data annotation", "training data annotation" → AI & Automation
    # AI — synthetic data generation (Gretel.ai, Mostly AI, SDV, DataSynthesizer)
    "synthetic": "ai",              # "synthetic data", "synthetic training data" → AI & Automation
    # AI — content moderation / LLM output filtering (Perspective API, OpenAI Mod, Llama Guard)
    "moderation": "ai",             # "content moderation api", "llm moderation" → AI & Automation
    # Auth — identity management terminology not yet mapped
    "idp": "authentication",        # IDP (Identity Provider) — Okta, Keycloak, ZITADEL, PingOne
    "iam": "authentication",        # IAM (Identity and Access Management) — authz policy engines
    # Database — embedded, CDC, and column-store query patterns
    "embedded": "database",         # "embedded database" — SQLite, DuckDB, PocketBase
    "cdc": "database",              # Change Data Capture — Debezium, Maxwell, Kafka Connect
    "debezium": "database",         # Debezium — open-source CDC platform for event streaming
    "columnstore": "database",      # "column-store database" (compound, no hyphen) → Database
    # Message queue — additional stream processing platform
    "pulsar": "message",            # Apache Pulsar — distributed message streaming (Kafka alternative)
    # Rust frontend / WASM frameworks — fast-growing query segment
    "leptos": "frontend",           # Leptos — Rust+WASM full-stack reactive web framework (16k★)
    "yew": "frontend",              # Yew — Rust/WASM component model framework (30k★)
    "dioxus": "frontend",           # Dioxus — Rust UI framework for web, desktop, and mobile (18k★)
    "trunk": "frontend",            # Trunk — Rust+WASM build tool and dev server (complement to wasm-pack)
    # CSS frameworks — atomic CSS and zero-runtime styling not yet individually mapped
    "unocss": "frontend",           # UnoCSS — instant on-demand atomic CSS engine (Windi/Tailwind successor, 17k★)
    "windi": "frontend",            # Windi CSS — on-demand utility CSS predecessor to UnoCSS (24k★)
    "pandacss": "frontend",         # Panda CSS — type-safe CSS-in-JS by Chakra UI team (3.5k★)
    "panda": "frontend",            # short form — "panda css alternative", "panda setup" → Frontend
    # PWA — "progressive web app" without the "pwa" abbreviation
    "progressive": "frontend",      # "progressive web app", "progressive enhancement" → Frontend Frameworks
    # SolidJS meta-framework (complement to "solid"→"frontend", "solidjs"→"frontend")
    "solidstart": "frontend",       # SolidStart — SolidJS meta-framework (SSR, file routing, Server Actions)
    # Node.js backend frameworks not yet individually mapped
    "adonisjs": "api",              # AdonisJS — Laravel-inspired full-stack Node.js MVC framework (17k★)
    "adonis": "api",                # short form — "adonis alternative", "adonis vs nestjs" queries
    "hapi": "api",                  # hapi.js — rich Node.js framework by Walmart Labs (14k★)
    "hapijs": "api",                # compound form — "hapijs alternative" queries
    # Kubernetes local dev — complement to k8s/kubernetes/helm/argocd already mapped
    "minikube": "devops",           # Minikube — local Kubernetes cluster (29k★, most-used local k8s)
    "k3s": "devops",                # k3s — lightweight Kubernetes by Rancher/SUSE (28k★)
    "k3d": "devops",                # k3d — run k3s in Docker for local dev (5k★)
    # LLM evaluation and agent observability — fast-growing AI developer query segment
    "braintrust": "ai",             # Braintrust Data — LLM evaluation, tracing, and dataset management
    "agentops": "ai",               # AgentOps — LLM/AI agent session replay and observability (4k★)
    "opik": "ai",                   # Opik (Comet ML) — open-source LLM evaluation and tracing (5k★)
    # Kubernetes tooling — cluster management and developer workflow tools
    "k9s": "devops",                # k9s — terminal-based Kubernetes TUI dashboard manager (27k★)
    "kustomize": "devops",          # Kustomize — Kubernetes-native configuration customization (CNCF)
    "skaffold": "devops",           # Skaffold — k8s build/push/deploy dev workflow tool (Google, 15k★)
    # Database — multi-model and document stores not yet individually mapped
    "arangodb": "database",         # ArangoDB — multi-model graph/document/key-value database (13k★)
    "couchdb": "database",          # Apache CouchDB — document-oriented NoSQL with HTTP API (6k★)
    # Caching — distributed in-memory data grids
    "hazelcast": "caching",         # Hazelcast — open-source distributed in-memory caching + compute
    # Testing — code quality, static analysis, and coverage platforms
    "sonar": "testing",             # SonarQube/SonarCloud shorthand — static analysis + quality gates
    "sonarcloud": "testing",        # SonarCloud — cloud-hosted SonarQube (free for OSS projects)
    "codecov": "testing",           # Codecov — code coverage tracking and PR annotation (10k★)
    "codacy": "testing",            # Codacy — automated code quality and test coverage reports
    "deepsource": "testing",        # DeepSource — static analysis for Python, JS, Go, Ruby
    # CMS — headless CMS tools not yet individually mapped
    "storyblok": "cms",             # Storyblok — headless CMS with visual block editor (SaaS, 2.6k★)
    "tinacms": "cms",               # TinaCMS — open-source Git-backed headless CMS (12k★)
    "contentlayer": "cms",          # ContentLayer — transforms content into type-safe data for Next.js (4k★)
    # AI — AI app builders and IDE coding assistants with fast-growing query volume
    "lovable": "ai",                # Lovable — AI-powered full-stack app builder (React + Supabase)
    "cline": "ai",                  # Cline — open-source AI coding extension (formerly Claude Dev, 38k★)
    "boltnew": "ai",                # Bolt.new (StackBlitz) — AI-powered full-stack app generator in browser
    # Monitoring — ELK stack components not yet individually mapped
    "kibana": "monitoring",         # Kibana — log and metrics visualization for Elasticsearch
    "elk": "monitoring",            # ELK stack — Elasticsearch + Logstash + Kibana (observability)
    # Logging — ELK pipeline component
    "logstash": "logging",          # Logstash — server-side log ingestion and transformation pipeline
    # API — SDK generation tools and developer-focused API gateways
    "speakeasy": "api",             # Speakeasy — type-safe SDK generation from OpenAPI specs (5k★)
    "zuplo": "api",                 # Zuplo — OpenAPI-native developer API gateway with rate limiting
    "stainless": "api",             # Stainless — automatic SDK generation for REST APIs
    "redocly": "api",               # Redocly — OpenAPI documentation, linting, and bundling (7k★)
    "hurl": "api",                  # Hurl — HTTP request testing with plain text files (13k★)
    # Email — email testing / sandbox servers for local development
    "mailpit": "email",             # Mailpit — modern email testing server (MailHog successor, 6k★)
    "mailhog": "email",             # MailHog — SMTP email testing server for local dev (14k★)
    # Developer Tools — JavaScript package registry alternative to npm
    "jsr": "developer",             # JSR (JavaScript Registry) — Deno's modern TypeScript-native package registry
    # Developer Tools — Python project manager and version manager
    "rye": "developer",             # Rye — Python project and package manager by Armin Ronacher (9k★)
    # Message Queue — Go event-driven application library
    "watermill": "message",         # Watermill — Go library for building event-driven applications (8k★)
    # DevOps — service mesh tools (Istio, Linkerd, Cilium, Envoy-based proxies)
    "istio": "devops",              # Istio — most-deployed Kubernetes service mesh (35k★)
    "linkerd": "devops",            # Linkerd — ultralight CNCF service mesh for Kubernetes (10k★)
    "cilium": "devops",             # Cilium — eBPF-based Kubernetes networking + security (19k★)
    "ebpf": "devops",               # eBPF — Linux kernel observability: Cilium, Tetragon, Falco queries
    "sidecar": "devops",            # "sidecar proxy", "sidecar pattern" — service mesh architecture
    "service-mesh": "devops",       # hyphenated form — "service-mesh comparison", "service-mesh setup"
    # AI — LLM observability named tools not yet mapped
    "arize": "ai",                  # Arize AI — LLM observability, tracing, and evaluation platform
    # Developer Tools — WASM runtimes (run WebAssembly outside the browser)
    "wasmtime": "developer",        # Wasmtime — fast, secure standalone WASM runtime (Bytecode Alliance, 15k★)
    "wasmer": "developer",          # Wasmer — universal WASM runtime (supports multiple languages, 18k★)
    # Message Queue — event-driven architecture patterns (CQRS, event sourcing)
    "event-sourcing": "message",    # "event sourcing pattern", "event sourcing library" → Message Queue
    "eventsourcing": "message",     # compound form — "eventsourcing framework" → Message Queue
    "cqrs": "message",              # CQRS — Command Query Responsibility Segregation → Message Queue
    # API — GraphQL federation and supergraph (Apollo Federation, Cosmo Router, WunderGraph)
    "federation": "api",            # "graphql federation", "apollo federation" → API Tools
    "supergraph": "api",            # "supergraph", "apollo supergraph" — federated GraphQL schema
    # Monitoring — VictoriaMetrics (fast Prometheus-compatible TSDB, popular alternative query)
    "victoriametrics": "monitoring",# VictoriaMetrics — high-perf time series DB, Prometheus-compatible (13k★)
    "victoria": "monitoring",       # first term — "victoria metrics alternative", "victoria metrics setup"
    # Security — runtime container security (CNCF Falco)
    "falco": "security",            # Falco — CNCF runtime security for containers and Kubernetes (7k★)
    # Python package / project managers — uv and Poetry dominate 2025 dev tool queries
    "uv": "developer",              # uv — extremely fast Python package installer + resolver by Astral (50k★)
    "poetry": "developer",          # Poetry — Python dependency management with pyproject.toml (28k★)
    "pdm": "developer",             # PDM — Python dependency manager with PEP 582 / lockfile (7k★)
    "pipenv": "developer",          # Pipenv — Python dev workflow tool (virtualenv + pip unified, 24k★)
    "conda": "developer",           # Conda — cross-language package + environment manager (data science)
    "mamba": "developer",           # Mamba — fast C++ conda alternative for env management
    "pixi": "developer",            # Pixi — fast conda-compatible package manager by prefix.dev (4k★)
    # Rust database / ORM tooling — growing fast as Rust web dev adoption increases
    "sqlx": "database",             # sqlx — async pure-Rust SQL toolkit (compile-time checked queries, 13k★)
    "diesel": "database",           # Diesel — safe, extensible ORM for Rust (12k★, type-checked queries)
    "sea-orm": "database",          # SeaORM — async Rust ORM built on sqlx (7k★, Active Record + Data Mapper)
    "seaorm": "database",           # compound form — "seaorm alternative", "seaorm vs diesel" queries
    # Elixir ORM — Ecto is searched alongside Phoenix queries
    "ecto": "database",             # Ecto — Elixir database wrapper + query composition library (6k★)
    # Frontend — React Query (original npm package name before TanStack rebranding)
    "react-query": "frontend",      # React Query — original name; "react-query alternative" high-volume
    "reactquery": "frontend",       # compound form — "reactquery vs swr", "react query v5" queries
    # Frontend — RedwoodJS full-stack React framework (not yet individually mapped)
    "redwood": "frontend",          # RedwoodJS — opinionated full-stack framework (React+GraphQL, 17k★)
    "redwoodjs": "frontend",        # explicit form — "redwoodjs alternative", "redwoodjs starter" queries
    # Media — HLS streaming protocol (very common in video streaming queries)
    "hls": "media",                 # HLS (HTTP Live Streaming) — Apple's adaptive streaming protocol
    "mpeg-dash": "media",           # MPEG-DASH — adaptive bitrate streaming standard (hyphenated form safe)
    # DevOps — JVM build tools (Gradle and Maven are dominant Java/Kotlin build queries)
    "gradle": "devops",             # Gradle — build automation for Java, Kotlin, Android (17k★)
    "maven": "devops",              # Apache Maven — Java build/project management tool (classic)
    # Developer Tools — code scaffolding and generator tools
    "plop": "developer",            # Plop.js — micro-generator framework for consistent boilerplate (6k★)
    "hygen": "developer",           # Hygen — scalable code generator built for teams (5k★)
    "yeoman": "developer",          # Yeoman — classic scaffolding tool for web projects (4k★)
    # Caching — "in-memory" query routing (hyphen stripped to single token in raw split)
    "in-memory": "caching",         # "in-memory cache", "in-memory database" — Redis, Memcached, Upstash
    "memory": "caching",            # "in memory" after stop-word strip: "in" removed → "memory" first term
    "inmemory": "caching",          # compound form — "inmemory store", "inmemory cache" → Caching
    # Security — certificate/TLS management tools (Let's Encrypt ecosystem)
    "letsencrypt": "security",      # Let's Encrypt — free, automated TLS certificate authority (by ISRG)
    "certbot": "security",          # Certbot — EFF ACME client for Let's Encrypt (most-used, 31k★)
    "step-ca": "security",          # step-ca — self-hosted certificate authority (smallstep, 7k★)
    "smallstep": "security",        # smallstep — brand name for step-ca and step CLI PKI tooling
    # AI — agentic / multi-agent system queries (fast-growing query segment 2026)
    "agentic": "ai",                # "agentic AI", "agentic system", "agentic workflow" → AI & Automation
    "multiagent": "ai",             # compound — "multiagent framework", "multi-agent system" → AI & Automation
    "llmops": "ai",                 # LLMOps — ML operations for LLM apps (MLflow-style but for LLMs)
    "tuning": "ai",                 # "fine-tuning" → hyphen stripped → "fine" "tuning"; "tuning" fires → AI
    # AI — LLM application platforms (no-code/low-code LLM builder tools)
    "dify": "ai",                   # Dify — open-source LLM application platform and RAG engine (60k★)
    "openwebui": "ai",              # Open WebUI — feature-rich web UI for Ollama/local LLMs (80k★)
    "open-webui": "ai",             # hyphenated form — "open-webui alternative" queries → AI & Automation
    # Identity — common query prefix not yet individually mapped
    "identity": "authentication",   # "identity provider", "identity management", "digital identity" → Authentication
    # FaaS — Function as a Service (serverless function alternatives)
    "faas": "devops",               # "FaaS alternative", "function as a service", "faas platform" → DevOps
    # Batch processing — complement to background-job synonyms (cron/queue/worker/scheduler)
    "batch": "background",          # "batch job", "batch processing", "batch queue" → Background Jobs
    # API endpoint — extremely common term missing from synonyms
    "endpoint": "api",              # "API endpoint", "endpoint testing", "REST endpoint" → API Tools
    # Type checking — TypeScript/Python type checking tools (mypy, pyright, tsc)
    "typecheck": "testing",         # "typecheck tool", "typecheck script" → Testing Tools (mypy, tsc, Pyright)
    "typechecking": "testing",      # long form — "typechecking in CI", "typechecking library" → Testing Tools
    # Package manager — routes to developer, not frontend (which "manager" → "frontend" would give)
    "package": "developer",         # "package manager", "package registry" → Developer Tools (npm, pnpm, Rye, uv)
    # Service worker — hyphenated form splits to "service"[unmapped] + "worker"[→background]
    "service-worker": "frontend",   # "service-worker caching", "service-worker library" → Frontend (Workbox)
    # Task runner — "task" not currently mapped; "task runner" queries (Grunt, Gulp, Nx run, Make)
    "task": "developer",            # "task runner", "task automation", "build task" → Developer Tools
    "runner": "developer",          # complement — "task runner", "script runner" → Developer Tools
    # Ingress controller — Kubernetes/reverse proxy routing
    "ingress": "devops",            # "ingress controller", "kubernetes ingress", "ingress rule" → DevOps
    # immer — immutable state library
    "immer": "frontend",            # Immer — produce next immutable state via mutations (26k★)
    # Medusa — open-source commerce
    "medusa": "developer",          # Medusa — open-source headless commerce engine (23k★)
    # Compiler / transpiler tools (Babel, SWC, Binaryen, esbuild — frontend build chain)
    "compiler": "frontend",         # "js compiler", "typescript compiler", "babel compiler" → Frontend Frameworks
    # Validation — complement to "validation" → developer; "validate" form catches verb queries
    "validate": "developer",        # "validate schema", "validate input", "data validate" → Developer Tools
    # OXC toolchain — Rust-based JS/TS tools (oxlint, rolldown, oxc-transform)
    "oxlint": "testing",            # OXLint — Rust-based JS/TS linter (50-100x faster than ESLint, 5k★)
    "oxc": "frontend",              # OXC (Oxidation Compiler) — Rust JS/TS toolchain: linter + bundler + parser
    "rolldown": "frontend",         # Rolldown — Rust-based bundler replacing Rollup in Vite 6 (9k★)
    # Dead code elimination — Knip finds unused exports/files/dependencies in TypeScript
    "knip": "developer",            # Knip — TypeScript dead code finder (unused exports, files, deps) (7k★)
    # Search / RAG — Trieve combines search + RAG + recommendations in one API
    "trieve": "search",             # Trieve — search, RAG, and recommendations platform (2k★)
    # API composition / data fetching — WunderGraph unifies APIs into a single GraphQL layer
    "wundergraph": "api",           # WunderGraph — API composition gateway (GraphQL, REST, gRPC, 2k★)
    # Serverless scripting — Val Town lets you write/run TypeScript scripts with HTTP triggers
    "valtown": "developer",         # Val Town — serverless TypeScript scripting platform (run code as API, 3k★)
    "val": "developer",             # short form — "val town alternative", "val.town serverless" queries
    # Frontend — Farm (Rust-based build tool, Vite-compatible, extremely fast cold starts)
    "farm": "frontend",             # Farm — Rust-based web build tool (Vite-compatible, 10k★)
    # Developer Tools — Rslib (Rsbuild-based library build tool, recommended for publishing npm packages)
    "rslib": "frontend",            # Rslib — Rsbuild-based library bundler for publishing npm/ESM packages
    # API — Relay (Meta's production-ready GraphQL client for React, 18k★)
    "relay": "api",                 # Relay — Meta's GraphQL client for React (declarative data, 18k★)
    # Developer — Turbo (Turborepo CLI short form; "turbo run build", "turbo monorepo" queries)
    "turbo": "developer",           # Turbo — CLI name for Turborepo monorepo build system (25k★)
    # DevOps — Wrangler (Cloudflare's CLI for Workers, Pages, D1, KV, R2 deployment)
    "wrangler": "devops",           # Wrangler — Cloudflare CLI for deploying Workers and Pages (10k★)
    # API — Kotlin/Gleam language queries route to API tools
    "kotlin": "api",                # Kotlin — JVM/multiplatform language; backend queries → Ktor, Spring (50k★)
    "gleam": "api",                 # Gleam — type-safe BEAM language; "gleam web framework" → API Tools (18k★)
    # Developer — Zig language tooling queries
    "zig": "developer",             # Zig — fast systems language; "zig build tool", "zig alternative" (11k★)
    # Monitoring — OpenReplay (open-source session replay + DevTools + observability)
    "openreplay": "monitoring",     # OpenReplay — open-source Hotjar/FullStory alternative (10k★)
    # Logging — Axiom (cloud log management and analytics; Logtail/Papertrail alternative)
    "axiom": "logging",             # Axiom — developer-first log management and analytics (5k★)
    # Changelog generation — git-cliff, semantic-release, release-it, conventional-changelog
    "changelog": "devops",          # "changelog generator", "changelog from git" → DevOps (git-cliff, semantic-release)
    # Data lakehouse / table formats — Apache Iceberg, Delta Lake, Apache Hudi
    "lakehouse": "database",        # "data lakehouse", "lakehouse architecture" → Database
    "iceberg": "database",          # Apache Iceberg — open table format for huge analytic datasets (9k★)
    "delta": "database",            # Delta Lake — ACID transactions on data lakes (Databricks, 7k★)
    "hudi": "database",             # Apache Hudi — streaming data lake platform (7k★)
    # Apache Spark — unified analytics engine for large-scale data processing
    "spark": "background",          # Apache Spark — distributed batch + stream processing engine (40k★)
    # Visual regression testing — Chromatic, Percy, Playwright screenshot tests
    "visual": "testing",            # "visual regression test", "visual testing tool" → Testing Tools
    # JVM / Kotlin backend frameworks — growing as Kotlin adoption rises
    "ktor": "api",                  # Ktor — Kotlin async web framework by JetBrains (12k★)
    "quarkus": "api",               # Quarkus — Supersonic Subatomic Java (GraalVM native, 14k★)
    "vertx": "api",                 # Eclipse Vert.x — reactive Java/JVM toolkit (14k★)
    "micronaut": "api",             # Micronaut — JVM microservices with compile-time DI (6k★)
    # Databricks — unified data + AI platform (very common alternative query)
    "databricks": "ai",             # Databricks — unified data lakehouse + AI/ML platform
    # ML feature stores — Feast, Hopsworks, Tecton
    "feast": "ai",                  # Feast — open-source ML feature store (6k★)
    "hopsworks": "ai",              # Hopsworks — ML platform + feature store (1k★)
    "feature-store": "ai",          # "feature store", "ml feature store" → AI & Automation
    "featurestore": "ai",           # compound form — "featurestore alternative" → AI & Automation
    # GraalVM — native image compilation for Java/JVM apps
    "graalvm": "devops",            # GraalVM — polyglot JVM with native image compilation (22k★)
    # Data visualization — generic "visualization" term
    "visualization": "analytics",  # "data visualization library", "visualization tool" → Analytics & Metrics
    "viz": "analytics",             # abbreviation — "data viz", "viz library", "viz component" → Analytics
    # Data science / Python ecosystem — DataFrame, numeric, and scientific computing tools
    "polars": "database",           # Polars — Rust DataFrame library, fast pandas alternative (34k★)
    "pandas": "ai",                 # pandas — Python data analysis and DataFrame library (44k★)
    "numpy": "ai",                  # NumPy — fundamental scientific computing for Python (28k★)
    "scipy": "ai",                  # SciPy — scientific algorithms and math for Python (13k★)
    "matplotlib": "analytics",      # Matplotlib — foundational Python plotting library (19k★)
    "seaborn": "analytics",         # Seaborn — statistical data visualization on Matplotlib (12k★)
    # Distributed computing / parallel Python — Ray (ML), Dask (big data)
    "ray": "ai",                    # Ray — distributed ML and parallel compute framework (35k★)
    "dask": "background",           # Dask — parallel Python computing for big data (12k★)
    # Cloudflare D1 — serverless SQLite database
    "d1": "database",               # Cloudflare D1 — serverless SQLite database on Workers
    # CLI frameworks — Go Cobra and Node.js Clack
    "cobra": "cli",                 # Cobra — dominant Go CLI framework used by Docker, kubectl, Hugo (38k★)
    "clack": "cli",                 # Clack — modern Node.js interactive CLI prompts (3k★)
    # Computer vision / autonomous agents
    "computer": "ai",               # "computer vision library", "computer use API" → AI & Automation
    # Caching — Varnish HTTP accelerator
    "varnish": "caching",           # Varnish Cache — high-performance HTTP reverse proxy + cache (11k★)
    # AI — audio/video transcription tools
    "transcription": "ai",          # "transcription API", "audio transcription" → AI & Automation
    # AI — standalone "vision" term
    "vision": "ai",                 # "vision model", "vision API", "LLM vision" → AI & Automation
    # Auth — attribute-based access control
    "abac": "authentication",       # ABAC — attribute-based access control → Authentication
    # DevOps — localhost tunneling tools
    "localtunnel": "devops",        # LocalTunnel — expose localhost to the web → DevOps
    "zrok": "devops",               # zrok — self-hosted ngrok alternative → DevOps
    # DevOps — IaC tools for Azure and AWS
    "bicep": "devops",              # Azure Bicep — domain-specific language for IaC on Azure
    "cdk": "devops",                # AWS CDK — Cloud Development Kit (TypeScript/Python/Java IaC)
    # Analytics — session recording / heatmaps
    "hotjar": "analytics",          # Hotjar — heatmaps, session recordings, and user feedback
    "clarity": "analytics",         # Microsoft Clarity — free heatmaps + session recordings → Analytics
    # Monitoring — FullStory session replay
    "fullstory": "monitoring",      # FullStory — enterprise session replay and digital experience analytics
    # Auth — FusionAuth CIAM platform
    "fusionauth": "authentication", # FusionAuth — customer identity and access management (CIAM) platform (10k★)
    # MCP — ModelContextProtocol full name
    "modelcontextprotocol": "mcp",  # ModelContextProtocol — MCP specification and registry → MCP Servers
    # jQuery — most downloaded JS library ever; still widely searched
    "jquery": "frontend",           # jQuery — DOM manipulation library (65k★) → Frontend Frameworks
    "jqueryui": "frontend",         # jQuery UI — interaction and widget library for jQuery → Frontend
    # RxJS — Reactive Extensions for JavaScript (Angular core dependency)
    "rxjs": "frontend",             # RxJS — reactive programming for JS (31k★, Angular core) → Frontend Frameworks
    # Utility libraries — Lodash, Underscore, Ramda
    "lodash": "developer",          # Lodash — JS utility library (59k★, one of most downloaded ever) → Developer Tools
    "underscore": "developer",      # Underscore.js — classic functional JS utilities (27k★) → Developer Tools
    "ramda": "developer",           # Ramda — functional programming library for JS (23k★) → Developer Tools
    # Nuxt.js compound form
    "nuxtjs": "frontend",           # NuxtJS — compound query form for Nuxt.js meta-framework
    # AngularJS — Angular 1.x legacy framework
    "angularjs": "frontend",        # AngularJS — Angular 1.x MVVM framework (59k★, legacy queries)
    # GraphQL Yoga — popular GraphQL server
    "yoga": "api",                  # GraphQL Yoga — flexible GraphQL server (The Guild, 8k★) → API Tools
    # Helmet.js — Express HTTP security headers middleware
    "helmet": "security",           # Helmet.js — secure Express apps via HTTP headers (62k★) → Security Tools
    # VS Code — most-used code editor; extension/plugin queries route to Developer Tools
    "vscode": "developer",          # VS Code — most-used code editor; extension/plugin queries → Developer Tools
    # act — run GitHub Actions locally
    "act": "devops",                # act — run GitHub Actions locally (nektos/act, 59k★) → DevOps & Infrastructure
    # Oh My Zsh / Starship — shell config framework and prompt
    "ohmyzsh": "developer",         # Oh My Zsh — Zsh config framework (174k★) → Developer Tools
    "starship": "developer",        # Starship — blazing-fast cross-shell prompt (Rust, 45k★) → Developer Tools
    # VPN / mesh networking — Tailscale, WireGuard, NetBird, ZeroTier
    "vpn": "devops",                # generic VPN queries → DevOps & Infrastructure
    "wireguard": "devops",          # WireGuard — modern VPN protocol (Linux kernel, fast, minimal) → DevOps
    "tailscale": "devops",          # Tailscale — zero-config mesh VPN built on WireGuard (18k★) → DevOps
    "netbird": "devops",            # NetBird — open-source Tailscale alternative (11k★) → DevOps
    "zerotier": "devops",           # ZeroTier — peer-to-peer virtual Ethernet (14k★) → DevOps
    "headscale": "devops",          # Headscale — self-hosted Tailscale control server (24k★) → DevOps
    # CLI productivity tools — tmux, fzf, zoxide
    "tmux": "cli",                  # tmux — terminal multiplexer (34k★) → CLI Tools
    "fzf": "cli",                   # fzf — fuzzy finder for the command line (64k★) → CLI Tools
    "zoxide": "cli",                # zoxide — smarter cd command (24k★) → CLI Tools
    "bat": "cli",                   # bat — better cat with syntax highlighting (48k★) → CLI Tools
    "ripgrep": "developer",         # ripgrep — extremely fast grep replacement (47k★) → Developer Tools
    "jq": "developer",              # jq — JSON processor for the command line (29k★) → Developer Tools
    "yq": "developer",              # yq — YAML/JSON/XML processor, jq wrapper (12k★) → Developer Tools
    # Web3 / blockchain development — fast-growing developer query segment (Hardhat, Foundry, ethers.js)
    "blockchain": "developer",      # "blockchain development", "blockchain dev tools" → Developer Tools
    "solidity": "developer",        # Solidity — Ethereum smart contract language
    "ethers": "developer",          # ethers.js — TypeScript/JS library for Ethereum interaction (8k★)
    "hardhat": "developer",         # Hardhat — Ethereum development environment (compile, test, deploy, 7k★)
    "wagmi": "developer",           # wagmi — React Hooks for Ethereum (Config + core, 7k★)
    "viem": "developer",            # viem — TypeScript Ethereum interface (low-level, wagmi foundation, 5k★)
    # Mobile — iOS/Swift and Android/Jetpack development queries
    "android": "frontend",          # Android app development — React Native, Flutter, Capacitor alternatives
    "ios": "frontend",              # iOS/iPadOS development queries → mobile frameworks (React Native, Expo)
    "swiftui": "frontend",          # SwiftUI — Apple's declarative UI framework for iOS/macOS
    "swift": "frontend",            # Swift — Apple's programming language (iOS/macOS/visionOS)
    "jetpack": "frontend",          # Android Jetpack Compose — Google's modern declarative Android UI
    # Mobile / offline database
    "realm": "database",            # Realm — offline-first mobile database (MongoDB Realm, iOS/Android, 12k★)
    # Shell — Fish Shell (interactive, Bash/Zsh replacement)
    "fish": "cli",                  # Fish Shell — friendly interactive shell (fish-shell/fish-shell, 26k★)
    # AI — plural forms and LLM interaction patterns (new terms growing in agent query volume)
    "agents": "ai",                 # plural "agents" — "AI agents framework", "multi-agent system" queries
    "hybrid": "search",             # "hybrid search" — BM25+vector combined retrieval (key RAG term)
    "toolcalling": "ai",            # compound — "toolcalling api", "tool calling llm" → AI & Automation
    "function-calling": "ai",       # hyphenated — "function-calling openai", "function-calling spec" → AI
    # Frontend — React Three Fiber (declarative Three.js for React, 27k★)
    "r3f": "frontend",              # R3F abbreviation — "r3f alternative", "r3f tutorial" → Frontend Frameworks
    "react-three-fiber": "frontend",# full form — "react-three-fiber alternative", "r3f vs threejs" → Frontend
    # Message Queue — Apache ActiveMQ (classic enterprise JMS broker)
    "activemq": "message",          # Apache ActiveMQ — enterprise JMS message broker (widely deployed)
    # DevOps — HashiCorp Nomad workload orchestrator
    "nomad": "devops",              # HashiCorp Nomad — flexible workload orchestrator (containers + VMs, 15k★)
    # Developer Tools — Foundry Ethereum toolchain (Forge + Cast + Anvil)
    "foundry": "developer",         # Foundry — professional Ethereum toolkit: Forge (test), Cast (CLI), Anvil (node)
    # Auth — Frontegg enterprise B2B identity platform
    "frontegg": "authentication",   # Frontegg — B2B SaaS user management and identity platform
    # API — additional Python async frameworks
    "sanic": "api",                 # Sanic — async Python web framework, Flask-style API (sanic-org/sanic, 18k★)
    "strawberry": "api",            # Strawberry GraphQL — Python type-annotated GraphQL library (4k★)
    # AI — ML model serving frameworks
    "bentoml": "ai",                # BentoML — open-source model serving + deployment framework (bentoml/bentoml, 7k★)
    # Auth — Authentik self-hosted identity provider
    "authentik": "authentication",  # Authentik — self-hosted SSO/IdP (goauthentik/authentik, 15k★)
    # DevOps — Earthly reproducible builds + Taskfile task runner
    "earthly": "devops",            # Earthly — reproducible containerised build system (12k★)
    "taskfile": "devops",           # Taskfile — modern YAML-based Makefile alternative (go-task, 10k★)
    # AI — fast inference cloud providers (open-weight model APIs)
    "fireworks": "ai",              # Fireworks AI — fastest open-source LLM inference API
    "cerebras": "ai",               # Cerebras — wafer-scale chip AI inference (ultra-fast)
    # Database — distributed SQL and graph-relational databases
    "edgedb": "database",           # EdgeDB — graph-relational DB with EdgeQL (14k★)
    "cockroach": "database",        # CockroachDB — distributed SQL, Postgres-compatible (30k★)
    # Monitoring — open-source observability platforms
    "coroot": "monitoring",         # Coroot — eBPF zero-instrumentation observability (5k★)
    "openobserve": "monitoring",    # OpenObserve — 10× cheaper Datadog alt, logs+metrics+traces (14k★)
    # AI — scikit-learn and HuggingFace Transformers (high ML developer query volume)
    "sklearn": "ai",                # scikit-learn abbreviation — "sklearn alternative"
    "scikit": "ai",                 # scikit-learn prefix — "scikit-learn alternative"
    "transformers": "ai",           # HuggingFace Transformers — most popular ML library (130k★)
    # Email — deliverability authentication (very common infra queries from indie makers)
    "dkim": "email",                # DKIM — DomainKeys Identified Mail (email signing DNS record)
    "spf": "email",                 # SPF — Sender Policy Framework (authorised sender DNS record)
    "dmarc": "email",               # DMARC — email auth policy ("dmarc setup", "dmarc tool" queries)
    # Caching — eviction policy query terms (most common caching algorithm searched)
    "lru": "caching",               # LRU (Least Recently Used) — "lru cache library", "lru eviction"
    # Auth — federated identity (SAML/OIDC, complement to "federation"→api for GraphQL federation)
    "federated": "authentication",  # "federated identity", "federated login" → Authentication
    # Monitoring — SRE reliability engineering terminology (growing query segment from platform teams)
    "slo": "monitoring",            # SLO — Service Level Objective ("slo tracking", "slo dashboard")
    "sli": "monitoring",            # SLI — Service Level Indicator ("sli definition tool")
    # Frontend — autocomplete and combobox UI widgets (complement to search-UI queries)
    "autocomplete": "frontend",     # "autocomplete component", "react autocomplete" → Frontend Frameworks
    "combobox": "frontend",         # "combobox component", "accessible combobox" → Frontend (Radix, Downshift)
    # Search — typeahead pattern (search-as-you-type UX; distinct from combobox UI widget)
    "typeahead": "search",          # "typeahead search", "typeahead input" → Search (Algolia, Typesense)
    # Monitoring — OpenTelemetry Protocol (complement to "otel"→monitoring; used in SDK config queries)
    "otlp": "monitoring",           # OTLP — OpenTelemetry Protocol (wire format; "otlp exporter" queries)
    # API — Buf protobuf toolchain (modern Protobuf DX, 5k★; "buf lint", "buf generate" queries)
    "buf": "api",                   # Buf — developer-first Protobuf toolchain → API Tools
    # Headless commerce / e-commerce platforms (Medusa, Saleor, Vendure live in Developer Tools)
    "ecommerce": "developer",       # "ecommerce platform", "headless ecommerce" → Developer Tools
    "commerce": "developer",        # generic "commerce engine", "headless commerce" → Developer Tools
    "storefront": "developer",      # "headless storefront", "custom storefront" → Developer Tools
    "shopify": "developer",         # "shopify alternative" — Medusa, Saleor, Vendure → Developer Tools
    "woocommerce": "developer",     # "woocommerce alternative" — headless commerce engines
    "saleor": "developer",          # Saleor — open-source headless commerce platform (20k★)
    "medusajs": "developer",        # compound form — "medusajs alternative", "medusa.js" → Developer Tools
    "vendure": "developer",         # Vendure — TypeScript headless commerce framework (5k★)
    "cart": "payments",             # "shopping cart", "cart library" → Payments (checkout flow)
    # Monorepo — Lerna (complement to turborepo/nx already mapped)
    "lerna": "developer",           # Lerna — original JS monorepo management tool (35k★) → Developer Tools
    # AI — reasoning models (o1, DeepSeek-R1, Claude extended thinking queries)
    "reasoning": "ai",              # "reasoning model", "reasoning LLM", "o1 alternative" → AI & Automation
    "thinking": "ai",               # "extended thinking", "thinking tokens", "thinking model" → AI & Automation
    # Frontend — React hooks singular form (complement to "hooks"→frontend already mapped)
    "hook": "frontend",             # "react hook library", "custom hook", "use hook" → Frontend Frameworks
    # Database — connection pool queries (PgBouncer, PgCat, Odyssey, pgpool)
    "pool": "database",             # "connection pool", "db pool", "postgres pool" → Database
    "pooler": "database",           # "connection pooler", "postgres pooler" → Database (PgBouncer, PgCat)
    # DevOps — container and artifact registry queries (Harbor, Quay, Zot, GHCR alternatives)
    "registry": "devops",           # "container registry", "image registry", "oci registry" → DevOps
    "harbor": "devops",             # Harbor — CNCF container image registry with RBAC and replication (22k★)
    # Background jobs — data/log ingestion pipeline queries (Airbyte, Kafka Connect, Debezium)
    "ingestion": "background",      # "data ingestion pipeline", "log ingestion" → Background Jobs / ETL
    "ingest": "background",         # verb form — "ingest data", "ingest logs" → Background Jobs
    # AI — LLM output queries (Instructor, Outlines, Guardrails; misrouted by removed "structured"→logging)
    "output": "ai",                 # "structured output", "llm output", "model output" → AI & Automation
    # AI — Pydantic AI compound form (complement to "pydantic-ai" already mapped)
    "pydanticai": "ai",             # compound — "pydanticai agent", "pydanticai framework" → AI & Automation
    # AI — OpenAI Agents SDK (Python SDK for building AI agents; "openai-agents install" queries)
    "openai-agents": "ai",          # OpenAI Agents SDK — Python multi-agent framework → AI & Automation
    # Background jobs — Restate durable workflow engine (TypeScript/Java; restatedev/restate, 9k★)
    "restate": "background",        # Restate — durable functions + event-driven workflows → Background Jobs
    # Background jobs — compound form of trigger.dev (period stripped in token normalisation)
    "triggerdev": "background",     # compound — "triggerdev alternative", "triggerdev open-source" → Background Jobs
    # Message queue — Upstash QStash (serverless HTTP message queue + scheduling; Upstash ecosystem)
    "qstash": "message",            # QStash — serverless message queue + delay queue by Upstash → Message Queues
    # Customer support — Chatwoot open-source Intercom/Zendesk alternative (chatwoot/chatwoot, 22k★)
    "chatwoot": "support",          # Chatwoot — self-hosted omnichannel customer support → Customer Support
    # Scheduling — compound form of "cal.com" (period stripped in token normalisation)
    "calcom": "scheduling",         # compound — "calcom alternative", "calcom self-hosted" → Scheduling & Booking
    # CRM — Twenty open-source Salesforce/HubSpot alternative (twentyhq/twenty, 25k★)
    "twenty": "crm",                # Twenty — open-source CRM, Salesforce alternative → CRM & Sales
    # Developer Tools — NocoDB open-source Airtable alternative (nocodb/nocodb, 51k★)
    "nocodb": "developer",          # NocoDB — turn any DB into a smart spreadsheet/Airtable → Developer Tools
    # Developer Tools — Baserow open-source no-code database platform (bram2w/baserow, 4k★)
    "baserow": "developer",         # Baserow — open-source Airtable/database platform → Developer Tools
    # Frontend — Ant Design UI ecosystem (most-searched enterprise React UI; "antd" is the npm package name)
    "antd": "frontend",              # Ant Design — enterprise React UI library (93k★); "antd install", "antd alternative"
    "ant": "frontend",               # bare term — "ant design alternative", "ant ui component" → Frontend Frameworks
    # Frontend — NextUI (shadcn/ui competitor; "nextui alternative" growing query segment, 22k★)
    "nextui": "frontend",            # NextUI — beautifully designed React UI library (22k★)
    # Frontend — PrimeTek component libraries for React and Vue (frequently searched in enterprise stacks)
    "primereact": "frontend",        # PrimeReact — 90+ React UI components, enterprise-grade (10k★)
    "primevue": "frontend",          # PrimeVue — comprehensive Vue.js UI component library (10k★)
    # Frontend — React Native mobile UI libraries (very common in RN starter/alternative queries)
    "nativebase": "frontend",        # NativeBase — React Native component library (20k★, Gluestack predecessor)
    "tamagui": "frontend",           # Tamagui — universal UI kit for React Native + web (11k★)
    "gluestack": "frontend",         # Gluestack UI — universal components (Gluestack/NativeBase successor)
    # AI — LLM memory and stateful agent frameworks (high query volume as devs add long-term memory to AI apps)
    "letta": "ai",                   # Letta — LLM memory OS + stateful agents (formerly MemGPT, 33k★)
    "memgpt": "ai",                  # MemGPT — original name for Letta; "memgpt alternative" queries still active
    # Auth — CASL authorization library (most popular JS RBAC/ABAC library, 5k★)
    "casl": "authentication",        # CASL.js — attribute-based authorization for JS/TS → Authentication
    # Developer Tools — TypeBox JSON Schema type builder for TypeScript (7k★)
    "typebox": "developer",          # TypeBox — JSON Schema Type Builder with static TypeScript types (7k★)
    # AI — Google Firebase Genkit (TypeScript/Go AI app framework, growing fast in 2025-2026)
    "genkit": "ai",                  # Genkit — Firebase AI framework for building AI-powered apps (5k★) → AI & Automation
    # AI — Microsoft Semantic Kernel (AI orchestration SDK for C#/Python/Java)
    "semantickernel": "ai",          # Semantic Kernel — Microsoft AI SDK; compound form (22k★) → AI & Automation
    "semantic-kernel": "ai",         # hyphenated — "semantic-kernel alternative", "semantic-kernel python" → AI
    # AI — RAGFlow open-source RAG platform (very high query volume, 28k★ in 2026)
    "ragflow": "ai",                 # RAGFlow — open-source RAG engine by InfiniFlow (28k★) → AI & Automation
    # Database — local-first / offline sync tools (growing segment alongside CRDT/ElectricSQL)
    "replicache": "database",        # Replicache — local-first sync engine by Rocicorp → Database
    "powersync": "database",         # PowerSync — offline-first real-time sync by JourneyApps → Database
    "instantdb": "database",         # InstantDB — realtime Firebase alternative (instantdb/instant) → Database
    # API — Spring Boot compound/hyphenated forms (complement to "spring"→"api" already mapped)
    "springboot": "api",             # Spring Boot — compound form; "springboot alternative" queries → API Tools
    "spring-boot": "api",            # hyphenated — "spring-boot vs quarkus", "spring-boot tutorial" → API Tools
    # API — "monolith" query routing (monolith vs microservices → API tools with backend frameworks)
    "monolith": "api",               # "monolith architecture", "modular monolith" → API Tools (Rails, Django)
    # Frontend — Astro compound form (complement to "astro"→"frontend" already mapped)
    "astrojs": "frontend",           # AstroJS — compound form; "astrojs alternative", "astrojs tutorial" → Frontend
    # API — Express.js compound form (complement to "express"→"api" already mapped)
    "expressjs": "api",              # ExpressJS — compound form; "expressjs alternative", "expressjs tutorial" → API
    # Frontend — Nuxt 3 version-specific queries (complement to "nuxt"→frontend, "nuxtjs"→frontend)
    "nuxt3": "frontend",            # Nuxt 3 — "nuxt3 starter", "nuxt3 alternative", "nuxt3 setup" queries → Frontend Frameworks
    # Frontend — Rsbuild build tool (ByteDance, Rspack-based, 9k★)
    "rsbuild": "frontend",          # Rsbuild — Rspack-based build tool; "rsbuild alternative", "rsbuild vite" → Frontend Frameworks
    # Frontend — Zag.js state machines for UI component logic (4k★)
    "zag": "frontend",              # Zag.js — state machines for accessible UI components (used by Chakra/Ark UI) → Frontend Frameworks
    # DevOps — SST (Serverless Stack) AWS IaC framework (21k★)
    "sst": "devops",                # SST Ion — AWS-native IaC framework; "sst alternative", "sst deploy" → DevOps & Infrastructure
    # DevOps — SSH tooling queries (SSH tunnels, SSH keys, SSH servers)
    "ssh": "devops",                # SSH tools — key management, tunneling, bastion hosts → DevOps & Infrastructure
    # Auth — OpenAuth.js (open-source auth framework by SST team)
    "openauth": "authentication",   # OpenAuth.js — open-source standards-based auth framework (SST team) → Authentication
    # Testing — promptfoo LLM testing and red-teaming (5k★)
    "promptfoo": "testing",         # promptfoo — LLM testing, red-teaming, and evaluation CLI (5k★) → Testing Tools
    # Developer Tools — oslo.js auth utility library (Lucia Auth base, very commonly installed)
    "oslo": "developer",            # oslo.js — JavaScript auth utility library (base of Lucia Auth) → Developer Tools
    # AI — LlamaParse document parsing for RAG pipelines (LlamaIndex team)
    "llamaparse": "ai",             # LlamaParse — high-accuracy document parser for LLM/RAG pipelines → AI & Automation
    # Developer Tools — URL/link shortener tools (Dub.co, YOURLS, Kutt)
    "shortener": "developer",       # "url shortener", "link shortener" → Developer Tools (Dub.co, YOURLS, Kutt)
    # CLI — oclif open-source CLI framework by Salesforce (8k★)
    "oclif": "cli",                 # oclif — open CLI framework by Salesforce; "oclif alternative" → CLI Tools
    # Database — ChromaDB explicit compound form (complement to "chroma"→database already mapped)
    "chromadb": "database",         # ChromaDB — explicit compound form for "chromadb alternative" queries → Database
    # Frontend — Vinxi app bundler (powers TanStack Start and SolidStart; "vinxi alternative" queries)
    "vinxi": "frontend",            # Vinxi — file-based app bundler by Nikhil Saraf (powers TanStack Start, SolidStart)
    # Frontend — TanStack Start meta-framework (React SSR + file routing; competitor to Next.js)
    "tanstack-start": "frontend",   # TanStack Start — hyphenated form; "tanstack-start vs nextjs" queries
    "tanstackstart": "frontend",    # TanStack Start — compound form; "tanstackstart alternative" queries
    # Frontend — Qwik City meta-framework (Qwik's file-based router + SSR layer)
    "qwik-city": "frontend",        # Qwik City — hyphenated form; "qwik-city alternative", "qwik-city vs nextjs"
    "qwikcity": "frontend",         # Qwik City — compound form; "qwikcity tutorial", "qwikcity routing" queries
    # Developer — tsup TypeScript library bundler (esbuild-powered, most common npm package build tool, 9k★)
    "tsup": "developer",            # tsup — bundle TypeScript libraries with no config (esbuild-backed, 9k★)
    # Developer — microbundle zero-config bundler for npm packages (8k★)
    "microbundle": "developer",     # microbundle — zero-config bundler for tiny modules (Preact team, 8k★)
    # Database — Slonik type-safe Postgres client for Node.js (4k★)
    "slonik": "database",           # Slonik — opinionated type-safe Postgres SQL client for Node.js (4k★)
    # Database — Objection.js ORM on top of Knex.js (7k★)
    "objection": "database",        # Objection.js — SQL-friendly ORM built on Knex (7k★) → Database
    # Frontend — Svelte 5 runes (new reactivity primitive — very high query volume post-Svelte 5 launch)
    "runes": "frontend",            # "svelte runes", "runes reactivity", "svelte 5 runes" → Frontend Frameworks
    # AI — Cursor AI IDE compound forms (complement to "cursor"→ai already mapped)
    "cursorai": "ai",               # compound — "cursorai alternative", "cursor ai setup" → AI & Automation
    # Developer — Bun package manager (bun install, bun run — distinct from Bun the runtime in stack.md)
    "buninstall": "developer",      # "bun install", "bun package manager" → Developer Tools
    # API — Fastify compound form (complement to "fastify"→api already mapped)
    "fastifyjs": "api",             # FastifyJS — compound; "fastifyjs alternative", "fastifyjs tutorial" → API Tools
    # AI — LLM inference servers (fast-growing segment; agents search "tgi", "mlx" before deploying)
    "tgi": "ai",                    # TGI (Text Generation Inference) — HuggingFace LLM serving engine (9k★)
    "mlx": "ai",                    # Apple MLX — ML framework for Apple Silicon (numpy+autograd+neural, 20k★)
    # AI — LLM fine-tuning frameworks (2026 growth segment; "unsloth alternative" queries increasing)
    "unsloth": "ai",                # Unsloth — 2× faster LLM fine-tuning with 70% less VRAM (24k★)
    "axolotl": "ai",                # Axolotl — LLM fine-tuning toolkit (LoRA, QLoRA, Flash Attention, 9k★)
    # Monitoring — Grafana observability stack completeness (Loki already mapped; adding Tempo + Mimir + Alloy)
    "tempo": "monitoring",          # Grafana Tempo — open-source distributed tracing backend (4k★)
    "mimir": "monitoring",          # Grafana Mimir — Prometheus-compatible horizontally scalable TSDB (4k★)
    "alloy": "monitoring",          # Grafana Alloy — OpenTelemetry collector (successor to Grafana Agent, 6k★)
    # Monitoring — continuous profiling (fast-growing infra observability segment)
    "pyroscope": "monitoring",      # Pyroscope — continuous profiling platform (Grafana/pyroscope, 10k★)
    "parca": "monitoring",          # Parca — open-source continuous profiling by Polar Signals (4k★)
    "flamegraph": "monitoring",     # "flame graph", "flamegraph viewer" — profiling visualization → Monitoring
    # DevOps — git commit and release automation (very common in CI/CD setup queries)
    "commitlint": "devops",         # commitlint — lint commit messages against Conventional Commits (17k★)
    "release-please": "devops",     # release-please — Google's PR-based release automation tool (7k★)
    "devpod": "devops",             # DevPod — open-source dev environments, Gitpod alternative (loft-sh, 8k★)
    # Frontend — ISR and prerendering (Next.js/Astro incremental static regeneration, common query segment)
    "isr": "frontend",              # ISR (Incremental Static Regeneration) — "isr nextjs", "isr alternative" → Frontend Frameworks
    "prerender": "frontend",        # "prerender service", "prerender.io alternative" → Frontend Frameworks
    "prerendering": "frontend",     # "prerendering tool", "dynamic prerendering" → Frontend Frameworks
    # Frontend — compound "state management" without space (complement to "state"→frontend already mapped)
    "statemanagement": "frontend",  # compound — "statemanagement library", "statemanagement react" → Frontend Frameworks
    # AI — Meta LlamaStack inference + agent server (8k★, fast-growing in 2026)
    "llamastack": "ai",             # LlamaStack — Meta's unified LLM inference + agent stack → AI & Automation
    "llama-stack": "ai",            # hyphenated form — "llama-stack alternative", "llama-stack server" → AI & Automation
    # AI — document parsing for RAG pipelines (fast-growing 2026 query segment)
    "docling": "ai",                # Docling — IBM's document extraction and conversion for RAG (10k★) → AI & Automation
    "kotaemon": "ai",               # Kotaemon — RAG chatbot UI framework by Cinnamon (22k★) → AI & Automation
    # AI — Jina AI neural search and multimodal embedding (22k★)
    "jina": "ai",                   # Jina AI — neural search and multimodal embedding framework (22k★) → AI & Automation
    "jinaai": "ai",                 # compound form — "jinaai alternative", "jina ai reader" → AI & Automation
    # MCP — client-side tooling (complement to "mcp"→mcp for server queries)
    "mcp-client": "mcp",            # "mcp client library", "mcp client sdk" → MCP Servers category
    "mcpclient": "mcp",             # compound — "mcpclient setup", "mcp client implementation" → MCP Servers
    # AI — DeepSeek open-weight LLM family (V3, R1 — hugely popular in 2026, 100k★+)
    "deepseek": "ai",               # DeepSeek — open-source frontier LLM (V3, R1); "deepseek alternative" → AI & Automation
    "deepseekr1": "ai",             # compound — "deepseek r1 setup", "deepseekr1 api" → AI & Automation
    # Auth — Modern auth providers missing from synonyms (kinde, descope, scalekit)
    "kinde": "authentication",      # Kinde — modern auth with built-in Next.js SDK (kinde.com)
    "descope": "authentication",    # Descope — no-code auth with visual flow builder
    "scalekit": "authentication",   # ScaleKit — enterprise SSO/SCIM for B2B SaaS
    "stackauth": "authentication",  # Stack Auth — open-source Next.js auth kit (stack-auth/stack)
    "stack-auth": "authentication", # hyphenated form — "stack-auth alternative", "stack auth nextjs" → Authentication
    # DevOps — Nixpacks build system (Railway's open-source build tool; 7k★)
    "nixpacks": "devops",           # Nixpacks — auto-detect language and build Docker image → DevOps
    # Frontend — CSS-in-JS tools (complement to pandacss, unocss already mapped)
    "panda-css": "frontend",        # Panda CSS hyphenated form — "panda-css alternative" → Frontend Frameworks
    "stylex": "frontend",           # StyleX — Meta's compile-time CSS-in-JS (powers Facebook.com, 8k★) → Frontend Frameworks
    # API / Browser automation — Browserbase cloud browser for AI agents
    "browserbase": "api",           # Browserbase — cloud browser API for AI agent web automation → API Tools
    # MCP — browser automation MCP server (high-growth query segment as agents use Playwright/Puppeteer)
    "playwright-mcp": "mcp",        # Playwright MCP — browser automation MCP server for AI agents → MCP Servers
    # Media — FFmpeg is the most-searched video/audio processing tool (every "video tool" query hits it)
    "ffmpeg": "media",              # FFmpeg — universal multimedia framework (video transcode, stream, convert) → Media Server
    # Developer Tools — data format parsers (config, data, interchange formats)
    "yaml": "developer",            # YAML parsers/validators — js-yaml, PyYAML, yamllint, strictyaml → Developer Tools
    "toml": "developer",            # TOML config parsers — toml.rs, tomllib, toml-ts, toml-node → Developer Tools
    # Payments — dunning management (failed payment retry and recovery)
    "dunning": "payments",          # dunning management — failed payment recovery flows → Payments (Stripe Billing, Chargebee)
    # Invoicing — VAT compliance and calculation
    "vat": "invoicing",             # VAT compliance — "vat calculation", "eu vat api" → Invoicing & Billing (Anrok, TaxJar, Avalara)
    # AI — text tokenization (tokenizer tools for LLM pre-processing pipelines)
    "tokenizer": "ai",              # tokenizer tools — "bpe tokenizer", "tiktoken alternative" → AI & Automation
    "tokenization": "ai",           # explicit form — "text tokenization", "input tokenization for llms" → AI & Automation
    # Frontend — Flowbite (open-source Tailwind CSS component library with React/Vue/Angular variants)
    "flowbite": "frontend",         # Flowbite — Tailwind CSS UI component library (React/Vue/Svelte, 8k★) → Frontend Frameworks
    # Developer Tools — Mermaid.js compound form (complement to "mermaid"→developer at line ~3538)
    "mermaidjs": "developer",       # MermaidJS — compound form; "mermaidjs alternative", "mermaidjs tutorial" → Developer Tools
    # Localization — RTL (right-to-left) layout support for Arabic, Hebrew, Persian, Urdu
    "rtl": "localization",          # RTL layout support — "rtl react", "rtl languages", "rtl css" → Localization
    # Analytics — Tremor (open-source React dashboard and charting component library)
    "tremor": "analytics",          # Tremor — React dashboard components for BI/analytics UIs (15k★) → Analytics & Metrics
    # Security — Content Security Policy (CSP headers, nonce generation, report-only mode)
    "csp": "security",              # CSP — Content Security Policy headers; "csp nonce", "csp middleware" → Security Tools
    # CLI — argument parsers (top npm downloads, very high "alternative" query volume)
    "yargs": "cli",                 # Yargs — most popular Node.js CLI argument parser (55M weekly downloads, 11k★) → CLI Tools
    "commander": "cli",             # Commander.js — second most popular Node.js CLI framework (26k★) → CLI Tools
    "chalk": "cli",                 # Chalk — terminal string styling (20k★); common CLI tooling query → CLI Tools
    "inquirer": "cli",              # Inquirer.js — interactive CLI prompts (19k★); "inquirer alternative" → CLI Tools
    # Developer — TypeScript and Node.js runtime tooling
    "ts-node": "developer",         # ts-node — TypeScript execution for Node.js without pre-compiling (13k★) → Developer Tools
    "tsnode": "developer",          # compound form — "tsnode alternative", "ts-node setup" → Developer Tools
    "nodemon": "developer",         # nodemon — auto-restart Node.js on file change (26k★) → Developer Tools
    # Payments — bank transfer standards (US ACH and EU SEPA — very common payment integration queries)
    "ach": "payments",              # ACH — US bank transfer protocol; "ach payment api", "ach transfer" → Payments
    "sepa": "payments",             # SEPA — EU bank transfer standard; "sepa direct debit", "sepa api" → Payments
    # Message Queue — AWS SQS (canonical alternative query target for message queues)
    "sqs": "message",               # AWS SQS — Simple Queue Service; "sqs alternative", "aws sqs" → Message Queues
    # Notifications — AWS SNS (common alternative query for notification services)
    "sns": "notifications",         # AWS SNS — Simple Notification Service; "sns alternative" → Notifications
    # Media — Shaka Player (Google's adaptive media player for HLS/DASH streams)
    "shaka": "media",               # Shaka Player — Google's open-source adaptive media player (6k★) → Media Server
    # Auth — Cerbos open-source authorization engine
    "cerbos": "authentication",     # Cerbos — open-source authorization service; "cerbos alternative" → Authentication
    # Database — MotherDuck cloud DuckDB service
    "motherduck": "database",       # MotherDuck — cloud DuckDB; "motherduck alternative", "motherduck vs" → Database
    # Analytics — Tinybird real-time analytics on ClickHouse
    "tinybird": "analytics",        # Tinybird — real-time analytics platform; "tinybird alternative" → Analytics & Metrics
    # Frontend — Anime.js animation library (50k★)
    "anime": "frontend",            # Anime.js — lightweight JS animation library (50k★); "anime.js alternative" → Frontend Frameworks
    # Frontend — WebGPU (successor to WebGL for GPU compute in browser)
    "webgpu": "frontend",           # WebGPU — next-gen browser graphics/compute API; "webgpu library" → Frontend Frameworks
    # Frontend — Fontsource npm-installable self-hosted fonts
    "fontsource": "frontend",       # Fontsource — self-hosted web fonts via npm; "fontsource alternative" → Frontend Frameworks
    # Background Jobs — Kestra workflow orchestration (14k★)
    "kestra": "background",         # Kestra — declarative workflow orchestration platform (14k★) → Background Jobs
    # AI — Gradio ML demo and UI framework (34k★)
    "gradio": "ai",                 # Gradio — build ML demos and web UIs in Python (34k★) → AI & Automation
    # AI — Streamlit Python data app framework (36k★)
    "streamlit": "ai",              # Streamlit — turn Python scripts into shareable data apps (36k★) → AI & Automation
    # AI — Google Gemma open-weight models
    "gemma": "ai",                  # Google Gemma — open-weight LLMs for local deployment → AI & Automation
    # AI — Alibaba Qwen open-weight models
    "qwen": "ai",                   # Qwen (Alibaba) — open-weight LLM family; "qwen alternative" → AI & Automation
    # Vibe coding — dominant 2026 term coined by Andrej Karpathy for AI-assisted coding
    "vibe": "ai",                   # "vibe coding", "vibe-based development" → AI & Automation
    "vibecoding": "ai",             # compound — "vibecoding tools", "vibecoding setup" → AI & Automation
    "vibe-coding": "ai",            # hyphenated — "vibe-coding workflow", "vibe-coding alternative" → AI & Automation
    # MCP — compound and hyphenated forms (complement to "mcp"→mcp and "protocol"→mcp)
    "mcpserver": "mcp",             # compound — "mcpserver typescript", "mcpserver node" → MCP Servers
    "mcp-server": "mcp",            # hyphenated — "mcp-server alternative", "mcp-server sdk" → MCP Servers
    # AI browser automation — fast-growing 2026 segment (agents browsing the web)
    "browser-use": "ai",            # Browser-use — Python AI-controlled browser automation (25k★) → AI & Automation
    "browseruse": "ai",             # compound — "browseruse alternative", "browseruse python" → AI & Automation
    "stagehand": "ai",              # Stagehand — Browserbase AI browser automation SDK (8k★) → AI & Automation
    # Frontend — Waku minimal React RSC framework
    "waku": "frontend",             # Waku — minimal React server components framework (5k★) → Frontend Frameworks
    # Database — RisingWave distributed SQL streaming database
    "risingwave": "database",       # RisingWave — distributed SQL streaming database (7k★) → Database
    # AI — OpenAI Swarm lightweight multi-agent orchestration
    "swarm": "ai",                  # OpenAI Swarm — lightweight multi-agent orchestration framework → AI & Automation
    # AI — Roo Code open-source AI coding assistant (VS Code extension)
    "roocode": "ai",                # Roo Code — open-source AI coding extension (VS Code, 38k★) → AI & Automation
    # AI — Bolt.new (StackBlitz AI web app builder from prompts, 2026 vibe-coding tool)
    "bolt": "ai",                   # Bolt.new — AI-powered app builder from text prompts → AI & Automation
    # AI — Pipecat real-time voice/video AI pipeline framework (6k★)
    "pipecat": "ai",                # Pipecat — real-time voice AI framework by Daily.co (6k★) → AI & Automation
    # AI — Replit Agent AI-assisted coding and deployment platform
    "replit": "ai",                 # Replit Agent — AI coding + instant deployment in the browser → AI & Automation
    # AI — Screenpipe open-source local AI screen data pipeline (9k★)
    "screenpipe": "ai",             # Screenpipe — open-source local AI screen monitoring pipeline (9k★) → AI & Automation
    # Developer — Apify web scraping and automation platform
    "apify": "developer",           # Apify — web scraping, crawling, and automation platform → Developer Tools
    # Search — Perplexica open-source AI-powered search engine (18k★)
    "perplexica": "search",         # Perplexica — open-source Perplexity-style AI search engine (18k★) → Search Engines
    # AI — Agent Zero open-source agentic AI OS framework
    "agentzero": "ai",              # Agent Zero — open-source agentic AI OS framework → AI & Automation
    "agent-zero": "ai",             # hyphenated form — "agent-zero alternative", "agent-zero python" → AI & Automation
    # Search — MiniSearch lightweight in-browser full-text search (5k★)
    "minisearch": "search",         # MiniSearch — lightweight in-memory full-text search for JS/TS (5k★) → Search Engines
    # AI — pgai Timescale Postgres extension for in-database LLM operations
    "pgai": "ai",                   # pgai — Postgres extension for AI/LLM directly in SQL (Timescale) → AI & Automation
    # Search — FlexSearch next-generation JS full-text search library (12k★)
    "flexsearch": "search",         # FlexSearch — high-performance full-text search library for JS/TS (12k★) → Search Engines
    # AI — SWE-agent Princeton autonomous software engineering agent (15k★)
    "sweagent": "ai",               # SWE-agent — Princeton autonomous software engineering agent (15k★) → AI & Automation
    # Security — software supply chain and SBOM tooling (fast-growing compliance segment)
    "sbom": "security",             # SBOM (Software Bill of Materials) — Syft, CycloneDX, SPDX tooling → Security Tools
    "sigstore": "security",         # Sigstore — artifact signing standard (Cosign, Rekor, Gitsign) → Security Tools
    "cosign": "security",           # Cosign — container image and artifact signing (Sigstore, 4k★) → Security Tools
    "syft": "security",             # Syft — open-source SBOM generator (Anchore, 6k★) → Security Tools
    "supply-chain": "security",     # "supply chain security", "software supply chain" → Security Tools
    "supplychain": "security",      # compound form — "supplychain attack", "supplychain hardening" → Security Tools
    # Security — compliance and privacy categories missing from synonyms
    "consent": "security",          # "consent management platform", "gdpr consent banner" → Security Tools (Cookiebot, Osano, iubenda)
    "hipaa": "security",            # HIPAA — US healthcare privacy law compliance tooling → Security Tools
    "pci": "security",              # PCI DSS — payment card industry compliance → Security Tools (Stripe Radar, Braintree)
    "soc2": "security",             # SOC 2 compliance automation → Security Tools (Vanta, Drata, Secureframe)
    "privacy": "security",          # "privacy-first analytics", "privacy tool", "user privacy" → Security Tools
    "devsecops": "security",        # DevSecOps — "devsecops pipeline", "security in devops" → Security Tools
    # AI — model optimization and architecture terms (fast-growing 2026 query segment)
    "quantization": "ai",           # "model quantization", "llm quantization", "gguf quantize" → AI & Automation
    "distillation": "ai",           # "knowledge distillation", "model distillation", "distill llm" → AI & Automation
    "moe": "ai",                    # MoE — Mixture of Experts ("moe model", "mixture of experts" queries) → AI & Automation
    # Vector database compound/hyphenated forms (complement to "vector"→database already mapped)
    "vectordb": "database",         # "vectordb python", "vectordb alternative" → Database (Qdrant, Weaviate, Chroma, pgvector)
    "vector-db": "database",        # hyphenated — "vector-db comparison", "vector-db for rag" → Database
    # Graph database compound form (complement to "graph"→database, "neo4j"→database already mapped)
    "graphdb": "database",          # "graphdb library", "graphdb query" → Database (Neo4j, ArangoDB, Dgraph)
    # Fuzzing / fuzz testing — security and reliability testing segment
    "fuzz": "testing",              # "fuzz testing", "fuzzer library", "afl fuzz" → Testing Tools (AFL++, libFuzzer, Atheris)
    "fuzzing": "testing",           # "fuzzing tool", "python fuzzing", "fuzzing framework" → Testing Tools
    # Actor model frameworks — JVM/Erlang/Elixir concurrency patterns
    "akka": "api",                  # Akka — Scala/Java actor model framework (26k★) → API Tools (reactive distributed)
    "erlang": "api",                # Erlang language queries → API tools (Cowboy, Ranch; complement to "elixir"→api)
    "actor": "api",                 # "actor model", "actor framework", "actor concurrency" → API Tools
    # IP geolocation — Maps & Location category (ipinfo.io, MaxMind, ipapi.co)
    "geoip": "maps",                # "geoip library", "geoip lookup", "geoip database" → Maps & Location (MaxMind)
    "geofencing": "maps",           # "geofencing API", "geofence trigger", "geofencing library" → Maps & Location
    "ipinfo": "maps",               # IPinfo.io — IP geolocation and network intelligence API → Maps & Location
    "maxmind": "maps",              # MaxMind GeoIP2 — most popular IP geolocation database → Maps & Location
    # WASM build tooling — Rust+WASM (complement to "wasm"→frontend, "webassembly"→frontend already mapped)
    "wasmpack": "frontend",         # wasm-pack — build Rust WASM packages for npm publishing (6k★) → Frontend Frameworks
    "wasm-pack": "frontend",        # hyphenated — "wasm-pack build", "wasm-pack alternative" → Frontend Frameworks
    # Auth — SAML 2.0 explicit version form (complement to "saml"→authentication already mapped)
    "saml2": "authentication",      # SAML 2.0 — "saml2 library", "saml2 python", "saml 2.0 sp" → Authentication
    # AI — ONNX model format and runtime (canonical ML portability standard, 16k★)
    "onnx": "ai",                   # ONNX — Open Neural Network Exchange; "onnx runtime", "onnx model" → AI & Automation
    "onnxruntime": "ai",            # compound — "onnxruntime inference", "onnxruntime alternative" → AI & Automation
    # AI — AutoGPT autonomous agent (still widely searched despite age, 170k★)
    "autogpt": "ai",                # AutoGPT — autonomous GPT-4 agent framework → AI & Automation
    # AI — GGUF/GGML quantized model formats (llama.cpp ecosystem, extremely common in local LLM queries)
    "gguf": "ai",                   # GGUF — quantized model format for llama.cpp; "gguf model", "gguf convert" → AI
    "ggml": "ai",                   # GGML — C tensor library underpinning llama.cpp, whisper.cpp → AI & Automation
    # AI — LoRA / QLoRA fine-tuning techniques (dominant query segment for ML fine-tuning)
    "lora": "ai",                   # LoRA — Low-Rank Adaptation fine-tuning; "lora adapter", "lora training" → AI
    "qlora": "ai",                  # QLoRA — quantized LoRA; "qlora fine-tuning", "qlora training" → AI & Automation
    # AI — Transformers.js in-browser / Node.js ML (HuggingFace, 10k★)
    "transformerjs": "ai",          # Transformers.js — HuggingFace models in browser/Node; "transformerjs alternative" → AI
    # AI — transformer architecture (complement to "transformers"→ai; "transformer model" queries)
    "transformer": "ai",            # "transformer architecture", "transformer model", "transformer layer" → AI & Automation
    # DevOps — kind (Kubernetes IN Docker) local cluster tool (13k★)
    "kind": "devops",               # kind — run local Kubernetes clusters in Docker; "kind cluster", "kind vs minikube" → DevOps
    # DevOps — canary and blue-green deployment strategy terms (common CI/CD pattern queries)
    "canary": "devops",             # canary deployment — "canary release", "canary testing", "canary rollout" → DevOps
    "bluegreen": "devops",          # compound — "bluegreen deployment", "blue green release strategy" → DevOps
    "blue-green": "devops",         # hyphenated — "blue-green deployment", "blue-green switch" → DevOps
    # Monitoring — SRE (Site Reliability Engineering) tooling queries (Prometheus/Grafana/PagerDuty workflows)
    "sre": "monitoring",            # SRE — "sre tools", "sre platform", "site reliability engineering" → Monitoring & Uptime
    # Message Queue — event bus libraries (mitt, EventEmitter; distinct from "event"→message already mapped)
    "eventbus": "message",          # event bus — "eventbus library", "in-process eventbus", "eventbus pattern" → Message Queue
    "event-bus": "message",         # hyphenated — "event-bus alternative", "event-bus typescript" → Message Queue
    # Frontend — canvas graphics and node-based diagram libraries
    "konva": "frontend",            # Konva.js — 2D canvas graphics library for React/Vue/vanilla (11k★) → Frontend Frameworks
    "fabricjs": "frontend",         # Fabric.js — canvas manipulation library; "fabricjs alternative" → Frontend Frameworks
    "fabric": "frontend",           # short form — "fabric.js alternative", "fabric canvas library" → Frontend Frameworks
    "reactflow": "frontend",        # React Flow — node-based UI / diagram library (27k★, xyflow/xyflow) → Frontend Frameworks
    "react-flow": "frontend",       # hyphenated — "react-flow alternative", "react-flow v12" → Frontend Frameworks
    "xyflow": "frontend",           # XYFlow — new org name for React Flow + Svelte Flow ecosystem → Frontend Frameworks
    # AI — code execution sandbox and inference servers
    "e2b": "ai",                    # E2B.dev — secure cloud sandbox for AI-generated code execution (7k★) → AI & Automation
    "triton": "ai",                 # NVIDIA Triton Inference Server — production ML model serving (8k★) → AI & Automation
    "greptile": "ai",               # Greptile — AI that understands your codebase; code search and Q&A → AI & Automation
    # Monitoring — status page systems (high "alternative" query volume)
    "statuspage": "monitoring",     # Statuspage.io — status page service; "statuspage alternative" → Monitoring & Uptime
    "cachet": "monitoring",         # Cachet — open-source status page system (15k★) → Monitoring & Uptime
    "upptime": "monitoring",        # Upptime — GitHub-powered uptime monitor + status page (14k★) → Monitoring & Uptime
    # DevOps — container management and Docker Desktop alternatives
    "colima": "devops",             # Colima — Docker Desktop alternative for macOS/Linux (18k★) → DevOps & Infrastructure
    "portainer": "devops",          # Portainer — Docker container management UI (31k★) → DevOps & Infrastructure
    "rancher": "devops",            # Rancher — Kubernetes cluster management platform (23k★) → DevOps & Infrastructure
    # Background jobs — Ruby job queue (Resque is the canonical Ruby background jobs tool)
    "resque": "background",         # Resque — Redis-backed Ruby background jobs (10k★) → Background Jobs
    # API — HTTP testing utilities
    "httpbin": "api",               # httpbin.org — HTTP request/response service for API testing → API Tools
    # Security — network scanning
    "nmap": "security",             # Nmap — open-source network security scanner (10k★) → Security Tools
    # Documentation — living code documentation
    "swimm": "documentation",       # Swimm — living code documentation that stays up-to-date with code → Documentation
    # Database — TypeScript type-safe Postgres query generation
    "pgtyped": "database",          # PgTyped — compile-time type-safe Postgres queries for TypeScript (3k★) → Database
    "pg-typed": "database",         # hyphenated — "pg-typed alternative", "pgtyped migration" → Database
    # Analytics — data visualization libraries missing from synonyms
    "visx": "analytics",            # Airbnb visx — low-level D3+React visualization primitives (18k★) → Analytics & Metrics
    "victory": "analytics",         # Victory.js — composable React chart library by FormidableLabs (10k★) → Analytics & Metrics
    "highcharts": "analytics",      # Highcharts — widely-searched commercial charting library → Analytics & Metrics
    "bokeh": "analytics",           # Bokeh — interactive Python visualization library (19k★) → Analytics & Metrics
    "dash": "analytics",            # Plotly Dash — Python analytical web app framework (21k★) → Analytics & Metrics
    # Frontend — icon libraries not yet covered (high alternative-query volume)
    "phosphor": "frontend",         # Phosphor Icons — flexible icon family; "phosphor alternative" (4k★) → Frontend Frameworks
    "phosphoricons": "frontend",    # compound — "phosphoricons react", "phosphoricons setup" → Frontend Frameworks
    "tabler": "frontend",           # Tabler Icons — 5000+ open-source SVG icons (18k★) → Frontend Frameworks
    "tablericons": "frontend",      # compound — "tablericons react", "tablericons alternative" → Frontend Frameworks
    "iconoir": "frontend",          # Iconoir — clean open-source icon set; "iconoir alternative" (4k★) → Frontend Frameworks
    # Database — columnar file format (common in data pipeline / data lake queries)
    "parquet": "database",          # Apache Parquet — columnar storage format; "parquet reader", "parquet alternative" → Database
    # API — Haskell and OCaml web framework queries
    "haskell": "api",               # Haskell web framework queries → API Tools (Servant, Yesod, IHP) → API Tools
    "ocaml": "api",                 # OCaml web framework queries → API Tools (Dream, Opium) → API Tools
    # Design — Figma (most-searched design tool; "figma alternative" is a top query)
    "figma": "design",              # Figma — "figma alternative", "figma open source" → Design & Creative
    # Monitoring — cron job monitoring (high "alternative" query volume)
    "cronitor": "monitoring",       # Cronitor — cron monitoring and alerting service → Monitoring & Uptime
    # AI — Vercel v0 AI UI builder and TabbyML self-hosted code assistant
    "v0": "ai",                     # v0.dev — Vercel's AI UI generator from text prompts → AI & Automation
    "tabbyml": "ai",                # TabbyML — self-hosted GitHub Copilot alternative (22k★) → AI & Automation
    "tabby": "ai",                  # short form — "tabby alternative", "tabby ai setup" → AI & Automation
    # AI — image generation models (complement to "dalle"→ai and "midjourney"→ai already mapped)
    "flux": "ai",                   # FLUX.1 — Black Forest Labs image generation model (16k★) → AI & Automation
    "sdxl": "ai",                   # Stable Diffusion XL — "sdxl alternative", "sdxl model" → AI & Automation
    "stability": "ai",              # Stability AI — "stability ai api", "stability diffusion" → AI & Automation
    # Developer Tools — Void open-source Cursor-alternative IDE
    "void": "developer",            # Void IDE — open-source VS Code fork with AI coding features → Developer Tools
    # Analytics — user lifecycle and product metrics (common Mixpanel/Amplitude query patterns)
    "churn": "analytics",           # "churn rate", "churn analysis", "churn prediction" → Analytics & Metrics
    "retention": "analytics",       # "user retention", "retention dashboard", "retention curve" → Analytics & Metrics
    "ltv": "analytics",             # LTV — lifetime value; "ltv calculation", "customer ltv" → Analytics & Metrics
    "lifetime": "analytics",        # "lifetime value", "customer lifetime", "lifetime revenue" → Analytics & Metrics
    # AI — recommendation engines and personalisation (Recombee, LensKit, Surprise.py)
    "recommendation": "ai",         # "recommendation engine", "recommendation api" → AI & Automation
    "recommender": "ai",            # "recommender system", "recommender framework" → AI & Automation
    "personalization": "ai",        # "personalization engine", "ai personalization" → AI & Automation
    "personalisation": "ai",        # UK spelling — "personalisation api", "personalisation tool" → AI & Automation
    # Security — device fingerprinting and bot protection (Fingerprint.com, FingerprintJS)
    "fingerprint": "security",      # "fingerprint api", "browser fingerprint", "device fingerprint" → Security Tools
    "fingerprintjs": "security",    # FingerprintJS explicit named tool → Security Tools
    # Auth — social login and magic link flows (very common auth pattern queries)
    "sociallogin": "authentication", # compound — "sociallogin provider", "sociallogin sdk" → Authentication
    "social-login": "authentication",# hyphenated — "social-login button", "social-login oauth" → Authentication
    "magic-link": "authentication",  # hyphenated — "magic-link auth", "magic-link email" → Authentication
    # Background jobs / ETL — reverse ETL (Hightouch, Census, Polytomic data activation)
    "reverse-etl": "background",    # hyphenated — "reverse-etl platform", "reverse-etl alternative" → Background Jobs
    "reversetl": "background",      # compound — "reversetl tool", "reversetl vs hightouch" → Background Jobs
    # DevOps — multi-cloud management (Crossplane, Terraform multi-cloud, Pulumi multi-cloud)
    "multicloud": "devops",         # compound — "multicloud management", "multicloud deployment" → DevOps & Infrastructure
    "multi-cloud": "devops",        # hyphenated — "multi-cloud strategy", "multi-cloud provider" → DevOps & Infrastructure
    # CRM — most-searched CRM alternative query targets
    "hubspot": "crm",               # HubSpot — "hubspot alternative", "hubspot crm" → CRM & Sales (Twenty, Monica)
    "salesforce": "crm",            # Salesforce — "salesforce alternative", "sfdc alternative" → CRM & Sales
    # Landing pages — no-code website builders (high "alternative" query volume)
    "webflow": "landing",           # Webflow — "webflow alternative", "webflow competitor" → Landing Pages
    "squarespace": "landing",       # Squarespace — "squarespace alternative", "website builder" → Landing Pages
    # Developer Tools — Airtable alternative queries (NocoDB, Baserow, Grist)
    "airtable": "developer",        # Airtable — "airtable alternative", "airtable open source" → Developer Tools
    # Localisation — i18next is the dominant JS/TS i18n library (React, Vue, Angular, Node)
    "i18next": "localization",      # i18next — most popular JS internationalisation framework → Localization
    "react-i18next": "localization", # react-i18next — React binding for i18next → Localization
    # API — Phoenix LiveView server-rendered interactive UI (Elixir ecosystem)
    "liveview": "api",              # Phoenix LiveView — "liveview alternative", "liveview vs inertia" → API Tools
    # Monitoring — Better Stack hyphenated query form (complement to "betterstack" already mapped)
    "better-stack": "monitoring",   # hyphenated — "better-stack alternative", "better-stack logging" → Monitoring & Uptime
    # Frontend — Floating UI positioning engine (underlies Radix, Headless UI, many UI libs)
    "floating-ui": "frontend",      # Floating UI — floating element positioning engine (29k★) → Frontend Frameworks
    # Frontend — data grids and table libraries
    "ag-grid": "frontend",          # AG Grid — feature-rich enterprise data grid (12k★) → Frontend Frameworks
    "react-table": "frontend",      # React Table / TanStack Table v8 — headless table (25k★) → Frontend Frameworks
    "sortablejs": "frontend",       # SortableJS — drag-and-drop sort library (29k★) → Frontend Frameworks
    "swiper": "frontend",           # Swiper — most popular mobile touch slider (40k★) → Frontend Frameworks
    "fullcalendar": "frontend",     # FullCalendar — full-sized JavaScript event calendar (18k★) → Frontend Frameworks
    # Frontend — accessible UI primitives and specialist components
    "ariakit": "frontend",          # Ariakit — composable accessible UI primitives (7k★) → Frontend Frameworks
    "embla": "frontend",            # Embla Carousel — lightweight extensible carousel (6k★) → Frontend Frameworks
    "cmdk": "frontend",             # cmdk — command palette component for React (10k★) → Frontend Frameworks
    "vaul": "frontend",             # Vaul — animated drawer component for React → Frontend Frameworks
    # Security — Open Policy Agent / Zanzibar-inspired authorization
    "open-policy-agent": "security", # full name — "open policy agent alternative" → Security Tools
    "spicedb": "security",          # SpiceDB — Google Zanzibar-inspired permissions DB (5k★) → Security Tools
    # Security — IaC and Dockerfile scanning
    "checkov": "security",          # Checkov — IaC security scanner by Bridgecrew (7k★) → Security Tools
    "hadolint": "security",         # Hadolint — Dockerfile linter and security checker → Security Tools
    # DevOps — commit message tooling (Commitizen, commitlint ecosystem)
    "commitizen": "devops",         # Commitizen — interactive conventional commit message tooling → DevOps & Infrastructure
    # Testing — API mocking and test reporting
    "allure": "testing",            # Allure — multi-language test report framework (4k★) → Testing Tools
    # CLI Tools — Python CLI frameworks (complement to "oclif"→cli, "cobra"→cli already mapped)
    "click": "cli",                 # Click — Python CLI toolkit by Pallets (16k★); most-used Python CLI framework
    "typer": "cli",                 # Typer — modern Python CLI by FastAPI creator Sebastián Ramírez (16k★)
    "clap": "cli",                  # Clap — dominant Rust CLI argument parser (14k★); "clap alternative", "clap rs"
    # CLI Tools — Go TUI frameworks (Charm ecosystem, very active community)
    "bubbletea": "cli",             # Bubble Tea — Elm-inspired Go TUI framework (29k★) → CLI Tools
    "bubble-tea": "cli",            # hyphenated — "bubble-tea alternative", "bubble-tea go" → CLI Tools
    "charm": "cli",                 # Charm — Go TUI toolkit (Bubble Tea + Lip Gloss + Glamour) → CLI Tools
    # CLI Tools — Python TUI (growing Textual ecosystem)
    "textual": "cli",               # Textual — Python TUI framework by Textualize/Will McGugan (26k★) → CLI Tools
    # Documentation — self-hosted wiki / knowledge-base tools
    "fumadocs": "documentation",    # Fumadocs — Next.js-first documentation framework (4k★) → Documentation
    "outline": "documentation",     # Outline — open-source knowledge base & wiki (Notion-like, 29k★) → Documentation
    "bookstack": "documentation",   # BookStack — self-hosted wiki and documentation platform (15k★) → Documentation
    "wikijs": "documentation",      # Wiki.js — modern open-source wiki (GraphQL API, 24k★) → Documentation
    "wiki-js": "documentation",     # hyphenated — "wiki-js alternative", "wiki-js self-hosted" → Documentation
    # Frontend — rich text editors (complement to "tiptap"→frontend, "lexical"→frontend)
    "slate": "frontend",            # Slate.js — highly customisable rich text editor framework (30k★) → Frontend Frameworks
    "plate": "frontend",            # Plate — rich text editor toolkit for React built on Slate (11k★) → Frontend Frameworks
    "ckeditor": "frontend",         # CKEditor — mature rich text editor; "ckeditor alternative", "ckeditor 5" → Frontend Frameworks
    "tinymce": "frontend",          # TinyMCE — widely-used browser WYSIWYG editor → Frontend Frameworks
    # Developer Tools — AI-powered terminal (complement to "ghostty"→developer, "atuin"→developer)
    "warp": "developer",            # Warp — Rust GPU-native AI terminal (23k★); "warp terminal alternative" → Developer Tools
    # Security — password managers (complement to "bitwarden"→security already mapped)
    "vaultwarden": "security",      # Vaultwarden — Bitwarden-compatible self-hosted server (Rust, 40k★) → Security Tools
    "keepass": "security",          # KeePass — open-source password manager family → Security Tools
    "1password": "security",        # 1Password — "1password cli", "1password secrets manager" queries → Security Tools
    # Developer Tools — CSV parsing libraries (PapaParse, fast-csv, csv-parse — very high query volume)
    "csv": "developer",             # "csv parser", "csv library", "read csv file" → Developer Tools (PapaParse, fast-csv)
    "papaparse": "developer",       # PapaParse — fast browser + Node.js CSV parser (13k★) → Developer Tools
    "fast-csv": "developer",        # fast-csv — Node.js CSV parsing/formatting library (3k★) → Developer Tools
    # Developer Tools — Excel/spreadsheet libraries (very common "parse excel" query segment)
    "excel": "developer",           # "excel library", "excel reader", "parse excel file" → Developer Tools
    "xlsx": "developer",            # xlsx npm package (SheetJS); ".xlsx parser", "xlsx alternative" → Developer Tools
    "sheetjs": "developer",         # SheetJS — spreadsheet parser and writer for JS/TS (35k★) → Developer Tools
    "exceljs": "developer",         # ExcelJS — Excel workbook read/write for Node.js (13k★) → Developer Tools
    "openpyxl": "developer",        # openpyxl — Python library for Excel 2010+ files → Developer Tools
    "xlsxwriter": "developer",      # XlsxWriter — Python library for creating Excel .xlsx files → Developer Tools
    # Auth — ACL and FIDO2 (complement to "rbac"→authentication and "webauthn"→authentication)
    "acl": "authentication",        # ACL (Access Control List) — "acl library", "acl middleware" → Authentication
    "fido": "authentication",       # FIDO — "fido2 key", "fido hardware key", "fido standard" → Authentication
    "b2b": "authentication",        # B2B — "b2b sso", "b2b authentication", "b2b saas auth" → Authentication
    # Background jobs — additional ELT data ingestion tools
    "fivetran": "background",       # Fivetran — managed ELT data connectors; "fivetran alternative" → Background Jobs
    "meltano": "background",        # Meltano — open-source Singer/dbt ELT platform → Background Jobs
    # Notifications — self-hosted push notification servers (high self-hosters query volume)
    "gotify": "notifications",      # Gotify — self-hosted push notification server (12k★) → Notifications
    "pushover": "notifications",    # Pushover — simple push notifications to mobile devices → Notifications
    "apprise": "notifications",     # Apprise — multi-platform notification library (11k★) → Notifications
    "ntfy": "notifications",        # ntfy.sh — topic-based self-hosted push notification server (18k★) → Notifications
    # AI — LLM model serving and registry (very common query prefix not yet mapped)
    "model": "ai",                  # "model serving", "model registry", "model deployment", "language model" → AI & Automation
    "serving": "ai",                # "model serving", "llm serving", "inference serving" → AI & Automation (complements "model")
    "grounding": "ai",              # "grounding llm outputs", "rag grounding", "grounding with search" → AI & Automation
    "context-window": "ai",         # "context window extension", "long context window" → AI & Automation
    "contextwindow": "ai",          # compound form — "contextwindow size", "contextwindow llm" → AI & Automation
    # Database — relational and offline-first query patterns not yet mapped
    "relational": "database",       # "relational database", "relational orm", "sql relational" → Database
    "offline": "database",          # "offline first app", "offline database", "offline sync" → Database (ElectricSQL, PocketBase, PowerSync)
    # Developer Tools — functional programming and type tooling
    "functional": "developer",      # "functional programming library", "fp-ts alternative", "functional js" → Developer Tools
    "type": "developer",            # "type guard", "type builder", "runtime type check" → Developer Tools (distinct from "typecheck"→testing)
    # DevOps — Kubernetes workload and release management patterns
    "workload": "devops",           # "Kubernetes workload", "workload orchestration", "workload isolation" → DevOps & Infrastructure
    "artifact": "devops",           # "artifact registry", "build artifact", "container artifact" → DevOps & Infrastructure (Harbor, Quay)
    "rollout": "devops",            # "canary rollout", "gradual rollout", "rollout strategy" → DevOps & Infrastructure
    # Auth — OAuth provider library by the Lucia team (used for Google, GitHub, Apple OAuth flows)
    "arctic": "authentication",     # Arctic — TypeScript OAuth 2.0 providers library (pilcrowOnPaper/arctic, 3k★) → Authentication
    # Frontend — Vike (formerly vite-plugin-ssr); SSR/SSG framework for React, Vue, Svelte, Solid
    "vike": "frontend",             # Vike (vite-plugin-ssr) — "vike alternative", "vike vs nextjs" → Frontend Frameworks
    # API — oRPC TypeScript-first type-safe RPC framework (no schema, end-to-end types like tRPC)
    "orpc": "api",                  # oRPC — TypeScript-first type-safe RPC; "orpc alternative", "orpc vs trpc" → API Tools
    # Database — EdgeDB rebranded to Gel in 2025 (graph-relational DB with schema migration)
    "gel": "database",              # Gel (formerly EdgeDB) — "gel alternative", "gel database", "gel edgedb" → Database
    # Developer Tools — VineJS validation library by AdonisJS team (Node.js-first, very fast)
    "vine": "developer",            # VineJS — Node.js validation library; "vine validation", "vinejs alternative" → Developer Tools
    "vinejs": "developer",          # compound form — "vinejs schema", "vinejs vs zod" → Developer Tools
    # Developer Tools — io-ts runtime type validation by gcanti (functional style, common in FP codebases)
    "io-ts": "developer",           # io-ts — "io-ts alternative", "io-ts decoder", "io-ts vs zod" → Developer Tools
    # Developer Tools — runtypes TypeScript runtime type checking library
    "runtypes": "developer",        # runtypes — "runtypes alternative", "runtypes vs zod" → Developer Tools
    # API — Grafbase GraphQL API platform (serverless GraphQL federation + edge caching)
    "grafbase": "api",              # Grafbase — "grafbase alternative", "grafbase graphql" → API Tools
    # Forms — hookform (shorthand for react-hook-form used in "hookform alternative" queries)
    "hookform": "forms",            # hookform — shorthand; "hookform alternative", "hookform vs formik" → Forms & Surveys
    # API — HatTip server-agnostic HTTP handler framework (runs on Node, Deno, Bun, Cloudflare)
    "hattip": "api",                # HatTip — "hattip alternative", "hattip vs hono" → API Tools
    # Web3 / blockchain — named query terms not yet mapped (complement to "blockchain"/"solidity"/"ethers" already mapped)
    "web3": "developer",            # Web3 — "web3 library", "web3 tools", "web3 development" → Developer Tools
    "nft": "developer",             # NFT — "nft minting", "nft smart contract", "nft tooling" → Developer Tools
    # AI — natural language processing query patterns not yet covered
    "natural": "ai",                # "natural language processing", "natural language API", "natural language search" → AI & Automation
    "tokenize": "ai",               # verb form — "tokenize input", "tokenize text for llm", "tokenize document" → AI & Automation
    # LLM proxy — routing for proxy/gateway query terms (complement to "litellm"→ai, "portkey"→ai, "openrouter"→ai)
    "llm-proxy": "ai",              # hyphenated — "llm-proxy setup", "llm-proxy alternative", "llm-proxy caching" → AI & Automation
    "llmproxy": "ai",               # compound — "llmproxy rate limiting", "llmproxy server" → AI & Automation
    # Database — data lake query routing (complement to "lakehouse"→database, "iceberg"→database, "delta"→database)
    "lake": "database",             # "data lake tool", "data lake platform", "lake formation alternative" → Database
    # API — API key management compound/hyphenated forms (Unkey, Kong, Zuplo live in API Tools)
    "apikey": "api",                # compound — "apikey management", "apikey generation", "apikey validation" → API Tools
    "api-key": "api",               # hyphenated — "api-key management", "api-key service", "api-key authentication" → API Tools
    # Testing — singular form for Testcontainers (complement to "testcontainers"→testing already mapped)
    "testcontainer": "testing",     # singular — "testcontainer for postgres", "testcontainer setup" → Testing Tools
    # Frontend — server/client rendering terminology (SSR, CSR, hybrid) not yet directly mapped
    "rendering": "frontend",        # "server-side rendering", "client rendering", "hybrid rendering" → Frontend Frameworks
    # Database — persistence layer terminology (complement to "relational"→database, "offline"→database)
    "persistence": "database",      # "persistence layer", "data persistence", "state persistence" → Database
    "persistent": "database",       # "persistent storage", "persistent connection", "persistent cache" → Database
    # API — bare "api" term routes "api gateway", "api testing", "api client" to API Tools
    "api": "api",                   # "api gateway", "api testing", "api client", "api mock" → API Tools
    # AI — Chainlit Python LLM chatbot UI framework (chainlit/chainlit, 7k★)
    "chainlit": "ai",               # Chainlit — Python framework for LLM-powered chatbot UIs → AI & Automation
    # AI — Chonkie fast RAG text chunking library (chonkie-ai/chonkie, 3k★)
    "chonkie": "ai",                # Chonkie — fast, lightweight text chunking for RAG pipelines → AI & Automation
    # API — Python asyncio event-loop queries (FastAPI, Starlette, Sanic are built on it)
    "asyncio": "api",               # asyncio — Python async event loop; "asyncio framework", "asyncio web" → API Tools
    # Search — FTS abbreviation (full-text search; very common in SQLite/Postgres query terms)
    "fts": "search",                # FTS — "fts5 search", "fts index", "fts alternative" → Search Engines
    # CMS — Kirby CMS PHP flat-file CMS (getkirby/kirby, 4k★)
    "kirby": "cms",                 # Kirby CMS — PHP flat-file flexible CMS; "kirby cms alternative" → Headless CMS
    # AI — CAMEL-AI multi-agent LLM framework (camel-ai/camel, 6k★)
    "camel": "ai",                  # CAMEL-AI — Communicative Agents for Mind Exploration (multi-agent) → AI & Automation
    "camelai": "ai",                # compound — "camelai alternative", "camel ai framework" → AI & Automation
    # AI — CAMEL-AI multi-agent LLM framework already mapped above
    # AI — xAI Grok model (high-volume "grok alternative", "grok api" queries)
    "grok": "ai",                   # Grok — xAI's LLM; "grok alternative", "grok api", "grok vs claude" → AI & Automation
    # AI — Kyutai Moshi realtime voice model (open-source voice conversation AI)
    "moshi": "ai",                  # Moshi — Kyutai's realtime voice foundation model; "moshi alternative" → AI & Automation
    # AI — SGLang structured generation language runtime for fast LLM serving
    "sglang": "ai",                 # SGLang — fast structured LLM serving runtime (lm-sys/sglang, 13k★) → AI & Automation
    # AI — TruLens LLM application evaluation with feedback functions
    "trulens": "ai",                # TruLens — LLM app evaluation with feedback functions (3k★) → AI & Automation
    # AI — EleutherAI lm-evaluation-harness (canonical open LLM benchmark runner)
    "lm-eval": "ai",                # lm-eval — EleutherAI LM evaluation harness; "lm-eval alternative" → AI & Automation
    "lmeval": "ai",                 # compound form — "lmeval benchmarks", "lmeval harness" → AI & Automation
    # Node.js runtime — common query prefix for framework/server/backend queries
    # "node" and "nodejs" are in _FRAMEWORK_QUERY_TERMS for frameworks_tested filter,
    # but NOT in _CAT_SYNONYMS, so they get no category boost. Adding here so
    # "node web framework", "nodejs server", "node backend api" route to API Tools
    # where Express, NestJS, Fastify, Hono, Koa live.
    "node": "api",                  # "node http server", "node web framework" → API Tools
    "nodejs": "api",                # explicit form — "nodejs framework", "nodejs backend" → API Tools
    # JSON — bare "json" not mapped; "jsonschema"/"json-schema" exist but not "json parser" etc.
    "json": "developer",            # "json parser", "json validator", "json schema" → Developer Tools (AJV, Joi)
    # XML — xml parser/library/transformer queries → Developer Tools
    "xml": "developer",             # "xml parser", "xml library", "xslt tool" → Developer Tools
    # Network — "network monitoring", "network scanner", "network analysis" → Monitoring & Uptime
    "network": "monitoring",        # "network monitoring", "network scanner" → Monitoring & Uptime (Nmap, Prometheus)
    # URL — url shortener / parser / builder queries → Developer Tools (Dub.co, YOURLS, Kutt)
    "url": "developer",             # "url parser", "url shortener", "url builder" → Developer Tools
    # Hash — "hash function", "password hash", "hashing library" → Security Tools
    # "hashing" already mapped; "hash" bare form missing
    "hash": "security",             # "hash function", "hash library", "hash password" → Security Tools (bcrypt, argon2)
    # Astro Starlight — docs framework; pair with new catalog tool entry
    "starlight": "documentation",   # Astro Starlight — "starlight alternative", "starlight docs" → Documentation
    # File management — file upload UI and infrastructure libraries
    "uploadthing": "file",          # UploadThing — upload infra for Next.js/React (6k★) → File Management
    "uppy": "file",                 # Uppy — modular file uploader UI with progress (29k★) → File Management
    # Security — JWT alternative token standard and JOSE cryptographic primitives
    "jose": "security",             # jose — JS JOSE (JWT/JWK/JWE/JWS) library (10k★) → Security Tools
    "paseto": "security",           # PASETO — Platform-Agnostic SEcurity TOkens, JWT alternative → Security Tools
    # Frontend — date utility libraries (ubiquitous dev dependency)
    "date-fns": "frontend",         # date-fns — modern JS date utility library (34k★) → Frontend Frameworks
    # API — lightweight fetch wrappers common in modern JS stacks
    "ofetch": "api",                # ofetch — unjs fetch with better error handling (Nuxt 3) → API Tools
    # Documentation — Markdown processing ecosystem
    "unified": "documentation",     # unified — text processing ecosystem (remark/rehype base) → Documentation
    "marked": "documentation",      # marked — fast Markdown parser + renderer for JS (32k★) → Documentation
    # Testing — accessibility, coverage, and HTTP mocking/assertion tools
    "pa11y": "testing",             # pa11y — automated accessibility testing CLI → Testing Tools
    "coveralls": "testing",         # Coveralls — hosted code coverage tracking for OSS → Testing Tools
    "nock": "testing",              # Nock — HTTP server mocking for Node.js test suites → Testing Tools
    "supertest": "testing",         # SuperTest — HTTP assertions for Node.js REST APIs (13k★) → Testing Tools
    "miragejs": "testing",          # Mirage JS — in-browser API mocking for front-end tests → Testing Tools
    "istanbul": "testing",          # Istanbul — JS code coverage (foundational; now nyc/c8) → Testing Tools
    "nyc": "testing",               # nyc — Istanbul CLI coverage runner (most-used JS coverage) → Testing Tools
    "c8": "testing",                # c8 — native V8 code coverage for Node.js → Testing Tools
    # DevOps — Google's hermetic multi-language monorepo build system
    "bazel": "devops",              # Bazel — Google's multi-language build system (22k★) → DevOps & Infrastructure
    # API — GraphQL schema building and code generation tools
    "pothos": "api",                # Pothos — plugin-based TypeScript GraphQL schema builder → API Tools
    "graphql-codegen": "api",       # GraphQL Code Generator — type-safe codegen from schema → API Tools
    "genql": "api",                 # genql — type-safe GraphQL client generated from SDL → API Tools
    # Automation — "automation" alone (not prefixed by "workflow") must still route to AI & Automation
    "automation": "ai",             # "automation platform", "automation tool" → AI & Automation
    "automate": "ai",               # "automate workflow", "automate tasks" → AI & Automation
    # Browser / VS Code extensions — Developer Tools category hosts WXT, Plasmo, CRXJS
    "extension": "developer",       # "browser extension framework", "VS Code extension" → Developer Tools
    "chrome": "developer",          # "chrome extension toolkit", "chrome extension boilerplate" → Developer Tools
    "browser-extension": "developer",  # explicit hyphenated form → Developer Tools
    # Vanilla JS — common "vanilla js alternative" or "vanilla js state" queries
    "vanilla": "frontend",          # "vanilla JS", "vanilla JavaScript framework" → Frontend Frameworks
    # Template engines — Handlebars, Nunjucks, Mustache, EJS, Pug live in Developer Tools
    "templating": "developer",      # "templating engine", "template language" → Developer Tools
    # Rate limiting — hyphenated form complement to ratelimit→api, rate→api, limit→api
    "rate-limit": "api",            # "rate-limit middleware", "rate-limit library" → API Tools
    # Parser libraries — tree-sitter, xml2js, cheerio, csv-parse, html-parser → Developer Tools
    "parse": "developer",           # "xml parse library", "html parse", "json parse" → Developer Tools
    "parser": "developer",          # "html parser", "xml parser", "css parser" → Developer Tools
    # AI — agent memory layers (fast-growing 2026 segment: stateful persistent agent memory)
    "mem0": "ai",                   # mem0 — AI agent long-term memory layer (mem0ai/mem0, 22k★) → AI & Automation
    "zep": "ai",                    # Zep — fast, scalable AI agent memory server (getzep/zep, 5k★) → AI & Automation
    # AI — tool calling (complement to "toolcalling"→ai and "function-calling"→ai already mapped)
    "tool-calling": "ai",           # hyphenated — "tool-calling api", "tool-calling framework" → AI & Automation
    # Notifications — toast libraries (Sonner is the dominant React toast library in 2026)
    "sonner": "notifications",      # Sonner — opinionated toast notifications for React (9k★) → Notifications
    # Frontend — dark mode / theming library for Next.js
    "next-themes": "frontend",      # next-themes — dark mode theme provider for Next.js (3.5k★) → Frontend Frameworks
    # File management — image CDN and optimization service
    "imgix": "file",                # imgix — real-time image processing and delivery CDN → File Management
    # Frontend — state management multi-word queries ("state management library", "state management react")
    "state management": "frontend", # maps to Frontend Frameworks where Zustand, Jotai, MobX, Recoil live
    "state-management": "frontend", # hyphenated form — "state-management solution", "state-management library"
    # API Tools — rate limiting multi-word queries (Kong, Tyk, express-rate-limit, Upstash Ratelimit)
    "rate limiting": "api",         # "rate limiting library", "rate limiting middleware", "API rate limiting"
    "rate-limiting": "api",         # hyphenated — "rate-limiting solution", "rate-limiting service"
    "rate limiter": "api",          # "rate limiter npm", "rate limiter implementation", "distributed rate limiter"
    "rate-limiter": "api",          # hyphenated — "rate-limiter express", "rate-limiter redis"
    # API Tools — real-time (alt spelling without hyphen already mapped; add hyphenated form)
    "real-time": "api",             # "real-time updates", "real-time database" → API Tools (Ably, Pusher, Liveblocks)
    # Database — vector database multi-word queries (Pinecone, Qdrant, Weaviate, Chroma, pgvector)
    "vector database": "database",  # "vector database comparison", "vector database python" → Database
    "vector-database": "database",  # hyphenated — "vector-database hosting", "vector-database open source"
    "vector store": "database",     # "vector store integration", "vector store LangChain" → Database
    "vector-store": "database",     # hyphenated — "vector-store backend", "vector-store retrieval"
    # Database — LanceDB (embedded Rust vector database, common query target)
    "lancedb": "database",          # LanceDB — serverless embedded vector DB (lancedb/lancedb, 5.5k★)
    # Frontend — Redux Toolkit (the official opinionated Redux wrapper, 10k★)
    "redux-toolkit": "frontend",    # hyphenated slug form — "redux-toolkit vs zustand" → Frontend Frameworks
    "rtk": "frontend",              # RTK abbreviation — "rtk query", "rtk slice", "rtk setup" → Frontend Frameworks
    # API Tools — express-rate-limit (most popular Node.js rate limiting middleware)
    "express-rate-limit": "api",    # hyphenated slug — "express-rate-limit alternative" → API Tools
    # CI/CD — continuous integration/delivery/deployment queries
    # "integration" and "deployment" are in _FTS_STOP_WORDS so they're stripped, leaving
    # "continuous" alone with no mapping. Adding here routes CI/CD queries to DevOps correctly.
    "continuous": "devops",         # "continuous integration", "continuous deployment" → DevOps & Infrastructure
    "delivery": "devops",           # "continuous delivery", "delivery pipeline" → DevOps & Infrastructure
    # Git tooling — "git hooks", "git server", "git workflow", "git lfs" → DevOps & Infrastructure
    # Fixes: "git hooks" was misrouting via "hooks"→"frontend" since "hooks" fires before no git synonym
    "git": "devops",                # "git server", "git hooks", "git workflow" → DevOps & Infrastructure
    # .NET / C# ecosystem — very common developer queries not yet mapped
    # ASP.NET Core, Blazor, MVC, Minimal APIs, Razor Pages live in api-tools category
    "csharp": "api",                # C# — "csharp web framework", "csharp api" → API Tools (ASP.NET Core, Carter)
    "c-sharp": "api",               # hyphenated — "c-sharp alternative", "c-sharp rest api" → API Tools
    "dotnet": "api",                # .NET — "dotnet web framework", "dotnet api" → API Tools (ASP.NET Core, Minimal APIs)
    "aspnet": "api",                # ASP.NET — "aspnet core alternative", "aspnet mvc" → API Tools
    "aspnetcore": "api",            # compound — "aspnetcore setup", "aspnetcore tutorial" → API Tools
    "asp-net": "api",               # hyphenated — "asp-net core alternative", "asp-net web api" → API Tools
    # Blazor — .NET WebAssembly + Server UI framework (lives in frontend-frameworks)
    "blazor": "frontend",           # Blazor — "blazor alternative", "blazor wasm vs react" → Frontend Frameworks
    "blazorwasm": "frontend",       # compound — "blazorwasm setup", "blazor webassembly" → Frontend Frameworks
    # .NET MAUI — cross-platform mobile/desktop UI framework (lives in frontend-frameworks)
    "maui": "frontend",             # .NET MAUI — "maui alternative", "dotnet maui mobile" → Frontend Frameworks
    # Scala web frameworks — Akka already mapped; add Scala language term itself
    "scala": "api",                 # Scala — "scala web framework", "scala api" → API Tools (Play, ZIO HTTP, Tapir)
    # Clojure web development
    "clojure": "api",               # Clojure — "clojure web framework", "clojure ring" → API Tools (Ring, Compojure, Luminus)
    # Polling patterns — long polling, short polling are common real-time alternatives
    "polling": "api",               # "long polling", "http polling", "polling library" → API Tools (SSE, WebSocket alternatives)
    "longpolling": "api",           # compound — "longpolling server", "longpolling alternative" → API Tools
    "long-polling": "api",          # hyphenated — "long-polling setup", "long-polling vs websocket" → API Tools
    # Regex / regular expression tools — libraries, testers, engines → Developer Tools
    "regex": "developer",           # "regex library", "regex engine", "regex tester" → Developer Tools
    "regexp": "developer",          # compound — "regexp library", "regexp alternative" → Developer Tools
    # Build task runners — Make, Just, Task
    "makefile": "devops",           # Makefile / GNU Make — "makefile alternative", "make build tool" → DevOps & Infrastructure
    "gnumake": "devops",            # GNU Make — explicit form → DevOps & Infrastructure
    "justfile": "devops",           # Justfile — just command runner; "justfile alternative", "just task runner" → DevOps
    # Ruby web frameworks — common alternative query targets in the Ruby ecosystem
    "sinatra": "api",               # Sinatra — lightweight Ruby DSL for web apps (13k★); "sinatra alternative" → API Tools
    "grape": "api",                 # Grape — Ruby REST-like API framework on Rack (9k★); "grape alternative" → API Tools
    "hanami": "api",                # Hanami — full-stack Ruby framework (3k★); "hanami alternative" → API Tools
    # Python async HTTP — aiohttp is the canonical asyncio HTTP framework before FastAPI era
    "aiohttp": "api",               # aiohttp — async HTTP client/server for Python (14k★); "aiohttp alternative" → API Tools
    # Python ASGI / REST frameworks not yet mapped
    "litestar": "api",              # Litestar (formerly Starlite) — Python ASGI framework (5k★) → API Tools
    "falcon": "api",                # Falcon — bare-metal Python WSGI/ASGI REST framework (9k★) → API Tools
    "django-ninja": "api",          # Django Ninja — FastAPI-style REST on top of Django (7k★) → API Tools
    # Rust web frameworks — rocket.rs is the most-searched Rust alternative after Axum
    "rocket": "api",                # Rocket — ergonomic Rust web framework (23k★); "rocket alternative" → API Tools
    # Swift server-side framework — Vapor is the dominant Swift backend framework
    "vapor": "api",                 # Vapor — server-side Swift web framework (24k★); "vapor alternative" → API Tools
    # Microsoft Phi SLMs — phi-3 and phi-4 are the dominant small/local LLM query targets 2025-2026
    "phi": "ai",                    # Phi — Microsoft Phi SLMs; "phi-3 alternative", "phi model" → AI & Automation
    "phi3": "ai",                   # Phi-3 — "phi3 local", "phi3 mini inference" → AI & Automation
    "phi-3": "ai",                  # hyphenated — "phi-3 alternative", "phi-3 mini setup" → AI & Automation
    "phi4": "ai",                   # Phi-4 — "phi4 inference", "phi4 alternative" → AI & Automation
    "phi-4": "ai",                  # hyphenated — "phi-4 local llm", "phi-4 benchmark" → AI & Automation
    # Build systems — CMake dominates C/C++ builds (50k★); Meson/Conan are its indie alternatives
    "cmake": "devops",              # CMake — cross-platform C/C++ build system (50k★) → DevOps & Infrastructure
    "meson": "devops",              # Meson — fast C/C++ build system; "meson alternative" → DevOps & Infrastructure
    "conan": "devops",              # Conan — C/C++ package manager; "conan alternative" → DevOps & Infrastructure
    "vcpkg": "devops",              # vcpkg — Microsoft C/C++ package manager → DevOps & Infrastructure
    # Nu Shell — modern structured data shell in Rust (32k★)
    "nushell": "cli",               # Nu Shell — "nushell alternative", "nushell setup" → CLI Tools
    # Nim language — compiled, efficient; "nim web framework" queries → API Tools (Jester, httpbeast)
    "nim": "api",                   # Nim language — "nim alternative", "nim web framework" → API Tools
    # Crystal language — Ruby-syntax compiled language (20k★); "crystal web framework" → API Tools (Lucky, Kemal)
    "crystal": "api",               # Crystal — "crystal alternative", "crystal vs ruby" → API Tools
    # PKCE — modern OAuth 2.0 security pattern (Proof Key for Code Exchange)
    "pkce": "authentication",       # PKCE — "pkce library", "pkce oauth", "pkce implementation" → Authentication
    # Zola — Rust-based fast SSG (13k★); single binary, no runtime deps
    "zola": "frontend",             # Zola — "zola alternative", "zola vs hugo", "zola ssg" → Frontend Frameworks
    # mdBook — Rust-based book/docs tool (19k★; used for official Rust lang docs)
    "mdbook": "documentation",      # mdBook — "mdbook alternative", "mdbook vs docusaurus" → Documentation
    "md-book": "documentation",     # hyphenated — "md-book setup", "md-book alternative" → Documentation
    # Typst — modern markup-based typesetting system (33k★); LaTeX alternative for technical docs
    "typst": "documentation",       # Typst — "typst alternative", "typst vs latex", "typst docs" → Documentation
    # HyperFine — command-line benchmarking (22k★, Rust); more accurate than `time`
    "hyperfine": "testing",         # HyperFine — "hyperfine alternative", "hyperfine benchmark" → Testing Tools
    # Criterion.rs — statistics-driven Rust benchmarks (4k★); Divan is the newer alternative
    "criterion": "testing",         # Criterion.rs — "criterion alternative", "rust benchmarks" → Testing Tools
    "divan": "testing",             # Divan — lightweight Rust benchmarking framework → Testing Tools
    # MindsDB — ML models via SQL interface (26k★); connects AI to existing databases
    "mindsdb": "ai",                # MindsDB — "mindsdb alternative", "ml in sql" → AI & Automation
    # ZenML — open-source MLOps framework in Python (4k★)
    "zenml": "ai",                  # ZenML — "zenml alternative", "zenml pipeline" → AI & Automation
    # GoReleaser — Go release automation: build, sign, publish binaries (14k★)
    "goreleaser": "devops",         # GoReleaser — "goreleaser alternative", "go release tool" → DevOps & Infrastructure
    # MetaFlow — Netflix ML workflow framework (8k★); data + compute + orchestration
    "metaflow": "ai",               # MetaFlow — "metaflow alternative", "metaflow pipeline" → AI & Automation
    # AI — GPU / fine-tuning infrastructure (fast-growing 2026 query segment)
    "cuda": "ai",                   # CUDA — NVIDIA GPU toolkit; "cuda setup", "run model on cuda" → AI & Automation
    "flashattention": "ai",         # Flash Attention — memory-efficient attention; "flash attention v2" → AI & Automation
    "flash-attention": "ai",        # hyphenated — "flash-attention install", "flash-attention v3" → AI & Automation
    "gptq": "ai",                   # GPTQ — quantized LLM format; "gptq model", "gptq inference" → AI & Automation
    "awq": "ai",                    # AWQ — Activation-aware Weight Quantization; "awq quantize" → AI & Automation
    "bitsandbytes": "ai",           # bitsandbytes — 8-bit/4-bit PyTorch quantization; "bnb qlora" → AI & Automation
    "peft": "ai",                   # HuggingFace PEFT — parameter-efficient fine-tuning; "peft lora" → AI & Automation
    "trl": "ai",                    # HuggingFace TRL — RLHF/DPO fine-tuning library; "trl sft" → AI & Automation
    "rlhf": "ai",                   # RLHF — Reinforcement Learning from Human Feedback; "rlhf training" → AI & Automation
    "dpo": "ai",                    # DPO — Direct Preference Optimization; "dpo training", "dpo fine-tune" → AI & Automation
    "accelerate": "ai",             # HuggingFace Accelerate — distributed multi-GPU training; "accelerate launch" → AI & Automation
    # Games — major named game engines missing from synonyms
    "unity": "games",               # Unity — most-searched game engine; "unity alternative", "unity 6" → Games & Entertainment
    "unreal": "games",              # Unreal Engine — "unreal alternative", "ue5 alternative" → Games & Entertainment
    "bevy": "games",                # Bevy — Rust ECS game engine (37k★); "bevy alternative" → Games & Entertainment
    "defold": "games",              # Defold — free game engine by King; "defold alternative" → Games & Entertainment
    # MCP — FastMCP Python framework (fast-growing; complements "mcp"→mcp, "mcpserver"→mcp)
    "fastmcp": "mcp",               # FastMCP — Python MCP server framework (5k★); "fastmcp alternative" → MCP Servers
    # Auth — Microsoft Entra ID (formerly Azure Active Directory)
    "entra": "authentication",      # Microsoft Entra ID — "entra sso", "entra id alternative" → Authentication
    "azuread": "authentication",    # Azure Active Directory / Entra — compound form queries → Authentication
    "azure-ad": "authentication",   # hyphenated — "azure-ad sso", "azure-ad login library" → Authentication
    # Database — Google Cloud Spanner (globally distributed SQL)
    "spanner": "database",          # Google Cloud Spanner — "spanner alternative", "cloud spanner" → Database
    # Message Queue — ZeroMQ (high-performance async messaging library, 17k★)
    "zeromq": "message",            # ZeroMQ — "zeromq alternative", "zeromq python", "zeromq vs kafka" → Message Queue
    "zmq": "message",               # ZMQ abbreviation — "zmq library", "zmq socket" → Message Queue
    "0mq": "message",               # 0MQ — npm/pip package name form (zeromq/0mq ecosystem) → Message Queue
    # Database — Hibernate Java ORM (most-searched Java ORM for alternatives, 37k★)
    "hibernate": "database",        # Hibernate — "hibernate alternative", "hibernate orm", "hibernate vs jpa" → Database
    # API — SignalR ASP.NET real-time framework (high .NET ecosystem query volume)
    "signalr": "api",               # SignalR — "signalr alternative", "signalr vs websocket", "signalr core" → API Tools
    # Frontend — Android Jetpack Compose compound/hyphenated forms (complement to "jetpack"→frontend)
    "jetpackcompose": "frontend",   # compound — "jetpackcompose alternative", "jetpackcompose tutorial" → Frontend Frameworks
    "jetpack-compose": "frontend",  # hyphenated — "jetpack-compose setup", "jetpack-compose vs swiftui" → Frontend Frameworks
    # Background Jobs — Kafka Connect ETL (complement to "kafka"→message, "kafkaconnect" queries grow with data pipelines)
    "kafkaconnect": "background",   # compound — "kafkaconnect pipeline", "kafkaconnect setup" → Background Jobs (ETL)
    "kafka-connect": "background",  # hyphenated — "kafka-connect alternative", "kafka-connect source" → Background Jobs
    # Testing — WireMock HTTP stub server (most popular Java integration testing mock, 6k★)
    "wiremock": "testing",          # WireMock — "wiremock alternative", "wiremock setup", "wiremock vs msw" → Testing Tools
    # DevOps — HashiCorp Configuration Language (Terraform/Nomad/Consul use HCL)
    "hcl": "devops",                # HCL — "hcl syntax", "hcl alternative", "terraform hcl" → DevOps & Infrastructure
    # DevOps — OpenFaaS open-source FaaS platform (24k★)
    "openfaas": "devops",           # OpenFaaS — "openfaas alternative", "openfaas kubernetes" → DevOps & Infrastructure
    # DevOps — Knative Kubernetes serverless (5k★)
    "knative": "devops",            # Knative — "knative alternative", "knative serving", "knative eventing" → DevOps
    # Message Queue — Faust Python stream processing (complement to Kafka/Flink synonyms)
    "faust": "message",             # Faust — Python stream processing library (Kafka-based, robinhood/faust) → Message Queue
    # Message Queue — Strimzi Kafka on Kubernetes operator (4k★)
    "strimzi": "message",           # Strimzi — Kafka operator for Kubernetes; "strimzi alternative" → Message Queue
    # Background Jobs — Camunda process automation / BPM platform (30k★, very common query)
    "camunda": "background",        # Camunda — "camunda alternative", "camunda bpm", "camunda workflow" → Background Jobs
    "zeebe": "background",          # Zeebe — Camunda's distributed workflow engine; "zeebe alternative" → Background Jobs
    # Background Jobs — Conductor Netflix/Orkes workflow orchestration (14k★)
    "conductor": "background",      # Conductor — Netflix/Orkes workflow engine; "conductor alternative" → Background Jobs
    # Database — Snowpark Snowflake developer API (Python/Java/Scala)
    "snowpark": "database",         # Snowpark — Snowflake's Python/Java/Scala API; "snowpark alternative" → Database
    # DevOps — Kargo Kubernetes GitOps promotion (5k★)
    "kargo": "devops",              # Kargo — "kargo alternative", "kargo gitops", "kargo promotion" → DevOps & Infrastructure
    # DevOps — Flagger Kubernetes progressive delivery (5k★)
    "flagger": "devops",            # Flagger — "flagger alternative", "flagger canary", "flagger k8s" → DevOps & Infrastructure
    # API — F# language web framework queries (Giraffe, Saturn, Falco)
    "fsharp": "api",                # F# — "fsharp web framework", "fsharp api" → API Tools (Giraffe, Saturn, Falco)
    "f-sharp": "api",               # hyphenated — "f-sharp alternative", "f-sharp backend" → API Tools
    # Developer Tools — Pkl Apple's config language (2k★)
    "pkl": "developer",             # Pkl — Apple's configuration language; "pkl alternative", "pkl config" → Developer Tools
    # PHP — testing and static analysis tools (high query volume from PHP devs)
    "phpunit": "testing",           # PHPUnit — de facto PHP unit testing framework (18k★) → Testing Tools
    "phpstan": "testing",           # PHPStan — PHP static analysis tool; "phpstan alternative" → Testing Tools
    "psalm": "testing",             # Psalm — PHP static analysis by Vimeo (5k★) → Testing Tools
    "pest": "testing",              # Pest — elegant PHP testing framework inspired by Jest (10k★) → Testing Tools
    "rector": "developer",          # Rector — automated PHP refactoring and version upgrade tool (10k★) → Developer Tools
    "infection": "testing",         # Infection — PHP mutation testing framework (2k★) → Testing Tools
    # Ruby — code analysis and testing tools
    "rubocop": "testing",           # RuboCop — Ruby linter and code formatter (13k★) → Testing Tools
    "minitest": "testing",          # Minitest — Ruby's default test suite and benchmarking library → Testing Tools
    "sorbet": "developer",          # Sorbet — fast Ruby type checker by Stripe (3k★) → Developer Tools
    # Elixir — code quality and data pipeline tools
    "credo": "testing",             # Credo — static code analysis for Elixir (5k★) → Testing Tools
    "dialyxir": "testing",          # Dialyxir — Elixir/Erlang Dialyzer wrapper for type analysis → Testing Tools
    "broadway": "background",       # Broadway — Elixir concurrent multi-stage data ingestion (4k★) → Background Jobs
    "nerves": "devops",             # Nerves — Elixir embedded systems / IoT platform (3k★) → DevOps & Infrastructure
    "livebook": "ai",               # Livebook — Elixir collaborative Jupyter-like notebook (4k★) → AI & Automation
    # Go — static analysis, linting, and security tools
    "golangci": "testing",          # golangci-lint — fast Go meta-linter (16k★) → Testing Tools
    "golangci-lint": "testing",     # hyphenated — "golangci-lint alternative", "golangci-lint config" → Testing Tools
    "staticcheck": "testing",       # staticcheck — authoritative Go vet + extras linter (5k★) → Testing Tools
    "govulncheck": "security",      # govulncheck — official Go vulnerability scanner by Google → Security Tools
    "gosec": "security",            # gosec — Go security checker (7k★) → Security Tools
    "revive": "testing",            # Revive — fast, configurable Go linter (4k★) → Testing Tools
    # Chaos engineering — testing system resilience under failure conditions
    "chaostoolkit": "devops",       # Chaos Toolkit — open-source chaos engineering framework (2k★) → DevOps
    "chaos-toolkit": "devops",      # hyphenated — "chaos-toolkit experiment", "chaos-toolkit alternative" → DevOps
    "toxiproxy": "testing",         # Toxiproxy — TCP proxy for simulating network failures (10k★) → Testing Tools
    "litmus": "devops",             # LitmusChaos — CNCF chaos engineering for Kubernetes (4k★) → DevOps & Infrastructure
    "chaos-mesh": "devops",         # Chaos Mesh — Kubernetes chaos engineering platform (6k★) → DevOps & Infrastructure
    "chaosmesh": "devops",          # compound — "chaosmesh alternative", "chaosmesh setup" → DevOps & Infrastructure
    "pumba": "devops",              # Pumba — chaos tool for Docker containers (3k★) → DevOps & Infrastructure
    # gRPC / Protocol Buffers — "proto file", "proto schema", "proto codegen" (complement to grpc→api, protobuf→api)
    "proto": "api",                 # proto — "proto file", "proto codegen", "proto schema" → API Tools (gRPC, ConnectRPC)
    # ConnectRPC — gRPC-compatible HTTP/1+HTTP/2 protocol by buf.build (9k★ Go, 5k★ JS)
    "connect-rpc": "api",           # ConnectRPC — "connect-rpc alternative", "connectrpc go" → API Tools
    "connectrpc": "api",            # compound — "connectrpc setup", "connectrpc vs grpc" → API Tools
    # gRPC-Web — gRPC for browser clients; "grpc-web client", "grpc-web alternative"
    "grpc-web": "api",              # grpc-web — "grpc-web alternative", "grpc-web proxy" → API Tools
    "grpcweb": "api",               # compound — "grpcweb client", "grpcweb setup" → API Tools
    # Twirp — Twitch's minimal RPC framework over HTTP/JSON (12k★)
    "twirp": "api",                 # Twirp — "twirp alternative", "twirp rpc", "twirp vs grpc" → API Tools
    # Docker Compose — "compose file", "compose spec", "docker compose alternative"
    # (docker→devops already; bare "compose" also needs devops mapping)
    "compose": "devops",            # Docker Compose — "compose file", "compose spec", "compose alternative" → DevOps & Infrastructure
    # Release automation — semantic-release (angular/semantic-release, 20k★)
    "semantic-release": "devops",   # semantic-release — "semantic-release alternative", "semantic release setup" → DevOps
    "semanticrelease": "devops",    # compound — "semanticrelease config", "semanticrelease ci" → DevOps
    # Conventional Commits — commit message standard used by semantic-release, release-please, commitlint
    "conventional-commits": "devops",  # Conventional Commits — "conventional commits standard" → DevOps & Infrastructure
    "conventionalcommits": "devops",   # compound — "conventionalcommits spec", "conventionalcommits setup" → DevOps
    # SolidStart — official SolidJS meta-framework (SSR/SSG/islands; like Next.js for Solid)
    "solid-start": "frontend",      # SolidStart — "solid-start alternative", "solidstart ssr" → Frontend Frameworks
    "solidstart": "frontend",       # compound — "solidstart setup", "solidstart vs nextjs" → Frontend Frameworks
    # Analog — Angular meta-framework (SSR/SSG/API routes; like Next.js for Angular, 3k★)
    "analog": "frontend",           # Analog — "analog angular framework", "analog ssr" → Frontend Frameworks
    "analogjs": "frontend",         # compound — "analogjs alternative", "analogjs setup" → Frontend Frameworks
    # Solito — React Native + Next.js cross-platform navigation library (5k★)
    "solito": "frontend",           # Solito — "solito navigation", "solito alternative" → Frontend Frameworks
    # Avalonia — .NET cross-platform desktop/mobile UI framework (25k★; WPF alternative)
    "avalonia": "frontend",         # Avalonia — "avalonia alternative", "avalonia .net ui" → Frontend Frameworks
    "avaloniaui": "frontend",       # compound — "avaloniaui setup", "avaloniaui vs maui" → Frontend Frameworks
    # Tamagui — high-performance cross-platform React/React Native UI kit (11k★)
    "tamagui": "frontend",          # Tamagui — "tamagui alternative", "tamagui rn ui" → Frontend Frameworks
    # Gluestack UI — React Native universal UI components (5k★)
    "gluestack": "frontend",        # Gluestack UI — "gluestack alternative", "gluestack ui" → Frontend Frameworks
    "gluestack-ui": "frontend",     # hyphenated — "gluestack-ui setup", "gluestack-ui react-native" → Frontend Frameworks
    # Moti — React Native animation library by Fernando Rojo (3k★; inspired by Framer Motion)
    "moti": "frontend",             # Moti — "moti animation", "moti alternative" → Frontend Frameworks
    # Master CSS — syntax-first CSS framework (5k★; ultra-compact utility class syntax)
    "master-css": "frontend",       # Master CSS — "master-css alternative", "master css utility" → Frontend Frameworks
    "mastercss": "frontend",        # compound — "mastercss setup", "mastercss vs tailwind" → Frontend Frameworks
    # Open Props — CSS custom properties design token system (4k★; minimal, framework-agnostic)
    "open-props": "frontend",       # Open Props — "open-props alternative", "open props css" → Frontend Frameworks
    "openprops": "frontend",        # compound — "openprops setup", "openprops tokens" → Frontend Frameworks
    # Config management — Puppet, SaltStack, CFEngine live in DevOps & Infrastructure
    # "config management" was mis-routing to Frontend via "management"→"frontend"; "config" fixes this
    "config": "devops",             # "config management", "config server", "config file watcher" → DevOps & Infrastructure
    "puppet": "devops",             # Puppet — declarative infrastructure config management (17k★) → DevOps
    "saltstack": "devops",          # SaltStack — remote execution + config management (14k★) → DevOps
    "cfengine": "devops",           # CFEngine — oldest config management tool (2k★) → DevOps & Infrastructure
    "infrastructure": "devops",     # "infrastructure provisioning", "infrastructure management" → DevOps
    # Developer Tools — REPL environments and Language Server Protocol
    "repl" : "developer",           # REPL — "repl alternative", "browser repl", "node repl", "pry repl" → Developer Tools
    "lsp": "developer",             # LSP — Language Server Protocol tooling (Neovim LSP, clangd, pyright) → Developer Tools
    "language-server": "developer", # hyphenated — "language-server protocol", "language-server setup" → Developer Tools
    "languageserver": "developer",  # compound — "languageserver alternative", "languageserver node" → Developer Tools
    # Testing — singular "unit" and hyphenated "end-to-end" forms (complements to "e2e"→"testing")
    "unit": "testing",              # "unit test framework", "unit testing library", "unit test runner" → Testing Tools
    "end-to-end": "testing",        # "end-to-end testing framework", "end-to-end test runner" → Testing Tools
    # Frontend — isomorphic / universal JavaScript rendering pattern
    "isomorphic": "frontend",       # "isomorphic JavaScript", "isomorphic rendering", "universal app" → Frontend Frameworks
    # Database — hyphenated form of "timeseries" (complement to "timeseries"→database already mapped)
    "time-series": "database",      # "time-series database", "time-series data" → Database (TimescaleDB, InfluxDB, QuestDB)
    # API Tools — Huma Go API framework (code-first OpenAPI 3.1, 5k★)
    "huma": "api",                  # Huma — "huma alternative", "huma go framework", "huma openapi" → API Tools
    # Monitoring — Pydantic Logfire structured observability for Python/FastAPI (5k★)
    "logfire": "monitoring",        # Logfire — "logfire alternative", "logfire pydantic", "logfire fastapi" → Monitoring & Uptime
    # Invoicing — OpenMeter open-source usage metering and billing infrastructure (3.5k★)
    "openmeter": "invoicing",       # OpenMeter — "openmeter alternative", "openmeter billing" → Invoicing & Billing
    # Message Queue — pgmq Postgres-native message queue (tembo-io/pgmq, 3k★)
    "pgmq": "message",              # pgmq — "pgmq alternative", "postgres message queue" → Message Queues
    # File Management — Unstorage universal key-value and storage layer (unjs/unstorage, 2k★)
    "unstorage": "file",            # Unstorage — "unstorage alternative", "unstorage nuxt", "kv storage layer" → File Management
    # Frontend — Ark UI accessible component primitives built on Zag.js state machines
    "arkui": "frontend",            # Ark UI — "arkui alternative", "ark ui components" → Frontend Frameworks
    "ark-ui": "frontend",           # hyphenated — "ark-ui setup", "ark-ui vs radix" → Frontend Frameworks
    # Testing — linting tools (ESLint, Biome, OXLint, Pylint, Ruff live in Testing Tools)
    # "lint" has no synonym despite being one of the most common dev queries
    "lint": "testing",              # "javascript lint", "lint tool", "lint setup" → Testing Tools (ESLint, Biome, OXLint)
    "linter": "testing",            # "css linter", "python linter", "linter alternative" → Testing Tools
    "linting": "testing",           # "linting rules", "linting pipeline", "code linting" → Testing Tools
    # Testing — property-based testing pattern (Hypothesis, fast-check, PropEr, QuickCheck)
    "property-based": "testing",    # "property-based testing", "property-based test framework" → Testing Tools
    "fast-check": "testing",        # fast-check — TypeScript property-based testing (dubzzz/fast-check, 4k★) → Testing Tools
    "fastcheck": "testing",         # compound — "fastcheck alternative", "fastcheck setup" → Testing Tools
    # Testing — HTTP load testing and benchmarking tools
    "autocannon": "testing",        # autocannon — Node.js HTTP benchmarking (mcollina/autocannon, 9k★) → Testing Tools
    "vegeta": "testing",            # Vegeta — Go HTTP load testing (tsenart/vegeta, 23k★) → Testing Tools
    # Testing — API contract testing
    "dredd": "testing",             # Dredd — OpenAPI/API Blueprint HTTP testing (apiaryio/dredd, 4k★) → Testing Tools
    # Testing — visual regression testing
    "visual-regression": "testing", # "visual-regression testing", "visual-regression tool" → Testing Tools
    "backstop": "testing",          # BackstopJS — CSS visual regression testing (garris/backstopjs, 7k★) → Testing Tools
    "backstopjs": "testing",        # compound — "backstopjs alternative", "backstopjs setup" → Testing Tools
    "applitools": "testing",        # Applitools — visual AI testing (applitools/eyes-sdk-javascript) → Testing Tools
    # Caching — Redis alternatives not yet mapped
    "garnet": "caching",            # Microsoft Garnet — high-perf Redis-compatible cache server (microsoft/garnet, 10k★) → Caching
    "redict": "caching",            # Redict — community LGPL Redis fork (redict-io/redict) → Caching
    # Monitoring — Grafana eBPF auto-instrumentation and legacy agent queries
    "beyla": "monitoring",          # Grafana Beyla — eBPF auto-instrumentation without code changes (grafana/beyla, 2k★)
    "grafana-agent": "monitoring",  # Grafana Agent — legacy name for what is now Alloy; "grafana-agent alternative"
    # Search — vector and semantic search query patterns (distinct from "vector database"→database)
    "vector-search": "search",      # "vector-search backend", "vector-search service" → Search Engine
    "semantic-search": "search",    # "semantic-search engine", "semantic-search open source" → Search Engine
    "hybrid-search": "search",      # "hybrid-search BM25 + vectors", "hybrid-search Qdrant" → Search Engine
    # CRM & Sales — named tools missing from synonyms (common "[tool] alternative" query targets)
    "pipedrive": "crm",             # Pipedrive — sales-focused CRM with visual pipeline (very common alt query)
    "attio": "crm",                 # Attio — AI-native CRM for modern B2B SaaS teams
    "monica": "crm",                # Monica — open-source personal relationship manager (monicahq/monica, 21k★)
    "streak": "crm",                # Streak — CRM built inside Gmail; "streak alternative" → CRM & Sales
    # Social Media — named tools missing from synonyms
    "buffer": "social",             # Buffer — social media scheduling and analytics; "buffer alternative" → Social Media
    "hootsuite": "social",          # Hootsuite — social media management; "hootsuite alternative" → Social Media
    "mastodon": "social",           # Mastodon — decentralised open-source social network (joinmastodon/mastodon, 45k★)
    # Learning & Education — key query terms not yet mapped
    "anki": "learning",             # Anki — spaced-repetition flashcard app (ankitects/anki, 12k★) → Learning
    "moodle": "learning",           # Moodle — open-source LMS; "moodle alternative" → Learning & Education
    "lms": "learning",              # LMS — Learning Management System; generic query term → Learning & Education
    "flashcard": "learning",        # "flashcard app", "flashcard library" → Learning & Education
    "flashcards": "learning",       # plural — "flashcards API", "flashcards SRS" → Learning & Education
    # Feedback & Reviews — key terms not individually mapped
    "nps": "feedback",              # NPS (Net Promoter Score) — "nps tool", "nps survey" → Feedback & Reviews
    "csat": "feedback",             # CSAT (Customer Satisfaction Score) — "csat survey" → Feedback & Reviews
    # Publishing / Newsletters — dominant brand names not yet individually mapped
    "substack": "newsletters",      # Substack — "substack alternative" is a top publishing query → Newsletters
    "beehiiv": "newsletters",       # beehiiv — modern newsletter platform; "beehiiv alternative" → Newsletters
    # Scheduling & Booking — additional named tools
    "doodle": "scheduling",         # Doodle — group availability polling; "doodle alternative" → Scheduling
    "acuity": "scheduling",         # Acuity Scheduling — appointment booking; "acuity alternative" → Scheduling
    # Media Server — key named tools not yet mapped
    "jellyfin": "media",            # Jellyfin — open-source media server (jellyfin/jellyfin, 34k★) → Media Server
    "emby": "media",                # Emby — commercial Jellyfin-like media server; "emby alternative" → Media Server
    # Design & Creative — open-source Figma alternatives (complement to "figma"→design already mapped)
    "penpot": "design",             # Penpot — open-source Figma alternative (penpot/penpot, 35k★) → Design & Creative
    # Maps & Location — additional named tools / query terms
    "osm": "maps",                  # OpenStreetMap — "osm tiles", "osm geocoding", "osm alternative" → Maps & Location
    "protomaps": "maps",            # Protomaps — self-hosted PMTiles map tiles (protomaps/protomaps, 3k★) → Maps & Location
    # Games & Entertainment — additional named game engines
    "cocos": "games",               # Cocos — cross-platform game engine; "cocos alternative", "cocos2d" → Games & Entertainment
    # Mobile testing — end-to-end and UI testing for React Native / native mobile apps
    "detox": "testing",             # Detox — grey-box E2E testing for React Native (Wix, 11k★) → Testing Tools
    "maestro": "testing",           # Maestro — mobile UI testing by mobile.dev; simple YAML-based flows → Testing Tools
    # Authentication — hyphenated form of Better Auth (betterauth compound already mapped)
    "better-auth": "authentication", # Better Auth — hyphenated query form; "better-auth alternative" → Authentication
    # Analytics — self-hosted Google Analytics alternatives not yet in synonym map
    "matomo": "analytics",          # Matomo — open-source privacy-friendly web analytics (19k★) → Analytics & Metrics
    "pirsch": "analytics",          # Pirsch — privacy-friendly website analytics (cookie-free) → Analytics & Metrics
    # AI inference — fal.ai serverless GPU API for image/video generation
    "fal": "ai",                    # fal.ai — serverless GPU inference for Stable Diffusion/FLUX → AI & Automation
    "fal-ai": "ai",                 # hyphenated — "fal-ai alternative", "fal-ai setup" → AI & Automation
    # File management — CDN / object storage providers not yet mapped
    "bunny": "file",                # BunnyCDN — fast CDN + object storage; "bunny cdn alternative" → File Management
    "bunnycdn": "file",             # compound — "bunnycdn pricing", "bunnycdn vs cloudflare" → File Management
    # DevOps — CDN + edge compute providers not yet mapped
    "fastly": "devops",             # Fastly — CDN + edge cloud; "fastly alternative", "fastly waf" → DevOps & Infrastructure
    # Database — ParadeDB: Postgres-native Elasticsearch replacement
    "paradedb": "database",         # ParadeDB — full-text search + analytics inside Postgres → Database
    # Maps — MapLibre GL JS: open-source Mapbox GL alternative
    "maplibre": "maps",             # MapLibre GL JS — open-source WebGL maps (Mapbox fork, 10k★) → Maps & Location
    # Feature flags — OpenFeature standard (CNCF spec for feature flagging)
    "openfeature": "feature",       # OpenFeature — CNCF feature flag standard; SDK for JS/Go/Java → Feature Flags
    # Monitoring — observability backends for OpenTelemetry
    "honeycomb": "monitoring",      # Honeycomb.io — observability for production; OTel-first (SaaS) → Monitoring & Uptime
    "uptrace": "monitoring",        # Uptrace — open-source Jaeger/Grafana alternative; OTel backend → Monitoring & Uptime
    # Auth — common query verbs and OAuth/identity patterns not yet mapped
    "credential": "authentication",  # "credential manager", "credential store", "api credential" → Authentication
    "credentials": "authentication", # plural — "credentials vault", "credentials management" → Authentication
    "signin": "authentication",      # compound — "signin handler", "signin flow" → Authentication
    "sign-in": "authentication",     # hyphenated — "sign-in page", "sign-in with google" → Authentication
    "logout": "authentication",      # "logout endpoint", "logout handler", "single logout (SLO)" → Authentication
    "signout": "authentication",     # compound — "signout flow", "signout redirect" → Authentication
    "sign-out": "authentication",    # hyphenated — "sign-out redirect", "sign-out button" → Authentication
    "role": "authentication",        # "role management", "user roles", "role-based" → Authentication (RBAC)
    "tenant": "authentication",      # "tenant isolation", "single-tenant vs multi-tenant" → Authentication
    # API — AWS AppSync managed GraphQL and FastHTML Python web framework
    "appsync": "api",                # AWS AppSync — managed GraphQL + WebSocket + event API → API Tools
    "fasthtml": "api",               # FastHTML — Python web framework (HTMX-based); "fasthtml alternative" → API Tools
    # Developer Tools — Marimo reactive Python notebook (Jupyter alternative)
    "marimo": "developer",           # Marimo — reactive Python notebook; "marimo alternative" → Developer Tools
    # AI — LitServe fast model serving engine (Lightning AI)
    "litserve": "ai",                # LitServe — fast AI model serving on FastAPI; "litserve alternative" → AI & Automation
    # Frontend — Aceternity UI animated Tailwind+Framer Motion component library
    "aceternity": "frontend",        # Aceternity UI — animated components; "aceternity alternative" → Frontend Frameworks
    # API — Microsoft TypeSpec API definition language (OpenAPI/JSON Schema/gRPC codegen)
    "typespec": "api",              # TypeSpec — Microsoft's API definition language (16k★); "typespec alternative" → API Tools
    # Frontend — Nuxt UI by NuxtLabs (Tailwind-based Vue component library for Nuxt)
    "nuxt-ui": "frontend",          # Nuxt UI — hyphenated form; "nuxt-ui alternative", "nuxt-ui setup" → Frontend Frameworks
    "nuxtui": "frontend",           # Nuxt UI — compound form; "nuxtui install", "nuxtui vs shadcn" → Frontend Frameworks
    # Testing — MSW.js compound form (complement to "msw"→testing already mapped)
    "mswjs": "testing",             # MSW.js — compound; "mswjs alternative", "mswjs setup", "mswjs handler" → Testing Tools
    # Developer Tools — Effect.ts hyphenated form (complement to "effect"→developer, "effectts"→developer)
    "effect-ts": "developer",       # Effect.ts — hyphenated; "effect-ts alternative", "effect-ts vs fp-ts" → Developer Tools
    # Project Management — major named tools missing from synonyms (very high "alternative" query volume)
    "asana": "project",             # Asana — "asana alternative", "asana open source" → Project Management
    "monday": "project",            # Monday.com — "monday alternative", "monday.com vs jira" → Project Management
    "shortcut": "project",          # Shortcut (formerly Clubhouse) — dev PM; "shortcut alternative" → Project Management
    "height": "project",            # Height.app — AI-enhanced PM; "height alternative" → Project Management
    "wrike": "project",             # Wrike — enterprise PM; "wrike alternative", "wrike vs asana" → Project Management
    # Blockchain / Web3 — platform-specific named tools (complement to "blockchain"/"solidity"/"ethers" already mapped)
    "solana": "developer",          # Solana — "solana sdk", "solana development", "solana web3" → Developer Tools
    "alchemy": "developer",         # Alchemy — Web3 API + RPC; "alchemy alternative", "alchemy rpc" → Developer Tools
    "infura": "developer",          # Infura — "infura alternative", "infura rpc node" → Developer Tools
    "moralis": "developer",         # Moralis — "moralis alternative", "moralis web3 sdk" → Developer Tools
    # Design & Creative — major tools missing from synonyms
    "blender": "creative",          # Blender — 3D creation suite; "blender alternative", "blender python api" → Creative Tools (13k★)
    "inkscape": "design",           # Inkscape — open-source SVG/vector editor; "inkscape alternative" → Design & Creative
    "affinity": "design",           # Affinity Designer/Photo/Publisher — "affinity alternative" → Design & Creative
    "canva": "design",              # Canva — "canva alternative", "canva api", "canva open source" → Design & Creative
    "obs": "media",                 # OBS Studio — "obs alternative", "obs studio streaming" → Media Server (57k★)
    "kdenlive": "creative",         # Kdenlive — KDE open-source video editor; "kdenlive alternative" → Creative Tools
    "davinci": "creative",          # DaVinci Resolve — "davinci alternative", "davinci resolve free" → Creative Tools
    "audacity": "creative",         # Audacity — "audacity alternative", "audio editor open source" → Creative Tools
    # Forms — specific form backend services not yet in synonym map
    "formspree": "forms",           # Formspree — "formspree alternative", "html form backend" → Forms & Surveys
    "formspark": "forms",           # Formspark — "formspark alternative", "form api service" → Forms & Surveys
    "formsubmit": "forms",          # FormSubmit.co — "formsubmit alternative", "free form backend" → Forms & Surveys
    # CRM — additional named tools not yet mapped (common "[tool] alternative" queries)
    "zoho": "crm",                  # Zoho CRM — "zoho alternative", "zoho crm api" → CRM & Sales
    "freshsales": "crm",            # Freshsales — Freshworks CRM; "freshsales alternative" → CRM & Sales
    "copper": "crm",                # Copper CRM — Google Workspace-integrated; "copper alternative" → CRM & Sales
    # File management — image CDN and file processing services
    "imagekit": "file",             # ImageKit.io — "imagekit alternative", "image cdn api" → File Management
    "transloadit": "file",          # Transloadit — upload + processing API; "transloadit alternative" → File Management
    # Auth — directory services and cloud identity tools not yet mapped
    "jumpcloud": "authentication",  # JumpCloud — "jumpcloud alternative", "cloud directory service" → Authentication
    "freeipa": "authentication",    # FreeIPA — open-source identity mgmt (Red Hat); "freeipa alternative" → Authentication
    # Cloud providers — routing "[provider] alternative" queries to DevOps & Infrastructure
    "aws": "devops",               # AWS — "aws alternative", "replace aws", "aws free tier" → DevOps & Infrastructure
    "gcp": "devops",               # GCP — Google Cloud Platform; "gcp alternative", "gcp free tier" → DevOps & Infrastructure
    "azure": "devops",             # Azure — Microsoft Azure; "azure alternative", "azure free tier" → DevOps & Infrastructure
    # AWS managed service abbreviations — very common in "[service] alternative" developer queries
    "rds": "database",             # AWS RDS — "rds alternative", "rds postgres", "rds vs neon" → Database
    "ec2": "devops",               # AWS EC2 — "ec2 alternative", "ec2 vps", "cloud vm alternative" → DevOps & Infrastructure
    "ecs": "devops",               # AWS ECS — "ecs alternative", "ecs vs kubernetes" → DevOps & Infrastructure
    "eks": "devops",               # AWS EKS — "eks alternative", "eks setup", "managed kubernetes aws" → DevOps & Infrastructure
    "fargate": "devops",           # AWS Fargate — "fargate alternative", "serverless containers" → DevOps & Infrastructure
    "gke": "devops",               # GKE — Google Kubernetes Engine; "gke alternative", "gke vs eks" → DevOps & Infrastructure
    "aks": "devops",               # AKS — Azure Kubernetes Service; "aks alternative", "aks vs gke" → DevOps & Infrastructure
    # AI — LLM evaluation singular form (complement to "evals"→ai, "evaluation"→ai already mapped)
    "eval": "ai",                  # "llm eval", "model eval", "eval harness", "run eval" → AI & Automation
    # Security — Open Policy Agent abbreviation (complement to "open-policy-agent"→security already mapped)
    "opa": "security",             # OPA — Open Policy Agent; "opa policy", "opa alternative" → Security Tools
    # Email — deliverability (DKIM/SPF/DMARC are mapped; "deliverability" bare term was missing)
    "deliverability": "email",     # "email deliverability", "deliverability tool", "sender reputation" → Email Marketing
    # Frontend — hot module reload queries (Vite, Webpack, esbuild all feature HMR)
    "hot-reload": "frontend",      # "hot-reload setup", "hot-reload alternative" → Frontend Frameworks
    "hotreload": "frontend",       # compound — "hotreload webpack", "hotreload vite" → Frontend Frameworks
    # Security — SOPS secrets file encryption (getsops/sops, 17k★; Doppler/Vault alternative)
    "sops": "security",            # SOPS — "sops alternative", "sops encryption", "sops secrets" → Security Tools
    # Payments — Lemon Squeezy hyphenated form (compound "lemonsqueezy"→payments already mapped)
    "lemon-squeezy": "payments",   # "lemon-squeezy alternative", "lemon squeezy stripe" → Payments
    # SEO — major SEO platforms missing from synonyms (high "alternative" query volume)
    "ahrefs": "seo",               # Ahrefs — backlink and keyword analysis; "ahrefs alternative" → SEO Tools
    "semrush": "seo",              # SEMrush — all-in-one SEO suite; "semrush alternative" → SEO Tools
    "moz": "seo",                  # Moz Pro — domain authority + keyword tracking; "moz alternative" → SEO Tools
    # Database — Firebase Firestore (complement to "firebase"→database; queried separately)
    "firestore": "database",       # Firestore — Firebase NoSQL document DB; "firestore alternative" → Database
    # Notifications — SignalWire (Twilio competitor for programmable voice, SMS, video)
    "signalwire": "notifications", # SignalWire — "signalwire alternative", "signalwire vs twilio" → Notifications
    # Analytics — Simple Analytics compound form ("simple" is a stop word so compound form needs mapping)
    "simpleanalytics": "analytics", # Simple Analytics — compound; "simpleanalytics alternative" → Analytics
    # Publishing / RSS — content feeds and podcast hosting route to newsletters-content / media-server
    "rss": "newsletters",           # "rss reader", "rss generator", "rss feed library" → Newsletters & Content
    "feed": "newsletters",          # "content feed", "news feed", "atom feed" → Newsletters & Content
    "podcast": "media",             # "podcast hosting", "podcast rss", "podcast player" → Media Servers
    # Monitoring — error tracking hyphenated/compound forms (complement to sentry→monitoring, bugsnag→monitoring)
    "error-tracking": "monitoring",  # "error-tracking tool", "error-tracking service" → Monitoring & Uptime
    "errortracking": "monitoring",   # compound — "errortracking alternative", "errortracking open source" → Monitoring
    # Database — graph database hyphenated/short forms (Neo4j, Memgraph, FalkorDB; graphdb→database exists)
    "graph-database": "database",   # hyphenated — "graph-database engine", "graph-database alternative" → Database
    "graph-db": "database",         # short hyphenated — "graph-db setup", "graph-db hosting" → Database
    # AI — guardrail singular form (NeMo Guardrails, Guardrails AI, Llama Guard; guardrails→ai exists)
    "guardrail": "ai",              # singular — "llm guardrail", "ai guardrail", "guardrail framework" → AI & Automation
    # AI — LlamaIndex hyphenated form (llamaindex→ai compound already mapped; add dashed form)
    "llama-index": "ai",            # "llama-index setup", "llama-index alternative", "llama-index rag" → AI & Automation
    # AI — prompt engineering (writing better prompts, tooling for prompt management)
    "prompt-engineering": "ai",     # "prompt-engineering tool", "prompt-engineering framework" → AI & Automation
    "promptengineering": "ai",      # compound — "promptengineering library", "promptengineering guide" → AI & Automation
    # Developer Tools — dotfile managers (chezmoi, yadm, GNU Stow, dotbot, mackup)
    "dotfile": "developer",         # "dotfile manager", "dotfile setup", "dotfile sync" → Developer Tools
    "dotfiles": "developer",        # plural — "dotfiles manager", "dotfiles tool", "manage dotfiles" → Developer Tools
    # Developer Tools — PDF generation libraries (pdfkit, puppeteer PDF, WeasyPrint, ReportLab)
    "pdf-generation": "developer",  # hyphenated — "pdf-generation library", "pdf-generation api" → Developer Tools
    # DevOps — CI/CD hyphenated form (cicd→devops exists; add dashed variant)
    "ci-cd": "devops",              # "ci-cd pipeline", "ci-cd platform", "ci-cd alternative" → DevOps & Infrastructure
    # DevOps — Travis CI (major CI/CD platform; "travis alternative" is a common developer query)
    "travis": "devops",             # Travis CI — "travis alternative", "travis ci setup", "travis pricing" → DevOps
    # DevOps — JetBrains TeamCity CI/CD server (on-premise CI, "teamcity alternative" queries)
    "teamcity": "devops",           # TeamCity — "teamcity alternative", "teamcity self-hosted" → DevOps & Infrastructure
    # Learning & Education — generic query terms not yet in synonym map
    # NEED_MAPPINGS terms list includes these but _CAT_SYNONYMS needs them for search routing
    "quiz": "learning",             # "quiz app alternative", "quiz platform open source" → Learning & Education
    "course": "learning",           # "online course platform", "course builder self-hosted" → Learning & Education
    "srs": "learning",              # SRS — Spaced Repetition System; "srs app", "srs flashcards" → Learning & Education
    "mooc": "learning",             # MOOC — Massive Open Online Course; "mooc platform", "mooc alternative" → Learning & Education
    "e-learning": "learning",       # hyphenated — "e-learning platform", "e-learning open source" → Learning & Education
    "elearning": "learning",        # compound — "elearning alternative", "elearning software" → Learning & Education
    # Games & Entertainment — PixiJS disambiguation (pixi→developer is for conda; pixijs is the 2D game renderer)
    "pixijs": "games",              # PixiJS — fast 2D WebGL renderer for games/interactive graphics (43k★)
    "kaboom": "games",              # Kaboom.js — fun browser JS game programming library (7k★)
    "construct": "games",           # Construct — visual no-code cross-platform game engine (Scirra)
    "gamemaker": "games",           # GameMaker Studio — "gamemaker alternative", "gamemaker free" → Games
    # Social Media — federated/decentralised social platforms (thin synonym coverage)
    "fediverse": "social",          # Fediverse — "fediverse app", "fediverse alternative", "self-host fediverse" → Social Media
    "activitypub": "social",        # ActivityPub — "activitypub server", "activitypub implementation" → Social Media
    "misskey": "social",            # Misskey — "misskey alternative", "misskey vs mastodon" → Social Media
    # Customer Support — thin coverage (1 entry); adding live chat + named tools
    "livechat": "customer",         # generic — "livechat software", "livechat widget" → Customer Support
    "live-chat": "customer",        # hyphenated — "live-chat integration", "live-chat open source" → Customer Support
    "tawk": "customer",             # Tawk.to — free live chat; "tawk alternative", "tawk.to widget" → Customer Support
    # Landing Pages — thin coverage (2 entries); adding major website builders for "[tool] alternative" queries
    "carrd": "landing",             # Carrd.co — simple single-page sites; "carrd alternative", "carrd vs" → Landing Pages
    "wix": "landing",               # Wix — "wix alternative", "wix open source" → Landing Pages
    # Feedback & Reviews — thin coverage (2 entries); adding feedback board and testimonial queries
    "canny": "feedback",            # Canny.io — product feedback boards; "canny alternative", "canny open source" → Feedback & Reviews
    "testimonial": "feedback",      # "testimonial tool", "collect testimonials", "testimonial widget" → Feedback & Reviews
    # Newsletters & Content — thin coverage (4 entries); adding key publishing platform synonyms
    "buttondown": "newsletters",    # Buttondown — indie newsletter tool; "buttondown alternative" → Newsletters & Content
    "hashnode": "newsletters",      # Hashnode — dev blogging + newsletter; "hashnode alternative" → Newsletters & Content
    # Creative Tools — thin coverage (4 entries); adding DAWs and video editors
    "krita": "creative",            # Krita — digital painting application; "krita alternative" → Creative Tools
    "lmms": "creative",             # LMMS (Linux MultiMedia Studio) — free DAW; "lmms alternative" → Creative Tools
    "ardour": "creative",           # Ardour — open-source DAW; "ardour alternative", "ardour recording" → Creative Tools
    "openshot": "creative",         # OpenShot — open-source video editor; "openshot alternative" → Creative Tools
    "shotcut": "creative",          # Shotcut — free cross-platform video editor; "shotcut alternative" → Creative Tools
    # Design & Creative — thin coverage (5 entries); adding design tool synonyms and query terms
    "sketch": "design",             # Sketch — macOS vector design tool; "sketch alternative", "sketch mac" → Design & Creative
    "wireframe": "design",          # "wireframe tool", "wireframing software", "wireframe app" → Design & Creative
    "balsamiq": "design",           # Balsamiq — rapid wireframing; "balsamiq alternative", "balsamiq mockups" → Design & Creative
    "zeplin": "design",             # Zeplin — design handoff tool; "zeplin alternative", "zeplin open source" → Design & Creative
    "mockup": "design",             # "mockup generator", "mockup tool", "website mockup" → Design & Creative
    # SEO Tools — thin coverage (6 entries); adding research + analysis query terms
    "backlink": "seo",              # "backlink checker", "backlink analysis" → SEO Tools (Ahrefs, Moz, OpenLinkProfiler)
    "crawl": "seo",                 # "SEO crawler", "site crawl tool", "crawl errors" → SEO Tools (Screaming Frog alternatives)
    "serp": "seo",                  # "SERP tracker", "SERP rank checker", "SERP analysis" → SEO Tools
    "keyword": "seo",               # "keyword research tool", "keyword tracker", "keyword difficulty" → SEO Tools
    "pagespeed": "seo",             # "page speed test", "core web vitals tool", "pagespeed optimization" → SEO Tools
    # Social Media — thin coverage (6 entries); adding scheduler + platform synonyms
    "bluesky": "social",            # Bluesky — decentralised social network; "bluesky client", "bluesky alternative" → Social Media
    "tweet": "social",              # "tweet scheduler", "tweet composer", "twitter scheduler" → Social Media
    "linkedin": "social",           # "linkedin scheduler", "linkedin tool", "linkedin post scheduler" → Social Media
    "postiz": "social",             # Postiz — open-source social media scheduler; "postiz alternative" → Social Media
    "later": "social",              # Later.com — visual social media scheduler; "later alternative" → Social Media
    # Scheduling & Booking — thin coverage (7 entries); adding indie scheduling tools
    "tidycal": "scheduling",        # TidyCal — simple booking tool by AppSumo; "tidycal alternative" → Scheduling & Booking
    "zcal": "scheduling",           # Zcal.com — free Calendly alternative; "zcal alternative" → Scheduling & Booking
    "reclaim": "scheduling",        # Reclaim.ai — AI-powered time blocking; "reclaim alternative" → Scheduling & Booking
    # Feedback & Reviews — thin coverage (4 entries); adding product feedback + roadmap tools
    "productboard": "feedback",     # ProductBoard — product feedback and roadmap; "productboard alternative" → Feedback & Reviews
    "uservoice": "feedback",        # UserVoice — customer feedback platform; "uservoice alternative" → Feedback & Reviews
    "nolt": "feedback",             # Nolt.io — feature voting boards; "nolt alternative", "nolt open source" → Feedback & Reviews
    "sleekplan": "feedback",        # SleekPlan — customer feedback widget; "sleekplan alternative" → Feedback & Reviews
    # CLI Tools — thin coverage (3 entries); adding framework + TUI query terms
    "tui": "cli",               # Terminal User Interface — "tui app", "tui framework", "tui library" → CLI Tools
    "clack": "cli",             # Clack.cc — modern CLI prompts framework; "clack alternative" → CLI Tools
    "inquirer": "cli",          # Inquirer.js — interactive CLI prompts; "inquirer alternative" → CLI Tools
    "oclif": "cli",             # Oclif — Salesforce CLI framework; "oclif alternative" → CLI Tools
    "ink": "cli",               # Ink — React for CLIs; "ink cli", "ink react terminal" → CLI Tools
    "zx": "cli",                # Google zx — shell scripting with JS; "zx alternative" → CLI Tools
    # Feature Flags — thin coverage (4 entries); adding tool names + behaviour terms
    "rollout": "feature",       # "gradual rollout", "rollout strategy" → Feature Flags
    "experiment": "feature",    # "A/B experiment", "feature experiment" → Feature Flags
    "unleash": "feature",       # Unleash — open-source feature flags; "unleash alternative" → Feature Flags
    "flagsmith": "feature",     # Flagsmith — open-source feature flags; "flagsmith alternative" → Feature Flags
    "growthbook": "feature",    # GrowthBook — A/B testing + flags; "growthbook alternative" → Feature Flags
    # Maps & Location — thin coverage (4 entries); adding library names + query terms
    "leaflet": "maps",          # Leaflet.js — interactive maps library; "leaflet alternative" → Maps & Location
    "maplibre": "maps",         # MapLibre GL — WebGL vector maps; "maplibre alternative" → Maps & Location
    "routing": "maps",          # "route planning api", "routing api", "directions routing" → Maps & Location
    "directions": "maps",       # "directions api", "turn-by-turn navigation" → Maps & Location
    "openstreetmap": "maps",    # OpenStreetMap — "openstreetmap api", "osm tiles server" → Maps & Location
    "osm": "maps",              # OSM abbreviation — "osm api", "osm routing", "osm tiles" → Maps & Location
    # Boilerplates & Starters — thin coverage (4 entries); adding popular starter names
    "t3": "boilerplate",        # T3 Stack (create-t3-app); "t3 stack", "t3 boilerplate" → Boilerplates
    "shipfast": "boilerplate",  # ShipFast — Next.js SaaS starter; "shipfast alternative" → Boilerplates
    "makerkit": "boilerplate",  # MakerKit — SaaS starter kit; "makerkit alternative" → Boilerplates
    "saaskit": "boilerplate",   # Generic SaaS kit; "saas kit", "saaskit boilerplate" → Boilerplates
    # File Management — thin coverage (5 entries); adding storage service names + terms
    "bucket": "file",           # "S3 bucket", "cloud storage bucket", "object bucket" → File Management
    "blob": "file",             # "blob storage", "Azure Blob alternative" → File Management
    "minio": "file",            # MinIO — self-hosted S3-compatible object storage; "minio alternative" → File Management
    "r2": "file",               # Cloudflare R2 — "r2 alternative", "r2 storage" → File Management
    "backblaze": "file",        # Backblaze B2 — "backblaze alternative", "backblaze b2" → File Management
    # Caching — thin coverage (5 entries); adding Redis + modern in-memory alternatives
    "redis": "caching",         # Redis — the primary caching/in-memory db; "redis alternative" → Caching
    "valkey": "caching",        # Valkey — Redis fork (Linux Foundation); "valkey alternative" → Caching
    "dragonfly": "caching",     # Dragonfly — fast Redis replacement; "dragonfly alternative" → Caching
    "garnet": "caching",        # Garnet — Microsoft Redis-compatible cache; "garnet alternative" → Caching
    # Notifications — thin coverage (6 entries); adding key tool names
    "novu": "notifications",    # Novu — open-source notification infra; "novu alternative" → Notifications
    "ntfy": "notifications",    # ntfy — self-hosted push notifications; "ntfy alternative" → Notifications
    "gotify": "notifications",  # Gotify — self-hosted push server; "gotify alternative" → Notifications
    "apprise": "notifications", # Apprise — universal notification library; "apprise alternative" → Notifications
    "onesignal": "notifications", # OneSignal — "onesignal alternative", "onesignal open source" → Notifications
    # Project Management — thin coverage (6 entries); adding tool names + query terms
    "roadmap": "project",       # "product roadmap tool", "roadmap builder", "public roadmap" → Project Management
    "gantt": "project",         # "gantt chart tool", "gantt open source" → Project Management
    "plane": "project",         # Plane.so — open-source Jira alternative; "plane alternative" → Project Management
    "basecamp": "project",      # Basecamp — "basecamp alternative", "basecamp self-hosted" → Project Management
    "asana": "project",         # Asana — "asana alternative", "asana open source" → Project Management
    # Forms & Surveys — thin coverage (6 entries); adding tool names + query terms
    "jotform": "forms",         # JotForm — "jotform alternative", "jotform open source" → Forms & Surveys
    "formspree": "forms",       # Formspree — "formspree alternative", "formspree self-hosted" → Forms & Surveys
    "formbricks": "forms",      # Formbricks — open-source surveys; "formbricks alternative" → Forms & Surveys
    "questionnaire": "forms",   # "questionnaire tool", "questionnaire builder" → Forms & Surveys
    # Customer Support — thinnest category (4 "customer" keys); adding helpdesk + named tools
    "ticket": "support",           # "support ticket system", "ticket management", "open-source ticketing" → Customer Support
    "groove": "customer",          # Groove — SMB helpdesk; "groove alternative", "groove helpdesk" → Customer Support
    "gorgias": "customer",         # Gorgias — e-commerce support; "gorgias alternative" → Customer Support
    "helpscout": "customer",       # Help Scout — "helpscout alternative", "help scout email support" → Customer Support
    "kayako": "customer",          # Kayako — "kayako alternative", "kayako helpdesk" → Customer Support
    "freshchat": "customer",       # Freshchat — Freshworks live chat; "freshchat alternative" → Customer Support
    # Landing Pages — thinnest category (4 entries); adding link-in-bio + indie builders
    "linktree": "landing",         # Linktree — "linktree alternative", "link in bio page" → Landing Pages
    "linkinbio": "landing",        # compound — "linkinbio tool", "link-in-bio builder" → Landing Pages
    "link-in-bio": "landing",      # hyphenated — "link-in-bio page", "link-in-bio alternative" → Landing Pages
    "landen": "landing",           # Landen.co — indie landing page builder; "landen alternative" → Landing Pages
    "brizy": "landing",            # Brizy — drag-drop page/site builder; "brizy alternative" → Landing Pages
    # Newsletters & Content — thin (6 entries); adding major publishing platforms
    "medium": "newsletters",       # Medium — "medium alternative", "medium-like platform" → Newsletters & Content
    "kit": "email",                # Kit (ex-ConvertKit) — "kit email", "kit newsletter", "convertkit" → Email Marketing
    "revue": "newsletters",        # Revue (retired Twitter newsletters) — "revue alternative" → Newsletters & Content
    "writeas": "newsletters",      # Write.as — "writeas alternative", "write.as blog" → Newsletters & Content
    # Scheduling & Booking — adding indie scheduling tools not yet mapped
    "savvycal": "scheduling",      # SavvyCal — "savvycal alternative", "savvycal vs calendly" → Scheduling
    "appointlet": "scheduling",    # Appointlet — "appointlet alternative" → Scheduling & Booking
    "harmonizely": "scheduling",   # Harmonizely — "harmonizely alternative", indie Calendly clone → Scheduling
    # CRM & Sales — adding modern/indie CRM tools
    "folk": "crm",                 # Folk.app — modern AI CRM; "folk alternative", "folk crm" → CRM & Sales
    "close": "crm",                # Close CRM — sales-focused; "close crm alternative" → CRM & Sales
    "affinity": "crm",             # Affinity CRM — relationship intelligence; "affinity alternative" → CRM & Sales
    # Creative Tools — adding major open-source creative apps
    "gimp": "creative",            # GIMP — GNU Image Manipulation Program; "gimp alternative" → Creative Tools
    "natron": "creative",          # Natron — open-source VFX compositor; "natron alternative" → Creative Tools
    "resolve": "creative",         # DaVinci Resolve — "resolve alternative", "davinci resolve free" → Creative Tools
    "premiere": "creative",        # Adobe Premiere — "premiere alternative", "video editor free" → Creative Tools
    # MCP Servers — adding A2A protocol and tool-use query variants
    "a2s": "mcp",                  # A2S shorthand (agent-to-server); "a2s protocol", "a2s spec" → MCP Servers
    "tool-use": "mcp",             # "tool-use server", "tool-use sdk", "llm tool use" → MCP Servers
    "context-protocol": "mcp",    # hyphenated form of model context protocol → MCP Servers
    # Feedback & Reviews — adding rating/voting/idea-management query terms + named tools
    "rating": "feedback",          # "star rating widget", "rating system", "product rating" → Feedback & Reviews
    "vote": "feedback",            # "feature vote board", "feature voting", "idea vote" → Feedback & Reviews
    "idea": "feedback",            # "idea management board", "idea tracker", "idea voting" → Feedback & Reviews
    "pendo": "feedback",           # Pendo — product analytics + feedback; "pendo alternative" → Feedback & Reviews
    "delighted": "feedback",       # Delighted — NPS/CSAT survey tool; "delighted alternative" → Feedback & Reviews
    # Landing Pages — adding conversion-optimisation tools + indie builders
    "leadpages": "landing",        # Leadpages — "leadpages alternative", "leadpages open source" → Landing Pages
    "unbounce": "landing",         # Unbounce — A/B landing page testing; "unbounce alternative" → Landing Pages
    "tilda": "landing",            # Tilda — no-code website/landing builder; "tilda alternative" → Landing Pages
    "unicorn": "landing",          # Unicorn Platform — maker-focused landing pages; "unicorn platform" → Landing Pages
    # Newsletters & Content — adding referral/digest/decentralised newsletter tools
    "mailbrew": "newsletters",     # Mailbrew — curated email digest service; "mailbrew alternative" → Newsletters
    "paragraph": "newsletters",    # Paragraph.xyz — decentralised newsletter platform; "paragraph alternative" → Newsletters
    "sparkloop": "newsletters",    # SparkLoop — newsletter referral growth; "sparkloop alternative" → Newsletters
    # Design & Creative — adding major design app query terms
    "photoshop": "design",         # Adobe Photoshop — "photoshop alternative", "photoshop open source" → Design & Creative
    "excalidraw": "design",        # Excalidraw — virtual whiteboard/sketching; "excalidraw alternative" → Design & Creative
    "procreate": "design",         # Procreate — "procreate alternative", "procreate android" → Design & Creative
    # SEO Tools — adding popular WordPress SEO plugin names + technical SEO terms
    "rankmath": "seo",             # Rank Math — WordPress SEO plugin; "rankmath alternative" → SEO Tools
    "yoast": "seo",                # Yoast SEO — WordPress plugin; "yoast alternative", "yoast seo" → SEO Tools
    "robots": "seo",               # "robots.txt generator", "robots meta tag" → SEO Tools
    # Social Media — adding major platform names + scheduling tools
    "threads": "social",           # Meta Threads — "threads alternative", "threads scheduler" → Social Media
    "pixelfed": "social",          # Pixelfed — open-source Instagram alternative; "pixelfed self-hosted" → Social Media
    "socialbee": "social",         # SocialBee — social media scheduling SaaS; "socialbee alternative" → Social Media
    "planoly": "social",           # Planoly — visual Instagram/social planner; "planoly alternative" → Social Media
    "instagram": "social",         # "instagram scheduler", "instagram management tool" → Social Media
    # Learning & Education — adding major online course platform names
    "teachable": "learning",       # Teachable — hosted course platform; "teachable alternative" → Learning & Education
    "thinkific": "learning",       # Thinkific — online course builder; "thinkific alternative" → Learning & Education
    "kajabi": "learning",          # Kajabi — course + community; "kajabi alternative" → Learning & Education
    "learnworlds": "learning",     # LearnWorlds — interactive course platform; "learnworlds alternative" → Learning & Education
    "podia": "learning",           # Podia — course + newsletter + downloads; "podia alternative" → Learning & Education
    # CRM & Sales — direct query terms missing from synonym map (named tools are mapped; bare terms weren't)
    "crm": "crm",               # "crm tool", "open source crm", "free crm" → CRM & Sales (Twenty, Monica, Pipedrive alternatives)
    "leads": "crm",             # "leads management", "leads tracking", "sales leads" → CRM & Sales
    "deal": "crm",              # "deal pipeline", "deal management", "crm deals" → CRM & Sales
    # Games & Entertainment — "game" singular not yet mapped (named engines are, but generic queries weren't)
    "game": "games",            # "game engine", "game development", "indie game" → Games & Entertainment
    # Scheduling & Booking — "scheduling" direct form not yet mapped (only booking/calendar/appointment were)
    "scheduling": "scheduling", # "scheduling api", "meeting scheduler", "scheduling library" → Scheduling & Booking
    # Learning & Education — "education" variant not yet mapped (only "learning" terms were)
    "education": "learning",    # "education platform", "online education tool" → Learning & Education
    # Authentication — self-hosted IdP and SSO tools missing from synonym map
    "casdoor": "authentication",   # Casdoor — SSO/OAuth 2.0/OIDC server; "casdoor alternative", "casdoor sso" → Authentication
    "authelia": "authentication",  # Authelia — self-hosted 2FA + reverse-proxy auth; "authelia alternative" → Authentication
    "dex": "authentication",       # Dex — CNCF OpenID Connect IdP; "dex oidc", "dex idp", "dex alternative" → Authentication
    # Database — distributed SQL and version-controlled data tools
    "yugabyte": "database",        # YugabyteDB — distributed PostgreSQL-compatible SQL; "yugabyte alternative" → Database
    "dolt": "database",            # Dolt — Git for data; version-controlled SQL; "dolt alternative", "dolt database" → Database
    "rqlite": "database",          # rqlite — distributed SQLite on Raft; "rqlite alternative", "rqlite setup" → Database
    # DevOps — CI/CD and zero-trust access tools missing from synonym map
    "concourse": "devops",         # Concourse CI — container-native pipeline CI/CD; "concourse alternative" → DevOps
    "gitness": "devops",           # Gitness (Harness) — open-source DevOps + git hosting; "gitness alternative" → DevOps
    "teleport": "devops",          # Teleport — zero-trust infrastructure access; "teleport alternative" → DevOps
    "pomerium": "devops",          # Pomerium — identity-aware reverse proxy; "pomerium alternative" → DevOps
    # Email Marketing — missing transactional/bulk email service names
    "mailersend": "email",         # MailerSend — transactional email with generous free tier; "mailersend alternative" → Email Marketing
    "emailoctopus": "email",       # Email Octopus — affordable email marketing; "emailoctopus alternative" → Email Marketing
    # DevOps — missing image-builder tool
    "packer": "devops",            # HashiCorp Packer — machine image builder (VM/container); "packer alternative" → DevOps & Infrastructure
    # Database/BaaS — nhost (Hasura-powered Firebase alternative)
    "nhost": "database",           # Nhost — open-source Firebase alternative (GraphQL + Postgres); "nhost alternative" → Database
    # AI & Automation — missing local LLM app and agent toolkit
    "anythingllm": "ai",           # AnythingLLM — all-in-one local LLM app (36k★); "anythingllm alternative" → AI & Automation
    "agentkit": "ai",              # AgentKit (Coinbase CDP) — LLM agent toolkit; "agentkit alternative" → AI & Automation
    # Monitoring & Uptime — missing Docker log viewer and lightweight server monitor
    "dozzle": "monitoring",        # Dozzle — real-time Docker log viewer (18k★); "dozzle alternative" → Monitoring & Uptime
    "beszel": "monitoring",        # Beszel — lightweight server/container monitoring (12k★); "beszel alternative" → Monitoring & Uptime
    # Developer Tools — data exploration missing
    "datasette": "developer",      # Datasette — instant web UI for SQLite data; "datasette alternative" → Developer Tools
    # Logging — classic centralised log management platforms missing from synonym map
    "graylog": "logging",          # Graylog — open-source centralized log management; "graylog alternative" → Logging
    # Monitoring — APM and infrastructure monitoring tools missing from synonym map
    "dynatrace": "monitoring",     # Dynatrace — APM + observability SaaS; "dynatrace alternative" → Monitoring & Uptime
    "nagios": "monitoring",        # Nagios — classic IT infra monitoring (open-source core); "nagios alternative" → Monitoring & Uptime
    "zabbix": "monitoring",        # Zabbix — open-source enterprise monitoring; "zabbix alternative" → Monitoring & Uptime
    "statsd": "monitoring",        # StatsD — UDP-based application metrics daemon; "statsd alternative" → Monitoring & Uptime
    "opsgenie": "monitoring",      # Atlassian OpsGenie — on-call alerting; "opsgenie alternative" → Monitoring & Uptime
    "victorops": "monitoring",     # Splunk On-Call (VictorOps) — incident response; "victorops alternative" → Monitoring & Uptime
    # Search — cloud-native log search engine missing from synonym map
    "quickwit": "search",          # Quickwit — cloud-native full-text search for logs (8k★); "quickwit alternative" → Search Engine
    # Project Management — open-source alternatives missing from synonym map
    "openproject": "project",      # OpenProject — open-source project management (Jira alternative, 10k★); "openproject alternative" → Project Management
    "taiga": "project",            # Taiga — open-source agile PM tool (Jira/Asana alternative); "taiga alternative" → Project Management
    "huly": "project",             # Huly — all-in-one team platform (Linear + Notion + GitHub, 17k★); "huly alternative" → Project Management
    # Video conferencing / WebRTC — tool names missing from synonym map
    "jitsi": "api",                # Jitsi Meet — open-source video conferencing (22k★); "jitsi alternative", "jitsi self-hosted" → API Tools
    "mediasoup": "api",            # mediasoup — WebRTC SFU server (6k★); "mediasoup alternative", "mediasoup sfu" → API Tools
    # File Management / Image Processing — image manipulation tools missing from synonym map
    "imagemagick": "file",         # ImageMagick — universal image manipulation CLI (12k★); "imagemagick alternative" → File Management
    "thumbor": "file",             # Thumbor — smart image CDN + thumbnail server (10k★); "thumbor alternative" → File Management
    "pillow": "file",              # Pillow — Python PIL fork for image processing; "pillow python", "pillow alternative" → File Management
    "jimp": "file",                # JIMP — pure JS image processing library (14k★); "jimp alternative", "jimp node" → File Management
    # Testing / Code Quality — missing named tool
    "codeclimate": "testing",      # Code Climate — automated code quality + test coverage; "codeclimate alternative" → Testing Tools
    # Developer Tools — PDF generation service missing from synonym map
    "gotenberg": "developer",      # Gotenberg — Docker-powered PDF generation API (7k★); "gotenberg alternative" → Developer Tools
    # Security — SIEM and intrusion detection terms missing from synonym map
    "siem": "security",            # SIEM — Security Information and Event Management category term; "siem alternative", "open source siem" → Security Tools
    "wazuh": "security",           # Wazuh — open-source SIEM/XDR platform (10k★); "wazuh alternative" → Security Tools
    "ossec": "security",           # OSSEC — classic host-based intrusion detection system; "ossec alternative" → Security Tools
    # Workflow automation — Make.com (formerly Integromat) old name still frequently searched
    "integromat": "background",    # Make.com old name — "integromat alternative" searches → Background Jobs & Workflow Automation
    # DevOps — lightweight Kubernetes distributions missing from synonym map
    "k0s": "devops",               # k0s — zero-friction single-binary Kubernetes by Mirantis (8k★); "k0s alternative" → DevOps & Infrastructure
    "spinnaker": "devops",         # Spinnaker — Netflix multi-cloud continuous delivery platform (9k★); "spinnaker alternative" → DevOps & Infrastructure
    # Frontend — Vue 2 state management (superseded by Pinia; still heavily searched)
    "vuex": "frontend",            # Vuex — official Vue 2 state management library; "vuex alternative" → Frontend Frameworks
    # Config management — Chef and Salt complete the classic triad (puppet/saltstack already mapped)
    "chef": "devops",              # Chef Infra — declarative infrastructure config management (chef/chef, 7.5k★) → DevOps
    "salt": "devops",              # SaltStack short form — "salt alternative", "salt vs ansible" → DevOps & Infrastructure
    "configuration": "devops",     # "configuration management tool", "configuration server" → DevOps (Ansible, Puppet, Chef)
    # Backup and cloud sync — high-query OSS tools not yet in synonyms
    "restic": "devops",            # Restic — fast, secure, encrypted backup (restic/restic, 26k★) → DevOps & Infrastructure
    "rclone": "devops",            # Rclone — cloud storage sync and backup CLI (rclone/rclone, 47k★) → DevOps & Infrastructure
    "velero": "devops",            # Velero — Kubernetes backup and disaster recovery (vmware-tanzu/velero, 8.5k★) → DevOps
    # Service discovery — generic query term for Consul, Eureka, etcd queries
    "discovery": "devops",         # "service discovery", "service registry", "auto-discovery" → DevOps & Infrastructure
    # Monitoring — anomaly detection is a distinct monitoring query segment
    "anomaly": "monitoring",       # "anomaly detection", "anomaly alerting", "anomaly in metrics" → Monitoring & Uptime
    # Developer Tools — Spotify Backstage developer portal (internal developer portal platform, 27k★)
    "backstage": "developer",      # Backstage — "backstage alternative", "developer portal tool" → Developer Tools
    # AI — LLM observability and evaluation platforms (fast-growing 2026 segment)
    "openlit": "ai",               # OpenLIT — open-source LLM observability; "openlit alternative" → AI & Automation
    "langwatch": "ai",             # LangWatch — LLM testing + observability platform → AI & Automation
    # DevOps — microVM runtimes and Linux container managers (complement to containerd/podman already mapped)
    "firecracker": "devops",       # Firecracker — AWS microVM runtime; "firecracker alternative", "firecracker kata" → DevOps
    "microvm": "devops",           # "microVM runtime", "microVM hypervisor" — Firecracker, Kata Containers → DevOps
    "lxc": "devops",               # LXC — Linux Containers; "lxc alternative", "lxc vs docker" → DevOps & Infrastructure
    "lxd": "devops",               # LXD — LXC-based container/VM manager; "lxd alternative" → DevOps & Infrastructure
    "incus": "devops",             # Incus — community fork of LXD (lxc/incus, 3k★); "incus alternative" → DevOps
    # Database — Tembo.io managed PostgreSQL platform (common "tembo alternative" query target)
    "tembo": "database",           # Tembo — managed PostgreSQL stacks; "tembo alternative", "tembo postgres" → Database
}

_FTS_STOP_WORDS = {
    'best', 'top', 'good', 'for', 'the', 'a', 'an', 'my', 'your', 'our',
    'with', 'and', 'or', 'in', 'on', 'to', 'of', 'is', 'it', 'that',
    'integration', 'solution', 'alternative', 'tool', 'tools', 'library',
    'framework', 'platform', 'service', 'software', 'app', 'application',
    'like', 'similar', 'recommend', 'suggestion', 'find', 'need',
    'want', 'looking', 'what', 'which', 'how', 'can', 'should', 'would',
    'use', 'using', 'build', 'building', 'add', 'adding', 'implement',
    'indie', 'developer', 'developers', 'project', 'projects',
    'lightweight', 'simple', 'easy', 'fast', 'modern', 'new',
    'free', 'alternative', 'alternatives',
    'open', 'source',
    # Gerunds/filler words that don't add FTS value (tools use root form in descriptions).
    'running', 'tracking', 'managing',
}

# Framework qualifier terms in queries (e.g. "auth for nextjs", "payments django").
# FTS5 tokenizes "Next.js" as "next"+"js" separately, so "nextjs" won't FTS-match
# descriptions. These terms are auto-routed to frameworks_tested LIKE filter instead.
# Maps normalised query word → value stored in frameworks_tested column.
_FRAMEWORK_QUERY_TERMS: dict[str, str] = {
    "nextjs": "nextjs",           # "next.js" → "nextjs" after punctuation strip
    "react": "react", "reactjs": "react",
    "vue": "vue", "vuejs": "vue",
    "svelte": "svelte", "sveltekit": "sveltekit",
    "nuxt": "nuxt",
    "astro": "astro",
    "angular": "angular",
    "gatsby": "gatsby",
    "remix": "remix",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "express": "express",
    "rails": "rails",
    "laravel": "laravel",
    "spring": "spring",
    "electron": "electron",
    "tauri": "tauri",
    "nestjs": "nestjs", "nest": "nestjs",
    # Newer frameworks likely to appear in frameworks_tested
    "solid": "solid", "solidjs": "solid",
    "qwik": "qwik",
    "hono": "hono",
    # Runtime qualifiers — "logging nodejs" → FTS "logging" + frameworks_tested LIKE '%node%'
    # Only "node"/"nodejs" added here since these are rarely primary search targets.
    # "python", "rust", "ruby", "php" excluded — too often the primary search term
    # (e.g., "fastapi python api" must FTS-match "fastapi" not strip it as a framework).
    "node": "node",
    "nodejs": "node",
}


def sanitize_fts(query: str) -> str:
    """Sanitize input for FTS5 — strip special chars, stop words, add prefix matching."""
    query = re.sub(r'[^\w\s]', '', query).strip()
    if not query:
        return ''
    terms = query.lower().split()
    # Strip stop words but keep at least one term
    meaningful = [t for t in terms if t not in _FTS_STOP_WORDS]
    if not meaningful:
        meaningful = terms[:1]
    # For 4+ meaningful terms, use OR instead of AND to avoid over-constraining.
    # "cron job scheduler nodejs" AND-matched returns garbage because few tools have
    # all 4 terms. OR-matching lets the engagement scoring (category, tags) rank relevance.
    # 3-term queries stay AND — they're specific enough to work (e.g. "self hosted auth").
    if len(meaningful) > 3:
        return ' OR '.join(f'"{t[:40]}"*' for t in meaningful[:10])
    return ' '.join(f'"{t[:40]}"*' for t in meaningful[:10])


async def search_tools(
    db: aiosqlite.Connection,
    query: str,
    limit: int = 20,
    source_type: str = "",
    *,
    compatible_with: str = "",
    price: str = "",
    min_success_rate: int = 0,
    min_confidence: str = "",
    has_api: bool = False,
    language: str = "",
    tags: str = "",
    exclude: str = "",
    health: str = "",
    min_stars: int = 0,
    sort: str = "",
    frameworks: str = "",
):
    # Detect "[tool] alternative" pattern — auto-exclude the named tool
    # "stripe alternative" → search "stripe" but exclude stripe from results
    # "alternative to stripe" → same
    # Also exclude tools whose name contains the target (e.g. "dj-stripe",
    # "laravel-stripe-webhooks") — these are wrappers, not alternatives.
    _alt_patterns = re.match(
        r'^(.+?)\s+alternatives?\s*$|^alternatives?\s+(?:to|for)\s+(.+)$',
        query.strip(), re.IGNORECASE)
    if _alt_patterns:
        _alt_tool = (_alt_patterns.group(1) or _alt_patterns.group(2) or '').strip().lower()
        if _alt_tool and not exclude:
            if len(_alt_tool) >= 4:
                # Exclude tools whose name/slug contains the target (wrappers)
                # AND tools tagged with the target (complements built ON the target,
                # e.g. WorkAid Dunning tagged "Stripe" should not appear in "stripe alternative").
                _slug_cursor = await db.execute(
                    """SELECT slug FROM tools
                       WHERE (LOWER(name) LIKE ? OR slug LIKE ?
                              OR (',' || LOWER(tags) || ',') LIKE ?)
                       AND status = 'approved'""",
                    (f"%{_alt_tool}%", f"%{_alt_tool}%", f"%,{_alt_tool},%"))
            else:
                # Short names (< 4 chars) — exact match only to avoid over-excluding
                _slug_cursor = await db.execute(
                    "SELECT slug FROM tools WHERE (LOWER(name) = ? OR slug = ? OR slug = ?) AND status = 'approved'",
                    (_alt_tool, _alt_tool, f"pypi-{_alt_tool}"))
            _exclude_slugs = [r['slug'] for r in await _slug_cursor.fetchall()]
            if _exclude_slugs:
                exclude = ','.join(_exclude_slugs)

    # Build dynamic WHERE clauses shared across FTS and fallback queries
    extra_where = ""
    extra_params: list = []

    if source_type in ("code", "saas"):
        extra_where += " AND t.source_type = ?"
        extra_params.append(source_type)

    if compatible_with:
        extra_where += (
            " AND t.slug IN (SELECT CASE WHEN tool_a_slug = ? THEN tool_b_slug"
            " ELSE tool_a_slug END FROM tool_pairs"
            " WHERE (tool_a_slug = ? OR tool_b_slug = ?) AND success_count >= 1)"
        )
        extra_params.extend([compatible_with, compatible_with, compatible_with])

    if price == "free":
        extra_where += " AND t.price_pence IS NULL"
    elif price == "paid":
        extra_where += " AND t.price_pence > 0"

    if has_api:
        extra_where += " AND t.api_type IS NOT NULL AND t.api_type != ''"

    if language:
        extra_where += " AND LOWER(t.github_language) = LOWER(?)"
        extra_params.append(language)

    if tags:
        for tag in tags.split(","):
            tag = tag.strip()
            if tag:
                extra_where += " AND (',' || LOWER(t.tags) || ',') LIKE LOWER(?)"
                extra_params.append(f"%,{tag},%")

    if exclude:
        slugs = [s.strip() for s in exclude.split(",") if s.strip()]
        if slugs:
            placeholders = ",".join("?" for _ in slugs)
            extra_where += f" AND t.slug NOT IN ({placeholders})"
            extra_params.extend(slugs)

    if health and health in ("active", "stale", "dead", "archived"):
        extra_where += " AND t.health_status = ?"
        extra_params.append(health)

    if min_stars > 0:
        extra_where += " AND t.github_stars >= ?"
        extra_params.append(min_stars)

    if frameworks:
        fw_list = [f.strip().lower() for f in frameworks.split(",") if f.strip()]
        if fw_list:
            fw_conditions = " OR ".join(["LOWER(t.frameworks_tested) LIKE ?" for _ in fw_list])
            extra_where += f" AND ({fw_conditions})"
            extra_params.extend([f"%{fw}%" for fw in fw_list])

    # Engagement-weighted scoring expression for ORDER BY.
    # Uses columns available on the tools table: upvote_count, mcp_view_count,
    # github_stars, health_status, created_at.  Name-match boost requires
    # two extra LIKE params (exact match + prefix match) injected into the
    # parameter tuple — see `_engagement_params` below.
    # Category-name boost: tools whose category matches the query rank higher.
    # Engagement scoring: category match and tag match dominate. Stars are a
    # weak tiebreaker — SaaS tools (Stripe, Resend) have 0 stars but should
    # rank above open-source tools with stars in unrelated categories.
    # MCP views indicate real agent usage and get a strong boost.
    _engagement_expr = (
        "(CASE WHEN LOWER(t.slug) = LOWER(?) AND (t.source_type = 'saas' OR COALESCE(t.quality_score, 0) >= 85) THEN 2000"
        "  WHEN LOWER(t.name) = LOWER(?) AND COALESCE(t.install_command, '') != '' THEN 150"
        "  WHEN LOWER(t.name) = LOWER(?) THEN 30 ELSE 0 END)"
        " + (CASE WHEN LOWER(t.name) LIKE (LOWER(?) || '%') THEN 60 ELSE 0 END)"
        " + (CASE WHEN LOWER(c.name) LIKE ('%' || LOWER(?) || '%') THEN 100 ELSE 0 END)"
        " + (CASE WHEN EXISTS(SELECT 1 FROM tool_categories tc2 JOIN categories c2 ON c2.id=tc2.category_id WHERE tc2.tool_id=t.id AND LOWER(c2.name) LIKE ('%' || LOWER(?) || '%')) THEN 180 ELSE 0 END)"
        " + (CASE WHEN (',' || LOWER(t.tags) || ',') LIKE ('%,' || LOWER(?) || ',%') THEN 20 ELSE 0 END)"
        " + (t.upvote_count * 2)"
        " + (COALESCE(t.mcp_view_count, 0) * 5)"
        " + (MIN(COALESCE(t.github_stars, 0), 5000) / 500.0)"
        " + (CASE WHEN t.health_status = 'alive' THEN 5 ELSE 0 END)"
        " + (CASE WHEN t.maker_id IS NOT NULL THEN 15 ELSE 0 END)"
        " + (CASE WHEN COALESCE(t.install_command, '') = '' THEN -40 ELSE 10 END)"
        " + (CASE WHEN COALESCE(t.is_reference, 0) = 1 THEN -30 ELSE 0 END)"
        " + (CASE WHEN (SELECT COUNT(*) FROM agent_actions aa WHERE aa.tool_slug = t.slug AND aa.action = 'report_outcome') >= 3"
        "     THEN (SELECT CAST(SUM(CASE WHEN aa2.success = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 30"
        "           FROM agent_actions aa2 WHERE aa2.tool_slug = t.slug AND aa2.action = 'report_outcome')"
        "     ELSE 0 END)"
        " + (CASE WHEN t.created_at > datetime('now', '-14 days') THEN"
        "     5.0 * (1.0 - (julianday('now') - julianday(t.created_at)) / 14.0)"
        "    ELSE 0 END)"
        " + (COALESCE(t.quality_score, 0) * 1.5)"
    )
    # The five params consumed by _engagement_expr (exact name w/install, exact name w/o, prefix, category, tags)
    # For category and tag matching, find the best synonym match across all meaningful terms.
    _q = query.strip()
    _meaningful = [t for t in _q.lower().split() if t not in _FTS_STOP_WORDS]
    # Strip framework qualifier terms (nodejs, react, etc.) from category lookup.
    # "nodejs background jobs" → use ["background","jobs"] not ["nodejs","background","jobs"]
    # so cat_term doesn't become "nodejs" (which matches no category name).
    _meaningful_for_cat = [t for t in _meaningful if t not in _FRAMEWORK_QUERY_TERMS] or _meaningful
    _raw_cat = _meaningful_for_cat[0] if _meaningful_for_cat else _q
    # Map synonyms so "cron" → "background" matches "Background Jobs" category.
    # For queries like "self hosted auth", the first meaningful term ("self") has no
    # synonym — scan all terms and prefer the first with a known synonym so "auth"
    # from "self hosted auth" gets the 100-point Authentication category boost.
    _syn_term = next((t for t in _meaningful_for_cat if t in _CAT_SYNONYMS), None)
    if _syn_term:
        _cat_term = _CAT_SYNONYMS[_syn_term]
    else:
        _cat_term = _raw_cat
    _engagement_params: list = [_q, _q, _q, _q, _cat_term, _cat_term, _cat_term]

    # Determine sort order — returns (sql_fragment, extra_params)
    def _fts_order():
        if sort == "stars":
            return ("COALESCE(t.github_stars, 0) DESC, t.quality_score DESC", [])
        elif sort == "upvotes":
            return ("t.upvote_count DESC, t.quality_score DESC", [])
        elif sort == "newest":
            return ("t.created_at DESC", [])
        # Blend FTS rank with engagement scoring
        # Divisor 40 (vs 50) gives category/install signals more weight vs raw FTS rank.
        return (f"rank - ({_engagement_expr} / 40.0)", list(_engagement_params))

    def _browse_order():
        if sort == "stars":
            return ("COALESCE(t.github_stars, 0) DESC, t.quality_score DESC", [])
        elif sort == "upvotes":
            return ("t.upvote_count DESC, t.quality_score DESC", [])
        elif sort == "newest":
            return ("t.created_at DESC", [])
        return (f"{_engagement_expr} DESC", list(_engagement_params))

    safe_q = sanitize_fts(query)

    # Auto-detect framework qualifier terms (e.g. "auth for nextjs", "payments django").
    # FTS5 tokenises "Next.js" as "next"+"js", so "nextjs" never FTS-matches descriptions.
    # Route detected framework terms to a frameworks_tested LIKE filter and strip them from
    # the FTS query so they don't AND-constrain results into zero-return territory.
    # Only applies when no explicit `frameworks` param was passed by the caller.
    if not frameworks:
        _q_words_raw = re.sub(r'[^\w\s]', '', query.lower()).split()
        _fw_detected = list(dict.fromkeys(  # deduplicate, preserve order
            _FRAMEWORK_QUERY_TERMS[w] for w in _q_words_raw if w in _FRAMEWORK_QUERY_TERMS
        ))
        _non_fw_words = [w for w in _q_words_raw
                         if w not in _FRAMEWORK_QUERY_TERMS and w not in _FTS_STOP_WORDS]
        if _fw_detected and _non_fw_words:
            # "auth for nextjs" → FTS searches "auth", filter to frameworks_tested LIKE '%nextjs%'
            fw_conditions = " OR ".join("LOWER(t.frameworks_tested) LIKE ?" for _ in _fw_detected)
            extra_where += f" AND ({fw_conditions})"
            extra_params.extend(f"%{fw}%" for fw in _fw_detected)
            # Rebuild safe_q without framework terms so FTS stays tight
            safe_q = sanitize_fts(" ".join(_non_fw_words))

    # If no query text but filters are present, do a filter-only browse
    has_filters = any([
        compatible_with, price, has_api, language, tags, exclude,
        health, min_stars, source_type,
    ])

    if not safe_q and not has_filters:
        return []

    rows = []

    if safe_q:
        # Primary FTS query
        fts_sql, fts_ord_params = _fts_order()
        cursor = await db.execute(
            f"""SELECT t.*, c.name as category_name, c.slug as category_slug,
                      bm25(tools_fts, 10.0, 5.0, 1.0, 3.0) as rank
               FROM tools_fts fts
               JOIN tools t ON t.id = fts.rowid
               JOIN categories c ON t.category_id = c.id
               WHERE tools_fts MATCH ? AND t.status = 'approved'{extra_where}
               ORDER BY {fts_sql} LIMIT ?""",
            (safe_q, *extra_params, *fts_ord_params, limit),
        )
        rows = await cursor.fetchall()

        # Fallback 1: OR-based FTS for multi-word queries that returned 0 results
        # Uses meaningful terms (stop words stripped) for better matching
        words = query.strip().split()
        if not rows and len(words) > 1:
            clean_words = [re.sub(r'[^\w]', '', w)[:40] for w in words[:10]]
            clean_words = [w for w in clean_words if w and w.lower() not in _FTS_STOP_WORDS]
            if not clean_words:
                clean_words = [re.sub(r'[^\w]', '', w)[:40] for w in words[:3] if re.sub(r'[^\w]', '', w)]
            or_q = ' OR '.join(f'"{w}"*' for w in clean_words)
            if or_q:
                fts_sql2, fts_ord_params2 = _fts_order()
                cursor = await db.execute(
                    f"""SELECT t.*, c.name as category_name, c.slug as category_slug,
                              bm25(tools_fts, 10.0, 5.0, 1.0, 3.0) as rank
                           FROM tools_fts fts
                           JOIN tools t ON t.id = fts.rowid
                           JOIN categories c ON t.category_id = c.id
                           WHERE tools_fts MATCH ? AND t.status = 'approved'{extra_where}
                           ORDER BY {fts_sql2} LIMIT ?""",
                    (or_q, *extra_params, *fts_ord_params2, limit),
                )
                rows = await cursor.fetchall()

        # Fallback 2: LIKE-based search on individual words
        if not rows and words:
            like_conditions = " OR ".join(
                "(LOWER(t.name) LIKE LOWER(?) OR LOWER(t.tagline) LIKE LOWER(?) OR LOWER(t.description) LIKE LOWER(?))"
                for _ in words[:5]
            )
            like_params: list = []
            for w in words[:5]:
                pat = f"%{w}%"
                like_params.extend([pat, pat, pat])
            brw_sql, brw_ord_params = _browse_order()
            cursor = await db.execute(
                f"""SELECT t.*, c.name as category_name, c.slug as category_slug
                   FROM tools t
                   JOIN categories c ON t.category_id = c.id
                   WHERE ({like_conditions}) AND t.status = 'approved'{extra_where}
                   ORDER BY {brw_sql}
                   LIMIT ?""",
                (*like_params, *extra_params, *brw_ord_params, limit),
            )
            rows = await cursor.fetchall()

        # Fallback 3: search 'replaces' field for big-name tool queries
        if not rows:
            like_q = f"%{query.strip()}%"
            brw_sql, brw_ord_params = _browse_order()
            cursor = await db.execute(
                f"""SELECT t.*, c.name as category_name, c.slug as category_slug
                   FROM tools t
                   JOIN categories c ON t.category_id = c.id
                   WHERE LOWER(t.replaces) LIKE LOWER(?) AND t.status = 'approved'{extra_where}
                   ORDER BY {brw_sql}
                   LIMIT ?""",
                (like_q, *extra_params, *brw_ord_params, limit),
            )
            rows = await cursor.fetchall()
    else:
        # Filter-only browse (no FTS)
        brw_sql, brw_ord_params = _browse_order()
        cursor = await db.execute(
            f"""SELECT t.*, c.name as category_name, c.slug as category_slug
               FROM tools t
               JOIN categories c ON t.category_id = c.id
               WHERE t.status = 'approved'{extra_where}
               ORDER BY {brw_sql}
               LIMIT ?""",
            (*extra_params, *brw_ord_params, limit),
        )
        rows = await cursor.fetchall()

    # Post-query soft filters: min_success_rate and min_confidence
    if min_confidence and min_confidence not in ("low", "medium", "high"):
        min_confidence = ""
    if rows and (min_success_rate > 0 or min_confidence):
        confidence_levels = {"none": 0, "low": 1, "medium": 2, "high": 3}
        min_conf_level = confidence_levels.get(min_confidence, 0)

        passed = []
        failed = []
        for row in rows:
            rate_info = await get_tool_success_rate(db, row["slug"])
            conf_level = confidence_levels.get(rate_info["confidence"], 0)
            passes = True
            if min_success_rate > 0 and rate_info["rate"] < min_success_rate:
                passes = False
            if min_conf_level > 0 and conf_level < min_conf_level:
                passes = False
            if passes:
                passed.append(row)
            else:
                failed.append(row)

        # If fewer than 3 results pass, return filtered first then unfiltered remainder
        if len(passed) < 3:
            rows = passed + failed
        else:
            rows = passed

    return rows


# ── Submission Quality Gates ──────────────────────────────────────────────

def normalize_url(url: str) -> str:
    """Normalize a URL for duplicate detection.
    Strips scheme, www prefix, trailing slashes, and lowercases."""
    u = url.strip().lower()
    for prefix in ('https://', 'http://'):
        if u.startswith(prefix):
            u = u[len(prefix):]
    if u.startswith('www.'):
        u = u[4:]
    return u.rstrip('/')


_MIN_TAGLINE_LENGTH = 10
_MIN_DESCRIPTION_LENGTH = 50
_BLOCKED_SUBDOMAINS = (
    '.vercel.app', '.netlify.app', '.herokuapp.com', '.fly.dev',
    '.railway.app', '.render.com', '.surge.sh', '.pages.dev',
)

def validate_submission_quality(name: str, tagline: str, description: str, url: str = '') -> list[str]:
    """Run quality checks on a submission. Returns list of error messages (empty = pass)."""
    errors = []
    if len(tagline.strip()) < _MIN_TAGLINE_LENGTH:
        errors.append(f"Tagline must be at least {_MIN_TAGLINE_LENGTH} characters (currently {len(tagline.strip())}).")
    if len(description.strip()) < _MIN_DESCRIPTION_LENGTH:
        errors.append(f"Description must be at least {_MIN_DESCRIPTION_LENGTH} characters (currently {len(description.strip())}).")
    if name.strip().lower() == tagline.strip().lower():
        errors.append("Tagline should be different from the name.")
    # Catch obvious spam patterns
    desc = description.strip()
    if desc and desc == desc.upper() and len(desc) > 20:
        errors.append("Description should not be all uppercase.")
    if tagline.strip() and desc and tagline.strip().lower() in desc.lower() and len(desc) < len(tagline.strip()) + 20:
        errors.append("Description should add more detail beyond the tagline.")
    # Block default deployment subdomains
    if url:
        from urllib.parse import urlparse
        try:
            host = urlparse(url).hostname or ''
            if any(host.endswith(blocked) for blocked in _BLOCKED_SUBDOMAINS):
                errors.append(
                    "IndieStack requires a custom domain. Default deployment URLs "
                    "are not accepted. See /guidelines for submission requirements."
                )
        except Exception:
            pass
    return errors


async def check_duplicate_url(db: aiosqlite.Connection, url: str) -> Optional[dict]:
    """Check if a tool with the same normalized URL already exists.
    Returns the existing tool dict if found, None otherwise.
    Uses SQL-based normalization for efficiency (no full table scan in Python)."""
    normalized = normalize_url(url)
    # SQL-based URL normalization: strip scheme, www., trailing slashes, lowercase
    cursor = await db.execute(
        """SELECT id, name, slug, url FROM tools
           WHERE status != 'rejected'
           AND RTRIM(
               REPLACE(REPLACE(REPLACE(LOWER(url),
                   'https://', ''), 'http://', ''), 'www.', ''),
               '/'
           ) = ?
           LIMIT 1""",
        (normalized,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def enrich_domain_age(db: aiosqlite.Connection, tool_id: int, url: str) -> Optional[int]:
    """Look up domain age via WHOIS and store on tool record. Returns age in days or None."""
    from urllib.parse import urlparse
    from datetime import datetime
    try:
        import whois
        hostname = urlparse(url).hostname
        if not hostname:
            return None
        # Strip subdomains to get registrable domain (e.g. app.example.com -> example.com)
        parts = hostname.split('.')
        domain = '.'.join(parts[-2:]) if len(parts) >= 2 else hostname
        import asyncio as _aio
        w = await _aio.to_thread(whois.whois, domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation:
            now = datetime.now(creation.tzinfo) if creation.tzinfo else datetime.now()
            age_days = (now - creation).days
            await db.execute(
                "UPDATE tools SET domain_age_days = ? WHERE id = ?",
                (age_days, tool_id),
            )
            return age_days
    except Exception:
        pass
    return None


async def enrich_free_tier(db: aiosqlite.Connection, tool_id: int, url: str) -> Optional[bool]:
    """Scan a tool's landing page for free tier keywords. Returns True/False/None."""
    import httpx
    _FREE_KEYWORDS = (
        'free tier', 'free plan', 'free trial', 'try free', 'get started free',
        'no credit card', 'open source', 'open-source', 'free forever',
        'free version', 'starter plan', 'hobby plan', 'community edition',
    )
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code < 400:
                text = resp.text.lower()
                has_free = 1 if any(kw in text for kw in _FREE_KEYWORDS) else 0
                await db.execute(
                    "UPDATE tools SET has_free_tier = ? WHERE id = ?",
                    (has_free, tool_id),
                )
                return bool(has_free)
    except Exception:
        pass
    return None


async def enrich_social_proof(db: aiosqlite.Connection, tool_id: int, url: str) -> Optional[int]:
    """Query HackerNews Algolia API for mentions of this tool's domain. Returns mention count."""
    import httpx
    from urllib.parse import urlparse, quote
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return None
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://hn.algolia.com/api/v1/search?query={quote(hostname)}&tags=story&hitsPerPage=0"
            )
            if resp.status_code == 200:
                data = resp.json()
                count = data.get('nbHits', 0)
                await db.execute(
                    "UPDATE tools SET social_mentions_count = ? WHERE id = ?",
                    (count, tool_id),
                )
                return count
    except Exception:
        pass
    return None


# ── Submissions ───────────────────────────────────────────────────────────

async def create_tool(db: aiosqlite.Connection, *, name: str, tagline: str, description: str,
                      url: str, maker_name: str, maker_url: str, category_id: int, tags: str,
                      price_pence: Optional[int] = None, delivery_type: str = 'link',
                      delivery_url: str = '', stripe_account_id: str = '',
                      tool_type: Optional[str] = None, platforms: str = '',
                      install_command: str = '') -> int:
    slug = slugify(name)
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while True:
        existing = await db.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
        if await existing.fetchone() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Auto-create maker profile if maker_name provided
    maker_id = None
    if maker_name.strip():
        maker_id = await get_or_create_maker(db, maker_name.strip(), maker_url.strip())

    # Auto-detect source_type from URL
    url_lower = url.lower()
    source_type = 'code' if any(host in url_lower for host in ('github.com', 'gitlab.com', 'codeberg.org')) else 'saas'

    cursor = await db.execute(
        """INSERT INTO tools (name, slug, tagline, description, url, maker_name, maker_url,
           category_id, tags, price_pence, delivery_type, delivery_url, stripe_account_id, maker_id,
           tool_type, platforms, install_command, source_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, slug, tagline, description, url, maker_name, maker_url, category_id, tags,
         price_pence, delivery_type, delivery_url, stripe_account_id, maker_id,
         tool_type, platforms, install_command, source_type),
    )
    tool_id = cursor.lastrowid
    await db.execute(
        "INSERT OR IGNORE INTO tool_categories (tool_id, category_id, is_primary) VALUES (?, ?, 1)",
        (tool_id, category_id))
    await db.commit()
    return tool_id


async def get_category_by_name(db: aiosqlite.Connection, name: str):
    """Fuzzy category lookup: tries exact name, then slug, then case-insensitive."""
    cursor = await db.execute("SELECT * FROM categories WHERE name = ?", (name,))
    row = await cursor.fetchone()
    if row:
        return row
    cursor = await db.execute("SELECT * FROM categories WHERE slug = ?", (slugify(name),))
    row = await cursor.fetchone()
    if row:
        return row
    cursor = await db.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(?)", (name,))
    return await cursor.fetchone()


async def bulk_create_tools(db: aiosqlite.Connection, tools_data: list[dict]) -> tuple[int, list[str]]:
    """Import multiple tools at once. Returns (created_count, errors)."""
    created = 0
    errors = []
    for i, t in enumerate(tools_data):
        try:
            name = str(t.get('name', '')).strip()
            if not name:
                errors.append(f"Tool #{i+1}: missing name")
                continue

            # Resolve category
            cat_name = str(t.get('category', '')).strip()
            cat = await get_category_by_name(db, cat_name) if cat_name else None
            if not cat:
                errors.append(f"Tool #{i+1} ({name}): unknown category '{cat_name}'")
                continue

            slug = slugify(name)
            base_slug = slug
            counter = 1
            while True:
                existing = await db.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
                if await existing.fetchone() is None:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1

            await db.execute(
                """INSERT INTO tools (name, slug, tagline, description, url, maker_name, maker_url,
                   category_id, tags, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved')""",
                (name, slug,
                 str(t.get('tagline', '')).strip(),
                 str(t.get('description', '')).strip(),
                 str(t.get('url', '')).strip(),
                 str(t.get('maker_name', '')).strip(),
                 str(t.get('maker_url', '')).strip(),
                 cat['id'],
                 str(t.get('tags', '')).strip()),
            )
            created += 1
        except Exception as e:
            errors.append(f"Tool #{i+1} ({t.get('name', '?')}): {e}")
    await db.commit()
    return created, errors


# ── Admin ─────────────────────────────────────────────────────────────────

async def get_pending_avatars(db: aiosqlite.Connection) -> list:
    """Get users with unapproved pixel avatars."""
    cursor = await db.execute(
        "SELECT id, name, email, pixel_avatar FROM users WHERE pixel_avatar IS NOT NULL AND pixel_avatar != '' AND pixel_avatar_approved = 0"
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_pending_tools(db: aiosqlite.Connection):
    """Get pending tools sorted by quality signals — best submissions first.
    Incorporates enrichment data: domain age, free tier, social proof, health."""
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name,
           (CASE WHEN t.url LIKE '%github.com%' THEN 10 ELSE 0 END
            + CASE WHEN LENGTH(t.description) > 200 THEN 5 ELSE 0 END
            + CASE WHEN LENGTH(t.description) > 100 THEN 3 ELSE 0 END
            + CASE WHEN t.tags != '' AND t.tags IS NOT NULL THEN 2 ELSE 0 END
            + CASE WHEN t.maker_name != '' AND t.maker_name IS NOT NULL THEN 1 ELSE 0 END
            + CASE WHEN t.domain_age_days > 90 THEN 15
                   WHEN t.domain_age_days > 30 THEN 8
                   WHEN t.domain_age_days IS NOT NULL THEN -10
                   ELSE 0 END
            + CASE WHEN t.has_free_tier = 1 THEN 5
                   WHEN t.has_free_tier = 0 AND t.source_type = 'saas' THEN -5
                   ELSE 0 END
            + CASE WHEN t.social_mentions_count > 3 THEN 10
                   WHEN t.social_mentions_count > 0 THEN 5
                   ELSE 0 END
            - CASE WHEN t.health_status = 'dead' THEN 10 ELSE 0 END
           ) AS submission_quality
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'pending'
           ORDER BY submission_quality DESC, t.created_at DESC"""
    )
    return await cursor.fetchall()


async def get_all_tools_admin(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name
           FROM tools t JOIN categories c ON t.category_id = c.id
           ORDER BY t.created_at DESC"""
    )
    return await cursor.fetchall()


async def update_tool_status(db: aiosqlite.Connection, tool_id: int, status: str):
    await db.execute("UPDATE tools SET status = ? WHERE id = ?", (status, tool_id))
    await db.commit()


async def toggle_verified(db: aiosqlite.Connection, tool_id: int) -> bool:
    """Toggle verified status. Returns new is_verified state."""
    cursor = await db.execute("SELECT is_verified FROM tools WHERE id = ?", (tool_id,))
    row = await cursor.fetchone()
    if not row:
        return False
    new_val = 0 if row['is_verified'] else 1
    await db.execute("UPDATE tools SET is_verified = ? WHERE id = ?", (new_val, tool_id))
    await db.commit()
    return bool(new_val)


async def toggle_ejectable(db: aiosqlite.Connection, tool_id: int) -> bool:
    """Toggle ejectable status. Returns new is_ejectable state."""
    cursor = await db.execute("SELECT is_ejectable FROM tools WHERE id = ?", (tool_id,))
    row = await cursor.fetchone()
    if not row:
        return False
    new_val = 0 if row.get('is_ejectable') else 1
    await db.execute("UPDATE tools SET is_ejectable = ? WHERE id = ?", (new_val, tool_id))
    await db.commit()
    return bool(new_val)


# ── Upvotes ───────────────────────────────────────────────────────────────

def hash_ip(ip: str) -> str:
    return hashlib.sha256(f"{_UPVOTE_SALT}{ip}".encode()).hexdigest()


async def toggle_upvote(db: aiosqlite.Connection, tool_id: int, ip: str) -> tuple[int, bool]:
    """Toggle upvote. Returns (new_count, is_upvoted)."""
    ip_h = hash_ip(ip)

    # Use a transaction to prevent race conditions
    await db.execute("BEGIN IMMEDIATE")
    try:
        cursor = await db.execute(
            "SELECT id FROM upvotes WHERE tool_id = ? AND ip_hash = ?", (tool_id, ip_h)
        )
        existing = await cursor.fetchone()

        if existing:
            await db.execute("DELETE FROM upvotes WHERE id = ?", (existing['id'],))
            await db.execute(
                "UPDATE tools SET upvote_count = MAX(0, upvote_count - 1) WHERE id = ?",
                (tool_id,))
            upvoted = False
        else:
            await db.execute(
                "INSERT INTO upvotes (tool_id, ip_hash) VALUES (?, ?)",
                (tool_id, ip_h))
            await db.execute(
                "UPDATE tools SET upvote_count = upvote_count + 1 WHERE id = ?",
                (tool_id,))
            upvoted = True

        count_cursor = await db.execute(
            "SELECT upvote_count FROM tools WHERE id = ?", (tool_id,))
        row = await count_cursor.fetchone()
        count = row['upvote_count'] if row else 0

        await db.commit()
        return count, upvoted
    except Exception:
        await db.rollback()
        raise


async def increment_mcp_view(db: aiosqlite.Connection, tool_id: int):
    """Increment MCP view count when an AI agent looks up a tool."""
    await db.execute("UPDATE tools SET mcp_view_count = mcp_view_count + 1 WHERE id = ?", (tool_id,))
    await db.commit()


async def increment_mcp_views_bulk(db: aiosqlite.Connection, tool_ids: list[int]):
    """Increment MCP view count for multiple tools (search results)."""
    if not tool_ids:
        return
    await db.executemany(
        "UPDATE tools SET mcp_view_count = mcp_view_count + 1 WHERE id = ?",
        [(tid,) for tid in tool_ids],
    )
    await db.commit()


async def log_agent_citation(db: aiosqlite.Connection, tool_id: int, agent_name: str = "unknown", context: str = ""):
    """Log when an AI agent recommends/cites a tool."""
    await db.execute(
        "INSERT INTO agent_citations (tool_id, agent_name, context) VALUES (?, ?, ?)",
        (tool_id, agent_name, context[:200])
    )
    await db.commit()
    # Check citation milestones in background (non-blocking)
    try:
        await check_citation_milestones(db, tool_id)
    except Exception:
        pass


async def log_agent_citations_bulk(db: aiosqlite.Connection, tool_ids: list[int], agent_name: str = "unknown"):
    """Log agent citations for multiple tools (e.g. from search results)."""
    if not tool_ids:
        return
    await db.executemany(
        "INSERT INTO agent_citations (tool_id, agent_name) VALUES (?, ?)",
        [(tid, agent_name) for tid in tool_ids]
    )
    await db.commit()
    # Check citation milestones for each tool (non-blocking)
    for tid in tool_ids:
        try:
            await check_citation_milestones(db, tid)
        except Exception:
            pass


async def get_tool_total_citations(db: aiosqlite.Connection, tool_id: int) -> int:
    """Get all-time citation count for a single tool."""
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_citations WHERE tool_id = ?",
        (tool_id,)
    )
    row = await cursor.fetchone()
    return row['cnt'] if row else 0


async def check_citation_milestones(db: aiosqlite.Connection, tool_id: int):
    """Check if a tool has crossed citation milestones (10, 25, 50, 100, 250, 500, 1000).

    Creates a notification and sends an email for significant milestones.
    Uses the milestones table to avoid duplicate notifications.
    """
    CITATION_MILESTONES = [10, 25, 50, 100, 250, 500, 1000]
    EMAIL_MILESTONES = {50, 100, 500, 1000}  # Only email for big ones

    # Get total citation count
    total = await get_tool_total_citations(db, tool_id)
    if total < CITATION_MILESTONES[0]:
        return

    # Find the tool's maker and user
    cursor = await db.execute("""
        SELECT t.name, t.slug, t.maker_id, u.id as user_id, u.email,
               m.name as maker_name
        FROM tools t
        JOIN makers m ON m.id = t.maker_id
        JOIN users u ON u.maker_id = m.id
        WHERE t.id = ?
    """, (tool_id,))
    row = await cursor.fetchone()
    if not row:
        return

    user_id = row['user_id']
    tool_name = row['name']
    tool_slug = row['slug']
    maker_name = row['maker_name']
    email = row['email']

    for milestone in CITATION_MILESTONES:
        if total >= milestone:
            milestone_type = f'citations-{milestone}'
            awarded = await _award_milestone(db, user_id, tool_id, milestone_type)
            if awarded:
                # Create in-app notification
                await create_notification(
                    db, user_id, 'milestone',
                    f'{tool_name} has been recommended by AI agents {milestone} times!',
                    f'/tool/{tool_slug}'
                )
                # Send email for significant milestones
                if milestone in EMAIL_MILESTONES and email:
                    try:
                        from indiestack.email import send_email, citation_milestone_html
                        html = citation_milestone_html(
                            maker_name=maker_name,
                            tool_name=tool_name,
                            tool_slug=tool_slug,
                            milestone=milestone,
                            total=total,
                        )
                        await send_email(
                            email,
                            f'{tool_name} hit {milestone} AI recommendations!',
                            html,
                        )
                    except Exception:
                        pass


async def get_citation_counts_bulk(db: aiosqlite.Connection, tool_ids: list[int], days: int = 7) -> dict:
    """Get citation counts for multiple tools. Returns {tool_id: count}."""
    if not tool_ids:
        return {}
    placeholders = ','.join('?' * len(tool_ids))
    cursor = await db.execute(f"""
        SELECT tool_id, COUNT(*) as cnt
        FROM agent_citations
        WHERE tool_id IN ({placeholders})
          AND created_at >= datetime('now', ?)
        GROUP BY tool_id
    """, (*tool_ids, f'-{days} days'))
    return {r['tool_id']: r['cnt'] for r in await cursor.fetchall()}


async def get_compatible_pairs_bulk(db: aiosqlite.Connection, slugs: list[str], limit_per_tool: int = 3) -> dict:
    """Get top compatible pairs for multiple tools. Returns {slug: [pair_slugs]}."""
    if not slugs:
        return {}
    placeholders = ','.join('?' * len(slugs))
    cursor = await db.execute(f"""
        SELECT tool_a_slug, tool_b_slug, success_count
        FROM tool_pairs
        WHERE tool_a_slug IN ({placeholders}) OR tool_b_slug IN ({placeholders})
        ORDER BY success_count DESC
    """, (*slugs, *slugs))
    rows = await cursor.fetchall()
    slug_set = set(slugs)
    result = {}
    for r in rows:
        a, b = r['tool_a_slug'], r['tool_b_slug']
        if a in slug_set:
            result.setdefault(a, [])
            if len(result[a]) < limit_per_tool:
                result[a].append(b)
        if b in slug_set:
            result.setdefault(b, [])
            if len(result[b]) < limit_per_tool:
                result[b].append(a)
    return result


async def get_tool_citation_stats(db: aiosqlite.Connection, tool_id: int) -> dict:
    """Get citation stats for a single tool (7d, 30d counts + agent breakdown)."""
    c7 = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_citations WHERE tool_id = ? AND created_at >= datetime('now', '-7 days')",
        (tool_id,))
    r7 = await c7.fetchone()
    c30 = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_citations WHERE tool_id = ? AND created_at >= datetime('now', '-30 days')",
        (tool_id,))
    r30 = await c30.fetchone()
    ca = await db.execute("""
        SELECT agent_name, COUNT(*) as count
        FROM agent_citations
        WHERE tool_id = ? AND created_at >= datetime('now', '-30 days')
        GROUP BY agent_name ORDER BY count DESC LIMIT 5
    """, (tool_id,))
    agents = await ca.fetchall()
    return {
        "citations_7d": r7['cnt'] if r7 else 0,
        "citations_30d": r30['cnt'] if r30 else 0,
        "agents": [{"name": a['agent_name'], "count": a['count']} for a in agents],
    }


async def get_tool_demand_context(db: aiosqlite.Connection, slug: str, limit: int = 5) -> list:
    """Get search queries that lead to this tool (what demand it fills)."""
    cursor = await db.execute("""
        SELECT query, COUNT(*) as search_count, MAX(created_at) as last_searched
        FROM search_logs
        WHERE top_result_slug = ?
          AND LENGTH(query) >= 3
        GROUP BY LOWER(query)
        ORDER BY search_count DESC
        LIMIT ?
    """, (slug, limit))
    return [dict(r) for r in await cursor.fetchall()]


async def get_tool_category_percentile(db: aiosqlite.Connection, tool_id: int, category_id: int, days: int = 30) -> int:
    """Get a tool's citation percentile within its category."""
    cursor = await db.execute("""
        WITH tool_citations AS (
            SELECT t.id, COUNT(ac.id) as cite_count
            FROM tools t
            LEFT JOIN agent_citations ac ON ac.tool_id = t.id
                AND ac.created_at >= datetime('now', ?)
            WHERE t.category_id = ? AND t.status = 'approved'
            GROUP BY t.id
        )
        SELECT CAST(PERCENT_RANK() OVER (ORDER BY cite_count) * 100 AS INTEGER) as percentile
        FROM tool_citations
        WHERE id = ?
    """, (f'-{days} days', category_id, tool_id))
    row = await cursor.fetchone()
    return row['percentile'] if row else 0


async def get_agent_citation_counts(db: aiosqlite.Connection, maker_id: int, days: int = 7):
    """Get citation counts per tool for a maker, last N days."""
    cursor = await db.execute("""
        SELECT t.id, t.name, t.slug, COUNT(ac.id) as citation_count
        FROM tools t
        LEFT JOIN agent_citations ac ON ac.tool_id = t.id
            AND ac.created_at >= datetime('now', ?)
        WHERE t.maker_id = ? AND t.status = 'approved'
        GROUP BY t.id
        ORDER BY citation_count DESC
    """, (f'-{days} days', maker_id))
    return await cursor.fetchall()


async def get_total_agent_citations(db: aiosqlite.Connection, maker_id: int, days: int = 7):
    """Get total citations across all of a maker's tools."""
    cursor = await db.execute("""
        SELECT COUNT(ac.id) as total
        FROM agent_citations ac
        JOIN tools t ON ac.tool_id = t.id
        WHERE t.maker_id = ? AND ac.created_at >= datetime('now', ?)
    """, (maker_id, f'-{days} days'))
    row = await cursor.fetchone()
    return row['total'] if row else 0


async def get_citation_percentile(db: aiosqlite.Connection, maker_id: int, days: int = 30):
    """Get the maker's best-performing tool's citation percentile within its category."""
    cursor = await db.execute("""
        WITH tool_citations AS (
            SELECT t.id, t.name, t.category_id,
                   COUNT(ac.id) as cite_count
            FROM tools t
            LEFT JOIN agent_citations ac ON ac.tool_id = t.id
                AND ac.created_at >= datetime('now', ?)
            WHERE t.status = 'approved'
            GROUP BY t.id
        ),
        ranked AS (
            SELECT id, name, category_id, cite_count,
                   PERCENT_RANK() OVER (PARTITION BY category_id ORDER BY cite_count) as pct_rank
            FROM tool_citations
        )
        SELECT r.name, r.cite_count, CAST(r.pct_rank * 100 AS INTEGER) as percentile
        FROM ranked r
        JOIN tools t ON r.id = t.id
        WHERE t.maker_id = ?
        ORDER BY r.cite_count DESC
        LIMIT 1
    """, (f'-{days} days', maker_id))
    row = await cursor.fetchone()
    if not row:
        return {'name': '', 'citations': 0, 'percentile': None}
    if row['cite_count'] == 0:
        return {'name': row['name'], 'citations': 0, 'percentile': None}
    return {'name': row['name'], 'citations': row['cite_count'], 'percentile': row['percentile']}


async def get_maker_tool_citations(db: aiosqlite.Connection, maker_id: int) -> list[dict]:
    """Per-tool citation breakdown from maker_weekly_citations view (7d/30d/all)."""
    cursor = await db.execute("""
        SELECT tool_slug, tool_name, citations_7d, citations_30d, citations_all
        FROM maker_weekly_citations
        WHERE maker_id = ?
        ORDER BY citations_30d DESC
    """, (maker_id,))
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_weekly_citation_digest(db, days: int = 7) -> list[dict]:
    """Get citation data for all makers with cited tools in the last N days.

    Returns a list of dicts, one per tool that was cited:
    {maker_email, maker_name, tool_name, tool_slug, citation_count,
     agent_names (comma-separated), sample_context, user_id}
    """
    cursor = await db.execute("""
        SELECT
            u.email AS maker_email,
            m.name AS maker_name,
            t.name AS tool_name,
            t.slug AS tool_slug,
            COUNT(ac.id) AS citation_count,
            GROUP_CONCAT(DISTINCT ac.agent_name) AS agent_names,
            MAX(ac.context) AS sample_context,
            u.id AS user_id
        FROM agent_citations ac
        JOIN tools t ON t.id = ac.tool_id
        JOIN makers m ON m.id = t.maker_id
        JOIN users u ON u.maker_id = m.id
        WHERE ac.created_at >= datetime('now', ?)
          AND u.email IS NOT NULL
          AND u.email != ''
          AND COALESCE(u.email_opt_out, 0) = 0
        GROUP BY t.id
        ORDER BY citation_count DESC
    """, (f'-{days} days',))
    rows = await cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


async def toggle_stack_upvote(db: aiosqlite.Connection, stack_id: int, ip: str) -> tuple[int, bool]:
    """Toggle stack upvote. Returns (new_count, is_upvoted)."""
    ip_h = hash_ip(ip)
    await db.execute("BEGIN IMMEDIATE")
    try:
        cursor = await db.execute(
            "SELECT id FROM stack_upvotes WHERE stack_id = ? AND ip_hash = ?", (stack_id, ip_h)
        )
        existing = await cursor.fetchone()
        if existing:
            await db.execute("DELETE FROM stack_upvotes WHERE id = ?", (existing['id'],))
            await db.execute(
                "UPDATE stacks SET upvote_count = MAX(0, upvote_count - 1) WHERE id = ?",
                (stack_id,))
            upvoted = False
        else:
            await db.execute(
                "INSERT INTO stack_upvotes (stack_id, ip_hash) VALUES (?, ?)",
                (stack_id, ip_h))
            await db.execute(
                "UPDATE stacks SET upvote_count = upvote_count + 1 WHERE id = ?",
                (stack_id,))
            upvoted = True
        count_cursor = await db.execute(
            "SELECT upvote_count FROM stacks WHERE id = ?", (stack_id,))
        row = await count_cursor.fetchone()
        count = row['upvote_count'] if row else 0
        await db.commit()
        return count, upvoted
    except Exception:
        await db.rollback()
        raise


async def has_upvoted(db: aiosqlite.Connection, tool_id: int, ip: str) -> bool:
    ip_h = hash_ip(ip)
    cursor = await db.execute(
        "SELECT id FROM upvotes WHERE tool_id = ? AND ip_hash = ?", (tool_id, ip_h)
    )
    return await cursor.fetchone() is not None


# ── Purchases ────────────────────────────────────────────────────────────

async def create_purchase(db: aiosqlite.Connection, *, tool_id: int, buyer_email: str,
                          stripe_session_id: str, amount_pence: int, commission_pence: int,
                          discount_pence: int = 0) -> str:
    """Create a purchase record. Returns the unique purchase_token."""
    token = secrets.token_urlsafe(32)
    await db.execute(
        """INSERT INTO purchases (tool_id, buyer_email, stripe_session_id, amount_pence,
           commission_pence, purchase_token, discount_pence)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (tool_id, buyer_email, stripe_session_id, amount_pence, commission_pence, token, discount_pence),
    )
    await db.commit()
    return token


async def get_purchase_by_token(db: aiosqlite.Connection, token: str):
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug, t.delivery_type,
                  t.delivery_url, t.maker_name
           FROM purchases p LEFT JOIN tools t ON p.tool_id = t.id
           WHERE p.purchase_token = ?""",
        (token,),
    )
    return await cursor.fetchone()


async def get_purchase_by_session(db: aiosqlite.Connection, session_id: str):
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug, t.delivery_type,
                  t.delivery_url, t.maker_name
           FROM purchases p JOIN tools t ON p.tool_id = t.id
           WHERE p.stripe_session_id = ?""",
        (session_id,),
    )
    return await cursor.fetchone()


async def get_purchases_for_tool(db: aiosqlite.Connection, tool_id: int):
    cursor = await db.execute(
        """SELECT * FROM purchases WHERE tool_id = ? ORDER BY created_at DESC""",
        (tool_id,),
    )
    return await cursor.fetchall()


async def get_purchase_stats(db: aiosqlite.Connection):
    """Get total revenue and purchase count for admin dashboard."""
    cursor = await db.execute(
        """SELECT COUNT(*) as total_purchases,
                  COALESCE(SUM(amount_pence), 0) as total_revenue,
                  COALESCE(SUM(commission_pence), 0) as total_commission
           FROM purchases"""
    )
    return await cursor.fetchone()


async def get_all_purchases_admin(db: aiosqlite.Connection):
    """Get all purchases with tool and maker details for admin view."""
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug,
                  m.name as maker_name, m.slug as maker_slug
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           LEFT JOIN makers m ON t.maker_id = m.id
           ORDER BY p.created_at DESC"""
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_purchases_by_email(db: aiosqlite.Connection, email: str):
    """Get all purchases made by a buyer (matched by email)."""
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug,
                  t.delivery_url, t.delivery_type
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           WHERE p.buyer_email = ?
           ORDER BY p.created_at DESC""",
        (email,),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def update_tool_stripe_account(db: aiosqlite.Connection, tool_id: int, stripe_account_id: str):
    await db.execute("UPDATE tools SET stripe_account_id = ? WHERE id = ?", (stripe_account_id, tool_id))
    await db.commit()


# ── Verification ─────────────────────────────────────────────────────────

async def verify_tool(db: aiosqlite.Connection, tool_id: int):
    """Mark a tool as verified (paid verification)."""
    now = datetime.utcnow().isoformat()
    await db.execute(
        "UPDATE tools SET is_verified = 1, verified_at = ? WHERE id = ?",
        (now, tool_id),
    )
    await db.commit()


async def get_tool_by_id(db: aiosqlite.Connection, tool_id: int):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.id = ?""",
        (tool_id,),
    )
    return await cursor.fetchone()


# ── Makers ───────────────────────────────────────────────────────────────

async def get_or_create_maker(db: aiosqlite.Connection, name: str, url: str = '') -> int:
    """Get existing maker by name or create one. Returns maker_id."""
    slug = slugify(name)
    if not slug:
        return None
    cursor = await db.execute("SELECT id FROM makers WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if row:
        return row['id']
    cursor = await db.execute(
        "INSERT INTO makers (slug, name, url) VALUES (?, ?, ?)",
        (slug, name, url),
    )
    await db.commit()
    return cursor.lastrowid


async def get_maker_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute("SELECT * FROM makers WHERE slug = ?", (slug,))
    return await cursor.fetchone()


async def get_maker_with_tools(db: aiosqlite.Connection, slug: str):
    """Get maker profile and all their approved tools."""
    maker = await get_maker_by_slug(db, slug)
    if not maker:
        return None, []
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.maker_id = ? AND t.status = 'approved'
           ORDER BY t.upvote_count DESC""",
        (maker['id'],),
    )
    tools = await cursor.fetchall()
    return maker, tools


async def get_maker_stats(db: aiosqlite.Connection, maker_id: int) -> dict:
    """Get aggregate stats for a maker."""
    cursor = await db.execute(
        """SELECT COUNT(*) as tool_count,
                  COALESCE(SUM(upvote_count), 0) as total_upvotes,
                  COALESCE(SUM(is_verified), 0) as verified_count
           FROM tools WHERE maker_id = ? AND status = 'approved'""",
        (maker_id,),
    )
    return await cursor.fetchone()


# ── Featured Tool ────────────────────────────────────────────────────────

async def set_featured_tool(db: aiosqlite.Connection, tool_id: int, headline: str, description: str = ''):
    await db.execute(
        "INSERT INTO featured_tools (tool_id, headline, description) VALUES (?, ?, ?)",
        (tool_id, headline, description),
    )
    await db.commit()


async def get_featured_tool(db: aiosqlite.Connection):
    """Get the most recently featured tool."""
    cursor = await db.execute(
        """SELECT ft.*, t.name as tool_name, t.slug as tool_slug, t.tagline,
                  t.is_verified, t.upvote_count, t.url as tool_url,
                  c.name as category_name, c.slug as category_slug
           FROM featured_tools ft
           JOIN tools t ON ft.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY ft.featured_date DESC LIMIT 1"""
    )
    return await cursor.fetchone()


async def clear_featured_tool(db: aiosqlite.Connection):
    """Remove all featured tool entries (clears Tool of the Week)."""
    await db.execute("DELETE FROM featured_tools")
    await db.commit()


async def delete_tool(db: aiosqlite.Connection, tool_id: int):
    """Permanently delete a tool and all its referencing rows."""
    # Look up slug for tool_pairs cleanup (references by slug, not id)
    row = await db.execute("SELECT slug FROM tools WHERE id = ?", (tool_id,))
    slug_row = await row.fetchone()
    tool_slug = slug_row["slug"] if slug_row else None

    # Delete from all tables that reference tools(id)
    for table in [
        "upvotes", "purchases", "featured_tools", "collection_tools",
        "reviews", "tool_views", "wishlists", "maker_updates",
        "stack_tools", "user_stack_tools", "outbound_clicks",
        "claim_tokens", "magic_claim_tokens", "sponsored_placements",
        "milestones", "claim_requests", "tool_reactions",
        "agent_citations",
    ]:
        try:
            await db.execute(f"DELETE FROM {table} WHERE tool_id = ?", (tool_id,))
        except Exception:
            pass  # Table may not exist yet
    # Delete from tool_pairs (references by slug, not id)
    if tool_slug:
        try:
            await db.execute(
                "DELETE FROM tool_pairs WHERE tool_a_slug = ? OR tool_b_slug = ?",
                (tool_slug, tool_slug),
            )
        except Exception:
            pass
    # Delete from FTS index
    try:
        await db.execute("DELETE FROM tools_fts WHERE rowid = ?", (tool_id,))
    except Exception:
        pass
    await db.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
    await db.commit()


# ── Collections ──────────────────────────────────────────────────────────

async def create_collection(db: aiosqlite.Connection, *, title: str, description: str = '',
                            cover_emoji: str = '') -> int:
    slug = slugify(title)
    base_slug = slug
    counter = 1
    while True:
        existing = await db.execute("SELECT id FROM collections WHERE slug = ?", (slug,))
        if await existing.fetchone() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    cursor = await db.execute(
        "INSERT INTO collections (slug, title, description, cover_emoji) VALUES (?, ?, ?, ?)",
        (slug, title, description, cover_emoji),
    )
    await db.commit()
    return cursor.lastrowid


async def get_all_collections(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT c.*, COUNT(ct.tool_id) as tool_count
           FROM collections c
           LEFT JOIN collection_tools ct ON ct.collection_id = c.id
           GROUP BY c.id ORDER BY c.created_at DESC"""
    )
    return await cursor.fetchall()


async def get_collection_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute("SELECT * FROM collections WHERE slug = ?", (slug,))
    return await cursor.fetchone()


async def get_collection_with_tools(db: aiosqlite.Connection, slug: str):
    """Get collection and its tools in order."""
    coll = await get_collection_by_slug(db, slug)
    if not coll:
        return None, []
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM collection_tools ct
           JOIN tools t ON ct.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ct.collection_id = ? AND t.status = 'approved'
           ORDER BY ct.position ASC""",
        (coll['id'],),
    )
    tools = await cursor.fetchall()
    return coll, tools


async def add_tool_to_collection(db: aiosqlite.Connection, collection_id: int, tool_id: int, position: int = 0):
    try:
        await db.execute(
            "INSERT INTO collection_tools (collection_id, tool_id, position) VALUES (?, ?, ?)",
            (collection_id, tool_id, position),
        )
        await db.commit()
    except Exception:
        pass  # Already in collection


async def remove_tool_from_collection(db: aiosqlite.Connection, collection_id: int, tool_id: int):
    await db.execute(
        "DELETE FROM collection_tools WHERE collection_id = ? AND tool_id = ?",
        (collection_id, tool_id),
    )
    await db.commit()


async def delete_collection(db: aiosqlite.Connection, collection_id: int):
    await db.execute("DELETE FROM collection_tools WHERE collection_id = ?", (collection_id,))
    await db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
    await db.commit()


# ── Comparisons ──────────────────────────────────────────────────────────

async def get_tools_for_comparison(db: aiosqlite.Connection, slug1: str, slug2: str):
    """Get two tools by slug for comparison."""
    t1 = await get_tool_by_slug(db, slug1)
    t2 = await get_tool_by_slug(db, slug2)
    return t1, t2


async def get_category_tools_for_compare(db: aiosqlite.Connection, category_id: int, limit: int = 20):
    """Get tools in a category for generating compare links."""
    cursor = await db.execute(
        """SELECT t.slug, t.name FROM tools t
           WHERE t.category_id = ? AND t.status = 'approved'
           ORDER BY t.upvote_count DESC LIMIT ?""",
        (category_id, limit),
    )
    return await cursor.fetchall()


# ── Recently Added ───────────────────────────────────────────────────────

async def get_recent_tools(db: aiosqlite.Connection, limit: int = 6, days: int = 7):
    """Get recently approved tools."""
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY t.created_at DESC LIMIT ?""",
        (limit,),
    )
    return await cursor.fetchall()


# ── Users & Sessions ─────────────────────────────────────────────────────

async def create_user(db: aiosqlite.Connection, *, email: str, password_hash: str,
                      name: str, role: str = 'buyer', maker_id: Optional[int] = None) -> int:
    cursor = await db.execute(
        "INSERT INTO users (email, password_hash, name, role, maker_id, trial_ends_at) VALUES (?, ?, ?, ?, ?, datetime('now', '+7 days'))",
        (email.lower().strip(), password_hash, name.strip(), role, maker_id),
    )
    await db.commit()
    return cursor.lastrowid


async def ensure_referral_code(db, user_id: int) -> str:
    """Generate a referral code for a user if they don't have one. Returns the code."""
    cursor = await db.execute("SELECT referral_code FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    if row and row['referral_code']:
        return row['referral_code']
    code = 'REF-' + secrets.token_hex(3)
    # Ensure uniqueness
    for _ in range(10):
        existing = await db.execute("SELECT id FROM users WHERE referral_code = ?", (code,))
        if not await existing.fetchone():
            break
        code = 'REF-' + secrets.token_hex(3)
    await db.execute("UPDATE users SET referral_code = ? WHERE id = ?", (code, user_id))
    await db.commit()
    return code


async def get_user_by_referral_code(db, code: str):
    """Look up a user by their referral code."""
    cursor = await db.execute("SELECT * FROM users WHERE referral_code = ?", (code,))
    return await cursor.fetchone()


async def credit_referral_boost(db, referrer_user_id: int, days: int = 10):
    """Add boost days to a referrer's balance."""
    await db.execute(
        "UPDATE users SET referral_boost_days = referral_boost_days + ? WHERE id = ?",
        (days, referrer_user_id))
    await db.commit()


async def claim_referral_boost(db, user_id: int, tool_id: int) -> int:
    """Apply a user's accumulated referral boost days to a tool. Returns days applied."""
    cursor = await db.execute("SELECT referral_boost_days FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    if not row or not row['referral_boost_days'] or row['referral_boost_days'] <= 0:
        return 0
    days = row['referral_boost_days']
    await activate_boost(db, tool_id, days=days)
    await db.execute("UPDATE users SET referral_boost_days = 0 WHERE id = ?", (user_id,))
    await db.commit()
    return days


async def get_referral_count(db, user_id: int) -> int:
    """Count how many users were referred by this user."""
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE referred_by = ?", (user_id,))
    row = await cursor.fetchone()
    return int(row['cnt']) if row else 0


async def get_user_by_email(db: aiosqlite.Connection, email: str):
    cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    return await cursor.fetchone()


async def get_user_by_id(db: aiosqlite.Connection, user_id: int):
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return await cursor.fetchone()


async def get_user_by_github_id(db: aiosqlite.Connection, github_id: int):
    """Look up user by GitHub OAuth ID."""
    cursor = await db.execute("SELECT * FROM users WHERE github_id = ?", (github_id,))
    return await cursor.fetchone()


async def create_github_user(db: aiosqlite.Connection, email: str, name: str,
                              github_id: int, github_username: str, github_avatar_url: str):
    """Create a user from GitHub OAuth — no password, auto-verified email, 7-day Pro trial."""
    cursor = await db.execute(
        """INSERT INTO users (email, password_hash, name, role, email_verified,
                              github_id, github_username, github_avatar_url, trial_ends_at)
           VALUES (?, 'GITHUB_OAUTH_NO_PASSWORD', ?, 'buyer', 1, ?, ?, ?, datetime('now', '+7 days'))""",
        (email, name, github_id, github_username, github_avatar_url),
    )
    await db.commit()
    user_id = cursor.lastrowid
    # Generate referral code
    import secrets as _s
    ref_code = f"REF-{_s.token_hex(4).upper()}"
    await db.execute("UPDATE users SET referral_code = ? WHERE id = ?", (ref_code, user_id))
    await db.commit()
    return await get_user_by_id(db, user_id)


async def link_github_to_user(db: aiosqlite.Connection, user_id: int,
                               github_id: int, github_username: str, github_avatar_url: str):
    """Link a GitHub account to an existing user (matched by email)."""
    await db.execute(
        "UPDATE users SET github_id = ?, github_username = ?, github_avatar_url = ? WHERE id = ?",
        (github_id, github_username, github_avatar_url, user_id),
    )
    await db.commit()


async def create_session(db: aiosqlite.Connection, user_id: int, token: str, expires_at: str) -> int:
    cursor = await db.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at),
    )
    await db.commit()
    return cursor.lastrowid


async def get_session_by_token(db: aiosqlite.Connection, token: str):
    cursor = await db.execute(
        """SELECT s.*, u.id as uid, u.email, u.name, u.role, u.maker_id, u.email_verified,
                  u.pixel_avatar, u.pixel_avatar_approved
           FROM sessions s JOIN users u ON s.user_id = u.id
           WHERE s.token = ? AND s.expires_at > datetime('now')""",
        (token,),
    )
    return await cursor.fetchone()


async def delete_session(db: aiosqlite.Connection, token: str):
    await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    await db.commit()


async def delete_expired_sessions(db: aiosqlite.Connection):
    await db.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
    await db.commit()


async def cleanup_expired_sessions(db: aiosqlite.Connection):
    """Delete expired sessions to prevent table bloat."""
    await db.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    await db.commit()


_ALLOWED_USER_FIELDS = {'name', 'email', 'avatar_url', 'bio', 'maker_id', 'role', 'email_verified', 'email_opt_out', 'password_hash', 'github_id', 'github_username', 'referral_code', 'referred_by', 'pixel_avatar', 'pixel_avatar_approved'}

async def update_user(db: aiosqlite.Connection, user_id: int, **fields):
    fields = {k: v for k, v in fields.items() if k in _ALLOWED_USER_FIELDS}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    await db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    await db.commit()


# ── Reviews ──────────────────────────────────────────────────────────────

async def create_review(db: aiosqlite.Connection, *, tool_id: int, user_id: int,
                        rating: int, title: str = '', body: str = '') -> int:
    # Auto-detect verified purchase
    cursor = await db.execute(
        """SELECT id FROM purchases WHERE tool_id = ? AND buyer_email = (
            SELECT email FROM users WHERE id = ?
        )""",
        (tool_id, user_id),
    )
    is_verified_purchase = 1 if await cursor.fetchone() else 0
    cursor = await db.execute(
        """INSERT INTO reviews (tool_id, user_id, rating, title, body, is_verified_purchase)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(tool_id, user_id) DO UPDATE SET
           rating=excluded.rating, title=excluded.title, body=excluded.body""",
        (tool_id, user_id, rating, title.strip(), body.strip(), is_verified_purchase),
    )
    await db.commit()
    return cursor.lastrowid


async def get_reviews_for_tool(db: aiosqlite.Connection, tool_id: int):
    cursor = await db.execute(
        """SELECT r.*, u.name as reviewer_name
           FROM reviews r JOIN users u ON r.user_id = u.id
           WHERE r.tool_id = ?
           ORDER BY r.created_at DESC""",
        (tool_id,),
    )
    return await cursor.fetchall()


async def get_tool_rating(db: aiosqlite.Connection, tool_id: int) -> dict:
    cursor = await db.execute(
        """SELECT COALESCE(AVG(rating), 0) as avg_rating, COUNT(*) as review_count
           FROM reviews WHERE tool_id = ?""",
        (tool_id,),
    )
    return await cursor.fetchone()


async def get_user_review_for_tool(db: aiosqlite.Connection, tool_id: int, user_id: int):
    cursor = await db.execute(
        "SELECT * FROM reviews WHERE tool_id = ? AND user_id = ?",
        (tool_id, user_id),
    )
    return await cursor.fetchone()


async def get_all_reviews_admin(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT r.*, u.name as reviewer_name, t.name as tool_name, t.slug as tool_slug
           FROM reviews r JOIN users u ON r.user_id = u.id JOIN tools t ON r.tool_id = t.id
           ORDER BY r.created_at DESC"""
    )
    return await cursor.fetchall()


async def delete_review(db: aiosqlite.Connection, review_id: int):
    await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    await db.commit()


# ── Advanced Search ──────────────────────────────────────────────────────

async def search_tools_advanced(db: aiosqlite.Connection, *, query: str = "",
                                 price_filter: str = "", sort: str = "relevance",
                                 verified_only: bool = False, category_id: Optional[int] = None,
                                 page: int = 1, per_page: int = 12):
    conditions = ["t.status = 'approved'"]
    params = []

    if price_filter == "free":
        conditions.append("t.price_pence IS NULL")
    elif price_filter == "paid":
        conditions.append("t.price_pence > 0")

    if verified_only:
        conditions.append("t.is_verified = 1")

    if category_id:
        conditions.append("EXISTS(SELECT 1 FROM tool_categories tc_f WHERE tc_f.tool_id = t.id AND tc_f.category_id = ?)")
        params.append(category_id)

    where = " AND ".join(conditions)

    # Sort
    order_by = {
        "upvotes": "t.upvote_count DESC, t.created_at DESC",
        "newest": "t.created_at DESC",
        "price_low": "COALESCE(t.price_pence, 0) ASC, t.created_at DESC",
        "price_high": "COALESCE(t.price_pence, 0) DESC, t.created_at DESC",
    }.get(sort, "t.upvote_count DESC, t.created_at DESC")

    pro_boost_expr = ("rank + (CASE WHEN EXISTS(SELECT 1 FROM subscriptions s2 "
                      "JOIN users u2 ON u2.id = s2.user_id "
                      "WHERE u2.maker_id = t.maker_id AND s2.status = 'active') "
                      "THEN -0.1 ELSE 0 END)")

    if query.strip():
        safe_q = sanitize_fts(query)
        if not safe_q:
            return [], 0
        # Use FTS
        relevance_order = pro_boost_expr if sort == "relevance" else order_by
        sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug, bm25(tools_fts) as rank,
                         CASE WHEN EXISTS(
                             SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                             WHERE u.maker_id = t.maker_id AND s.status = 'active'
                         ) THEN 1 ELSE 0 END AS maker_is_pro
                  FROM tools_fts fts
                  JOIN tools t ON t.id = fts.rowid
                  JOIN categories c ON t.category_id = c.id
                  WHERE tools_fts MATCH ? AND {where}
                  ORDER BY {relevance_order}
                  LIMIT ? OFFSET ?"""
        fts_params = [safe_q] + params + [per_page, (page - 1) * per_page]
        cursor = await db.execute(sql, fts_params)
        rows = await cursor.fetchall()

        count_sql = f"""SELECT COUNT(*) as cnt
                        FROM tools_fts fts
                        JOIN tools t ON t.id = fts.rowid
                        WHERE tools_fts MATCH ? AND {where}"""
        count_cursor = await db.execute(count_sql, [safe_q] + params)
        total = (await count_cursor.fetchone())['cnt']

        # Fallback: if FTS found nothing, search the 'replaces' field
        # This catches searches for big-name tools (e.g. "Vercel", "Auth0")
        if total == 0 and page == 1:
            raw_q = query.strip()
            like_q = f"%{raw_q}%"
            fallback_order = "t.upvote_count DESC, t.created_at DESC"
            fallback_sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug,
                                     CASE WHEN EXISTS(
                                         SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                                         WHERE u.maker_id = t.maker_id AND s.status = 'active'
                                     ) THEN 1 ELSE 0 END AS maker_is_pro
                      FROM tools t
                      JOIN categories c ON t.category_id = c.id
                      WHERE LOWER(t.replaces) LIKE LOWER(?) AND {where}
                      ORDER BY {fallback_order}
                      LIMIT ? OFFSET ?"""
            fallback_params = [like_q] + params + [per_page, 0]
            cursor = await db.execute(fallback_sql, fallback_params)
            rows = await cursor.fetchall()

            fallback_count_sql = f"""SELECT COUNT(*) as cnt FROM tools t
                            WHERE LOWER(t.replaces) LIKE LOWER(?) AND {where}"""
            count_cursor = await db.execute(fallback_count_sql, [like_q] + params)
            total = (await count_cursor.fetchone())['cnt']
    else:
        sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug,
                         CASE WHEN EXISTS(
                             SELECT 1 FROM subscriptions s JOIN users u ON u.id = s.user_id
                             WHERE u.maker_id = t.maker_id AND s.status = 'active'
                         ) THEN 1 ELSE 0 END AS maker_is_pro
                  FROM tools t JOIN categories c ON t.category_id = c.id
                  WHERE {where}
                  ORDER BY {order_by}
                  LIMIT ? OFFSET ?"""
        cursor = await db.execute(sql, params + [per_page, (page - 1) * per_page])
        rows = await cursor.fetchall()

        count_sql = f"""SELECT COUNT(*) as cnt FROM tools t WHERE {where}"""
        # Need to rebuild conditions without aliases for count
        count_cursor = await db.execute(count_sql, params)
        total = (await count_cursor.fetchone())['cnt']

    return rows, total


# ── Maker Dashboard Queries ──────────────────────────────────────────────

async def get_tools_by_maker(db: aiosqlite.Connection, maker_id: int):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.maker_id = ?
           ORDER BY t.created_at DESC""",
        (maker_id,),
    )
    return await cursor.fetchall()


async def get_similar_makers(db: aiosqlite.Connection, maker_id: int, limit: int = 3) -> list:
    """Find makers with tools that share tags with this maker's tools."""
    cursor = await db.execute(
        "SELECT tags FROM tools WHERE maker_id = ? AND status = 'approved'", (maker_id,))
    rows = await cursor.fetchall()

    all_tags = set()
    for row in rows:
        tags_str = row['tags'] or ''
        for tag in tags_str.split(','):
            tag = tag.strip().lower()
            if tag:
                all_tags.add(tag)

    if not all_tags:
        return []

    # Find other makers whose tools share tags
    conditions = ' OR '.join(['t.tags LIKE ?' for _ in all_tags])
    params = [f'%{tag}%' for tag in all_tags]
    params.append(maker_id)

    cursor = await db.execute(f"""
        SELECT DISTINCT m.id, m.name, m.slug, m.bio, m.indie_status,
               t.name as tool_name, t.slug as tool_slug,
               COUNT(DISTINCT t.id) as tool_count
        FROM makers m
        JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        WHERE ({conditions}) AND m.id != ?
        GROUP BY m.id
        ORDER BY tool_count DESC
        LIMIT ?
    """, params + [limit])
    return [dict(row) for row in await cursor.fetchall()]


async def get_sales_by_maker(db: aiosqlite.Connection, maker_id: int):
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           WHERE t.maker_id = ?
           ORDER BY p.created_at DESC""",
        (maker_id,),
    )
    return await cursor.fetchall()


async def get_maker_revenue(db: aiosqlite.Connection, maker_id: int) -> dict:
    cursor = await db.execute(
        """SELECT COUNT(*) as sale_count,
                  COALESCE(SUM(p.amount_pence), 0) as total_revenue,
                  COALESCE(SUM(p.commission_pence), 0) as total_commission
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           WHERE t.maker_id = ?""",
        (maker_id,),
    )
    return await cursor.fetchone()


_ALLOWED_TOOL_FIELDS = {
    'name', 'tagline', 'description', 'url', 'tags', 'category_id', 'price_pence',
    'delivery_url', 'delivery_type', 'integration_python', 'integration_curl',
    'replaces', 'status', 'is_verified', 'is_ejectable', 'maker_id', 'maker_name',
    'stripe_account_id', 'tool_of_the_week', 'boost_active', 'boost_expires_at',
    'badge_nudge_sent', 'indie_score', 'mcp_view_count', 'pixel_icon',
    'api_type', 'auth_method', 'install_command', 'sdk_packages', 'env_vars', 'frameworks_tested',
    'verified_pairs', 'agent_instructions',
}

async def update_tool(db: aiosqlite.Connection, tool_id: int, **fields):
    fields = {k: v for k, v in fields.items() if k in _ALLOWED_TOOL_FIELDS}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [tool_id]
    await db.execute(f"UPDATE tools SET {set_clause} WHERE id = ?", values)
    await db.commit()


# ── Tool Pairs (Agentic Package Manager) ─────────────────────────────────

async def get_verified_pairs(db: aiosqlite.Connection, slug: str, limit: int = 50) -> list:
    """Get tools verified to work well with this tool."""
    cursor = await db.execute("""
        SELECT CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END as pair_slug,
               tp.success_count, tp.verified,
               t.url as pair_url
        FROM tool_pairs tp
        LEFT JOIN tools t ON t.slug = CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END
        WHERE (tp.tool_a_slug = ? OR tp.tool_b_slug = ?)
        ORDER BY tp.success_count DESC
        LIMIT ?
    """, (slug, slug, slug, slug, limit))
    return [dict(r) for r in await cursor.fetchall()]


async def record_tool_pair(db: aiosqlite.Connection, slug_a: str, slug_b: str, source: str = "agent"):
    """Record that two tools were used together. Increments success_count if exists."""
    a, b = sorted([slug_a, slug_b])
    await db.execute("""
        INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source)
        VALUES (?, ?, ?)
        ON CONFLICT(tool_a_slug, tool_b_slug) DO UPDATE SET success_count = success_count + 1
    """, (a, b, source))
    await db.commit()


async def record_verified_stack(db: aiosqlite.Connection, tool_slugs: list[str], use_case: str = None, source: str = "agent"):
    """Record a verified stack (set of tools used together successfully)."""
    if not tool_slugs or len(tool_slugs) < 2:
        return
    import json
    sorted_slugs = json.dumps(sorted(tool_slugs))
    await db.execute(
        """INSERT INTO verified_stacks (tool_slugs, use_case, source)
           VALUES (?, ?, ?)
           ON CONFLICT(tool_slugs) DO UPDATE SET success_count = success_count + 1""",
        (sorted_slugs, use_case, source),
    )
    await db.commit()


async def record_tool_conflict(db: aiosqlite.Connection, slug_a: str, slug_b: str, reason: str = None):
    """Record an incompatibility between two tools."""
    if not slug_a or not slug_b or slug_a == slug_b:
        return
    a, b = sorted([slug_a, slug_b])
    await db.execute(
        """INSERT INTO tool_conflicts (tool_a_slug, tool_b_slug, reason)
           VALUES (?, ?, ?)
           ON CONFLICT(tool_a_slug, tool_b_slug) DO UPDATE SET report_count = report_count + 1,
           reason = COALESCE(NULLIF(excluded.reason, ''), tool_conflicts.reason)""",
        (a, b, reason),
    )
    await db.commit()


async def get_tool_conflicts(db: aiosqlite.Connection, slug: str, limit: int = 20) -> list:
    """Get known conflicts for a tool."""
    if not slug:
        return []
    cursor = await db.execute("""
        SELECT CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END as conflict_slug,
               reason, report_count
        FROM tool_conflicts
        WHERE tool_a_slug = ? OR tool_b_slug = ?
        ORDER BY report_count DESC
        LIMIT ?
    """, (slug, slug, slug, limit))
    return [dict(r) for r in await cursor.fetchall()]


async def get_compatible_tools_grouped(db: aiosqlite.Connection, slug: str, category_slug: str = "", min_success_count: int = 1, limit: int = 100) -> dict:
    """Get tools compatible with the given slug, grouped by category, with metadata."""
    cat_filter = ""
    cat_params = []
    if category_slug:
        cat_filter = " AND c.slug = ?"
        cat_params = [category_slug]

    cursor = await db.execute(f"""
        SELECT
            CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END as pair_slug,
            tp.success_count,
            t.name, t.tagline, t.url, t.health_status, t.github_stars,
            c.name as category_name, c.slug as category_slug
        FROM tool_pairs tp
        JOIN tools t ON t.slug = CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END
        JOIN categories c ON t.category_id = c.id
        WHERE (tp.tool_a_slug = ? OR tp.tool_b_slug = ?)
          AND tp.success_count >= ?
          AND t.status = 'approved'
          {cat_filter}
        ORDER BY tp.success_count DESC
        LIMIT ?
    """, (slug, slug, slug, slug, min_success_count, *cat_params, limit))
    rows = [dict(r) for r in await cursor.fetchall()]

    grouped = {}
    for r in rows:
        cat = r['category_name']
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(r)

    return {"pairs": rows, "grouped": grouped, "total": len(rows)}


async def find_stack_triangles(db: aiosqlite.Connection, slug: str, min_success: int = 1) -> list:
    """Find triangles in the compatibility graph — 3 tools all mutually compatible.

    Limits to top 15 partners and uses a batch query to check mutual pairs
    instead of O(n^2) individual queries.
    """
    cursor = await db.execute("""
        SELECT CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END as partner
        FROM tool_pairs
        WHERE (tool_a_slug = ? OR tool_b_slug = ?) AND success_count >= ?
        ORDER BY success_count DESC LIMIT 15
    """, (slug, slug, slug, min_success))
    partners = [r['partner'] for r in await cursor.fetchall()]

    if len(partners) < 2:
        return []

    # Batch-fetch all mutual pairs among the partners in one query
    placeholders = ",".join("?" for _ in partners)
    mutual_cursor = await db.execute(f"""
        SELECT tool_a_slug, tool_b_slug, success_count
        FROM tool_pairs
        WHERE tool_a_slug IN ({placeholders})
          AND tool_b_slug IN ({placeholders})
          AND success_count >= ?
    """, (*partners, *partners, min_success))
    mutual_set = {}
    for r in await mutual_cursor.fetchall():
        mutual_set[(r['tool_a_slug'], r['tool_b_slug'])] = r['success_count']

    triangles = []
    for i, p1 in enumerate(partners):
        for p2 in partners[i + 1:]:
            a, b = sorted([p1, p2])
            sc = mutual_set.get((a, b))
            if sc is not None:
                triangles.append({
                    "tools": sorted([slug, p1, p2]),
                    "mutual_success": sc,
                })
                if len(triangles) >= 5:
                    return triangles
    return triangles


# ── Tool Views (Analytics) ───────────────────────────────────────────────

async def record_tool_view(db: aiosqlite.Connection, tool_id: int, ip: str):
    ip_h = hash_ip(ip)
    await db.execute(
        "INSERT INTO tool_views (tool_id, ip_hash) VALUES (?, ?)",
        (tool_id, ip_h),
    )
    await db.commit()


async def record_outbound_click(db: aiosqlite.Connection, tool_id: int, url: str, ip: str, referrer: str = ''):
    """Record an outbound click from a tool listing to the tool's website."""
    ip_h = hash_ip(ip)
    await db.execute(
        "INSERT INTO outbound_clicks (tool_id, url, ip_hash, referrer) VALUES (?, ?, ?, ?)",
        (tool_id, url, ip_h, referrer),
    )
    await db.commit()


async def get_outbound_click_count(db: aiosqlite.Connection, tool_id: int, days: int = 30) -> int:
    """Get outbound click count for a tool over the last N days."""
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM outbound_clicks WHERE tool_id = ? AND created_at > datetime('now', ?)",
        (tool_id, f'-{days} days'),
    )
    row = await cursor.fetchone()
    return int(row['cnt']) if row else 0


async def get_outbound_clicks_by_tool(db: aiosqlite.Connection, tool_id: int, days: int = 30) -> list:
    """Get outbound clicks grouped by day for a tool."""
    cursor = await db.execute(
        """SELECT date(created_at) as day, COUNT(*) as clicks
           FROM outbound_clicks
           WHERE tool_id = ? AND created_at > datetime('now', ?)
           GROUP BY date(created_at)
           ORDER BY day DESC""",
        (tool_id, f'-{days} days'),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_tool_view_count(db: aiosqlite.Connection, tool_id: int, days: int = 30) -> int:
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM tool_views
           WHERE tool_id = ? AND viewed_at >= datetime('now', ?)""",
        (tool_id, f'-{days} days'),
    )
    return (await cursor.fetchone())['cnt']


async def get_tool_views_by_maker(db: aiosqlite.Connection, maker_id: int, days: int = 30):
    cursor = await db.execute(
        """SELECT t.id, t.name, t.slug, COUNT(tv.id) as view_count
           FROM tools t
           LEFT JOIN tool_views tv ON tv.tool_id = t.id AND tv.viewed_at >= datetime('now', ?)
           WHERE t.maker_id = ?
           GROUP BY t.id
           ORDER BY view_count DESC""",
        (f'-{days} days', maker_id),
    )
    return await cursor.fetchall()


# ── Subscriptions ────────────────────────────────────────────────────────

async def create_subscription(db: aiosqlite.Connection, *, user_id: int,
                               stripe_subscription_id: str, plan: str = 'pro',
                               current_period_end: str = '') -> int:
    cursor = await db.execute(
        """INSERT INTO subscriptions (user_id, stripe_subscription_id, plan, current_period_end)
           VALUES (?, ?, ?, ?)""",
        (user_id, stripe_subscription_id, plan, current_period_end),
    )
    await db.commit()
    return cursor.lastrowid


async def get_active_subscription(db: aiosqlite.Connection, user_id: int):
    cursor = await db.execute(
        """SELECT * FROM subscriptions
           WHERE user_id = ? AND status = 'active'
           ORDER BY created_at DESC LIMIT 1""",
        (user_id,),
    )
    return await cursor.fetchone()


async def update_subscription_status(db: aiosqlite.Connection, stripe_subscription_id: str, status: str):
    await db.execute(
        "UPDATE subscriptions SET status = ? WHERE stripe_subscription_id = ?",
        (status, stripe_subscription_id),
    )
    await db.commit()


async def check_pro(db, user_id: int) -> bool:
    """Check if a user has an active Pro subscription (any plan) or active trial."""
    if not user_id:
        return False
    sub = await get_active_subscription(db, user_id)
    if sub is not None:
        return True
    # Check for active free trial
    cursor = await db.execute(
        "SELECT trial_ends_at FROM users WHERE id = ? AND trial_ends_at > datetime('now')",
        (user_id,),
    )
    trial = await cursor.fetchone()
    return trial is not None


async def get_founder_seat_count(db) -> int:
    """Count how many founder subscriptions have been sold."""
    cursor = await db.execute(
        "SELECT COUNT(*) AS cnt FROM subscriptions WHERE plan = 'founder' AND status = 'active'"
    )
    row = await cursor.fetchone()
    return row['cnt'] if row else 0


# ── Maker by ID ──────────────────────────────────────────────────────────

async def get_maker_by_id(db: aiosqlite.Connection, maker_id: int):
    cursor = await db.execute("SELECT * FROM makers WHERE id = ?", (maker_id,))
    return await cursor.fetchone()


_ALLOWED_MAKER_FIELDS = {'name', 'bio', 'avatar_url', 'url', 'stripe_account_id', 'indie_status', 'twitter_handle', 'github_handle', 'story_motivation', 'story_challenge', 'story_advice', 'story_fun_fact'}

async def update_maker(db: aiosqlite.Connection, maker_id: int, **fields):
    fields = {k: v for k, v in fields.items() if k in _ALLOWED_MAKER_FIELDS}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [maker_id]
    await db.execute(f"UPDATE makers SET {set_clause} WHERE id = ?", values)
    await db.commit()


async def update_maker_stripe_account(db: aiosqlite.Connection, maker_id: int, stripe_account_id: str):
    """Save Stripe Connect account ID to maker record."""
    await db.execute("UPDATE makers SET stripe_account_id = ? WHERE id = ?", (stripe_account_id, maker_id))
    await db.commit()


# ── Recently Added ───────────────────────────────────────────────────────

async def get_recent_tools_paginated(db: aiosqlite.Connection, page: int = 1, per_page: int = 12):
    offset = (page - 1) * per_page
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY t.created_at DESC LIMIT ? OFFSET ?""",
        (per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'"
    )
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


# ── Maker Search & Directory ─────────────────────────────────────────────

async def search_makers(db: aiosqlite.Connection, query: str, limit: int = 20):
    safe_q = sanitize_fts(query)
    if not safe_q:
        return []
    cursor = await db.execute(
        """SELECT m.*, bm25(makers_fts) as rank
           FROM makers_fts fts
           JOIN makers m ON m.id = fts.rowid
           WHERE makers_fts MATCH ?
           ORDER BY rank LIMIT ?""",
        (safe_q, limit),
    )
    return await cursor.fetchall()


async def get_all_makers_paginated(db: aiosqlite.Connection, page: int = 1, per_page: int = 12,
                                    sort: str = "most_tools"):
    offset = (page - 1) * per_page
    order_by = {
        "most_tools": "tool_count DESC, m.created_at DESC",
        "most_upvoted": "total_upvotes DESC, m.created_at DESC",
        "newest": "m.created_at DESC",
    }.get(sort, "tool_count DESC, m.created_at DESC")

    cursor = await db.execute(
        f"""SELECT m.*,
                   COUNT(t.id) as tool_count,
                   COALESCE(SUM(t.upvote_count), 0) as total_upvotes
            FROM makers m
            LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
            WHERE m.slug != 'community'
            GROUP BY m.id
            ORDER BY {order_by}
            LIMIT ? OFFSET ?""",
        (per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute("SELECT COUNT(*) as cnt FROM makers WHERE slug != 'community'")
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


# ── Wishlists ────────────────────────────────────────────────────────────

async def toggle_wishlist(db: aiosqlite.Connection, user_id: int, tool_id: int) -> tuple[bool, int]:
    """Toggle wishlist. Returns (is_saved, total_saves_for_tool)."""
    cursor = await db.execute(
        "SELECT id FROM wishlists WHERE user_id = ? AND tool_id = ?", (user_id, tool_id)
    )
    existing = await cursor.fetchone()
    if existing:
        await db.execute("DELETE FROM wishlists WHERE id = ?", (existing['id'],))
        is_saved = False
    else:
        await db.execute("INSERT INTO wishlists (user_id, tool_id) VALUES (?, ?)", (user_id, tool_id))
        is_saved = True
    await db.commit()
    count_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM wishlists WHERE tool_id = ?", (tool_id,)
    )
    count = (await count_cursor.fetchone())['cnt']
    return is_saved, count


async def is_wishlisted(db: aiosqlite.Connection, user_id: int, tool_id: int) -> bool:
    cursor = await db.execute(
        "SELECT id FROM wishlists WHERE user_id = ? AND tool_id = ?", (user_id, tool_id)
    )
    return await cursor.fetchone() is not None


async def get_user_wishlist(db: aiosqlite.Connection, user_id: int, page: int = 1, per_page: int = 12):
    offset = (page - 1) * per_page
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug, w.created_at as saved_at
           FROM wishlists w
           JOIN tools t ON w.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE w.user_id = ? AND t.status = 'approved'
           ORDER BY w.created_at DESC LIMIT ? OFFSET ?""",
        (user_id, per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM wishlists w JOIN tools t ON w.tool_id = t.id WHERE w.user_id = ? AND t.status = 'approved'",
        (user_id,),
    )
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


# ── Maker Updates ────────────────────────────────────────────────────────

async def create_maker_update(db: aiosqlite.Connection, maker_id: int, title: str,
                               body: str, update_type: str = 'update',
                               tool_id: int = None) -> int:
    if update_type not in ('update', 'launch', 'milestone', 'changelog'):
        update_type = 'update'
    cursor = await db.execute(
        "INSERT INTO maker_updates (maker_id, title, body, update_type, tool_id) VALUES (?, ?, ?, ?, ?)",
        (maker_id, title.strip(), body.strip(), update_type, tool_id),
    )
    await db.commit()
    return cursor.lastrowid


async def get_recent_updates(db: aiosqlite.Connection, limit: int = 20):
    cursor = await db.execute(
        """SELECT mu.*, m.name as maker_name, m.slug as maker_slug
           FROM maker_updates mu
           JOIN makers m ON mu.maker_id = m.id
           ORDER BY mu.created_at DESC LIMIT ?""",
        (limit,),
    )
    return await cursor.fetchall()


async def get_tool_changelogs(db, tool_id: int, limit: int = 20) -> list:
    cursor = await db.execute(
        """SELECT mu.*, m.name AS maker_name, m.slug AS maker_slug
           FROM maker_updates mu
           JOIN makers m ON mu.maker_id = m.id
           WHERE mu.tool_id = ?
           ORDER BY mu.created_at DESC LIMIT ?""",
        (tool_id, limit)
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_updates_by_maker(db: aiosqlite.Connection, maker_id: int, limit: int = 10):
    cursor = await db.execute(
        """SELECT * FROM maker_updates
           WHERE maker_id = ?
           ORDER BY created_at DESC LIMIT ?""",
        (maker_id, limit),
    )
    return await cursor.fetchall()


# ── All Makers (admin) ──────────────────────────────────────────────────

async def get_all_makers_admin(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT m.*, COUNT(t.id) as tool_count
           FROM makers m
           LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
           GROUP BY m.id ORDER BY m.created_at DESC"""
    )
    return await cursor.fetchall()


# ── Notifications ────────────────────────────────────────────────────────

async def create_notification(db: aiosqlite.Connection, user_id: int, type: str,
                               message: str, link: str = '') -> int:
    cursor = await db.execute(
        "INSERT INTO notifications (user_id, type, message, link) VALUES (?, ?, ?, ?)",
        (user_id, type, message, link),
    )
    await db.commit()
    return cursor.lastrowid


async def get_unread_count(db: aiosqlite.Connection, user_id: int) -> int:
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,),
    )
    return (await cursor.fetchone())['cnt']


async def get_notifications(db: aiosqlite.Connection, user_id: int, limit: int = 20):
    cursor = await db.execute(
        """SELECT * FROM notifications
           WHERE user_id = ?
           ORDER BY is_read ASC, created_at DESC LIMIT ?""",
        (user_id, limit),
    )
    return await cursor.fetchall()


async def mark_notifications_read(db: aiosqlite.Connection, user_id: int):
    await db.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
        (user_id,),
    )
    await db.commit()


async def mark_notification_read(db: aiosqlite.Connection, notification_id: int):
    await db.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ?",
        (notification_id,),
    )
    await db.commit()


# ── Page Views (Site Analytics) ──────────────────────────────────────────

async def track_pageview(db, page: str, visitor_id: str, referrer: str = ""):
    from datetime import datetime
    await db.execute(
        "INSERT INTO page_views (timestamp, page, visitor_id, referrer) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), page, visitor_id, referrer)
    )
    await db.commit()


async def cleanup_old_page_views(db, days: int = 90):
    """Delete page views older than N days to prevent table bloat. Keeps aggregate counts accurate via tool view_count."""
    await db.execute(
        "DELETE FROM page_views WHERE timestamp < datetime('now', ?)",
        (f'-{days} days',))
    await db.commit()


# ── Password Reset & Email Verification ─────────────────────────────────

async def create_password_reset_token(db, user_id: int) -> str:
    """Generate a password reset token with 1-hour expiry."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    await db.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at.isoformat())
    )
    await db.commit()
    return token


async def get_valid_reset_token(db, token: str):
    """Return user_id if token is valid and unused, else None."""
    cursor = await db.execute(
        "SELECT user_id, expires_at, used FROM password_reset_tokens WHERE token = ?",
        (token,)
    )
    row = await cursor.fetchone()
    if not row:
        return None
    if row['used']:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        return None
    return row['user_id']


async def mark_reset_token_used(db, token: str):
    """Mark a reset token as used."""
    await db.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,))
    await db.commit()


async def create_email_verification_token(db, user_id: int) -> str:
    """Generate an email verification token with 24-hour expiry."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    await db.execute(
        "INSERT INTO email_verification_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at.isoformat())
    )
    await db.commit()
    return token


async def verify_email_token(db, token: str):
    """Verify email token: mark user as verified, return user_id or None.

    Note: token is NOT deleted after use — it expires naturally after 24h.
    This prevents email client link prefetching from consuming the token
    before the user actually clicks.
    """
    cursor = await db.execute(
        "SELECT user_id, expires_at FROM email_verification_tokens WHERE token = ?",
        (token,)
    )
    row = await cursor.fetchone()
    if not row:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        # Expired — clean it up
        await db.execute("DELETE FROM email_verification_tokens WHERE token = ?", (token,))
        await db.commit()
        return None
    # Mark user as verified (idempotent — safe to call multiple times)
    await db.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (row['user_id'],))
    await db.commit()
    # Generate referral code on verification
    await ensure_referral_code(db, row['user_id'])
    return row['user_id']


# ── Magic Link Auth ──────────────────────────────────────────────────────

async def create_magic_link_token(db, email: str) -> str:
    """Create a magic link token. Returns the token string. 15 minute expiry."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
    await db.execute(
        "INSERT INTO magic_link_tokens (email, token, expires_at) VALUES (?, ?, ?)",
        (email.lower().strip(), token, expires)
    )
    await db.commit()
    return token


async def validate_magic_link_token(db, token: str):
    """Validate and consume a magic link token atomically. Returns email or None."""
    # Atomically mark as used and return email in one step to prevent race conditions
    cursor = await db.execute(
        "UPDATE magic_link_tokens SET used = 1 "
        "WHERE token = ? AND used = 0 AND expires_at > datetime('now') "
        "RETURNING email",
        (token,)
    )
    row = await cursor.fetchone()
    if not row:
        return None
    await db.commit()
    return row[0]


# ── Tokens Saved ─────────────────────────────────────────────────────────

async def get_platform_tokens_saved(db: aiosqlite.Connection) -> int:
    """Calculate total tokens saved across all purchases."""
    cursor = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           GROUP BY c.slug"""
    )
    rows = await cursor.fetchall()
    total = 0
    for row in rows:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    return total


async def get_user_tokens_saved(db: aiosqlite.Connection, user_id: int) -> int:
    """Calculate tokens saved for a specific user (purchases + wishlist)."""
    # Purchases
    cursor = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE p.buyer_email = (SELECT email FROM users WHERE id = ?)
           GROUP BY c.slug""",
        (user_id,),
    )
    rows = await cursor.fetchall()
    total = 0
    for row in rows:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    # Wishlist
    cursor2 = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM wishlists w
           JOIN tools t ON w.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE w.user_id = ?
           GROUP BY c.slug""",
        (user_id,),
    )
    rows2 = await cursor2.fetchall()
    for row in rows2:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    return total


# ── Maker Pulse (Last Activity) ──────────────────────────────────────────

async def get_tool_last_activity(db: aiosqlite.Connection, tool_id: int) -> str:
    """Get the most recent activity date for a tool (changelog or tool update)."""
    cursor = await db.execute(
        """SELECT MAX(dt) as last_active FROM (
            SELECT created_at as dt FROM maker_updates WHERE tool_id = ?
            UNION ALL
            SELECT created_at as dt FROM tools WHERE id = ?
        )""",
        (tool_id, tool_id),
    )
    row = await cursor.fetchone()
    return row['last_active'] if row and row['last_active'] else ''


async def get_tools_replacing(db: aiosqlite.Connection, competitor: str, limit: int = 20):
    """Get all approved tools that replace a given competitor."""
    # Search in the replaces field (comma-separated list)
    like_pattern = f'%{competitor}%'
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved' AND LOWER(t.replaces) LIKE LOWER(?)
           ORDER BY (CASE WHEN t.boosted_competitor != '' THEN 0 ELSE 1 END), t.upvote_count DESC LIMIT ?""",
        (like_pattern, limit),
    )
    return await cursor.fetchall()


async def get_all_competitors(db: aiosqlite.Connection):
    """Get a list of all unique competitors mentioned in tool replaces fields."""
    cursor = await db.execute(
        "SELECT DISTINCT replaces FROM tools WHERE status = 'approved' AND replaces != ''"
    )
    rows = await cursor.fetchall()
    competitors = set()
    for row in rows:
        for comp in row['replaces'].split(','):
            comp = comp.strip()
            if comp:
                competitors.add(comp)
    return sorted(competitors, key=str.lower)


async def get_competitor_stats(db: aiosqlite.Connection) -> list:
    """Get competitors with tool counts for the alternatives index page."""
    cursor = await db.execute(
        "SELECT replaces FROM tools WHERE status = 'approved' AND replaces != ''"
    )
    rows = await cursor.fetchall()
    counts: dict[str, int] = {}
    for row in rows:
        for comp in row['replaces'].split(','):
            comp = comp.strip()
            if comp:
                counts[comp] = counts.get(comp, 0) + 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0].lower()))


async def toggle_tool_boost(db: aiosqlite.Connection, tool_id: int, competitor: str = ''):
    """Toggle a tool's boosted status for a specific competitor alternatives page."""
    cursor = await db.execute("SELECT boosted_competitor FROM tools WHERE id = ?", (tool_id,))
    row = await cursor.fetchone()
    if not row:
        return
    current = row[0] or ''
    if current == competitor and competitor:
        # Un-boost
        await db.execute("UPDATE tools SET boosted_competitor = '' WHERE id = ?", (tool_id,))
    else:
        # Set boost
        await db.execute("UPDATE tools SET boosted_competitor = ? WHERE id = ?", (competitor, tool_id))
    await db.commit()


async def activate_boost(db, tool_id: int, days: int = 30):
    """Activate or extend a platform boost for a tool."""
    # Check if tool already has an active boost
    cursor = await db.execute(
        "SELECT boost_expires_at FROM tools WHERE id = ?", (tool_id,))
    row = await cursor.fetchone()
    now = datetime.utcnow()
    if row and row['boost_expires_at']:
        try:
            existing_expiry = datetime.fromisoformat(row['boost_expires_at'])
            if existing_expiry > now:
                # Extend existing boost
                expires_at = (existing_expiry + timedelta(days=days)).isoformat()
                await db.execute(
                    "UPDATE tools SET is_boosted = 1, boost_expires_at = ? WHERE id = ?",
                    (expires_at, tool_id))
                await db.commit()
                return
        except Exception:
            pass
    # New boost
    expires_at = (now + timedelta(days=days)).isoformat()
    await db.execute(
        "UPDATE tools SET is_boosted = 1, boost_expires_at = ? WHERE id = ?",
        (expires_at, tool_id))
    await db.commit()

async def get_active_boosts(db):
    """Get all tools with active (unexpired) platform boosts."""
    now = datetime.utcnow().isoformat()
    cursor = await db.execute(
        "SELECT * FROM tools WHERE is_boosted = 1 AND boost_expires_at > ? AND status = 'approved'",
        (now,))
    return await cursor.fetchall()


# ── Sponsored placements (B2B) ─────────────────────────────────────────

async def get_sponsored_for_competitor(db, competitor_slug: str) -> list:
    """Get active sponsored placements for a competitor's alternatives page."""
    cursor = await db.execute("""
        SELECT sp.*, t.name, t.slug, t.tagline, t.url, t.upvote_count, t.is_verified,
               t.price_pence, t.tags
        FROM sponsored_placements sp
        JOIN tools t ON sp.tool_id = t.id
        WHERE sp.competitor_slug = ? AND sp.is_active = 1
        AND (sp.expires_at IS NULL OR sp.expires_at > datetime('now'))
        ORDER BY sp.id
    """, (competitor_slug,))
    return [dict(row) for row in await cursor.fetchall()]


async def create_sponsored_placement(db, tool_id: int, competitor_slug: str, label: str = 'Sponsored', days: int = 30):
    """Create a sponsored placement."""
    expires = (datetime.utcnow() + timedelta(days=days)).isoformat() if days else None
    await db.execute(
        "INSERT INTO sponsored_placements (tool_id, competitor_slug, label, expires_at) VALUES (?, ?, ?, ?)",
        (tool_id, competitor_slug, label, expires))
    await db.commit()


async def delete_sponsored_placement(db, placement_id: int):
    """Delete a sponsored placement."""
    await db.execute("DELETE FROM sponsored_placements WHERE id = ?", (placement_id,))
    await db.commit()


async def get_all_sponsored_placements(db) -> list:
    """Get all sponsored placements for admin."""
    cursor = await db.execute("""
        SELECT sp.*, t.name as tool_name, t.slug as tool_slug
        FROM sponsored_placements sp
        JOIN tools t ON sp.tool_id = t.id
        ORDER BY sp.is_active DESC, sp.started_at DESC
    """)
    return [dict(row) for row in await cursor.fetchall()]


# ── Stacks (Bundles) ────────────────────────────────────────────────────

async def create_stack(db, *, title: str, description: str = '', cover_emoji: str = '',
                       discount_percent: int = 15) -> int:
    """Create a new stack (bundle). Returns the stack id."""
    slug = slugify(title)
    base_slug = slug
    counter = 1
    while True:
        existing = await db.execute("SELECT id FROM stacks WHERE slug = ?", (slug,))
        if await existing.fetchone() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    cursor = await db.execute(
        "INSERT INTO stacks (slug, title, description, cover_emoji, discount_percent) VALUES (?, ?, ?, ?, ?)",
        (slug, title, description, cover_emoji, discount_percent),
    )
    await db.commit()
    return cursor.lastrowid


async def get_all_stacks(db):
    """Get all stacks with tool counts."""
    cursor = await db.execute(
        """SELECT s.*, COUNT(st.tool_id) as tool_count
           FROM stacks s LEFT JOIN stack_tools st ON st.stack_id = s.id
           GROUP BY s.id ORDER BY s.created_at DESC""")
    return await cursor.fetchall()


async def get_stacks_by_source(db, source: str):
    """Get stacks filtered by source, with tool counts, ordered by confidence."""
    cursor = await db.execute(
        """SELECT s.*, COUNT(st.tool_id) as tool_count
           FROM stacks s LEFT JOIN stack_tools st ON st.stack_id = s.id
           WHERE s.source = ?
           GROUP BY s.id ORDER BY s.confidence_score DESC""", (source,))
    return await cursor.fetchall()


async def get_stack_stats(db):
    """Get aggregate stats for the stacks page hero (single query)."""
    c = await db.execute("""
        SELECT
            (SELECT COUNT(*) FROM tool_pairs) as pair_count,
            (SELECT COUNT(*) FROM tools WHERE status='approved') as tool_count,
            (SELECT COUNT(*) FROM stacks WHERE source LIKE 'auto-%') as auto_stack_count,
            (SELECT COUNT(DISTINCT framework) FROM stacks WHERE framework IS NOT NULL) as framework_count
    """)
    return await c.fetchone()


async def get_stack_by_slug(db, slug: str):
    """Get a stack by its slug."""
    cursor = await db.execute("SELECT * FROM stacks WHERE slug = ?", (slug,))
    return await cursor.fetchone()


async def get_stack_by_id(db, stack_id: int):
    """Get a stack by its id."""
    cursor = await db.execute("SELECT * FROM stacks WHERE id = ?", (stack_id,))
    return await cursor.fetchone()


async def get_stack_with_tools(db, slug: str):
    """Get a stack and its tools in order. Returns (stack, tools)."""
    stack = await get_stack_by_slug(db, slug)
    if not stack:
        return None, []
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  m.name as maker_name, m.slug as maker_slug
           FROM stack_tools st
           JOIN tools t ON st.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           LEFT JOIN makers m ON t.maker_id = m.id
           WHERE st.stack_id = ? AND t.status = 'approved'
           ORDER BY st.position ASC""",
        (stack['id'],))
    tools = await cursor.fetchall()
    return stack, tools


async def add_tool_to_stack(db, stack_id: int, tool_id: int, position: int = 0):
    """Add a tool to a stack."""
    try:
        await db.execute("INSERT INTO stack_tools (stack_id, tool_id, position) VALUES (?, ?, ?)",
                         (stack_id, tool_id, position))
        await db.commit()
    except Exception:
        pass


async def remove_tool_from_stack(db, stack_id: int, tool_id: int):
    """Remove a tool from a stack."""
    await db.execute("DELETE FROM stack_tools WHERE stack_id = ? AND tool_id = ?", (stack_id, tool_id))
    await db.commit()


async def delete_stack(db, stack_id: int):
    """Delete a stack and its associated data."""
    await db.execute("DELETE FROM stack_tools WHERE stack_id = ?", (stack_id,))
    await db.execute("DELETE FROM stack_purchases WHERE stack_id = ?", (stack_id,))
    await db.execute("DELETE FROM stacks WHERE id = ?", (stack_id,))
    await db.commit()


# ── Stack Purchases ─────────────────────────────────────────────────────

async def create_stack_purchase(db, *, stack_id: int, buyer_email: str,
                                stripe_session_id: str, total_amount_pence: int,
                                discount_pence: int = 0) -> str:
    """Create a stack purchase record. Returns the unique purchase_token."""
    token = secrets.token_urlsafe(32)
    await db.execute(
        """INSERT INTO stack_purchases (stack_id, buyer_email, stripe_session_id,
           total_amount_pence, discount_pence, purchase_token)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (stack_id, buyer_email, stripe_session_id, total_amount_pence, discount_pence, token))
    await db.commit()
    return token


async def get_stack_purchase_by_session(db, session_id: str):
    """Get a stack purchase by Stripe session ID."""
    cursor = await db.execute(
        """SELECT sp.*, s.title as stack_title, s.slug as stack_slug
           FROM stack_purchases sp JOIN stacks s ON sp.stack_id = s.id
           WHERE sp.stripe_session_id = ?""", (session_id,))
    return await cursor.fetchone()


async def get_stack_purchase_by_token(db, token: str):
    """Get a stack purchase by its purchase token."""
    cursor = await db.execute(
        """SELECT sp.*, s.title as stack_title, s.slug as stack_slug, s.cover_emoji
           FROM stack_purchases sp JOIN stacks s ON sp.stack_id = s.id
           WHERE sp.purchase_token = ?""", (token,))
    return await cursor.fetchone()


# ── Buyer Badges ────────────────────────────────────────────────────────

async def get_or_create_badge_token(db, user_id: int) -> str:
    """Get or create a badge token for a user."""
    cursor = await db.execute("SELECT badge_token FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    if row and row.get('badge_token'):
        return row['badge_token']
    token = secrets.token_urlsafe(16)
    await db.execute("UPDATE users SET badge_token = ? WHERE id = ?", (token, user_id))
    await db.commit()
    return token


async def get_user_by_badge_token(db, badge_token: str):
    """Get a user by their badge token."""
    cursor = await db.execute("SELECT id, name, email FROM users WHERE badge_token = ?", (badge_token,))
    return await cursor.fetchone()


async def get_buyer_tokens_saved_by_token(db, badge_token: str) -> int:
    """Calculate tokens saved for a buyer identified by badge token."""
    cursor = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE p.buyer_email = (SELECT email FROM users WHERE badge_token = ?)
           GROUP BY c.slug""", (badge_token,))
    rows = await cursor.fetchall()
    total = 0
    for row in rows:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    return total


# ── Discovery (Round 8) ─────────────────────────────────────────────────

async def get_all_tags_with_counts(db: aiosqlite.Connection, min_count: int = 1):
    """Get all unique tags across approved tools with their usage counts.
    Tags are stored as comma-separated strings in tools.tags.
    Returns list of dicts: [{'tag': 'api', 'slug': 'api', 'count': 5}, ...]
    """
    now = _time.time()
    cache_key = min_count
    if _tags_cache['data'] is not None and now < _tags_cache['expires'] and _tags_cache.get('min_count') == cache_key:
        return _tags_cache['data']
    cursor = await db.execute(
        "SELECT tags FROM tools WHERE status = 'approved' AND tags != ''"
    )
    rows = await cursor.fetchall()
    counts: dict[str, int] = {}
    for row in rows:
        for raw_tag in row['tags'].split(','):
            tag = raw_tag.strip()
            if tag:
                key = tag.lower()
                counts[key] = counts.get(key, 0) + 1
    results = [
        {'tag': tag, 'slug': slugify(tag), 'count': count}
        for tag, count in counts.items()
        if count >= min_count
    ]
    results.sort(key=lambda x: x['count'], reverse=True)
    _tags_cache['data'] = results
    _tags_cache['expires'] = now + 300  # 5 min TTL
    _tags_cache['min_count'] = cache_key
    return results


async def get_tools_by_tag(db: aiosqlite.Connection, tag: str, *, page: int = 1, per_page: int = 12):
    """Get approved tools that have a specific tag. Returns (tools, total).
    Uses LIKE matching on the comma-separated tags field.
    """
    offset = (page - 1) * per_page
    tag_lower = tag.strip().lower()
    # Match: entire field is the tag, starts with tag+comma, ends with comma+tag, or has comma+tag+comma
    like_exact = tag_lower
    like_start = f'{tag_lower},%'
    like_end = f'%,{tag_lower}'
    like_mid = f'%,{tag_lower},%'

    sql = """SELECT t.*, c.name as category_name, c.slug as category_slug
             FROM tools t JOIN categories c ON t.category_id = c.id
             WHERE t.status = 'approved'
               AND (LOWER(TRIM(t.tags)) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)
             ORDER BY t.quality_score DESC, t.github_stars DESC, t.upvote_count DESC
             LIMIT ? OFFSET ?"""
    cursor = await db.execute(sql, (like_exact, like_start, like_end, like_mid, per_page, offset))
    rows = await cursor.fetchall()

    count_sql = """SELECT COUNT(*) as cnt FROM tools t
                   WHERE t.status = 'approved'
                     AND (LOWER(TRIM(t.tags)) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)"""
    count_cursor = await db.execute(count_sql, (like_exact, like_start, like_end, like_mid))
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


async def explore_tools(db: aiosqlite.Connection, *, category_id: int = None,
                         tag: str = "", price_filter: str = "", sort: str = "trending",
                         verified_only: bool = False, ejectable_only: bool = False,
                         source_type: str = "", query: str = "",
                         compatible_with: str = "",
                         page: int = 1, per_page: int = 12):
    """Unified explore query with faceted filtering. Returns (tools, total)."""
    conditions = ["t.status = 'approved'"]
    params: list = []

    if query:
        conditions.append("(LOWER(t.name) LIKE ? OR LOWER(t.tagline) LIKE ?)")
        q_like = f"%{query.strip().lower()}%"
        params.extend([q_like, q_like])

    if category_id:
        conditions.append("EXISTS(SELECT 1 FROM tool_categories tc_f WHERE tc_f.tool_id = t.id AND tc_f.category_id = ?)")
        params.append(category_id)

    if tag:
        tag_lower = tag.strip().lower()
        conditions.append(
            "(LOWER(TRIM(t.tags)) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)"
        )
        params.extend([tag_lower, f'{tag_lower},%', f'%,{tag_lower}', f'%,{tag_lower},%'])

    if price_filter == "free":
        conditions.append("t.price_pence IS NULL")
    elif price_filter == "paid":
        conditions.append("t.price_pence > 0")

    if verified_only:
        conditions.append("t.is_verified = 1")

    if ejectable_only:
        conditions.append("t.is_ejectable = 1")

    if source_type in ("code", "saas"):
        conditions.append("t.source_type = ?")
        params.append(source_type)

    if compatible_with:
        conditions.append("""
            t.slug IN (
                SELECT CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END
                FROM tool_pairs tp
                WHERE (tp.tool_a_slug = ? OR tp.tool_b_slug = ?) AND tp.success_count >= 1
            )
        """)
        params.extend([compatible_with, compatible_with, compatible_with])

    where = " AND ".join(conditions)

    boost_prefix = "(CASE WHEN t.is_boosted = 1 AND t.boost_expires_at > datetime('now') THEN 0 ELSE 1 END), "
    order_by = {
        "hot": boost_prefix + "t.upvote_count DESC, t.created_at DESC",
        "trending": boost_prefix + "t.upvote_count DESC, t.created_at DESC",
        "newest": boost_prefix + "t.created_at DESC",
        "name": boost_prefix + "t.name ASC",
        "upvotes": boost_prefix + "t.upvote_count DESC, t.created_at DESC",
    }.get(sort, boost_prefix + "t.upvote_count DESC, t.created_at DESC")

    offset = (page - 1) * per_page

    sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug,
              EXISTS(SELECT 1 FROM maker_updates mu WHERE mu.tool_id = t.id AND mu.created_at >= datetime('now', '-14 days')) as has_changelog_14d
              FROM tools t JOIN categories c ON t.category_id = c.id
              WHERE {where}
              ORDER BY {order_by}
              LIMIT ? OFFSET ?"""
    cursor = await db.execute(sql, params + [per_page, offset])
    rows = await cursor.fetchall()

    count_sql = f"SELECT COUNT(*) as cnt FROM tools t WHERE {where}"
    count_cursor = await db.execute(count_sql, params)
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


async def get_similar_tools(db: aiosqlite.Connection, tool_id: int, category_id: int,
                             tags: str, limit: int = 4):
    """Get similar tools based on shared tags and same category.
    Filters in SQL first (same category), then scores by tag overlap in Python.
    Returns list of tool dicts with category info.
    """
    # First: get same-category tools (typically ~40, not ~880)
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved' AND t.id != ? AND t.category_id = ?
           ORDER BY t.upvote_count DESC
           LIMIT ?""",
        (tool_id, category_id, limit * 5),
    )
    results = [dict(r) for r in await cursor.fetchall()]

    # Score by tag overlap if we have tags
    input_tags = {t.strip().lower() for t in tags.split(',') if t.strip()} if tags else set()
    if input_tags and results:
        for r in results:
            r_tags = set(t.strip().lower() for t in (r.get('tags', '') or '').split(',') if t.strip())
            r['_score'] = len(input_tags & r_tags)
        results.sort(key=lambda x: (-x.get('_score', 0), -x.get('upvote_count', 0)))

    # If not enough same-category results, backfill with tag-matching tools from other categories
    if len(results) < limit and input_tags:
        existing_ids = {r['id'] for r in results}
        existing_ids.add(tool_id)
        # Build LIKE clauses for tag matching
        tag_conditions = []
        tag_params = []
        for tag in list(input_tags)[:5]:  # cap at 5 tags to keep query bounded
            tag_conditions.append("LOWER(t.tags) LIKE ?")
            tag_params.append(f"%{tag}%")
        if tag_conditions:
            placeholders = ','.join('?' for _ in existing_ids)
            sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug
                      FROM tools t JOIN categories c ON t.category_id = c.id
                      WHERE t.status = 'approved'
                        AND t.id NOT IN ({placeholders})
                        AND t.category_id != ?
                        AND ({' OR '.join(tag_conditions)})
                      ORDER BY t.upvote_count DESC
                      LIMIT ?"""
            params = list(existing_ids) + [category_id] + tag_params + [limit - len(results)]
            cursor2 = await db.execute(sql, params)
            extras = [dict(r) for r in await cursor2.fetchall()]
            results.extend(extras)

    # Clean up internal scoring key
    for r in results:
        r.pop('_score', None)

    return results[:limit]


# ── Round 9: Retention & Engagement ──────────────────────────────────────

def extract_domain(url: str) -> str:
    """Extract base domain from a URL. 'https://www.example.com/path' -> 'example.com'"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url if '://' in url else f'https://{url}')
        host = parsed.hostname or ''
        if host.startswith('www.'):
            host = host[4:]
        return host.lower()
    except Exception:
        return ''


async def complete_claim(db, tool_id: int, user_id: int):
    """Finalize a tool claim — set maker_id, claimed_at, and user role."""
    cursor = await db.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
    user_row = await cursor.fetchone()
    maker_name = user_row['name'] or user_row['email'].split('@')[0]
    maker_id = await get_or_create_maker(db, maker_name)
    await db.execute(
        "UPDATE tools SET maker_id = ?, claimed_at = CURRENT_TIMESTAMP WHERE id = ? AND claimed_at IS NULL",
        (maker_id, tool_id),
    )
    await db.execute(
        "UPDATE users SET maker_id = COALESCE(maker_id, ?), role = 'maker' WHERE id = ?",
        (maker_id, user_id),
    )
    await db.commit()
    return maker_id


async def create_claim_token(db, tool_id: int, user_id: int) -> str:
    """Create a claim token for a user wanting to claim a tool. 24h expiry."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    await db.execute(
        "INSERT INTO claim_tokens (tool_id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
        (tool_id, user_id, token, expires_at.isoformat()))
    await db.commit()
    return token


async def verify_claim_token(db, token: str):
    """Verify a claim token. Returns (tool_id, user_id) or None.
    On success: marks token used, delegates claim completion to complete_claim()."""
    cursor = await db.execute(
        "SELECT tool_id, user_id, expires_at, used FROM claim_tokens WHERE token = ?", (token,))
    row = await cursor.fetchone()
    if not row or row['used']:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        return None
    tool_id, user_id = row['tool_id'], row['user_id']
    # Complete the claim (single source of truth)
    await complete_claim(db, tool_id, user_id)
    # Mark token used
    await db.execute("UPDATE claim_tokens SET used = 1 WHERE token = ?", (token,))
    await db.commit()
    return (tool_id, user_id)


async def create_magic_claim_token(db, tool_id: int, days: int = 30) -> str:
    """Create a magic claim token for admin to share. 30-day expiry. No user required."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()
    await db.execute(
        "INSERT INTO magic_claim_tokens (tool_id, token, expires_at) VALUES (?, ?, ?)",
        (tool_id, token, expires_at))
    await db.commit()
    return token


async def get_magic_claim_token(db, token: str):
    """Look up a magic claim token. Returns dict with tool_id or None."""
    cursor = await db.execute(
        "SELECT id, tool_id, expires_at, used FROM magic_claim_tokens WHERE token = ?", (token,))
    row = await cursor.fetchone()
    if not row or row['used']:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        return None
    return dict(row)


async def use_magic_claim_token(db, token: str):
    """Mark a magic claim token as used."""
    await db.execute("UPDATE magic_claim_tokens SET used = 1 WHERE token = ?", (token,))
    await db.commit()


async def get_makers_in_category(db, category_id: int, exclude_tool_id: int = None):
    """Get all makers who have tools in a given category, with their emails.
    Returns list of dicts: {email, name, maker_id}"""
    exclude = f"AND t.id != {int(exclude_tool_id)}" if exclude_tool_id else ""
    cursor = await db.execute(f"""
        SELECT DISTINCT u.email, u.name, m.id as maker_id, m.name as maker_name
        FROM tools t
        JOIN makers m ON t.maker_id = m.id
        JOIN users u ON u.maker_id = m.id
        WHERE t.category_id = ? AND t.status = 'approved' {exclude}
    """, (category_id,))
    return await cursor.fetchall()


async def get_showcase_tools(db, limit: int = 6):
    """Get landing page showcase tools — curated first, then AI-recommended.
    Tools with landing_position set appear first (ordered by position).
    Remaining slots filled by highest mcp_view_count (AI recommendations)."""
    cursor = await db.execute("""
        SELECT t.*, c.name as category_name, c.slug as category_slug,
               m.name as maker_name, m.slug as maker_slug
        FROM tools t
        JOIN categories c ON t.category_id = c.id
        LEFT JOIN makers m ON t.maker_id = m.id
        WHERE t.status = 'approved'
        ORDER BY
            CASE WHEN t.landing_position IS NOT NULL THEN 0 ELSE 1 END,
            t.landing_position,
            t.mcp_view_count DESC,
            t.upvote_count DESC
        LIMIT ?
    """, (limit,))
    return [dict(r) for r in await cursor.fetchall()]


async def get_trending_scored(db, limit: int = 20, days: int = 7):
    """Get tools ranked by time-decayed heat score.
    Score = (upvotes + views_7d) / (hours_since_created ^ 1.5)"""
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT t.*, c.name as category_name, c.slug as category_slug,
               COALESCE(v.view_count, 0) as views_7d,
               (t.upvote_count + COALESCE(v.view_count, 0) + (CASE WHEN t.claimed_at IS NOT NULL THEN 20 ELSE 0 END)) * 1.0 /
               MAX(1.0, POWER(MAX(1, (julianday('now') - julianday(t.created_at)) * 24), 1.5)) as heat_score,
               EXISTS(SELECT 1 FROM maker_updates mu WHERE mu.tool_id = t.id AND mu.created_at >= datetime('now', '-14 days')) as has_changelog_14d
        FROM tools t
        JOIN categories c ON t.category_id = c.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as view_count
            FROM tool_views
            WHERE viewed_at >= datetime('now', ?)
            GROUP BY tool_id
        ) v ON v.tool_id = t.id
        WHERE t.status = 'approved'
        ORDER BY heat_score DESC
        LIMIT ?
    """, (days_param, limit))
    results = [dict(r) for r in await cursor.fetchall()]
    results.sort(key=lambda r: (0 if r.get('is_boosted') and r.get('boost_expires_at', '') > datetime.utcnow().isoformat() else 1))
    return results


async def get_new_for_user(db: aiosqlite.Connection, user_id: int, limit: int = 6) -> list[dict]:
    """Get recently added tools in categories the user has bookmarked or viewed."""
    # Find categories the user is interested in (from bookmarks)
    cursor = await db.execute("""
        SELECT DISTINCT t.category_id
        FROM wishlists w
        JOIN tools t ON t.id = w.tool_id
        WHERE w.user_id = ?
        LIMIT 10
    """, (user_id,))
    cat_rows = await cursor.fetchall()
    cat_ids = [r['category_id'] for r in cat_rows]

    if not cat_ids:
        return []

    # Get recently added tools in those categories, excluding ones they've already bookmarked
    placeholders = ','.join('?' for _ in cat_ids)
    cursor = await db.execute(f"""
        SELECT t.*, c.name as category_name, c.slug as category_slug,
               COALESCE(m.name, t.maker_name) as display_maker_name,
               m.slug as maker_slug
        FROM tools t
        LEFT JOIN categories c ON c.id = t.category_id
        LEFT JOIN makers m ON m.id = t.maker_id
        WHERE t.status = 'approved'
          AND t.category_id IN ({placeholders})
          AND t.id NOT IN (SELECT tool_id FROM wishlists WHERE user_id = ?)
          AND t.created_at >= datetime('now', '-30 days')
        ORDER BY t.created_at DESC
        LIMIT ?
    """, (*cat_ids, user_id, limit))

    return [dict(row) for row in await cursor.fetchall()]


async def get_maker_funnel(db, maker_id: int, days: int = 7):
    """Get funnel analytics for a maker's tools over the last N days.
    Returns list of dicts: {tool_name, tool_slug, views, wishlist_saves, upvotes, clicks}"""
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT t.id, t.name as tool_name, t.slug as tool_slug,
               t.upvote_count as upvotes,
               COALESCE(v.view_count, 0) as views,
               COALESCE(w.save_count, 0) as wishlist_saves,
               COALESCE(c.click_count, 0) as clicks
        FROM tools t
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as view_count
            FROM tool_views
            WHERE viewed_at >= datetime('now', ?)
            GROUP BY tool_id
        ) v ON v.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as save_count
            FROM wishlists
            GROUP BY tool_id
        ) w ON w.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as click_count
            FROM outbound_clicks
            WHERE created_at >= datetime('now', ?)
            GROUP BY tool_id
        ) c ON c.tool_id = t.id
        WHERE t.maker_id = ?
        ORDER BY views DESC
    """, (days_param, days_param, maker_id))
    return await cursor.fetchall()


async def get_wishlist_users_for_tool(db, tool_id: int):
    """Get all users who wishlisted a specific tool. Returns list of {email, name, user_id}."""
    cursor = await db.execute("""
        SELECT u.id as user_id, u.email, u.name
        FROM wishlists w
        JOIN users u ON w.user_id = u.id
        WHERE w.tool_id = ?
    """, (tool_id,))
    return await cursor.fetchall()


async def get_recent_activity(db, limit: int = 10, days: int = 7):
    """Get recent marketplace activity for the homepage ticker.
    Returns list of dicts: {type, message, created_at}"""
    days_param = f'-{int(days)} days'
    activities = []
    # Recent tool approvals
    cursor = await db.execute("""
        SELECT t.name, t.created_at FROM tools t
        WHERE t.status = 'approved' AND t.created_at >= datetime('now', ?)
        ORDER BY t.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor.fetchall():
        activities.append({
            'type': 'launch',
            'message': f"{row['name']} just launched",
            'created_at': row['created_at']
        })
    # Recent upvotes
    cursor2 = await db.execute("""
        SELECT t.name, u.created_at FROM upvotes u
        JOIN tools t ON u.tool_id = t.id
        WHERE u.created_at >= datetime('now', ?)
        ORDER BY u.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor2.fetchall():
        activities.append({
            'type': 'upvote',
            'message': f"Someone upvoted {row['name']}",
            'created_at': row['created_at']
        })
    # Recent maker updates
    cursor3 = await db.execute("""
        SELECT mu.title, m.name as maker_name, mu.created_at
        FROM maker_updates mu JOIN makers m ON mu.maker_id = m.id
        WHERE mu.created_at >= datetime('now', ?)
        ORDER BY mu.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor3.fetchall():
        activities.append({
            'type': 'update',
            'message': f"{row['maker_name']} posted: {row['title']}" if row['title'] else f"{row['maker_name']} shipped an update",
            'created_at': row['created_at']
        })
    # Recent purchases
    cursor4 = await db.execute("""
        SELECT t.name, p.created_at FROM purchases p
        JOIN tools t ON p.tool_id = t.id
        WHERE p.created_at >= datetime('now', ?)
        ORDER BY p.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor4.fetchall():
        activities.append({
            'type': 'sale',
            'message': f"Someone just bought {row['name']}!",
            'created_at': row['created_at']
        })
    # Sort all by time, take top N
    activities.sort(key=lambda x: x['created_at'], reverse=True)
    return activities[:limit]


async def has_recent_changelog(db, tool_id: int, days: int = 14) -> bool:
    """Check if a tool has had a changelog/update in the last N days."""
    cursor = await db.execute(
        "SELECT 1 FROM maker_updates WHERE tool_id = ? AND created_at >= datetime('now', ?) LIMIT 1",
        (tool_id, f'-{days} days'))
    return await cursor.fetchone() is not None


async def get_tools_for_rss(db, *, category_slug: str = None, tag: str = None, limit: int = 20):
    """Get tools for RSS feed generation with full details."""
    conditions = ["t.status = 'approved'"]
    params = []
    if category_slug:
        conditions.append("c.slug = ?")
        params.append(category_slug)
    if tag:
        tag_lower = tag.lower().strip()
        conditions.append("(LOWER(t.tags) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)")
        params.extend([tag_lower, f'{tag_lower},%', f'%,{tag_lower}', f'%,{tag_lower},%'])
    where = " AND ".join(conditions)
    cursor = await db.execute(f"""
        SELECT t.*, c.name as category_name, c.slug as category_slug
        FROM tools t JOIN categories c ON t.category_id = c.id
        WHERE {where}
        ORDER BY t.created_at DESC LIMIT ?
    """, params + [limit])
    return await cursor.fetchall()


async def get_all_subscribers(db):
    """Get all subscriber emails."""
    cursor = await db.execute("SELECT email, unsubscribe_token FROM subscribers ORDER BY created_at DESC")
    return await cursor.fetchall()


# ── Round 10: User Stacks ─────────────────────────────────────────────

async def create_user_stack(db, user_id: int, title: str = 'My Stack', description: str = '') -> int:
    """Create a user stack. One per user (UNIQUE constraint)."""
    cursor = await db.execute(
        "INSERT OR IGNORE INTO user_stacks (user_id, title, description) VALUES (?, ?, ?)",
        (user_id, title.strip() or 'My Stack', description.strip()))
    await db.commit()
    if cursor.lastrowid:
        return cursor.lastrowid
    # Already exists — return existing
    row = await (await db.execute("SELECT id FROM user_stacks WHERE user_id = ?", (user_id,))).fetchone()
    return row['id'] if row else 0


async def get_user_stack(db, user_id: int):
    """Get a user's stack with all tools."""
    cursor = await db.execute("SELECT * FROM user_stacks WHERE user_id = ?", (user_id,))
    stack = await cursor.fetchone()
    if not stack:
        return None, []
    tools_cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  ust.note, ust.position
           FROM user_stack_tools ust
           JOIN tools t ON ust.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ust.stack_id = ? AND t.status = 'approved'
           ORDER BY ust.position ASC, t.name ASC""",
        (stack['id'],))
    tools = await tools_cursor.fetchall()
    return stack, tools


async def get_user_stack_by_username(db, username: str):
    """Get a public user stack by username (user.name field). Returns (stack, tools, user)."""
    cursor = await db.execute(
        """SELECT us.*, u.name as user_name, u.id as uid
           FROM user_stacks us
           JOIN users u ON us.user_id = u.id
           WHERE LOWER(REPLACE(u.name, ' ', '-')) = LOWER(?) AND us.is_public = 1""",
        (username,))
    stack = await cursor.fetchone()
    if not stack:
        return None, [], None
    tools_cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  ust.note, ust.position
           FROM user_stack_tools ust
           JOIN tools t ON ust.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ust.stack_id = ? AND t.status = 'approved'
           ORDER BY ust.position ASC, t.name ASC""",
        (stack['id'],))
    tools = await tools_cursor.fetchall()
    return stack, tools, stack


async def add_tool_to_user_stack(db, stack_id: int, tool_id: int, note: str = '', position: int = 0):
    """Add a tool to a user's stack."""
    try:
        await db.execute(
            "INSERT INTO user_stack_tools (stack_id, tool_id, note, position) VALUES (?, ?, ?, ?)",
            (stack_id, tool_id, note.strip(), position))
        await db.commit()
        return True
    except Exception:
        return False


async def remove_tool_from_user_stack(db, stack_id: int, tool_id: int):
    """Remove a tool from a user's stack."""
    await db.execute(
        "DELETE FROM user_stack_tools WHERE stack_id = ? AND tool_id = ?",
        (stack_id, tool_id))
    await db.commit()


_ALLOWED_STACK_FIELDS = {'title', 'description', 'is_public'}

async def update_user_stack(db, stack_id: int, **fields):
    """Update user stack settings (title, description, is_public)."""
    fields = {k: v for k, v in fields.items() if k in _ALLOWED_STACK_FIELDS}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [stack_id]
    await db.execute(f"UPDATE user_stacks SET {set_clause} WHERE id = ?", values)
    await db.commit()


async def get_public_stacks(db, limit: int = 20):
    """Get public user stacks for the community gallery."""
    cursor = await db.execute(
        """SELECT us.*, u.name as user_name,
                  COUNT(ust.tool_id) as tool_count
           FROM user_stacks us
           JOIN users u ON us.user_id = u.id
           LEFT JOIN user_stack_tools ust ON ust.stack_id = us.id
           WHERE us.is_public = 1
           GROUP BY us.id
           HAVING tool_count > 0
           ORDER BY tool_count DESC, us.created_at DESC
           LIMIT ?""",
        (limit,))
    return await cursor.fetchall()


async def get_stack_preview_tools(db, stack_id: int, limit: int = 3):
    """Get first N tools from a user stack for preview cards."""
    cursor = await db.execute(
        """SELECT t.name, t.slug, c.icon as category_icon
           FROM user_stack_tools ust
           JOIN tools t ON ust.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ust.stack_id = ? AND t.status = 'approved'
           ORDER BY ust.position ASC LIMIT ?""",
        (stack_id, limit))
    return await cursor.fetchall()


# ── Round 10: Search Logs & Live Wire ─────────────────────────────────

async def log_search(db, query: str, source: str = 'web', result_count: int = 0,
                     top_result_slug: str = None, top_result_name: str = None,
                     api_key_id: int = None, agent_client: str = None,
                     visitor_id: str = None):
    """Log a search query for the Live Wire feed and maker analytics."""
    if not query or not query.strip():
        return
    normalized = normalize_search_query(query)
    await db.execute(
        """INSERT INTO search_logs (query, normalized_query, source, result_count, top_result_slug, top_result_name, api_key_id, agent_client, visitor_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (query.strip()[:200], normalized, source, result_count, top_result_slug, top_result_name, api_key_id,
         str(agent_client)[:100] if agent_client else None,
         str(visitor_id)[:16] if visitor_id else None))
    await db.commit()


async def get_search_demand(db, query: str, days: int = 30):
    """Count how many times a query (case-insensitive) has been searched in the last N days."""
    if not query or not query.strip():
        return 0
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM search_logs
           WHERE LOWER(query) = LOWER(?)
           AND created_at >= datetime('now', ?)""",
        (query.strip(), f'-{days} days'))
    row = await cursor.fetchone()
    return row['cnt'] if row else 0


async def get_recent_searches(db, limit: int = 30):
    """Get recent search queries for the Live Wire feed."""
    cursor = await db.execute(
        """SELECT * FROM search_logs
           ORDER BY created_at DESC LIMIT ?""",
        (limit,))
    return await cursor.fetchall()


async def get_search_gaps(db: aiosqlite.Connection, days: int = 30, min_searches: int = 3, limit: int = 20) -> list:
    """Get zero-result search queries as demand signals."""
    cursor = await db.execute("""
        SELECT normalized_query as query, COUNT(*) as count,
               MAX(created_at) as last_searched,
               COUNT(DISTINCT COALESCE(api_key_id, -1)) as unique_sources,
               GROUP_CONCAT(DISTINCT source) as sources
        FROM search_logs
        WHERE result_count = 0
          AND normalized_query IS NOT NULL
          AND normalized_query != ''
          AND created_at > datetime('now', '-' || ? || ' days')
        GROUP BY normalized_query
        HAVING COUNT(*) >= ?
        ORDER BY count DESC
        LIMIT ?
    """, (days, min_searches, limit))
    return [dict(r) for r in await cursor.fetchall()]


async def get_search_stats(db):
    """Get search statistics for the Live Wire dashboard."""
    cursor = await db.execute("""
        SELECT
            (SELECT COUNT(*) FROM search_logs WHERE created_at >= datetime('now', '-1 day')) as today,
            (SELECT COUNT(*) FROM search_logs WHERE created_at >= datetime('now', '-7 days')) as this_week,
            (SELECT COUNT(*) FROM search_logs) as all_time
    """)
    stats = await cursor.fetchone()
    # Top query this week
    top_cursor = await db.execute("""
        SELECT query, COUNT(*) as cnt FROM search_logs
        WHERE created_at >= datetime('now', '-7 days')
        GROUP BY LOWER(query) ORDER BY cnt DESC LIMIT 1
    """)
    top = await top_cursor.fetchone()
    return {
        'today': stats['today'],
        'this_week': stats['this_week'],
        'all_time': stats['all_time'],
        'top_query': top['query'] if top else None,
        'top_query_count': top['cnt'] if top else 0,
    }


async def get_follow_through_rate(db, days: int = 30) -> dict:
    """Calculate MCP search → detail view follow-through rate."""
    cursor = await db.execute(
        """SELECT
            (SELECT COUNT(*) FROM search_logs WHERE source = 'api'
             AND created_at >= datetime('now', ? || ' days')) as searches,
            (SELECT COUNT(*) FROM agent_citations
             WHERE created_at >= datetime('now', ? || ' days')) as details
        """, (f'-{days}', f'-{days}'))
    row = await cursor.fetchone()
    searches = (row['searches'] if row else 0) or 0
    details = row['details'] or 0
    rate = round(details / searches * 100, 1) if searches > 0 else 0
    return {"searches": searches, "details": details, "rate": rate, "days": days}


async def get_search_terms_for_tool(db, tool_slug: str, limit: int = 10):
    """Get search queries that led to a specific tool being the top result."""
    cursor = await db.execute(
        """SELECT query, COUNT(*) as count, MAX(created_at) as last_seen
           FROM search_logs WHERE top_result_slug = ?
           GROUP BY LOWER(query) ORDER BY count DESC LIMIT ?""",
        (tool_slug, limit))
    return await cursor.fetchall()


# ── AI Pulse: Unified Activity Feed ──────────────────────────────────

async def get_pulse_feed(db, limit: int = 50):
    """Get a unified, chronological feed of AI activity (searches + citations).

    Returns a list of dicts with keys:
        type: 'recommend' | 'search' | 'gap'
        query: the search query (for search/gap events)
        tool_name: tool name (for recommend events, or top result for search events)
        tool_slug: tool slug for linking
        agent: agent name (for recommend events)
        created_at: timestamp string
    """
    cursor = await db.execute("""
        SELECT * FROM (
            SELECT
                CASE WHEN sl.result_count > 0 AND sl.top_result_name IS NOT NULL
                     THEN 'search' ELSE 'gap' END as type,
                sl.query as query,
                sl.top_result_name as tool_name,
                sl.top_result_slug as tool_slug,
                CASE WHEN sl.source = 'api' THEN 'AI Agent' ELSE 'Developer' END as agent,
                sl.created_at as created_at
            FROM search_logs sl
            WHERE sl.created_at >= datetime('now', '-7 days')
              AND LENGTH(TRIM(sl.query)) >= 2
              AND sl.query NOT LIKE '%http%'
              AND sl.query NOT LIKE '%.com%'
              AND sl.query NOT LIKE '%.org%'
              AND sl.query NOT LIKE '%.net%'
              AND sl.query NOT LIKE '%.io%'
              AND sl.query NOT LIKE '@%'

            UNION ALL

            SELECT
                'recommend' as type,
                NULL as query,
                t.name as tool_name,
                t.slug as tool_slug,
                COALESCE(ac.agent_name, 'AI Agent') as agent,
                ac.created_at as created_at
            FROM agent_citations ac
            JOIN tools t ON t.id = ac.tool_id
            WHERE ac.created_at >= datetime('now', '-7 days')
        )
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    return await cursor.fetchall()


# ── Round 10: Milestones ──────────────────────────────────────────────

MILESTONE_THRESHOLDS = {
    'first-tool': {'description': 'Listed your first tool on IndieStack', 'emoji': '🎉'},
    '100-views': {'description': 'Your tool hit 100 views', 'emoji': '👀'},
    '10-upvotes': {'description': '10 developers upvoted your tool', 'emoji': '🔥'},
    'first-review': {'description': 'Got your first review', 'emoji': '⭐'},
    'launch-ready': {'description': '100% Launch Ready', 'emoji': '🚀'},
    '50-wishlists': {'description': '50 developers wishlisted your tool', 'emoji': '💾'},
}


async def check_milestones(db, user_id: int, tool_id: int = None):
    """Check and award any newly achieved milestones. Returns list of newly awarded types."""
    new_milestones = []

    # first-tool: user has at least 1 approved tool
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM tools t
           JOIN makers m ON t.maker_id = m.id
           JOIN users u ON u.maker_id = m.id
           WHERE u.id = ? AND t.status = 'approved'""", (user_id,))
    if (await cursor.fetchone())['cnt'] >= 1:
        if await _award_milestone(db, user_id, tool_id, 'first-tool'):
            new_milestones.append('first-tool')

    if tool_id:
        # 100-views
        views = await get_tool_view_count(db, tool_id, days=9999)
        if views >= 100:
            if await _award_milestone(db, user_id, tool_id, '100-views'):
                new_milestones.append('100-views')

        # 10-upvotes
        tool = await get_tool_by_id(db, tool_id)
        if tool and tool.get('upvote_count', 0) >= 10:
            if await _award_milestone(db, user_id, tool_id, '10-upvotes'):
                new_milestones.append('10-upvotes')

        # first-review
        review_cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE tool_id = ?", (tool_id,))
        if (await review_cursor.fetchone())['cnt'] >= 1:
            if await _award_milestone(db, user_id, tool_id, 'first-review'):
                new_milestones.append('first-review')

        # 50-wishlists
        wl_cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM wishlists WHERE tool_id = ?", (tool_id,))
        if (await wl_cursor.fetchone())['cnt'] >= 50:
            if await _award_milestone(db, user_id, tool_id, '50-wishlists'):
                new_milestones.append('50-wishlists')

    return new_milestones


async def _award_milestone(db, user_id: int, tool_id: int, milestone_type: str) -> bool:
    """Award a milestone if not already achieved. Returns True if newly awarded."""
    try:
        await db.execute(
            "INSERT INTO milestones (user_id, tool_id, milestone_type) VALUES (?, ?, ?)",
            (user_id, tool_id, milestone_type))
        await db.commit()
        return True
    except Exception:
        return False  # Already exists (UNIQUE constraint)


async def get_user_milestones(db, user_id: int):
    """Get all milestones for a user."""
    cursor = await db.execute(
        """SELECT ml.*, t.name as tool_name, t.slug as tool_slug
           FROM milestones ml
           LEFT JOIN tools t ON ml.tool_id = t.id
           WHERE ml.user_id = ?
           ORDER BY ml.achieved_at DESC""",
        (user_id,))
    return await cursor.fetchall()


async def get_unshared_milestones(db, user_id: int):
    """Get milestones that haven't been shared yet (for celebration prompts)."""
    cursor = await db.execute(
        """SELECT ml.*, t.name as tool_name, t.slug as tool_slug
           FROM milestones ml
           LEFT JOIN tools t ON ml.tool_id = t.id
           WHERE ml.user_id = ? AND ml.shared = 0
           ORDER BY ml.achieved_at DESC""",
        (user_id,))
    return await cursor.fetchall()


async def mark_milestone_shared(db, milestone_id: int):
    """Mark a milestone as shared."""
    await db.execute("UPDATE milestones SET shared = 1 WHERE id = ?", (milestone_id,))
    await db.commit()


async def get_launch_readiness(db, maker_id: int) -> dict:
    """Calculate launch readiness score for a maker's tools.
    Returns dict with 'score' (0-100), 'total' items, 'completed' items, and 'items' checklist."""
    maker = await get_maker_by_id(db, maker_id)
    if not maker:
        return {'score': 0, 'total': 8, 'completed': 0, 'items': []}

    # Get maker's first approved tool (primary)
    cursor = await db.execute(
        """SELECT t.* FROM tools t WHERE t.maker_id = ? AND t.status = 'approved'
           ORDER BY t.created_at ASC LIMIT 1""", (maker_id,))
    tool = await cursor.fetchone()

    tool_edit_url = f'/dashboard/tools/{tool["id"]}/edit' if tool else '/submit'

    items = []
    # 1. Tool has tags
    items.append({
        'label': 'Add tags to your tool',
        'done': bool(tool and tool.get('tags', '').strip()),
        'icon': '🏷️',
        'action': 'link',
        'url': tool_edit_url,
    })
    # 2. Tool has replaces field
    items.append({
        'label': 'List competitors you replace',
        'done': bool(tool and tool.get('replaces', '').strip()),
        'icon': '⚔️',
        'action': 'form',
        'field': 'replaces',
        'input_type': 'text',
        'placeholder': 'e.g. Slack, Teams, Notion',
        'current': tool.get('replaces', '') if tool else '',
    })
    # 3. Maker has bio
    items.append({
        'label': 'Write your maker bio',
        'done': bool(maker.get('bio', '').strip()),
        'icon': '📝',
        'action': 'form',
        'field': 'bio',
        'input_type': 'textarea',
        'placeholder': 'Tell developers about yourself...',
        'current': maker.get('bio', '') or '',
    })
    # 4. Maker has avatar
    items.append({
        'label': 'Upload an avatar',
        'done': bool(maker.get('avatar_url', '').strip()),
        'icon': '🖼️',
        'action': 'form',
        'field': 'avatar_url',
        'input_type': 'url',
        'placeholder': 'https://example.com/avatar.jpg',
        'current': maker.get('avatar_url', '') or '',
    })
    # 5. Maker has URL
    items.append({
        'label': 'Add your website URL',
        'done': bool(maker.get('url', '').strip()),
        'icon': '🔗',
        'action': 'form',
        'field': 'url',
        'input_type': 'url',
        'placeholder': 'https://yoursite.com',
        'current': maker.get('url', '') or '',
    })
    # 6. At least 1 changelog
    has_changelog = False
    if tool:
        cl_cursor = await db.execute(
            "SELECT 1 FROM maker_updates WHERE tool_id = ? LIMIT 1", (tool['id'],))
        has_changelog = await cl_cursor.fetchone() is not None
    items.append({
        'label': 'Post your first changelog',
        'done': has_changelog,
        'icon': '📋',
        'action': 'link',
        'url': '/dashboard/updates' if tool else '/submit',
    })
    # 7. Tool has github_url (via the url field or a github link)
    has_github = bool(tool and 'github.com' in (tool.get('url', '') or ''))
    items.append({
        'label': 'Link your GitHub repo',
        'done': has_github,
        'icon': '🐙',
        'action': 'link',
        'url': tool_edit_url,
    })

    completed = sum(1 for item in items if item['done'])
    score = round(completed / len(items) * 100)

    return {
        'score': score,
        'total': len(items),
        'completed': completed,
        'items': items,
        'tool_id': tool['id'] if tool else None,
    }


async def get_makers_for_ego_ping(db) -> list[dict]:
    """Get all makers with claimed tools and their weekly stats for ego ping emails."""
    cursor = await db.execute("""
        SELECT
            m.id as maker_id, m.name as maker_name,
            u.email,
            t.id as tool_id, t.name as tool_name, t.slug as tool_slug,
            t.upvote_count,
            (SELECT COUNT(*) FROM tool_views WHERE tool_id = t.id
             AND viewed_at > datetime('now', '-7 days')) as weekly_views,
            (SELECT COUNT(*) FROM wishlists WHERE tool_id = t.id) as wishlist_count,
            (SELECT COUNT(*) FROM outbound_clicks WHERE tool_id = t.id
             AND created_at > datetime('now', '-7 days')) as weekly_clicks,
            (SELECT COUNT(*) FROM maker_updates WHERE tool_id = t.id) as changelog_count,
            (SELECT COUNT(*) FROM maker_updates WHERE tool_id = t.id
             AND created_at > datetime('now', '-14 days')) as recent_updates,
            (SELECT COUNT(*) FROM agent_citations WHERE tool_id = t.id
             AND created_at > datetime('now', '-7 days')) as weekly_citations
        FROM makers m
        JOIN users u ON u.maker_id = m.id
        JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        WHERE u.email IS NOT NULL AND u.email != ''
        AND COALESCE(u.email_opt_out, 0) = 0
        ORDER BY m.id
    """)
    return [dict(row) for row in await cursor.fetchall()]


# ── Admin Analytics & Outreach Queries ──────────────────────────────────


async def get_revenue_timeseries(db, days: int = 30) -> list:
    """Daily revenue for time-series chart."""
    cursor = await db.execute("""
        SELECT DATE(created_at) as date,
               SUM(amount_pence) as revenue_pence,
               SUM(commission_pence) as commission_pence,
               COUNT(*) as count
        FROM purchases
        WHERE created_at >= datetime('now', ? || ' days')
        GROUP BY DATE(created_at)
        ORDER BY date
    """, (f'-{days}',))
    return [dict(r) for r in await cursor.fetchall()]


async def get_pro_subscriber_stats(db) -> dict:
    """Active Pro subscriber count and MRR estimate."""
    cursor = await db.execute("""
        SELECT COUNT(*) as active_count
        FROM subscriptions
        WHERE status = 'active' AND current_period_end > datetime('now')
    """)
    row = await cursor.fetchone()
    active = row['active_count'] if row else 0
    # Pro plan = £9/mo = 900 pence
    return {'active_count': active, 'mrr_pence': active * 900}


async def get_rate_metrics(db, days: int = 30) -> dict:
    """Key rate metrics: CTR, claim rate, catalog growth rate, churn rate."""
    days_param = f'-{days} days'

    # CTR: outbound clicks / tool views
    cursor = await db.execute("""
        SELECT
            (SELECT COUNT(*) FROM outbound_clicks WHERE created_at >= datetime('now', ?)) as clicks,
            (SELECT COUNT(*) FROM tool_views WHERE viewed_at >= datetime('now', ?)) as views
    """, (days_param, days_param))
    row = await cursor.fetchone()
    clicks = (row['clicks'] if row else 0) or 0
    views = (row['views'] if row else 0) or 0
    ctr = round(clicks / views * 100, 1) if views > 0 else 0

    # Claim rate: tools with a maker (claimed) / total approved
    cursor = await db.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(maker_id) as claimed
        FROM tools WHERE status = 'approved'
    """)
    row = await cursor.fetchone()
    total_tools = (row['total'] if row else 0) or 0
    claimed_tools = (row['claimed'] if row else 0) or 0
    claim_rate = round(claimed_tools / total_tools * 100, 1) if total_tools > 0 else 0

    # Catalog growth rate: new approved tools in period / total approved
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND created_at >= datetime('now', ?)",
        (days_param,)
    )
    row = await cursor.fetchone()
    new_tools = (row['cnt'] if row else 0) or 0
    growth_rate = round(new_tools / total_tools * 100, 1) if total_tools > 0 else 0

    # Churn: non-active subscriptions / total subscriptions
    cursor = await db.execute("SELECT status, COUNT(*) as cnt FROM subscriptions GROUP BY status")
    sub_counts: dict = {}
    for r in await cursor.fetchall():
        sub_counts[r['status']] = r['cnt']
    total_subs = sum(sub_counts.values()) or 0
    active_subs = sub_counts.get('active', 0)
    churned_subs = total_subs - active_subs
    churn_rate = round(churned_subs / total_subs * 100, 1) if total_subs > 0 else 0

    return {
        'ctr': ctr, 'clicks': clicks, 'views': views,
        'claim_rate': claim_rate, 'claimed': claimed_tools, 'total_tools': total_tools,
        'growth_rate': growth_rate, 'new_tools': new_tools,
        'churn_rate': churn_rate, 'churned': churned_subs, 'total_subs': total_subs,
        'days': days,
    }


async def get_platform_funnel(db, days: int = 30) -> list:
    """Platform-wide funnel: views -> clicks -> wishlists -> purchases per tool."""
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT t.id, t.name, t.slug,
               COALESCE(v.cnt, 0) as views,
               COALESCE(c.cnt, 0) as clicks,
               COALESCE(w.cnt, 0) as wishlists,
               COALESCE(p.cnt, 0) as purchases
        FROM tools t
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM tool_views
                   WHERE viewed_at >= datetime('now', ?) GROUP BY tool_id) v ON v.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM outbound_clicks
                   WHERE created_at >= datetime('now', ?) GROUP BY tool_id) c ON c.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM wishlists GROUP BY tool_id) w ON w.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM purchases
                   WHERE created_at >= datetime('now', ?) GROUP BY tool_id) p ON p.tool_id = t.id
        WHERE t.status = 'approved'
          AND (COALESCE(v.cnt, 0) > 0 OR COALESCE(c.cnt, 0) > 0 OR COALESCE(w.cnt, 0) > 0 OR COALESCE(p.cnt, 0) > 0)
        ORDER BY views DESC
        LIMIT 30
    """, (days_param, days_param, days_param))
    return [dict(r) for r in await cursor.fetchall()]


async def get_top_tools_by_metric(db, metric: str = 'views', days: int = 30, limit: int = 15) -> list:
    """Top tools by views, clicks, or wishlists."""
    table_map = {
        'views': ('tool_views', 'viewed_at'),
        'clicks': ('outbound_clicks', 'created_at'),
        'wishlists': ('wishlists', 'created_at'),
    }
    if metric not in table_map:
        return []
    table, date_col = table_map[metric]
    days_param = f'-{int(days)} days'
    cursor = await db.execute(f"""
        SELECT t.name, t.slug, COUNT(m.id) as count
        FROM tools t
        JOIN {table} m ON m.tool_id = t.id
        WHERE m.{date_col} >= datetime('now', ?)
          AND t.status = 'approved'
        GROUP BY t.id
        ORDER BY count DESC
        LIMIT ?
    """, (days_param, int(limit)))
    return [dict(r) for r in await cursor.fetchall()]


async def get_maker_leaderboard(db, days: int = 30) -> list:
    """Makers ranked by total views across their tools."""
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT m.id, m.name, m.slug,
               COUNT(DISTINCT t.id) as tool_count,
               COALESCE(SUM(v.cnt), 0) as total_views,
               COALESCE(SUM(c.cnt), 0) as total_clicks,
               MAX(mu.created_at) as last_update
        FROM makers m
        JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM tool_views
                   WHERE viewed_at >= datetime('now', ?) GROUP BY tool_id) v ON v.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM outbound_clicks
                   WHERE created_at >= datetime('now', ?) GROUP BY tool_id) c ON c.tool_id = t.id
        LEFT JOIN maker_updates mu ON mu.maker_id = m.id
        GROUP BY m.id
        ORDER BY total_views DESC
    """, (days_param, days_param))
    return [dict(r) for r in await cursor.fetchall()]


async def get_maker_reputation_leaderboard(db) -> list:
    """Public maker leaderboard with reputation scores.
    Score: upvotes*1 + reviews*5 + clicks(30d)*2 + verified*10 + active_changelog*5
    """
    cursor = await db.execute("""
        SELECT m.id, m.name, m.slug, m.indie_status,
               COUNT(DISTINCT t.id) as tool_count,
               COALESCE(SUM(t.upvote_count), 0) as total_upvotes,
               COALESCE(SUM(t.is_verified), 0) as verified_count,
               COALESCE(rv.review_count, 0) as total_reviews,
               COALESCE(cl.click_count, 0) as total_clicks,
               COALESCE(ch.has_recent, 0) as has_changelog,
               (COALESCE(SUM(t.upvote_count), 0) * 1
                + COALESCE(rv.review_count, 0) * 5
                + COALESCE(cl.click_count, 0) * 2
                + 0
                + COALESCE(ch.has_recent, 0) * 5
               ) as reputation_score
        FROM makers m
        JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        LEFT JOIN (
            SELECT t2.maker_id, COUNT(*) as review_count
            FROM reviews r JOIN tools t2 ON r.tool_id = t2.id
            GROUP BY t2.maker_id
        ) rv ON rv.maker_id = m.id
        LEFT JOIN (
            SELECT t3.maker_id, COUNT(*) as click_count
            FROM outbound_clicks oc JOIN tools t3 ON oc.tool_id = t3.id
            WHERE oc.created_at >= datetime('now', '-30 days')
            GROUP BY t3.maker_id
        ) cl ON cl.maker_id = m.id
        LEFT JOIN (
            SELECT mu2.maker_id, 1 as has_recent
            FROM maker_updates mu2
            WHERE mu2.created_at >= datetime('now', '-14 days')
            GROUP BY mu2.maker_id
        ) ch ON ch.maker_id = m.id
        WHERE m.slug != 'community'
        GROUP BY m.id
        HAVING tool_count > 0
        ORDER BY reputation_score DESC
    """)
    return [dict(r) for r in await cursor.fetchall()]



async def get_search_trends(db, days: int = 30, limit: int = 20) -> list:
    """Most popular searches with result counts."""
    cursor = await db.execute("""
        SELECT LOWER(TRIM(query)) as query, COUNT(*) as count,
               ROUND(AVG(result_count), 1) as avg_results
        FROM search_logs
        WHERE created_at >= datetime('now', ? || ' days')
        GROUP BY LOWER(TRIM(query))
        ORDER BY count DESC
        LIMIT ?
    """, (f'-{days}', limit))
    return [dict(r) for r in await cursor.fetchall()]


async def get_subscriber_growth(db) -> list:
    """Daily subscriber signups with running cumulative total."""
    cursor = await db.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as new_subs
        FROM subscribers
        GROUP BY DATE(created_at)
        ORDER BY date
    """)
    rows = [dict(r) for r in await cursor.fetchall()]
    cumulative = 0
    for row in rows:
        cumulative += row['new_subs']
        row['cumulative'] = cumulative
    return rows


async def get_subscriber_count(db) -> int:
    """Total email subscriber count."""
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM subscribers")
    row = await cursor.fetchone()
    return row['cnt'] if row else 0


async def get_maker_activity_status(db) -> list:
    """All makers with activity status: active (<14d), idle (14-60d), dormant (>60d)."""
    cursor = await db.execute("""
        SELECT m.id, m.name, m.slug, m.created_at as joined,
               COUNT(DISTINCT t.id) as tool_count,
               MAX(mu.created_at) as last_update,
               u.email,
               CAST(JULIANDAY('now') - JULIANDAY(
                   MAX(COALESCE(mu.created_at, m.created_at), m.created_at)
               ) AS INTEGER) as days_inactive
        FROM makers m
        LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        LEFT JOIN maker_updates mu ON mu.maker_id = m.id
        LEFT JOIN users u ON u.maker_id = m.id
        GROUP BY m.id
        ORDER BY days_inactive DESC
    """)
    rows = [dict(r) for r in await cursor.fetchall()]
    for row in rows:
        d = row.get('days_inactive') or 999
        if d < 14:
            row['status'] = 'active'
        elif d < 60:
            row['status'] = 'idle'
        else:
            row['status'] = 'dormant'
    return rows


async def get_all_subscribers_with_dates(db) -> list:
    """All subscribers for email blast UI."""
    cursor = await db.execute("SELECT id, email, unsubscribe_token, created_at FROM subscribers ORDER BY created_at DESC")
    return [dict(r) for r in await cursor.fetchall()]


async def get_unclaimed_tools_for_outreach(db) -> list:
    """Unclaimed approved tools for bulk magic link outreach.
    Sorted by mcp_view_count DESC so outreach targets the most AI-recommended tools first."""
    cursor = await db.execute("""
        SELECT t.id, t.name, t.slug, t.maker_name, t.maker_url,
               COALESCE(t.mcp_view_count, 0) AS mcp_view_count
        FROM tools t
        WHERE t.maker_id IS NULL AND t.status = 'approved'
        ORDER BY t.mcp_view_count DESC, t.upvote_count DESC
    """)
    return [dict(r) for r in await cursor.fetchall()]


async def get_recently_claimed_tools(db, limit=20) -> list:
    """Recently claimed tools with maker info, for admin outreach tracking."""
    cursor = await db.execute("""
        SELECT t.id, t.name, t.slug, t.claimed_at,
               m.name as maker_name, m.slug as maker_slug,
               u.email as maker_email
        FROM tools t
        JOIN makers m ON t.maker_id = m.id
        LEFT JOIN users u ON u.maker_id = m.id
        WHERE t.maker_id IS NOT NULL AND t.claimed_at IS NOT NULL
        ORDER BY t.claimed_at DESC
        LIMIT ?
    """, (limit,))
    return [dict(r) for r in await cursor.fetchall()]


# ── API Keys ──────────────────────────────────────────────────────────────

async def create_api_key(db: aiosqlite.Connection, user_id: int, name: str = "Default") -> dict:
    """Create a new API key for a user. Returns the full key (only time it's visible)."""
    key = "isk_" + secrets.token_urlsafe(32)
    # Check if user is Pro — new keys should inherit the correct tier
    is_pro = await check_pro(db, user_id)
    tier = "pro" if is_pro else "free"
    await db.execute(
        "INSERT INTO api_keys (key, user_id, name, tier) VALUES (?, ?, ?, ?)",
        (key, user_id, name, tier),
    )
    await db.commit()
    return {"key": key, "name": name, "tier": tier}


async def get_api_keys_for_user(db: aiosqlite.Connection, user_id: int) -> list[dict]:
    """Get all API keys for a user (key masked to prefix + last 8 chars)."""
    cursor = await db.execute(
        "SELECT id, key, name, tier, scopes, is_active, last_used_at, created_at "
        "FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        k = r["key"]
        result.append({
            "id": r["id"],
            "key_preview": k[:4] + "..." + k[-8:] if len(k) > 12 else k,
            "name": r["name"],
            "tier": r["tier"],
            "scopes": r["scopes"],
            "is_active": r["is_active"],
            "last_used_at": r["last_used_at"],
            "created_at": r["created_at"],
        })
    return result


async def get_api_key_by_key(db: aiosqlite.Connection, key: str) -> dict | None:
    """Look up an active API key by its full key string."""
    cursor = await db.execute(
        "SELECT ak.id, ak.key, ak.user_id, ak.name, ak.tier, ak.scopes, ak.is_active, u.email "
        "FROM api_keys ak JOIN users u ON ak.user_id = u.id "
        "WHERE ak.key = ? AND ak.is_active = 1",
        (key,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def revoke_api_key(db: aiosqlite.Connection, key_id: int, user_id: int) -> bool:
    """Revoke an API key. user_id check prevents cross-user revocation."""
    cursor = await db.execute(
        "UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?",
        (key_id, user_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def touch_api_key(db: aiosqlite.Connection, key_id: int):
    """Update last_used_at timestamp."""
    await db.execute(
        "UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?",
        (key_id,),
    )


async def log_api_usage(db: aiosqlite.Connection, key_id: int, endpoint: str):
    """Log a single API request."""
    await db.execute(
        "INSERT INTO api_usage_logs (key_id, endpoint) VALUES (?, ?)",
        (key_id, endpoint),
    )


async def record_agent_action(
    db: aiosqlite.Connection,
    api_key_id: int | None,
    user_id: int,
    action: str,
    tool_slug: str,
    tool_b_slug: str | None = None,
    success: int | None = None,
    notes: str | None = None,
    query_context: str | None = None,
) -> int:
    """Record an agent action. Returns the action ID."""
    cursor = await db.execute(
        """INSERT INTO agent_actions
           (api_key_id, user_id, action, tool_slug, tool_b_slug, success, notes, query_context)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (api_key_id, user_id, action, tool_slug, tool_b_slug, success, notes, query_context),
    )
    await db.commit()
    return cursor.lastrowid


async def get_agent_action_counts(db: aiosqlite.Connection, user_id: int, days: int = 30) -> dict:
    """Get agent action counts for a user's dashboard."""
    cursor = await db.execute(
        """SELECT action, COUNT(*) as cnt
           FROM agent_actions
           WHERE user_id = ? AND created_at >= datetime('now', ?)
           GROUP BY action""",
        (user_id, f'-{days} days'),
    )
    rows = await cursor.fetchall()
    counts = {r['action']: r['cnt'] for r in rows}
    cursor2 = await db.execute(
        """SELECT success, COUNT(*) as cnt
           FROM agent_actions
           WHERE user_id = ? AND action = 'report_outcome' AND created_at >= datetime('now', ?)
           GROUP BY success""",
        (user_id, f'-{days} days'),
    )
    outcome_rows = await cursor2.fetchall()
    counts['outcomes_success'] = sum(r['cnt'] for r in outcome_rows if r['success'] == 1)
    counts['outcomes_fail'] = sum(r['cnt'] for r in outcome_rows if r['success'] == 0)
    return counts


async def get_agent_action_log(db: aiosqlite.Connection, user_id: int, limit: int = 50) -> list[dict]:
    """Get recent agent actions for the activity log."""
    cursor = await db.execute(
        """SELECT action, tool_slug, tool_b_slug, success, notes, query_context, created_at
           FROM agent_actions
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def check_agent_action_exists(db: aiosqlite.Connection, user_id: int, action: str, tool_slug: str, tool_b_slug: str | None = None) -> bool:
    """Check if an agent action already exists (for dedup)."""
    if tool_b_slug:
        cursor = await db.execute(
            "SELECT 1 FROM agent_actions WHERE user_id = ? AND action = ? AND tool_slug = ? AND tool_b_slug = ?",
            (user_id, action, tool_slug, tool_b_slug),
        )
    else:
        cursor = await db.execute(
            "SELECT 1 FROM agent_actions WHERE user_id = ? AND action = ? AND tool_slug = ?",
            (user_id, action, tool_slug),
        )
    return await cursor.fetchone() is not None


async def check_agent_daily_action(db: aiosqlite.Connection, user_id: int, action: str, tool_slug: str) -> bool:
    """Check if this action was already taken today (for daily dedup)."""
    cursor = await db.execute(
        "SELECT 1 FROM agent_actions WHERE user_id = ? AND action = ? AND tool_slug = ? AND created_at >= date('now')",
        (user_id, action, tool_slug),
    )
    return await cursor.fetchone() is not None


async def count_agent_actions_today(db: aiosqlite.Connection, api_key_id: int, action: str) -> int:
    """Count how many times this action was taken today by this key."""
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_actions WHERE api_key_id = ? AND action = ? AND created_at >= date('now')",
        (api_key_id, action),
    )
    row = await cursor.fetchone()
    return row['cnt'] if row else 0


async def get_tool_recommendation_count(db: aiosqlite.Connection, tool_slug: str) -> int:
    """Get total recommendation count for a tool (across all agents)."""
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_actions WHERE tool_slug = ? AND action = 'recommend'",
        (tool_slug,),
    )
    row = await cursor.fetchone()
    return row['cnt'] if row else 0


async def get_tool_success_rate(db: aiosqlite.Connection, tool_slug: str) -> dict:
    """Get success rate for a tool from agent outcome reports."""
    cursor = await db.execute(
        "SELECT success, COUNT(*) as cnt FROM agent_actions WHERE tool_slug = ? AND action = 'report_outcome' GROUP BY success",
        (tool_slug,),
    )
    rows = await cursor.fetchall()
    success = sum(r['cnt'] for r in rows if r['success'] == 1)
    fail = sum(r['cnt'] for r in rows if r['success'] == 0)
    total = success + fail
    # Confidence: low (<5 signals), medium (5-20), high (>20)
    confidence = "none" if total == 0 else "low" if total < 5 else "medium" if total <= 20 else "high"
    return {"success": success, "fail": fail, "total": total, "rate": round(success / total * 100) if total else 0, "confidence": confidence}


async def compute_implicit_signals(db: aiosqlite.Connection, hours: int = 24) -> list[dict]:
    """Infer adoption/rejection from search→detail view sequences.

    Adoption: agent searches, views tool detail (citation), no further search
    in same category within 30 minutes.
    Rejection: agent searches, views tool detail, searches same category again
    within 10 minutes.
    """
    # Get recent MCP searches that had results, grouped by api_key_id
    cursor = await db.execute("""
        SELECT sl.id, sl.query, sl.top_result_slug, sl.api_key_id, sl.created_at,
               t.category_id, t.slug as tool_slug
        FROM search_logs sl
        JOIN tools t ON sl.top_result_slug = t.slug
        WHERE sl.source = 'mcp'
          AND sl.api_key_id IS NOT NULL
          AND sl.result_count > 0
          AND sl.created_at >= datetime('now', ?)
        ORDER BY sl.api_key_id, sl.created_at
    """, (f'-{hours} hours',))
    searches = await cursor.fetchall()
    if not searches:
        return []

    signals = []
    for i, search in enumerate(searches):
        key_id = search['api_key_id']
        cat_id = search['category_id']
        ts = search['created_at']
        slug = search['tool_slug']

        # Check for citation (detail view) of the top result after this search
        cite_cursor = await db.execute("""
            SELECT 1 FROM agent_citations ac
            JOIN tools t ON ac.tool_id = t.id
            WHERE t.slug = ? AND ac.created_at >= ? AND ac.created_at <= datetime(?, '+30 minutes')
            LIMIT 1
        """, (slug, ts, ts))
        was_viewed = await cite_cursor.fetchone()
        if not was_viewed:
            continue

        # Check for follow-up search in same category by same key within 10 min
        followup_cursor = await db.execute("""
            SELECT 1 FROM search_logs sl2
            JOIN tools t2 ON sl2.top_result_slug = t2.slug
            WHERE sl2.api_key_id = ?
              AND t2.category_id = ?
              AND sl2.created_at > ?
              AND sl2.created_at <= datetime(?, '+10 minutes')
              AND sl2.id != ?
            LIMIT 1
        """, (key_id, cat_id, ts, ts, search['id']))
        followup = await followup_cursor.fetchone()

        if followup:
            signals.append({
                "tool_slug": slug, "signal_type": "implicit_rejection",
                "confidence": 0.7, "api_key_id": key_id, "timestamp": ts,
            })
        else:
            signals.append({
                "tool_slug": slug, "signal_type": "implicit_adoption",
                "confidence": 0.5, "api_key_id": key_id, "timestamp": ts,
            })

    return signals


async def aggregate_tool_signals(db: aiosqlite.Connection, tool_slug: str) -> dict:
    """Combined explicit + implicit outcome stats for a tool.

    Returns {explicit: {...}, implicit: {...}, combined: {...}, confidence: str}
    """
    explicit = await get_tool_success_rate(db, tool_slug)

    # Count implicit signals from recent agent behavior
    adopt_cursor = await db.execute("""
        SELECT COUNT(*) as cnt FROM search_logs sl
        JOIN tools t ON sl.top_result_slug = t.slug
        WHERE t.slug = ? AND sl.source = 'mcp' AND sl.result_count > 0
          AND sl.api_key_id IS NOT NULL
          AND sl.created_at >= datetime('now', '-90 days')
          AND NOT EXISTS (
              SELECT 1 FROM search_logs sl2
              JOIN tools t2 ON sl2.top_result_slug = t2.slug
              WHERE sl2.api_key_id = sl.api_key_id
                AND t2.category_id = t.category_id
                AND sl2.created_at > sl.created_at
                AND sl2.created_at <= datetime(sl.created_at, '+10 minutes')
                AND sl2.id != sl.id
          )
    """, (tool_slug,))
    adopt_row = await adopt_cursor.fetchone()
    implicit_adoptions = adopt_row['cnt'] if adopt_row else 0

    reject_cursor = await db.execute("""
        SELECT COUNT(*) as cnt FROM search_logs sl
        JOIN tools t ON sl.top_result_slug = t.slug
        WHERE t.slug = ? AND sl.source = 'mcp' AND sl.result_count > 0
          AND sl.api_key_id IS NOT NULL
          AND sl.created_at >= datetime('now', '-90 days')
          AND EXISTS (
              SELECT 1 FROM search_logs sl2
              JOIN tools t2 ON sl2.top_result_slug = t2.slug
              WHERE sl2.api_key_id = sl.api_key_id
                AND t2.category_id = t.category_id
                AND sl2.created_at > sl.created_at
                AND sl2.created_at <= datetime(sl.created_at, '+10 minutes')
                AND sl2.id != sl.id
          )
    """, (tool_slug,))
    reject_row = await reject_cursor.fetchone()
    implicit_rejections = reject_row['cnt'] if reject_row else 0

    implicit_total = implicit_adoptions + implicit_rejections
    implicit = {
        "adoptions": implicit_adoptions, "rejections": implicit_rejections,
        "total": implicit_total,
        "rate": round(implicit_adoptions / implicit_total * 100) if implicit_total else 0,
    }

    # Combine: explicit weight 1.0, implicit weight 0.6
    pos = explicit["success"] + (implicit_adoptions * 0.6)
    neg = explicit["fail"] + (implicit_rejections * 0.6)
    combined_total = pos + neg
    combined = {
        "positive": round(pos, 1), "negative": round(neg, 1),
        "total": round(combined_total, 1),
        "rate": round(pos / combined_total * 100) if combined_total else 0,
    }

    total_signals = explicit["total"] + implicit_total
    if total_signals >= 20:
        confidence = "high"
    elif total_signals >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    return {"explicit": explicit, "implicit": implicit, "combined": combined, "confidence": confidence}


async def update_api_key_scopes(db: aiosqlite.Connection, key_id: int, user_id: int, scopes: str) -> bool:
    """Update API key scopes. user_id check prevents cross-user modification."""
    if scopes not in ('read', 'read,write'):
        return False
    cursor = await db.execute(
        "UPDATE api_keys SET scopes = ? WHERE id = ? AND user_id = ?",
        (scopes, key_id, user_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def get_api_key_usage_stats(db: aiosqlite.Connection, user_id: int, days: int = 30) -> list[dict]:
    """Get usage stats per key for a user over the last N days."""
    cursor = await db.execute(
        "SELECT ak.id, ak.name, COUNT(al.id) as request_count "
        "FROM api_keys ak LEFT JOIN api_usage_logs al ON ak.id = al.key_id "
        "  AND al.created_at >= datetime('now', ?) "
        "WHERE ak.user_id = ? GROUP BY ak.id ORDER BY request_count DESC",
        (f"-{days} days", user_id),
    )
    return [dict(r) for r in await cursor.fetchall()]


# ── Tool Reactions ──────────────────────────────────────────────────

async def toggle_reaction(db, tool_id: int, reaction: str, user_id: int = None, session_id: str = None):
    """Toggle a reaction on/off. Returns {"toggled": bool, "count": int}."""
    if user_id:
        existing = await db.execute(
            "SELECT id FROM tool_reactions WHERE tool_id=? AND user_id=? AND reaction=?",
            (tool_id, user_id, reaction),
        )
    else:
        existing = await db.execute(
            "SELECT id FROM tool_reactions WHERE tool_id=? AND session_id=? AND reaction=?",
            (tool_id, session_id, reaction),
        )
    row = await existing.fetchone()
    if row:
        await db.execute("DELETE FROM tool_reactions WHERE id=?", (row["id"],))
        toggled = False
    else:
        await db.execute(
            "INSERT INTO tool_reactions (tool_id, user_id, session_id, reaction) VALUES (?,?,?,?)",
            (tool_id, user_id, session_id, reaction),
        )
        toggled = True
    await db.commit()
    count_row = await db.execute(
        "SELECT COUNT(*) as c FROM tool_reactions WHERE tool_id=? AND reaction=?",
        (tool_id, reaction),
    )
    count = (await count_row.fetchone())["c"]
    return {"toggled": toggled, "count": count}


async def get_reaction_counts(db, tool_id: int, user_id: int = None, session_id: str = None):
    """Get reaction counts + whether current user/session has reacted."""
    counts = {}
    for r in ("use_this", "bookmark"):
        row = await db.execute(
            "SELECT COUNT(*) as c FROM tool_reactions WHERE tool_id=? AND reaction=?",
            (tool_id, r),
        )
        counts[r] = (await row.fetchone())["c"]
    user_reactions = set()
    if user_id:
        rows = await db.execute(
            "SELECT reaction FROM tool_reactions WHERE tool_id=? AND user_id=?",
            (tool_id, user_id),
        )
        user_reactions = {r["reaction"] for r in await rows.fetchall()}
    elif session_id:
        rows = await db.execute(
            "SELECT reaction FROM tool_reactions WHERE tool_id=? AND session_id=?",
            (tool_id, session_id),
        )
        user_reactions = {r["reaction"] for r in await rows.fetchall()}
    return {"counts": counts, "user_reactions": user_reactions}


# ── Agent Memory: Developer Profiles ──────────────────────────

async def get_developer_profile(db, api_key_id: int) -> dict | None:
    """Get a developer's personalization profile."""
    cursor = await db.execute(
        "SELECT * FROM developer_profiles WHERE api_key_id = ?", (api_key_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def clear_developer_profile(db, api_key_id: int):
    """Clear personalization data but keep the profile row."""
    await db.execute(
        """UPDATE developer_profiles
           SET interests = '{}', tech_stack = '[]', favorite_tools = '[]',
               search_count = 0, last_rebuilt_at = NULL
           WHERE api_key_id = ?""", (api_key_id,))
    await db.commit()


async def toggle_personalization(db, api_key_id: int) -> bool:
    """Toggle personalization on/off. Returns new state."""
    cursor = await db.execute(
        "SELECT personalization_enabled FROM developer_profiles WHERE api_key_id = ?",
        (api_key_id,))
    row = await cursor.fetchone()
    if not row:
        return True
    new_state = 0 if row['personalization_enabled'] else 1
    await db.execute(
        "UPDATE developer_profiles SET personalization_enabled = ? WHERE api_key_id = ?",
        (new_state, api_key_id))
    await db.commit()
    return bool(new_state)


async def mark_notice_shown(db, api_key_id: int):
    """Mark that the first-search personalization notice has been shown."""
    await db.execute(
        "UPDATE developer_profiles SET notice_shown = 1 WHERE api_key_id = ?",
        (api_key_id,))
    await db.commit()


async def build_developer_profile(db, api_key_id: int) -> dict:
    """Build or rebuild a developer profile from their search history.

    Aggregates last 90 days of searches into:
    - interests: category slug -> confidence score (0-1)
    - tech_stack: list of inferred technology keywords
    - favorite_tools: list of tool slugs they interact with repeatedly
    """
    import json
    from collections import Counter

    # Get recent searches for this API key
    cursor = await db.execute(
        """SELECT query, top_result_slug, created_at,
                  julianday('now') - julianday(created_at) as days_ago
           FROM search_logs
           WHERE api_key_id = ? AND created_at >= datetime('now', '-90 days')
           ORDER BY created_at DESC""",
        (api_key_id,))
    searches = [dict(r) for r in await cursor.fetchall()]

    search_count = len(searches)
    if search_count == 0:
        return {'interests': {}, 'tech_stack': [], 'favorite_tools': [], 'search_count': 0}

    # Score categories from search queries using NEED_MAPPINGS
    category_scores = Counter()
    tech_found = Counter()
    tool_slugs = Counter()

    for s in searches:
        q = (s['query'] or '').lower()
        days = s['days_ago'] or 0

        # Recency weight: last 7 days = 3x, last 30 = 2x, older = 1x
        weight = 3.0 if days <= 7 else (2.0 if days <= 30 else 1.0)

        # Match against NEED_MAPPINGS keywords
        for keyword, mapping in NEED_MAPPINGS.items():
            terms = [keyword] + mapping.get('terms', [])
            for term in terms:
                if term.lower() in q:
                    category_scores[mapping['category']] += weight
                    break

        # Extract tech keywords
        for kw in TECH_KEYWORDS:
            if kw in q:
                tech_found[kw] += weight

        # Track tool slugs from top results
        if s['top_result_slug']:
            tool_slugs[s['top_result_slug']] += 1

    # Also check bookmarks for this user
    key_cursor = await db.execute(
        "SELECT user_id FROM api_keys WHERE id = ?", (api_key_id,))
    key_row = await key_cursor.fetchone()
    if key_row:
        user_id = key_row['user_id']
        wl_cursor = await db.execute(
            """SELECT t.slug, t.tags, c.slug as cat_slug
               FROM wishlists w
               JOIN tools t ON w.tool_id = t.id
               JOIN categories c ON t.category_id = c.id
               WHERE w.user_id = ?""", (user_id,))
        for row in await wl_cursor.fetchall():
            tool_slugs[row['slug']] += 2  # Bookmarks count more
            category_scores[row['cat_slug']] += 1.0
            # Infer tech from bookmarked tool names
            name_lower = row['slug'].replace('-', ' ')
            for kw in TECH_KEYWORDS:
                if kw in name_lower:
                    tech_found[kw] += 1.0

    # Normalize interests to 0-1 scale
    max_score = max(category_scores.values()) if category_scores else 1
    interests = {cat: round(score / max_score, 2) for cat, score in category_scores.most_common(10)}

    # Top 10 tech keywords
    tech_stack = [kw for kw, _ in tech_found.most_common(10)]

    # Favorite tools: appeared 2+ times
    favorite_tools = [slug for slug, count in tool_slugs.most_common(20) if count >= 2]

    # Upsert profile
    profile = await get_developer_profile(db, api_key_id)
    if profile:
        await db.execute(
            """UPDATE developer_profiles
               SET interests = ?, tech_stack = ?, favorite_tools = ?,
                   search_count = ?, last_rebuilt_at = CURRENT_TIMESTAMP
               WHERE api_key_id = ?""",
            (json.dumps(interests), json.dumps(tech_stack), json.dumps(favorite_tools),
             search_count, api_key_id))
    else:
        await db.execute(
            """INSERT INTO developer_profiles
               (api_key_id, interests, tech_stack, favorite_tools, search_count, last_rebuilt_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (api_key_id, json.dumps(interests), json.dumps(tech_stack),
             json.dumps(favorite_tools), search_count))
    await db.commit()

    return {'interests': interests, 'tech_stack': tech_stack,
            'favorite_tools': favorite_tools, 'search_count': search_count}


async def _get_visitor_profile(db, visitor_id: str):
    """Get an anonymous visitor's personalisation profile."""
    cursor = await db.execute(
        "SELECT * FROM visitor_profiles WHERE visitor_id = ?", (visitor_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def build_visitor_profile(db, visitor_id: str) -> dict:
    """Build a profile from anonymous search history (keyed on visitor_id).

    Same logic as build_developer_profile but uses visitor_id instead of api_key_id.
    Only builds after 10+ searches to avoid noise from drive-by visitors.
    """
    import json
    from collections import Counter

    cursor = await db.execute(
        """SELECT query, top_result_slug, created_at,
                  julianday('now') - julianday(created_at) as days_ago
           FROM search_logs
           WHERE visitor_id = ? AND created_at >= datetime('now', '-90 days')
           ORDER BY created_at DESC""",
        (visitor_id,))
    searches = [dict(r) for r in await cursor.fetchall()]

    search_count = len(searches)
    if search_count < 10:
        return {'interests': {}, 'tech_stack': [], 'favorite_tools': [], 'search_count': search_count}

    category_scores = Counter()
    tech_found = Counter()
    tool_slugs = Counter()

    for s in searches:
        q = (s['query'] or '').lower()
        days = s['days_ago'] or 0
        weight = 3.0 if days <= 7 else (2.0 if days <= 30 else 1.0)

        for keyword, mapping in NEED_MAPPINGS.items():
            terms = [keyword] + mapping.get('terms', [])
            for term in terms:
                if term.lower() in q:
                    category_scores[mapping['category']] += weight
                    break

        for kw in TECH_KEYWORDS:
            if kw in q:
                tech_found[kw] += weight

        if s['top_result_slug']:
            tool_slugs[s['top_result_slug']] += 1

    max_score = max(category_scores.values()) if category_scores else 1
    interests = {cat: round(score / max_score, 2) for cat, score in category_scores.most_common(10)}
    tech_stack = [kw for kw, _ in tech_found.most_common(10)]
    favorite_tools = [slug for slug, count in tool_slugs.most_common(20) if count >= 2]

    # Upsert visitor profile
    existing = await _get_visitor_profile(db, visitor_id)
    if existing:
        await db.execute(
            """UPDATE visitor_profiles
               SET interests = ?, tech_stack = ?, favorite_tools = ?,
                   search_count = ?, last_rebuilt_at = CURRENT_TIMESTAMP
               WHERE visitor_id = ?""",
            (json.dumps(interests), json.dumps(tech_stack), json.dumps(favorite_tools),
             search_count, visitor_id))
    else:
        await db.execute(
            """INSERT INTO visitor_profiles
               (visitor_id, interests, tech_stack, favorite_tools, search_count, last_rebuilt_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (visitor_id, json.dumps(interests), json.dumps(tech_stack),
             json.dumps(favorite_tools), search_count))
    await db.commit()

    return {'interests': interests, 'tech_stack': tech_stack,
            'favorite_tools': favorite_tools, 'search_count': search_count}


async def get_maker_query_intelligence(db, maker_id: int, days: int = 30) -> list:
    """Get search queries that surface a maker's tools, ranked by frequency.
    Note: top_result_slug/name are an arbitrary row from the group (SQLite behaviour).
    This is acceptable — shows a representative tool for each query."""
    cursor = await db.execute("""
        SELECT sl.query, COUNT(*) as count, sl.top_result_slug, sl.top_result_name
        FROM search_logs sl
        JOIN tools t ON sl.top_result_slug = t.slug
        WHERE t.maker_id = ?
          AND t.status = 'approved'
          AND sl.created_at >= datetime('now', ?)
          AND sl.query IS NOT NULL AND sl.query != ''
        GROUP BY LOWER(sl.query)
        ORDER BY count DESC
        LIMIT 15
    """, (maker_id, f'-{days} days'))
    return [dict(r) for r in await cursor.fetchall()]


async def get_maker_agent_breakdown(db, maker_id: int, days: int = 30) -> list:
    """Get breakdown of which agents/sources cite a maker's tools."""
    cursor = await db.execute("""
        SELECT ac.agent_name, COUNT(*) as count
        FROM agent_citations ac
        JOIN tools t ON ac.tool_id = t.id
        WHERE t.maker_id = ?
          AND t.status = 'approved'
          AND ac.created_at >= datetime('now', ?)
        GROUP BY ac.agent_name
        ORDER BY count DESC
    """, (maker_id, f'-{days} days'))
    return [dict(r) for r in await cursor.fetchall()]


async def get_demand_trends(db, days: int = 30) -> list:
    """Get demand signal trends over time — searches grouped by day."""
    cursor = await db.execute("""
        SELECT DATE(created_at) as day,
               COUNT(*) as total_searches,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) as zero_results
        FROM search_logs
        WHERE created_at >= datetime('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY day DESC
    """, (f'-{days} days',))
    return [dict(r) for r in await cursor.fetchall()]


async def get_demand_clusters(db, limit: int = 50) -> list:
    """Get clustered demand signals with richer metadata than basic gaps."""
    cursor = await db.execute("""
        SELECT LOWER(query) as query,
               COUNT(*) as search_count,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) as zero_count,
               MAX(created_at) as last_searched,
               MIN(created_at) as first_searched,
               COUNT(DISTINCT source) as source_count,
               GROUP_CONCAT(DISTINCT source) as sources
        FROM search_logs
        WHERE LENGTH(query) >= 3
          AND query NOT LIKE '%http%'
          AND query NOT LIKE '%.com%'
        GROUP BY LOWER(query)
        HAVING zero_count > 0
        ORDER BY zero_count DESC, search_count DESC
        LIMIT ?
    """, (limit,))
    return [dict(r) for r in await cursor.fetchall()]


async def get_demand_clusters_enriched(db, limit: int = 50) -> list:
    """Enriched demand clusters with opportunity score, competitor density, and sparkline data."""
    from datetime import date, timedelta

    cursor = await db.execute("""
        SELECT LOWER(TRIM(query)) as query,
               COUNT(*) as search_count,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) as zero_count,
               MAX(created_at) as last_searched,
               MIN(created_at) as first_searched,
               COUNT(DISTINCT source) as source_count,
               GROUP_CONCAT(DISTINCT source) as sources
        FROM search_logs
        WHERE LENGTH(TRIM(query)) >= 3
          AND query NOT LIKE '%http%'
          AND query NOT LIKE '%.com%'
        GROUP BY LOWER(TRIM(query))
        HAVING zero_count > 0
        ORDER BY zero_count DESC, search_count DESC
        LIMIT ?
    """, (limit,))
    clusters = [dict(r) for r in await cursor.fetchall()]

    for c in clusters:
        sc = max(c['search_count'], 1)
        c['opportunity_score'] = round(c['zero_count'] * (1 + c['zero_count'] / sc), 1)

        q_like = f"%{c['query']}%"
        cur2 = await db.execute(
            """SELECT COUNT(*) as cnt FROM tools
               WHERE status = 'approved'
               AND (LOWER(name) LIKE ? OR LOWER(tagline) LIKE ? OR LOWER(tags) LIKE ?)""",
            (q_like, q_like, q_like),
        )
        row = await cur2.fetchone()
        c['competitor_density'] = row['cnt'] if row else 0

        cur3 = await db.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as cnt
               FROM search_logs
               WHERE LOWER(TRIM(query)) = ?
                 AND created_at >= datetime('now', '-14 days')
               GROUP BY DATE(created_at)
               ORDER BY day""",
            (c['query'],),
        )
        day_rows = await cur3.fetchall()
        day_map = {r['day']: r['cnt'] for r in day_rows}
        today = date.today()
        c['daily_counts'] = [day_map.get((today - timedelta(days=13 - i)).isoformat(), 0) for i in range(14)]

    clusters.sort(key=lambda c: c['opportunity_score'], reverse=True)
    return clusters


async def get_maker_daily_trend(db, maker_id: int, days: int = 30) -> list:
    """Get daily citation counts for trend chart."""
    cursor = await db.execute("""
        SELECT
            DATE(ac.created_at) as day,
            COUNT(*) as citations
        FROM agent_citations ac
        JOIN tools t ON ac.tool_id = t.id
        WHERE t.maker_id = ?
          AND ac.created_at >= datetime('now', ?)
        GROUP BY DATE(ac.created_at)
        ORDER BY day ASC
    """, (maker_id, f'-{days} days'))
    return [dict(r) for r in await cursor.fetchall()]


async def get_listing_quality_score(db, tool: dict) -> dict:
    """Compute listing quality score (0-100) with breakdown."""
    # Metadata completeness (40% weight)
    metadata_fields = [
        ('description', bool(tool.get('description', '').strip())),
        ('tags', bool(tool.get('tags', '').strip())),
        ('api_type', bool(tool.get('api_type', '').strip())),
        ('auth_method', bool(tool.get('auth_method', '').strip())),
        ('install_command', bool(tool.get('install_command', '').strip())),
        ('agent_instructions', bool(tool.get('agent_instructions', '').strip())),
    ]
    filled = sum(1 for _, has in metadata_fields if has)
    metadata_score = filled / len(metadata_fields) * 100

    # Success rate (35% weight) — only if we have data
    sr = await get_tool_success_rate(db, tool['slug'])
    if sr['total'] > 0:
        success_score = sr['rate']
    else:
        success_score = 50  # Neutral when no data

    # Freshness (25% weight) — proxy via metadata completeness
    # Real freshness would need an updated_at column
    freshness_score = metadata_score

    total = round(metadata_score * 0.40 + success_score * 0.35 + freshness_score * 0.25)

    missing = [name for name, has in metadata_fields if not has]

    return {
        'score': min(total, 100),
        'metadata_score': round(metadata_score),
        'success_score': round(success_score),
        'freshness_score': round(freshness_score),
        'missing_fields': missing,
        'tips': _quality_tips(missing, sr['total']),
    }


def _quality_tips(missing: list, outcome_count: int) -> list[str]:
    """Generate actionable tips to improve listing quality."""
    tips = []
    if 'agent_instructions' in missing:
        tips.append('Add Agent Instructions to tell AI agents exactly how to implement your tool')
    if 'install_command' in missing:
        tips.append('Add an install command so agents can set up your tool automatically')
    if 'api_type' in missing:
        tips.append('Specify your API type (REST, GraphQL, SDK, CLI)')
    if 'tags' in missing:
        tips.append('Add tags to help agents find your tool for the right queries')
    if 'description' in missing:
        tips.append('Write a description — agents use this to decide whether to recommend you')
    if 'auth_method' in missing:
        tips.append('Specify your auth method so agents can generate correct setup code')
    if outcome_count == 0:
        tips.append('No outcome data yet — agents will report success/failure as they recommend your tool')
    return tips[:3]  # Top 3 most impactful


async def get_batch_success_rates(db: aiosqlite.Connection, tool_slugs: list[str]) -> dict[str, dict]:
    """Get success rates for multiple tools in one query. Returns {slug: {success, fail, total, rate}}."""
    if not tool_slugs:
        return {}
    placeholders = ",".join("?" for _ in tool_slugs)
    cursor = await db.execute(
        f"SELECT tool_slug, success, COUNT(*) as cnt FROM agent_actions WHERE tool_slug IN ({placeholders}) AND action = 'report_outcome' GROUP BY tool_slug, success",
        tool_slugs,
    )
    rows = await cursor.fetchall()
    result: dict[str, dict] = {}
    for r in rows:
        slug = r['tool_slug']
        if slug not in result:
            result[slug] = {"success": 0, "fail": 0, "total": 0, "rate": 0}
        if r['success'] == 1:
            result[slug]["success"] += r['cnt']
        else:
            result[slug]["fail"] += r['cnt']
    for slug, data in result.items():
        data["total"] = data["success"] + data["fail"]
        data["rate"] = round(data["success"] / data["total"] * 100) if data["total"] else 0
    return result


async def get_outcome_stats(db: aiosqlite.Connection) -> dict:
    """Get aggregate outcome report statistics for the admin trust layer dashboard."""
    # Total outcomes all time
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_actions WHERE action = 'report_outcome'"
    )
    total_all = (await cursor.fetchone())['cnt']

    # Total outcomes last 30 days
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_actions WHERE action = 'report_outcome' AND created_at >= datetime('now', '-30 days')"
    )
    total_30d = (await cursor.fetchone())['cnt']

    # Unique tools with outcome data
    cursor = await db.execute(
        "SELECT COUNT(DISTINCT tool_slug) as cnt FROM agent_actions WHERE action = 'report_outcome'"
    )
    unique_tools = (await cursor.fetchone())['cnt']

    # Average success rate across all tools with data
    cursor = await db.execute(
        "SELECT tool_slug, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as wins, COUNT(*) as total FROM agent_actions WHERE action = 'report_outcome' GROUP BY tool_slug"
    )
    tool_rows = await cursor.fetchall()
    if tool_rows:
        rates = [round(r['wins'] / r['total'] * 100) for r in tool_rows if r['total'] > 0]
        avg_rate = round(sum(rates) / len(rates)) if rates else 0
    else:
        avg_rate = 0

    # Top 10 most-reported tools with their success rates
    cursor = await db.execute("""
        SELECT aa.tool_slug, t.name,
               SUM(CASE WHEN aa.success = 1 THEN 1 ELSE 0 END) as wins,
               COUNT(*) as total
        FROM agent_actions aa
        LEFT JOIN tools t ON t.slug = aa.tool_slug
        WHERE aa.action = 'report_outcome'
        GROUP BY aa.tool_slug
        ORDER BY total DESC
        LIMIT 10
    """)
    top_tools = [dict(r) for r in await cursor.fetchall()]
    for t in top_tools:
        t['rate'] = round(t['wins'] / t['total'] * 100) if t['total'] > 0 else 0

    return {
        "total_all": total_all,
        "total_30d": total_30d,
        "unique_tools": unique_tools,
        "avg_rate": avg_rate,
        "top_tools": top_tools,
    }


# ── Community Flags ──────────────────────────────────────────────────────

async def create_tool_flag(db: aiosqlite.Connection, tool_id: int, user_id: int,
                           flag_type: str, note: str = '') -> bool:
    """Create a community flag on a tool. Returns True if created, False if duplicate."""
    try:
        await db.execute(
            "INSERT INTO tool_flags (tool_id, user_id, flag_type, note) VALUES (?, ?, ?, ?)",
            (tool_id, user_id, flag_type, note),
        )
        await db.commit()
        return True
    except Exception:
        return False


async def get_flags_for_tool(db: aiosqlite.Connection, tool_id: int):
    cursor = await db.execute(
        """SELECT tf.*, u.name as user_name, u.email as user_email
           FROM tool_flags tf JOIN users u ON tf.user_id = u.id
           WHERE tf.tool_id = ? ORDER BY tf.created_at DESC""",
        (tool_id,),
    )
    return await cursor.fetchall()


async def get_flagged_tools(db: aiosqlite.Connection):
    """Get tools with community flags, ordered by flag count."""
    cursor = await db.execute(
        """SELECT t.id, t.name, t.slug, t.status,
                  COUNT(tf.id) as flag_count,
                  GROUP_CONCAT(DISTINCT tf.flag_type) as flag_types
           FROM tool_flags tf
           JOIN tools t ON tf.tool_id = t.id
           GROUP BY t.id
           ORDER BY flag_count DESC"""
    )
    return await cursor.fetchall()


async def get_pro_users_with_makers(db) -> list:
    """Get all Pro users who have maker accounts, for weekly report emails."""
    cursor = await db.execute("""
        SELECT u.id as user_id, u.email, u.username, u.maker_id,
               m.name as maker_name
        FROM users u
        JOIN subscriptions s ON s.user_id = u.id AND s.status = 'active'
        LEFT JOIN makers m ON u.maker_id = m.id
        WHERE u.email IS NOT NULL AND u.email != ''
    """)
    return [dict(r) for r in await cursor.fetchall()]


async def get_weekly_citations_by_maker(db, maker_id: int) -> dict:
    """Get citation stats for a maker over the past 7 days."""
    # Total citations
    cursor = await db.execute("""
        SELECT COUNT(*) as total
        FROM agent_citations ac
        JOIN tools t ON ac.tool_id = t.id
        WHERE t.maker_id = ? AND ac.created_at >= datetime('now', '-7 days')
    """, (maker_id,))
    total_row = await cursor.fetchone()
    total = total_row['total'] if total_row else 0

    # Top cited tool
    cursor = await db.execute("""
        SELECT t.name, t.slug, COUNT(*) as cnt
        FROM agent_citations ac
        JOIN tools t ON ac.tool_id = t.id
        WHERE t.maker_id = ? AND ac.created_at >= datetime('now', '-7 days')
        GROUP BY t.id
        ORDER BY cnt DESC
        LIMIT 1
    """, (maker_id,))
    top_tool = await cursor.fetchone()

    # Agent breakdown
    cursor = await db.execute("""
        SELECT COALESCE(ac.agent_name, 'unknown') as agent_name, COUNT(*) as count
        FROM agent_citations ac
        JOIN tools t ON ac.tool_id = t.id
        WHERE t.maker_id = ? AND ac.created_at >= datetime('now', '-7 days')
        GROUP BY ac.agent_name
        ORDER BY count DESC
    """, (maker_id,))
    agents = [dict(r) for r in await cursor.fetchall()]

    return {
        'total': total,
        'top_tool_name': top_tool['name'] if top_tool else None,
        'top_tool_slug': top_tool['slug'] if top_tool else None,
        'top_tool_citations': top_tool['cnt'] if top_tool else 0,
        'agents': agents,
    }


async def get_new_tools_in_maker_categories(db, maker_id: int, days: int = 7) -> list:
    """Get new tools added to the same categories as a maker's tools in the past N days."""
    cursor = await db.execute("""
        SELECT DISTINCT t2.name, t2.slug, t2.tagline
        FROM tools t1
        JOIN tools t2 ON t2.category_id = t1.category_id
        WHERE t1.maker_id = ?
          AND t2.maker_id != ?
          AND t2.status = 'approved'
          AND t2.created_at >= datetime('now', ?)
        ORDER BY t2.created_at DESC
        LIMIT 5
    """, (maker_id, maker_id, f'-{days} days'))
    return [dict(r) for r in await cursor.fetchall()]


# ── Arena (Roast My Stack) ────────────────────────────────────────────────


async def create_stack_roast(db, user_id: int, stack_name: str, stack_json: str, ai_roast_text: str) -> int:
    """Create a new stack roast and return its ID."""
    cursor = await db.execute(
        "INSERT INTO stack_roasts (user_id, stack_name, stack_json, ai_roast_text) VALUES (?, ?, ?, ?)",
        (user_id, stack_name, stack_json, ai_roast_text))
    await db.commit()
    return cursor.lastrowid


async def get_arena_feed(db, limit: int = 50) -> list:
    """Get arena feed sorted by upvotes."""
    cursor = await db.execute("""
        SELECT sr.*, u.name as author_name
        FROM stack_roasts sr
        JOIN users u ON sr.user_id = u.id
        ORDER BY sr.upvotes DESC, sr.created_at DESC
        LIMIT ?
    """, (limit,))
    return [dict(r) for r in await cursor.fetchall()]


async def get_roast_details(db, roast_id: int):
    """Get a single roast with its comments. Returns (roast_dict, comments_list) or (None, [])."""
    cursor = await db.execute("""
        SELECT sr.*, u.name as author_name
        FROM stack_roasts sr
        JOIN users u ON sr.user_id = u.id
        WHERE sr.id = ?
    """, (roast_id,))
    roast = await cursor.fetchone()
    if not roast:
        return None, []
    roast = dict(roast)
    cursor = await db.execute("""
        SELECT rc.*, u.name as author_name
        FROM roast_comments rc
        JOIN users u ON rc.user_id = u.id
        WHERE rc.roast_id = ?
        ORDER BY rc.created_at ASC
    """, (roast_id,))
    comments = [dict(r) for r in await cursor.fetchall()]
    return roast, comments


async def add_roast_comment(db, roast_id: int, user_id: int, comment_text: str):
    """Add a comment to a roast."""
    await db.execute(
        "INSERT INTO roast_comments (roast_id, user_id, comment_text) VALUES (?, ?, ?)",
        (roast_id, user_id, comment_text))
    await db.commit()


async def toggle_roast_upvote(db, roast_id: int, user_id: int) -> bool:
    """Toggle upvote on a roast. Returns True if upvoted, False if removed."""
    try:
        await db.execute(
            "INSERT INTO roast_upvotes (user_id, roast_id) VALUES (?, ?)",
            (user_id, roast_id))
        await db.execute(
            "UPDATE stack_roasts SET upvotes = upvotes + 1 WHERE id = ?",
            (roast_id,))
        await db.commit()
        return True
    except Exception:
        await db.execute(
            "DELETE FROM roast_upvotes WHERE user_id = ? AND roast_id = ?",
            (user_id, roast_id))
        await db.execute(
            "UPDATE stack_roasts SET upvotes = MAX(0, upvotes - 1) WHERE id = ?",
            (roast_id,))
        await db.commit()
        return False


async def has_user_upvoted_roast(db, roast_id: int, user_id: int) -> bool:
    """Check if a user has upvoted a specific roast."""
    cursor = await db.execute(
        "SELECT 1 FROM roast_upvotes WHERE user_id = ? AND roast_id = ?",
        (user_id, roast_id))
    return await cursor.fetchone() is not None


async def get_tool_analytics_wall_data(db, tool_slug: str, tool_id: int, detailed: bool = False) -> dict:
    """Get aggregated AI agent usage stats for the claim-to-reveal analytics wall.
    Returns safe aggregate totals always; detailed breakdowns only when detailed=True."""
    # Aggregate totals from search_logs (agent/MCP queries that surfaced this tool)
    cursor = await db.execute("""
        SELECT
            COUNT(*) as total_agent_queries,
            COUNT(DISTINCT agent_client) as unique_platforms,
            SUM(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 ELSE 0 END) as queries_last_7d
        FROM search_logs
        WHERE top_result_slug = ?
          AND source IN ('api', 'mcp')
    """, (tool_slug,))
    row = await cursor.fetchone()
    stats = dict(row) if row else {'total_agent_queries': 0, 'unique_platforms': 0, 'queries_last_7d': 0}

    # Total citations from agent_citations
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_citations WHERE tool_id = ?", (tool_id,))
    cit_row = await cursor.fetchone()
    stats['total_citations'] = cit_row['cnt'] if cit_row else 0

    if not detailed:
        stats['platform_breakdown'] = []
        stats['top_queries'] = []
        stats['daily_trend'] = []
        return stats

    # Platform breakdown
    cursor = await db.execute("""
        SELECT COALESCE(agent_client, 'Unknown') as platform, COUNT(*) as count
        FROM search_logs
        WHERE top_result_slug = ? AND source IN ('api', 'mcp')
        GROUP BY COALESCE(agent_client, 'Unknown')
        ORDER BY count DESC
    """, (tool_slug,))
    stats['platform_breakdown'] = [dict(r) for r in await cursor.fetchall()]

    # Top queries leading to this tool
    cursor = await db.execute("""
        SELECT query, COUNT(*) as count, MAX(created_at) as last_seen
        FROM search_logs
        WHERE top_result_slug = ?
          AND source IN ('api', 'mcp')
          AND query IS NOT NULL AND query != ''
        GROUP BY LOWER(query)
        ORDER BY count DESC
        LIMIT 10
    """, (tool_slug,))
    stats['top_queries'] = [dict(r) for r in await cursor.fetchall()]

    # Daily trend (last 30 days)
    cursor = await db.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM search_logs
        WHERE top_result_slug = ? AND source IN ('api', 'mcp')
          AND created_at >= datetime('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY day ASC
    """, (tool_slug,))
    stats['daily_trend'] = [dict(r) for r in await cursor.fetchall()]

    return stats


async def get_maker_follow_up_data(db: aiosqlite.Connection, tool_id: int) -> dict | None:
    """Return data for maker follow-up emails.

    Powers:
    - Day 3 email: quality score + how to improve
    - Day 7 email: agent recommendation count + top search queries
    """
    cursor = await db.execute(
        """SELECT name, slug, quality_score, mcp_view_count, sdk_packages
           FROM tools WHERE id = ?""",
        (tool_id,),
    )
    tool = await cursor.fetchone()
    if not tool:
        return None

    slug = tool["slug"]
    sdk = tool["sdk_packages"] or ""
    tool_packages = [p.strip() for p in sdk.split(",") if p.strip()]
    tool_packages.append(slug)
    placeholders = ",".join("?" * len(tool_packages))

    result = {
        "name": tool["name"],
        "slug": slug,
        "quality_score": round(float(tool["quality_score"] or 0.0), 2),
        "mcp_view_count": int(tool["mcp_view_count"] or 0),
    }

    # Repos that migrated TO this tool
    cursor = await db.execute(
        f"SELECT COUNT(DISTINCT repo) as n FROM migration_paths WHERE to_package IN ({placeholders})",
        tool_packages,
    )
    row = await cursor.fetchone()
    result["migration_repos_gained"] = int(row["n"] or 0) if row else 0

    # Verified combos count
    cursor = await db.execute(
        f"""SELECT COUNT(DISTINCT repo) as n FROM verified_combos
            WHERE package_a IN ({placeholders}) OR package_b IN ({placeholders})""",
        tool_packages + tool_packages,
    )
    row = await cursor.fetchone()
    result["verified_combos_count"] = int(row["n"] or 0) if row else 0

    # Top search queries this tool appeared as top result (last 30 days)
    cursor = await db.execute(
        """SELECT query, COUNT(*) as count FROM search_logs
           WHERE top_result_slug = ? AND source IN ('api', 'mcp')
             AND created_at >= datetime('now', '-30 days')
             AND query IS NOT NULL AND query != ''
           GROUP BY LOWER(query)
           ORDER BY count DESC
           LIMIT 5""",
        (slug,),
    )
    result["top_search_queries"] = [
        {"query": r["query"], "count": r["count"]}
        for r in await cursor.fetchall()
    ]

    return result


# ── MCP Session Tracking ─────────────────────────────────────────────────

async def log_mcp_query(
    db: aiosqlite.Connection,
    session_id: str,
    query: str,
    category: str,
    tools_returned: list,
    outcome: str = "unknown",
) -> None:
    """Log a find_tools call. outcome=gap if no results, unknown otherwise (backfilled to adopted/bounce later)."""
    import time as _time
    import json as _json

    if session_id:
        await db.execute(
            """INSERT INTO mcp_sessions (id, created_at, query_count)
               VALUES (?, ?, 1)
               ON CONFLICT(id) DO UPDATE SET query_count = query_count + 1""",
            (session_id, int(_time.time())),
        )

    await db.execute(
        """INSERT INTO mcp_query_outcomes
               (session_id, query, category, tools_returned, outcome, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            session_id or None,
            query,
            category or None,
            _json.dumps(tools_returned) if tools_returned else "[]",
            outcome,
            int(_time.time()),
        ),
    )
    await db.commit()


async def backfill_mcp_adoption(
    db: aiosqlite.Connection,
    session_id: str,
    slug: str,
) -> None:
    """When get_tool_details is called, mark the most recent find_tools call in the
    same session as 'adopted' if the slug was in tools_returned."""
    import json as _json

    if not session_id:
        return

    cursor = await db.execute(
        """SELECT id, tools_returned FROM mcp_query_outcomes
           WHERE session_id = ? AND outcome IN ('unknown', 'bounce')
           ORDER BY created_at DESC LIMIT 1""",
        (session_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return

    try:
        slugs = _json.loads(row["tools_returned"] or "[]")
    except Exception:
        slugs = []

    if slug in slugs:
        await db.execute(
            "UPDATE mcp_query_outcomes SET adopted_slug = ?, outcome = 'adopted' WHERE id = ?",
            (slug, row["id"]),
        )
        await db.commit()


async def get_mcp_quality_stats(db: aiosqlite.Connection) -> dict:
    """Aggregate session tracking stats for /api/quality."""

    def _tokens_for_rows(rows) -> int:
        total = 0
        for r in rows:
            cost = CATEGORY_TOKEN_COSTS.get(r["category"] or "", 15_000)
            total += cost
        return total

    cursor = await db.execute(
        """SELECT category FROM mcp_query_outcomes
           WHERE outcome = 'adopted' AND created_at >= strftime('%s', 'now', '-7 days')""",
    )
    adopted_7d = await cursor.fetchall()

    cursor = await db.execute(
        """SELECT category FROM mcp_query_outcomes
           WHERE outcome = 'adopted' AND created_at >= strftime('%s', 'now', '-30 days')""",
    )
    adopted_30d = await cursor.fetchall()

    tokens_7d = _tokens_for_rows(adopted_7d)
    tokens_30d = _tokens_for_rows(adopted_30d)

    cursor = await db.execute(
        """SELECT outcome, COUNT(*) as cnt FROM mcp_query_outcomes
           WHERE outcome IN ('adopted', 'bounce')
             AND created_at >= strftime('%s', 'now', '-7 days')
           GROUP BY outcome""",
    )
    rate_rows = {r["outcome"]: r["cnt"] for r in await cursor.fetchall()}
    adopted_n = rate_rows.get("adopted", 0)
    bounce_n = rate_rows.get("bounce", 0)
    adoption_rate = round(adopted_n / (adopted_n + bounce_n), 3) if (adopted_n + bounce_n) > 0 else None

    cursor = await db.execute(
        """SELECT COUNT(*) as total,
                  SUM(CASE WHEN outcome = 'gap' THEN 1 ELSE 0 END) as gaps
           FROM mcp_query_outcomes
           WHERE created_at >= strftime('%s', 'now', '-7 days')""",
    )
    gr = await cursor.fetchone()
    total_n = gr["total"] if gr else 0
    gaps_n = gr["gaps"] if gr else 0
    gap_rate = round(gaps_n / total_n, 3) if total_n > 0 else None

    cursor = await db.execute(
        """SELECT query, COUNT(*) as cnt FROM mcp_query_outcomes
           WHERE outcome = 'gap' AND created_at >= strftime('%s', 'now', '-7 days')
             AND query IS NOT NULL AND query != ''
           GROUP BY LOWER(query)
           ORDER BY cnt DESC LIMIT 10""",
    )
    gap_queries = [r["query"] for r in await cursor.fetchall()]

    cursor = await db.execute(
        """SELECT COUNT(DISTINCT session_id) as cnt FROM mcp_query_outcomes
           WHERE session_id IS NOT NULL
             AND created_at >= strftime('%s', 'now', '-7 days')""",
    )
    sess_row = await cursor.fetchone()
    session_count = sess_row["cnt"] if sess_row else 0

    return {
        "tokens_saved_7d": tokens_7d,
        "tokens_saved_30d": tokens_30d,
        "adoption_rate_7d": adoption_rate,
        "gap_rate_7d": gap_rate,
        "top_gap_queries": gap_queries,
        "session_count_7d": session_count,
    }


# ── Agent Services (agent-to-agent procurement) ────────────────────────

async def create_agent_service(db: aiosqlite.Connection, *, name: str, tagline: str,
                                description: str = '', capability_tags: str = '',
                                category_id: int = None, input_schema: str = '{}',
                                output_schema: str = '{}', delivery_types: str = 'inline_json',
                                estimated_sla_minutes: int = 5, cost_estimate_cents: int = None,
                                cost_unit: str = 'per_task', url: str = None,
                                github_url: str = None, source_type: str = 'saas',
                                maker_id: int = None) -> int:
    """Create a new agent service listing."""
    slug = slugify(name)
    cursor = await db.execute(
        """INSERT INTO agent_services
           (slug, name, tagline, description, capability_tags, category_id,
            input_schema, output_schema, delivery_types, estimated_sla_minutes,
            cost_estimate_cents, cost_unit, url, github_url, source_type, maker_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (slug, name, tagline, description, capability_tags, category_id,
         input_schema, output_schema, delivery_types, estimated_sla_minutes,
         cost_estimate_cents, cost_unit, url, github_url, source_type, maker_id),
    )
    await db.commit()
    return cursor.lastrowid


async def get_agent_service_by_slug(db: aiosqlite.Connection, slug: str):
    """Get an approved agent service by slug."""
    cursor = await db.execute(
        "SELECT * FROM agent_services WHERE slug = ? AND status = 'approved'", (slug,))
    return await cursor.fetchone()


async def get_agent_service_by_slug_any(db: aiosqlite.Connection, slug: str):
    """Get an agent service by slug regardless of status (for admin/callbacks)."""
    cursor = await db.execute(
        "SELECT * FROM agent_services WHERE slug = ?", (slug,))
    return await cursor.fetchone()


async def search_agent_services(db: aiosqlite.Connection, capability: str, *,
                                 max_sla: int = 0, max_cost: int = 0,
                                 source_type: str = 'all', limit: int = 10, offset: int = 0):
    """Search agent services by capability. Returns list of matching services."""
    where = ["status = 'approved'"]
    params = []
    if capability:
        terms = [t.strip().lower() for t in capability.split() if t.strip()]
        for term in terms:
            where.append("LOWER(capability_tags || ' ' || name || ' ' || tagline) LIKE ?")
            params.append(f"%{term}%")
    if max_sla > 0:
        where.append("estimated_sla_minutes <= ?")
        params.append(max_sla)
    if max_cost > 0:
        where.append("(cost_estimate_cents IS NULL OR cost_estimate_cents <= ?)")
        params.append(max_cost)
    if source_type != 'all':
        where.append("source_type = ?")
        params.append(source_type)
    params.extend([limit, offset])
    cursor = await db.execute(
        f"SELECT * FROM agent_services WHERE {' AND '.join(where)} "
        f"ORDER BY quality_score DESC, success_count DESC LIMIT ? OFFSET ?",
        params)
    return await cursor.fetchall()


async def get_all_agent_services(db: aiosqlite.Connection, *, status: str = 'approved',
                                  limit: int = 50, offset: int = 0):
    """Get all agent services with given status."""
    cursor = await db.execute(
        "SELECT * FROM agent_services WHERE status = ? "
        "ORDER BY quality_score DESC LIMIT ? OFFSET ?",
        (status, limit, offset))
    return await cursor.fetchall()


async def increment_agent_timeout(db: aiosqlite.Connection, agent_slug: str):
    """Increment timeout count and recalculate timeout_rate."""
    await db.execute(
        "UPDATE agent_services SET timeout_count = timeout_count + 1, "
        "timeout_rate = CAST(timeout_count + 1 AS REAL) / MAX(success_count + timeout_count + 1, 1), "
        "updated_at = CURRENT_TIMESTAMP WHERE slug = ?", (agent_slug,))
    await db.commit()


async def increment_agent_success(db: aiosqlite.Connection, agent_slug: str):
    """Increment success count and recalculate timeout_rate."""
    await db.execute(
        "UPDATE agent_services SET success_count = success_count + 1, "
        "timeout_rate = CAST(timeout_count AS REAL) / MAX(success_count + timeout_count + 1, 1), "
        "updated_at = CURRENT_TIMESTAMP WHERE slug = ?", (agent_slug,))
    await db.commit()


# ── Agent Contracts (agent-to-agent procurement) ───────────────────────

async def create_agent_contract(db: aiosqlite.Connection, *, contract_id: str,
                                 host_user_id: int = None, host_session_id: str = None,
                                 host_api_key_id: int = None, hired_agent_slug: str,
                                 input_payload: str = '{}', sla_deadline_at: str = None,
                                 cost_estimate_cents: int = None):
    await db.execute(
        """INSERT INTO agent_contracts
           (id, host_user_id, host_session_id, host_api_key_id, hired_agent_slug,
            input_payload, status, sla_deadline_at, cost_estimate_cents)
           VALUES (?,?,?,?,?,?,'pending',?,?)""",
        (contract_id, host_user_id, host_session_id, host_api_key_id,
         hired_agent_slug, input_payload, sla_deadline_at, cost_estimate_cents))
    await db.commit()


async def update_contract_status(db: aiosqlite.Connection, contract_id: str,
                                  status: str, **kwargs):
    sets = ["status = ?", "status_changed_at = CURRENT_TIMESTAMP"]
    params = [status]
    for key, val in kwargs.items():
        sets.append(f"{key} = ?")
        params.append(val)
    params.append(contract_id)
    await db.execute(
        f"UPDATE agent_contracts SET {', '.join(sets)} WHERE id = ?", params)
    await db.commit()


async def get_agent_contracts(db: aiosqlite.Connection, *, host_user_id: int = None,
                               host_session_id: str = None, contract_id: str = None,
                               status: str = None, limit: int = 20):
    where = []
    params = []
    if contract_id:
        where.append("id = ?"); params.append(contract_id)
    if host_user_id:
        where.append("host_user_id = ?"); params.append(host_user_id)
    if host_session_id:
        where.append("host_session_id = ?"); params.append(host_session_id)
    if status:
        where.append("status = ?"); params.append(status)
    where_str = f"WHERE {' AND '.join(where)}" if where else ""
    params.append(limit)
    cursor = await db.execute(
        f"SELECT * FROM agent_contracts {where_str} ORDER BY created_at DESC LIMIT ?",
        params)
    return await cursor.fetchall()


async def get_expired_contracts(db: aiosqlite.Connection):
    cursor = await db.execute(
        "SELECT id, hired_agent_slug FROM agent_contracts "
        "WHERE status = 'processing' AND sla_deadline_at < datetime('now')")
    return await cursor.fetchall()


async def rate_agent_delivery(db: aiosqlite.Connection, contract_id: str,
                               useful: bool, notes: str = ''):
    """Rate a delivered contract. Updates contract and agent quality score."""
    contracts = await get_agent_contracts(db, contract_id=contract_id)
    if not contracts:
        return False
    contract = contracts[0]
    if contract["status"] != "delivered":
        return False

    # Update contract
    await db.execute(
        "UPDATE agent_contracts SET outcome_useful = ?, outcome_notes = ? WHERE id = ?",
        (1 if useful else 0, notes, contract_id))

    # Update agent service counters
    if useful:
        await db.execute(
            "UPDATE agent_services SET useful_count = useful_count + 1, "
            "quality_score = MIN(100, quality_score + 2), "
            "updated_at = CURRENT_TIMESTAMP WHERE slug = ?",
            (contract["hired_agent_slug"],))
    else:
        await db.execute(
            "UPDATE agent_services SET not_useful_count = not_useful_count + 1, "
            "quality_score = MAX(0, quality_score - 5), "
            "updated_at = CURRENT_TIMESTAMP WHERE slug = ?",
            (contract["hired_agent_slug"],))
    await db.commit()
    return True
