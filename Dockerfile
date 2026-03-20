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
COPY scripts/ scripts/
COPY logo/ logo/
COPY founder-photos/ founder-photos/


ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "indiestack"]
