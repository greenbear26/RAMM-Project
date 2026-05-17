# Deploying Team Projects to Coolify

Staff-facing checklist for deploying each student team's fork to the course Coolify server.

- **Coolify dashboard:** [coolify.cs4535.cloud](https://coolify.cs4535.cloud)
- **Team app domain:** `team{N}.neu-in-leuven.cloud`
- **Team API domain (optional):** `team{N}-api.neu-in-leuven.cloud`

The deploy model is **pure Coolify with no GitHub Actions**: Coolify watches each team's GitHub fork via a webhook and redeploys on every push to `main`. The repo ships a dedicated `docker-compose.prod.yaml` that Coolify uses to build and run the stack.

By default only the Streamlit `app` service is exposed publicly. The Flask `api` and MySQL `db` services are reachable only on the internal Docker network (the Streamlit app talks to the API via `http://web-api:4000`). Expose the API publicly only if a team needs external `curl`/Postman access — most teams don't.

---

## One-time setup (do once per course/semester)

### 1. DNS

Two viable approaches, depending on how the Coolify server is run:

**Wildcard A record (recommended for single-node Coolify).** One record covers every team:

```
A    *.neu-in-leuven.cloud    →    <coolify-droplet-ip>
```

No DNS work per team afterwards — just pick a hostname and Coolify handles the rest. Works as long as every team's containers live on **one** Coolify host.

**Per-team A records (required if teams are spread across multiple nodes).** Skip the wildcard. Each team gets a specific A record pointing at whichever node hosts them. One extra DNS click during onboarding; needed because a wildcard can resolve to only one IP.

The Coolify server's own record at `coolify.cs4535.cloud` is unchanged either way — only deployed team apps live under `neu-in-leuven.cloud`.

Verify with `dig team1.neu-in-leuven.cloud +short` — it should return the right droplet's IP before you try to deploy.

### 2. Server sizing

Approximate per-team idle footprint: Streamlit ~250 MB, Flask ~150 MB, MySQL ~500 MB → **~1 GB RAM idle**, modest CPU. For a class of ~7 teams expect:

- **8 vCPU / 16 GB RAM minimum** with comfortable headroom for normal use, demos, and parallel builds (Coolify rebuilds images on every push, which is CPU-heavy).
- **8 vCPU / 32 GB RAM** if budget allows — no tuning, no surprises during demo days.
- **120–160 GB SSD** to cover Docker images + build cache across teams (MySQL data is in tmpfs / RAM, not on disk).

DigitalOcean/Hetzner droplets can be vertically resized; bumping the existing droplet is simpler than splitting across nodes.

### 3. Coolify ↔ GitHub integration

Install the Coolify GitHub App on the course GitHub org (or on each team's fork individually) so Coolify can clone student repos and auto-register webhooks.

- In Coolify: **Sources → New → GitHub App**.
- Follow the prompts to install on the org that hosts team forks.
- Once installed, Coolify can list and select team repos in the per-team setup below.

A Personal Access Token works as a fallback if the GitHub App route is blocked.

---

## Per-team onboarding (~5 min per team)

Repeat for each team. Use `team1`, `team2`, etc. as the subdomain prefix.

### Step 1 — Create the resource in Coolify

1. Open `coolify.cs4535.cloud` → select the course project (or create one) → **+ New Resource**.
2. Choose **Public Repository** (or **Private Repository** if using the GitHub App).
3. Paste the team's fork URL (e.g. `https://github.com/<org>/team1-doc-project`).
4. **Branch:** `main`.
5. **Build Pack:** **Docker Compose**.
6. **Docker Compose Location:** `docker-compose.prod.yaml`.

### Step 2 — Configure domains

In the resource's **Configuration → Network / Domains** panel, set per-service domains:

| Service | Domain                                      | Port | Required? |
| ------- | ------------------------------------------- | ---- | --------- |
| `app`   | `https://team{N}.neu-in-leuven.cloud`         | 8501 | yes       |
| `api`   | `https://team{N}-api.neu-in-leuven.cloud`     | 4000 | optional  |
| `db`    | —                                           | —    | never     |

Coolify auto-provisions Let's Encrypt certificates for each domain on first hit.

> **If the deployed URL returns 404 with no HTTPS:** Coolify's Traefik doesn't know which container port to route to. In some Coolify versions you need to include the container port directly in the domain field, e.g. `https://team{N}.neu-in-leuven.cloud:8501` (the `:8501` is the *container* port; the public port stays 443). Confirm the domain is attached to the correct service (`app`), not the resource as a whole or another service.

### Step 3 — Set environment variables

In **Environment Variables**, add the following. Generate fresh values per team — do not reuse across teams.

| Variable              | Value                                                      |
| --------------------- | ---------------------------------------------------------- |
| `SECRET_KEY`          | `openssl rand -hex 32` output (run locally, paste here)    |
| `MYSQL_ROOT_PASSWORD` | `openssl rand -hex 24` output                              |
| `DB_USER`             | `root`                                                     |
| `DB_NAME`             | `ngo_db` (or the team's chosen database name)              |

Note: `DB_HOST`, `DB_PORT`, and service hostnames are hardcoded in `docker-compose.prod.yaml`; nothing else to set.

### Step 4 — Enable auto-deploy and deploy

1. Find the auto-deploy setting (labelled something like **Auto Deploy** or **Automatic Deployment**; exact location varies by Coolify version — usually on the resource's main config tab or a "Webhooks" tab) and turn it on. Coolify registers a webhook on the team's fork.
2. Click **Deploy**.

First deploy takes ~3–5 minutes (image build + MySQL init from `database-files/*.sql`). Subsequent deploys are faster (Docker layer cache).

> **Note on the database:** the prod stack runs MySQL with a **tmpfs (RAM-backed) data dir**, deliberately overriding the `mysql:9` image's default volume. Every redeploy starts the `db` container fresh and re-runs all `database-files/*.sql` scripts. This means the SQL committed in the team's repo is always the source of truth — there is no production state that can drift from the repo. Teams can iterate on schema by editing the SQL and pushing; no staff volume-wipe is needed.
>
> Implication: any data inserted through the running app (e.g. via the Streamlit "Add NGO" page) disappears on the next push. To make data "permanent," teams must add it to `database-files/*.sql`.

---

## Verification checklist

After the first deploy completes:

- [ ] `https://team{N}.neu-in-leuven.cloud` loads the Streamlit Home page.
- [ ] Browser shows a valid Let's Encrypt cert (lock icon, no warning).
- [ ] Streamlit pages that hit the API (e.g. **NGO Directory**, **API Test**) load data without errors. (This proves app ↔ api ↔ db all work over the internal network.)
- [ ] In Coolify's **Logs** view for the `db` container, the lines `Initializing database files`, `running /docker-entrypoint-initdb.d/ngo_db.sql`, and `MySQL init process done` are all present. If init didn't run, the database will appear empty in the UI.
- [ ] If you exposed the API publicly: `curl https://team{N}-api.neu-in-leuven.cloud/data` returns JSON.
- [ ] Push a trivial commit to the team's `main` — Coolify should rebuild and redeploy within ~1–3 min.

---

## End-of-semester teardown

For each team in Coolify:

1. **Resource → Settings → Stop** to stop containers.
2. **Resource → Settings → Delete** to remove the project and reclaim the disk volume.

Optionally archive each team's GitHub fork separately.

---

## Troubleshooting

- **404 / "page not found" on the deployed URL, no HTTPS:** Traefik is up but can't route to the app. Most common cause: the domain isn't bound to the `app` service at port 8501. Edit the domain field for the `app` service to `https://team{N}.neu-in-leuven.cloud:8501` (the `:8501` is the container port). See Step 2 above.
- **MySQL init didn't run / database appears empty:** check the `db` container logs for the line `running /docker-entrypoint-initdb.d/ngo_db.sql`. If absent, init didn't execute — almost always because something is mounting a volume at `/var/lib/mysql` that already has data (defeating the tmpfs). The compose ships with the right config; if you've edited it, check the `tmpfs` declaration on the `db` service.
- **MySQL init errors:** check the `db` container logs for SQL syntax errors in the seed files. Fix in the repo and push; the next deploy reseeds automatically (no manual volume cleanup).
- **Streamlit can't reach the API:** confirm the `api` service is healthy in Coolify logs. Streamlit pages call `http://web-api:4000` internally — that hostname is set via the `hostname: web-api` line in `docker-compose.prod.yaml`. If logs show DNS errors for `web-api`, that line was modified.
- **Cert provisioning fails:** confirm the team's domain resolves (`dig team{N}.neu-in-leuven.cloud`) before retrying. Let's Encrypt rate-limits failed validations (5/hour/hostname) and overall issuance (50/week per registered domain) — see notes below.
- **Auto-deploy isn't triggering:** check the GitHub repo's **Settings → Webhooks** for the Coolify webhook and recent delivery status. Either reinstall the Coolify GitHub App on the repo or toggle Auto Deploy off and back on to re-register the webhook.

### Let's Encrypt rate limits — won't bite under normal use

Once a hostname has a cert, it's reused for ~90 days (auto-renewed by Traefik). Redeploys don't issue new certs. The 50-issuances-per-week limit only matters when **onboarding** new hostname pairs (app + api ≈ 2 per team). You can comfortably onboard ~25 teams per week. Teams hammering the deploy button after onboarding doesn't count.
