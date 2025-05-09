FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Add uv to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml ./

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY trainings/ ./trainings/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# Install dependencies using uv
RUN uv pip install --system -e .

# Create data directory
RUN mkdir -p /app/data
