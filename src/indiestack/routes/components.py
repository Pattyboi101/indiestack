"""Design system and shared components for IndieStack."""

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
        [data-theme="dark"] .btn-secondary { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }
        [data-theme="dark"] .btn-secondary:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.15); }
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
            display: inline-block; padding: 4px 12px; border-radius: 999px;
            font-size: 12px; font-weight: 600; cursor: pointer;
            border: 1px solid var(--border); background: var(--card-bg); color: var(--ink-light);
            font-family: var(--font-body); transition: all var(--duration-fast) ease;
            text-decoration: none; white-space: nowrap;
        }
        .pill-filter:hover { border-color: var(--terracotta); color: var(--ink); }
        .pill-filter.active { background: var(--terracotta); color: white; border-color: var(--terracotta); }

        /* ── Copy Button ──────────── */
        .copy-btn {
            font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 999px;
            border: 1px solid var(--border); background: var(--card-bg); cursor: pointer;
            color: var(--ink-muted); font-family: var(--font-body); transition: all var(--duration-fast) ease;
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
            background-color: #1a1a2e;
            border-color: rgba(255,255,255,0.1);
            color: var(--ink);
        }
        [data-theme="dark"] select option {
            background-color: #1a1a2e;
            color: #e2e8f0;
        }
        /* Light mode select option readability */
        select option {
            background-color: #ffffff;
            color: #1A2D4A;
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
                position: absolute; top: 64px; left: 0; right: 0;
                background: var(--nav-bg); border-bottom: 1px solid var(--border);
                padding: 8px 0; z-index: 99;
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
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
                border-radius: 999px; color: white !important;
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
                <a href="/dashboard/notifications" style="position:relative;color:var(--ink-light);font-size:18px;text-decoration:none;">&#128276;</a>
                <div style="display:flex;align-items:center;gap:8px;">
                    {avatar_html}
                    <span style="color:var(--ink);font-size:13px;font-weight:600;">{user_name}</span>
                    {cofounder_badge_html() if user.get('email', '').lower() in {e.lower() for e in COFOUNDER_EMAILS} else ''}
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
                <div class="nav-dropdown" style="position:relative;">
                    <button onclick="this.parentElement.classList.toggle('open')"
                            style="background:none;border:none;cursor:pointer;font-family:var(--font-body);
                                   font-size:14px;font-weight:500;color:var(--ink-light);display:flex;
                                   align-items:center;gap:4px;padding:0;">
                        For Makers <span style="font-size:10px;">&#9660;</span>
                    </button>
                    <div class="nav-dropdown-menu" style="display:none;position:absolute;top:calc(100% + 8px);
                                left:50%;transform:translateX(-50%);background:var(--card-bg);
                                border:1px solid var(--border);border-radius:var(--radius-sm);
                                box-shadow:var(--shadow-md);padding:8px 0;min-width:180px;z-index:200;">
                        <a href="/geo" class="nav-dropdown-item">AI Optimize</a>
                        <a href="/submit" class="nav-dropdown-item">Submit a Tool</a>
                    </div>
                </div>
                <div class="nav-dropdown" style="position:relative;">
                    <button onclick="this.parentElement.classList.toggle('open')"
                            style="background:none;border:none;cursor:pointer;font-family:var(--font-body);
                                   font-size:14px;font-weight:500;color:var(--ink-light);display:flex;
                                   align-items:center;gap:4px;padding:0;">
                        Resources <span style="font-size:10px;">&#9660;</span>
                    </button>
                    <div class="nav-dropdown-menu" style="display:none;position:absolute;top:calc(100% + 8px);
                                left:50%;transform:translateX(-50%);background:var(--card-bg);
                                border:1px solid var(--border);border-radius:var(--radius-sm);
                                box-shadow:var(--shadow-md);padding:8px 0;min-width:180px;z-index:200;">
                        <a href="/what-is-indiestack" class="nav-dropdown-item">What is IndieStack?</a>
                        <a href="/gaps" class="nav-dropdown-item">Demand Board</a>
                        <a href="/stacks" class="nav-dropdown-item">Stacks</a>
                        <a href="/changelog" class="nav-dropdown-item">Changelog</a>
                    </div>
                </div>
                <a href="/submit" class="btn btn-primary" style="padding:8px 16px;font-size:13px;">Submit</a>
                <button onclick="toggleTheme()" id="theme-toggle" style="background:none;border:1px solid var(--border);border-radius:999px;padding:8px 12px;cursor:pointer;font-size:14px;color:var(--ink-muted);transition:all 0.15s ease;min-width:44px;min-height:44px;" title="Toggle dark mode">&#9790;</button>
                {auth_links}
            </div>
            <button class="hamburger" onclick="document.getElementById('mobile-menu').classList.toggle('open')" aria-label="Menu">&#9776;</button>
        </div>
        <div class="mobile-menu" id="mobile-menu">
            <a href="/explore">Explore</a>
            <a href="/geo">AI Optimize</a>
            <a href="/stacks">Stacks</a>
            <a href="/gaps">Demand Board</a>
            <a href="/what-is-indiestack">What is IndieStack?</a>
            <a href="/changelog">Changelog</a>
            <a href="/submit" class="btn btn-primary">Submit</a>
            <button onclick="toggleTheme()">Toggle Theme</button>
            {mobile_auth_links}
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
                style="border:none;border-radius:999px;padding:10px 16px;font-size:14px;
                min-width:200px;flex:1;outline:none;">
            <button type="submit" style="background:var(--slate);color:var(--terracotta);
                font-weight:700;border:none;border-radius:999px;padding:10px 20px;
                cursor:pointer;white-space:nowrap;">Subscribe</button>
            <button type="button" id="sticky-dismiss" style="color:rgba(255,255,255,0.6);font-size:20px;
                cursor:pointer;background:none;border:none;padding:4px 8px;">&times;</button>
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
            <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.6;margin:0;">Discover indie creations built by independent makers and small teams.</p>
          </div>
          <!-- Product -->
          <div>
            <div class="footer-heading">Product</div>
            <a href="/explore" class="footer-link">Explore</a>
            <a href="/explore?sort=newest" class="footer-link">New Arrivals</a>
            <a href="/stacks" class="footer-link">Stacks</a>
            <a href="/makers" class="footer-link">Makers</a>
            <a href="/blog" class="footer-link">Blog</a>
            <a href="/best" class="footer-link">Best Indie</a>
          </div>
          <!-- Company -->
          <div>
            <div class="footer-heading">Company</div>
            <a href="/about" class="footer-link">About</a>
            <a href="/faq" class="footer-link">FAQ</a>
            <a href="/submit" class="footer-link">Submit</a>
            <a href="/changelog" class="footer-link">Changelog</a>
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
    <p style="color:rgba(255,255,255,0.85);font-size:14px;font-weight:600;margin-bottom:12px;">Get weekly picks — the best new indie creations in your inbox.</p>
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
          <span style="color:rgba(255,255,255,0.7);font-size:13px;font-weight:600;display:block;width:100%;text-align:center;margin-bottom:12px;">The open-source supply chain for AI agents and indie creators.</span>
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
    return '<span class="badge badge-success">&#128275; Ejectable</span>'


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

    return f'<span class="badge {badge_class}">&#128994; {label}</span>'


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
            <pre id="snippet-py" style="background:var(--ink);color:var(--slate);border-radius:var(--radius-sm);padding:16px 20px;
                        font-family:var(--font-mono);font-size:13px;line-height:1.7;overflow-x:auto;margin:0;">{python_snippet}</pre>
        </div>
        <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:12px;font-weight:700;color:var(--ink-muted);background:var(--cream-dark);padding:2px 10px;border-radius:999px;">cURL</span>
                <button onclick="navigator.clipboard.writeText(document.getElementById('snippet-curl').textContent);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                        class="copy-btn">Copy</button>
            </div>
            <pre id="snippet-curl" style="background:var(--ink);color:var(--slate);border-radius:var(--radius-sm);padding:16px 20px;
                        font-family:var(--font-mono);font-size:13px;line-height:1.7;overflow-x:auto;margin:0;">{curl_snippet}</pre>
        </div>
    </div>
    """


# Co-founder emails — update Ed's when he signs up
COFOUNDER_EMAILS = {'ameyjonesP@gmail.com', 'ed@placeholder.com'}


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
    """Card component for a Vibe Stack bundle."""
    emoji = stack.get('cover_emoji', '') or '&#128230;'
    title = escape(str(stack['title']))
    desc = escape(str(stack.get('description', '')))
    slug = escape(str(stack['slug']))
    count = stack.get('tool_count', 0)
    discount = stack.get('discount_percent', 15)
    return f"""
    <a href="/stacks/{slug}" class="card" style="text-decoration:none;color:inherit;display:block;">
        <span style="font-size:32px;display:block;margin-bottom:8px;">{emoji}</span>
        <h3 style="font-family:var(--font-display);font-size:17px;margin-bottom:8px;color:var(--ink);">{title}</h3>
        <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;
                  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{desc}</p>
        <div style="display:flex;gap:8px;align-items:center;">
            <span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);
                         padding:4px 12px;border-radius:999px;">{count} tool{"s" if count != 1 else ""}</span>
            {f'<span class="badge badge-success" style="font-weight:700;">{discount}% off</span>' if stack.get('discount_percent', 0) > 0 else ''}
        </div>
    </a>
    """


# ── Tool Card ─────────────────────────────────────────────────────────────

def verified_badge_html() -> str:
    return ""


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
        streak_html = '<span class="badge badge-warning" style="font-weight:700;margin-top:8px;">&#128293; Active</span>'

    # Add bookmark icon — positioned absolutely in top-right of card (hidden in compact mode)
    bookmark_html = ''
    if not compact:
        bookmark_html = f'''<button class="wishlist-btn" onclick="event.stopPropagation();toggleWishlist({tool['id']})" id="wishlist-{tool['id']}"
        style="position:absolute;top:12px;right:12px;z-index:2;background:none;border:none;cursor:pointer;padding:8px;font-size:20px;line-height:1;color:var(--ink-muted);opacity:0.5;transition:color 0.2s,transform 0.2s,opacity 0.2s;min-width:44px;min-height:44px;"
        onmouseenter="this.style.color='#E2B764';this.style.opacity='1';this.style.transform='scale(1.1)';"
        onmouseleave="if(!this.dataset.wishlisted){{this.style.color='var(--ink-muted)';this.style.opacity='0.5';this.style.transform='scale(1)';}}else{{this.style.transform='scale(1)';}}"
        title="Bookmark">&#9734;</button>'''

    visit_html = f'<a href="/api/click/{slug}" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="font-size:12px;color:var(--accent);font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:2px;">Visit&nbsp;&rarr;</a>'

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

    badge = ''
    is_boosted = bool(tool.get('is_boosted', 0))
    if is_boosted:
        badge += ' ' + boosted_badge_html()
    # Show "Maker ✓" badge only for claimed tools — no badge for unclaimed
    if tool.get('claimed_at'):
        badge += ' <span class="badge badge-success" style="font-size:var(--text-xs);">Maker &#10003;</span>'
    price_pence = tool.get('price_pence')
    if price_pence and price_pence > 0 and not tool.get('stripe_account_id'):
        badge += f' <span class="pill-price">&pound;{price_pence // 100}/mo</span>'
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
                    favicon_html = f'<img src="https://www.google.com/s2/favicons?domain={domain}&sz=32" alt="" width="24" height="24" loading="lazy" style="border-radius:4px;border:1px solid var(--border);flex-shrink:0;" onerror="this.style.display=\'none\'">'
            except Exception:
                pass

    card_class = 'card'

    upvote_html = ''
    if not compact:
        # Hide count when low (< 3) — show just the arrow, count appears after voting
        count_display = str(upvotes) if upvotes >= 3 else ''
        upvote_html = (
            f'<button class="upvote-btn" onclick="upvote({tool["id"]})" id="upvote-{tool["id"]}">'
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
                {f'<a href="/maker/{escape(str(tool.get("maker_slug", "")))}" style="font-size:12px;color:var(--ink-muted);text-decoration:none;display:flex;align-items:center;gap:4px;" title="Made by {escape(str(tool.get("maker_name", "")))}"><span style="color:var(--ink-muted);">by</span> <span style="color:var(--cyan);font-weight:600;">{escape(str(tool.get("maker_name", "")))}</span></a>' if tool.get('maker_name') and tool.get('maker_slug') else ''}
                {visit_html}
                {gh_indicator}
                {ai_recs_html}
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
    return f'<button data-copy="{safe}" style="background:var(--slate,#64748B);color:#fff;border:none;border-radius:999px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer;font-family:var(--font-body);display:inline-flex;align-items:center;gap:4px;">{label}</button>'


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


# ── Page Shell ────────────────────────────────────────────────────────────

def page_shell(title: str, body: str, *, description: str = "", extra_head: str = "", user=None, og_image: str = f"{BASE_URL}/logo.png", canonical: str = "") -> str:
    desc = escape(description) if description else "Discover indie creations built by independent makers and small teams."
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
        badge_html = '<span style="background:var(--success-text);color:#fff;padding:4px 12px;border-radius:999px;font-size:13px;font-weight:600;margin-left:12px;">&#128640; Launch Ready</span>'

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
