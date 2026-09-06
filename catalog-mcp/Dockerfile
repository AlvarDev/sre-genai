FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN /uv/bin/uv sync --frozen --no-install-project

FROM python:3.11-slim AS runner
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .

RUN addgroup --system --gid 10001 appgroup && adduser --system --uid 10001 --ingroup appgroup appuser
USER appuser

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
