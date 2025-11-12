"""
Database Schemas for Sports Analytics SaaS

Each Pydantic model corresponds to a MongoDB collection. Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# Users
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    provider: Optional[Literal["email", "google", "facebook", "apple"]] = Field(
        "email", description="Auth provider"
    )
    photo_url: Optional[str] = Field(None, description="Avatar URL")
    locale: Optional[str] = Field("en", description="Language preference")
    currency: Optional[str] = Field("USD", description="Currency preference")
    plan: Optional[Literal["free", "starter", "pro"]] = Field("free")
    is_active: bool = Field(True)

# Predictions
class Prediction(BaseModel):
    league: str = Field(..., description="League name, e.g., Premier League")
    country: Optional[str] = Field(None, description="Country/Region")
    match_id: str = Field(..., description="Unique match identifier")
    home_team: str
    away_team: str
    kickoff_iso: str = Field(..., description="UTC kickoff time ISO8601")
    pick: Literal[
        "home_win",
        "away_win",
        "draw",
        "over_2_5",
        "under_2_5",
        "both_teams_score",
        "home_asian",
        "away_asian",
    ]
    odds: float = Field(..., gt=1.0, description="Decimal odds")
    confidence: int = Field(..., ge=1, le=100)
    risk: Literal["low", "medium", "high"] = Field("medium")
    xg_home: Optional[float] = Field(None, ge=0)
    xg_away: Optional[float] = Field(None, ge=0)
    injuries: Optional[str] = None
    weather: Optional[str] = None
    head_to_head: Optional[str] = None
    recent_form: Optional[str] = None
    analysis: Optional[str] = None
    tags: Optional[List[str]] = []
    status: Literal["pending", "won", "lost", "void"] = "pending"

# Blog posts
class Blog(BaseModel):
    slug: str = Field(..., description="URL slug")
    title: str
    excerpt: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    author: Optional[str] = "Analyst Team"
    published_at: Optional[str] = None
    language: Optional[str] = Field("en", description="en/es/fr/pt")
    tags: Optional[List[str]] = []

# Testimonials / Results
class Testimonial(BaseModel):
    name: str
    location: Optional[str] = None
    message: str
    slip_image: Optional[str] = Field(None, description="URL to verified slip image")
    verified: bool = True

# Newsletter subscriptions
class Subscription(BaseModel):
    email: str
    source: Optional[str] = "landing"
    locale: Optional[str] = "en"

# Support tickets / contact
class Contact(BaseModel):
    name: str
    email: str
    message: str
    topic: Optional[str] = "general"

# Plans (reference; pricing may be static via endpoint)
class Plan(BaseModel):
    code: Literal["free", "starter", "pro"]
    name: str
    monthly_price: float
    yearly_price: float
    currency: str = "USD"
    features: List[str] = []

# Legal pages
class Legal(BaseModel):
    slug: Literal["terms", "privacy", "responsible-betting"]
    title: str
    content: str
    updated_at: Optional[datetime] = None
