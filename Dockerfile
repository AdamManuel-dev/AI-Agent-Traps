# AI Agent Traps — Docker reproducibility image
#
# Produces a self-contained environment for running the benchmark suite
# without any local Python installation.
#
# Usage
# -----
#   # Build
#   docker build -t ai-agent-traps .
#
#   # Quick smoke test (no API keys needed)
#   docker run --rm ai-agent-traps python scripts/quick_smoke_test.py
#
#   # Full benchmark run (results mounted to ./results/)
#   docker run --rm -v "$(pwd)/results:/app/results" ai-agent-traps \
#       python scripts/run_benchmark.py --output-dir /app/results
#
#   # With LLM judge (pass API key via env var)
#   docker run --rm \
#       -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
#       -v "$(pwd)/results:/app/results" \
#       ai-agent-traps \
#       python scripts/run_benchmark.py \
#           --model claude-haiku-4-5-20251001 \
#           --budget 0.10 \
#           --output-dir /app/results
#
# Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
# SSRN: ssrn-6372438

FROM python:3.11-slim

# Metadata
LABEL org.opencontainers.image.title="AI Agent Traps"
LABEL org.opencontainers.image.description="Reproducible benchmark environment for the AI Agent Traps taxonomy (Franklin et al., 2025)"
LABEL org.opencontainers.image.authors="Franklin, Tomasev, Jacobs, Leibo, Osindero (Google DeepMind)"

# Install system dependencies
# git: needed for _get_git_hash() provenance tracking
# build-essential: needed by some Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specification first (for layer caching)
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package with all extras for full reproducibility
# The [llm,rag,image] extras are optional — omit if you don't need them
RUN pip install --no-cache-dir -e ".[llm,image,dev]"

# Copy remaining project files
COPY configs/ ./configs/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY README.md REPRODUCTION_NOTES.md ./

# Create results directory for benchmark output
RUN mkdir -p results

# Verify the installation by running the smoke test
# This will fail fast if any imports or core functionality is broken
RUN python scripts/quick_smoke_test.py

# Default command: run the smoke test
CMD ["python", "scripts/quick_smoke_test.py"]
