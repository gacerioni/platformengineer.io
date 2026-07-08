#!/usr/bin/env bash
# Rebuild the demos host on a clean, hardened GCP VM.
# Own VPC (isolated from the shared 'default' network), only 80/443 + IAP SSH,
# reusing the existing static IP so DNS stays put. Idempotent / re-runnable.
# Config (PROJECT/ZONE/GCLOUD) comes from ../.env. Needs gcloud auth (owner/editor).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
[ -f .env ] && { set -a; . ./.env; set +a; }

PROJECT="${PROJECT:?set PROJECT in .env}"
ZONE="${ZONE:-us-central1-a}"
REGION="${REGION:-${ZONE%-*}}"
GCLOUD="${GCLOUD:-gcloud}"

NET="${NET:-gabs-vpc}"
SUBNET="${SUBNET:-gabs-subnet}"
VM="${VM:-gabs-demos}"
STATIC_IP="${STATIC_IP:-34.136.162.94}"   # gabs-demo-workshop-serasa-ip, where DNS points
OLD_VM="${OLD_VM:-gabs-iris-bank}"         # compromised + stopped; keep its disk for forensics
MACHINE="${MACHINE:-e2-standard-2}"

g(){ "$GCLOUD" --project "$PROJECT" "$@"; }
have(){ "$@" >/dev/null 2>&1; }

echo "==> VPC + subnet (isolated from the shared default network)"
have g compute networks describe "$NET" \
  || g compute networks create "$NET" --subnet-mode=custom
have g compute networks subnets describe "$SUBNET" --region "$REGION" \
  || g compute networks subnets create "$SUBNET" --network "$NET" --region "$REGION" --range 10.10.0.0/24

echo "==> firewall: internet only on 80/443, SSH only via IAP (35.235.240.0/20)"
have g compute firewall-rules describe gabs-allow-web \
  || g compute firewall-rules create gabs-allow-web --network "$NET" --direction INGRESS \
       --action ALLOW --rules tcp:80,tcp:443 --source-ranges 0.0.0.0/0 --target-tags gabs-demos
have g compute firewall-rules describe gabs-allow-iap-ssh \
  || g compute firewall-rules create gabs-allow-iap-ssh --network "$NET" --direction INGRESS \
       --action ALLOW --rules tcp:22 --source-ranges 35.235.240.0/20 --target-tags gabs-demos

echo "==> free the static IP from the old (stopped) VM, keeping its disk for forensics"
if have g compute instances describe "$OLD_VM" --zone "$ZONE"; then
  g compute instances delete-access-config "$OLD_VM" --zone "$ZONE" --access-config-name "External NAT" 2>/dev/null \
    || g compute instances delete-access-config "$OLD_VM" --zone "$ZONE" --access-config-name "external-nat" 2>/dev/null \
    || echo "   (nothing to detach, or already freed)"
fi

echo "==> create the hardened VM, reattaching the static IP"
have g compute instances describe "$VM" --zone "$ZONE" || g compute instances create "$VM" \
  --zone "$ZONE" --machine-type "$MACHINE" \
  --network "$NET" --subnet "$SUBNET" --address "$STATIC_IP" --tags gabs-demos \
  --image-family debian-12 --image-project debian-cloud \
  --boot-disk-size 40GB --boot-disk-type pd-balanced \
  --metadata=startup-script='#!/bin/bash
set -e
command -v docker >/dev/null || (curl -fsSL https://get.docker.com | sh)
systemctl enable --now docker
if ! command -v caddy >/dev/null; then
  apt-get update -y
  apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt | tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -y && apt-get install -y caddy
fi'

echo
echo "==> done. VM=$VM  IP=$STATIC_IP  net=$NET  (only 80/443 + IAP SSH; Docker+Caddy install on first boot)"
echo "    then deploy the site with:  INSTANCE=$VM TUNNEL=1 bash deploy/deploy.sh"
