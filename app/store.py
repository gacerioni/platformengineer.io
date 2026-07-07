import json
import os
import time
from typing import List, Optional

from . import seed as seedmod
from .models import Demo, Event, Lesson, Post

PREFIX = os.getenv("REDIS_PREFIX", "peio:")


def _k(*parts) -> str:
    return PREFIX + ":".join(parts)


def _date_score(d: str) -> int:
    try:
        return int(str(d).replace("-", ""))
    except Exception:
        return 0


def _zslice(members, start, end):
    n = len(members)
    if end < 0:
        end = n + end
    return members[start : end + 1]


class MiniRedis:
    """In-memory stand-in for Redis, used for local dev/preview only. Not persisted.

    Implements just the handful of commands this app uses. Set REDIS_URL to run
    against a real Redis (Redis Cloud) instead.
    """

    def __init__(self):
        self._kv = {}
        self._z = {}
        self._sets = {}
        self._streams = {}
        self._seq = 0

    def ping(self):
        return True

    def set(self, k, v):
        self._kv[k] = v
        return True

    def get(self, k):
        return self._kv.get(k)

    def exists(self, k):
        return 1 if (k in self._kv or k in self._z or k in self._sets or k in self._streams) else 0

    def incr(self, k):
        self._kv[k] = str(int(self._kv.get(k, "0")) + 1)
        return int(self._kv[k])

    def zadd(self, k, mapping):
        self._z.setdefault(k, {}).update(mapping)
        return len(mapping)

    def zrange(self, k, start, end):
        members = [m for m, _ in sorted(self._z.get(k, {}).items(), key=lambda x: x[1])]
        return _zslice(members, start, end)

    def zrevrange(self, k, start, end):
        members = [m for m, _ in sorted(self._z.get(k, {}).items(), key=lambda x: x[1], reverse=True)]
        return _zslice(members, start, end)

    def sadd(self, k, *vals):
        self._sets.setdefault(k, set()).update(vals)
        return len(vals)

    def delete(self, *keys):
        n = 0
        for k in keys:
            for bucket in (self._kv, self._z, self._sets, self._streams):
                if k in bucket:
                    del bucket[k]
                    n += 1
        return n

    def xadd(self, k, fields):
        self._seq += 1
        sid = f"0-{self._seq}"
        self._streams.setdefault(k, []).append((sid, dict(fields)))
        return sid

    def xrange(self, k, start="-", end="+", count=None):
        return list(self._streams.get(k, []))


def _connect():
    url = os.getenv("REDIS_URL") or os.getenv("REDIS_URI")
    if url:
        import redis

        return (
            redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            ),
            "redis-cloud",
        )
    return MiniRedis(), "dev-memory"


def _region() -> str:
    import re
    from urllib.parse import urlparse

    url = os.getenv("REDIS_URL") or os.getenv("REDIS_URI") or ""
    host = urlparse(url).hostname or ""
    m = re.search(r"([a-z]{2}-[a-z]+-\d+)", host)
    return m.group(1) if m else ""


