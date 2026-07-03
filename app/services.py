"""
Core business logic for the AI Resume Analyzer:
  - PDF text extraction
  - Text cleaning
  - Skills / education / experience / project extraction
  - ATS score, semantic similarity, keyword match
  - Missing skills detection
  - Summary, strengths, weaknesses, suggestions
  - PDF report generation
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Dict, Any

import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.skills_data import (
    SKILLS_DB,
    DEGREE_KEYWORDS,
    EDUCATION_SECTION_HEADERS,
    EXPERIENCE_SECTION_HEADERS,
    PROJECT_SECTION_HEADERS,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# PDF Extraction
# --------------------------------------------------------------------------

def extract_text_from_pdf(file_path: Path) -> str:
    """Extract raw text from a PDF resume using pdfplumber."""
    text_parts: List[str] = []
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
    except Exception as exc:
        logger.exception("Failed to extract text from PDF %s", file_path)
        raise ValueError(f"Could not read PDF file: {exc}") from exc

    full_text = "\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("No extractable text found in the PDF. It may be a scanned image.")
    return full_text


# --------------------------------------------------------------------------
# Cleaning
# --------------------------------------------------------------------------

def clean_text(raw_text: str) -> str:
    """Normalize whitespace and strip non-printable artifacts from extracted text."""
    text = raw_text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


def _flatten_for_matching(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


# --------------------------------------------------------------------------
# Section splitting helper
# --------------------------------------------------------------------------

def _extract_section(lines: List[str], headers: List[str]) -> str:
    """Grab the block of text under any of the given section headers."""
    lower_lines = [ln.lower().strip(" :\t") for ln in lines]
    start_idx = None
    for i, ln in enumerate(lower_lines):
        if ln in headers or any(ln.startswith(h) and len(ln) < len(h) + 6 for h in headers):
            start_idx = i
            break
    if start_idx is None:
        return ""

    all_headers = (
        EDUCATION_SECTION_HEADERS + EXPERIENCE_SECTION_HEADERS + PROJECT_SECTION_HEADERS
        + ["skills", "technical skills", "certifications", "achievements",
           "summary", "objective", "contact", "references", "languages",
           "core competencies", "key skills"]
    )
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        candidate = lower_lines[j]
        if candidate in all_headers and candidate not in headers:
            end_idx = j
            break
    return "\n".join(lines[start_idx + 1:end_idx]).strip()


# --------------------------------------------------------------------------
# Skills extraction
# --------------------------------------------------------------------------

def extract_skills(text: str) -> List[str]:
    """Extract known skills from resume text using keyword matching."""
    flat = _flatten_for_matching(text)
    found = set()
    for skill in SKILLS_DB:
        pattern = r"(?<![a-zA-Z0-9+#.])" + re.escape(skill) + r"(?![a-zA-Z0-9+#])"
        if re.search(pattern, flat):
            found.add(skill)
    return sorted(found)


# --------------------------------------------------------------------------
# Education extraction
# --------------------------------------------------------------------------

def extract_education(text: str) -> List[str]:
    lines = [ln for ln in text.split("\n") if ln.strip()]
    section = _extract_section(lines, EDUCATION_SECTION_HEADERS)
    entries: List[str] = []

    source_lines = section.split("\n") if section else lines
    flat_lower = text.lower()

    for degree in DEGREE_KEYWORDS:
        if degree in flat_lower:
            for ln in source_lines:
                if degree in ln.lower():
                    cleaned = ln.strip(" -•\t")
                    if cleaned and cleaned not in entries:
                        entries.append(cleaned)
                    break

    if not entries and section:
        entries = [ln.strip(" -•\t") for ln in section.split("\n") if ln.strip()][:5]

    return entries[:8]


# --------------------------------------------------------------------------
# Experience extraction
# --------------------------------------------------------------------------

_DATE_RANGE_RE = re.compile(
    r"(20\d{2}|19\d{2})\s*(?:-|–|to)\s*(20\d{2}|present|current|now)",
    re.IGNORECASE,
)


def extract_experience(text: str) -> List[str]:
    lines = [ln for ln in text.split("\n") if ln.strip()]
    section = _extract_section(lines, EXPERIENCE_SECTION_HEADERS)
    entries: List[str] = []

    source_lines = section.split("\n") if section else lines
    for ln in source_lines:
        if _DATE_RANGE_RE.search(ln):
            cleaned = ln.strip(" -•\t")
            if cleaned and cleaned not in entries:
                entries.append(cleaned)

    if not entries and section:
        entries = [ln.strip(" -•\t") for ln in section.split("\n") if ln.strip()][:6]

    return entries[:10]


def estimate_years_of_experience(text: str) -> float:
    """Roughly estimate total years of experience from date ranges found in text."""
    years_found = []
    for match in _DATE_RANGE_RE.finditer(text):
        start_raw, end_raw = match.group(1), match.group(2)
        try:
            start = int(start_raw)
        except ValueError:
            continue
        if end_raw.lower() in ("present", "current", "now"):
            from datetime import datetime

            end = datetime.utcnow().year
        else:
            try:
                end = int(end_raw)
            except ValueError:
                continue
        if end >= start:
            years_found.append(end - start)
    return float(sum(years_found)) if years_found else 0.0


# --------------------------------------------------------------------------
# Project extraction
# --------------------------------------------------------------------------

def extract_projects(text: str) -> List[str]:
    lines = [ln for ln in text.split("\n") if ln.strip()]
    section = _extract_section(lines, PROJECT_SECTION_HEADERS)
    if not section:
        return []
    entries = [ln.strip(" -•\t") for ln in section.split("\n") if ln.strip()]
    return entries[:10]


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def compute_keyword_match(resume_text: str, job_description: str) -> Dict[str, Any]:
    """TF-IDF-based keyword overlap between resume and job description."""
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(job_description))

    if not jd_skills:
        return {"score": 0.0, "matched": sorted(resume_skills), "missing": []}

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    score = round((len(matched) / len(jd_skills)) * 100, 2) if jd_skills else 0.0

    return {"score": score, "matched": matched, "missing": missing}


def compute_semantic_similarity(resume_text: str, job_description: str) -> float:
    """
    Cosine similarity between resume and job description using TF-IDF vectors.

    This intentionally avoids embedding models (e.g. sentence-transformers/torch),
    which require far more memory than fits in constrained/free-tier hosting.
    TF-IDF still captures meaningful term-overlap similarity at a fraction of the
    memory and startup cost.
    """
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vectorizer.fit_transform([resume_text, job_description])
        sim = cosine_similarity(tfidf[0], tfidf[1])[0][0]
        return round(float(sim) * 100, 2)
    except ValueError:
        return 0.0


def compute_ats_score(resume_text: str, sections_found: Dict[str, bool], keyword_score: float) -> float:
    """
    A composite ATS-friendliness score based on:
      - presence of key resume sections
      - keyword match with job description
      - resume length / formatting sanity checks
    """
    section_weight = 40
    keyword_weight = 40
    formatting_weight = 20

    sections_present = sum(1 for v in sections_found.values() if v)
    section_score = (sections_present / max(len(sections_found), 1)) * section_weight

    keyword_score_component = (keyword_score / 100) * keyword_weight

    word_count = len(resume_text.split())
    if 250 <= word_count <= 900:
        formatting_score = formatting_weight
    elif word_count < 250:
        formatting_score = formatting_weight * (word_count / 250)
    else:
        formatting_score = formatting_weight * max(0.5, 900 / word_count)

    total = section_score + keyword_score_component + formatting_score
    return round(min(total, 100), 2)


# --------------------------------------------------------------------------
# Summary / Strengths / Weaknesses / Suggestions
# --------------------------------------------------------------------------

def generate_summary(skills: List[str], education: List[str], experience: List[str],
                      projects: List[str], years_exp: float) -> str:
    parts = []
    if years_exp > 0:
        parts.append(f"Candidate has approximately {years_exp:.0f} year(s) of relevant experience")
    else:
        parts.append("Candidate profile is likely early-career or does not list explicit date ranges")

    if skills:
        top_skills = ", ".join(skills[:8])
        parts.append(f"with demonstrated skills in {top_skills}")

    if education:
        parts.append(f"holds {len(education)} listed qualification(s)")

    if projects:
        parts.append(f"and has showcased {len(projects)} project(s)")

    return ". ".join(p.strip() for p in parts if p).strip() + "."


def generate_strengths(matched_skills: List[str], sections_found: Dict[str, bool],
                        years_exp: float, ats_score: float) -> List[str]:
    strengths = []
    if len(matched_skills) >= 5:
        strengths.append(f"Strong alignment with {len(matched_skills)} required skills from the job description.")
    elif matched_skills:
        strengths.append(f"Some relevant skills present: {', '.join(matched_skills[:5])}.")

    if sections_found.get("projects"):
        strengths.append("Includes a dedicated projects section demonstrating hands-on work.")
    if sections_found.get("experience"):
        strengths.append("Work experience section clearly present and identifiable.")
    if years_exp >= 2:
        strengths.append(f"Approximately {years_exp:.0f}+ years of relevant experience.")
    if ats_score >= 75:
        strengths.append("Resume structure is well-optimized for ATS parsing.")

    if not strengths:
        strengths.append("Resume was successfully parsed and contains identifiable content sections.")
    return strengths


def generate_weaknesses(missing_skills: List[str], sections_found: Dict[str, bool],
                         ats_score: float, word_count: int) -> List[str]:
    weaknesses = []
    if missing_skills:
        weaknesses.append(
            f"Missing {len(missing_skills)} skill(s) mentioned in the job description: "
            f"{', '.join(missing_skills[:8])}."
        )
    if not sections_found.get("education"):
        weaknesses.append("No clearly identifiable education section was found.")
    if not sections_found.get("experience"):
        weaknesses.append("No clearly identifiable work experience section was found.")
    if not sections_found.get("projects"):
        weaknesses.append("No projects section found; consider adding relevant project work.")
    if word_count < 200:
        weaknesses.append("Resume content appears short; consider adding more detail.")
    if word_count > 1200:
        weaknesses.append("Resume is quite long; consider condensing to 1-2 pages.")
    if ats_score < 50:
        weaknesses.append("Overall ATS compatibility score is low; formatting or keyword coverage needs improvement.")

    if not weaknesses:
        weaknesses.append("No major weaknesses detected relative to the job description.")
    return weaknesses


def generate_suggestions(missing_skills: List[str], sections_found: Dict[str, bool],
                          similarity_score: float) -> List[str]:
    suggestions = []
    if missing_skills:
        suggestions.append(
            f"Add or highlight experience with: {', '.join(missing_skills[:8])} if applicable."
        )
    if not sections_found.get("projects"):
        suggestions.append("Add a Projects section with 2-3 relevant, quantifiable projects.")
    if not sections_found.get("education"):
        suggestions.append("Add a clearly labeled Education section.")
    if similarity_score < 50:
        suggestions.append(
            "Tailor resume wording more closely to the job description's terminology and responsibilities."
        )
    suggestions.append("Use quantifiable achievements (metrics, percentages, outcomes) wherever possible.")
    suggestions.append("Ensure consistent formatting and standard section headings for better ATS parsing.")
    return suggestions


def detect_sections(text: str) -> Dict[str, bool]:
    lower = text.lower()
    return {
        "education": any(h in lower for h in EDUCATION_SECTION_HEADERS),
        "experience": any(h in lower for h in EXPERIENCE_SECTION_HEADERS),
        "projects": any(h in lower for h in PROJECT_SECTION_HEADERS),
        "skills": any(h in lower for h in ["skills", "technical skills", "core competencies"]),
    }


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def analyze_resume(resume_raw_text: str, job_description: str) -> Dict[str, Any]:
    """Run the full analysis pipeline and return a structured result dict."""
    resume_text = clean_text(resume_raw_text)
    jd_text = clean_text(job_description)

    skills = extract_skills(resume_text)
    education = extract_education(resume_text)
    experience = extract_experience(resume_text)
    projects = extract_projects(resume_text)
    years_exp = estimate_years_of_experience(resume_text)

    sections_found = detect_sections(resume_text)

    keyword_result = compute_keyword_match(resume_text, jd_text)
    similarity_score = compute_semantic_similarity(resume_text, jd_text)
    ats_score = compute_ats_score(resume_text, sections_found, keyword_result["score"])

    overall_score = round(
        (ats_score * 0.35) + (similarity_score * 0.40) + (keyword_result["score"] * 0.25), 2
    )

    word_count = len(resume_text.split())

    summary = generate_summary(skills, education, experience, projects, years_exp)
    strengths = generate_strengths(keyword_result["matched"], sections_found, years_exp, ats_score)
    weaknesses = generate_weaknesses(keyword_result["missing"], sections_found, ats_score, word_count)
    suggestions = generate_suggestions(keyword_result["missing"], sections_found, similarity_score)

    return {
        "resume_text": resume_text,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "years_experience": years_exp,
        "ats_score": ats_score,
        "similarity_score": similarity_score,
        "keyword_match_score": keyword_result["score"],
        "overall_score": overall_score,
        "matched_skills": keyword_result["matched"],
        "missing_skills": keyword_result["missing"],
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "sections_found": sections_found,
        "word_count": word_count,
    }
