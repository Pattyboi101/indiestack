FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml README_PYPI.md ./
COPY src/ src/
RUN pip install --no-cache-dir ".[server]"

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY src/ src/
COPY logo/ logo/
COPY founder-photos/ founder-photos/
COPY seed_tools.py seed_social_proof.py seed_search_gaps.py seed_ai_dev_tools.py seed_launch_changelog.py seed_integration_snippets.py seed_mcp_coverage.py seed_comprehensive.py seed_round2.py seed_round3.py seed_plugins.py seed_more_tools.py seed_round4.py purge_seeded_data.py send_comet_email.py send_ed_email.py send_launch_morning.py ./

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "indiestack"]
