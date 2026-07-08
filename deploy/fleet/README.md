# gabs-demos — fleet runbook

Operational source of truth for the VM that hosts every `*.platformengineer.io`
demo. If the box dies, this directory is how it comes back.

- **VM:** `gabs-demos` (GCP, project `central-beach-194106`, zone `us-central1-a`)
- **Public IP:** `34.136.162.94` (reserved; all DNS points here)
- **Ingress:** Caddy only (systemd), one `/etc/caddy/Caddyfile` — versioned at
  [`../caddy/Caddyfile`](../caddy/Caddyfile). Every app binds to `127.0.0.1`.

## What runs here

| Subdomain | Port (loopback) | Container(s) | Image source | Repo |
|---|---|---|---|---|
| platformengineer.io + www | 8088 | `platformengineer-io` | built on VM | this repo |
| langcache | 7860 | `langcache-demo` | built on VM | Redislabs-SA fork |
| messaging | 5000 | `messaging-ui` + `messaging-redis` | built on VM | `gacerioni/redis-messaging-streaming-demo` |
| auth | 8050 | `face-auth-backend` + `face-auth-redis` | Docker Hub | `gacerioni/redis-...biometrics` |
| celeb | 8070 / 3090 | `celeb-backend` + `celeb-frontend` + `celeb-redis` | Hub (backend) + VM (frontend) | `gacerioni/celebrity-face-match` |

## Security model (post-incident, 2026-07)

The previous box was compromised via a container bound to `0.0.0.0` on a shared
VPC. The rules that keep this one clean — do not weaken them:

1. **Every container binds to `127.0.0.1:PORT`.** Caddy is the only public listener.
2. **Firewall:** only 80/443 open to the world; SSH (`gabs-allow-ssh-me`) is locked
   to Gabriel's `/32`. Update that rule if his IP changes.
3. **Isolated VPC** (`gabs-vpc`), not the shared `default` network.
4. **CD is pull-based:** the VM pulls code/images; GitHub/CI never gets SSH into it.

## Day-to-day (from your laptop)

```bash
cd deploy/fleet
make ps                      # what's running
make caddy                   # edit ../caddy/Caddyfile, then push+validate+reload
make logs SVC=celeb-backend  # tail a container
make deploy-celeb            # roll out celeb (see CI/CD below)
make deploy-site             # roll out the site
```

## CI/CD

- **CI** (GitHub Actions, per app repo): a push to `main` builds the Docker image
  and pushes it to Docker Hub (`gacerioni/*`). First wired for celeb
  (`.github/workflows/docker-publish.yml` builds the backend). Add the same 15-line
  workflow to the other repos as they graduate.
  - Repo secrets required: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.
- **CD** (pull-based): `make deploy-<demo>` SSHes in, `git pull`s the app repo,
  `docker compose pull`s the CI-built image, and brings the stack up. Nothing
  outside the box initiates a deploy.
- One-time per demo: `make setup-celeb` turns `~/celeb` into a clone of its repo so
  future deploys are just a pull.

## Rebuild the whole box from scratch

```bash
# 1. Provision a hardened VM (own VPC, 80/443 + your-IP SSH, reattach the static IP)
bash deploy/provision.sh

# 2. Restore Caddy routing
make -C deploy/fleet caddy

# 3. Bring each demo up (per-repo compose + deploy notes)
make -C deploy/fleet setup-celeb deploy-celeb
#   ... langcache / messaging / auth: see each repo's deploy notes
```

> Next up: give langcache/messaging/auth the same `git clone` + compose + CI
> treatment as celeb, so `make deploy-<demo>` covers the whole fleet uniformly.
