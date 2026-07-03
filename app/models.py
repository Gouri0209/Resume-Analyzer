"""
SQLAlchemy ORM models for storing resume analysis history.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime

from app.database import Base


class Analysis(Base):
    """Stores a single resume-vs-job-description analysis result."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(255), nullable=True)
    resume_filename = Column(String(255), nullable=False)

    job_title = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=False)
    resume_text = Column(Text, nullable=False)

    ats_score = Column(Float, default=0.0)
    similarity_score = Column(Float, default=0.0)
    keyword_match_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)

    matched_skills = Column(Text, default="[]")   # JSON-encoded list
    missing_skills = Column(Text, default="[]")   # JSON-encoded list
    education = Column(Text, default="[]")        # JSON-encoded list
    experience = Column(Text, default="[]")       # JSON-encoded list
    projects = Column(Text, default="[]")         # JSON-encoded list

    summary = Column(Text, default="")
    strengths = Column(Text, default="[]")        # JSON-encoded list
    weaknesses = Column(Text, default="[]")       # JSON-encoded list
    suggestions = Column(Text, default="[]")      # JSON-encoded list

    report_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        import json

        return {
            "id": self.id,
            "candidate_name": self.candidate_name,
            "resume_filename": self.resume_filename,
            "job_title": self.job_title,
            "ats_score": self.ats_score,
            "similarity_score": self.similarity_score,
            "keyword_match_score": self.keyword_match_score,
            "overall_score": self.overall_score,
            "matched_skills": json.loads(self.matched_skills or "[]"),
            "missing_skills": json.loads(self.missing_skills or "[]"),
            "education": json.loads(self.education or "[]"),
            "experience": json.loads(self.experience or "[]"),
            "projects": json.loads(self.projects or "[]"),
            "summary": self.summary,
            "strengths": json.loads(self.strengths or "[]"),
            "weaknesses": json.loads(self.weaknesses or "[]"),
            "suggestions": json.loads(self.suggestions or "[]"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
