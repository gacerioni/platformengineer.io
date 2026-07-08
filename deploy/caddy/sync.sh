#!/usr/bin/env bash
# Push the versioned fleet Caddyfile to gabs-demos: back up, validate, reload.
# Caddy config is git-managed here — edit deploy/caddy/Caddyfile, never on the box.
# Config (ZONE/INSTANCE/PROJECT/GCLOUD) comes from the repo .env (gitignored).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
[ -f "$ROOT/.env" ] && { set -a; . "$ROOT/.env"; set +a; }

ZONE="${ZONE:-us-central1-a}"
INSTANCE="${INSTANCE:-gabs-demos}"
GCLOUD="${GCLOUD:-gcloud}"
: "${PROJECT:?set PROJECT in .env}"
LOCAL="$ROOT/deploy/caddy/Caddyfile"

echo "==> uploading Caddyfile to $INSTANCE"
"$GCLOUD" compute scp "$LOCAL" "$INSTANCE:/tmp/Caddyfile.new" --zone "$ZONE" --project "$PROJECT"

echo "==> validate NEW file, then backup + install + reload on the box"
"$GCLOUD" compute ssh "$INSTANCE" --zone "$ZONE" --project "$PROJECT" --command '
set -e
sudo caddy validate --config /tmp/Caddyfile.new --adapter caddyfile
sudo cp /etc/caddy/Caddyfile "/etc/caddy/Caddyfile.bak.$(date +%Y%m%d-%H%M%S)"
sudo cp /tmp/Caddyfile.new /etc/caddy/Caddyfile
sudo systemctl reload caddy && echo "caddy reloaded OK"
'
echo "==> done."
