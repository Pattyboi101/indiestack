"""Design system and shared components for IndieStack."""

import json
from html import escape

from indiestack.config import BASE_URL

# ── Design Tokens ─────────────────────────────────────────────────────────

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
            --text-xs: 11px;
            --text-sm: 13px;
            --text-base: 14px;
            --text-lg: 16px;
            --heading-sm: 20px;
            --heading-md: 26px;
            --heading-lg: 34px;
            --heading-xl: 44px;

            /* Layout */
            --max-w: 1100px;
            --radius: 12px;
            --radius-sm: 8px;

            /* Elevation */
            --shadow-sm: 0 1px 3px rgba(26,45,74,0.06);
            --shadow-md: 0 4px 12px rgba(26,45,74,0.08);
            --shadow-lg: 0 12px 40px rgba(26,45,74,0.10);

            /* Layered elevation — premium depth */
            --shadow-lifted: 0 1px 2px rgba(26,45,74,0.04),
                             0 4px 8px rgba(26,45,74,0.06),
                             0 16px 48px rgba(26,45,74,0.08);
            --shadow-floating: 0 2px 4px rgba(26,45,74,0.04),
                               0 8px 24px rgba(26,45,74,0.08),
                               0 24px 64px rgba(26,45,74,0.12);

            /* Glassmorphism */
            --backdrop-blur: blur(12px);
            --nav-bg-glass: rgba(247,249,252,0.85);

            /* Animation */
            --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
            --duration-fast: 0.15s;
            --duration-normal: 0.25s;
            --stagger-delay: 80ms;

            /* Status */
            --success-bg: #ECFDF5;
            --success-text: #065F46;
            --success-border: #A7F3D0;
            --warning-bg: #FDF8EE;
            --warning-text: #92400E;
            --warning-border: #FDE68A;
            --info-bg: #F0F9FF;
            --info-text: #0E7490;
            --info-border: #A5F3FC;
            --error-bg: #FEF2F2;
            --error-text: #991B1B;
            --error-border: #FECACA;
        }

        [data-theme="dark"] {
            --terracotta: #3A6A9F;
            --terracotta-light: #4A7AB0;
            --terracotta-dark: #2B4A6E;
            --gold: #F0D898;
            --gold-light: #D4A24A;
            --gold-dark: #F0D898;
            --slate: #40E8FF;
            --slate-light: #80F0FF;
            --slate-dark: #20C8E0;
            --accent: var(--slate);
            --cream: #0A0E1A;
            --cream-dark: #141B2D;
            --card-bg: #141B2D;
            --nav-bg: #0A0E1A;
            --ink: #F1F5F9;
            --ink-light: #94A3B8;
            --ink-muted: #546178;
            --border: rgba(255,255,255,0.08);
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.03);
            --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
            --shadow-lg: 0 12px 40px rgba(0,0,0,0.5);
            --shadow-lifted: 0 4px 16px rgba(0,0,0,0.4), 0 0 32px rgba(64,232,255,0.06);
            --shadow-floating: 0 8px 32px rgba(0,0,0,0.5), 0 0 64px rgba(64,232,255,0.08);
            --nav-bg-glass: rgba(10,14,26,0.8);
            --success-bg: #052E16;
            --success-text: #86EFAC;
            --success-border: #166534;
            --warning-bg: #451A03;
            --warning-text: #FDE68A;
            --warning-border: #92400E;
            --info-bg: #0C1929;
            --info-text: var(--slate);
            --info-border: var(--slate-dark);
            --error-bg: #2D0F0F;
            --error-text: #FCA5A5;
            --error-border: #7F1D1D;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        html, body { overflow-x: hidden; }
        body {
            font-family: var(--font-body);
            background: var(--cream);
            color: var(--ink);
            line-height: 1.6;
            min-height: 100vh;
        }
        [data-theme="dark"] body {
            background: linear-gradient(180deg, #0A0E1A 0%, #0D1225 50%, #0A0E1A 100%);
        }

        a { color: var(--terracotta); text-decoration: none; }
        a:hover { color: var(--terracotta-dark); }

        .container { max-width: var(--max-w); margin: 0 auto; padding: 0 24px; }

        /* ── Cards ─────────────────── */
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 24px;
            transition: transform 0.25s var(--ease-out-expo), box-shadow 0.25s var(--ease-out-expo), border-color 0.25s ease;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            word-break: break-word;
        }
        .card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lifted);
            border-color: var(--accent);
        }

        .card-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            max-width: 100%;
            overflow: hidden;
        }
        .card-grid > * { min-width: 0; overflow: hidden; }
        @media (max-width: 900px) { .card-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 600px) { .card-grid { grid-template-columns: 1fr; } }

        /* ── Scroll Row ───────────── */
        .scroll-row {
            display: flex;
            gap: 24px;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 16px;
        }
        .scroll-row > * {
            scroll-snap-align: start;
            flex: 0 0 340px;
            min-width: 280px;
        }
        .scroll-row::-webkit-scrollbar { height: 8px; }
        .scroll-row::-webkit-scrollbar-track { background: var(--cream-dark); border-radius: 3px; }
        .scroll-row::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        .scroll-row::-webkit-scrollbar-thumb:hover { background: var(--ink-muted); }

        /* ── Buttons ───────────────── */
        .btn {
            display: inline-flex; align-items: center; gap: 8px;
            font-family: var(--font-body);
            font-weight: 600; font-size: 14px;
            padding: 12px 24px;
            border-radius: 999px;
            border: none; cursor: pointer;
            transition: all 0.15s ease;
            min-height: 44px;
        }
        .btn-primary { background: var(--accent); color: #000; font-weight: 700; }
        .btn-primary:hover { background: var(--accent); color: #000; filter: brightness(1.1); }
        .btn-secondary { background: var(--cream-dark); color: var(--ink); border: 1px solid var(--border); }
        .btn-secondary:hover { background: var(--border); }
        [data-theme="dark"] .btn-secondary { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); color: #fff; }
        [data-theme="dark"] .btn-secondary:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.15); color: #fff; }
        .btn-slate { background: var(--slate); color: white; }
        .btn-slate:hover { background: var(--slate-dark); color: white; }
        .btn-lg { padding: 16px 32px; font-size: 16px; }
        .btn-sm { padding: 8px 16px; font-size: 12px; min-height: 36px; }
        .btn:focus-visible { outline: none; box-shadow: 0 0 0 2px var(--card-bg), 0 0 0 4px var(--accent); }
        a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }

        /* ── Hover utilities ──────── */
        .hover-lift { transition: transform 0.15s ease, box-shadow 0.15s ease; }
        .hover-lift:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
        .hover-highlight { transition: background 0.15s ease; }
        .hover-highlight:hover { background: var(--cream-dark); }
        .totw-link { transition: box-shadow 0.2s ease, transform 0.2s ease; }
        .totw-link:hover { box-shadow: 0 4px 16px rgba(226,183,100,0.25); transform: translateY(-1px); }
        .pill-link { transition: border-color 0.15s ease, color 0.15s ease; }
        .pill-link:hover { border-color: var(--slate) !important; color: var(--ink) !important; }

        /* ── Tags ──────────────────── */
        .tag {
            display: inline-block;
            font-family: var(--font-mono);
            font-size: 12px; font-weight: 500;
            padding: 4px 12px;
            background: rgba(26,45,74,0.07);
            color: var(--terracotta);
            border-radius: 999px;
            border: 1px solid transparent;
        }
        [data-theme="dark"] .tag {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.05);
            color: var(--ink-light);
            font-weight: 600;
        }

        /* ── Upvote button ─────────── */
        .upvote-btn {
            display: inline-flex; flex-direction: column; align-items: center;
            gap: 2px; padding: 8px 16px;
            min-width: 48px; min-height: 48px;
            background: var(--cream-dark); border: none; border-left: 1px solid rgba(255,255,255,0.05);
            border-radius: var(--radius);
            cursor: pointer; transition: all 0.2s var(--ease-out-expo);
            font-family: var(--font-body); font-size: 13px; font-weight: 700;
            color: var(--ink-light);
        }
        .upvote-btn:hover {
            border-color: var(--slate);
            color: var(--slate);
            background: var(--info-bg);
            transform: translateY(-2px);
            box-shadow: 0 0 16px rgba(64,232,255,0.15);
        }
        .upvote-btn:active { transform: scale(0.93); }
        .upvote-btn.active {
            border-color: var(--slate);
            color: var(--slate);
            background: rgba(0, 212, 245, 0.08);
            box-shadow: 0 0 12px rgba(64,232,255,0.12);
        }
        .upvote-btn.active .arrow {
            color: var(--slate);
        }
        .upvote-btn .arrow { font-size: 18px; line-height: 1; }

        /* ── Form elements ─────────── */
        .form-group { margin-bottom: 24px; }
        .form-group label {
            display: block; font-weight: 600; font-size: 14px;
            color: var(--ink); margin-bottom: 8px;
        }
        .form-input, .form-textarea, .form-select {
            width: 100%; padding: 12px 16px;
            font-family: var(--font-body); font-size: 15px;
            border: 1px solid var(--border); border-radius: var(--radius-sm);
            background: var(--card-bg); color: var(--ink);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
            min-height: 44px;
        }
        .form-input:focus, .form-textarea:focus, .form-select:focus {
            outline: none; border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(64,232,255,0.15);
        }
        .form-textarea { resize: vertical; min-height: 100px; }

        /* ── Search ────────────────── */
        .search-box {
            position: relative; max-width: 600px; margin: 0 auto;
        }
        .search-box input {
            width: 100%; padding: 14px 20px 14px 48px;
            font-size: 16px; font-family: var(--font-body);
            border: 2px solid var(--border); border-radius: 999px;
            background: var(--card-bg);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
            box-shadow: var(--shadow-sm);
        }
        .search-box input:focus {
            outline: none; border-color: var(--accent);
            box-shadow: 0 0 0 4px rgba(64,232,255,0.12);
        }
        .search-box .search-icon {
            position: absolute; left: 18px; top: 50%; transform: translateY(-50%);
            font-size: 18px; color: var(--ink-muted);
        }

        /* ── Badges ────────────────── */
        .badge {
            display: inline-flex; align-items: center; gap: 4px;
            font-size: var(--text-xs); font-weight: 600;
            padding: 4px 8px; border-radius: 999px;
            border: 1px solid transparent;
        }
        .badge-success { color: var(--success-text); background: var(--success-bg); border-color: var(--success-border); }
        .badge-warning { color: var(--warning-text); background: var(--warning-bg); border-color: var(--gold); }
        .badge-danger  { color: var(--error-text); background: var(--error-bg); border-color: var(--error-border); }
        .badge-info    { color: var(--info-text); background: var(--info-bg); border-color: var(--info-border); }
        .badge-muted   { color: var(--ink-muted); background: var(--cream-dark); border-color: var(--border); }
        .badge-gold    { color: var(--gold-dark); background: linear-gradient(135deg, var(--gold-light), var(--gold)); border-color: var(--gold); }

        /* ── Section Divider ──────── */
        .section-divider {
            margin-top: 48px; padding-top: 24px; border-top: none; position: relative;
        }
        .section-divider::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            opacity: 0.3;
        }

        /* ── Price Pill ───────────── */
        .pill-price {
            display: inline-block; background: var(--terracotta); color: var(--slate);
            font-size: var(--text-xs); font-weight: 600;
            padding: 4px 8px; border-radius: 4px;
        }

        /* ── Alert / Flash ─────────── */
        .alert {
            padding: 16px 24px; border-radius: var(--radius-sm);
            font-size: 14px; font-weight: 500; margin-bottom: 24px;
        }
        .alert-success { background: var(--success-bg); color: var(--success-text); border: 1px solid var(--success-border); }
        .alert-error { background: var(--error-bg); color: var(--error-text); border: 1px solid var(--error-border); }
        .alert-info { background: var(--info-bg); color: var(--info-text); border: 1px solid var(--info-border); }

        /* ── Pagination ────────────── */
        .pagination {
            display: flex; gap: 8px; justify-content: center;
            align-items: center; margin-top: 32px; flex-wrap: wrap;
        }
        .pagination a, .pagination span {
            display: inline-flex; align-items: center; justify-content: center;
            min-width: 40px; height: 40px; border-radius: 999px;
            font-weight: 600; font-size: 14px; padding: 0 4px;
            border: 1px solid var(--border); color: var(--ink-light);
            text-decoration: none;
        }
        .pagination a:hover { background: var(--cream-dark); }
        .pagination .active {
            background: var(--terracotta); color: white; border-color: var(--terracotta);
        }
        .pagination .ellipsis {
            border: none; color: var(--ink-light); pointer-events: none;
            min-width: 32px; font-size: 16px;
        }
        .pagination .prev-next {
            padding: 0 12px; font-size: 13px; gap: 4px;
        }
        .pagination .disabled {
            opacity: 0.35; pointer-events: none;
        }

        /* ── Utility ───────────────── */
        .text-center { text-align: center; }
        .mt-2 { margin-top: 8px; } .mt-4 { margin-top: 16px; } .mt-8 { margin-top: 32px; }
        .mb-2 { margin-bottom: 8px; } .mb-4 { margin-bottom: 16px; } .mb-8 { margin-bottom: 32px; }
        .text-muted { color: var(--ink-muted); }
        .text-sm { font-size: 14px; }

        /* ── Pill Filter ──────────── */
        .pill-filter {
            display: inline-flex; align-items: center; padding: 10px 16px; min-height: 44px; border-radius: 999px;
            font-size: 12px; font-weight: 600; cursor: pointer;
            border: 1px solid var(--border); background: var(--card-bg); color: var(--ink-light);
            font-family: var(--font-body); transition: all var(--duration-fast) ease;
            text-decoration: none; white-space: nowrap; box-sizing: border-box;
        }
        .pill-filter:hover { border-color: var(--terracotta); color: var(--ink); }
        .pill-filter.active { background: var(--terracotta); color: white; border-color: var(--terracotta); }

        /* ── Copy Button ──────────── */
        .copy-btn {
            font-size: 11px; font-weight: 600; padding: 10px 16px; min-height: 44px; min-width: 44px; border-radius: 999px;
            border: 1px solid var(--border); background: var(--card-bg); cursor: pointer;
            color: var(--ink-muted); font-family: var(--font-body); transition: all var(--duration-fast) ease;
            box-sizing: border-box;
        }
        .copy-btn:hover { border-color: var(--terracotta); color: var(--ink); }
        .copy-btn:active { transform: scale(0.96); }

        /* ── Glassmorphism Nav ─────── */
        .backdrop-nav {
            backdrop-filter: var(--backdrop-blur); -webkit-backdrop-filter: var(--backdrop-blur);
            background: var(--nav-bg-glass) !important;
        }

        /* ── Card Stagger Animation ── */
        @keyframes card-enter {
            from { opacity: 0; transform: translateY(24px) scale(0.97); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .card-stagger > * {
            opacity: 0; animation: card-enter 0.6s var(--ease-out-expo) forwards;
        }
        .card-stagger > :nth-child(1) { animation-delay: calc(0 * var(--stagger-delay)); }
        .card-stagger > :nth-child(2) { animation-delay: calc(1 * var(--stagger-delay)); }
        .card-stagger > :nth-child(3) { animation-delay: calc(2 * var(--stagger-delay)); }
        .card-stagger > :nth-child(4) { animation-delay: calc(3 * var(--stagger-delay)); }
        .card-stagger > :nth-child(5) { animation-delay: calc(4 * var(--stagger-delay)); }
        .card-stagger > :nth-child(6) { animation-delay: calc(5 * var(--stagger-delay)); }
        .card-stagger > :nth-child(7) { animation-delay: calc(6 * var(--stagger-delay)); }
        .card-stagger > :nth-child(8) { animation-delay: calc(7 * var(--stagger-delay)); }
        .card-stagger > :nth-child(9) { animation-delay: calc(8 * var(--stagger-delay)); }
        .card-stagger > :nth-child(n+10) { animation-delay: calc(9 * var(--stagger-delay)); }
        @media (prefers-reduced-motion: reduce) { .card-stagger > * { opacity: 1; animation: none; } }

        /* ── Button Press State ───── */
        .btn:active { transform: scale(0.95); transition-duration: 0.05s; }
        [data-theme="dark"] .btn-primary { box-shadow: 0 0 24px rgba(64,232,255,0.2); }
        [data-theme="dark"] .btn-primary:hover { box-shadow: 0 0 32px rgba(64,232,255,0.35); }

        /* ── Custom Checkbox ──────── */
        .custom-checkbox {
            appearance: none; -webkit-appearance: none; width: 20px; height: 20px;
            border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; background: var(--card-bg);
            cursor: pointer; position: relative; transition: all var(--duration-fast) ease; flex-shrink: 0;
        }
        .custom-checkbox:checked { background: var(--accent); border-color: var(--accent); }
        .custom-checkbox:checked::after {
            content: ''; position: absolute; left: 5px; top: 2px;
            width: 6px; height: 10px; border: solid #000; border-width: 0 2px 2px 0; transform: rotate(45deg);
        }
        .custom-checkbox:focus-visible { outline: none; box-shadow: 0 0 0 2px var(--card-bg), 0 0 0 4px var(--accent); }

        /* ── Custom Select Pill ───── */
        .form-select-pill {
            max-width: 180px; font-size: 13px; padding: 8px 32px 8px 12px; border-radius: 999px;
            border: 1px solid var(--border);
            background: var(--card-bg) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 5l3 3 3-3' fill='none' stroke='%236B7280' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E") no-repeat right 12px center;
            appearance: none; -webkit-appearance: none; font-family: var(--font-body); font-weight: 500;
            color: var(--ink); cursor: pointer; transition: border-color var(--duration-fast) ease; min-height: 36px;
        }
        .form-select-pill:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(64,232,255,0.15); }

        /* ── Verified Badge ────────── */
        .verified-badge {
            display: inline-flex; align-items: center; gap: 4px;
            font-size: 12px; font-weight: 700;
            color: #0a4f5c;
            background: var(--accent);
            padding: 4px 12px; border-radius: 999px;
            border: 1px solid var(--accent);
        }
        .verified-badge svg { width: 14px; height: 14px; fill: none; stroke: #0a4f5c; }
        .verified-card { border-color: var(--accent); border-top-color: var(--accent); background: linear-gradient(180deg, rgba(64,232,255,0.06) 0%, var(--card-bg) 40%); }
        .verified-card:hover { box-shadow: var(--shadow-lifted); }

        /* ── Toast notification ───── */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: var(--terracotta);
            color: white;
            padding: 12px 24px;
            border-radius: var(--radius-sm);
            font-size: 14px;
            font-weight: 600;
            font-family: var(--font-body);
            z-index: 9999;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.3s ease, transform 0.3s ease;
            pointer-events: none;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }
        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }

        /* ── Dark mode transitions ── */
        body, .card, nav, footer, .form-input, .form-textarea, .form-select {
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }

        [data-theme="dark"] .alert-success { background: var(--success-bg); color: var(--success-text); border-color: var(--success-border); }
        [data-theme="dark"] .alert-error { background: var(--error-bg); color: var(--error-text); border-color: var(--error-border); }
        [data-theme="dark"] .alert-info { background: var(--info-bg); color: var(--info-text); border-color: var(--info-border); }
        [data-theme="dark"] .verified-card { border-color: var(--accent); background: linear-gradient(180deg, rgba(64,232,255,0.08) 0%, var(--card-bg) 40%); }
        [data-theme="dark"] .card:hover { box-shadow: var(--shadow-lg); }

        /* Dark mode form inputs */
        [data-theme="dark"] .form-input,
        [data-theme="dark"] .form-textarea,
        [data-theme="dark"] .form-select {
            background: rgba(0,0,0,0.2);
            border-color: rgba(255,255,255,0.1);
            color: var(--ink);
        }
        [data-theme="dark"] .form-input:focus,
        [data-theme="dark"] .form-textarea:focus,
        [data-theme="dark"] .form-select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0,212,245,0.15), inset 0 2px 4px rgba(0,0,0,0.2);
        }
        /* Dark mode select styling */
        [data-theme="dark"] select,
        [data-theme="dark"] .form-select-pill {
            background-color: var(--card-bg);
            border-color: rgba(255,255,255,0.1);
            color: var(--ink);
        }
        [data-theme="dark"] select option {
            background-color: var(--card-bg);
            color: var(--ink);
        }
        /* Light mode select option readability */
        select option {
            background-color: var(--card-bg);
            color: var(--terracotta);
        }
        /* Global focus reset — no browser default rings */
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0,212,245,0.15);
            transition: all 0.2s ease;
        }

        /* Mobile nav */
        .nav-links { display: flex; align-items: center; gap: 24px; font-size: 14px; font-weight: 500; }
        .hamburger { display: none; background: none; border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; cursor: pointer; font-size: 20px; color: var(--ink); min-width: 44px; min-height: 44px; }
        .mobile-menu { display: none; }

        /* Nav dropdown */
        .nav-dropdown .nav-dropdown-menu {
            opacity: 0; transform: translateY(8px) translateX(-50%); pointer-events: none;
            transition: opacity var(--duration-normal) var(--ease-out-expo), transform var(--duration-normal) var(--ease-out-expo);
        }
        .nav-dropdown.open .nav-dropdown-menu { display: block !important; opacity: 1; transform: translateY(0) translateX(-50%); pointer-events: auto; }
        .nav-dropdown-menu a:hover { background: var(--cream-dark); color: var(--ink) !important; }

        @media (max-width: 768px) {
            .nav-links { display: none; }
            .hamburger { display: block; }
            .mobile-menu.open {
                display: flex; flex-direction: column; gap: 0;
                position: fixed; top: 64px; left: 0; right: 0;
                background: var(--nav-bg); border-bottom: 1px solid var(--border);
                padding: 8px 0; z-index: 99;
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
                max-height: calc(100vh - 64px); overflow-y: auto;
            }
            .mobile-menu a, .mobile-menu button {
                display: block; padding: 12px 24px; color: var(--ink-light);
                text-decoration: none; font-size: 15px; font-weight: 500;
                border: none; background: none; text-align: left; width: 100%;
                cursor: pointer; font-family: var(--font-body);
            }
            .mobile-menu a:hover, .mobile-menu button:hover { background: var(--cream-dark); }
            .mobile-menu .btn-primary {
                margin: 8px 24px; width: auto; text-align: center;
                border-radius: 999px; color: #000 !important;
            }
            [data-theme="dark"] .mobile-menu .btn-primary {
                color: #000 !important;
            }
        }
        details > summary::-webkit-details-marker { display: none; }
        details > summary::marker { display: none; content: ''; }

        /* Nav dropdown items */
        .nav-dropdown-item { display: block; padding: 8px 16px; color: var(--ink-light); font-size: 14px; text-decoration: none; }
        .nav-dropdown-item:hover { background: var(--cream-dark); }

        /* Footer */
        .footer { background: var(--terracotta); color: white; padding: 64px 24px 32px; margin-top: 0; }
        .footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; margin-bottom: 40px; }
        .footer-heading { font-weight: 700; font-size: 14px; margin-bottom: 12px; }
        .footer-link { color: rgba(255,255,255,0.7); font-size: 13px; line-height: 2; display: block; text-decoration: none; }
        .footer-link:hover { color: white; }
        .footer-muted { color: rgba(255,255,255,0.5); font-size: 12px; }
        .footer-email-input::placeholder { color: rgba(255,255,255,0.5); opacity: 1; }
        .footer-bottom { border-top: 1px solid rgba(255,255,255,0.15); padding-top: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
        @media (max-width: 768px) { .footer-grid { grid-template-columns: 1fr 1fr; } }
        @media (max-width: 480px) { .footer-grid { grid-template-columns: 1fr; } }
    </style>
    """


# ── Nav ───────────────────────────────────────────────────────────────────

def nav_html(user=None) -> str:
    if user:
        user_name = escape(str(user.get('name', '') or user.get('email', '')))
        initial = user_name[0].upper() if user_name else '?'
        avatar_html = user_avatar_html(user, size=32, is_own=True)
        auth_links = f"""
                <a href="/dashboard" style="color:var(--ink-light);">Dashboard</a>
                <a href="/dashboard/notifications" style="position:relative;color:var(--ink-light);font-size:18px;text-decoration:none;"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg></a>
                <div style="display:flex;align-items:center;gap:8px;">
                    {avatar_html}
                    <span style="color:var(--ink);font-size:13px;font-weight:600;">{user_name}</span>
                    {cofounder_badge_html() if user.get('email', '').lower() in {e.lower() for e in COFOUNDER_EMAILS} else pro_badge_html() if user.get('is_pro') else ''}
                </div>
                <a href="/logout" style="color:var(--ink-muted);font-size:13px;">Log out</a>
        """
        mobile_auth_links = f"""
                <a href="/dashboard">Dashboard</a>
                <a href="/dashboard/notifications">Notifications</a>
                <a href="/logout">Log out</a>
        """
    else:
        auth_links = """
                <a href="/login" style="color:var(--ink-light);">Log in</a>
                <a href="/signup" class="btn btn-secondary" style="padding:8px 16px;font-size:13px;">Sign up</a>
        """
        mobile_auth_links = """
                <a href="/login">Log in</a>
                <a href="/signup">Sign up</a>
        """
    # Email verification banner
    verification_banner = ""
    if user and not user.get('email_verified', 1):
        verification_banner = '''
    <div style="background:var(--warning-bg);color:var(--warning-text);padding:12px 24px;text-align:center;font-size:14px;border-bottom:1px solid var(--gold);">
        Please verify your email address.
        <a href="/resend-verification" style="color:var(--warning-text);font-weight:600;text-decoration:underline;margin-left:8px;">Resend verification email</a>
    </div>
        '''

    return f"""
    <nav class="backdrop-nav" style="position:sticky;top:0;z-index:100;border-bottom:1px solid var(--border);">
        <div class="container" style="display:flex;align-items:center;justify-content:space-between;height:64px;">
            <a href="/" style="display:flex;align-items:center;">
                <img src="/logo.png" height="40" alt="IndieStack">
            </a>
            <div class="nav-links">
                <a href="/explore" style="color:var(--ink-light);">Explore</a>
                <a href="/setup" style="color:var(--ink-light);">Set Up MCP</a>
                <a href="/migrations" style="color:var(--ink-light);">Migrations</a>
                <a href="/oracle" style="color:var(--ink-light);">Oracle API</a>
                <a href="/pricing" style="color:var(--ink-light);">Pricing</a>
                <a href="/submit" class="btn btn-primary" style="padding:8px 16px;font-size:13px;">Submit</a>
                <button onclick="toggleTheme()" id="theme-toggle" aria-label="Toggle dark mode" style="background:none;border:1px solid var(--border);border-radius:999px;padding:8px 12px;cursor:pointer;font-size:14px;color:var(--ink-muted);transition:all 0.15s ease;min-width:44px;min-height:44px;" title="Toggle dark mode">&#9790;</button>
                {auth_links}
            </div>
            <button class="hamburger" onclick="document.getElementById('mobile-menu').classList.toggle('open')" aria-label="Menu">&#9776;</button>
        </div>
        <div class="mobile-menu" id="mobile-menu">
            <a href="/explore">Explore</a>
            <a href="/setup">Set Up MCP</a>
            <a href="/migrations">Migrations</a>
            <a href="/oracle">Oracle API</a>
            <a href="/pricing">Pricing</a>
            {mobile_auth_links}
            <a href="/submit">Submit a Tool</a>
            <button onclick="toggleTheme()">Toggle Theme</button>
        </div>
    </nav>
    {verification_banner}
    """


# ── Sticky Email Bar ──────────────────────────────────────────────────────

def email_sticky_bar():
    """Sticky bottom email capture bar for browse pages."""
    return """
    <div id="sticky-email-bar" style="position:fixed;bottom:0;left:0;right:0;z-index:99;
        background:linear-gradient(135deg, var(--terracotta), var(--terracotta-dark));
        padding:16px 24px;box-shadow:0 -4px 20px rgba(0,0,0,0.15);">
        <form id="sticky-email-form" style="max-width:800px;margin:0 auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <span style="color:white;font-size:14px;font-weight:500;white-space:nowrap;">
                Get weekly indie picks straight to your inbox</span>
            <input type="email" name="email" placeholder="you@example.com" required
                aria-label="Email address"
                style="border:none;border-radius:999px;padding:10px 16px;font-size:14px;
                min-width:200px;flex:1;outline:none;">
            <button type="submit" style="background:var(--slate);color:var(--terracotta);
                font-weight:700;border:none;border-radius:999px;padding:10px 20px;min-height:44px;
                cursor:pointer;white-space:nowrap;">Subscribe</button>
            <button type="button" id="sticky-dismiss" aria-label="Dismiss" style="color:rgba(255,255,255,0.6);font-size:20px;
                cursor:pointer;background:none;border:none;padding:10px 12px;min-height:44px;min-width:44px;box-sizing:border-box;">&times;</button>
        </form>
    </div>
    <style>
    @media(max-width:600px){
        #sticky-email-bar form{flex-wrap:wrap;}
        #sticky-email-bar form>span{width:100%;}
        #sticky-email-bar form>input{width:100%;}
        #sticky-email-bar form>button[type="submit"]{width:100%;}
    }
    </style>
    <script>
    (function(){
        var bar = document.getElementById('sticky-email-bar');
        if (!bar) return;
        if (sessionStorage.getItem('sticky_dismissed') || location.search.includes('subscribed=1')) {
            bar.style.display = 'none';
            return;
        }
        document.getElementById('sticky-dismiss').addEventListener('click', function() {
            bar.style.display = 'none';
            sessionStorage.setItem('sticky_dismissed', '1');
        });
        document.getElementById('sticky-email-form').addEventListener('submit', function(e) {
            e.preventDefault();
            var em = this.email.value;
            fetch('/api/subscribe', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'email=' + encodeURIComponent(em) + '&source=sticky_bar'
            }).then(function() {
                bar.innerHTML = '<p style="color:white;font-weight:600;font-size:14px;text-align:center;margin:0;padding:8px 0;">You\\'re in! Check your inbox.</p>';
            }).catch(function() {
                bar.innerHTML = '<p style="color:var(--danger);font-size:14px;text-align:center;margin:0;">Something went wrong. Try again.</p>';
            });
        });
    })();
    </script>"""


# ── Footer ────────────────────────────────────────────────────────────────

def footer_html() -> str:
    return '''
    <footer class="footer">
      <div style="max-width:1100px;margin:0 auto;">
        <div class="footer-grid">
          <!-- Brand -->
          <div>
            <div style="font-family:var(--font-display);font-size:22px;font-weight:700;margin-bottom:8px;">IndieStack</div>
            <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.6;margin:0;">Dependency guardrail for AI coding agents. Validates packages, catches hallucinations, migration intelligence.</p>
          </div>
          <!-- Product -->
          <div>
            <div class="footer-heading">Product</div>
            <a href="/explore" class="footer-link">Explore</a>
            <a href="/migrations" class="footer-link">Migrations</a>
            <a href="/oracle" class="footer-link">Oracle API</a>
            <a href="/agents" class="footer-link">Agent Services</a>
            <a href="/gaps" class="footer-link">Market Gaps</a>
            <a href="/analyze" class="footer-link">Stack Health</a>
            <a href="/api" class="footer-link">REST API</a>
          </div>
          <!-- Company -->
          <div>
            <div class="footer-heading">Company</div>
            <a href="/about" class="footer-link">About</a>
            <a href="/submit" class="footer-link">Submit</a>
            <a href="/changelog" class="footer-link">Changelog</a>
            <a href="https://github.com/Pattyboi101/indiestack" class="footer-link">GitHub</a>
          </div>
          <!-- Legal -->
          <div>
            <div class="footer-heading">Legal</div>
            <a href="/terms" class="footer-link">Terms of Service</a>
            <a href="/privacy" class="footer-link">Privacy Policy</a>
            <a href="mailto:pajebay1@gmail.com?subject=Bug%20Report%20%E2%80%94%20IndieStack&body=What%20happened%3A%0A%0AWhat%20I%20expected%3A%0A%0APage%20URL%3A%0A" class="footer-link">Report a Bug</a>
          </div>
        </div>
        <div class="footer-bottom">
          <div style="text-align:center;margin-bottom:24px;">
    <p style="color:rgba(255,255,255,0.85);font-size:14px;font-weight:600;margin-bottom:12px;">Get weekly picks — the best new developer tools in your inbox.</p>
    <form action="/api/subscribe" method="POST" style="display:flex;gap:8px;justify-content:center;max-width:400px;margin:0 auto;">
        <input type="email" name="email" required placeholder="you@example.com"
               style="flex:1;padding:8px 14px;border-radius:999px;border:1px solid rgba(255,255,255,0.3);
                      background:rgba(255,255,255,0.1);color:white;font-size:14px;font-family:var(--font-body);
                      --placeholder-color:rgba(255,255,255,0.5);"
               class="footer-email-input">
        <button type="submit" style="padding:8px 18px;border-radius:999px;border:none;
                background:var(--slate);color:white;font-weight:600;font-size:14px;cursor:pointer;
                font-family:var(--font-body);">Subscribe</button>
    </form>
</div>
          <span style="color:rgba(255,255,255,0.7);font-size:13px;font-weight:600;display:block;width:100%;text-align:center;margin-bottom:12px;">Dependency guardrail for AI coding agents.</span>
          <span class="footer-muted">&copy; 2026 IndieStack. All rights reserved.</span>
          <span class="footer-muted">Made with care for the indie maker community.</span>
        </div>
      </div>
    </footer>
    '''


# ── Indie Badge ──────────────────────────────────────────────────────────

def indie_badge_html(indie_status: str) -> str:
    """Render indie maker status badge."""
    if indie_status == 'solo':
        return '<span class="badge badge-info">Solo Maker</span>'
    elif indie_status == 'small_team':
        return '<span class="badge badge-info">Small Team</span>'
    return ''


def ejectable_badge_html() -> str:
    """Render Certified Ejectable badge — signals clean data export / no lock-in."""
    return '<span class="badge badge-success"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg> Ejectable</span>'


def maker_pulse_html(last_active: str) -> str:
    """Render a 'last updated' pulse badge showing how recently the tool was maintained."""
    if not last_active:
        return ''
    try:
        from datetime import datetime
        last_dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
        now = datetime.utcnow()
        delta = (now - last_dt.replace(tzinfo=None)).days
    except Exception:
        return ''

    if delta <= 7:
        badge_class = 'badge-success'
        label = 'Updated this week'
    elif delta <= 30:
        badge_class = 'badge-success'
        label = f'Updated {delta}d ago'
    elif delta <= 90:
        badge_class = 'badge-warning'
        label = f'Updated {delta}d ago'
    elif delta <= 365:
        badge_class = 'badge-muted'
        label = f'Updated {delta // 30}mo ago'
    else:
        badge_class = 'badge-muted'
        label = f'Updated {delta // 365}y ago'

    return f'<span class="badge {badge_class}"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--success-text,#22C55E);vertical-align:middle;margin-right:4px;"></span> {label}</span>'


def integration_snippet_html(tool: dict) -> str:
    """Render integration code snippets for a purchased tool."""
    name = escape(str(tool.get('name', 'tool')))
    url = escape(str(tool.get('url', 'https://example.com')))
    delivery_url = escape(str(tool.get('delivery_url', '')))

    # Prefer custom snippets from database, fall back to generic
    python_snippet = tool.get('integration_python') or f'''import httpx

# {name} — via IndieStack
client = httpx.Client(base_url="{url}")

# Example: check the tool is reachable
resp = client.get("/")
print(f"{name} status: {{resp.status_code}}")'''

    curl_snippet = tool.get('integration_curl') or f'''# Quick test — {name}
curl -s "{url}" -o /dev/null -w "%{{http_code}}"'''

    return f"""
    <div style="margin-top:32px;">
        <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:12px;color:var(--ink);">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-2px;"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg> Quick Integration
        </h3>
        <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
            Copy-paste this into your project to get started with {name}.
        </p>
        <div style="margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span class="badge badge-info" style="font-weight:700;">Python</span>
                <button onclick="navigator.clipboard.writeText(document.getElementById('snippet-py').textContent);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                        class="copy-btn">Copy</button>
            </div>
            <pre id="snippet-py" style="background:#1A1A2E;color:var(--slate);border-radius:var(--radius-sm);padding:16px 20px;
                        font-family:var(--font-mono);font-size:13px;line-height:1.7;overflow-x:auto;margin:0;">{python_snippet}</pre>
        </div>
        <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:12px;font-weight:700;color:var(--ink-muted);background:var(--cream-dark);padding:2px 10px;border-radius:999px;">cURL</span>
                <button onclick="navigator.clipboard.writeText(document.getElementById('snippet-curl').textContent);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                        class="copy-btn">Copy</button>
            </div>
            <pre id="snippet-curl" style="background:#1A1A2E;color:var(--slate);border-radius:var(--radius-sm);padding:16px 20px;
                        font-family:var(--font-mono);font-size:13px;line-height:1.7;overflow-x:auto;margin:0;">{curl_snippet}</pre>
        </div>
    </div>
    """


# Co-founder emails — loaded from env to keep out of public repo
import os as _os
COFOUNDER_EMAILS = set(filter(None, _os.environ.get("COFOUNDER_EMAILS", "").split(",")))


def cofounder_badge_html() -> str:
    """Render co-founder badge."""
    return '<span class="badge badge-gold" style="font-weight:700;">&#9733; Co-founder</span>'


def maker_discount_badge_html() -> str:
    """Green pill badge showing Indie Ring 50% maker discount."""
    return '<span class="badge badge-success" style="font-weight:700;"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-1px;"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg> 50% off &middot; Indie Ring</span>'


def indie_score_html(tool: dict) -> str:
    """Calculate and render an Indie Score badge (0-100)."""
    score = 0
    # Solo maker: +30 / Small team: +20
    indie_status = str(tool.get('indie_status', ''))
    if indie_status == 'solo':
        score += 30
    elif indie_status == 'small_team':
        score += 20
    # Has reviews (review_count field): +15
    if int(tool.get('review_count', 0)) > 0:
        score += 15
    # Affordable (< £50 = 5000 pence): +10
    price = tool.get('price_pence')
    if price is None or (isinstance(price, int) and price < 5000):
        score += 10
    # Detailed description (> 100 chars): +10
    if len(str(tool.get('description', ''))) > 100:
        score += 10
    # Has maker profile: +10
    if tool.get('maker_id'):
        score += 10

    # Badge class based on score
    if score >= 70:
        badge_class = 'badge-success'
    elif score >= 40:
        badge_class = 'badge-warning'
    else:
        badge_class = 'badge-muted'

    return f'''<span class="badge {badge_class}" style="gap:6px;font-size:12px;font-weight:700;padding:4px 12px;">
        <span style="display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;
                     border-radius:50%;background:currentColor;font-size:10px;font-weight:800;">
            <span style="color:white;">{score}</span>
        </span>
        Indie Score
    </span>'''


def stack_card(stack: dict) -> str:
    """Card component for a stack — shows intelligence metadata for auto stacks."""
    title = escape(str(stack['title']))
    desc = escape(str(stack.get('description', '')))
    slug = escape(str(stack['slug']))
    count = stack.get('tool_count', 0) or stack.get('tool_count_cached', 0)
    confidence = stack.get('confidence_score', 0) or 0
    tokens_k = (stack.get('total_tokens_saved', 0) or 0) // 1000
    source = stack.get('source', 'curated')

    badges = []
    badges.append(
        f'<span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);'
        f'padding:4px 12px;border-radius:999px;">{count} tool{"s" if count != 1 else ""}</span>'
    )
    if confidence > 0 and source in ('auto-framework', 'auto-usecase'):
        # Show pair verification count instead of raw confidence %
        tool_n = int(count) if count else 0
        max_pairs = tool_n * (tool_n - 1) // 2 if tool_n >= 2 else 0
        # Estimate verified pairs from confidence: verified contribute 0.7-1.0, inferred 0.3
        # For display, show "agent-verified pairs" as a positive signal
        if max_pairs > 0:
            badges.append(
                f'<span style="font-size:12px;font-weight:600;color:var(--success-text);background:var(--success-bg);'
                f'padding:4px 12px;border-radius:999px;">agent-verified pairs</span>'
            )
    elif confidence > 0:
        conf_pct = f"{confidence:.0%}"
        badges.append(
            f'<span style="font-size:12px;font-weight:600;color:var(--success-text);background:var(--success-bg);'
            f'padding:4px 12px;border-radius:999px;">{conf_pct} confidence</span>'
        )
    if tokens_k > 0:
        badges.append(
            f'<span style="font-size:12px;font-weight:600;color:var(--warning-text);background:var(--warning-bg);'
            f'padding:4px 12px;border-radius:999px;">~{tokens_k}k tokens saved</span>'
        )
    discount = stack.get('discount_percent', 0)
    if discount and discount > 0 and source == 'curated':
        badges.append(f'<span class="badge badge-success" style="font-weight:700;">{discount}% off</span>')

    badges_html = "\n".join(badges)

    replaces_html = ""
    replaces_raw = stack.get('replaces_json')
    if replaces_raw:
        try:
            replaces = json.loads(replaces_raw) if isinstance(replaces_raw, str) else replaces_raw
            if replaces:
                preview = ", ".join(replaces[:3])
                if len(replaces) > 3:
                    preview += f" +{len(replaces) - 3} more"
                replaces_html = (
                    f'<p style="color:var(--ink-muted);font-size:12px;margin-top:8px;">'
                    f'Replaces: {escape(preview)}</p>'
                )
        except (json.JSONDecodeError, TypeError):
            pass

    # Category icons from the stack's tools (same SVG icons as "Browse by Category")
    from indiestack.routes.category_icons import category_icon
    cat_slugs = stack.get('_category_slugs', [])
    if cat_slugs:
        icon_items = [
            f'<span style="color:var(--accent);display:flex;align-items:center;">{category_icon(cs, size=22)}</span>'
            for cs in cat_slugs[:4]
        ]
        icons_html = '<div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">' + ''.join(icon_items) + '</div>'
    else:
        emoji = stack.get('cover_emoji', '') or '\U0001f4e6'
        icons_html = f'<span style="font-size:32px;display:block;margin-bottom:8px;">{emoji}</span>'

    upvote_count = stack.get('upvote_count', 0) or 0
    count_display = str(upvote_count) if upvote_count >= 3 else ''
    stack_id = stack.get('id', 0)
    upvote_html = (
        f'<button class="upvote-btn" onclick="event.preventDefault();stackUpvote({stack_id})" id="stack-upvote-{stack_id}" aria-label="Upvote {title}">'
        f'<span class="arrow">&#9650;</span>'
        f'<span id="stack-count-{stack_id}">{count_display}</span>'
        f'</button>'
    )

    return f"""
    <div class="card" style="position:relative;display:flex;gap:16px;">
        <a href="/stacks/{slug}" style="flex:1;min-width:0;text-decoration:none;color:inherit;display:block;">
            {icons_html}
            <h3 style="font-family:var(--font-display);font-size:17px;margin-bottom:8px;color:var(--ink);">{title}</h3>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;
                      display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{desc}</p>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
                {badges_html}
            </div>
            {replaces_html}
        </a>
        {upvote_html}
    </div>
    """


# ── Tool Card ─────────────────────────────────────────────────────────────

def verified_badge_html() -> str:
    """Verified badge for claimed + Pro makers — signals active, trusted tool."""
    return '<span style="display:inline-flex;align-items:center;gap:3px;background:linear-gradient(135deg,rgba(0,212,245,0.1),rgba(0,212,245,0.05));color:var(--accent);font-size:10px;font-weight:700;padding:3px 8px;border-radius:4px;border:1px solid rgba(0,212,245,0.2);text-transform:uppercase;letter-spacing:0.3px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1l3.09 6.26L22 8.27l-5 4.87 1.18 6.88L12 16.77l-6.18 3.25L7 13.14 2 8.27l6.91-1.01L12 1z"/></svg> Verified</span>'


def pro_badge_html() -> str:
    """Small Pro badge for tool cards and maker cards."""
    return '<span style="display:inline-block;background:var(--accent);color:white;font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;text-transform:uppercase;letter-spacing:0.5px;">Pro</span>'


def boosted_badge_html():
    """Render Featured/Boosted badge for tool cards."""
    return '<span class="badge" style="font-weight:700;color:var(--terracotta);background:linear-gradient(135deg,var(--slate),var(--slate-light));">&#9733; Featured</span>'


def pixel_icon_svg(pixel_data: str, size: int = 24) -> str:
    """Render a 7x7 pixel art icon as inline SVG."""
    PIXEL_COLORS = {
        '1': '#1A2D4A', '2': '#00D4F5', '3': '#E2B764',
        '4': '#FFFFFF', '5': '#64748B', '6': '#E07A5F', '7': '#22C55E',
        '8': '#000000', '9': '#EF4444', 'a': '#EC4899',
        'b': '#8B5CF6', 'c': '#F97316', 'd': '#7DD3FC',
        'e': '#86EFAC', 'f': '#92400E',
    }
    if not pixel_data or len(pixel_data) != 49:
        return ''
    cell = size / 7
    rects = ''
    for i, c in enumerate(pixel_data):
        color = PIXEL_COLORS.get(c)
        if color:
            x, y = (i % 7) * cell, (i // 7) * cell
            rects += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}"/>'
    if not rects:
        return ''
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="border-radius:4px;border:1px solid var(--border);flex-shrink:0;">{rects}</svg>'


def user_avatar_html(user: dict, size: int = 32, is_own: bool = False) -> str:
    """Render user avatar: pixel art → GitHub avatar → letter initial."""
    name = str(user.get('name', '') or user.get('email', ''))
    initial = name[0].upper() if name else '?'

    # Pixel art avatar
    pixel_data = str(user.get('pixel_avatar', '') or '')
    approved = bool(user.get('pixel_avatar_approved', 0))
    if pixel_data and len(pixel_data) == 49 and (approved or is_own):
        return pixel_icon_svg(pixel_data, size=size)

    # Letter initial fallback (rounded square)
    font_size = max(10, size // 2.5)
    return (f'<div style="width:{size}px;height:{size}px;border-radius:4px;background:var(--terracotta);'
            f'color:white;display:flex;align-items:center;justify-content:center;'
            f'font-size:{font_size:.0f}px;font-weight:700;flex-shrink:0;">{escape(initial)}</div>')


def tool_card(tool: dict, compact: bool = False) -> str:
    name = escape(str(tool['name']))
    tagline = escape(str(tool['tagline']))
    slug = escape(str(tool['slug']))
    cat_name = escape(str(tool.get('category_name', '')))
    cat_slug = escape(str(tool.get('category_slug', '')))
    upvotes = int(tool.get('upvote_count', 0))
    tags = str(tool.get('tags', ''))
    tag_html = ''
    if tags.strip():
        tag_list = [t.strip() for t in tags.split(',') if t.strip()][:3]
        tag_html = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">'
        for t in tag_list:
            tag_html += f'<span class="tag">{escape(t)}</span>'
        tag_html += '</div>'

    # Changelog streak badge — fire emoji if updated in last 14 days
    streak_html = ''
    if tool.get('has_changelog_14d'):
        streak_html = '<span class="badge badge-warning" style="font-weight:700;margin-top:8px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg> Active</span>'

    # Add bookmark icon — positioned absolutely in top-right of card (hidden in compact mode)
    bookmark_html = ''
    if not compact:
        bookmark_html = f'''<button class="wishlist-btn" onclick="event.stopPropagation();toggleWishlist({tool['id']})" id="wishlist-{tool['id']}"
        aria-label="Bookmark {name}"
        style="position:absolute;top:12px;right:12px;z-index:2;background:none;border:none;cursor:pointer;padding:8px;font-size:20px;line-height:1;color:var(--ink-muted);opacity:0.5;transition:color 0.2s,transform 0.2s,opacity 0.2s;min-width:44px;min-height:44px;"
        onmouseenter="this.style.color='#E2B764';this.style.opacity='1';this.style.transform='scale(1.1)';"
        onmouseleave="if(!this.dataset.wishlisted){{this.style.color='var(--ink-muted)';this.style.opacity='0.5';this.style.transform='scale(1)';}}else{{this.style.transform='scale(1)';}}"
        title="Bookmark">&#9734;</button>'''

    visit_html = f'<a href="/api/click/{slug}" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="font-size:12px;color:var(--accent);font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:2px;padding:10px 12px;min-height:44px;box-sizing:border-box;">Visit&nbsp;&rarr;</a>'

    gh_indicator = ''
    if tool.get('github_url'):
        gh_stars = int(tool.get('github_stars', 0))
        if gh_stars:
            gh_indicator = f'<span style="display:inline-flex;align-items:center;gap:3px;font-size:11px;color:var(--ink-muted);margin-top:8px;"><svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg> {gh_stars}&#9733;</span>'

    # AI agent recommendation indicator
    ai_recs_html = ''
    mcp_views = int(tool.get('mcp_view_count', 0))
    if mcp_views > 0:
        ai_recs_html = f'<span style="display:inline-flex;align-items:center;gap:3px;font-size:11px;color:var(--accent);font-weight:600;margin-top:8px;" title="Recommended by AI agents {mcp_views} times"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg> {mcp_views} AI recommendations</span>'

    # Trust badge from agent outcome reports (only shown if success_rate data is present)
    trust_html = ''
    sr_data = tool.get('_success_rate')
    if sr_data and sr_data.get('total', 0) >= 5:
        sr_rate = sr_data['rate']
        sr_total = sr_data['total']
        if sr_rate < 50:
            tr_color = 'var(--error-text, #DC2626)'
            tr_icon = '&#9888;'
            tr_title = f'Low agent success rate: {sr_rate}% from {sr_total} reports'
        elif sr_rate >= 70 and sr_total >= 20:
            tr_color = 'var(--success-text, #16a34a)'
            tr_icon = '&#10003;'
            tr_title = f'Verified: {sr_rate}% success from {sr_total} agent reports'
        else:
            tr_color = 'var(--ink-muted)'
            tr_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>'
            tr_title = f'{sr_rate}% success from {sr_total} agent reports'
        trust_html = f'<span style="display:inline-flex;align-items:center;gap:3px;font-size:11px;color:{tr_color};margin-top:8px;" title="{tr_title}">{tr_icon} {sr_rate}% success ({sr_total})</span>'

    badge = ''
    is_boosted = bool(tool.get('is_boosted', 0))
    if is_boosted:
        badge += ' ' + boosted_badge_html()
    # Show combined "Verified" badge for claimed + Pro, or just "Maker ✓" for claimed-only
    if tool.get('claimed_at') and tool.get('maker_is_pro'):
        badge += ' ' + verified_badge_html()
    elif tool.get('claimed_at'):
        badge += ' <span class="badge badge-success" style="font-size:var(--text-xs);">Maker &#10003;</span>'
    price_pence = tool.get('price_pence')
    if price_pence and price_pence > 0 and not tool.get('stripe_account_id'):
        badge += f' <span class="pill-price">&pound;{price_pence // 100}/mo</span>'
    if tool.get('maker_is_pro') and not tool.get('claimed_at'):
        badge += ' ' + pro_badge_html()
    # Pixel art icon takes priority over favicon
    pixel_icon = str(tool.get('pixel_icon', '') or '')
    pixel_svg = pixel_icon_svg(pixel_icon) if pixel_icon else ''
    if pixel_svg:
        favicon_html = pixel_svg
    else:
        # Favicon — Google service, no letter fallback
        website = str(tool.get('website', '') or '')
        favicon_html = ''
        if website:
            try:
                from urllib.parse import urlparse
                domain = urlparse(website).netloc or urlparse('https://' + website).netloc
                if domain:
                    favicon_html = f'<img src="https://www.google.com/s2/favicons?domain={escape(domain, quote=True)}&sz=32" alt="" width="24" height="24" loading="lazy" style="border-radius:4px;border:1px solid var(--border);flex-shrink:0;" onerror="this.style.display=\'none\'">'
            except Exception:
                pass

    card_class = 'card'

    upvote_html = ''
    if not compact:
        # Hide count when low (< 3) — show just the arrow, count appears after voting
        count_display = str(upvotes) if upvotes >= 3 else ''
        upvote_html = (
            f'<button class="upvote-btn" onclick="upvote({tool["id"]})" id="upvote-{tool["id"]}" aria-label="Upvote {name}">'
            f'<span class="arrow">&#9650;</span>'
            f'<span id="count-{tool["id"]}">{count_display}</span>'
            f'</button>'
        )

    return f"""
    <div class="{card_class}" style="position:relative;display:flex;gap:16px;">
        {bookmark_html}
        <div style="flex:1;min-width:0;display:flex;flex-direction:column;">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding-right:32px;">
                {favicon_html}
                <a href="/tool/{slug}" style="font-family:var(--font-display);font-size:17px;
                                              color:var(--ink);">{name}</a>
                {badge}
            </div>
            <p style="color:var(--ink-muted);font-size:14px;margin-top:4px;
                      overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{tagline}</p>
            <a href="/category/{cat_slug}" class="tag" style="margin-top:12px;display:inline-block;
                                                              font-family:var(--font-mono);">{cat_name}</a>
            {tag_html}
            <div style="display:flex;align-items:center;gap:12px;margin-top:auto;padding-top:12px;flex-wrap:wrap;">
                {f'<a href="/maker/{escape(str(tool.get("maker_slug", "")))}" style="font-size:12px;color:var(--ink-muted);text-decoration:none;display:flex;align-items:center;gap:4px;" title="Made by {escape(str(tool.get("maker_name", "")))}"><span style="color:var(--ink-muted);">by</span> <span style="color:var(--accent);font-weight:600;">{escape(str(tool.get("maker_name", "")))}</span></a>' if tool.get('maker_name') and tool.get('maker_slug') else ''}
                {visit_html}
                {gh_indicator}
                {ai_recs_html}
                {trust_html}
                {streak_html}
            </div>
        </div>
        {upvote_html}
    </div>
    """


# ── Maker Card ───────────────────────────────────────────────────────────

def maker_card(maker: dict, stats: dict = None) -> str:
    """Render a maker card for the directory grid."""
    name = escape(str(maker['name']))
    slug = escape(str(maker['slug']))
    bio = escape(str(maker.get('bio', '')))
    indie_status = str(maker.get('indie_status', ''))

    # Truncate bio
    if len(bio) > 120:
        bio = bio[:117] + '...'

    tool_count = int((stats or maker).get('tool_count', 0))
    total_upvotes = int((stats or maker).get('total_upvotes', 0))

    badge = indie_badge_html(indie_status) if indie_status else ''

    return f"""
    <a href="/maker/{slug}" class="card" style="text-decoration:none;color:inherit;display:block;text-align:center;">
        <div style="display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;
                    border-radius:50%;background:var(--terracotta);color:white;font-size:22px;
                    font-family:var(--font-display);margin-bottom:12px;">
            {name[0].upper() if name else '?'}
        </div>
        <div style="display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;">
            <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);">{name}</h3>
            {badge}
        </div>
        <p style="color:var(--ink-muted);font-size:13px;margin-top:8px;line-height:1.5;">{bio if bio else 'Indie maker'}</p>
        <div style="display:flex;gap:16px;justify-content:center;margin-top:12px;font-size:13px;">
            <span style="color:var(--ink-light);"><strong style="color:var(--ink);">{tool_count}</strong> tools</span>
            <span style="color:var(--ink-light);"><strong style="color:var(--slate-dark);">{total_upvotes}</strong> upvotes</span>
        </div>
    </a>
    """


# ── Update Card ──────────────────────────────────────────────────────────

def update_card(update: dict) -> str:
    """Render a maker update card for the feed."""
    title = escape(str(update.get('title', '')))
    body = escape(str(update.get('body', '')))
    maker_name = escape(str(update.get('maker_name', '')))
    maker_slug = escape(str(update.get('maker_slug', '')))
    update_type = str(update.get('update_type', 'update'))
    created = str(update.get('created_at', ''))[:10]

    type_colors = {
        'update': ('var(--slate)', 'var(--info-bg)', 'Update'),
        'launch': ('var(--terracotta)', 'var(--cream-dark)', 'Launch'),
        'milestone': ('var(--gold)', 'var(--warning-bg)', 'Milestone'),
        'changelog': ('var(--ink-muted)', 'var(--cream-dark)', 'Changelog'),
    }
    color, bg, label = type_colors.get(update_type, type_colors['update'])

    title_html = f'<h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:6px;">{title}</h3>' if title else ''

    return f"""
    <div class="card" style="margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
            <span style="font-size:11px;font-weight:700;color:{color};background:{bg};padding:4px 12px;border-radius:999px;text-transform:uppercase;letter-spacing:0.5px;">{label}</span>
            <span style="font-size:13px;color:var(--ink-muted);">{created}</span>
        </div>
        {title_html}
        <p style="color:var(--ink-light);font-size:14px;line-height:1.6;white-space:pre-line;">{body}</p>
        <div style="margin-top:12px;display:flex;align-items:center;gap:8px;">
            <div style="width:24px;height:24px;border-radius:50%;background:var(--terracotta);color:white;
                        display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;">
                {maker_name[0].upper() if maker_name else '?'}
            </div>
            <a href="/maker/{maker_slug}" style="font-size:13px;font-weight:600;color:var(--ink);">{maker_name}</a>
        </div>
    </div>
    """


# ── Copy-to-Clipboard Script ─────────────────────────────────────────────

def copy_js() -> str:
    """Sitewide copy-to-clipboard with micro-interaction feedback."""
    return '''<script>
document.addEventListener('click', function(e) {
    const btn = e.target.closest('[data-copy]');
    if (!btn) return;
    const text = btn.getAttribute('data-copy');
    if (!text) return;
    navigator.clipboard.writeText(text).then(function() {
        const orig = btn.innerHTML;
        const origBg = btn.style.background;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!';
        btn.style.background = 'var(--accent)';
        btn.style.transform = 'scale(1.05)';
        btn.style.transition = 'transform 0.15s ease, background 0.15s ease';
        fetch('/api/track', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({event:'install_copied', metadata:{text: text.substring(0, 50)}})});
        setTimeout(function() {
            btn.innerHTML = orig;
            btn.style.background = origBg;
            btn.style.transform = 'scale(1)';
        }, 1500);
    });
});
</script>'''


def copy_button(text: str, label: str = "Copy") -> str:
    """Render a copy button with data-copy attribute for the sitewide copy handler."""
    safe = escape(text).replace("'", "&#39;").replace('"', "&quot;")
    return f'<button data-copy="{safe}" style="background:var(--slate,#64748B);color:#fff;border:none;border-radius:999px;padding:6px 14px;min-height:44px;font-size:12px;font-weight:600;cursor:pointer;font-family:var(--font-body);display:inline-flex;align-items:center;gap:4px;">{label}</button>'


# ── Upvote Script ─────────────────────────────────────────────────────────

def upvote_js() -> str:
    return """
    <script>
    async function upvote(toolId) {
        const btn = document.getElementById('upvote-' + toolId);
        const countEl = document.getElementById('count-' + toolId);
        try {
            const res = await fetch('/api/upvote', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({tool_id: toolId})
            });
            const data = await res.json();
            if (data.ok) {
                countEl.textContent = data.count;
                btn.classList.toggle('active', data.upvoted);
                showToast(data.upvoted ? '\u25b2 Upvoted!' : 'Vote removed');
            }
        } catch(e) { console.error(e); }
    }
    // Check upvote state on page load
    document.addEventListener('DOMContentLoaded', async () => {
        const btns = document.querySelectorAll('.upvote-btn');
        if (!btns.length) return;
        const ids = Array.from(btns).map(b => parseInt(b.id.replace('upvote-', ''))).filter(n => n > 0);
        if (!ids.length) return;
        try {
            const res = await fetch('/api/upvote-check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({tool_ids: ids})
            });
            const data = await res.json();
            if (data.upvoted) {
                data.upvoted.forEach(id => {
                    const btn = document.getElementById('upvote-' + id);
                    if (btn) btn.classList.add('active');
                });
            }
        } catch(e) {}
    });
    </script>
    """


# ── Stack Upvote Script ──────────────────────────────────────────────────

def stack_upvote_js() -> str:
    return """
    <script>
    async function stackUpvote(stackId) {
        const btn = document.getElementById('stack-upvote-' + stackId);
        const countEl = document.getElementById('stack-count-' + stackId);
        try {
            const res = await fetch('/api/stack-upvote', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({stack_id: stackId})
            });
            const data = await res.json();
            if (data.ok) {
                countEl.textContent = data.count >= 3 ? data.count : '';
                btn.classList.toggle('active', data.upvoted);
                showToast(data.upvoted ? '\u25b2 Upvoted!' : 'Vote removed');
            }
        } catch(e) { console.error(e); }
    }
    document.addEventListener('DOMContentLoaded', async () => {
        const btns = document.querySelectorAll('[id^="stack-upvote-"]');
        if (!btns.length) return;
        const ids = Array.from(btns).map(b => parseInt(b.id.replace('stack-upvote-', ''))).filter(n => n > 0);
        if (!ids.length) return;
        try {
            const res = await fetch('/api/stack-upvote-check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({stack_ids: ids})
            });
            const data = await res.json();
            if (data.upvoted) {
                data.upvoted.forEach(id => {
                    const btn = document.getElementById('stack-upvote-' + id);
                    if (btn) btn.classList.add('active');
                });
            }
        } catch(e) {}
    });
    </script>
    """


# ── Wishlist Script ──────────────────────────────────────────────────────

def wishlist_js() -> str:
    return """
    <script>
    async function toggleWishlist(toolId) {
        try {
            const res = await fetch('/api/wishlist', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({tool_id: toolId})
            });
            const data = await res.json();
            if (data.ok) {
                const btn = document.getElementById('wishlist-' + toolId);
                if (btn) {
                    btn.innerHTML = data.saved ? '&#9733;' : '&#9734;';
                    btn.style.color = data.saved ? '#E2B764' : 'var(--ink-muted)';
                    btn.style.opacity = data.saved ? '1' : '0.5';
                    if (data.saved) { btn.dataset.wishlisted = '1'; } else { delete btn.dataset.wishlisted; }
                }
                showToast(data.saved ? '\u2605 Bookmarked' : 'Bookmark removed');
            } else if (data.error === 'login_required') {
                window.location.href = '/auth/github?next=' + encodeURIComponent(window.location.pathname);
            }
        } catch(e) { console.error(e); }
    }
    </script>
    """


# ── Theme Toggle Script ──────────────────────────────────────────────────

def theme_js() -> str:
    return """
    <script>
    (function() {
        const saved = localStorage.getItem('indiestack-theme');
        if (saved) {
            document.documentElement.setAttribute('data-theme', saved);
        } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
        // Update toggle icon
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            btn.innerHTML = isDark ? '&#9788;' : '&#9790;';
        }
    })();
    // Close nav dropdown on outside click
    document.addEventListener('click', function(e) {
        document.querySelectorAll('.nav-dropdown.open').forEach(function(dd) {
            if (!dd.contains(e.target)) dd.classList.remove('open');
        });
    });
    function toggleTheme() {
        const html = document.documentElement;
        const isDark = html.getAttribute('data-theme') === 'dark';
        const newTheme = isDark ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('indiestack-theme', newTheme);
        const btn = document.getElementById('theme-toggle');
        if (btn) btn.innerHTML = isDark ? '&#9790;' : '&#9788;';
    }
    </script>
    """


# ── Analytics ─────────────────────────────────────────────────────────────

_CLARITY_SCRIPT = '<script type="text/javascript">(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","wcjqc0vmmu");</script>'

# ── Page Shell ────────────────────────────────────────────────────────────

def page_shell(title: str, body: str, *, description: str = "", extra_head: str = "", user=None, og_image: str = f"{BASE_URL}/logo.png", canonical: str = "") -> str:
    desc = escape(description) if description else "Discover 8,000+ developer tools for AI coding agents. Find indie alternatives for auth, payments, analytics, email, and more — curated for developers."
    canonical_tag = f'\n    <link rel="canonical" href="{BASE_URL}{escape(canonical)}">' if canonical else ""
    # Strip trailing " | IndieStack" or " — IndieStack" to avoid duplication
    clean_title = title
    for suffix in (" | IndieStack", " — IndieStack", " -- IndieStack"):
        if clean_title.endswith(suffix):
            clean_title = clean_title[:-len(suffix)]
            break
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(clean_title)} — IndieStack</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <meta name="description" content="{desc}">{canonical_tag}
    <meta property="og:site_name" content="IndieStack">
    <meta property="og:title" content="{escape(clean_title)} — IndieStack">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="website">
    <meta property="og:image" content="{escape(og_image)}">{f'''
    <meta property="og:url" content="{BASE_URL}{escape(canonical)}">''' if canonical else ''}
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(clean_title)} — IndieStack">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{escape(og_image)}">
    {design_tokens()}
    <link rel="alternate" type="application/rss+xml" title="IndieStack — New Creations" href="{BASE_URL}/feed/rss">
    {_CLARITY_SCRIPT}
    {extra_head}
</head>
<body>
    {nav_html(user=user)}
    {body}
    {footer_html()}
    {upvote_js()}
    {wishlist_js()}
    {theme_js()}
    {copy_js()}
    <div id="toast" class="toast" role="alert" aria-live="polite"></div>
    <script>
    function showToast(message) {{
        var t = document.getElementById('toast');
        if (!t) return;
        t.textContent = message;
        t.classList.add('show');
        clearTimeout(t._timer);
        t._timer = setTimeout(function() {{ t.classList.remove('show'); }}, 2500);
    }}
    (function() {{
        var p = new URLSearchParams(window.location.search);
        var msg = p.get('toast');
        if (msg) {{
            showToast(decodeURIComponent(msg));
            p.delete('toast');
            var clean = p.toString();
            var url = window.location.pathname + (clean ? '?' + clean : '') + window.location.hash;
            window.history.replaceState(null, '', url);
        }}
    }})();
    </script>
</body>
</html>"""


