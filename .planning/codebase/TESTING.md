# Testing Patterns

**Analysis Date:** 2026-03-13

## Test Framework

**Runner:**
- No test framework installed (no pytest, unittest runner, or vitest)
- Only testing tool is a custom HTTP smoke test: `smoke_test.py`
- Uses Python stdlib only (`urllib.request`, `json`, `sys`, `time`)

**Assertion Library:**
- No assertion library -- smoke test uses status code comparison and substring/callable checks

**Run Commands:**
```bash
python smoke_test.py                          # Run against production (indiestack.ai)
python smoke_test.py http://localhost:8080     # Run against local server
```

## Test File Organization

**Location:**
- Single test file at project root: `smoke_test.py`
- No test directory, no `tests/` folder
- No unit tests, no integration tests beyond the smoke test

**Naming:**
- `smoke_test.py` -- the only test file

## Test Structure

**Suite Organization:**
```python
# smoke_test.py uses a flat list of test tuples
TESTS = [
    # (method, path, expected_status, label)
    ("GET", "/", 200, "Landing"),
    ("GET", "/explore", 200, "Explore"),
    ("GET", "/new", 302, "New tools redirect"),
    ("GET", "/search?q=analytics", 200, "Search"),
    # ... 37 total endpoint checks
]

# Content checks: path -> (substring_or_callable, description)
CONTENT_CHECKS = {
    "/": ("IndieStack", "page contains 'IndieStack'"),
    "/health": (lambda body: json.loads(body).get("status") == "ok", "returns {\"status\": \"ok\"}"),
    "/sitemap.xml": ("<urlset", "contains <urlset"),
    "/api/tools/search?q=email": (lambda body: "tools" in json.loads(body), "JSON has 'tools' key"),
}
```

**Patterns:**
- Each test is a tuple: `(HTTP_method, path, expected_status_code, label)`
- Expected status can be int or list of ints (for endpoints that may redirect): `[200, 303]`
- Content checks are optional -- only 5 endpoints have content validation
- Tests run sequentially against a live server (not mocked)
- No setup/teardown, no fixtures, no database seeding for tests

## Smoke Test Details

**What it covers (37 endpoints):**
- Core pages: `/`, `/explore`, `/search`, `/makers`, `/collections`, `/tags`, `/alternatives`, `/stacks`
- Static pages: `/about`, `/faq`, `/terms`, `/privacy`, `/pricing`
- Blog: `/blog`, `/blog/stop-wasting-tokens`
- Auth pages: `/login`, `/signup`
- Protected pages: `/dashboard`, `/submit` (expect redirect or 200)
- API endpoints: `/api/tools/search`, `/api/tools/simple-analytics`, `/health`
- SEO: `/robots.txt`, `/sitemap.xml`, `/feed/rss`
- Agent: `/cards/index.json`, `/geo`
- SVG: `/api/badge/simple-analytics.svg`, `/api/milestone/simple-analytics.svg`
- Content pages: `/tool/simple-analytics`, `/tag/open-source`, `/alternatives/google-analytics`

**What it does NOT cover:**
- POST requests (no form submission testing)
- Authentication flows (login, signup, logout)
- Database mutations (create tool, upvote, review)
- Stripe payment flows
- Background tasks (ego pings, digests, TOTW selection)
- Admin panel functionality
- Rate limiting behavior
- CSRF protection
- Error handling (invalid slugs, malformed input)
- API key authentication
- GitHub OAuth flow
- Email sending

**How it works:**
```python
def fetch(base_url, method, path):
    """Custom fetch that does NOT follow redirects (to detect 303s)."""
    url = base_url.rstrip("/") + path
    # Uses urllib.request with custom NoRedirectHandler
    # Returns (status_code, body_text)

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://indiestack.ai"
    for method, path, expected, label in TESTS:
        status, body = fetch(base_url, method, path)
        ok = check_status(status, expected)
        # Also runs optional content checks
        # Prints colored pass/fail with timing
    # Exit 1 if any test failed
```

## Mocking

**Framework:** None

**What to Mock:** N/A -- no unit tests exist. If adding tests:
- Mock `aiosqlite` connections for database tests
- Mock `httpx` for GitHub OAuth tests
- Mock `smtplib.SMTP` for email tests
- Mock Stripe SDK for payment tests

## Fixtures and Factories

**Test Data:** None -- no test fixtures or factories exist

**If adding tests, seed data is available in:**
- `src/indiestack/db.py` line ~470: `SEED_CATEGORIES` list with 25 categories
- `scripts/seeds/` directory: various seed scripts for tools, plugins, etc.
- Database schema and seed logic in `db.py` `init_db()` function

## Coverage

**Requirements:** None enforced

**Current State:**
- No coverage tool configured
- No coverage targets or thresholds
- The smoke test covers endpoint availability only, not code path coverage

## Test Types

**Unit Tests:**
- None exist
- No isolated function testing for `db.py` query functions, `auth.py` password hashing, `components.py` HTML generation, or `email.py` templates

**Integration Tests:**
- None exist
- The smoke test is the closest to integration testing but runs against a deployed server, not a test instance

**E2E Tests:**
- No browser-based testing (no Playwright, Cypress, Selenium)
- The smoke test functions as a minimal E2E check (HTTP-level only)

**Smoke Tests:**
- `smoke_test.py` -- 37 endpoint checks with status code validation and 5 content checks
- Run pre-deploy as part of the manual deployment process
- Targets production URL by default, can target localhost

## Pre-Deploy Validation

**Current process (from CLAUDE.md):**
```bash
# 1. Syntax check all Python files
python -m py_compile src/indiestack/main.py  # etc.

# 2. Run smoke test
python smoke_test.py http://localhost:8080

# 3. Deploy
cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

## Adding Tests -- Recommended Approach

**If adding pytest-based tests:**

1. Install: `pip install pytest pytest-asyncio httpx`
2. Create `tests/` directory at project root
3. Add `conftest.py` with async database fixture using in-memory SQLite
4. Test database functions directly by importing from `indiestack.db`
5. Test HTML generators by calling component functions and checking output contains expected content
6. Test auth functions (`hash_password`, `verify_password`) as pure unit tests
7. Use `httpx.AsyncClient` with FastAPI's `TestClient` for API endpoint tests

**Example test structure (does not exist yet):**
```python
# tests/conftest.py
import pytest
import aiosqlite
from indiestack.db import SCHEMA, FTS_SCHEMA

@pytest.fixture
async def db():
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.executescript(SCHEMA)
    try:
        await conn.executescript(FTS_SCHEMA)
    except Exception:
        pass
    yield conn
    await conn.close()

# tests/test_auth.py
from indiestack.auth import hash_password, verify_password

def test_password_roundtrip():
    hashed = hash_password("test123")
    assert verify_password("test123", hashed)
    assert not verify_password("wrong", hashed)

# tests/test_db.py
import pytest
from indiestack.db import create_tool, get_tool_by_slug

@pytest.mark.asyncio
async def test_create_and_get_tool(db):
    await create_tool(db, name="Test", slug="test", ...)
    await db.commit()
    tool = await get_tool_by_slug(db, "test")
    assert tool['name'] == "Test"
```

---

*Testing analysis: 2026-03-13*
