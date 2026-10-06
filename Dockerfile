# Stage 1: build the frontend
FROM node:24-slim AS frontend
RUN npm install -g pnpm@12.8.1
WORKDIR /build
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# Stage 2: API plus built frontend
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./backend/
COPY --from=frontend /build/dist ./static
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/backend
RUN useradd --system --no-create-home app
USER app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
