"""
Generates a downloadable PDF analysis report using fpdf2.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from fpdf import FPDF

from app.config import settings

logger = logging.getLogger(__name__)

PRIMARY_COLOR = (79, 70, 229)   # indigo
TEXT_COLOR = (31, 41, 55)       # gray-800
MUTED_COLOR = (107, 114, 128)   # gray-500


class ReportPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, "AI Resume Analyzer - Analysis Report", ln=True)
        self.set_draw_color(*PRIMARY_COLOR)
        self.line(10, 20, 200, 20)
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MUTED_COLOR)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*PRIMARY_COLOR)
        self.ln(4)
        self.cell(0, 8, title, ln=True)
        self.set_text_color(*TEXT_COLOR)
        self.set_font("Helvetica", "", 11)

    def bullet_list(self, items) -> None:
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*TEXT_COLOR)
        for item in items:
            safe_item = _sanitize(item)
            self.multi_cell(0, 6, f"- {safe_item}")
        self.ln(1)

    def score_row(self, label: str, value: float) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*TEXT_COLOR)
        self.cell(70, 8, label)
        self.set_font("Helvetica", "", 11)
        self.cell(0, 8, f"{value:.1f} / 100", ln=True)


def _sanitize(text: str) -> str:
    """fpdf2's core fonts only support latin-1; strip unsupported characters."""
    if not text:
        return ""
    return text.encode("latin-1", "ignore").decode("latin-1")


def generate_report(analysis: Dict[str, Any], candidate_name: str, job_title: str) -> Path:
    """Build a PDF report from an analysis dict and save it to REPORTS_DIR."""
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*MUTED_COLOR)
    pdf.cell(0, 6, _sanitize(f"Candidate: {candidate_name or 'N/A'}"), ln=True)
    pdf.cell(0, 6, _sanitize(f"Target Role: {job_title or 'N/A'}"), ln=True)
    pdf.ln(2)

    pdf.section_title("Scores")
    pdf.score_row("Overall Score", analysis["overall_score"])
    pdf.score_row("ATS Score", analysis["ats_score"])
    pdf.score_row("Semantic Similarity", analysis["similarity_score"])
    pdf.score_row("Keyword Match", analysis["keyword_match_score"])

    pdf.section_title("Summary")
    pdf.multi_cell(0, 6, _sanitize(analysis["summary"]))

    pdf.section_title("Matched Skills")
    pdf.bullet_list(analysis["matched_skills"] or ["None identified"])

    pdf.section_title("Missing Skills")
    pdf.bullet_list(analysis["missing_skills"] or ["None - great coverage!"])

    pdf.section_title("Education")
    pdf.bullet_list(analysis["education"] or ["Not clearly identified"])

    pdf.section_title("Experience")
    pdf.bullet_list(analysis["experience"] or ["Not clearly identified"])

    pdf.section_title("Projects")
    pdf.bullet_list(analysis["projects"] or ["Not clearly identified"])

    pdf.section_title("Strengths")
    pdf.bullet_list(analysis["strengths"])

    pdf.section_title("Weaknesses")
    pdf.bullet_list(analysis["weaknesses"])

    pdf.section_title("Improvement Suggestions")
    pdf.bullet_list(analysis["suggestions"])

    safe_name = "".join(c for c in (candidate_name or "candidate") if c.isalnum() or c in ("-", "_")) or "candidate"
    filename = f"report_{safe_name}_{_next_report_id()}.pdf"
    output_path = settings.REPORTS_DIR / filename
    pdf.output(str(output_path))
    logger.info("Generated report at %s", output_path)
    return output_path


_report_counter = 0


def _next_report_id() -> int:
    global _report_counter
    _report_counter += 1
    import time

    return int(time.time())
