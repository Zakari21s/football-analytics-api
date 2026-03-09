# Football Analytics API

REST API for football analytics with favourite player lists. Dataset resources (players, teams, performances, transfers, market value) are read-only; **FavouriteList** is the main CRUD resource.

## Tech stack

- **Backend**: Python, FastAPI
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Database**: SQLite (dev)
- **Testing**: pytest + httpx
- **Frontend**: HTML, CSS, JavaScript (vanilla)

## Setup

### 1. Python environment

- Python 3.10 or higher recommended.
- Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

Copy the example env file and set your values:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

- `DATABASE_URL` – e.g. `sqlite:///./football_analytics.db`
- `API_KEY` – secret key for `X-API-Key` header

### 4. Database

- Run migrations (when Alembic is configured), or use `create_all` for minimal setup.
- Import filtered dataset with the script under `scripts/` (see project plan for filter and import order).

### 5. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

### 6. Run tests

```bash
pytest
```

### 7. Frontend

- Served via FastAPI static mount or open `frontend/index.html` and set API base URL as documented in the app.

## Project structure

```
app/
  main.py              # App factory, routers, CORS
  config.py            # Env (DATABASE_URL, API_KEY)
  database.py          # Engine, SessionLocal, get_db
  models/              # SQLAlchemy models
  schemas/             # Pydantic request/response schemas
  routers/             # API route modules
  services/            # Business logic
  auth/                # API key validation
frontend/
  index.html
  styles.css
  script.js
scripts/
  filter_and_import.py # Filter CSVs (top-5 leagues), load DB
tests/
  conftest.py
  test_*.py
```

## API

- Base path: `/api/v1`
- Authentication: `X-API-Key` header required for `/api/v1/*`.
- See `/docs` for full API documentation once endpoints are implemented.

## Deployment

- Plan: deploy to a live host (e.g. PythonAnywhere or Docker on Railway/Render).
- README and technical report will state the live URL once deployed.
