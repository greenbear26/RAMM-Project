# Your Team's Live Deployment

Your team's app is automatically deployed to the course's Coolify server whenever you push to `main`.

## URLs

- **Your Streamlit app:** `https://team{N}.neu-in-leuven.cloud`
- **Your Flask API (optional, ask staff):** `https://team{N}-api.neu-in-leuven.cloud`

Ask course staff for your specific team number if you don't know it yet.

By default only the Streamlit app is publicly reachable. The Streamlit app talks to the Flask API through the internal Docker network, so you don't need a public API URL for the app to work. If you specifically want to hit your API from outside (e.g. with `curl` or Postman), ask staff to enable the API domain for your team.

## How it works

1. You push to `main` on your team's GitHub fork.
2. GitHub notifies Coolify via a webhook.
3. Coolify pulls your repo, builds the Docker images from `docker-compose.prod.yaml`, and restarts your stack.
4. Within ~1–3 minutes, your changes are live.

No GitHub Actions runs. No CI to pass. The deploy is triggered purely by the push.

## Watching a deploy / reading logs

Course staff can grant you view-only access to the Coolify dashboard at `coolify.cs4535.cloud`. There you can:

- See the live deploy progress.
- Read container logs (`app`, `api`, `db`) — useful when something works locally but not in production.
- Manually trigger a redeploy.

## A note on the database

Both local dev and production run MySQL **without a persistent volume**. Every fresh container start reseeds the database from `database-files/*.sql`. This means:

- The SQL files in your repo are the source of truth for what's in the database.
- Rows you insert through the app (e.g. via the **Add NGO** page) disappear when the container is recreated (on every push to production, or any `docker compose down && up` locally).
- To make data "permanent," add it to `database-files/*.sql` and commit.

## What's different between local dev and production

- **Local (`docker compose up`)** mounts your source code into the containers for hot-reload. Edit a file → see the change immediately.
- **Production (Coolify)** builds the source into the image at deploy time. To change production, you must commit and push.

Everything else — service names, ports, the MySQL schema — is the same in both.

## Changing a secret or env var

The values of `SECRET_KEY`, `MYSQL_ROOT_PASSWORD`, etc., live in Coolify's UI, not in your repo. To change one, ask course staff.

## When things break

1. Check the Coolify logs first (or ask staff to).
2. The most common failure is an SQL syntax error in `database-files/*.sql` — those scripts run on **every** deploy (the database is reseeded from scratch each time), so a bad SQL file will block the whole stack until you fix it. Look at the `db` container logs for the offending line.
3. The second most common is a Python dependency installed locally but missing from `requirements.txt`. If your app works from a *clean* `docker compose up` locally, it will work in production.
4. The third: hard-coded paths or URLs that work locally but break under the production hostname. If something works locally and 404s in production, suspect a hard-coded `localhost` or `127.0.0.1` somewhere.
