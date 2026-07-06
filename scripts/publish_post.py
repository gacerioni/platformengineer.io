#!/usr/bin/env python3
"""Push a markdown post file into Redis as the system of record.

Usage: python scripts/publish_post.py app/content/posts/my-post.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import Post  # noqa: E402
from app.seed import _parse_frontmatter  # noqa: E402
from app.store import Store  # noqa: E402


def main(path: str):
    text = Path(path).read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    p = Post(
        slug=meta.get("slug", Path(path).stem),
        title=meta.get("title", Path(path).stem),
        summary=meta.get("summary", ""),
        body_md=body,
        tags=tags,
        published_at=meta.get("published_at", ""),
        reading_minutes=int(meta.get("reading_minutes", "5") or 5),
        draft=str(meta.get("draft", "false")).lower() == "true",
    )
    Store().upsert_post(p)
    print(f"published {p.slug} ({'draft' if p.draft else 'live'})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: publish_post.py <path-to-md>")
        sys.exit(1)
    main(sys.argv[1])
