FROM python:3.12-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY src src
COPY api api
COPY models models
COPY uv.lock uv.lock
COPY pyproject.toml pyproject.toml
COPY README.md README.md
ENV UV_NO_DEV=1 \
    UV_FROZEN=1
RUN uv sync
CMD ["uv", "run", "uvicorn", "api.fast:app", "--host", "0.0.0.0", "--port", "8080"]
