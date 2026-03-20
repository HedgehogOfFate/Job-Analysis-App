# Labor Market Analyzer

A web application that fetches job listings from the Adzuna API, analyzes them using regex-based skill extraction, and presents interactive charts and exportable reports.

## Features

- **Job Search** across 15 countries (UK, US, Germany, France, Canada, Australia, and more)
- **Skill Extraction** using regex keyword matching against 100+ known skills (multi-language support)
- **Skill Categorization** into Languages, Frameworks, Databases, Cloud & DevOps, Data & ML, Tools, Web Frontend, Concepts
- **Work Type Detection** — classifies jobs as Remote, Hybrid, On-site, or Unspecified
- **Experience Level Detection** — Entry Level, Mid Level, Senior, or Unspecified
- **Salary Analysis** — normalization (hourly/monthly to annual), statistics, and per-location breakdown
- **Interactive Charts** — location distribution, top skills, work type breakdown, experience levels, skills by category, salary by location
- **Data Export** — CSV, JSON, Excel (.xlsx), and PNG chart downloads for all 6 chart types
- **Redis Caching** — repeated searches are served instantly from cache, skipping the Adzuna API entirely

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.13 |
| API Client | httpx (async, connection pooling) |
| Caching | Redis |
| Skill Extraction | Regex keyword matching |
| Charts (server) | matplotlib |
| Charts (frontend) | Chart.js |
| Excel Export | openpyxl |
| Frontend | Jinja2, vanilla JS, CSS |
| Testing | pytest, pytest-asyncio |
| Containerization | Docker, Docker Compose |

## Project Structure

```
app/
  main.py                  # FastAPI app, routes, export endpoints
  config.py                # Environment-based configuration
  cache.py                 # Redis cache client and key builder
  clients/
    adzuna_client.py       # Async Adzuna API client with batched fetching
  analysis/
    analyzer.py            # Job analysis (locations, salary, work type, experience)
    skill_extractor.py     # Regex-based skill extraction (100+ skills)
  exporter/
    exporter.py            # CSV, JSON, XLSX, and matplotlib chart exporters
  templates/
    index.html             # Main UI template
  static/
    main.js                # Frontend logic and Chart.js rendering
    style.css              # Styles
tests/
  unit/                    # Unit tests for client, analyzer, skill extractor, exporter
  integration/             # Data pipeline tests (analyze -> export)
  api/                     # API endpoint tests (search, export)
  functional/              # End-to-end workflow tests
  performance/             # Performance and scalability benchmarks
```

## Setup

### Prerequisites

- Python 3.13+
- Adzuna API credentials ([developer.adzuna.com](https://developer.adzuna.com))
- Redis (optional but recommended — see [Redis Setup](#redis-setup))

### Installation

```bash
git clone <repository-url>
cd JobAnalisysApp

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

Optional settings (with defaults):

```env
# Adzuna
ADZUNA_RESULTS_PER_PAGE=50
ADZUNA_BATCH_SIZE=10
ADZUNA_BATCH_DELAY=0.1
ADZUNA_MAX_PAGES=50

# Redis
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600
```

### Running

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

### Docker

```bash
docker compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/api/search?what=...&country=...&where=...` | Search and analyze jobs |
| `GET` | `/api/search/cache/clear?what=...&country=...&where=...` | Invalidate a cached search result |
| `GET` | `/api/export/csv` | Download analysis as CSV |
| `GET` | `/api/export/json` | Download analysis as JSON |
| `GET` | `/api/export/xlsx` | Download analysis as Excel |
| `GET` | `/api/export/chart/location` | Download location distribution chart (PNG) |
| `GET` | `/api/export/chart/skills` | Download top skills chart (PNG) |
| `GET` | `/api/export/chart/work-type` | Download work type breakdown chart (PNG) |
| `GET` | `/api/export/chart/experience` | Download experience level chart (PNG) |
| `GET` | `/api/export/chart/skills-category` | Download skills by category chart (PNG) |
| `GET` | `/api/export/chart/salary-location` | Download salary by location chart (PNG) |
| `GET` | `/health` | Health check (includes Redis status) |

### Search Response Shape

```json
{
  "total_jobs": 450,
  "jobs_by_location": {"London": 120, "Manchester": 45},
  "top_skills": [["Python", 180], ["SQL", 140]],
  "skills_by_category": {
    "Languages": [["Python", 180], ["Java", 90]],
    "Cloud & DevOps": [["AWS", 110], ["Docker", 85]]
  },
  "salary_stats": {"count": 300, "avg": 62000, "min": 28000, "max": 120000},
  "work_type_breakdown": {"remote": 85, "hybrid": 120, "onsite": 150, "unspecified": 95},
  "experience_breakdown": {"entry_level": 60, "mid_level": 150, "senior": 130, "unspecified": 110},
  "salary_by_location": {
    "London": {"avg": 70000, "min": 35000, "max": 120000, "count": 80}
  }
}
```

### Health Check Response

```json
{
  "status": "healthy",
  "adzuna_configured": true,
  "last_search_available": true,
  "redis_available": true
}
```

## Testing

```bash
# All tests (210 total)
pytest tests/ -v

# By category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/api/ -v
pytest tests/functional/ -v
pytest tests/performance/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Supported Countries

GB, US, DE, FR, CA, AU, NL, IT, PL, IN, BR, AT, NZ, SG, ZA
