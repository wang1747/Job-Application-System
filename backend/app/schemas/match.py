from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class MatchRequest(BaseModel):
    jd_id: str
    resume_id: str


class MatchResultItem(BaseModel):
    jd_id: str
    resume_id: str
    score: float
    skill_match_detail: Optional[Dict] = None
    gap_analysis: Optional[Dict] = None
    suggestion: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RankingItem(BaseModel):
    jd_id: str
    company: Optional[str] = None
    position: Optional[str] = None
    score: float
