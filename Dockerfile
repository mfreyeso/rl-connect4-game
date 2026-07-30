FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --no-create-home appuser

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock ./
COPY connect4/ connect4/
COPY static/ static/

# Copy Q-table (trained model)
COPY q_table.pkl ./

# Install dependencies (as root, before dropping privileges)
RUN uv sync --frozen --no-dev --link-mode=copy

# Give appuser read access to the installed venv
RUN chown -R appuser:appuser /app

# Drop privileges
USER appuser

ENV ENV=production
ENV UV_CACHE_DIR=/tmp/uv-cache

# Expose port
EXPOSE 8000

# --no-sync prevents uv from trying to re-install packages as appuser
CMD ["sh", "-c", "exec uv run --no-sync uvicorn connect4.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
