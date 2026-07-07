from pathlib import Path
from typing import List, Tuple

from .models import Demo, Event, Lesson, Post

CONTENT = Path(__file__).resolve().parent / "content"


def seed_demos() -> List[Demo]:
    return [
        Demo(
            slug="gabs-bank",
            title="Gabs Bank",
            tagline="Agentic AI banking assistant on Redis.",
            description=(
                "Gabs Bank is a conversational banking assistant built on my IRIS agent "
                "stack, with Redis powering retrieval, guardrails, and a real-time feature "
                "store.\n\n"
                "Ask it in plain language (move money, check balances, get advice) and it "
                "acts, not just chats: it reads live account state and scores in the moment, "
                "behind a confirmation gate.\n\n"
                "A fictional bank, real agent engineering. The live, English demo of the "
                "platform I run for the largest banks in Latin America."
            ),
            tags=["ai-agents", "rag", "guardrails", "llm"],
            links={"live": "https://gabsbank.platformengineer.io"},
            status="live",
            icon="robot",
            featured=True,
            protected=True,
            order=5,
        ),
        Demo(
            slug="celeb-face-match",
            title="Celebrity Face Match",
            tagline="Find your celebrity lookalike.",
            description=(
                "Upload a photo and Redis vector search finds your closest celebrity match "
                "over face embeddings, in milliseconds.\n\n"
                "A visual way to show vector similarity: embeddings live in Redis and KNN runs "
                "at query time, no separate vector database in the stack.\n\n"
                "Full-stack demo running on the bastion."
            ),
            tags=["vector", "vision", "search"],
            links={"live": "https://celeb.platformengineer.io/"},
            status="live",
            icon="face-id",
            featured=True,
            order=10,
        ),
        Demo(
            slug="gaming-search",
            title="Gaming Search",
            tagline="Hybrid search over a game catalog.",
            description=(
                "Search a game catalog by meaning and by keyword at once: full-text, vector "
                "similarity, and filters combined in a single Redis query.\n\n"
                "Shows how one engine covers what usually takes a search cluster plus a "
                "separate vector database, with results ranked as you type."
            ),
            tags=["vector", "search", "gaming"],
            links={"live": "https://cactus-demo.pages.dev/"},
            status="live",
            icon="device-gamepad-2",
            featured=True,
            order=20,
        ),
        Demo(
            slug="langcache",
            title="LangCache",
            tagline="Semantic cache for LLM apps.",
            description=(
                "Cut LLM latency and token spend by serving cached answers to semantically "
                "similar prompts, powered by Redis.\n\n"
                "A near-hit on a previous question returns instantly instead of calling the "
                "model again. Drop-in in front of any LLM app."
            ),
            tags=["llm", "semantic-cache", "redis"],
            links={"live": "https://langcache.platformengineer.io/"},
            status="live",
            icon="bolt",
            featured=True,
            order=30,
        ),
        Demo(
            slug="messaging",
            title="Redis Messaging",
            tagline="Queues, stacks, pub/sub, and streams.",
            description=(
                "One demo, every messaging shape on Redis: queues and stacks with lists, "
                "fan-out with pub/sub, and durable event logs with streams.\n\n"
                "A hands-on tour of how Redis covers the messaging patterns people usually "
                "reach for a broker to get, without the extra moving parts."
            ),
            tags=["messaging", "streams", "pub-sub", "queues"],
            links={"live": "https://messaging.platformengineer.io/"},
            status="live",
            icon="messages",
            order=40,
        ),
        Demo(
            slug="auth",
            title="Face Auth",
            tagline="Log in with your face, Redis as the vector DB.",
            description=(
                "Biometric login powered by facial recognition, with Redis as the vector "
                "database.\n\n"
                "Your face becomes an embedding and Redis vector search matches it against "
                "enrolled users in milliseconds to authenticate, no password.\n\n"
                "Redis doing double duty: the vector store and the fast path for auth."
            ),
            tags=["vector", "biometrics", "auth"],
            links={"live": "https://auth.platformengineer.io/"},
            status="live",
            icon="scan-eye",
            order=50,
        ),
        Demo(
            slug="iris",
            title="IRIS",
            tagline="Agentic AI assistants for banks.",
            description=(
                "IRIS is a platform of agentic AI assistants I built for the largest banks in "
                "Latin America.\n\n"
                "Each assistant pairs a retrieval layer and hard guardrails with a real-time "
                "feature store on Redis, so it does more than chat: it reads live account "
                "state, scores risk, and takes actions like moving money, behind a "
                "confirmation gate that prevents double-apply.\n\n"
                "The interesting engineering is in the boring parts: reproducible resets, "
                "byte-identical guardrail starters, and a Redis topology where the feature "
                "store is recomputed on write."
            ),
            tags=["ai-agents", "rag", "guardrails", "feature-store"],
            status="in production",
            icon="robot",
            order=60,
        ),
        Demo(
            slug="token-control-plane",
            title="Token Control Plane",
            tagline="Redis as an LLM rate limiter and control plane.",
            description=(
                "A standalone gateway that puts Redis in front of your LLMs as a rate limiter "
                "and control plane.\n\n"
                "Every request runs a short gauntlet: a router picks the model, a semantic "
                "cache short-circuits repeats, a token bucket enforces per-model and "
                "per-tenant budgets, and only survivors reach the model. Each stage is a "
                "microsecond Redis lookup.\n\n"
                "Turns a runaway token bill into something you can see, shape, and cap from "
                "one place."
            ),
            tags=["ai-infra", "rate-limiting", "llm"],
            status="validated e2e",
            icon="gauge",
            order=70,
        ),
        Demo(
            slug="rdi-fraud-feature-store",
            title="RDI Fraud Feature Store",
            tagline="Snowflake to Redis in real time, for fraud.",
            description=(
                "Real-time fraud features served from Redis, fed by streaming change data "
                "capture from Snowflake through Redis Data Integration.\n\n"
                "The warehouse stays the source of record; RDI keeps the online features fresh "
                "without a nightly job, so a fraud model reads sub-millisecond features on the "
                "hot path."
            ),
            tags=["feature-store", "rdi", "fraud", "cdc"],
            status="demo",
            icon="shield-check",
            order=80,
        ),
        Demo(
            slug="redis-cloud-autoscaler",
            title="Redis Cloud Autoscaler",
            tagline="Scale on demand, not on a guess.",
            description=(
                "A proof of concept that scales a Redis Cloud database on live demand instead "
                "of a fixed guess.\n\n"
                "Under a memtier load generator, an alert-driven loop scaled a database from "
                "one thousand to five thousand operations per second and back, end to end."
            ),
            tags=["infra", "autoscaling", "poc"],
            status="validated e2e",
            icon="trending-up",
            order=90,
        ),
        Demo(
            slug="valkey-vs-redis-cloud",
            title="Valkey vs Redis Cloud",
            tagline="A 7.1M ops/sec benchmark on AWS.",
            description=(
                "A head-to-head throughput benchmark between Valkey and Redis Cloud, run with "
                "memtier on AWS.\n\n"
                "The headline number, over seven million operations per second, is nominal "
                "capacity; the more useful part is separating that from the real demand a "
                "workload puts on the system. Reproducible from a versioned script."
            ),
            tags=["benchmark", "memtier", "performance"],
            status="benchmark",
            icon="chart-bar",
            order=100,
        ),
    ]