# ── Featured Card ────────────────────────────────────────────────────────

def featured_card(featured: dict) -> str:
    """Render a large featured tool banner for the homepage."""
    name = escape(str(featured['tool_name']))
    slug = escape(str(featured['tool_slug']))
    tagline = escape(str(featured.get('tagline', '')))
    headline = escape(str(featured.get('headline', '')))
    desc = escape(str(featured.get('description', '')))
    badge = ''

    return f"""
    <div class="card" style="background:var(--terracotta);border:none;padding:32px;color:white;
                box-shadow:var(--shadow-md);">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <span style="font-size:var(--text-xs);font-weight:700;text-transform:uppercase;letter-spacing:1.5px;
                         color:var(--slate);">
                Tool of the Week
            </span>
            {badge}
        </div>
        <h3 style="font-family:var(--font-display);font-size:24px;margin-bottom:8px;">
            <a href="/tool/{slug}" style="color:white;text-decoration:none;">{headline or name}</a>
        </h3>
        <p style="color:rgba(255,255,255,0.7);font-size:15px;margin-bottom:24px;line-height:1.6;">{desc or tagline}</p>
        <a href="/tool/{slug}" class="btn" style="background:var(--slate);color:var(--terracotta);font-weight:700;
                padding:12px 24px;">
            View tool
        </a>
    </div>
    """


