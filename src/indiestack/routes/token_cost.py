"""Token cost methodology — explains how IndieStack calculates token savings."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/token-cost", response_class=HTMLResponse)
async def token_cost_page(request: Request):
    user = request.state.user

    body = '''
    <div style="max-width:720px;margin:0 auto;padding:64px 24px;">

        <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);line-height:1.2;margin-bottom:8px;">
            How We Calculate Token Savings
        </h1>
        <p style="font-size:18px;color:var(--ink-muted);line-height:1.7;margin-bottom:48px;">
            When an AI agent uses IndieStack instead of generating infrastructure code from scratch,
            it saves tokens. Here&rsquo;s exactly how we measure that.
        </p>

        <!-- The Problem -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                The problem: agents reinvent the wheel
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;">
                When you ask an AI coding agent to &ldquo;add authentication&rdquo; or &ldquo;set up payments,&rdquo;
                it generates hundreds of lines of boilerplate from scratch. This burns
                <strong style="color:var(--ink);">5,000&ndash;30,000 output tokens</strong> per infrastructure task,
                depending on complexity.
            </p>
            <p style="color:var(--ink-light);line-height:1.7;margin-top:12px;">
                If instead the agent queries IndieStack, finds a suitable tool, and writes the integration code,
                it typically uses <strong style="color:var(--ink);">500&ndash;3,000 tokens</strong> &mdash;
                a 5&ndash;10x reduction.
            </p>
        </div>

        <!-- Methodology -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                Methodology
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;margin-bottom:16px;">
                We assign each category an estimated &ldquo;build-from-scratch&rdquo; token cost based on
                the typical output an agent would generate. These are rough estimates, not precise measurements.
            </p>
            <div class="card" style="padding:20px;margin-bottom:16px;">
                <table style="width:100%;border-collapse:collapse;font-size:14px;">
                    <thead>
                        <tr style="border-bottom:2px solid var(--border);">
                            <th style="padding:8px 12px;text-align:left;font-size:12px;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Category</th>
                            <th style="padding:8px 12px;text-align:right;font-size:12px;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Est. build cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:8px 12px;color:var(--ink);">Authentication</td>
                            <td style="padding:8px 12px;text-align:right;font-family:var(--font-mono);color:var(--ink);">~25,000 tokens</td>
                        </tr>
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:8px 12px;color:var(--ink);">Payments</td>
                            <td style="padding:8px 12px;text-align:right;font-family:var(--font-mono);color:var(--ink);">~20,000 tokens</td>
                        </tr>
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:8px 12px;color:var(--ink);">Database</td>
                            <td style="padding:8px 12px;text-align:right;font-family:var(--font-mono);color:var(--ink);">~15,000 tokens</td>
                        </tr>
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:8px 12px;color:var(--ink);">Analytics</td>
                            <td style="padding:8px 12px;text-align:right;font-family:var(--font-mono);color:var(--ink);">~12,000 tokens</td>
                        </tr>
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:8px 12px;color:var(--ink);">Email</td>
                            <td style="padding:8px 12px;text-align:right;font-family:var(--font-mono);color:var(--ink);">~10,000 tokens</td>
                        </tr>
                        <tr>
                            <td style="padding:8px 12px;color:var(--ink-muted);">Other categories</td>
                            <td style="padding:8px 12px;text-align:right;font-family:var(--font-mono);color:var(--ink-muted);">~15,000 tokens</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <p style="color:var(--ink-muted);font-size:13px;line-height:1.6;">
                These estimates are conservative approximations. Actual savings depend on the specific task,
                the model used, and how many attempts the agent needs. We use these figures for our
                &ldquo;tokens saved&rdquo; metrics and the <a href="/calculator" style="color:var(--accent);">/calculator</a> page.
            </p>
        </div>

        <!-- How it works -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                How the savings happen
            </h2>
            <div style="display:flex;flex-direction:column;gap:16px;">
                <div style="display:flex;gap:16px;align-items:flex-start;">
                    <div style="min-width:32px;height:32px;border-radius:50%;background:var(--accent);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">1</div>
                    <div>
                        <strong style="color:var(--ink);">Agent queries IndieStack</strong>
                        <p style="color:var(--ink-light);margin:4px 0 0;font-size:14px;">
                            &ldquo;Find me an auth solution for Next.js&rdquo; &mdash; ~50 tokens for the API call.
                        </p>
                    </div>
                </div>
                <div style="display:flex;gap:16px;align-items:flex-start;">
                    <div style="min-width:32px;height:32px;border-radius:50%;background:var(--accent);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">2</div>
                    <div>
                        <strong style="color:var(--ink);">Gets structured recommendations</strong>
                        <p style="color:var(--ink-light);margin:4px 0 0;font-size:14px;">
                            Tool name, install command, API type, compatibility data &mdash; ~200 tokens to parse.
                        </p>
                    </div>
                </div>
                <div style="display:flex;gap:16px;align-items:flex-start;">
                    <div style="min-width:32px;height:32px;border-radius:50%;background:var(--accent);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">3</div>
                    <div>
                        <strong style="color:var(--ink);">Writes integration code</strong>
                        <p style="color:var(--ink-light);margin:4px 0 0;font-size:14px;">
                            Install + configure an existing tool: ~1,000&ndash;3,000 tokens. Build from scratch: 10,000&ndash;30,000.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Caveats -->
        <div style="margin-bottom:40px;padding:24px;background:var(--cream-dark);border-radius:var(--radius);border:1px solid var(--border);">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">
                Honest caveats
            </h3>
            <ul style="color:var(--ink-light);line-height:2.0;padding-left:0;list-style:none;">
                <li style="position:relative;padding-left:24px;">
                    <span style="position:absolute;left:0;color:var(--ink-muted);">&mdash;</span>
                    These are estimates, not benchmarks. Different models produce different token counts.
                </li>
                <li style="position:relative;padding-left:24px;">
                    <span style="position:absolute;left:0;color:var(--ink-muted);">&mdash;</span>
                    Token savings assume the agent would have built from scratch. If the dev was going to write the code manually, the comparison doesn&rsquo;t apply.
                </li>
                <li style="position:relative;padding-left:24px;">
                    <span style="position:absolute;left:0;color:var(--ink-muted);">&mdash;</span>
                    We don&rsquo;t count the tokens used to read IndieStack&rsquo;s response in the savings figure. The net saving is lower than the gross.
                </li>
                <li style="position:relative;padding-left:24px;">
                    <span style="position:absolute;left:0;color:var(--ink-muted);">&mdash;</span>
                    Not every search leads to a tool adoption. Our &ldquo;tokens saved&rdquo; metric only counts adopted outcomes.
                </li>
            </ul>
        </div>

        <!-- CTA -->
        <div style="text-align:center;padding:32px 0;border-top:1px solid var(--border);">
            <a href="/setup" class="btn btn-lg btn-primary">Set Up IndieStack &rarr;</a>
            <p style="color:var(--ink-muted);font-size:13px;margin-top:12px;">
                Free. No API key required.
            </p>
        </div>
    </div>
    '''

    return HTMLResponse(page_shell(
        "How We Calculate Token Savings",
        body,
        user=user,
        description="IndieStack's token savings methodology: how we measure the cost difference between AI agents building from scratch vs using existing tools.",
        canonical="/token-cost",
    ))
