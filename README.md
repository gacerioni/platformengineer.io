# platformengineer.io

My personal site: a portfolio and blog that runs on Redis. The demo catalog,
blog posts, view counters, and contact inbox all live in Redis as the system
of record, and a live latency chip in the nav proves it.

Live at https://platformengineer.io

## Stack

- FastAPI + Jinja templates, served by uvicorn, behind Caddy for TLS.
- Redis as the system of record (Redis Cloud in prod; an in-memory stand-in for local dev when `REDIS_URL` is unset).
- All keys namespaced under `peio:` so it can share a Redis database safely.
- Dark, neon-on-black UI. No build step, no framework.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --app-dir . --port 8080
```

Open http://127.0.0.1:8080 . With no `REDIS_URL` set it runs on an in-memory
store (not persisted). Set `REDIS_URL` to point at a real Redis.

## Configuration

Copy `.env.example` to `.env` and fill it in: Redis URL, admin credentials,
optional SMTP for contact email, and the deploy target. `.env` is gitignored.

## Content

- Demos are defined in `app/seed.py` (rebuilt into Redis on every boot).
- Blog posts are Markdown in `app/content/posts/*.md`, or written from `/admin`.
- `/admin` (HTTP basic auth) is the cockpit: write posts, read the contact inbox, watch view stats.

## Deploy

`deploy/deploy.sh` builds a container and ships it to a VM over gcloud; a Caddy
site block (`deploy/caddy-site.conf`) reverse-proxies the domain to it, with
automatic Let's Encrypt TLS. Details in `deploy/README.md`.
