"""User authentication routes — login, signup, logout, GitHub OAuth."""

import os
import secrets as _secrets
from html import escape

import httpx
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell
from indiestack.auth import hash_password, verify_password, create_user_session
from indiestack.db import (
    get_user_by_email, create_user, get_or_create_maker, update_user, delete_session, update_maker,
    create_password_reset_token, get_valid_reset_token, mark_reset_token_used,
    create_email_verification_token, verify_email_token,
    get_user_by_github_id, create_github_user, link_github_to_user,
)
from indiestack.email import send_email, password_reset_html, email_verification_html, welcome_signup_html

router = APIRouter()

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")

_GITHUB_SVG = '<svg width="20" height="20" viewBox="0 0 16 16" fill="white"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'


def _github_button(next_url: str = "") -> str:
    """GitHub sign-in button + divider. Returns empty string if OAuth not configured."""
    if not GITHUB_CLIENT_ID:
        return ""
    qs = f"?next={next_url}" if next_url else ""
    return f"""
    <a href="/auth/github{qs}" style="display:flex;align-items:center;justify-content:center;gap:10px;
       width:100%;padding:12px;background:#24292e;color:white;border-radius:8px;text-decoration:none;
       font-weight:600;font-size:15px;margin-bottom:20px;box-sizing:border-box;">
        {_GITHUB_SVG}
        Sign in with GitHub
    </a>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
        <div style="flex:1;height:1px;background:var(--border);"></div>
        <span style="color:var(--ink-muted);font-size:13px;">or</span>
        <div style="flex:1;height:1px;background:var(--border);"></div>
    </div>
    """


# ── Login ────────────────────────────────────────────────────────────────

def _safe_next(url: str) -> str:
    """Validate a next= redirect URL. Must start with / but not // (protocol-relative)."""
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return ""


def login_form(error: str = "", email: str = "", next_url: str = "") -> str:
    alert = f'<div class="alert alert-error">{escape(error)}</div>' if error else ''
    next_hidden = f'<input type="hidden" name="next" value="{escape(next_url)}">' if next_url else ''
    next_qs = f"?next={escape(next_url)}" if next_url else ""
    return f"""
    <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;">
        <div class="card" style="max-width:420px;width:100%;">
            <h1 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:24px;color:var(--ink);">
                Log In
            </h1>
            {alert}
            {_github_button(next_url)}
            <form method="post" action="/login">
                {next_hidden}
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" class="form-input" required
                           value="{escape(email)}" placeholder="you@example.com" autocomplete="email">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" class="form-input" required
                           placeholder="Your password" autocomplete="current-password">
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:12px;">
                    Log In
                </button>
            </form>
            <p style="text-align:center;margin-top:12px;font-size:14px;">
                <a href="/forgot-password" style="color:var(--ink-muted);text-decoration:none;">Forgot your password?</a>
            </p>
            <p style="text-align:center;margin-top:8px;font-size:14px;color:var(--ink-muted);">
                Don't have an account? <a href="/signup{next_qs}" style="color:var(--terracotta);font-weight:600;">Sign up</a>
            </p>
        </div>
    </div>
    """


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if request.state.user:
        return RedirectResponse(url="/dashboard", status_code=303)
    next_url = _safe_next(request.query_params.get("next", ""))
    return HTMLResponse(page_shell("Log In", login_form(next_url=next_url), user=request.state.user))


@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, email: str = Form(""), password: str = Form(""), next: str = Form("")):
    db = request.state.db
    next_url = _safe_next(next)

    if not email.strip() or not password:
        return HTMLResponse(page_shell("Log In", login_form("Please enter your email and password.", email, next_url=next_url),
                                       user=request.state.user))

    user = await get_user_by_email(db, email)
    if not user:
        return HTMLResponse(page_shell("Log In", login_form("Invalid email or password.", email, next_url=next_url),
                                       user=request.state.user))

    if user['password_hash'] == 'GITHUB_OAUTH_NO_PASSWORD':
        return HTMLResponse(page_shell("Log In", login_form(
            "This account uses GitHub login. Click 'Sign in with GitHub' above.", email, next_url=next_url),
            user=request.state.user))

    if not verify_password(password, user['password_hash']):
        return HTMLResponse(page_shell("Log In", login_form("Invalid email or password.", email, next_url=next_url),
                                       user=request.state.user))

    token = await create_user_session(db, user['id'])
    redirect_to = next_url or "/dashboard"
    response = RedirectResponse(url=redirect_to, status_code=303)
    response.set_cookie(key="indiestack_session", value=token, httponly=True, samesite="lax", max_age=30*86400, secure=True)
    return response


