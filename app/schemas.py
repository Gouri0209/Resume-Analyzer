"""
Pydantic schemas for request/response validation.
"""
from typing import List, Optional
from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    id: int
    candidate_name: Optional[str] = None
    resume_filename: str
    job_title: Optional[str] = None

    ats_score: float
    similarity_score: float
    keyword_match_score: float
    overall_score: float

    matched_skills: List[str]
    missing_skills: List[str]
    education: List[str]
    experience: List[str]
    projects: List[str]

    summary: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]

    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    id: int
    candidate_name: Optional[str]
    resume_filename: str
    job_title: Optional[str]
    overall_score: float
    created_at: Optional[str]

    class Config:
        from_attributes = True
