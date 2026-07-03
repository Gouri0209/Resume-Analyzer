"""
API and page routes for the AI Resume Analyzer.
"""
from __future__ import annotations

import json
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Analysis
from app.services import analyze_resume, extract_text_from_pdf
from app.report import generate_report

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

ALLOWED_EXTENSIONS = {".pdf"}


# --------------------------------------------------------------------------
# Page routes
# --------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.APP_NAME})


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request, "app_name": settings.APP_NAME})


@router.get("/dashboard/{analysis_id}", response_class=HTMLResponse)
async def dashboard_page(request: Request, analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "app_name": settings.APP_NAME, "analysis": analysis.to_dict()},
    )


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: Session = Depends(get_db)):
    records = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "app_name": settings.APP_NAME, "records": [r.to_dict() for r in records]},
    )


# --------------------------------------------------------------------------
# API routes
# --------------------------------------------------------------------------

def _validate_upload(file: UploadFile) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")


@router.post("/api/analyze")
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    candidate_name: str = Form(""),
    job_title: str = Form(""),
    db: Session = Depends(get_db),
):
    _validate_upload(resume)

    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await resume.read()
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.")

    unique_name = f"{uuid.uuid4().hex}_{resume.filename}"
    saved_path = settings.UPLOAD_DIR / unique_name
    try:
        with open(saved_path, "wb") as f:
            f.write(contents)
    except OSError as exc:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.") from exc

    try:
        raw_text = extract_text_from_pdf(saved_path)
        result = analyze_resume(raw_text, job_description)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Analysis pipeline failed")
        raise HTTPException(status_code=500, detail="Internal error during resume analysis.") from exc

    record = Analysis(
        candidate_name=candidate_name or None,
        resume_filename=resume.filename,
        job_title=job_title or None,
        job_description=job_description,
        resume_text=result["resume_text"],
        ats_score=result["ats_score"],
        similarity_score=result["similarity_score"],
        keyword_match_score=result["keyword_match_score"],
        overall_score=result["overall_score"],
        matched_skills=json.dumps(result["matched_skills"]),
        missing_skills=json.dumps(result["missing_skills"]),
        education=json.dumps(result["education"]),
        experience=json.dumps(result["experience"]),
        projects=json.dumps(result["projects"]),
        summary=result["summary"],
        strengths=json.dumps(result["strengths"]),
        weaknesses=json.dumps(result["weaknesses"]),
        suggestions=json.dumps(result["suggestions"]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        report_path = generate_report(result, candidate_name, job_title)
        record.report_path = str(report_path)
        db.commit()
    except Exception:
        logger.exception("Failed to generate PDF report; continuing without it.")

    return {"analysis_id": record.id, "redirect_url": f"/dashboard/{record.id}"}


@router.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return record.to_dict()


@router.get("/api/history")
async def get_history(db: Session = Depends(get_db)):
    records = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "candidate_name": r.candidate_name,
            "resume_filename": r.resume_filename,
            "job_title": r.job_title,
            "overall_score": r.overall_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/api/report/{analysis_id}")
async def download_report(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record or not record.report_path:
        raise HTTPException(status_code=404, detail="Report not found")

    report_path = Path(record.report_path)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file no longer exists")

    filename = f"resume_analysis_{analysis_id}.pdf"
    return FileResponse(str(report_path), media_type="application/pdf", filename=filename)
