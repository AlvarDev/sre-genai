FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN /uv/bin/uv sync --frozen --no-install-project

FROM gcr.io/distroless/python3-debian13:nonroot AS runner
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/.venv/lib/python3.13/site-packages"

WORKDIR /app
COPY --from=builder /app/.venv/lib/python3.13/site-packages /app/.venv/lib/python3.13/site-packages
# Root owns the code; the distroless nonroot group (gid 65532) can read but not change it.
# Works whether the build host creates files as 0644 or 0640.
COPY --chown=0:65532 . .

USER nonroot

EXPOSE 8080
ENTRYPOINT ["/usr/bin/python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
