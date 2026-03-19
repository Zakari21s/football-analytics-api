# Football Analytics API

REST API for football analytics with a minimal web frontend. Dataset resources (players, teams, performances, transfers, market values) are read-only; **FavouriteList** is the main CRUD resource (create, read, update, delete lists; add/remove players). The frontend provides a players table (sort, filter, pagination), favourite lists (card-based UI), analytics (top scorers, assists, market values, minutes, youngest stars), and a player-details modal (career summary, market value history).

## Tech stack

- **Backend:** Python 3.10+, FastAPI
- **ORM:** SQLAlchemy 2.x
- **Validation:** Pydantic
- **Database:** SQLite (development)
- **Testing:** pytest, FastAPI TestClient
- **Frontend:** Vanilla HTML, CSS, JavaScript

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

### 4. Dataset filter and database

The dataset is scoped to **top-five European leagues** only (Premier League, La Liga, Serie A, Bundesliga, Ligue 1). Definition: `scripts/constants.py` → `TOP_5_COMPETITION_IDS = ["GB1", "ES1", "IT1", "L1", "FR1"]`.

**Filtered CSVs (recommended)**

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

- **Local:** API at `http://localhost:8000`, frontend at `http://localhost:8000/app/`, interactive docs at `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc`.
- **GitHub Codespaces:** Use the forwarded port URL (e.g. `https://<workspace>-8000.app.github.dev`) for the API and `/app/`, `/docs`, `/redoc` as above.

### 6. Run tests

```bash
pytest
```

### 7. Frontend

- Open the app (e.g. `http://localhost:8000/`); you are redirected to **/app/** where the single-page frontend is served.
- **Players:** Table with sort (name, age, market value, minutes, goals, etc.), order (asc/desc), pagination, and optional search and league/season filters. Click a row to open player details (snapshot, career summary, market value history). Use "Add to list" to add a player to a favourite list.
- **Favourite lists:** Create lists by name; your lists appear as cards. Click a list to open it, then search for players by name and click a result to add, or remove with the button. Toggle between cards and table view.
- **Analytics:** Top scorers, top assists, top market values, most minutes played, youngest stars (with league, season, and age filters).
- **API key:** Set the key in the header bar (stored in `localStorage`). All API requests use the `X-API-Key` header; without it you get "Invalid or missing API key".
- Single `index.html`, `script.js`, and `styles.css`; no frontend framework.

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

- **Base path:** `/api/v1/` (trailing slash; all endpoints use consistent trailing slashes).
- **Authentication:** `X-API-Key` header required for all `/api/v1/*` routes (see OpenAPI security scheme at `/docs`).
- **API documentation (PDF):** [docs/API_Documentation.pdf](docs/API_Documentation.pdf). Interactive docs when the server is running: `/docs` (Swagger UI), `/redoc`.
- **Technical report (PDF):** [docs/Technical_Report.pdf](docs/Technical_Report.pdf) — design, stack justification, testing, GenAI declaration. To regenerate from Markdown: `python scripts/export_report_pdf.py`.

## Dataset

- **Source:** Filtered football dataset derived from Transfermarkt CSV exports (as provided in the coursework materials), originally obtained from a Kaggle dataset: `https://www.kaggle.com/datasets/xfkzujqjvx97n/football-datasets/code`.
- **Scope:** Top-five European leagues only (Premier League, La Liga, Serie A, Bundesliga, Ligue 1) via `competition_id` in `TOP_5_COMPETITION_IDS` (`scripts/constants.py`).
- **Licence:** Follow the licensing and terms of use specified in the coursework brief and the original data provider (Transfermarkt / Kaggle). Do not redistribute raw data outside the course without checking licence and ToS.

## Deployment

- **Live deployment (PythonAnywhere):**  
  - Base URL: `https://zakari21s.pythonanywhere.com`.  
  - Frontend and API are deployed at `https://zakari21s.pythonanywhere.com`.  
  - The main UI is served at `https://zakari21s.pythonanywhere.com/app/`.  
  - Interactive API docs are available at `https://zakari21s.pythonanywhere.com/docs` and ReDoc at `https://zakari21s.pythonanywhere.com/redoc`.
- **Server configuration:**  
  - `DATABASE_URL` is set to point at the SQLite database file on the host (e.g. `sqlite:////home/Zakari21s/football-analytics-api/football_analytics.db`).  
  - `API_KEY` is set as an environment variable; the frontend API key bar must use the same value so that requests include a valid `X-API-Key` header.  
  - Database tables and data are created by running `scripts/create_db.py` and `scripts/load_data.py` once on the host.
- **Local development:** The project can still be run locally with SQLite using the setup steps above; the deployment does not change the local workflow.
