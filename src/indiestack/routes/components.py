"""Design system and shared components for IndieStack."""

import json
from html import escape

from indiestack.config import BASE_URL

# ── Design Tokens ─────────────────────────────────────────────────────────────────────────────

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
            --success: #22C55E;
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
            --danger: #991B1B;
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
            --danger: #FCA5A5;
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

        /* ── Cards ───────────────── */
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

        /* ── Buttons ──────────────── */
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

        /* ── Hover utilities ────────── */
        .hover-lift { transition: transform 0.15s ease, box-shadow 0.15s ease; }
        .hover-lift:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
        .hover-highlight { transition: background 0.15s ease; }
        .hover-highlight:hover { background: var(--cream-dark); }
        .totw-link { transition: box-shadow 0.2s ease, transform 0.2s ease; }
        .totw-link:hover { box-shadow: 0 4px 16px rgba(226,183,100,0.25); transform: translateY(-1px); }
        .pill-link { transition: border-color 0.15s ease, color 0.15s ease; }
        .pill-link:hover { border-color: var(--slate) !important; color: var(--ink) !important; }

        /* ── Tags ────────────────── */
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

        /* ── Search ──────────────── */
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

        /* ── Badges ──────────────── */
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

        /* ── Section Divider ───────── */
        .section-divider {
            margin-top: 48px; padding-top: 24px; border-top: none; position: relative;
        }
        .section-divider::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            opacity: 0.3;
        }

        /* ── Price Pill ──────────── */
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

        /* ── Pagination ───────────── */
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

        /* ── Utility ──────────────── */
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

        /* ── Glassmorphism Nav ──────── */
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

        /* ── Button Press State ────── */
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

        /* ── Custom Select Pill ────── */
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