# ── Signup ───────────────────────────────────────────────────────────────

def signup_form(error: str = "", values: dict = None, next_url: str = "", ref: str = "") -> str:
    v = values or {}
    alert = f'<div class="alert alert-error">{escape(error)}</div>' if error else ''
    is_maker_checked = ' checked' if v.get('is_maker') else ''
    next_hidden = f'<input type="hidden" name="next" value="{escape(next_url)}">' if next_url else ''
    ref_hidden = f'<input type="hidden" name="ref" value="{escape(ref)}">' if ref else ''
    next_qs = f"?next={escape(next_url)}" if next_url else ""
    return f"""
    <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;">
        <div class="card" style="max-width:420px;width:100%;">
            <h1 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:24px;color:var(--ink);">
                Create Account
            </h1>
            {alert}
            {_github_button(next_url)}
            <form method="post" action="/signup">
                {next_hidden}
                {ref_hidden}
                <div class="form-group">
                    <label for="name">Name</label>
                    <input type="text" id="name" name="name" class="form-input" required
                           value="{escape(str(v.get('name', '')))}" placeholder="Your name" autocomplete="name">
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" class="form-input" required
                           value="{escape(str(v.get('email', '')))}" placeholder="you@example.com" autocomplete="email">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" class="form-input" required
                           placeholder="At least 8 characters" autocomplete="new-password" minlength="8">
                </div>
                <div class="form-group" style="display:flex;align-items:center;gap:8px;">
                    <input type="checkbox" id="is_maker" name="is_maker" value="1"{is_maker_checked}
                           style="accent-color:var(--terracotta);">
                    <label for="is_maker" style="margin-bottom:0;cursor:pointer;">I'm a maker (I build tools)</label>
                </div>
                <div class="form-group" id="team-size-group" style="display:none;margin-top:-8px;padding-left:26px;">
                    <label for="indie_status">Team size</label>
                    <select id="indie_status" name="indie_status" class="form-select" style="max-width:200px;">
                        <option value="solo">Solo developer</option>
                        <option value="small_team">Small team (2-5)</option>
                        <option value="company">Company</option>
                    </select>
                </div>
                <script>
                document.getElementById('is_maker').addEventListener('change', function() {{
                    document.getElementById('team-size-group').style.display = this.checked ? 'block' : 'none';
                }});
                </script>
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:12px;">
                    Create Account
                </button>
            </form>
            <p style="text-align:center;margin-top:16px;font-size:14px;color:var(--ink-muted);">
                Already have an account? <a href="/login{next_qs}" style="color:var(--terracotta);font-weight:600;">Log in</a>
            </p>
        </div>
    </div>
    """


@router.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    if request.state.user:
        return RedirectResponse(url="/dashboard", status_code=303)
    next_url = _safe_next(request.query_params.get("next", ""))
    ref = request.query_params.get('ref', '')
    return HTMLResponse(page_shell("Sign Up", signup_form(next_url=next_url, ref=ref), user=request.state.user))


@router.post("/signup", response_class=HTMLResponse)
async def signup_post(
    request: Request,
    name: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    is_maker: str = Form(""),
    indie_status: str = Form(""),
    next: str = Form(""),
    ref: str = Form(""),
):
    db = request.state.db
    next_url = _safe_next(next)
    values = dict(name=name, email=email, is_maker=is_maker)

    errors = []
    if not name.strip():
        errors.append("Name is required.")
    if not email.strip() or '@' not in email:
        errors.append("Valid email is required.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")

    if errors:
        return HTMLResponse(page_shell("Sign Up", signup_form(" ".join(errors), values, next_url=next_url, ref=ref),
                                       user=request.state.user))

    # Check if email already exists
    existing = await get_user_by_email(db, email)
    if existing:
        return HTMLResponse(page_shell("Sign Up", signup_form("An account with that email already exists.", values, next_url=next_url, ref=ref),
                                       user=request.state.user))

    role = 'maker' if is_maker else 'buyer'
    pw_hash = hash_password(password)

    # If maker, try to match or create maker profile
    maker_id = None
    if is_maker:
        maker_id = await get_or_create_maker(db, name.strip(), '')

    if is_maker and maker_id:
        if indie_status in ('solo', 'small_team', 'company'):
            await update_maker(db, maker_id, indie_status=indie_status)

    user_id = await create_user(db, email=email, password_hash=pw_hash,
                                 name=name.strip(), role=role, maker_id=maker_id)

    # Handle referral
    ref_code = ref.strip()
    if ref_code:
        from indiestack.db import get_user_by_referral_code
        referrer = await get_user_by_referral_code(db, ref_code)
        if referrer and referrer['id'] != user_id:
            await db.execute("UPDATE users SET referred_by = ? WHERE id = ?",
                            (referrer['id'], user_id))
            await db.commit()

    # Send verification email
    verify_token = await create_email_verification_token(db, user_id)
    base_url = str(request.base_url).rstrip("/").replace("http://", "https://")
    verify_url = f"{base_url}/verify-email?token={verify_token}"
    await send_email(email, "Verify your IndieStack email", email_verification_html(verify_url))

    # Send welcome email
    await send_email(email, "Welcome to IndieStack", welcome_signup_html())

    token = await create_user_session(db, user_id)
    redirect_to = next_url or "/dashboard"
    response = RedirectResponse(url=redirect_to, status_code=303)
    response.set_cookie(key="indiestack_session", value=token, httponly=True, samesite="lax", max_age=30*86400, secure=True)
    return response


