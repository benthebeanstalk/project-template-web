set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
# Linux CI runners: pwsh is preinstalled, so the PowerShell recipes below run unchanged.
set shell := ["pwsh", "-NoLogo", "-Command"]

default:
    @just --list

# Install deps and create .env if missing
setup:
    uv sync
    pnpm --dir frontend install
    if (-not (Test-Path .env)) { Copy-Item .env.example .env }
    -pre-commit install

# Start Postgres
db:
    docker compose up -d db

# Run backend (:8000) and frontend (:5173); run in two terminals
api:
    uv run uvicorn app.main:app --reload --app-dir backend --port 8000

web:
    pnpm --dir frontend dev

# Build and run the production image on http://localhost:8080
image:
    docker build -t app-local .
    docker run --rm -p 8080:8080 app-local

# Deploy to Fly.io (first deploy: follow docs/deploy.md)
deploy:
    fly deploy

test:
    uv run pytest
    pnpm --dir frontend test

# Coverage report (not a CI gate)
coverage:
    uv run pytest --cov=backend/app --cov-report=term-missing
    pnpm --dir frontend exec vitest run --coverage

lint:
    uv run ruff check .
    uv run ruff format --check .
    pnpm --dir frontend lint

fmt:
    uv run ruff format .
    uv run ruff check --fix .
    pnpm --dir frontend exec prettier --write src

# Quiet test run: prints only failures and a one-line summary. Full log: .logs/test.log
test-quiet:
    @& ./scripts/quiet.ps1 -Name test -Commands 'uv run pytest -q --tb=short','pnpm --dir frontend exec vitest run --reporter=dot'; exit $LASTEXITCODE

# Quiet lint run: prints only findings and a one-line summary. Full log: .logs/lint.log
lint-quiet:
    @& ./scripts/quiet.ps1 -Name lint -Commands 'uv run ruff check . --output-format=concise','uv run ruff format --check .','pnpm --dir frontend exec eslint . --quiet'; exit $LASTEXITCODE

# Self-test for the quiet recipes (a failing command must fail the run)
quiet-selftest:
    @& ./scripts/quiet-selftest.ps1; exit $LASTEXITCODE

# Check docs links, `just` names and paths in the Markdown files (read only, no network). Allow-list: docs/.docs-check-ignore
docs-check:
    uv run --no-project python scripts/docs_check.py
