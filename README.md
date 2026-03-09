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

### 4. Dataset filter (Step 0) and database

The dataset is scoped to **top-5 European leagues** only (Premier League, La Liga, Serie A, Bundesliga, Ligue 1).  
Definition: `scripts/constants.py` → `TOP_5_COMPETITION_IDS = ["GB1", "ES1", "IT1", "L1", "FR1"]`.

**Option A (chosen): filtered CSVs**

- Run the filter script from the project root. It builds **allowed_club_ids** (from `team_details` and `team_competitions_seasons` where `competition_id` in TOP_5) and **allowed_player_ids** (from `player_performances` where `competition_id` in TOP_5, union players whose `current_club_id` is in allowed clubs). It then writes filtered CSVs to `web/filtered/`:

```bash
python scripts/filter_dataset.py
```

- Row counts are printed so you can verify the dataset is reduced.
- Optional: `web/filtered/allowed_ids.json` is also written (allowed_club_ids and allowed_player_ids) for an alternative filter-at-import (option B) if you prefer not to keep filtered copies.

**Database**

- Create tables (no data yet) by running:
  ```bash
  python scripts/create_db.py
  ```
  This uses SQLAlchemy `Base.metadata.create_all(bind=engine)` and creates all tables (players, teams, player_performances, transfer_history, player_market_value, favourite_lists, favourite_list_players). Alternatively use Alembic: `alembic init`, create initial migration, then `alembic upgrade head`.
- Load the filtered dataset into the DB (expects CSVs in `web/filtered/`; run `filter_dataset.py` first if needed):
  ```bash
  python scripts/load_data.py
  ```
  Import order: teams (deduplicated by club_id) → players → player_performances → transfer_history → player_market_value. Row counts per table are logged. Uses batch commits and streams CSVs to avoid loading everything into memory.

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
  constants.py          # TOP_5_COMPETITION_IDS
  create_db.py          # Create DB tables (create_all)
  filter_dataset.py     # Step 0: build allowed IDs, write web/filtered/
  load_data.py          # Step 3: import web/filtered/ into DB (teams → players → …)
  filter_and_import.py  # Legacy/stub; use load_data.py for import
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
