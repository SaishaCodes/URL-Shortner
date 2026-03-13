from app.database import SessionLocal
from app.models import Click
from sqlalchemy import func
import datetime
 
 
async def record_click(code: str, request):
    db = SessionLocal()
    try:
        db.add(Click(
            short_code=code,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        ))
        db.commit()
    finally:
        db.close()
 
 
def get_click_stats(code: str, days: int = 7):
    db = SessionLocal()
    try:
        since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        rows = (
            db.query(
                func.date(Click.clicked_at).label("date"),
                func.count().label("count")
            )
            .filter(Click.short_code == code, Click.clicked_at >= since)
            .group_by(func.date(Click.clicked_at))
            .order_by(func.date(Click.clicked_at))
            .all()
        )
        return [{"date": str(r.date), "count": r.count} for r in rows]
    finally:
        db.close()