# ── Pagination Helper ─────────────────────────────────────────────────────

def pagination_html(current: int, total_pages: int, base_url: str) -> str:
    if total_pages <= 1:
        return ""
    sep = "&amp;" if "?" in base_url else "?"

    def href(p):
        return f'{base_url}{sep}page={p}'

    # Build the set of page numbers to show: 1, last, current +/- 1
    visible = sorted({1, total_pages} | {p for p in range(current - 1, current + 2) if 1 <= p <= total_pages})

    parts = ['<div class="pagination">']

    # Prev
    if current > 1:
        parts.append(f'<a href="{href(current - 1)}" class="prev-next">&#8592; Prev</a>')
    else:
        parts.append('<span class="prev-next disabled">&#8592; Prev</span>')

    # Page numbers with ellipsis in gaps
    last = 0
    for p in visible:
        if last and p - last > 1:
            parts.append('<span class="ellipsis">&#8230;</span>')
        if p == current:
            parts.append(f'<span class="active">{p}</span>')
        else:
            parts.append(f'<a href="{href(p)}">{p}</a>')
        last = p

    # Next
    if current < total_pages:
        parts.append(f'<a href="{href(current + 1)}" class="prev-next">Next &#8594;</a>')
    else:
        parts.append('<span class="prev-next disabled">Next &#8594;</span>')

    parts.append('</div>')
    return ''.join(parts)


