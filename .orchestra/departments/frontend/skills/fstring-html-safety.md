# F-String HTML Safety — Frontend Skill

IndieStack uses Python f-string templates returning HTMLResponse. No Jinja2, React, or Vue. This creates XSS risks if not handled carefully.

## Rules

### Always escape user data
```python
from html import escape
name = escape(tool['name'])  # BEFORE injecting into f-string
html = f'<h1>{name}</h1>'
```

### Never hardcode hex colors
```python
# BAD
style="color:#00D4F5"

# GOOD
style="color:var(--accent)"
```
CSS variables are in components.py `:root` block. Use them always.

### Touch targets >= 44px
Every clickable element needs min-height:44px for mobile:
```python
style="min-height:44px;padding:10px 16px;"
```

### Button not inside link
```python
# BAD — invalid HTML
<a href="/x"><button>Click</button></a>

# GOOD
<a href="/x" class="btn-primary" style="...">Click</a>
```

### Python 3.11 f-string limitations
Backslashes not allowed inside `{}` in f-strings. Pre-compute:
```python
# BAD
f'<p>{value.replace("x", "y")}</p>'

# GOOD
cleaned = value.replace("x", "y")
f'<p>{cleaned}</p>'
```

### JSON-LD in templates
Use `json.dumps()` for JSON-LD content — it handles escaping:
```python
import json
json_ld = json.dumps({"@type": "FAQPage", ...})
html = f'<script type="application/ld+json">{json_ld}</script>'
```

## Verification
After every edit: `python3 -c "import ast; ast.parse(open('file.py').read())"`
