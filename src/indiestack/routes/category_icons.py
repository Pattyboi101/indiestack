def category_icon(slug: str, size: int = 20) -> str:
    """Return an inline SVG icon for a category slug. Falls back to a generic grid icon."""
    _attrs = (
        f'xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
    )
    icons = {
        # Bot/robot head
        'ai-automation': (
            f'<svg {_attrs}>'
            '<rect x="3" y="11" width="18" height="10" rx="2"/>'
            '<circle cx="9" cy="16" r="1"/>'
            '<circle cx="15" cy="16" r="1"/>'
            '<path d="M12 2v4"/>'
            '<path d="M8 11V9a4 4 0 0 1 8 0v2"/>'
            '</svg>'
        ),
        # Brain with circuit
        'ai-dev-tools': (
            f'<svg {_attrs}>'
            '<path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z"/>'
            '<path d="M9 21h6"/>'
            '<path d="M10 17v-3"/>'
            '<path d="M14 17v-3"/>'
            '<circle cx="10" cy="10" r="1"/>'
            '<circle cx="14" cy="10" r="1"/>'
            '</svg>'
        ),
        # Plug/connection
        'api-tools': (
            f'<svg {_attrs}>'
            '<path d="M12 22v-5"/>'
            '<path d="M9 8V2"/>'
            '<path d="M15 8V2"/>'
            '<path d="M18 8v4a6 6 0 0 1-12 0V8z"/>'
            '</svg>'
        ),
        # Bar chart ascending
        'analytics-metrics': (
            f'<svg {_attrs}>'
            '<path d="M3 3v18h18"/>'
            '<rect x="7" y="13" width="3" height="7" rx="1"/>'
            '<rect x="12" y="9" width="3" height="11" rx="1"/>'
            '<rect x="17" y="5" width="3" height="15" rx="1"/>'
            '</svg>'
        ),
        # Shield with checkmark
        'authentication': (
            f'<svg {_attrs}>'
            '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
            '<path d="m9 12 2 2 4-4"/>'
            '</svg>'
        ),
        # Users/people group
        'crm-sales': (
            f'<svg {_attrs}>'
            '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
            '<circle cx="9" cy="7" r="4"/>'
            '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
            '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
            '</svg>'
        ),
        # Paintbrush
        'creative-tools': (
            f'<svg {_attrs}>'
            '<path d="M18.37 2.63a2.12 2.12 0 0 1 3 3L14 13l-4 1 1-4z"/>'
            '<path d="M9 14.5A3.5 3.5 0 0 0 5.5 18c-1.22 0-2.5.74-2.5 2 2.5 0 5-1.5 5-3.5 0-.56-.17-1.08-.45-1.53"/>'
            '</svg>'
        ),
        # Headphones
        'customer-support': (
            f'<svg {_attrs}>'
            '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"/>'
            '</svg>'
        ),
        # Pen tool (bezier)
        'design-creative': (
            f'<svg {_attrs}>'
            '<path d="M12 19l7-7 3 3-7 7-3-3z"/>'
            '<path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>'
            '<path d="M2 2l7.586 7.586"/>'
            '<circle cx="11" cy="11" r="2"/>'
            '</svg>'
        ),
        # Code brackets
        'developer-tools': (
            f'<svg {_attrs}>'
            '<polyline points="16 18 22 12 16 6"/>'
            '<polyline points="8 6 2 12 8 18"/>'
            '</svg>'
        ),
        # Mail envelope
        'email-marketing': (
            f'<svg {_attrs}>'
            '<rect width="20" height="16" x="2" y="4" rx="2"/>'
            '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>'
            '</svg>'
        ),
        # Star
        'feedback-reviews': (
            f'<svg {_attrs}>'
            '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a.53.53 0 0 0 .4.29l5.16.756a.53.53 0 0 1 .294.904l-3.733 3.638a.53.53 0 0 0-.152.469l.882 5.14a.53.53 0 0 1-.77.56l-4.615-2.425a.53.53 0 0 0-.494 0L6.18 18.73a.53.53 0 0 1-.77-.56l.882-5.14a.53.53 0 0 0-.152-.47L2.407 8.924a.53.53 0 0 1 .294-.906l5.16-.754a.53.53 0 0 0 .4-.29z"/>'
            '</svg>'
        ),
        # Folder
        'file-management': (
            f'<svg {_attrs}>'
            '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2z"/>'
            '</svg>'
        ),
        # Clipboard with list
        'forms-surveys': (
            f'<svg {_attrs}>'
            '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>'
            '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
            '<path d="M12 11h4"/>'
            '<path d="M12 16h4"/>'
            '<path d="M8 11h.01"/>'
            '<path d="M8 16h.01"/>'
            '</svg>'
        ),
        # Gamepad
        'games-entertainment': (
            f'<svg {_attrs}>'
            '<line x1="6" y1="11" x2="10" y2="11"/>'
            '<line x1="8" y1="9" x2="8" y2="13"/>'
            '<line x1="15" y1="12" x2="15.01" y2="12"/>'
            '<line x1="18" y1="10" x2="18.01" y2="10"/>'
            '<path d="M17.32 5H6.68a4 4 0 0 0-3.978 3.59c-.006.052-.01.101-.017.152C2.604 9.416 2 14.456 2 16a3 3 0 0 0 3 3c1 0 1.5-.5 2-1l1.414-1.414A2 2 0 0 1 9.828 16h4.344a2 2 0 0 1 1.414.586L17 18c.5.5 1 1 2 1a3 3 0 0 0 3-3c0-1.545-.604-6.584-.685-7.258-.007-.05-.011-.1-.017-.151A4 4 0 0 0 17.32 5z"/>'
            '</svg>'
        ),
        # Receipt with dollar
        'invoicing-billing': (
            f'<svg {_attrs}>'
            '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1z"/>'
            '<path d="M14 8H8"/>'
            '<path d="M16 12H8"/>'
            '<path d="M13 16H8"/>'
            '</svg>'
        ),
        # Layout/browser window
        'landing-pages': (
            f'<svg {_attrs}>'
            '<rect width="20" height="16" x="2" y="4" rx="2"/>'
            '<path d="M2 8h20"/>'
            '<path d="M10 4v4"/>'
            '</svg>'
        ),
        # Book open
        'learning-education': (
            f'<svg {_attrs}>'
            '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
            '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>'
            '</svg>'
        ),
        # Activity/heartbeat line
        'monitoring-uptime': (
            f'<svg {_attrs}>'
            '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'
            '</svg>'
        ),
        # Newspaper/file-text
        'newsletters-content': (
            f'<svg {_attrs}>'
            '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/>'
            '<polyline points="14 2 14 8 20 8"/>'
            '<line x1="16" y1="13" x2="8" y2="13"/>'
            '<line x1="16" y1="17" x2="8" y2="17"/>'
            '<line x1="10" y1="9" x2="8" y2="9"/>'
            '</svg>'
        ),
        # Credit card
        'payments': (
            f'<svg {_attrs}>'
            '<rect width="20" height="14" x="2" y="5" rx="2"/>'
            '<line x1="2" y1="10" x2="22" y2="10"/>'
            '</svg>'
        ),
        # Kanban/columns
        'project-management': (
            f'<svg {_attrs}>'
            '<rect x="4" y="3" width="4" height="18" rx="1"/>'
            '<rect x="10" y="3" width="4" height="12" rx="1"/>'
            '<rect x="16" y="3" width="4" height="8" rx="1"/>'
            '</svg>'
        ),
        # Search/magnifying glass
        'seo-tools': (
            f'<svg {_attrs}>'
            '<circle cx="11" cy="11" r="8"/>'
            '<line x1="21" y1="21" x2="16.65" y2="16.65"/>'
            '</svg>'
        ),
        # Calendar
        'scheduling-booking': (
            f'<svg {_attrs}>'
            '<rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>'
            '<line x1="16" y1="2" x2="16" y2="6"/>'
            '<line x1="8" y1="2" x2="8" y2="6"/>'
            '<line x1="3" y1="10" x2="21" y2="10"/>'
            '</svg>'
        ),
        # Share/network nodes
        'social-media': (
            f'<svg {_attrs}>'
            '<circle cx="18" cy="5" r="3"/>'
            '<circle cx="6" cy="12" r="3"/>'
            '<circle cx="18" cy="19" r="3"/>'
            '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>'
            '<line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>'
            '</svg>'
        ),
    }
    # Generic grid fallback
    fallback = (
        f'<svg {_attrs}>'
        '<rect x="3" y="3" width="7" height="7"/>'
        '<rect x="14" y="3" width="7" height="7"/>'
        '<rect x="3" y="14" width="7" height="7"/>'
        '<rect x="14" y="14" width="7" height="7"/>'
        '</svg>'
    )
    return icons.get(slug, fallback)