# ── Star Rating ──────────────────────────────────────────────────────────

def star_rating_html(rating: float, count: int = 0, size: int = 16) -> str:
    """Render star rating display. rating is 0-5 float."""
    stars = ''
    for i in range(1, 6):
        if rating >= i:
            color = 'var(--gold)'
        elif rating >= i - 0.5:
            color = 'var(--gold-light)'
        else:
            color = 'var(--border)'
        stars += f'<span style="color:{color};font-size:{size}px;">&#9733;</span>'
    count_html = f'<span style="color:var(--ink-muted);font-size:13px;margin-left:6px;">({count})</span>' if count else ''
    return f'<span style="display:inline-flex;align-items:center;gap:1px;">{stars}{count_html}</span>'


def review_card(review: dict) -> str:
    """Render a single review card."""
    reviewer = escape(str(review.get('reviewer_name', 'Anonymous')))
    rating = int(review.get('rating', 5))
    title = escape(str(review.get('title', '')))
    body = escape(str(review.get('body', '')))
    is_vp = bool(review.get('is_verified_purchase', 0))
    created = str(review.get('created_at', ''))[:10]
    vp_badge = '<span style="font-size:11px;color:var(--success-text);background:var(--success-bg);padding:2px 8px;border-radius:999px;font-weight:600;margin-left:8px;">Verified Purchase</span>' if is_vp else ''

    title_html = f'<strong style="font-size:15px;color:var(--ink);">{title}</strong><br>' if title else ''

    return f"""
    <div style="padding:16px 0;border-bottom:1px solid var(--border);">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            {star_rating_html(rating)}
            {vp_badge}
        </div>
        {title_html}
        <p style="color:var(--ink-light);font-size:14px;line-height:1.6;margin-top:4px;">{body}</p>
        <p style="color:var(--ink-muted);font-size:12px;margin-top:8px;">{reviewer} &middot; {created}</p>
    </div>
    """