class Store:
    def __init__(self):
        self.r, self.backend = _connect()
        self.region = _region()

    def ping_ms(self) -> float:
        start = time.perf_counter()
        try:
            self.r.ping()
        except Exception:
            return -1.0
        return round((time.perf_counter() - start) * 1000, 2)

    # demos
    def upsert_demo(self, d: Demo):
        self.r.set(_k("demo", d.slug), json.dumps(d.to_dict()))
        self.r.zadd(_k("demos", "index"), {d.slug: d.order})

    def sync_demos(self):
        # Demos are static content: rebuild from seed on every boot so deploys apply.
        for s in self.r.zrange(_k("demos", "index"), 0, -1):
            self.r.delete(_k("demo", s))
        self.r.delete(_k("demos", "index"))
        try:
            for k in self.r.scan_iter(match=_k("demos", "tag", "*")):
                self.r.delete(k)
        except Exception:
            pass
        for d in seedmod.seed_demos():
            self.upsert_demo(d)

    # lessons (the Learn series)
    def upsert_lesson(self, lesson: Lesson):
        self.r.set(_k("lesson", lesson.slug), json.dumps(lesson.to_dict()))
        self.r.zadd(_k("lessons", "index"), {lesson.slug: lesson.order})

    def list_lessons(self):
        out = []
        for s in self.r.zrange(_k("lessons", "index"), 0, -1):
            raw = self.r.get(_k("lesson", s))
            if raw:
                out.append(Lesson.from_dict(json.loads(raw)))
        return out

    def sync_lessons(self):
        for s in self.r.zrange(_k("lessons", "index"), 0, -1):
            self.r.delete(_k("lesson", s))
        self.r.delete(_k("lessons", "index"))
        for lesson in seedmod.seed_lessons():
            self.upsert_lesson(lesson)

    def get_demo(self, slug: str) -> Optional[Demo]:
        raw = self.r.get(_k("demo", slug))
        return Demo.from_dict(json.loads(raw)) if raw else None

    def list_demos(self, tag: Optional[str] = None) -> List[Demo]:
        out = []
        for s in self.r.zrange(_k("demos", "index"), 0, -1):
            d = self.get_demo(s)
            if d and (tag is None or tag in d.tags):
                out.append(d)
        return out

    def featured_demos(self) -> List[Demo]:
        return [d for d in self.list_demos() if d.featured]

    def all_tags(self) -> List[str]:
        tags = set()
        for d in self.list_demos():
            tags.update(d.tags)
        return sorted(tags)

    # posts
    def upsert_post(self, p: Post):
        self.r.set(_k("post", p.slug), json.dumps(p.to_dict()))
        self.r.zadd(_k("posts", "index"), {p.slug: _date_score(p.published_at)})

    def get_post(self, slug: str) -> Optional[Post]:
        raw = self.r.get(_k("post", slug))
        return Post.from_dict(json.loads(raw)) if raw else None

    def list_posts(self, include_drafts: bool = False) -> List[Post]:
        out = []
        for s in self.r.zrevrange(_k("posts", "index"), 0, -1):
            p = self.get_post(s)
            if p and (include_drafts or not p.draft):
                out.append(p)
        return out

    # events
    def upsert_event(self, e: Event):
        self.r.set(_k("event", e.slug), json.dumps(e.to_dict()))
        self.r.zadd(_k("events", "index"), {e.slug: _date_score(e.date)})

    def list_events(self) -> List[Event]:
        out = []
        for s in self.r.zrevrange(_k("events", "index"), 0, -1):
            raw = self.r.get(_k("event", s))
            if raw:
                out.append(Event.from_dict(json.loads(raw)))
        return out

    # views
    def incr_views(self, kind: str, slug: str) -> int:
        return int(self.r.incr(_k("views", kind, slug)))

    def get_views(self, kind: str, slug: str) -> int:
        v = self.r.get(_k("views", kind, slug))
        return int(v) if v else 0

    def incr_site_view(self) -> int:
        return int(self.r.incr(_k("views", "site")))

    # contact
    def add_contact(self, name: str, email: str, message: str) -> str:
        return self.r.xadd(
            _k("contact", "inbox"),
            {"name": name, "email": email, "message": message, "ts": str(int(time.time()))},
        )

    def list_contacts(self, limit: int = 200):
        try:
            entries = self.r.xrange(_k("contact", "inbox"))
        except Exception:
            return []
        out = []
        for entry_id, fields in entries:
            item = dict(fields)
            item["id"] = entry_id
            out.append(item)
        out.reverse()
        return out[:limit]

    def total_views(self) -> int:
        total = 0
        for d in self.list_demos():
            total += self.get_views("demo", d.slug)
        for p in self.list_posts(include_drafts=True):
            total += self.get_views("post", p.slug)
        return total

    # seed
    def seed_if_empty(self) -> bool:
        # Posts and events seed once (they may be edited later); demos sync separately.
        if self.r.exists(_k("posts", "index")):
            return False
        for p in seedmod.load_posts():
            self.upsert_post(p)
        for e in seedmod.seed_events():
            self.upsert_event(e)
        return True
