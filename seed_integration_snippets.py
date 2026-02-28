"""
Seed real integration snippets for the top ~20 tools on IndieStack.

Run on production:
    flyctl ssh console -C "python3 /app/seed_integration_snippets.py"

Idempotent — safe to run multiple times (UPDATEs, not INSERTs).
"""
import sqlite3

conn = sqlite3.connect("/data/indiestack.db")

snippets = [
    # ── 1. Simple Analytics ──────────────────────────────────────────────
    ("simple-analytics",
     '''# Add to your HTML <head>:
# <script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
# <noscript><img src="https://queue.simpleanalyticscdn.com/noscript.gif" alt="" referrerpolicy="no-referrer-when-downgrade" /></noscript>

# Fetch pageview stats via API (no auth needed for public stats)
import httpx

domain = "yourdomain.com"
resp = httpx.get(f"https://simpleanalytics.com/{domain}.json",
                 params={"version": 5, "fields": "pageviews,visitors"})
data = resp.json()
print(f"Pageviews: {data['pageviews']}, Visitors: {data['visitors']}")

# Filter by date range
resp = httpx.get(f"https://simpleanalytics.com/{domain}.json",
                 params={"version": 5, "start": "2025-01-01", "end": "2025-01-31",
                         "fields": "pageviews"})''',

     '''# Fetch pageview stats (replace yourdomain.com)
curl -s "https://simpleanalytics.com/yourdomain.com.json?version=5&fields=pageviews,visitors" \\
  | python3 -m json.tool

# Filter by date range
curl -s "https://simpleanalytics.com/yourdomain.com.json?version=5&start=2025-01-01&end=2025-01-31&fields=pageviews"'''),

    # ── 2. Plausible Analytics ───────────────────────────────────────────
    ("plausible-analytics",
     '''# Add to your HTML <head>:
# <script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>

# pip install httpx
import httpx

API_KEY = "your-api-key"  # Settings > API Keys
SITE_ID = "yourdomain.com"
BASE = "https://plausible.io/api/v1"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Real-time visitors
resp = httpx.get(f"{BASE}/stats/realtime/visitors",
                 params={"site_id": SITE_ID}, headers=headers)
print(f"Current visitors: {resp.text}")

# Aggregate stats (last 30 days)
resp = httpx.get(f"{BASE}/stats/aggregate",
                 params={"site_id": SITE_ID, "period": "30d",
                         "metrics": "visitors,pageviews,bounce_rate,visit_duration"},
                 headers=headers)
print(resp.json())

# Top pages
resp = httpx.get(f"{BASE}/stats/breakdown",
                 params={"site_id": SITE_ID, "period": "30d",
                         "property": "event:page", "limit": 10},
                 headers=headers)
for page in resp.json()["results"]:
    print(f"  {page['page']}: {page['visitors']} visitors")''',

     '''# Real-time visitors
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://plausible.io/api/v1/stats/realtime/visitors?site_id=yourdomain.com"

# Aggregate stats (last 30 days)
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://plausible.io/api/v1/stats/aggregate?site_id=yourdomain.com&period=30d&metrics=visitors,pageviews,bounce_rate"

# Top pages breakdown
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://plausible.io/api/v1/stats/breakdown?site_id=yourdomain.com&period=30d&property=event:page&limit=10"'''),

    # ── 3. Fathom Analytics ──────────────────────────────────────────────
    ("fathom-analytics",
     '''# Add to your HTML <head> (replace ABCDEFGH with your Site ID):
# <script src="https://cdn.usefathom.com/script.js" data-site="ABCDEFGH" defer></script>

# pip install httpx
import httpx

API_KEY = "your-api-key"  # Settings > API Keys
SITE_ID = "ABCDEFGH"
BASE = "https://api.usefathom.com/v1"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Get current visitors
resp = httpx.get(f"{BASE}/current_visitors",
                 params={"site_id": SITE_ID}, headers=headers)
print(f"Current visitors: {resp.json()['total']}")

# Aggregated pageviews (last 30 days)
resp = httpx.get(f"{BASE}/aggregations",
                 params={"entity": "pageview", "entity_id": SITE_ID,
                         "aggregates": "visits,pageviews,avg_duration",
                         "date_from": "2025-01-01", "date_to": "2025-01-31"},
                 headers=headers)
print(resp.json())''',

     '''# Current visitors
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://api.usefathom.com/v1/current_visitors?site_id=ABCDEFGH"

# Aggregated stats
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://api.usefathom.com/v1/aggregations?entity=pageview&entity_id=ABCDEFGH&aggregates=visits,pageviews&date_from=2025-01-01&date_to=2025-01-31"'''),

    # ── 4. Invoice Ninja ─────────────────────────────────────────────────
    ("invoice-ninja",
     '''# pip install httpx
import httpx

API_URL = "https://invoicing.co/api/v1"  # or your self-hosted URL
API_TOKEN = "your-api-token"  # Settings > Account Management > API Tokens

headers = {
    "X-Api-Token": API_TOKEN,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
}

# List clients
resp = httpx.get(f"{API_URL}/clients", headers=headers)
clients = resp.json()["data"]
print(f"Found {len(clients)} clients")

# Create an invoice
invoice = {
    "client_id": clients[0]["id"],
    "line_items": [
        {
            "product_key": "Consulting",
            "notes": "Web development — January 2025",
            "quantity": 10,
            "cost": 150.00,
        }
    ],
    "auto_bill_enabled": False,
}
resp = httpx.post(f"{API_URL}/invoices", json=invoice, headers=headers)
new_invoice = resp.json()["data"]
print(f"Created invoice #{new_invoice['number']} for ${new_invoice['amount']}")

# Send the invoice via email
httpx.put(f"{API_URL}/invoices/{new_invoice['id']}?email_invoice=true",
          json={}, headers=headers)''',

     '''# List clients
curl -s -H "X-Api-Token: YOUR_TOKEN" -H "X-Requested-With: XMLHttpRequest" \\
  "https://invoicing.co/api/v1/clients" | python3 -m json.tool

# Create an invoice
curl -s -X POST "https://invoicing.co/api/v1/invoices" \\
  -H "X-Api-Token: YOUR_TOKEN" \\
  -H "X-Requested-With: XMLHttpRequest" \\
  -H "Content-Type: application/json" \\
  -d '{
    "client_id": "CLIENT_ID",
    "line_items": [{
      "product_key": "Consulting",
      "notes": "Web development",
      "quantity": 10,
      "cost": 150.00
    }]
  }' '''),

    # ── 5. Invoice as a Service ──────────────────────────────────────────
    ("invoice-as-a-service",
     '''# pip install httpx
import httpx

# Generate a PDF invoice via the API
invoice_data = {
    "from": "Your Company\\n123 Main St\\nLondon, UK",
    "to": "Client Name\\n456 Oak Ave\\nNew York, US",
    "number": "INV-001",
    "date": "2025-02-01",
    "due_date": "2025-03-01",
    "items": [
        {"name": "Web Development", "quantity": 40, "unit_cost": 100},
        {"name": "Design Review", "quantity": 5, "unit_cost": 80},
    ],
    "notes": "Payment due within 30 days.",
    "currency": "GBP",
}

resp = httpx.post("https://invoice-generator.com/api/v1/invoices",
                  json=invoice_data,
                  headers={"Content-Type": "application/json"})

# Save the PDF
with open("invoice.pdf", "wb") as f:
    f.write(resp.content)
print("Saved invoice.pdf")''',

     '''# Generate a PDF invoice
curl -s -X POST "https://invoice-generator.com/api/v1/invoices" \\
  -H "Content-Type: application/json" \\
  -d '{
    "from": "Your Company\\n123 Main St",
    "to": "Client Name\\n456 Oak Ave",
    "number": "INV-001",
    "date": "2025-02-01",
    "items": [
      {"name": "Web Development", "quantity": 40, "unit_cost": 100}
    ],
    "currency": "GBP"
  }' --output invoice.pdf

echo "Saved invoice.pdf"'''),

    # ── 6. Chatwoot ──────────────────────────────────────────────────────
    ("chatwoot",
     '''# Embed the widget — add before </body>:
# <script>
#   (function(d,t) {
#     var BASE_URL="https://app.chatwoot.com";
#     var g=d.createElement(t),s=d.getElementsByTagName(t)[0];
#     g.src=BASE_URL+"/packs/js/sdk.js";
#     g.defer=true;
#     g.async=true;
#     s.parentNode.insertBefore(g,s);
#     g.onload=function(){
#       window.chatwootSDK.run({
#         websiteToken: 'YOUR_WEBSITE_TOKEN',
#         baseUrl: BASE_URL
#       })
#     }
#   })(document,"script");
# </script>

# pip install httpx
import httpx

BASE = "https://app.chatwoot.com"  # or your self-hosted URL
API_TOKEN = "your-user-api-token"  # Profile > Access Token
ACCOUNT_ID = 1

headers = {"api_access_token": API_TOKEN, "Content-Type": "application/json"}

# List conversations
resp = httpx.get(f"{BASE}/api/v1/accounts/{ACCOUNT_ID}/conversations",
                 headers=headers)
conversations = resp.json()["data"]["payload"]
print(f"Found {len(conversations)} conversations")

# Send a message in a conversation
conv_id = conversations[0]["id"]
resp = httpx.post(
    f"{BASE}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/messages",
    json={"content": "Thanks for reaching out! We'll get back to you shortly.",
          "message_type": "outgoing"},
    headers=headers)
print(f"Sent message: {resp.json()['id']}")''',

     '''# List conversations
curl -s -H "api_access_token: YOUR_TOKEN" \\
  "https://app.chatwoot.com/api/v1/accounts/1/conversations" | python3 -m json.tool

# Send a message
curl -s -X POST "https://app.chatwoot.com/api/v1/accounts/1/conversations/CONV_ID/messages" \\
  -H "api_access_token: YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Thanks for reaching out!", "message_type": "outgoing"}'
'''),

    # ── 7. Papercups ─────────────────────────────────────────────────────
    ("papercups",
     '''# Embed the widget — add before </body>:
# <script
#   type="text/javascript"
#   async
#   defer
#   src="https://app.papercups.io/widget.js"
# ></script>
# <script>
#   window.Papercups = {
#     config: {
#       accountId: "YOUR_ACCOUNT_ID",
#       title: "Welcome!",
#       subtitle: "Ask us anything in the chat below.",
#       primaryColor: "#1890ff",
#       greeting: "Hi there! How can we help?",
#       newMessagePlaceholder: "Type a message...",
#       requireEmailUpfront: false,
#       baseUrl: "https://app.papercups.io",
#     },
#   };
# </script>

# pip install httpx
import httpx

BASE = "https://app.papercups.io/api"  # or your self-hosted URL
API_KEY = "your-api-key"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# List conversations
resp = httpx.get(f"{BASE}/conversations", headers=headers)
conversations = resp.json()["data"]
for conv in conversations[:5]:
    print(f"  [{conv['status']}] {conv['customer']['email'] or 'anonymous'}")

# Send a reply
conv_id = conversations[0]["id"]
httpx.post(f"{BASE}/messages", json={
    "message": {"body": "Thanks for your message!", "conversation_id": conv_id}
}, headers=headers)''',

     '''# List conversations
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://app.papercups.io/api/conversations" | python3 -m json.tool

# Send a reply
curl -s -X POST "https://app.papercups.io/api/messages" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"message": {"body": "Thanks for your message!", "conversation_id": "CONV_ID"}}'
'''),

    # ── 8. Ghost ─────────────────────────────────────────────────────────
    ("ghost",
     '''# pip install httpx
import httpx

GHOST_URL = "https://yourblog.ghost.io"
CONTENT_API_KEY = "your-content-api-key"  # Settings > Integrations > Add custom

# List published posts
resp = httpx.get(f"{GHOST_URL}/ghost/api/content/posts/",
                 params={"key": CONTENT_API_KEY, "limit": 10,
                         "fields": "title,slug,published_at,excerpt",
                         "include": "tags"})
posts = resp.json()["posts"]
for post in posts:
    tags = ", ".join(t["name"] for t in post.get("tags", []))
    print(f"  {post['title']} [{tags}] — {post['published_at'][:10]}")

# Get a single post by slug
resp = httpx.get(f"{GHOST_URL}/ghost/api/content/posts/slug/my-first-post/",
                 params={"key": CONTENT_API_KEY, "formats": "html"})
post = resp.json()["posts"][0]
print(post["html"][:200])

# List tags
resp = httpx.get(f"{GHOST_URL}/ghost/api/content/tags/",
                 params={"key": CONTENT_API_KEY, "limit": "all"})
for tag in resp.json()["tags"]:
    print(f"  #{tag['slug']} ({tag['count']['posts']} posts)")''',

     '''# List published posts
curl -s "https://yourblog.ghost.io/ghost/api/content/posts/?key=YOUR_CONTENT_API_KEY&limit=10&fields=title,slug,published_at" \\
  | python3 -m json.tool

# Get a single post by slug
curl -s "https://yourblog.ghost.io/ghost/api/content/posts/slug/my-first-post/?key=YOUR_CONTENT_API_KEY&formats=html"

# List all tags
curl -s "https://yourblog.ghost.io/ghost/api/content/tags/?key=YOUR_CONTENT_API_KEY&limit=all"
'''),

    # ── 9. Payload CMS ──────────────────────────────────────────────────
    ("payload-cms",
     '''# pip install httpx
import httpx

BASE = "http://localhost:3000"  # your Payload server
API_KEY = "your-api-key"  # or use email/password login

headers = {"Authorization": f"API-Key {API_KEY}", "Content-Type": "application/json"}

# List documents in a collection
resp = httpx.get(f"{BASE}/api/posts",
                 params={"limit": 10, "sort": "-createdAt"},
                 headers=headers)
docs = resp.json()["docs"]
for doc in docs:
    print(f"  {doc['title']} (id: {doc['id']})")

# Create a new document
new_post = {
    "title": "Hello from Python",
    "content": "This post was created via the Payload REST API.",
    "status": "draft",
}
resp = httpx.post(f"{BASE}/api/posts", json=new_post, headers=headers)
print(f"Created: {resp.json()['doc']['id']}")

# Query with filters (Payload uses qs-style where queries)
resp = httpx.get(f"{BASE}/api/posts",
                 params={"where[status][equals]": "published", "limit": 5},
                 headers=headers)
print(f"Published posts: {resp.json()['totalDocs']}")''',

     '''# List documents in a collection
curl -s -H "Authorization: API-Key YOUR_KEY" \\
  "http://localhost:3000/api/posts?limit=10&sort=-createdAt" | python3 -m json.tool

# Create a new document
curl -s -X POST "http://localhost:3000/api/posts" \\
  -H "Authorization: API-Key YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Hello from cURL", "content": "Created via REST API.", "status": "draft"}'

# Query with filters
curl -s -H "Authorization: API-Key YOUR_KEY" \\
  "http://localhost:3000/api/posts?where[status][equals]=published&limit=5"
'''),

    # ── 10. Coolify ──────────────────────────────────────────────────────
    ("coolify",
     '''# pip install httpx
import httpx

BASE = "https://your-coolify-instance.com/api/v1"
API_TOKEN = "your-api-token"  # Settings > API > Generate Token

headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}

# List servers
resp = httpx.get(f"{BASE}/servers", headers=headers)
for server in resp.json():
    print(f"  {server['name']} — {server['ip']} ({'online' if server['is_reachable'] else 'offline'})")

# List applications
resp = httpx.get(f"{BASE}/applications", headers=headers)
for app in resp.json():
    print(f"  {app['name']} — {app['fqdn'] or 'no domain'} ({app['status']})")

# Deploy an application
app_uuid = "your-app-uuid"
resp = httpx.post(f"{BASE}/applications/{app_uuid}/deploy", headers=headers)
print(f"Deployment started: {resp.json()['message']}")

# Get deployment logs
resp = httpx.get(f"{BASE}/applications/{app_uuid}/logs", headers=headers)
print(resp.text[:500])''',

     '''# List servers
curl -s -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://your-coolify-instance.com/api/v1/servers" | python3 -m json.tool

# List applications
curl -s -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://your-coolify-instance.com/api/v1/applications" | python3 -m json.tool

# Deploy an application
curl -s -X POST -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://your-coolify-instance.com/api/v1/applications/APP_UUID/deploy"
'''),

    # ── 11. Supabase ─────────────────────────────────────────────────────
    ("supabase",
     '''# pip install supabase
from supabase import create_client

SUPABASE_URL = "https://xyzproject.supabase.co"
SUPABASE_KEY = "your-anon-or-service-key"  # Project Settings > API

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Select rows
result = supabase.table("todos").select("*").eq("completed", False).limit(10).execute()
for row in result.data:
    print(f"  [{row['id']}] {row['title']}")

# Insert a row
result = supabase.table("todos").insert({
    "title": "Buy milk",
    "completed": False,
}).execute()
print(f"Created todo: {result.data[0]['id']}")

# Update a row
supabase.table("todos").update({"completed": True}).eq("id", 1).execute()

# Auth — sign up a user
auth_resp = supabase.auth.sign_up({"email": "user@example.com", "password": "securepass123"})
print(f"User ID: {auth_resp.user.id}")

# Storage — upload a file
with open("photo.jpg", "rb") as f:
    supabase.storage.from_("avatars").upload("user1/photo.jpg", f)''',

     '''# Select rows (uses PostgREST)
curl -s "https://xyzproject.supabase.co/rest/v1/todos?completed=eq.false&limit=10" \\
  -H "apikey: YOUR_ANON_KEY" \\
  -H "Authorization: Bearer YOUR_ANON_KEY"

# Insert a row
curl -s -X POST "https://xyzproject.supabase.co/rest/v1/todos" \\
  -H "apikey: YOUR_ANON_KEY" \\
  -H "Authorization: Bearer YOUR_ANON_KEY" \\
  -H "Content-Type: application/json" \\
  -H "Prefer: return=representation" \\
  -d '{"title": "Buy milk", "completed": false}'

# Update a row
curl -s -X PATCH "https://xyzproject.supabase.co/rest/v1/todos?id=eq.1" \\
  -H "apikey: YOUR_ANON_KEY" \\
  -H "Authorization: Bearer YOUR_ANON_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"completed": true}'
'''),

    # ── 12. Clerk ────────────────────────────────────────────────────────
    ("clerk",
     '''# pip install clerk-backend-api httpx
from clerk_backend_api import Clerk

# Initialize with your secret key (Dashboard > API Keys)
clerk = Clerk(bearer_auth="sk_live_xxxxx")

# List users
users = clerk.users.list(limit=10, order_by="-created_at")
for user in users:
    email = user.email_addresses[0].email_address if user.email_addresses else "n/a"
    print(f"  {user.id}: {email} (created {user.created_at})")

# Get a specific user
user = clerk.users.get(user_id="user_xxxxx")
print(f"Name: {user.first_name} {user.last_name}")

# Verify a session token (in your backend middleware)
import httpx
resp = httpx.get("https://api.clerk.com/v1/sessions/sess_xxxxx/verify",
                 headers={"Authorization": "Bearer sk_live_xxxxx",
                          "Content-Type": "application/json"})
session = resp.json()
print(f"User: {session['user_id']}, Status: {session['status']}")''',

     '''# List users
curl -s -H "Authorization: Bearer sk_live_xxxxx" \\
  "https://api.clerk.com/v1/users?limit=10&order_by=-created_at" | python3 -m json.tool

# Get a specific user
curl -s -H "Authorization: Bearer sk_live_xxxxx" \\
  "https://api.clerk.com/v1/users/user_xxxxx"

# Verify a session
curl -s -X POST -H "Authorization: Bearer sk_live_xxxxx" \\
  "https://api.clerk.com/v1/sessions/sess_xxxxx/verify"
'''),

    # ── 13. Loops ────────────────────────────────────────────────────────
    ("loops",
     '''# pip install httpx
import httpx

API_KEY = "your-api-key"  # Loops dashboard > Settings > API
BASE = "https://app.loops.so/api/v1"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Create (or update) a contact
resp = httpx.post(f"{BASE}/contacts/create", json={
    "email": "user@example.com",
    "firstName": "Jane",
    "lastName": "Doe",
    "source": "website",
    "userGroup": "beta",
}, headers=headers)
print(f"Contact: {resp.json()}")

# Send a transactional email
resp = httpx.post(f"{BASE}/transactional", json={
    "transactionalId": "your-template-id",
    "email": "user@example.com",
    "dataVariables": {
        "name": "Jane",
        "loginUrl": "https://app.example.com/magic?token=abc123",
    },
}, headers=headers)
print(f"Email sent: {resp.json()['success']}")

# Trigger an event (for automated sequences)
resp = httpx.post(f"{BASE}/events/send", json={
    "email": "user@example.com",
    "eventName": "signup_completed",
}, headers=headers)''',

     '''# Create a contact
curl -s -X POST "https://app.loops.so/api/v1/contacts/create" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "firstName": "Jane", "source": "website"}'

# Send a transactional email
curl -s -X POST "https://app.loops.so/api/v1/transactional" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"transactionalId": "TEMPLATE_ID", "email": "user@example.com", "dataVariables": {"name": "Jane"}}'

# Trigger an event
curl -s -X POST "https://app.loops.so/api/v1/events/send" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "eventName": "signup_completed"}'
'''),

    # ── 14. Nolt ─────────────────────────────────────────────────────────
    ("nolt",
     '''# Embed the Nolt feedback widget — add before </body>:
# <script async src="https://nolt.io/widget.js"></script>
# <button data-nolt="board" data-board="YOUR_BOARD.nolt.io">
#   Give Feedback
# </button>

# Nolt also supports an iframe embed:
# <iframe
#   src="https://YOUR_BOARD.nolt.io"
#   width="100%"
#   height="800"
#   frameborder="0"
#   style="border: none;">
# </iframe>

# SSO: Identify logged-in users with a JWT
# pip install pyjwt
import jwt

sso_token = jwt.encode({
    "id": "user_123",
    "email": "user@example.com",
    "name": "Jane Doe",
    "imageUrl": "https://example.com/avatar.jpg",
}, "your-nolt-sso-secret", algorithm="HS256")

# Then use: data-jwt="<sso_token>" on the button/widget
# <button data-nolt="board" data-board="YOUR_BOARD.nolt.io" data-jwt="TOKEN">
#   Give Feedback
# </button>''',

     '''# Nolt is primarily widget-based. Embed in HTML:
#
# <script async src="https://nolt.io/widget.js"></script>
# <button data-nolt="board" data-board="YOUR_BOARD.nolt.io">
#   Give Feedback
# </button>
#
# Or as a full-page iframe:
# <iframe src="https://YOUR_BOARD.nolt.io" width="100%" height="800"></iframe>
#
# Generate SSO JWT (for identifying logged-in users):
python3 -c "
import jwt
token = jwt.encode({
    'id': 'user_123',
    'email': 'user@example.com',
    'name': 'Jane Doe'
}, 'your-nolt-sso-secret', algorithm='HS256')
print(token)
"'''),

    # ── 15. Checkly ──────────────────────────────────────────────────────
    ("checkly",
     '''# pip install httpx
import httpx

API_KEY = "your-api-key"  # Account Settings > API Keys
ACCOUNT_ID = "your-account-id"
BASE = "https://api.checklyhq.com/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "x-checkly-account": ACCOUNT_ID,
    "Content-Type": "application/json",
}

# List all checks
resp = httpx.get(f"{BASE}/checks", headers=headers)
for check in resp.json():
    status = "passing" if check["hasFailures"] is False else "FAILING"
    print(f"  [{status}] {check['name']} — {check['checkType']}")

# Get check results (last 24h)
check_id = "your-check-id"
resp = httpx.get(f"{BASE}/check-results/{check_id}",
                 params={"limit": 10},
                 headers=headers)
for result in resp.json():
    print(f"  {result['created_at']} — {result['responseTime']}ms — {'PASS' if result['hasFailures'] is False else 'FAIL'}")

# Create an API check
resp = httpx.post(f"{BASE}/checks/api", json={
    "name": "Homepage Health",
    "activated": True,
    "frequency": 5,  # minutes
    "checkType": "API",
    "request": {
        "method": "GET",
        "url": "https://example.com/health",
        "assertions": [{"source": "STATUS_CODE", "comparison": "EQUALS", "target": "200"}],
    },
    "locations": ["us-east-1", "eu-west-1"],
}, headers=headers)
print(f"Created check: {resp.json()['id']}")''',

     '''# List all checks
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "x-checkly-account: YOUR_ACCOUNT_ID" \\
  "https://api.checklyhq.com/v1/checks" | python3 -m json.tool

# Get check results
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "x-checkly-account: YOUR_ACCOUNT_ID" \\
  "https://api.checklyhq.com/v1/check-results/CHECK_ID?limit=10"

# Create an API check
curl -s -X POST "https://api.checklyhq.com/v1/checks/api" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "x-checkly-account: YOUR_ACCOUNT_ID" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Homepage Health",
    "activated": true,
    "frequency": 5,
    "request": {"method": "GET", "url": "https://example.com/health",
                "assertions": [{"source": "STATUS_CODE", "comparison": "EQUALS", "target": "200"}]},
    "locations": ["us-east-1", "eu-west-1"]
  }'
'''),

    # ── 16. Better Stack ─────────────────────────────────────────────────
    ("better-stack",
     '''# pip install httpx
import httpx

API_TOKEN = "your-api-token"  # Better Stack > Settings > API tokens
BASE = "https://uptime.betterstack.com/api/v2"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

# List monitors
resp = httpx.get(f"{BASE}/monitors", headers=headers)
for monitor in resp.json()["data"]:
    attrs = monitor["attributes"]
    status = attrs["status"]
    print(f"  [{status}] {attrs['pronounceable_name']} — {attrs['url']}")

# Create a new monitor
resp = httpx.post(f"{BASE}/monitors", json={
    "monitor_type": "status",
    "url": "https://example.com",
    "pronounceable_name": "Production Website",
    "check_frequency": 60,  # seconds
    "regions": ["us", "eu"],
}, headers=headers)
print(f"Created monitor: {resp.json()['data']['id']}")

# List incidents
resp = httpx.get(f"{BASE}/incidents", headers=headers)
for inc in resp.json()["data"]:
    attrs = inc["attributes"]
    print(f"  [{attrs['status']}] {attrs['name']} — started {attrs['started_at']}")''',

     '''# List monitors
curl -s -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://uptime.betterstack.com/api/v2/monitors" | python3 -m json.tool

# Create a monitor
curl -s -X POST "https://uptime.betterstack.com/api/v2/monitors" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"monitor_type": "status", "url": "https://example.com", "pronounceable_name": "Production", "check_frequency": 60}'

# List incidents
curl -s -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://uptime.betterstack.com/api/v2/incidents" | python3 -m json.tool
'''),

    # ── 17. Spike.sh ─────────────────────────────────────────────────────
    ("spike-sh",
     '''# pip install httpx
import httpx

API_KEY = "your-api-key"  # Spike.sh dashboard > Settings > API
BASE = "https://api.spike.sh/v1"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# List incidents
resp = httpx.get(f"{BASE}/incidents", headers=headers)
for inc in resp.json()["data"]:
    print(f"  [{inc['status']}] {inc['title']} — {inc['created_at']}")

# Trigger an incident (from your monitoring system)
resp = httpx.post(f"{BASE}/incidents", json={
    "integration_key": "your-integration-key",
    "title": "High CPU on web-01",
    "description": "CPU usage exceeded 95% for 5 minutes.",
    "severity": "critical",
}, headers=headers)
print(f"Incident created: {resp.json()['data']['id']}")

# Resolve an incident
incident_id = "inc_xxxxx"
resp = httpx.patch(f"{BASE}/incidents/{incident_id}/resolve",
                   headers=headers)
print(f"Resolved: {resp.json()['data']['status']}")''',

     '''# List incidents
curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://api.spike.sh/v1/incidents" | python3 -m json.tool

# Trigger an incident
curl -s -X POST "https://api.spike.sh/v1/incidents" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"integration_key": "YOUR_KEY", "title": "High CPU on web-01", "severity": "critical"}'

# Resolve an incident
curl -s -X PATCH -H "Authorization: Bearer YOUR_API_KEY" \\
  "https://api.spike.sh/v1/incidents/INCIDENT_ID/resolve"
'''),

    # ── 18. GovLink ──────────────────────────────────────────────────────
    ("govlink",
     '''# pip install govlink httpx
import httpx

BASE = "https://govlink.fly.dev"

# Verify a UK company (using Companies House data)
resp = httpx.get(f"{BASE}/api/verify",
                 params={"domain": "example.co.uk"})
data = resp.json()
print(f"Company: {data['company_name']}")
print(f"Status: {data['status']}")
print(f"Trust Score: {data['trust_score']}/100")

# Bulk verify multiple domains
resp = httpx.post(f"{BASE}/api/verify/bulk", json={
    "domains": ["example.co.uk", "acme.com", "startup.io"]
})
for result in resp.json()["results"]:
    print(f"  {result['domain']}: {result['trust_score']}/100")

# Check trust badge embed
# Add to your site:
# <a href="https://govlink.fly.dev/verify/example.co.uk">
#   <img src="https://govlink.fly.dev/badge/example.co.uk.svg" alt="GovLink Verified" />
# </a>''',

     '''# Verify a domain
curl -s "https://govlink.fly.dev/api/verify?domain=example.co.uk" | python3 -m json.tool

# Bulk verify
curl -s -X POST "https://govlink.fly.dev/api/verify/bulk" \\
  -H "Content-Type: application/json" \\
  -d '{"domains": ["example.co.uk", "acme.com"]}'

# Get trust badge SVG
curl -s "https://govlink.fly.dev/badge/example.co.uk.svg" -o badge.svg
'''),

    # ── 19. Railway ──────────────────────────────────────────────────────
    ("railway",
     '''# pip install httpx
import httpx

API_TOKEN = "your-railway-token"  # Account Settings > Tokens > Create Token
BASE = "https://backboard.railway.app/graphql/v2"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

# List your projects
query = """
query {
  me {
    projects {
      edges {
        node {
          id
          name
          createdAt
          services {
            edges {
              node {
                name
                id
              }
            }
          }
        }
      }
    }
  }
}
"""
resp = httpx.post(BASE, json={"query": query}, headers=headers)
projects = resp.json()["data"]["me"]["projects"]["edges"]
for p in projects:
    node = p["node"]
    services = [s["node"]["name"] for s in node["services"]["edges"]]
    print(f"  {node['name']}: {', '.join(services) or 'no services'}")

# Trigger a deployment
mutation = """
mutation($serviceId: String!, $environmentId: String!) {
  serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $environmentId)
}
"""
resp = httpx.post(BASE, json={
    "query": mutation,
    "variables": {"serviceId": "your-service-id", "environmentId": "your-env-id"},
}, headers=headers)
print(f"Redeployed: {resp.json()}")''',

     '''# List projects (GraphQL)
curl -s -X POST "https://backboard.railway.app/graphql/v2" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "{ me { projects { edges { node { id name } } } } }"}' \\
  | python3 -m json.tool

# Trigger a redeployment
curl -s -X POST "https://backboard.railway.app/graphql/v2" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "mutation($sid: String!, $eid: String!) { serviceInstanceRedeploy(serviceId: $sid, environmentId: $eid) }",
    "variables": {"sid": "SERVICE_ID", "eid": "ENV_ID"}
  }'
'''),

    # ── 20. Buffer ───────────────────────────────────────────────────────
    ("buffer",
     '''# pip install httpx
import httpx

ACCESS_TOKEN = "your-access-token"  # Buffer > Settings > Apps > Access Token
BASE = "https://api.bufferapp.com/1"

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# List social profiles
resp = httpx.get(f"{BASE}/profiles.json", headers=headers)
for profile in resp.json():
    print(f"  {profile['service']}: @{profile['service_username']} (id: {profile['id']})")

# Create a scheduled post
profile_id = "your-profile-id"
resp = httpx.post(f"{BASE}/updates/create.json", data={
    "access_token": ACCESS_TOKEN,
    "profile_ids[]": profile_id,
    "text": "Just shipped a new feature! Check it out: https://example.com",
    "scheduled_at": "2025-03-01T14:00:00Z",
}, headers=headers)
update = resp.json()["updates"][0]
print(f"Scheduled: {update['text'][:50]}... for {update['due_at']}")

# Get pending updates for a profile
resp = httpx.get(f"{BASE}/profiles/{profile_id}/updates/pending.json",
                 headers=headers)
for update in resp.json()["updates"]:
    print(f"  [{update['due_at']}] {update['text'][:60]}...")''',

     '''# List social profiles
curl -s -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://api.bufferapp.com/1/profiles.json" | python3 -m json.tool

# Create a scheduled post
curl -s -X POST "https://api.bufferapp.com/1/updates/create.json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d "profile_ids[]=PROFILE_ID" \\
  -d "text=Just shipped a new feature!" \\
  -d "scheduled_at=2025-03-01T14:00:00Z"

# Get pending updates
curl -s -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://api.bufferapp.com/1/profiles/PROFILE_ID/updates/pending.json"
'''),
]

# ── Run updates ──────────────────────────────────────────────────────────
updated = 0
not_found = []

for slug, python_code, curl_code in snippets:
    cur = conn.execute(
        "UPDATE tools SET integration_python = ?, integration_curl = ? WHERE slug = ?",
        (python_code, curl_code, slug)
    )
    if cur.rowcount:
        updated += 1
        print(f"  Updated: {slug}")
    else:
        not_found.append(slug)
        print(f"  NOT FOUND: {slug}")

conn.commit()
print(f"\nDone. {updated}/{len(snippets)} tools updated.")
if not_found:
    print(f"Missing slugs: {', '.join(not_found)}")
conn.close()