def review_form_html(tool_slug: str, existing_review: dict = None) -> str:
    """Render a review submission form."""
    title_val = escape(str(existing_review.get('title', ''))) if existing_review else ''
    body_val = escape(str(existing_review.get('body', ''))) if existing_review else ''
    rating_val = int(existing_review.get('rating', 5)) if existing_review else 5
    btn_text = 'Update Review' if existing_review else 'Submit Review'

    rating_options = ''
    for i in range(1, 6):
        sel = ' selected' if i == rating_val else ''
        rating_options += f'<option value="{i}"{sel}>{"&#9733;" * i} ({i}/5)</option>'

    return f"""
    <div style="margin-top:24px;padding:24px;background:var(--cream-dark);border-radius:var(--radius);">
        <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:16px;color:var(--ink);">
            {'Update Your Review' if existing_review else 'Write a Review'}
        </h3>
        <form method="post" action="/tool/{escape(tool_slug)}/review">
            <div class="form-group">
                <label for="rating">Rating</label>
                <select id="rating" name="rating" class="form-select" style="max-width:200px;">
                    {rating_options}
                </select>
            </div>
            <div class="form-group">
                <label for="review_title">Title (optional)</label>
                <input type="text" id="review_title" name="review_title" class="form-input"
                       value="{title_val}" placeholder="Summarize your experience" maxlength="100">
            </div>
            <div class="form-group">
                <label for="review_body">Review</label>
                <textarea id="review_body" name="review_body" class="form-textarea"
                          placeholder="Share your experience with this tool...">{body_val}</textarea>
            </div>
            <button type="submit" class="btn btn-primary">{btn_text}</button>
        </form>
    </div>
    """


