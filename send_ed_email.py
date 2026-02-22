"""One-off script to email Ed the maker outreach list."""
import os
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

db = sqlite3.connect('/data/indiestack.db')
rows = db.execute(
    "SELECT t.id, t.name, t.slug, t.url FROM tools t "
    "WHERE t.maker_id IS NULL AND t.status = 'approved' ORDER BY t.name"
).fetchall()
db.close()

# Build HTML table rows
rows_html = ''
for tool_id, name, slug, url in rows:
    listing = f'https://indiestack.fly.dev/tool/{slug}'
    short_url = url.split('//')[1][:40] if '//' in url else url[:40]
    rows_html += (
        f'<tr>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:600;">{name}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #eee;"><a href="{url}">{short_url}</a></td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #eee;"><a href="{listing}">View Listing</a></td>'
        f'</tr>'
    )

html = f"""
<div style="font-family:-apple-system,sans-serif;max-width:700px;margin:0 auto;">
    <h1 style="color:#1A2D4A;font-size:24px;">IndieStack - Maker Outreach List</h1>
    <p style="color:#444;font-size:15px;line-height:1.6;">Hey Ed,</p>
    <p style="color:#444;font-size:15px;line-height:1.6;">
        Here are the <strong>{len(rows)} unclaimed tools</strong> on IndieStack. These are tools we've listed but whose makers haven't claimed their listing yet.
        Your job: DM these makers and get them to claim.
    </p>

    <h2 style="color:#1A2D4A;font-size:18px;margin-top:32px;">How Magic Claim Links Work</h2>
    <p style="color:#444;font-size:15px;line-height:1.6;">
        Go to <a href="https://indiestack.fly.dev/admin?tab=tools&filter=unclaimed">the admin panel (unclaimed filter)</a>.
        Each unclaimed tool has a <strong>"Copy Link"</strong> button. Click it to generate a magic claim URL.
        Send that link in your DM. When the maker clicks it, they sign up and claim their tool in one step.
    </p>

    <h2 style="color:#1A2D4A;font-size:18px;margin-top:32px;">DM Template</h2>
    <div style="background:#F5F3F0;padding:16px 20px;border-radius:12px;border-left:4px solid #00D4F5;margin:16px 0;">
        <p style="color:#333;font-size:14px;line-height:1.6;margin:0;">
            Hey! I'm building IndieStack - a curated directory of indie SaaS tools. I've listed [TOOL NAME] and thought you might want to claim your listing.
            <br><br>
            Claiming takes 10 seconds - you can track analytics, post changelogs, and get discovered by developers looking for tools like yours.
            <br><br>
            Here's your claim link: [PASTE MAGIC LINK]
            <br><br>
            Cheers!
        </p>
    </div>

    <h2 style="color:#1A2D4A;font-size:18px;margin-top:32px;">Where to DM</h2>
    <ul style="color:#444;font-size:14px;line-height:1.8;">
        <li><strong>GitHub repos</strong> - open an issue or find their email in commits</li>
        <li><strong>Twitter/X</strong> - search for the tool name, DM the maker</li>
        <li><strong>.com tools</strong> (Crisp, Tally, etc.) - use their contact page or support email</li>
    </ul>

    <h2 style="color:#1A2D4A;font-size:18px;margin-top:32px;">Priority Targets</h2>
    <p style="color:#444;font-size:14px;">Start with these - they're active indie makers most likely to engage:</p>
    <ol style="color:#444;font-size:14px;line-height:2;">
        <li><strong>Domain Locker</strong> (Lissy93) - very active GitHub, huge following</li>
        <li><strong>Activepieces</strong> - popular open-source automation platform</li>
        <li><strong>SSOReady</strong> - funded indie, active on Twitter</li>
        <li><strong>Tally</strong> - big indie brand, great social proof if they claim</li>
        <li><strong>n8n Workflow Builder</strong> - massive community</li>
        <li><strong>Invoice Ninja</strong> - established indie tool</li>
        <li><strong>Maizzle</strong> - active maintainer, email dev community</li>
        <li><strong>Page UI</strong> - active on GitHub, React/Next.js community</li>
    </ol>

    <h2 style="color:#1A2D4A;font-size:18px;margin-top:32px;">Full Unclaimed Tools List ({len(rows)} tools)</h2>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr style="background:#1A2D4A;color:#fff;">
            <th style="padding:10px 12px;text-align:left;">Tool</th>
            <th style="padding:10px 12px;text-align:left;">Website</th>
            <th style="padding:10px 12px;text-align:left;">Listing</th>
        </tr>
        {rows_html}
    </table>

    <p style="color:#888;font-size:13px;margin-top:32px;">
        Admin panel: <a href="https://indiestack.fly.dev/admin">indiestack.fly.dev/admin</a><br>
        Login with your IndieStack account to access admin.
    </p>
</div>
"""

msg = MIMEMultipart('alternative')
msg['Subject'] = 'IndieStack - 55 Unclaimed Tools to DM (Magic Links Ready)'
msg['From'] = f'IndieStack <{os.environ.get("SMTP_FROM", "noreply@indiestack.fly.dev")}>'
msg['To'] = 'toedgamings@gmail.com'
msg.attach(MIMEText(html, 'html'))

with smtplib.SMTP(os.environ['SMTP_HOST'], 587) as server:
    server.starttls()
    server.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
    server.sendmail(os.environ['SMTP_FROM'], ['toedgamings@gmail.com'], msg.as_string())
    print('Email sent successfully to toedgamings@gmail.com!')
