"""Design system and shared components for IndieStack."""

import json
from html import escape

from indiestack.config import BASE_URL

# ── Design Tokens ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def design_tokens() -> str:
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            /* Primary palette — legacy names preserved for compatibility */
            --terracotta: #1A2D4A;
            --terracotta-light: #2B4A6E;
            --terracotta-dark: #0F1D30;
            --gold: #E2B764;
            --gold-light: #F0D898;
            --gold-dark: #78350F;
            --slate: #00D4F5;
            --slate-light: #B2F0FF;
            --slate-dark: #00A8C6;
            --accent: var(--slate);

            /* Surfaces */
            --cream: #F7F9FC;
            --cream-dark: #EDF1F7;
            --card-bg: white;
            --nav-bg: white;

            /* Text */
            --ink: #1A1A2E;
            --ink-light: #475569;
            --ink-muted: #64748B;
            --border: #E2E8F0;

            /* Typography */
            --font-display: 'DM Serif Display', serif;
            --font-body: 'DM Sans', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        