# ── Logout ───────────────────────────────────────────────────────────────

@router.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("indiestack_session")
    if token:
        await delete_session(request.state.db, token)
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("indiestack_session")
    return response


# ── Forgot Password ──────────────────────────────────────────────────────

@router.get("/forgot-password")
async def forgot_password_form(request: Request):
    user = request.state.user
    if user:
        return RedirectResponse("/dashboard", status_code=303)

    body = '''
    <div style="max-width:420px;margin:60px auto;padding:0 20px;">
        <h1 style="font-family:var(--font-display);color:var(--terracotta);margin-bottom:8px;">Reset Password</h1>
        <p style="color:var(--ink-muted);margin-bottom:32px;">Enter your email and we'll send you a reset link.</p>
        <form method="POST" action="/forgot-password">
            <label style="display:block;font-size:14px;font-weight:600;color:var(--ink);margin-bottom:6px;">Email</label>
            <input type="email" name="email" required placeholder="you@example.com"
                style="width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:15px;box-sizing:border-box;margin-bottom:24px;">
            <button type="submit" style="width:100%;padding:14px;background:var(--terracotta);color:white;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;">Send Reset Link</button>
        </form>
        <p style="text-align:center;margin-top:20px;font-size:14px;color:var(--ink-muted);">
            <a href="/login" style="color:var(--terracotta);text-decoration:none;">Back to login</a>
        </p>
    </div>
    '''
    return HTMLResponse(page_shell("Forgot Password", body, user=None))


@router.post("/forgot-password")
async def forgot_password_submit(request: Request):
    form = await request.form()
    email = form.get("email", "").strip().lower()
    db = request.state.db

    # Always show success message (security: don't reveal if email exists)
    success_body = '''
    <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
        <div style="font-size:48px;margin-bottom:16px;">&#9993;</div>
        <h1 style="font-family:var(--font-display);color:var(--terracotta);margin-bottom:8px;">Check Your Email</h1>
        <p style="color:var(--ink-muted);line-height:1.6;">If an account with that email exists, we've sent a password reset link. It expires in 1 hour.</p>
        <p style="margin-top:24px;font-size:14px;"><a href="/login" style="color:var(--terracotta);text-decoration:none;">Back to login</a></p>
    </div>
    '''

    if email:
        user = await get_user_by_email(db, email)
        if user:
            token = await create_password_reset_token(db, user['id'])
            base_url = str(request.base_url).rstrip("/").replace("http://", "https://")
            reset_url = f"{base_url}/reset-password?token={token}"
            await send_email(email, "Reset your IndieStack password", password_reset_html(reset_url))

    return HTMLResponse(page_shell("Check Your Email", success_body, user=None))