def search_filters_html(*, query: str = "", price_filter: str = "", sort: str = "relevance",
                         verified_only: bool = False, categories: list = None,
                         category_id: int = None) -> str:
    """Render search filter bar with pills and dropdowns."""
    safe_q = escape(query)

    # Price pills (removed)
    price_pills = ''

    # Sort dropdown
    sort_options = ''
    for val, label in [("relevance", "Relevance"), ("upvotes", "Most Upvoted"),
                        ("newest", "Newest")]:
        sel = ' selected' if val == sort else ''
        sort_options += f'<option value="{val}"{sel}>{label}</option>'

    # Category dropdown
    cat_html = ''
    if categories:
        cat_options = '<option value="">All Categories</option>'
        for c in categories:
            sel = ' selected' if category_id and int(c['id']) == int(category_id) else ''
            cat_options += f'<option value="{c["id"]}"{sel}>{escape(str(c["name"]))}</option>'
        cat_html = f"""
        <select name="category" class="form-select" style="max-width:180px;font-size:13px;padding:6px 10px;border-radius:999px;"
                onchange="this.form.submit()">
            {cat_options}
        </select>
        """

    return f"""
    <form action="/search" method="GET" style="margin-bottom:24px;">
        <input type="hidden" name="q" value="{safe_q}">
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
            <div style="display:flex;gap:6px;">
                {price_pills}
            </div>
            <select name="sort" class="form-select" style="max-width:180px;font-size:13px;padding:6px 10px;border-radius:999px;"
                    onchange="this.form.submit()">
                {sort_options}
            </select>
            {cat_html}
        </div>
    </form>
    """


