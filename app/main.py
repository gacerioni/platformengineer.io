import os
import re
import secrets
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
from starlette.exceptions import HTTPException as StarletteHTTPException

from .models import Post
from .store import PREFIX, Store

BASE = Path(__file__).resolve().parent
app = FastAPI(title="platformengineer.io")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))
store = Store()

NAV = [("demos", "/demos"), ("learn", "/learn"), ("writing", "/writing"), ("about", "/about"), ("contact", "/contact")]
# commonmark preset keeps the typographer off, so no em dashes or curly quotes are introduced.
_md = MarkdownIt("commonmark")

ADMIN_USER = os.getenv("ADMIN_USER", "gabriel")
ADMIN_PASS = os.getenv("ADMIN_PASS", "")
_basic = HTTPBasic()


def render_md(text: str) -> str:
    return _md.render(text or "")


def base_ctx(**kw):
    data = {
        "latency": store.ping_ms(),
        "backend": store.backend,
        "nav": NAV,
        "year": datetime.now().year,
        "views_total": store.incr_site_view(),
    }
    data.update(kw)
    return data


def page(request: Request, name: str, status_code: int = 200, **kw):
    return templates.TemplateResponse(request, name, base_ctx(**kw), status_code=status_code)


def _demo_views(demos):
    for d in demos:
        d.views = store.get_views("demo", d.slug)
    return demos


def _post_views(posts):
    for p in posts:
        p.views = store.get_views("post", p.slug)
    return posts


def require_admin(creds: HTTPBasicCredentials = Depends(_basic)):
    ok = (
        bool(ADMIN_PASS)
        and secrets.compare_digest(creds.username, ADMIN_USER)
        and secrets.compare_digest(creds.password, ADMIN_PASS)
    )
    if not ok:
        raise HTTPException(status_code=401, detail="unauthorized", headers={"WWW-Authenticate": "Basic"})
    return creds.username


def notify_contact(name: str, email: str, message: str) -> bool:
    host, user, pwd = os.getenv("SMTP_HOST"), os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")
    if not (host and user and pwd):
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = f"platformengineer.io — contact from {name}"
        msg["From"] = user
        msg["To"] = os.getenv("CONTACT_TO", user)
        msg["Reply-To"] = email
        msg.set_content(f"From: {name} <{email}>\n\n{message}")
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        return True
    except Exception:
        return False


@app.on_event("startup")
def _startup():
    store.sync_demos()
    store.sync_lessons()
    store.seed_if_empty()


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def home(request: Request):
    return page(request, "home.html", featured=_demo_views(store.featured_demos()[:3]), posts=_post_views(store.list_posts()[:3]))


@app.get("/demos", response_class=HTMLResponse)
def demos(request: Request, tag: str = None):
    return page(request, "demos.html", demos=_demo_views(store.list_demos(tag)), tags=store.all_tags(), active_tag=tag)


@app.get("/demos/{slug}", response_class=HTMLResponse)
def demo_detail(request: Request, slug: str):
    d = store.get_demo(slug)
    if not d:
        raise HTTPException(status_code=404)
    views = store.incr_views("demo", slug)
    return page(request, "demo.html", d=d, description_html=render_md(d.description), views=views)


@app.get("/writing", response_class=HTMLResponse)
def writing(request: Request):
    return page(request, "writing.html", posts=_post_views(store.list_posts()))


@app.get("/writing/{slug}", response_class=HTMLResponse)
def post_detail(request: Request, slug: str):
    p = store.get_post(slug)
    if not p or p.draft:
        raise HTTPException(status_code=404)
    views = store.incr_views("post", slug)
    return page(request, "post.html", p=p, body_html=render_md(p.body_md), views=views)


@app.get("/learn", response_class=HTMLResponse)
def learn(request: Request):
    return page(request, "learn.html", lessons=store.list_lessons(), workshop_url="https://redis.io/iris-workshop/")


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return page(request, "about.html")


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request, sent: int = 0):
    return page(request, "contact.html", sent=bool(sent))


@app.post("/contact")
def contact_submit(name: str = Form(...), email: str = Form(...), message: str = Form(...)):
    store.add_contact(name, email, message)
    notify_contact(name, email, message)
    return RedirectResponse("/contact?sent=1", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request, _: str = Depends(require_admin)):
    demos_ = store.list_demos()
    posts_ = store.list_posts(include_drafts=True)
    contacts = store.list_contacts()
    stats = {"demos": len(demos_), "posts": len(posts_), "views": store.total_views(), "contacts": len(contacts)}
    return page(
        request,
        "admin.html",
        stats=stats,
        contacts=contacts[:5],
        demo_views=[(d, store.get_views("demo", d.slug)) for d in demos_],
        post_views=[(p, store.get_views("post", p.slug)) for p in posts_],
    )


@app.get("/admin/write", response_class=HTMLResponse)
def admin_write(request: Request, _: str = Depends(require_admin)):
    return page(request, "admin_write.html")


@app.post("/admin/write")
def admin_write_post(
    _: str = Depends(require_admin),
    title: str = Form(...),
    slug: str = Form(""),
    summary: str = Form(""),
    tags: str = Form(""),
    published_at: str = Form(""),
    reading_minutes: int = Form(5),
    draft: str = Form(""),
    body_md: str = Form(""),
):
    s = slug.strip() or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    store.upsert_post(
        Post(
            slug=s,
            title=title,
            summary=summary,
            body_md=body_md,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
            published_at=published_at.strip() or datetime.now().strftime("%Y-%m-%d"),
            reading_minutes=reading_minutes,
            draft=bool(draft),
        )
    )
    return RedirectResponse("/admin" if draft else f"/writing/{s}", status_code=303)


@app.get("/admin/inbox", response_class=HTMLResponse)
def admin_inbox(request: Request, _: str = Depends(require_admin)):
    return page(request, "admin_inbox.html", contacts=store.list_contacts())


@app.get("/healthz")
def healthz():
    info = {
        "backend": store.backend,
        "latency_ms": store.ping_ms(),
        "demos": len(store.list_demos()),
        "posts": len(store.list_posts(include_drafts=True)),
    }
    try:
        info["dbsize"] = store.r.dbsize()
        info["peio_keys"] = sum(1 for _ in store.r.scan_iter(match=PREFIX + "*", count=500))
    except Exception:
        pass
    return info


@app.exception_handler(StarletteHTTPException)
async def http_exc(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return page(request, "404.html", status_code=404)
    return HTMLResponse(str(exc.status_code), status_code=exc.status_code, headers=getattr(exc, "headers", None) or {})
