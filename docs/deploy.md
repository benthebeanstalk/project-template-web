# Deploy to Fly.io

One Fly app serves the API and the built frontend. The Dockerfile builds both. The API serves the frontend files from `/app/static`.

You must do the account steps yourself. An agent must not create accounts or enter payment details.

## One-time setup
1. Create a Fly.io account and add a payment method.
2. Install the CLI: `winget install --id Fly-io.flyctl -e`. Open a new terminal.
3. Log in: `fly auth login`.
4. Choose a unique app name. Put it in `fly.toml` (`app = "..."`).
5. Create the app: `fly apps create <name>`.
6. Create a Postgres database in the Fly dashboard (Managed Postgres) or with `fly postgres create`. Attach it to the app. Attaching sets the `DATABASE_URL` secret.
7. Set `FRONTEND_ORIGIN` to the app URL: `fly secrets set FRONTEND_ORIGIN=https://<name>.fly.dev`.

The API changes `postgres://` URLs to the `postgresql+psycopg://` form by itself.

## Deploy
```
fly deploy
```
Open `https://<name>.fly.dev`. The page must show "API status: ok".

## Test the image before you deploy
```
docker build -t app-local .
docker run --rm -p 8080:8080 app-local
```
Open http://localhost:8080. The health check is `/api/health`.

## Rules
- Never put secrets in `fly.toml` or the Dockerfile. Use `fly secrets set`.
- The app stops when idle (`min_machines_running = 0`). The first request after a pause is slow.
- Add a deploy step to CI only after a human has done the first deploy.
