# Fleet ops for the gabs-demos VM.
# Runs from your laptop and drives the box over `gcloud compute ssh`.
# GitHub never touches the VM (pull-based CD): the box pulls code/images itself.
# Target config (ZONE/INSTANCE/PROJECT/GCLOUD) is read from the repo .env.
#
#   make ps                        # what is running
#   make caddy                     # push+validate+reload the versioned Caddyfile
#   make logs SVC=celeb-backend    # tail a container
#   make setup-celeb               # one-time: clone the celeb repo onto the box
#   make deploy-celeb              # pull-based deploy of celeb
#   make deploy-site               # pull-based deploy of the site

ROOT := $(abspath $(CURDIR)/../..)
ENV  := set -a; . "$(ROOT)/.env"; set +a
GC    = "$${GCLOUD:-gcloud}" compute ssh "$${INSTANCE:-gabs-demos}" --zone "$${ZONE:-us-central1-a}" --project "$$PROJECT" --command

.PHONY: help ps caddy logs setup-celeb deploy-celeb deploy-site

help:
	@echo "make ps | caddy | logs SVC=<name> | setup-celeb | deploy-celeb | deploy-site"

ps:
	@$(ENV); $(GC) 'sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

caddy:
	@bash "$(ROOT)/deploy/caddy/sync.sh"

logs:
	@$(ENV); $(GC) 'sudo docker logs --tail 100 --timestamps $(SVC)'

# One-time: make ~/celeb a clone of the app repo so deploys are a git pull.
setup-celeb:
	@$(ENV); $(GC) 'if [ ! -d ~/celeb/.git ]; then mv ~/celeb ~/celeb.bak.$$(date +%s) 2>/dev/null || true; git clone https://github.com/gacerioni/celebrity-face-match.git ~/celeb && echo "cloned to ~/celeb"; else echo "~/celeb already a git repo"; fi'

# Pull-based: git pull the app repo, pull the CI-built backend image, rebuild
# the (domain-specific) frontend, and bring the stack up.
deploy-celeb:
	@$(ENV); $(GC) 'set -e; test -d ~/celeb/.git || { echo "run: make setup-celeb"; exit 1; }; cd ~/celeb && git pull --ff-only && sudo docker compose -f deploy_peio/docker-compose.celeb.yml pull; sudo docker compose -f deploy_peio/docker-compose.celeb.yml up -d --build && sudo docker compose -f deploy_peio/docker-compose.celeb.yml ps'

deploy-site:
	@$(ENV); $(GC) 'set -e; cd ~/platformengineer.io && (git pull --ff-only 2>/dev/null || true) && sudo docker compose up -d --build && sudo docker compose ps'
