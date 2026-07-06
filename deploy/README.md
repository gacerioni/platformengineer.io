# Deploy platformengineer.io

The app is one container that reads Redis from `.env` (`REDIS_URL`, `REDIS_PREFIX=peio:`).
It listens on container port 8080, published on the bastion at `127.0.0.1:8088` (loopback only),
so the reverse proxy already on the box terminates TLS and forwards to it. Nothing new binds 80/443.

## 0. Prereqs on the bastion (gabs-iris-bank)
- docker + docker compose
- ports 80/443 open in the GCP firewall (already the case if other demos serve HTTP)

## 1. Deploy the app
From the project root, on your laptop (gcloud authenticated):

```bash
bash deploy/deploy.sh
```

Copies the source + `.env` to `~/platformengineer.io` on the box, builds, and starts it.
Verify on the box: `curl -s localhost:8088/healthz` should show `"backend":"redis-cloud"`.

## 2. DNS
Add an A record: `platformengineer.io` -> the box's public IP.
Get the IP:

```bash
gcloud compute instances describe gabs-iris-bank --zone us-central1-a \
  --project central-beach-194106 \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

## 3. TLS + domain (two cases)

### A. A Caddy already runs on the box (likely, IRIS uses one)
Add `deploy/caddy-site.conf` to that Caddy (import in the main Caddyfile or drop in its sites dir),
then reload Caddy. It fetches a Let's Encrypt cert automatically once DNS resolves.

### B. No reverse proxy on the box yet
Run a standalone Caddy next to the app. Add this to `docker-compose.yml` and switch the app to the
compose network (`reverse_proxy app:8080` in the Caddyfile instead of `127.0.0.1:8088`):

```yaml
  caddy:
    image: caddy:2
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - ./deploy/caddy-site.conf:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
volumes:
  caddy_data:
  caddy_config:
```

## Notes
- `.env` holds the Redis credential. It is gitignored and not baked into the image (`.dockerignore`);
  `deploy.sh` copies it to the box and compose reads it via `env_file`.
- `/healthz` currently exposes dbsize + peio key count (dev diagnostic). Gate or remove before public.
