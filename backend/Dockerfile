FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
WORKDIR /app
# Copy the dependency specifications and locks
COPY pyproject.toml uv.lock ./
# Install dependencies into /app/.venv without installing the project yet
RUN /uv/bin/uv sync --frozen --no-install-project
# Copy project code
COPY . .

# Create non-root user for container security
RUN addgroup --system --gid 10001 appgroup && adduser --system --uid 10001 --ingroup appgroup appuser
USER appuser

# Run uvicorn using the virtualenv's binary path
EXPOSE 8080
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
