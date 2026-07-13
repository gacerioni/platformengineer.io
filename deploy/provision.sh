#!/usr/bin/env bash
# Rebuild the demos host on a clean, hardened GCP VM.
# Own VPC (isolated from the shared 'default' network), only 80/443 + your-IP SSH.
# Reserves a LABELED static IP + LABELS the VM so the GCP janitor won't reap them
# (it deletes resources missing owner=/skip_deletion= — that is what nuked the box).
# Idempotent / re-runnable. Config (PROJECT/ZONE/GCLOUD/SSH_CIDR) from ../.env.
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
ADDR="${ADDR:-gabs-demos-ip}"
SSH_CIDR="${SSH_CIDR:-189.46.30.176/32}"   # your laptop's egress IP; update when it changes
MACHINE="${MACHINE:-e2-standard-2}"
# The GCP janitor deletes untagged VMs. THESE LABELS ARE WHAT KEEP THE BOX ALIVE.
LABELS="owner=gabriel_cerioni,skip_deletion=yes"

g(){ "$GCLOUD" --project "$PROJECT" "$@"; }
have(){ "$@" >/dev/null 2>&1; }

echo "==> static IP (labeled so the janitor skips it)"
have g compute addresses describe "$ADDR" --region "$REGION" \
  || g compute addresses create "$ADDR" --region "$REGION"
g compute addresses update "$ADDR" --region "$REGION" --update-labels "$LABELS" >/dev/null 2>&1 || true
STATIC_IP=$(g compute addresses describe "$ADDR" --region "$REGION" --format="value(address)")
echo "    IP=$STATIC_IP"

echo "==> VPC + subnet (isolated from the shared default network)"
have g compute networks describe "$NET" \
  || g compute networks create "$NET" --subnet-mode=custom
have g compute networks subnets describe "$SUBNET" --region "$REGION" \
  || g compute networks subnets create "$SUBNET" --network "$NET" --region "$REGION" --range 10.10.0.0/24

echo "==> firewall: internet on 80/443, SSH only from your IP ($SSH_CIDR)"
have g compute firewall-rules describe gabs-allow-web \
  || g compute firewall-rules create gabs-allow-web --network "$NET" --direction INGRESS \
       --action ALLOW --rules tcp:80,tcp:443 --source-ranges 0.0.0.0/0 --target-tags gabs-demos
have g compute firewall-rules describe gabs-allow-ssh-me \
  || g compute firewall-rules create gabs-allow-ssh-me --network "$NET" --direction INGRESS \
       --action ALLOW --rules tcp:22 --source-ranges "$SSH_CIDR" --target-tags gabs-demos
g compute firewall-rules update gabs-allow-ssh-me --source-ranges "$SSH_CIDR" >/dev/null 2>&1 || true

echo "==> create the hardened, LABELED VM with the static IP"
have g compute instances describe "$VM" --zone "$ZONE" || g compute instances create "$VM" \
  --zone "$ZONE" --machine-type "$MACHINE" \
  --network "$NET" --subnet "$SUBNET" --address "$STATIC_IP" --tags gabs-demos \
  --labels "$LABELS" \
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
echo "==> done. VM=$VM  IP=$STATIC_IP  net=$NET  labels=[$LABELS]"
echo "    (only 80/443 + SSH from $SSH_CIDR; Docker+Caddy install on first boot)"