def seed_events() -> List[Event]:
    return []


def seed_lessons() -> List[Lesson]:
    modules = [
        ("context-surfaces", "Context surfaces",
         "Give the agent exactly the right data at the right moment, served from Redis."),
        ("agent-memory", "Agent memory",
         "Short and long-term memory, so the agent remembers who it is talking to and what happened."),
        ("semantic-guardrails", "Semantic guardrails",
         "Block off-topic or unsafe turns by meaning, not by brittle keyword lists."),
        ("semantic-router", "Semantic router",
         "Send each request to the right tool or flow based on intent."),
        ("rag", "RAG",
         "Ground answers in your own data with retrieval-augmented generation."),
        ("semantic-cache", "Semantic cache",
         "Skip the model when a semantically similar question was already answered."),
    ]
    return [Lesson(slug=s, title=t, summary=d, order=(i + 1) * 10) for i, (s, t, d) in enumerate(modules)]


def _parse_frontmatter(text: str) -> Tuple[dict, str]:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            meta = {}
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    meta[key.strip()] = val.strip()
            return meta, parts[2].lstrip("\n")
    return {}, text


def load_posts() -> List[Post]:
    posts: List[Post] = []
    d = CONTENT / "posts"
    if not d.exists():
        return posts
    for f in sorted(d.glob("*.md")):
        meta, body = _parse_frontmatter(f.read_text(encoding="utf-8"))
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        posts.append(
            Post(
                slug=meta.get("slug", f.stem),
                title=meta.get("title", f.stem),
                summary=meta.get("summary", ""),
                body_md=body,
                tags=tags,
                published_at=meta.get("published_at", ""),
                reading_minutes=int(meta.get("reading_minutes", "5") or 5),
                draft=str(meta.get("draft", "false")).lower() == "true",
            )
        )
    return posts