# ── User Stack Card (Round 10) ──────────────────────────────────────────

def user_stack_card(stack):
    """Card for displaying a user's public stack in the community gallery."""
    name = stack.get('user_name', 'Anonymous')
    title = stack.get('title', 'My Stack')
    tool_count = stack.get('tool_count', 0)
    desc = stack.get('description', '')
    # Build username slug for the link
    username_slug = name.lower().replace(' ', '-')

    return f"""
    <a href="/stack/{username_slug}" style="text-decoration:none;color:inherit;display:block;">
    <div class="card hover-lift" style="border-radius:var(--radius);padding:24px;cursor:pointer;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
            <div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--terracotta),var(--accent));
                        display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:16px;">
                {name[0].upper() if name else '?'}
            </div>
            <div>
                <div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">{title}</div>
                <div style="font-size:13px;color:var(--ink-muted);">by {name}</div>
            </div>
        </div>
        {f'<p style="font-size:14px;color:var(--ink-light);margin:0 0 12px 0;line-height:1.5;">{desc[:120]}{"..." if len(desc) > 120 else ""}</p>' if desc else ''}
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="background:var(--cream-dark);color:var(--accent);padding:4px 12px;border-radius:999px;font-size:13px;font-weight:600;">
                {tool_count} tool{'s' if tool_count != 1 else ''}
            </span>
        </div>
    </div>
    </a>"""


# ── Launch Readiness Bar (Round 10) ─────────────────────────────────────

def launch_readiness_bar(readiness):
    """Render the Launch Readiness progress bar and checklist for maker dashboard."""
    score = readiness.get('score', 0)
    items = readiness.get('items', [])
    completed = readiness.get('completed', 0)
    total = readiness.get('total', 8)
    tool_id = readiness.get('tool_id')

    bar_color = 'var(--success-text)' if score >= 100 else 'var(--accent)'
    badge_html = ''
    if score >= 100:
        badge_html = '<span style="background:var(--success-text);color:#fff;padding:4px 12px;border-radius:999px;font-size:13px;font-weight:600;margin-left:12px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg> Launch Ready</span>'

    checklist_items = ''
    for item in items:
        check = '&#10003;' if item['done'] else '&#9675;'
        color = 'var(--success-text)' if item['done'] else 'var(--ink-muted)'
        text_style = 'color:var(--ink-light);' if item['done'] else 'color:var(--ink);'
        strike = 'text-decoration:line-through;opacity:0.7;' if item['done'] else ''
        action = item.get('action', '')

        # Base row content
        row_inner = f"""
            <span style="font-size:18px;">{item['icon']}</span>
            <span style="color:{color};font-weight:700;font-size:16px;width:20px;text-align:center;">{check}</span>
            <span style="flex:1;font-size:14px;{text_style}{strike}">{item['label']}</span>
        """

        if action == 'link' and not item['done']:
            url = item.get('url', '#')
            checklist_items += f"""
            <a href="{url}" style="display:flex;align-items:center;gap:12px;padding:12px;border-bottom:1px solid var(--border);
                text-decoration:none;border-radius:8px;transition:background 0.15s;cursor:pointer;"
                onmouseover="this.style.background='var(--cream-dark)'" onmouseout="this.style.background='transparent'">
                {row_inner}
                <span style="color:var(--accent);font-size:14px;font-weight:600;">&#8594;</span>
            </a>"""
        elif action == 'form' and not item['done']:
            field = item.get('field', '')
            input_type = item.get('input_type', 'text')
            placeholder = item.get('placeholder', '')
            current = item.get('current', '')
            current_escaped = escape(str(current)) if current else ''
            placeholder_escaped = escape(str(placeholder))

            if input_type == 'textarea':
                input_html = f'<textarea name="value" placeholder="{placeholder_escaped}" style="width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:14px;font-family:inherit;resize:vertical;min-height:80px;">{current_escaped}</textarea>'
            else:
                input_html = f'<input type="{input_type}" name="value" value="{current_escaped}" placeholder="{placeholder_escaped}" style="width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:14px;font-family:inherit;">'

            checklist_items += f"""
            <details style="border-bottom:1px solid var(--border);">
                <summary style="display:flex;align-items:center;gap:12px;padding:12px;cursor:pointer;list-style:none;
                    border-radius:8px;transition:background 0.15s;"
                    onmouseover="this.style.background='var(--cream-dark)'" onmouseout="this.style.background='transparent'">
                    {row_inner}
                    <span style="color:var(--accent);font-size:12px;transition:transform 0.2s;">&#9660;</span>
                </summary>
                <form method="post" action="/dashboard/readiness-update" style="padding:8px 12px 16px 48px;">
                    <input type="hidden" name="field" value="{field}">
                    <input type="hidden" name="tool_id" value="{tool_id or ''}">
                    <div style="display:flex;gap:8px;align-items:flex-start;">
                        <div style="flex:1;">{input_html}</div>
                        <button type="submit" style="background:var(--accent);color:var(--ink);border:none;padding:12px 24px;
                            border-radius:8px;font-weight:600;font-size:14px;cursor:pointer;white-space:nowrap;">Save</button>
                    </div>
                </form>
            </details>"""
        elif action == 'stripe' and not item['done']:
            checklist_items += f"""
            <div style="display:flex;align-items:center;gap:12px;padding:12px;border-bottom:1px solid var(--border);
                border-radius:8px;transition:background 0.15s;cursor:pointer;"
                onmouseover="this.style.background='var(--cream-dark)'" onmouseout="this.style.background='transparent'"
                onclick="this.querySelector('form').submit()">
                {row_inner}
                <form method="post" action="/dashboard/stripe-connect" style="margin:0;">
                    <button type="submit" style="background:var(--accent);color:var(--ink);border:none;padding:8px 16px;
                        border-radius:8px;font-weight:600;font-size:12px;cursor:pointer;">Connect &#8594;</button>
                </form>
            </div>"""
        else:
            # Completed items or items without action — static row
            checklist_items += f"""
            <div style="display:flex;align-items:center;gap:12px;padding:12px;border-bottom:1px solid var(--border);">
                {row_inner}
            </div>"""

    return f"""
    <div style="background:var(--card-bg);border-radius:var(--radius);padding:24px;border:1px solid var(--border);margin-bottom:24px;">
        <div style="display:flex;align-items:center;margin-bottom:16px;">
            <h3 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin:0;">
                Launch Readiness
            </h3>
            {badge_html}
        </div>
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
            <div style="flex:1;background:var(--cream-dark);border-radius:999px;height:6px;overflow:hidden;">
                <div style="width:{score}%;height:100%;background:{bar_color};border-radius:999px;transition:width 0.5s;"></div>
            </div>
            <span style="font-family:var(--font-display);font-size:24px;color:var(--ink);white-space:nowrap;">
                {score}%
            </span>
        </div>
        <div style="font-size:13px;color:var(--ink-muted);margin-bottom:16px;">{completed} of {total} completed</div>
        <div>{checklist_items}</div>
    </div>"""


# ── Arena (Roast My Stack) ────────────────────────────────────────────────


def render_arena_feed(roasts: list, user=None, error: str = "") -> str:
    """Render the arena feed page with publish form and roast cards."""
    error_html = ""
    if error:
        error_html = f'<div style="background:var(--error-bg);color:var(--error-text);padding:12px 16px;border-radius:var(--radius-sm);margin-bottom:16px;font-size:14px;">{escape(error)}</div>'

    # Publish form (only for logged-in users)
    if user:
        form_html = f"""
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                Publish Your Stack
            </h2>
            {error_html}
            <form method="post" action="/arena/publish">
                <div style="margin-bottom:16px;">
                    <label for="stack_name" style="display:block;font-weight:600;color:var(--ink);font-size:14px;margin-bottom:6px;">
                        Stack Name
                    </label>
                    <input type="text" id="stack_name" name="stack_name"
                           placeholder="My SaaS Stack" required maxlength="100"
                           style="width:100%;padding:12px 16px;border:2px solid var(--border);border-radius:var(--radius-sm);
                                  font-size:15px;background:var(--card-bg);color:var(--ink);box-sizing:border-box;">
                </div>
                <div style="margin-bottom:16px;">
                    <label for="stack_json" style="display:block;font-weight:600;color:var(--ink);font-size:14px;margin-bottom:6px;">
                        Tools (JSON array of tool names)
                    </label>
                    <textarea id="stack_json" name="stack_json" rows="5" required
                              placeholder='["Next.js", "Supabase", "Stripe", "Vercel", "Tailwind CSS"]'
                              style="width:100%;font-family:var(--font-mono);font-size:14px;padding:12px 16px;
                                     border:2px solid var(--border);border-radius:var(--radius-sm);
                                     background:var(--card-bg);color:var(--ink);resize:vertical;box-sizing:border-box;"></textarea>
                    <p style="font-size:12px;color:var(--ink-muted);margin-top:4px;">
                        JSON array of tool/framework names, e.g. ["React", "PostgreSQL", "Redis"]
                    </p>
                </div>
                <button type="submit" class="btn btn-primary" style="font-size:15px;padding:14px 32px;">
                    Publish &amp; Get Roasted
                </button>
            </form>
        </div>
        """
    else:
        form_html = f"""
        <div class="card" style="padding:24px;text-align:center;margin-bottom:32px;">
            <p style="color:var(--ink-muted);font-size:15px;margin-bottom:12px;">
                Got a hot take on your tech stack? Submit it and let the community roast your choices.
            </p>
            <a href="/login?next=/arena" class="btn btn-primary" style="font-size:14px;padding:12px 24px;">
                Log in to Publish Your Stack
            </a>
        </div>
        """

    # Roast cards
    cards_html = ""
    if roasts:
        for r in roasts:
            rid = int(r['id'])
            name = escape(str(r['stack_name']))
            author = escape(str(r.get('author_name', 'Anonymous')))
            upvotes = int(r.get('upvotes', 0))
            roast_preview = escape(str(r.get('ai_roast_text', '')))[:120]
            if len(str(r.get('ai_roast_text', ''))) > 120:
                roast_preview += "..."
            created = str(r.get('created_at', ''))[:10]

            cards_html += f"""
            <a href="/arena/{rid}" style="text-decoration:none;display:block;">
                <div class="card" style="padding:20px;transition:transform .15s,box-shadow .15s;cursor:pointer;"
                     onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)'"
                     onmouseout="this.style.transform='none';this.style.boxShadow='none'">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                        <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0;">
                            {name}
                        </h3>
                        <span style="font-family:var(--font-mono);font-size:13px;color:var(--slate);white-space:nowrap;
                                     display:flex;align-items:center;gap:4px;">
                            &#9650; {upvotes}
                        </span>
                    </div>
                    <p style="font-size:14px;color:var(--ink-muted);margin:0 0 8px 0;font-style:italic;">
                        &ldquo;{roast_preview}&rdquo;
                    </p>
                    <div style="font-size:12px;color:var(--ink-muted);">
                        by {author} &middot; {created}
                    </div>
                </div>
            </a>
            """
    else:
        cards_html = """
        <div style="text-align:center;padding:60px 20px;">
            <p style="font-size:48px;margin-bottom:16px;">&#128293;</p>
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">No stacks roasted yet</h2>
            <p style="color:var(--ink-muted);margin:8px 0;">Be the first to submit your stack for roasting!</p>
        </div>"""

    return f"""
    {form_html}
    <div style="display:flex;flex-direction:column;gap:16px;">
        {cards_html}
    </div>
    """


