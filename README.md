# AI Resume Analyzer

A production-ready, AI-powered resume analysis platform. Upload a resume (PDF) and a
job description, and get an instant ATS score, semantic similarity score, keyword match
analysis, missing-skill detection, and actionable improvement suggestions — all presented
in a modern, animated SaaS-style dashboard.

## Features

-  Drag & drop PDF resume upload
-  Semantic similarity scoring using TF-IDF term-overlap analysis
-  ATS-friendliness score based on section coverage, keyword density, and formatting
-  Skills, education, experience, and project extraction
-  Missing skill / keyword gap detection
-  Auto-generated summary, strengths, weaknesses, and improvement suggestions
-  Animated score circles and Chart.js skill-match doughnut chart
-  Dark mode with persisted preference
-  Downloadable PDF analysis report
-  Analysis history stored in SQLite via SQLAlchemy
-  Fully responsive, modern SaaS UI

## Tech Stack

**Backend:** Python 3.12, FastAPI, Uvicorn, Jinja2
**ML/NLP:** scikit-learn (TF-IDF similarity), pdfplumber, NumPy, pandas, curated skills taxonomy
**Frontend:** HTML5, CSS3 (custom design system), vanilla JavaScript, Chart.js
**Database:** SQLite + SQLAlchemy ORM
**Reports:** fpdf2 (PDF generation)
**Deployment:** Render (via `render.yaml` / `Procfile`)

## Folder Structure

```
resume-analyzer/
├── app/
│   ├── main.py            # FastAPI app entrypoint
│   ├── routes.py           # Page + API routes
│   ├── services.py         # Extraction, scoring, NLP pipeline
│   ├── report.py           # PDF report generation
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # DB engine/session setup
│   ├── config.py             # Environment-based settings
│   ├── schemas.py            # Pydantic response schemas
│   ├── skills_data.py         # Skills taxonomy & section headers
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── upload.html
│   │   ├── dashboard.html
│   │   └── history.html
│   └── static/
│       ├── css/styles.css
│       └── js/ (theme.js, upload.js, dashboard.js)
├── uploads/                  # Uploaded resume PDFs (gitignored)
├── reports/                   # Generated PDF reports (gitignored)
├── requirements.txt
├── render.yaml
├── Procfile
├── .env.example
├── .gitignore
└── README.md
```

## Installation

1. Clone the repository and enter the folder:
   ```bash
   git clone <your-repo-url>
   cd resume-analyzer
   ```
2. Create and activate a virtual environment:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

## Running Locally

```bash
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000** in your browser.

- Landing page: `/`
- Upload & analyze: `/upload`
- History: `/history`
- Health check: `/health`
- API docs (Swagger): `/docs`

## Deployment on Render

1. Push this repository to GitHub.
2. In Render, click **New +** → **Blueprint**, and point it at your repo — Render will
   detect `render.yaml` automatically. Alternatively, create a **Web Service** manually:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set environment variables from `.env.example` in the Render dashboard (or let
   `render.yaml` generate `SECRET_KEY` automatically).
4. Attach a persistent disk (already configured in `render.yaml`) if you want uploaded
   resumes and the SQLite database to survive restarts/deploys.
5. Deploy — Render will build and start the service automatically.

> For production use with real user data, consider swapping SQLite for a managed
> PostgreSQL database (update `DATABASE_URL` accordingly — SQLAlchemy needs no code
> changes beyond the connection string).

## Notes on ML Behavior

This project deliberately uses **TF-IDF cosine similarity** (via scikit-learn) instead of
transformer embedding models (e.g. `sentence-transformers` + PyTorch) for semantic
similarity scoring. Embedding models typically need 500MB-1GB+ of RAM just to load,
which exceeds the 512MB limit on Render's free tier and similar constrained hosting.
TF-IDF is lightweight, has no model download step, and still produces a meaningful
term-overlap similarity score.

If you deploy on a paid Render plan (or any host with more memory) and want true
semantic embeddings, you can reintroduce `sentence-transformers`:
1. Add `sentence-transformers` back to `requirements.txt`.
2. In `app/services.py`, replace the body of `compute_semantic_similarity` with a
   `SentenceTransformer(...).encode(...)` + cosine similarity call (cache the loaded
   model at module level so it only loads once per process).

Skills, education, experience, and project extraction use a curated keyword/regex-based
taxonomy (`app/skills_data.py`) rather than spaCy NER, which keeps memory usage and cold
start times low while still being reliable for structured resume text.

## License

MIT License — free to use, modify, and deploy.
