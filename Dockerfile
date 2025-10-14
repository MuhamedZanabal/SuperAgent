FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN useradd -m -u 1000 superagent && \
    mkdir -p /app /data && \
    chown -R superagent:superagent /app /data

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY --chown=superagent:superagent pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY --chown=superagent:superagent superagent/ ./superagent/

# Switch to app user
USER superagent

# Set data directory
ENV SUPERAGENT_DATA_DIR=/data

# Expose port for API (if needed)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import superagent; print('healthy')" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "superagent"]
CMD ["--help"]