@router.get("/reset-password")
async def reset_password_form(request: Request):
    token = request.query_params.get("token", "")
    db = request.state.db

    user_id = await get_valid_reset_token(db, token)
    if not user_id:
        body = '''
        <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
            <h1 style="font-family:var(--font-display);color:var(--terracotta);margin-bottom:8px;">Invalid or Expired Link</h1>
            <p style="color:var(--ink-muted);">This reset link is no longer valid. Please request a new one.</p>
            <a href="/forgot-password" style="display:inline-block;margin-top:20px;padding:12px 28px;background:var(--terracotta);color:white;border-radius:8px;text-decoration:none;font-weight:600;">Request New Link</a>
        </div>
        '''
        return HTMLResponse(page_shell("Invalid Link", body, user=None))

    body = f'''
    <div style="max-width:420px;margin:60px auto;padding:0 20px;">
        <h1 style="font-family:var(--font-display);color:var(--terracotta);margin-bottom:8px;">Set New Password</h1>
        <p style="color:var(--ink-muted);margin-bottom:32px;">Choose a new password for your account.</p>
        <form method="POST" action="/reset-password">
            <input type="hidden" name="token" value="{token}">
            <label style="display:block;font-size:14px;font-weight:600;color:var(--ink);margin-bottom:6px;">New Password</label>
            <input type="password" name="password" required minlength="8" placeholder="Min 8 characters"
                style="width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:15px;box-sizing:border-box;margin-bottom:16px;">
            <label style="display:block;font-size:14px;font-weight:600;color:var(--ink);margin-bottom:6px;">Confirm Password</label>
            <input type="password" name="password_confirm" required minlength="8" placeholder="Confirm password"
                style="width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:15px;box-sizing:border-box;margin-bottom:24px;">
            <button type="submit" style="width:100%;padding:14px;background:var(--terracotta);color:white;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;">Update Password</button>
        </form>
    </div>
    '''
    return HTMLResponse(page_shell("Reset Password", body, user=None))


@router.post("/reset-password")
async def reset_password_submit(request: Request):
    form = await request.form()
    token = form.get("token", "")
    password = form.get("password", "")
    password_confirm = form.get("password_confirm", "")
    db = request.state.db

    if password != password_confirm:
        body = '''
        <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
            <p style="color:#c0392b;font-weight:600;">Passwords do not match.</p>
            <a href="javascript:history.back()" style="color:var(--terracotta);text-decoration:none;">Go back</a>
        </div>
        '''
        return HTMLResponse(page_shell("Error", body, user=None))

    if len(password) < 8:
        body = '''
        <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
            <p style="color:#c0392b;font-weight:600;">Password must be at least 8 characters.</p>
            <a href="javascript:history.back()" style="color:var(--terracotta);text-decoration:none;">Go back</a>
        </div>
        '''
        return HTMLResponse(page_shell("Error", body, user=None))

    user_id = await get_valid_reset_token(db, token)
    if not user_id:
        body = '''
        <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
            <h1 style="font-family:var(--font-display);color:var(--terracotta);">Invalid or Expired Link</h1>
            <p style="color:var(--ink-muted);">Please request a new reset link.</p>
            <a href="/forgot-password" style="display:inline-block;margin-top:20px;padding:12px 28px;background:var(--terracotta);color:white;border-radius:8px;text-decoration:none;font-weight:600;">Request New Link</a>
        </div>
        '''
        return HTMLResponse(page_shell("Invalid Link", body, user=None))

    # Hash new password using same method as signup
    new_hash = hash_password(password)
    await update_user(db, user_id, password_hash=new_hash)
    await mark_reset_token_used(db, token)

    body = '''
    <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
        <div style="font-size:48px;margin-bottom:16px;">&#10003;</div>
        <h1 style="font-family:var(--font-display);color:var(--terracotta);">Password Updated</h1>
        <p style="color:var(--ink-muted);margin-bottom:24px;">Your password has been reset. You can now log in.</p>
        <a href="/login" style="display:inline-block;padding:12px 28px;background:var(--terracotta);color:white;border-radius:8px;text-decoration:none;font-weight:600;">Log In</a>
    </div>
    '''
    return HTMLResponse(page_shell("Password Updated", body, user=None))


# ── GitHub OAuth ─────────────────────────────────────────────────────────

@router.get("/auth/github")
async def github_auth(request: Request):
    if not GITHUB_CLIENT_ID:
        return RedirectResponse("/login", status_code=303)
    next_url = _safe_next(request.query_params.get("next", ""))
    state = _secrets.token_urlsafe(32)
    callback = str(request.base_url).rstrip("/").replace("http://", "https://") + "/auth/github/callback"
    url = (f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}"
           f"&scope=user:email&state={state}&redirect_uri={callback}")
    response = RedirectResponse(url=url, status_code=303)
    response.set_cookie("github_oauth_state", f"{state}|{next_url}", httponly=True, samesite="lax", max_age=600, secure=True)
    return response


