"""
A curated taxonomy of common technical and professional skills used for
keyword-based extraction and matching. This intentionally avoids requiring
a network call at runtime, so extraction works even if optional NLP models
(spaCy) are unavailable.
"""

SKILLS_DB = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "dart",
    "sql", "html", "css", "bash", "shell scripting",
    # Web frameworks
    "react", "react.js", "angular", "vue", "vue.js", "next.js", "nuxt.js", "django",
    "flask", "fastapi", "express", "express.js", "spring", "spring boot", "asp.net",
    "laravel", "ruby on rails", "node.js", "nodejs",
    # Data / ML
    "machine learning", "deep learning", "artificial intelligence", "nlp",
    "natural language processing", "computer vision", "data science", "data analysis",
    "data engineering", "data visualization", "statistics", "pandas", "numpy",
    "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras", "opencv",
    "sentence transformers", "transformers", "huggingface", "spacy", "nltk",
    "power bi", "tableau", "excel", "big data", "hadoop", "spark", "pyspark",
    "airflow", "etl",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "ci/cd", "git", "github", "gitlab", "bitbucket",
    "linux", "nginx", "microservices", "rest api", "graphql", "grpc", "serverless",
    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "sqlite", "redis", "oracle",
    "elasticsearch", "cassandra", "dynamodb", "firebase",
    # Soft / project skills
    "leadership", "communication", "teamwork", "problem solving", "project management",
    "agile", "scrum", "kanban", "time management", "critical thinking",
    "presentation skills", "collaboration", "mentoring", "stakeholder management",
    # Other tools
    "jira", "confluence", "figma", "postman", "vs code", "unit testing", "pytest",
    "selenium", "webpack", "sass", "tailwind", "tailwind css", "bootstrap",
    "api development", "system design", "object-oriented programming", "oop",
]

DEGREE_KEYWORDS = [
    "b.tech", "btech", "bachelor of technology", "b.e.", "bachelor of engineering",
    "m.tech", "mtech", "master of technology", "b.sc", "bachelor of science",
    "m.sc", "master of science", "mba", "master of business administration",
    "bachelor of arts", "b.a.", "master of arts", "m.a.", "phd", "ph.d",
    "doctorate", "diploma", "associate degree", "bachelor", "master",
    "high school", "b.com", "m.com", "bca", "mca",
]

EDUCATION_SECTION_HEADERS = ["education", "academic background", "academic qualifications"]
EXPERIENCE_SECTION_HEADERS = ["experience", "work experience", "employment history",
                               "professional experience", "work history"]
PROJECT_SECTION_HEADERS = ["projects", "personal projects", "academic projects",
                            "key projects"]
SKILLS_SECTION_HEADERS = ["skills", "technical skills", "core competencies",
                           "key skills"]
