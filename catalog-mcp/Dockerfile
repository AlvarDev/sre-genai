FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
WORKDIR /app
# Copy dependency specification and locks
COPY pyproject.toml uv.lock ./
# Install dependencies into /app/.venv
RUN /uv/bin/uv sync --frozen --no-install-project
# Copy project code
COPY . .
# Run uvicorn using the virtualenv's binary path
EXPOSE 8001
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