@router.get("/auth/github/callback")
async def github_callback(request: Request):
    code = request.query_params.get("code", "")
    state = request.query_params.get("state", "")

    # Validate CSRF state
    cookie_state = request.cookies.get("github_oauth_state", "")
    parts = cookie_state.split("|", 1)
    expected_state = parts[0] if parts else ""
    next_url = _safe_next(parts[1] if len(parts) > 1 else "")

    if not code or not state or state != expected_state:
        return RedirectResponse("/login?error=github_failed", status_code=303)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Exchange code for access token
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                json={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
                headers={"Accept": "application/json"},
            )
            token_data = token_resp.json()
            access_token = token_data.get("access_token", "")
            if not access_token:
                return RedirectResponse("/login?error=github_failed", status_code=303)

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            # Fetch user profile
            user_resp = await client.get("https://api.github.com/user", headers=headers)
            gh_user = user_resp.json()

            # Fetch emails (user:email scope)
            emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
            emails = emails_resp.json()

        github_id = gh_user.get("id")
        github_username = gh_user.get("login", "")
        github_avatar = gh_user.get("avatar_url", "")
        name = gh_user.get("name") or github_username

        # Find primary verified email
        email = ""
        if isinstance(emails, list):
            for e in emails:
                if e.get("primary") and e.get("verified"):
                    email = e["email"]
                    break
            if not email:
                for e in emails:
                    if e.get("verified"):
                        email = e["email"]
                        break
        if not email:
            email = gh_user.get("email", "")

        if not email or not github_id:
            return RedirectResponse("/login?error=github_no_email", status_code=303)

        db = request.state.db

        # Three-way user matching
        existing = await get_user_by_github_id(db, github_id)
        if existing:
            user_id = existing["id"]
        else:
            existing_email = await get_user_by_email(db, email)
            if existing_email:
                await link_github_to_user(db, existing_email["id"], github_id, github_username, github_avatar)
                user_id = existing_email["id"]
            else:
                user_id = await create_github_user(db, email, name, github_id, github_username, github_avatar)

        # Create session and redirect
        token = await create_user_session(db, user_id)
        redirect_to = next_url or "/dashboard"
        response = RedirectResponse(url=redirect_to, status_code=303)
        response.set_cookie(key="indiestack_session", value=token, httponly=True, samesite="lax", max_age=30*86400, secure=True)
        response.delete_cookie("github_oauth_state")
        return response

    except Exception:
        return RedirectResponse("/login?error=github_failed", status_code=303)


# ── Email Verification ───────────────────────────────────────────────────

@router.get("/verify-email")
async def verify_email(request: Request):
    token = request.query_params.get("token", "")
    db = request.state.db

    user_id = await verify_email_token(db, token)
    if user_id:
        return RedirectResponse("/dashboard?verified=1", status_code=303)

    body = '''
    <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
        <h1 style="font-family:var(--font-display);color:var(--terracotta);">Invalid or Expired Link</h1>
        <p style="color:var(--ink-muted);">This verification link is no longer valid.</p>
        <a href="/resend-verification" style="display:inline-block;margin-top:20px;padding:12px 28px;background:var(--terracotta);color:white;border-radius:8px;text-decoration:none;font-weight:600;">Resend Verification</a>
    </div>
    '''
    return HTMLResponse(page_shell("Invalid Link", body, user=None))


@router.get("/resend-verification")
async def resend_verification(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user['email_verified']:
        return RedirectResponse("/dashboard", status_code=303)

    db = request.state.db
    token = await create_email_verification_token(db, user['id'])
    base_url = str(request.base_url).rstrip("/").replace("http://", "https://")
    verify_url = f"{base_url}/verify-email?token={token}"
    await send_email(user['email'], "Verify your IndieStack email", email_verification_html(verify_url))

    body = '''
    <div style="max-width:420px;margin:60px auto;padding:0 20px;text-align:center;">
        <div style="font-size:48px;margin-bottom:16px;">&#9993;</div>
        <h1 style="font-family:var(--font-display);color:var(--terracotta);">Verification Sent</h1>
        <p style="color:var(--ink-muted);">Check your email for a verification link.</p>
        <p style="margin-top:20px;font-size:14px;"><a href="/dashboard" style="color:var(--terracotta);text-decoration:none;">Back to dashboard</a></p>
    </div>
    '''
    return HTMLResponse(page_shell("Verification Sent", body, user=user))
