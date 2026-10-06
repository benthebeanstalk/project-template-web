# Contributing

1. Branch from `main`: `feat/...`, `fix/...`, `chore/...`.
2. `just setup` once; `just lint` and `just test` before pushing.
3. Commit with Conventional Commits.
4. Open a PR; CI must pass. Keep PRs small.
5. Never commit secrets; add new variables to `.env.example`.

## Commands
- `just setup`: install dependencies and create `.env` from `.env.example`
- `just db`: start Postgres. `just api` and `just web`: run the backend and the frontend (two terminals)
- `just test`, `just lint`, `just fmt`
- `just coverage`: coverage report (report only, no CI gate)
- `just docs-check`: check docs links, `just` names and paths (read only; allow-list in `docs/.docs-check-ignore`)

## Conventions
- Small commits on feature branches. Do not commit to `main`.
- Never read, edit or commit `.env` files other than `.env.example`.
- Tests: pytest in `backend/tests/` (named `test_*.py`), vitest next to the code. Every bug fix gets a regression test. No real network in tests.
- Run `just lint` and `just test` before you open a PR.
