# syntax=docker/dockerfile:1.7
# Context-enriched ad generation: Streamlit apps, pipeline, evaluator, tests.
# Builds natively for linux/arm64 and linux/amd64. Model calls go to a LiteLLM proxy (see env.example).

FROM node:22-bookworm-slim AS node

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_NO_SYNC=1 \
    PATH="/opt/venv/bin:${PATH}" \
    U2NET_HOME=/models/rembg \
    NUMBA_CACHE_DIR=/tmp/numba \
    PROMPTFOO_DISABLE_TELEMETRY=1 \
    PROMPTFOO_PYTHON=/opt/venv/bin/python

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Node 22 for promptfoo (eval-dev / eval-test only).
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

COPY --from=ghcr.io/astral-sh/uv:0.9.4 /uv /usr/local/bin/uv

# The app runs as this user; the entrypoint starts as root only to fix volume ownership, then drops to it.
RUN useradd --create-home --uid 1000 app

WORKDIR /app

# Dependencies first, so code changes do not invalidate the dependency layer.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY --chown=app:app . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen \
    && chmod +x scripts/docker-entrypoint.sh \
    && mkdir -p /models /app/data/runs \
    && chown app:app /app \
    && chown -R app:app /models /app/data /opt/venv

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=2m --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4)"

ENTRYPOINT ["scripts/docker-entrypoint.sh"]
CMD ["demo"]
