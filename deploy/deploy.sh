#!/usr/bin/env bash
# Reproducible deploy of platformengineer.io to a bastion VM over gcloud.
# Config comes from .env (gitignored): copy .env.example to .env and fill it in.
# Needs gcloud auth locally, and docker + docker compose on the bastion.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && { set -a; . ./.env; set +a; }

ZONE="${ZONE:-us-central1-a}"
REMOTE_DIR="${REMOTE_DIR:-platformengineer.io}"
GCLOUD="${GCLOUD:-gcloud}"
: "${INSTANCE:?set INSTANCE in .env (the bastion VM name)}"
: "${PROJECT:?set PROJECT in .env (the GCP project id)}"

ssh_box() { "$GCLOUD" compute ssh --zone "$ZONE" "$INSTANCE" --project "$PROJECT" --command "$1"; }

echo "==> ensuring remote dir ~/$REMOTE_DIR on $INSTANCE"
ssh_box "mkdir -p ~/$REMOTE_DIR"

echo "==> copying source (+ .env)"
"$GCLOUD" compute scp --recurse --zone "$ZONE" --project "$PROJECT" \
  Dockerfile docker-compose.yml requirements.txt .dockerignore app .env \
  "$INSTANCE:~/$REMOTE_DIR/"

echo "==> build + start (docker needs sudo on this box)"
ssh_box "cd ~/$REMOTE_DIR && sudo docker compose up -d --build && sudo docker compose ps"

echo "==> health check"
ssh_box "sleep 2 && curl -s localhost:8088/healthz && echo"

echo
echo "App runs on the box at 127.0.0.1:8088. Wire the domain via deploy/caddy-site.conf."
