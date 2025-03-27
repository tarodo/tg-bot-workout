FROM python:3.13-slim

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

# Install dependencies using uv
RUN uv pip install --system -e .

# Run the application
CMD ["python", "-m", "src.bot.main"]
