FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml .

# Install dependencies (without lock file for now, or I'll generate it)
RUN uv sync --no-install-project

# Copy source code
COPY core.py .
COPY app.py .

# Create downloads directory
RUN mkdir downloads

# Expose Chainlit port
EXPOSE 8000

# Run chainlit
CMD ["uv", "run", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]