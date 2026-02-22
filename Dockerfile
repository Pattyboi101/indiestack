FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY src/ src/
COPY logo/ logo/
COPY seed_tools.py seed_social_proof.py purge_seeded_data.py ./

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "indiestack"]
