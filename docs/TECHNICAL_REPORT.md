# Football Analytics API – Technical Report

**Module**: COMP3011  
**Project**: REST API + minimal frontend for football analytics and favourite player lists.

---

## 1. Technology stack and justification

| Layer       | Choice                    | Justification |
|------------|---------------------------|---------------|
| **Backend** | Python 3.10+, FastAPI     | Async support, automatic OpenAPI/Swagger, Pydantic validation, clear routing and dependency injection. |
| **ORM**     | SQLAlchemy 2.x            | Mature ORM with declarative models, session management, and FK support; fits the ERD and CSV-derived schema. |
| **Validation** | Pydantic              | Request/response schemas, clear validation errors (422), type-safe config via pydantic-settings. |
| **Database** | SQLite                   | Single-file, no separate server; suitable for coursework and local deployment; can be swapped for PostgreSQL via `DATABASE_URL`. |
| **Testing**  | pytest, FastAPI TestClient | In-process API tests, fixtures for client and auth headers; no need for httpx async for basic status-code and JSON tests. |
| **Frontend** | Vanilla HTML, CSS, JS    | No framework; fetch API with X-API-Key; minimal scope as per brief (players list, favourite lists CRUD, add/remove players). |

Environment configuration is via `.env` and `pydantic-settings`; no secrets in code. The API key is validated in a single dependency and applied to all `/api/v1/*` routes.

---

## 2. Architecture

Request flow is layered: **Client → FastAPI app → Auth (X-API-Key) → Routers → Services → Database**. Routers are thin (parse request, call service, map exceptions to HTTP); business logic lives in services and receives the DB session via dependency injection.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐     ┌──────────┐
│   Client /  │────▶│  FastAPI     │────▶│  Auth       │────▶│ Routers  │────▶│ Services │
│   Frontend  │     │  app (CORS)  │     │  X-API-Key  │     │ (thin)   │     │ (logic)  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘     └────┬─────┘
                                                                                    │
                                                                                    ▼
                                                                             ┌──────────────┐
                                                                             │   SQLite    │
                                                                             │   (SQLAlchemy)
                                                                             └──────────────┘
```

**Key components:**

- **app/main.py**: App factory, CORS, mount of API v1 router and frontend at `/app`; `/health` and `/docs` remain on the main app.
- **app/auth**: Single dependency that reads `X-API-Key`, compares to config, returns 401 with a consistent JSON body if missing or invalid.
- **app/routers**: One router per resource (players, teams, favourite_lists, analytics); all under `/api/v1` with the auth dependency.
- **app/services**: Reusable functions (e.g. `get_players`, `get_top_scorers`) that take a DB session; no HTTP concerns.
- **app/models / app/schemas**: SQLAlchemy models for dataset and application tables; Pydantic schemas for request/response and pagination.

The dataset (players, teams, performances, transfers, market values) is read-only from the API; the only full CRUD resource is **FavouriteList**, with **FavouriteListPlayer** used for many-to-many membership (add/remove/view list players).

---

## 3. Design choices

**REST and URLs:** All API endpoints are under `/api/v1`. Resource-based paths: e.g. `GET /api/v1/players`, `GET /api/v1/players/{id}/performances`, `POST /api/v1/favourite-lists`, `GET /api/v1/favourite-lists/{id}/players`.

**Status codes:** 200 (OK), 201 (Created for POST), 204 (No Content for DELETE), 400/422 (validation), 401 (missing/invalid API key), 404 (resource not found), 409 (e.g. player already in list). Error responses use a consistent JSON shape (e.g. `{"detail": {"message": "...", "code": "..."}}`).

**CRUD resource:** The main database-backed CRUD resource is **FavouriteList** (create, read list, read one, update name, delete). FavouriteListPlayer supports only add player, remove player, and list players (with optional sort); it is not a separate full CRUD resource.

**Pagination:** List endpoints that return many items (e.g. players, performances, transfers) use `page`, `limit`, and respond with `{ "data": [...], "page", "total_pages", "total_count" }`.

**Authentication:** Every `/api/v1/*` request must include a valid `X-API-Key` header; the dependency runs before route handlers. `/health`, `/docs`, and `/openapi.json` are unauthenticated.

---

## 4. Implementation highlights

**Sorting (players and list players):** The API supports `sort_by` (e.g. `name`, `age`, `market_value`, `minutes_played`) and `order` (asc/desc). Age is derived from `date_of_birth`; market value from the latest row per player in `player_market_value` (subquery on max date); minutes from `SUM(minutes_played)` over `player_performances`. The same logic is used for listing players inside a favourite list.

**Analytics:** Three endpoints demonstrate use of the football dataset: (1) **top-scorers** – `SUM(goals)` from performances, optional filter by season/competition_id; (2) **top-market-values** – latest value per player, ordered by value desc; (3) **most-minutes-played** – `SUM(minutes_played)` per player, optional season filter. All return a list of player identifiers and the computed metric.

**Dataset pipeline:** Data is filtered to top-five leagues (GB1, ES1, IT1, L1, FR1) in a dedicated script that builds allowed club/player IDs and writes filtered CSVs to `web/filtered/`. A separate import script loads these in FK order (teams → players → performances, transfers, market values) with batched commits and streaming reads to avoid loading entire files into memory.

---

## 5. Testing approach

Tests use pytest and FastAPI’s `TestClient` (no separate server). **conftest.py** provides a shared client and `auth_headers` (valid API key). The same SQLite database used for local development is used for tests (no in-memory override in the current setup).

**Coverage:** (1) **Auth** – request without key → 401; wrong key → 401; valid key → 200 on a protected route. (2) **Favourite lists CRUD** – full cycle (create, get, patch, delete, then 404); 404 for get/patch/delete on missing id. (3) **Favourite list players** – add player, list players, add same again → 409, remove player, list empty; 404 when list or player does not exist. (4) **Validation** – POST favourite list with empty or missing name → 422; add player with non-existent player_id → 404. (5) **Players** – list returns 200 and structure `data`, `page`, `total_pages`, `total_count`; sort_by=name; get by id 200/404. (6) **Analytics** – GET top-scorers (and other analytics endpoints) returns 200 and list of items with expected fields.

Tests are run with `pytest` or `pytest tests/ -v`; see README.

---

## 6. Deployment

Deployment has **not** been performed for this submission. The project runs locally with SQLite. The README describes how to run the server (`uvicorn app.main:app`), create the DB, load data, and run tests. It also states that when deploying (e.g. PythonAnywhere or a Docker-based host), one should set `DATABASE_URL` and `API_KEY`, run the create-db and load-data scripts once, and expose the ASGI app `app.main:app`. The live API URL (and frontend URL if applicable) should be added to the README and this report when deployment is completed.

---

## 7. Limitations and future work

- **Single API key:** Authentication is a single shared key; there is no per-user identity or rate limiting.
- **SQLite:** Suitable for coursework and small scale; for production, a server DB (e.g. PostgreSQL) and proper migrations (e.g. Alembic) would be preferable.
- **Frontend:** Minimal by design; improvements could include better error feedback, loading states, and responsive layout.
- **Data:** Dataset is static after import; no live sync with an external source. Analytics are computed at request time (subqueries/aggregations); materialized views or cached aggregates could improve performance for heavy use.

---

*Report length: ~5 pages when rendered to PDF. Export from this Markdown (e.g. via Pandoc or print-to-PDF from a Markdown viewer) for submission.*