def render_roast_detail(roast: dict, comments: list, user=None, has_upvoted: bool = False) -> str:
    """Render a single roast detail page with comments and voting."""
    rid = int(roast['id'])
    name = escape(str(roast['stack_name']))
    author = escape(str(roast.get('author_name', 'Anonymous')))
    roast_text = escape(str(roast.get('ai_roast_text', '')))
    upvotes = int(roast.get('upvotes', 0))
    created = str(roast.get('created_at', ''))[:10]

    # Parse stack tools from JSON
    tools_html = ""
    try:
        import json
        tools_list = json.loads(roast.get('stack_json', '[]'))
        if isinstance(tools_list, list):
            pills = " ".join(
                f'<span style="display:inline-block;font-family:var(--font-mono);font-size:13px;background:var(--cream-dark);'
                f'padding:6px 14px;border-radius:999px;color:var(--ink);margin:4px 2px;">{escape(str(t))}</span>'
                for t in tools_list
            )
            tools_html = f'<div style="margin-bottom:24px;line-height:2.2;">{pills}</div>'
    except (json.JSONDecodeError, TypeError):
        tools_html = '<p style="color:var(--ink-muted);font-size:14px;">Could not parse stack tools.</p>'

    # Upvote button
    upvote_color = "var(--slate)" if has_upvoted else "var(--ink-muted)"
    upvote_bg = "var(--slate-light)" if has_upvoted else "var(--cream-dark)"
    if user:
        upvote_html = f"""
        <form method="post" action="/arena/{rid}/upvote" style="display:inline;">
            <button type="submit" style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;
                    border-radius:999px;border:2px solid {upvote_color};background:{upvote_bg};
                    color:{upvote_color};font-weight:700;font-size:15px;cursor:pointer;transition:all .15s;">
                &#9650; {upvotes}
            </button>
        </form>
        """
    else:
        upvote_html = f"""
        <span style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;
                border-radius:999px;border:2px solid var(--border);background:var(--cream-dark);
                color:var(--ink-muted);font-weight:700;font-size:15px;">
            &#9650; {upvotes}
        </span>
        """

    # AI Roast callout
    roast_callout = f"""
    <div style="background:linear-gradient(135deg,#FFF7ED,#FEF3C7);border:2px solid var(--gold);
                border-radius:var(--radius);padding:24px;margin-bottom:24px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="font-size:20px;">&#128293;</span>
            <span style="font-weight:700;color:var(--gold-dark);font-size:14px;text-transform:uppercase;letter-spacing:0.5px;">
                AI Roast
            </span>
        </div>
        <p style="font-size:17px;color:var(--gold-dark);line-height:1.6;margin:0;font-style:italic;">
            &ldquo;{roast_text}&rdquo;
        </p>
    </div>
    """

    # Comments section
    comments_html = ""
    if comments:
        for c in comments:
            c_author = escape(str(c.get('author_name', 'Anonymous')))
            c_text = escape(str(c['comment_text']))
            c_date = str(c.get('created_at', ''))[:10]
            comments_html += f"""
            <div style="padding:16px;border-bottom:1px solid var(--border);">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                    <span style="font-weight:600;color:var(--ink);font-size:14px;">{c_author}</span>
                    <span style="font-size:12px;color:var(--ink-muted);">{c_date}</span>
                </div>
                <p style="color:var(--ink);font-size:15px;line-height:1.5;margin:0;">{c_text}</p>
            </div>
            """
    else:
        comments_html = '<p style="text-align:center;color:var(--ink-muted);padding:24px;font-size:14px;">No comments yet. Be the first to weigh in!</p>'

    # Comment form
    if user:
        comment_form = f"""
        <form method="post" action="/arena/{rid}/comment" style="margin-top:16px;">
            <textarea name="comment_text" rows="3" required maxlength="1000"
                      placeholder="What do you think of this stack?"
                      style="width:100%;padding:12px 16px;border:2px solid var(--border);border-radius:var(--radius-sm);
                             font-size:14px;background:var(--card-bg);color:var(--ink);resize:vertical;
                             box-sizing:border-box;margin-bottom:8px;"></textarea>
            <button type="submit" class="btn btn-primary" style="font-size:14px;padding:10px 24px;">
                Post Comment
            </button>
        </form>
        """
    else:
        comment_form = f"""
        <div style="text-align:center;padding:16px;margin-top:16px;border:1px dashed var(--border);border-radius:var(--radius-sm);">
            <a href="/login?next=/arena/{rid}" style="color:var(--slate);font-weight:600;text-decoration:none;">
                Log in to comment
            </a>
        </div>
        """

    return f"""
    <div>
        <a href="/arena" style="color:var(--ink-muted);font-size:14px;font-weight:600;text-decoration:none;">&larr; Back to Arena</a>

        <div style="margin-top:20px;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(26px,4vw,36px);color:var(--ink);margin-bottom:8px;">
                {name}
            </h1>
            <div style="font-size:14px;color:var(--ink-muted);">
                by {author} &middot; {created} &middot; {upvote_html}
            </div>
        </div>

        {tools_html}
        {roast_callout}

        <div class="card" style="padding:0;overflow:hidden;">
            <div style="padding:16px 20px;border-bottom:1px solid var(--border);">
                <h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0;">
                    Comments ({len(comments)})
                </h2>
            </div>
            {comments_html}
            {comment_form}
        </div>
    </div>
    """


def analytics_wall_blurred(stats: dict, tool_name: str, slug: str, user_logged_in: bool, tool_id: int = 0) -> str:
    """Render blurred AI agent analytics wall for unclaimed tools. Drives claim activation via loss aversion."""
    from html import escape
    total = stats.get('total_agent_queries') or 0
    citations = stats.get('total_citations') or 0
    platforms = stats.get('unique_platforms') or 0
    last_7d = stats.get('queries_last_7d') or 0
    safe_name = escape(str(tool_name))

    if user_logged_in:
        cta_btn = f'''<form method="POST" action="/api/claim" style="margin:0;">
            <input type="hidden" name="tool_id" value="{tool_id}">
            <button type="submit" class="btn btn-primary" style="padding:14px 32px;font-size:15px;font-weight:700;border-radius:999px;cursor:pointer;">
                Claim This Listing
            </button>
        </form>'''
    else:
        cta_btn = f'''<a href="/signup?next=/tool/{escape(slug)}" class="btn btn-primary"
            style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:700;border-radius:999px;text-decoration:none;">
            Sign Up to Claim
        </a>'''

    # Fake platform bars for the blurred section (visual tease only)
    fake_bars = ''
    for label, pct in [('Claude Code', 45), ('Cursor', 28), ('Windsurf', 15), ('Other', 12)]:
        fake_bars += f'''<div style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-muted);">
            <span style="min-width:80px;">{label}</span>
            <div style="flex:1;height:8px;background:var(--border);border-radius:4px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:var(--accent);border-radius:4px;"></div>
            </div>
            <span style="min-width:30px;text-align:right;">{pct}%</span>
        </div>'''

    return f'''
    <div style="margin:16px 0;padding:24px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);position:relative;overflow:hidden;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
            <span style="font-size:18px;">&#128274;</span>
            <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0;">AI Agent Activity</h3>
        </div>

        <!-- Blurred stats -->
        <div style="filter:blur(6px);user-select:none;pointer-events:none;">
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:20px;">
                <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                    <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{total}</div>
                    <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Agent Queries</div>
                </div>
                <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                    <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{citations}</div>
                    <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Citations</div>
                </div>
                <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                    <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{platforms}</div>
                    <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Platforms</div>
                </div>
                <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                    <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{last_7d}</div>
                    <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Last 7 days</div>
                </div>
            </div>
            <div style="display:flex;flex-direction:column;gap:6px;">
                {fake_bars}
            </div>
        </div>

        <!-- CTA overlay -->
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
                    background:var(--cream-dark);opacity:0.88;z-index:1;">
            <p style="font-size:15px;font-weight:700;color:var(--ink);margin-bottom:4px;text-align:center;padding:0 20px;">
                {f"AI agents evaluated {safe_name} {last_7d} time{'s' if last_7d != 1 else ''} this week"
                 if last_7d > 0
                 else f"AI agents have recommended {safe_name} {total} time{'s' if total != 1 else ''}"}
            </p>
            <p style="font-size:13px;color:var(--ink-muted);margin-bottom:16px;text-align:center;padding:0 20px;">
                Claim this listing to see which agents, what they searched, and your recommendation trend.
            </p>
            {cta_btn}
        </div>
    </div>
    '''


def analytics_wall_revealed(stats: dict, tool_name: str) -> str:
    """Render full unblurred AI agent analytics for claimed tool owners."""
    from html import escape
    total = stats.get('total_agent_queries') or 0
    citations = stats.get('total_citations') or 0
    platforms = stats.get('unique_platforms') or 0
    last_7d = stats.get('queries_last_7d') or 0
    platform_breakdown = stats.get('platform_breakdown', [])
    top_queries = stats.get('top_queries', [])
    daily_trend = stats.get('daily_trend', [])
    safe_name = escape(str(tool_name))

    # Platform breakdown bars
    platform_html = ''
    if platform_breakdown:
        max_count = max(p['count'] for p in platform_breakdown) if platform_breakdown else 1
        for p in platform_breakdown:
            pct = round(p['count'] / max(max_count, 1) * 100)
            platform_html += f'''<div style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-muted);">
                <span style="min-width:90px;font-weight:600;color:var(--ink);">{escape(str(p["platform"]))}</span>
                <div style="flex:1;height:8px;background:var(--border);border-radius:4px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:var(--accent);border-radius:4px;"></div>
                </div>
                <span style="min-width:30px;text-align:right;font-family:var(--font-mono);font-size:12px;">{p["count"]}</span>
            </div>'''

    # Top queries table
    queries_html = ''
    if top_queries:
        rows = ''
        for q in top_queries:
            last_seen = str(q.get('last_seen', ''))[:10]
            rows += f'''<tr>
                <td style="padding:6px 8px;font-size:13px;color:var(--ink);">{escape(str(q["query"]))}</td>
                <td style="padding:6px 8px;font-size:13px;color:var(--ink-muted);text-align:center;font-family:var(--font-mono);">{q["count"]}</td>
                <td style="padding:6px 8px;font-size:12px;color:var(--ink-muted);text-align:right;">{last_seen}</td>
            </tr>'''
        queries_html = f'''
        <div style="margin-top:16px;">
            <h4 style="font-size:13px;font-weight:700;color:var(--ink);margin-bottom:8px;">Top Queries</h4>
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="border-bottom:1px solid var(--border);">
                    <th style="padding:6px 8px;font-size:11px;color:var(--ink-muted);text-align:left;">Query</th>
                    <th style="padding:6px 8px;font-size:11px;color:var(--ink-muted);text-align:center;">Count</th>
                    <th style="padding:6px 8px;font-size:11px;color:var(--ink-muted);text-align:right;">Last Seen</th>
                </tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>'''

    # Daily trend sparkline (CSS bars)
    trend_html = ''
    if daily_trend:
        max_day = max(d['count'] for d in daily_trend) if daily_trend else 1
        bars = ''
        for d in daily_trend:
            h = max(round(d['count'] / max(max_day, 1) * 32), 2)
            bars += f'<div title="{d["day"]}: {d["count"]}" style="width:6px;height:{h}px;background:var(--accent);border-radius:2px;flex-shrink:0;"></div>'
        trend_html = f'''
        <div style="margin-top:16px;">
            <h4 style="font-size:13px;font-weight:700;color:var(--ink);margin-bottom:8px;">30-Day Trend</h4>
            <div style="display:flex;align-items:flex-end;gap:2px;height:40px;padding:4px 0;">
                {bars}
            </div>
        </div>'''

    return f'''
    <div style="margin:16px 0;padding:24px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
            <span style="font-size:18px;">&#128202;</span>
            <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0;">AI Agent Activity</h3>
            <span class="badge badge-success" style="font-size:11px;">&#10003; Your listing</span>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:20px;">
            <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{total}</div>
                <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Agent Queries</div>
            </div>
            <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{citations}</div>
                <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Citations</div>
            </div>
            <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{platforms}</div>
                <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Platforms</div>
            </div>
            <div style="text-align:center;padding:12px;background:var(--card-bg);border-radius:8px;border:1px solid var(--border);">
                <div style="font-size:24px;font-weight:800;color:var(--accent);font-family:var(--font-mono);">{last_7d}</div>
                <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">Last 7 days</div>
            </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:6px;">
            {platform_html}
        </div>

        {queries_html}
        {trend_html}

        <div style="margin-top:16px;text-align:right;">
            <a href="/dashboard" style="font-size:13px;color:var(--accent);text-decoration:none;font-weight:600;">
                View full dashboard &#8594;
            </a>
        </div>
    </div>
    '''
