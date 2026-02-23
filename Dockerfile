FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock ./
COPY connect4/ connect4/
COPY static/ static/

# Copy Q-table (trained model)
COPY q_table.pkl ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8000

# Run the web server
CMD ["uv", "run", "uvicorn", "connect4.api:app", "--host", "0.0.0.0", "--port", "8000"]
