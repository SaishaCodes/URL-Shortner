from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.limiter import rate_limit
from app.database import SessionLocal, init_db
from app.models import URL, Click
from app import cache
from app import analytics
import hashlib
import datetime

app = FastAPI()


# ── Startup: create DB tables if they don't exist ────────────────────────────
@app.on_event("startup")
def startup():
    init_db()


# ── DB session dependency ─────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── POST /shorten — create a short URL ───────────────────────────────────────
@app.post("/shorten")
async def shorten(payload: dict, db: Session = Depends(get_db)):
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' in request body")

    # Generate a 6-character short code from MD5 hash of the URL
    code = hashlib.md5(url.encode()).hexdigest()[:6]

    # Only insert if this code doesn't already exist
    if not db.query(URL).filter(URL.short_code == code).first():
        db.add(URL(short_code=code, original_url=url))
        db.commit()

    return {"short_url": f"http://localhost:8000/{code}"}


# ── GET /metrics — summary stats for the dashboard ───────────────────────────
@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    today = datetime.date.today()
    return {
        "clicks_today": db.query(Click).filter(
            func.date(Click.clicked_at) == today
        ).count(),
        "total_links":  db.query(URL).count(),
        "cache_hit_rate": 91,   # TODO: replace with real Redis INFO stat
        "rate_blocked":   0     # TODO: replace with Redis blocked-request counter
    }


# ── GET /urls — list all shortened URLs with click counts ────────────────────
@app.get("/urls")
def list_urls(db: Session = Depends(get_db)):
    urls = db.query(URL).order_by(URL.created_at.desc()).all()
    return [
        {
            "short_code":   u.short_code,
            "original_url": u.original_url,
            "created_at":   u.created_at,
            "click_count":  db.query(Click).filter_by(
                                short_code=u.short_code
                            ).count()
        }
        for u in urls
    ]


# ── GET /stats/{code} — time-series click data for a specific short code ─────
@app.get("/stats/{code}")
def stats(code: str, db: Session = Depends(get_db)):
    # Verify the code exists first
    if not db.query(URL).filter(URL.short_code == code).first():
        raise HTTPException(status_code=404, detail="Short code not found")
    return analytics.get_click_stats(code)


# ── GET /{code} — redirect to original URL (rate limited) ────────────────────
@app.get("/{code}", dependencies=[Depends(rate_limit)])
async def redirect(code: str, request: Request, db: Session = Depends(get_db)):
    # Step 1: check Redis cache first (fast path)
    cached = await cache.get(code)
    if cached:
        await analytics.record_click(code, request)
        return RedirectResponse(url=cached)

    # Step 2: cache miss — look up in PostgreSQL
    url_obj = db.query(URL).filter(URL.short_code == code).first()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")

    # Step 3: store in Redis for next time (TTL = 1 hour)
    await cache.set(code, url_obj.original_url, ttl=3600)

    # Step 4: record the click in analytics
    await analytics.record_click(code, request)

    return RedirectResponse(url=url_obj.original_url)


# ── Serve frontend static files ───────────────────────────────────────────────
# IMPORTANT: this must always be the LAST line in this file.
# It acts as a catch-all — if it were placed earlier, it would
# intercept /shorten, /metrics, /urls etc. before they could match.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")