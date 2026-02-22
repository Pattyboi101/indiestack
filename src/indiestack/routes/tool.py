"""Tool detail page."""

import json
from html import escape
from urllib.parse import quote

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import (
    page_shell,
    tool_card,
    verified_badge_html,
    boosted_badge_html,
    ejectable_badge_html,
    maker_pulse_html,
    indie_score_html,
    star_rating_html,
    review_card,
    review_form_html,
    update_card,
    maker_discount_badge_html,
)
from indiestack.db import (
    get_tool_by_slug,
    get_related_tools,
    get_similar_tools,
    slugify,
    get_reviews_for_tool,
    get_tool_rating,
    get_user_review_for_tool,
    create_review,
    record_tool_view,
    is_wishlisted,
    get_tool_changelogs,
    CATEGORY_TOKEN_COSTS,
    get_tool_last_activity,
)

router = APIRouter()


def format_price(pence: int) -> str:
    """Format pence as display string."""
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


@router.get("/tool/{slug}", response_class=HTMLResponse)
async def tool_detail(request: Request, slug: str):
    db = request.state.db
    user = request.state.user
    tool = await get_tool_by_slug(db, slug)

    if not tool or tool['status'] != 'approved':
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Tool Not Found</h1>
            <p class="text-muted mt-4">This tool doesn't exist or hasn't been approved yet.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=user), status_code=404)

    name = escape(str(tool['name']))
    tagline = escape(str(tool['tagline']))
    description = escape(str(tool['description']))
    url = escape(str(tool['url']))
    maker_name = escape(str(tool.get('maker_name', '')))
    maker_url = escape(str(tool.get('maker_url', '')))
    cat_name = escape(str(tool.get('category_name', '')))
    cat_slug = escape(str(tool.get('category_slug', '')))
    upvotes = int(tool.get('upvote_count', 0))
    tags = str(tool.get('tags', ''))
    is_verified = bool(tool.get('is_verified', 0))
    is_ejectable = bool(tool.get('is_ejectable', 0))
    tool_id = tool['id']
    price_pence = tool.get('price_pence')

    # Indie Ring: check if current user is a maker viewing another maker's paid tool
    is_indie_ring = False
    discounted_price = 0
    if user and price_pence and price_pence > 0:
        buyer_maker_id = user.get('maker_id')
        tool_maker_id = tool.get('maker_id')
        if buyer_maker_id and tool_maker_id and buyer_maker_id != tool_maker_id:
            is_indie_ring = True
            discounted_price = price_pence // 2

    # Record view
    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    await record_tool_view(db, tool_id, ip)

    # Fetch reviews and rating
    reviews = await get_reviews_for_tool(db, tool_id)
    rating_info = await get_tool_rating(db, tool_id)
    tool['review_count'] = int(rating_info['review_count'])
    user_review = await get_user_review_for_tool(db, tool_id, user['id']) if user else None
    wishlisted = await is_wishlisted(db, user['id'], tool_id) if user else False

    # Maker pulse
    last_active = await get_tool_last_activity(db, tool_id)
    pulse_html = maker_pulse_html(last_active)

    # Build rating display
    avg_rating = float(rating_info['avg_rating'])
    review_count = int(rating_info['review_count'])
    rating_display_html = ''
    if review_count > 0:
        rating_display_html = f'<span style="margin-left:12px;">{star_rating_html(avg_rating, review_count)}</span>'

    # Build reviews section
    reviews_html = '<div style="margin-top:48px;border-top:1px solid var(--border);padding-top:24px;">'
    reviews_html += '<h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;">Reviews</h2>'
    if reviews:
        for r in reviews:
            reviews_html += review_card(r)
    else:
        reviews_html += '''<div style="text-align:center;padding:32px 20px;background:var(--cream-dark);border-radius:12px;border:1px dashed var(--border);">
    <p style="font-size:28px;margin-bottom:8px;">&#9998;</p>
    <p style="font-weight:600;color:var(--ink);margin-bottom:4px;">No reviews yet</p>
    <p style="color:var(--ink-muted);font-size:14px;">Used this tool? Be the first to share your experience.</p>
</div>'''

    if user:
        reviews_html += review_form_html(slug, existing_review=user_review)
    else:
        reviews_html += '<p style="margin-top:24px;color:var(--ink-muted);font-size:14px;"><a href="/login">Log in</a> to leave a review.</p>'
    reviews_html += '</div>'

    # Tags
    tag_html = ''
    if tags.strip():
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        tag_html = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;">'
        for t in tag_list:
            tag_html += f'<span class="tag">{escape(t)}</span>'
        tag_html += '</div>'

    # Token savings hint
    token_hint_html = ''
    cat_slug_val = str(tool.get('category_slug', ''))
    token_cost = CATEGORY_TOKEN_COSTS.get(cat_slug_val, 50_000)
    token_k = token_cost // 1000
    token_hint_html = f'''
        <div style="margin-top:16px;padding:10px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);
                    display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-light);">
            <span style="font-size:16px;">&#9889;</span>
            Using this tool saves ~{token_k}k tokens vs building from scratch
        </div>
    '''

    # Claim + Boost CTA — show for unclaimed tools
    claim_html = ''
    if not tool.get('maker_id'):
        if user:
            claim_action = f'''
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <form method="POST" action="/api/claim" style="margin:0;">
                    <input type="hidden" name="tool_id" value="{tool['id']}">
                    <button type="submit" style="padding:10px 20px;background:var(--card-bg);color:var(--ink);border:1px solid var(--border);border-radius:999px;font-weight:600;font-size:14px;cursor:pointer;font-family:var(--font-body);">
                        Claim Free
                    </button>
                </form>
                <form method="POST" action="/api/claim-and-boost" style="margin:0;">
                    <input type="hidden" name="tool_id" value="{tool['id']}">
                    <button type="submit" style="padding:10px 20px;background:linear-gradient(135deg,#00D4F5,#40E8FF);color:#1A2D4A;border:none;border-radius:999px;font-weight:700;font-size:14px;cursor:pointer;font-family:var(--font-body);">
                        &#9733; Claim &amp; Boost &pound;29
                    </button>
                </form>
            </div>'''
        else:
            claim_action = f'''
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <a href="/signup?next=/tool/{slug}" style="padding:10px 20px;background:var(--card-bg);color:var(--ink);border:1px solid var(--border);border-radius:999px;font-weight:600;font-size:14px;text-decoration:none;font-family:var(--font-body);">
                    Claim Free
                </a>
                <a href="/signup?next=/tool/{slug}" style="padding:10px 20px;background:linear-gradient(135deg,#00D4F5,#40E8FF);color:#1A2D4A;border:none;border-radius:999px;font-weight:700;font-size:14px;text-decoration:none;font-family:var(--font-body);">
                    &#9733; Claim &amp; Boost &pound;29
                </a>
            </div>'''
        claim_html = f'''
        <div style="margin:16px 0;padding:20px;background:linear-gradient(135deg,#FFF7ED,#FFFBEB);border:1px solid #FDBA74;border-radius:var(--radius-sm);">
            <div style="display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap;">
                <span style="font-size:24px;">&#128075;</span>
                <div style="flex:1;min-width:200px;">
                    <p style="font-weight:700;font-size:15px;color:#92400E;margin-bottom:2px;">Is this your tool?</p>
                    <p style="font-size:13px;color:#B45309;margin-bottom:12px;">Claim this listing to track analytics, post changelogs, and connect Stripe.</p>
                    {claim_action}
                    <div style="margin-top:12px;font-size:12px;color:#B45309;">
                        <strong>Boost includes:</strong> Featured badge for 30 days &middot; Priority placement &middot; Weekly newsletter feature
                    </div>
                </div>
            </div>
        </div>
        '''

    # Boost upsell for tools the current user owns
    boost_html = ''
    if user and tool.get('maker_id') and user.get('maker_id') == tool.get('maker_id'):
        if tool.get('is_boosted') and tool.get('boost_expires_at', '') > '':
            from datetime import datetime
            try:
                expires = datetime.fromisoformat(tool['boost_expires_at'])
                if expires > datetime.utcnow():
                    boost_html = f'<div class="alert alert-info" style="margin:16px 0;">&#9733; <strong>Boosted</strong> until {expires.strftime("%d %b %Y")}. Your tool has priority placement and a Featured badge.</div>'
            except (ValueError, TypeError):
                pass
        if not boost_html:
            boost_html = f'''
            <div style="margin:16px 0;padding:16px;background:linear-gradient(135deg,#E0F7FA,#F0FFFE);border:1px solid #80DEEA;border-radius:var(--radius-sm);">
                <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                    <span style="font-size:20px;">&#9733;</span>
                    <div style="flex:1;">
                        <p style="font-weight:700;font-size:14px;color:#0E7490;">Boost this tool for &pound;29</p>
                        <p style="font-size:12px;color:#0E7490;">Featured badge for 30 days &middot; Priority placement &middot; Newsletter feature</p>
                    </div>
                    <form method="POST" action="/api/boost" style="margin:0;">
                        <input type="hidden" name="tool_id" value="{tool['id']}">
                        <button type="submit" style="padding:8px 18px;background:linear-gradient(135deg,#00D4F5,#40E8FF);color:#1A2D4A;border:none;border-radius:999px;font-weight:700;font-size:13px;cursor:pointer;font-family:var(--font-body);">
                            Boost Now
                        </button>
                    </form>
                </div>
            </div>
            '''

    # Maker info (link to profile)
    maker_html = ''
    unclaimed_badge = ''
    if not tool.get('claimed_by') and not tool.get('maker_id'):
        unclaimed_badge = '''<span style="display:inline-flex;align-items:center;gap:4px;font-size:12px;color:var(--ink-muted);background:var(--cream-dark);padding:2px 8px;border-radius:999px;border:1px solid var(--border);">
    &#128279; Unclaimed listing
</span>'''
    if maker_name:
        maker_slug = slugify(maker_name)
        maker_html = f'<p class="text-muted text-sm mt-4">Built by <a href="/maker/{escape(maker_slug)}">{maker_name}</a> {unclaimed_badge}</p>'
    elif unclaimed_badge:
        maker_html = f'<p class="text-muted text-sm mt-4">{unclaimed_badge}</p>'

    # Price tag
    price_tag_html = ''
    if price_pence and price_pence > 0:
        if is_indie_ring:
            price_tag_html = f'''
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:12px;">
                <span style="font-family:var(--font-display);font-size:28px;color:var(--ink);">
                    {format_price(discounted_price)}
                </span>
                <span style="text-decoration:line-through;color:var(--ink-muted);font-size:16px;">
                    {format_price(price_pence)}
                </span>
                {maker_discount_badge_html()}
            </div>
            '''
        else:
            price_display = format_price(price_pence)
            price_tag_html = f"""
            <span style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-display);
                         font-size:24px;color:var(--terracotta);margin-top:12px;">
                {price_display}
            </span>
            """

    # Wishlist button
    wishlist_btn_html = ''
    if user:
        wl_icon = '&#9733;' if wishlisted else '&#9734;'
        wl_color = 'var(--gold)' if wishlisted else 'var(--ink-muted)'
        wl_text = 'Saved' if wishlisted else 'Save to Wishlist'
        wishlist_btn_html = f'''<button class="btn btn-secondary" onclick="toggleWishlist({tool_id})" id="wishlist-{tool_id}"
            style="font-size:14px;padding:10px 20px;">
            <span style="color:{wl_color};" id="wl-icon-{tool_id}">{wl_icon}</span> {wl_text}
        </button>'''
    else:
        wishlist_btn_html = f'<a href="/login" class="btn btn-secondary" style="font-size:14px;padding:10px 20px;">&#9734; Save to Wishlist</a>'

    # CTA button — "Buy Now" only if tool has Stripe connected, otherwise link to their site
    has_stripe = bool(tool.get('stripe_account_id'))
    if price_pence and price_pence > 0 and has_stripe:
        cta_price = format_price(discounted_price) if is_indie_ring else format_price(price_pence)
        cta_html = f"""
        <form method="post" action="/api/checkout" style="display:inline;">
            <input type="hidden" name="tool_id" value="{tool_id}">
            {'<input type="hidden" name="indie_ring" value="1">' if is_indie_ring else ''}
            <button type="submit" class="btn btn-slate" style="font-size:16px;padding:14px 32px;">
                Buy Now {cta_price} &rarr;
            </button>
        </form>
        """
    elif price_pence and price_pence > 0:
        # Paid tool but not selling through IndieStack — link to their site with price shown
        cta_price = format_price(price_pence)
        cta_html = f"""
        <a href="{url}" target="_blank" rel="noopener" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
            Get it from {cta_price}/mo &rarr;
        </a>
        """
    else:
        cta_html = f"""
        <a href="{url}" target="_blank" rel="noopener" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
            Visit Website &rarr;
        </a>
        """

    # JSON-LD structured data for SEO
    json_ld_data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": tool['name'],
        "description": tool['tagline'],
        "url": f"https://indiestack.fly.dev/tool/{tool['slug']}",
        "applicationCategory": tool.get('category_name', 'WebApplication'),
        "operatingSystem": "Web",
        "offers": {
            "@type": "Offer",
            "price": str(tool.get('price_pence', 0) / 100 if tool.get('price_pence') else 0),
            "priceCurrency": "GBP"
        }
    }
    if review_count > 0:
        json_ld_data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(avg_rating),
            "reviewCount": str(review_count)
        }
    json_ld = json.dumps(json_ld_data, ensure_ascii=False)
    extra_head = f'<script type="application/ld+json">{json_ld}</script>'

    # Changelogs
    changelogs = await get_tool_changelogs(db, tool_id, limit=10)
    changelog_html = ''
    if changelogs:
        cl_cards = '\n'.join(update_card(cl) for cl in changelogs)
        changelog_html = f"""
        <div style="margin-top:48px;border-top:1px solid var(--border);padding-top:24px;">
            <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;">Changelog</h2>
            {cl_cards}
        </div>
        """

    # Smart similar tools: score by shared tags + same category
    similar = await get_similar_tools(db, tool_id, int(tool['category_id']), tool.get('tags', ''))
    if not similar:
        # Fallback to basic category-based related tools
        similar = await get_related_tools(db, tool_id, int(tool['category_id']))

    # Similar tools section
    if similar:
        similar_cards = "".join(tool_card(t) for t in similar)
        similar_html = f'''
        <div style="margin-top:48px;border-top:1px solid var(--border);padding-top:24px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:16px;">
                Similar Tools
            </h2>
            <div class="scroll-row">{similar_cards}</div>
        </div>
        '''
    else:
        similar_html = ''

    # Success/info banners for claim flow
    banners_html = ''
    if request.query_params.get('claimed') == '1':
        banners_html += '<div class="alert alert-success" style="margin-bottom:16px;">&#127881; You\'ve claimed this tool! You can now manage it from your <a href="/dashboard" style="font-weight:700;">dashboard</a>.</div>'
    elif request.query_params.get('claim') == 'sent':
        banners_html += '<div class="alert alert-info" style="margin-bottom:16px;">Claim request received! Check your email to verify ownership.</div>'
    boosted_param = request.query_params.get('boosted')
    if boosted_param == '1':
        banners_html += '<div class="alert alert-success" style="margin-bottom:16px;">&#9733; <strong>Your tool is now boosted!</strong> It has priority placement for 30 days and will be featured in our weekly newsletter.</div>'
    claim_banner = banners_html

    # Breadcrumbs
    breadcrumb_html = f'''
<nav style="font-size:13px;color:var(--ink-muted);margin-bottom:16px;">
    <a href="/" style="color:var(--ink-muted);text-decoration:none;">Home</a>
    <span style="margin:0 6px;">&rsaquo;</span>
    <a href="/category/{escape(str(tool.get('category_slug', '')))}" style="color:var(--ink-muted);text-decoration:none;">{escape(str(tool.get('category_name', '')))}</a>
    <span style="margin:0 6px;">&rsaquo;</span>
    <span style="color:var(--ink);">{escape(str(tool['name']))}</span>
</nav>
'''

    # Share row
    tool_url = f"https://indiestack.fly.dev/tool/{slug}"
    share_text = f"Check out {name} on IndieStack"
    twitter_url = f"https://twitter.com/intent/tweet?text={quote(share_text)}&url={quote(tool_url)}"
    safe_tool_url = tool_url.replace("'", "\\'")

    share_row = f'''
<div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
    <button onclick="navigator.clipboard.writeText('{safe_tool_url}');this.innerHTML='&#10003; Copied!';setTimeout(()=>this.innerHTML='&#128279; Copy Link',2000)"
            style="padding:6px 14px;background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;
                   font-size:12px;font-weight:600;cursor:pointer;color:var(--ink-light);font-family:var(--font-body);">
        &#128279; Copy Link
    </button>
    <a href="{twitter_url}" target="_blank" rel="noopener"
       style="padding:6px 14px;background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;
              font-size:12px;font-weight:600;text-decoration:none;color:var(--ink-light);display:inline-flex;align-items:center;gap:4px;">
        &#120143; Share
    </a>
    <a href="/api/badge/{slug}.svg" target="_blank"
       style="padding:6px 14px;background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;
              font-size:12px;font-weight:600;text-decoration:none;color:var(--ink-light);display:inline-flex;align-items:center;gap:4px;">
        &#128247; Embed Badge
    </a>
</div>
'''

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:800px;">
        {breadcrumb_html}
        {claim_banner}
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:24px;">
            <div style="flex:1;">
                <a href="/category/{cat_slug}" class="tag mb-2" style="display:inline-block;">{cat_name}</a>
                <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:8px;">
                    <h1 style="font-family:var(--font-display);font-size:36px;">{name}</h1>
                    {verified_badge_html() if is_verified else ''}
                    {ejectable_badge_html() if is_ejectable else ''}
                    {pulse_html}
                    {indie_score_html(tool)}
                    {rating_display_html}
                </div>
                <p style="font-size:18px;color:var(--ink-muted);margin-top:8px;">{tagline}</p>
                {price_tag_html}
            </div>
            <button class="upvote-btn" onclick="upvote({tool_id})" id="upvote-{tool_id}"
                    style="flex-shrink:0;min-width:60px;">
                <span class="arrow">&#9650;</span>
                <span id="count-{tool_id}">{upvotes}</span>
            </button>
        </div>

        {claim_html}
        {boost_html}

        <div style="margin-top:32px;">
            <p style="white-space:pre-line;color:var(--ink-light);line-height:1.8;font-size:16px;">{description}</p>
        </div>

        <div style="margin-top:32px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
            {cta_html}
            {wishlist_btn_html}
            {maker_html}
        </div>
        {share_row}

        {tag_html}
        {token_hint_html}

        {'<div style="margin-top:48px;padding:24px;border:1px dashed var(--gold);border-radius:var(--radius);background:#FDF8EE;text-align:center;"><p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">Boost this listing</p><p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">Get a verified badge, rank higher in search, and build buyer trust.</p><a href="/verify/' + slug + '" class="btn" style="background:linear-gradient(135deg,var(--gold),#D4A24A);color:#5C3D0E;font-weight:700;padding:10px 24px;border-radius:999px;border:1px solid var(--gold);">Get Verified — £29 &rarr;</a></div>' if not is_verified else ''}

        {similar_html}

        {changelog_html}

        {reviews_html}
    </div>
    """
    og_image_url = f"https://indiestack.fly.dev/api/og/{slug}.svg"
    return HTMLResponse(page_shell(name, body, description=tagline, extra_head=extra_head, user=user, og_image=og_image_url, canonical=f"/tool/{slug}"))


@router.post("/tool/{slug}/review")
async def submit_review(
    request: Request,
    slug: str,
    rating: int = Form(...),
    review_title: str = Form("", alias="review_title"),
    review_body: str = Form("", alias="review_body"),
):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=302)

    db = request.state.db
    tool = await get_tool_by_slug(db, slug)
    if not tool:
        return RedirectResponse("/", status_code=302)

    # Validate rating
    if rating < 1 or rating > 5:
        rating = 5

    await create_review(
        db,
        tool_id=tool['id'],
        user_id=user['id'],
        rating=rating,
        title=review_title,
        body=review_body,
    )

    return RedirectResponse(f"/tool/{slug}", status_code=303)
