FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN /uv/bin/uv sync --frozen --no-install-project

FROM python:3.13-slim AS runner
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
RUN addgroup --system --gid 10001 appgroup && adduser --system --uid 10001 --ingroup appgroup appuser
COPY --from=builder /app/.venv /app/.venv
# Root owns the code; the app's group (gid 10001, created above) can read but not change it.
# Works whether the build host creates files as 0644 or 0640.
COPY --chown=0:10001 . .

USER appuser

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
