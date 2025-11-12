import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Prediction, Blog, Testimonial, Subscription, Contact, Plan, User, Legal

app = FastAPI(title="Sports Analytics SaaS API", version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Sports Analytics API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }

    if os.getenv("DATABASE_URL"):
        response["database_url"] = "✅ Set"
    if os.getenv("DATABASE_NAME"):
        response["database_name"] = "✅ Set"

    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:20]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# ---------- Demo seed endpoints ----------
class SeedResult(BaseModel):
    created: int


@app.post("/seed/demo", response_model=SeedResult)
def seed_demo_content():
    """Insert demo predictions, blog posts, plans, testimonials, and legal pages"""
    created = 0

    # Demo plans
    plans = [
        Plan(code="free", name="Free", monthly_price=0, yearly_price=0, currency="USD", features=["Limited daily picks", "Blog access"]),
        Plan(code="starter", name="Starter", monthly_price=19, yearly_price=180, currency="USD", features=["Daily picks", "Confidence & risk labels", "Email alerts"]),
        Plan(code="pro", name="Pro", monthly_price=49, yearly_price=468, currency="USD", features=["All leagues", "Advanced stats (xG)", "Priority support", "Telegram alerts"]),
    ]
    for p in plans:
        try:
            create_document("plan", p)
            created += 1
        except Exception:
            pass

    # Demo blog posts (6)
    blog_samples = [
        Blog(slug=f"intro-{i}", title=f"Data-Driven Football Insights #{i}", excerpt="How we model expected goals and risk.", content="<p>Sample blog content for SEO.</p>", language="en")
        for i in range(1, 7)
    ]
    for b in blog_samples:
        try:
            create_document("blog", b)
            created += 1
        except Exception:
            pass

    # Demo predictions (12)
    leagues = ["Premier League", "La Liga", "Serie A", "Ligue 1", "Bundesliga", "MLS"]
    teams = [
        ("Barcelona", "Real Madrid"),
        ("Man City", "Arsenal"),
        ("Bayern", "Dortmund"),
        ("PSG", "Lyon"),
        ("Inter", "Juventus"),
        ("LAFC", "Seattle")
    ]
    import datetime as dt
    samples: List[Prediction] = []
    for i in range(12):
        home, away = teams[i % len(teams)]
        pr = Prediction(
            league=leagues[i % len(leagues)],
            country="International",
            match_id=f"M{i+1:03d}",
            home_team=home,
            away_team=away,
            kickoff_iso=(dt.datetime.utcnow() + dt.timedelta(hours=i+6)).isoformat() + "Z",
            pick=["home_win", "away_win", "draw", "over_2_5", "under_2_5"][i % 5],
            odds=1.6 + (i % 5) * 0.2,
            confidence=60 + (i % 4) * 5,
            risk=["low", "medium", "high"][i % 3],
            xg_home=1.2 + (i % 3) * 0.3,
            xg_away=0.9 + (i % 3) * 0.2,
            recent_form="W-D-W-L-W",
            analysis="Model favors home due to xG and recent form.",
            tags=["demo", "major-league"],
        )
        samples.append(pr)
    for s in samples:
        try:
            create_document("prediction", s)
            created += 1
        except Exception:
            pass

    # Testimonials
    testis = [
        Testimonial(name="Carlos", location="Mexico", message="Doubled my bankroll with safer picks.", verified=True),
        Testimonial(name="Aïcha", location="Senegal", message="Great xG insights, very helpful!", verified=True),
    ]
    for t in testis:
        try:
            create_document("testimonial", t)
            created += 1
        except Exception:
            pass

    # Legal
    legal = [
        Legal(slug="terms", title="Terms of Service", content="<p>Terms...</p>"),
        Legal(slug="privacy", title="Privacy Policy", content="<p>Privacy...</p>"),
        Legal(slug="responsible-betting", title="Responsible Betting", content="<p>Play responsibly.</p>"),
    ]
    for l in legal:
        try:
            create_document("legal", l)
            created += 1
        except Exception:
            pass

    return SeedResult(created=created)


# ---------- Public API ----------

@app.get("/predictions")
def list_predictions(league: Optional[str] = None, date: Optional[str] = None,
                     min_odds: Optional[float] = None, max_odds: Optional[float] = None,
                     min_conf: Optional[int] = None, max_conf: Optional[int] = None,
                     limit: int = 20):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    filt = {}
    if league:
        filt["league"] = league
    if date:
        # naive filter by string prefix of day
        filt["kickoff_iso"] = {"$regex": f"^{date}"}
    if min_conf or max_conf:
        conf = {}
        if min_conf is not None:
            conf["$gte"] = min_conf
        if max_conf is not None:
            conf["$lte"] = max_conf
        if conf:
            filt["confidence"] = conf
    if min_odds or max_odds:
        odds = {}
        if min_odds is not None:
            odds["$gte"] = min_odds
        if max_odds is not None:
            odds["$lte"] = max_odds
        if odds:
            filt["odds"] = odds

    docs = get_documents("prediction", filt, limit)
    # convert ObjectId
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


@app.get("/predictions/{match_id}")
def get_prediction(match_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    docs = get_documents("prediction", {"match_id": match_id}, 1)
    if not docs:
        raise HTTPException(404, detail="Not found")
    doc = docs[0]
    doc["_id"] = str(doc.get("_id"))
    return doc


@app.get("/blogs")
def list_blogs(limit: int = 6):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    docs = get_documents("blog", {}, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


@app.get("/blogs/{slug}")
def get_blog(slug: str):
    if db is None:
        raise HTTPException(500, detail="Database not available")
    docs = get_documents("blog", {"slug": slug}, 1)
    if not docs:
        raise HTTPException(404, detail="Not found")
    doc = docs[0]
    doc["_id"] = str(doc.get("_id"))
    return doc


@app.get("/plans")
def get_plans():
    if db is None:
        # fallback static
        return {
            "items": [
                {"code": "free", "name": "Free", "monthly_price": 0, "yearly_price": 0, "currency": "USD"},
                {"code": "starter", "name": "Starter", "monthly_price": 19, "yearly_price": 180, "currency": "USD"},
                {"code": "pro", "name": "Pro", "monthly_price": 49, "yearly_price": 468, "currency": "USD"},
            ]
        }
    docs = get_documents("plan", {}, None)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


@app.get("/legal/{slug}")
def get_legal(slug: str):
    if db is None:
        # simple static fallback
        if slug == "terms":
            return {"slug": "terms", "title": "Terms of Service", "content": "<p>Terms...</p>"}
        if slug == "privacy":
            return {"slug": "privacy", "title": "Privacy Policy", "content": "<p>Privacy...</p>"}
        if slug == "responsible-betting":
            return {"slug": "responsible-betting", "title": "Responsible Betting", "content": "<p>Play responsibly.</p>"}
        raise HTTPException(404, detail="Not found")
    docs = get_documents("legal", {"slug": slug}, 1)
    if not docs:
        raise HTTPException(404, detail="Not found")
    doc = docs[0]
    doc["_id"] = str(doc.get("_id"))
    return doc


@app.post("/subscribe")
def subscribe(payload: Subscription):
    try:
        create_document("subscription", payload)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/contact")
def contact(payload: Contact):
    try:
        create_document("contact", payload)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ---------- Simple Admin fetchers (read-only) ----------
@app.get("/admin/testimonials")
def admin_testimonials(limit: int = 10):
    if db is None:
        raise HTTPException(500, detail="Database not available")
    docs = get_documents("testimonial", {}, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}
