---
name: football-analytics-outstanding-upgrade
overview: Upgrade the existing Football Analytics API project to an Outstanding-level coursework submission using only the current dataset, by deepening analytics, polishing the frontend, strengthening tests and deployment, and clarifying documentation and GenAI use.
todos:
  - id: backend-player-details
    content: Add player market value history and details endpoint(s) using existing tables (PlayerMarketValue, PlayerPerformance, Team) and expose via players router with new response schemas.
    status: pending
  - id: backend-extra-analytics
    content: Implement new analytics endpoints (top assists, youngest stars, and optional similar players) using existing performance and market value data.
    status: pending
  - id: frontend-tabs-modal
    content: Update frontend to use tabbed layout for Players, Favourite Lists, and Analytics, and add a player details modal that shows photo, current value, value history chart, seasons, and previous clubs.
    status: pending
  - id: code-quality-cleanup
    content: Refactor pagination/response logic into a shared helper, remove debug prints and unused code, and ensure consistent error responses across routers.
    status: pending
  - id: testing-improvements
    content: Introduce isolated test database in pytest fixtures and add tests for new analytics and player details endpoints.
    status: pending
  - id: deployment-docs
    content: Deploy the FastAPI app to a chosen host, configure environment variables and data loading, and document deployment details and live URLs in README and technical report.
    status: pending
  - id: api-doc-pdf
    content: Generate an API documentation PDF from FastAPI docs, add it under docs/, and link it from README and technical report as the formal API documentation deliverable.
    status: pending
  - id: genai-declaration
    content: Complete GENAI_DECLARATION.md with tools, excerpts, and reflection, and add a concise GenAI usage summary section in the technical report.
    status: pending
isProject: false
---

# Football Analytics Outstanding Upgrade Plan

## Goals

- **Lift content mark toward 75/75** without adding new datasets/APIs.
- **Deepen analytics** and use of existing football data (players, performances, transfers, market values).
- **Improve frontend UX** to clearly expose analytics (tabs + rich player details modal).
- **Polish tests, deployment, documentation, and GenAI declaration** to match high-band rubric expectations.

## 1. Backend analytics and player details

- **1.1 Player market value history & details endpoint**
  - In `[app/services/player_service.py](app/services/player_service.py)`, design helper(s) to:
    - Fetch **latest market value** for a player from `PlayerMarketValue` (max `date_unix`).
    - Fetch **market value history** as ordered list of `{date, value}` points.
    - Compute **career summary**: number of seasons played (distinct `season_name` in `PlayerPerformance`) and list of **previous clubs** (distinct club names from performances or transfers, excluding current club).
  - In `[app/routers/players.py](app/routers/players.py)`, add a new route, e.g. `GET /api/v1/players/{player_id}/details` (or `market-value-history` + `career` endpoints) returning a structured schema with:
    - Basic info (id, name, club, position, image URL).
    - Current market value.
    - Market value history for charting.
    - Seasons played and previous clubs.
  - Define corresponding Pydantic response models in `[app/schemas/player.py](app/schemas/player.py)`.
  - Ensure 404 and validation behaviour matches existing players routes.
- **1.2 Additional analytics endpoints using existing data**
  - In `[app/services/analytics_service.py](app/services/analytics_service.py)`, add queries for:
    - **Top assists**: sum of `assists` per player, optional `season` and `competition_id` filters.
    - **Youngest stars**: players under a configurable age (e.g. 23) with minutes/goals thresholds, sorted by minutes or goals.
  - In `[app/routers/analytics.py](app/routers/analytics.py)`, add endpoints, e.g.:
    - `GET /api/v1/analytics/top-assists`.
    - `GET /api/v1/analytics/youngest-stars`.
  - Reuse pagination/limit patterns and consistent error handling.
- **1.3 (Optional) Similar players endpoint**
  - If time allows, design a simple heuristic in `player_service`:
    - Same main_position.
    - Similar age band and similar aggregated stat (e.g. goals/minutes or market value).
  - Expose as `GET /api/v1/players/{player_id}/similar?limit=` in `players.py` with a dedicated response schema.

## 2. Frontend UX: tabs and player modal

- **2.1 Add tabbed layout in frontend**
  - In `[frontend/index.html](frontend/index.html)`, introduce a simple tab structure (no new framework):
    - Tab 1: **Players** – existing players list, filters, sorting, search.
    - Tab 2: **Favourite lists** – existing CRUD and add/remove players.
    - Tab 3: **Analytics** – cards or tables for the analytics endpoints (top scorers, top market values, most minutes, new top assists/youngest stars).
  - Style the tabs in `[frontend/styles.css](frontend/styles.css)` for a clean, professional look (active tab state, good spacing, typography).
- **2.2 Implement rich player details modal**
  - In `[frontend/script.js](frontend/script.js)`, add logic so that clicking a player row:
    - Fetches the new `GET /api/v1/players/{id}/details` endpoint.
    - Opens a **modal or side panel** showing:
      - Photo, name, age, current club name, current market value.
      - Text summary: seasons played, previous clubs.
      - Data for a **market value chart** (date/value pairs).
  - Implement a simple chart using either:
    - A very lightweight chart library (if acceptable for the coursework), or
    - A custom SVG/Canvas/HTML representation (e.g. simple line or bar chart), documented in the report.
  - Ensure error states (e.g. missing value history) are handled gracefully with fallback messages.

## 3. Code quality and architecture polish

- **3.1 Centralise pagination response logic**
  - Identify repeated patterns in routers (players, teams, performances, transfers) where `total_pages` and `PaginatedResponse` are constructed.
  - Add a small helper in `[app/schemas/common.py](app/schemas/common.py)` or a utility module to calculate `total_pages` and build `PaginatedResponse` objects.
  - Refactor routers to use this helper for consistency and reduced duplication.
- **3.2 Remove debug code and tidy imports**
  - In `[app/main.py](app/main.py)`, remove or guard the `DEBUG_ROUTES_ON_IMPORT` print so the production app is clean.
  - Quickly inspect routers and services for unused imports or commented-out code; remove anything clearly dead.

## 4. Testing and reliability

- **4.1 Improve test isolation**
  - In `[tests/conftest.py](tests/conftest.py)`, introduce an **in-memory SQLite** (or dedicated test DB) and create tables per test session, so tests do not depend on the development DB file.
  - Use SQLAlchemy `Base.metadata.create_all` with a dedicated engine for tests.
- **4.2 Add tests for new features**
  - In new or existing test files (e.g. `[tests/test_players.py](tests/test_players.py)`, `[tests/test_analytics.py](tests/test_analytics.py)`), add tests for:
    - Player details/market value history endpoint (200 with expected keys; 404 for missing player).
    - New analytics endpoints: top assists and youngest stars (200 responses, correct sorting assumptions, structure checks).
    - (Optional) Similar players endpoint (non-empty list when data allows; excludes the original player).
  - Update tests to use the API key fixtures and any new routes you introduce.

## 5. Deployment and configuration

- **5.1 Deploy existing app**
  - Choose a host (e.g. PythonAnywhere, Render, Railway) and deploy the existing FastAPI app using `uvicorn` or the platform’s ASGI support.
  - Set required environment variables (e.g. `DATABASE_URL`, `API_KEY`) on the host.
  - Run your existing DB creation and data load scripts once on the host.
- **5.2 Document deployment**
  - In `[README.md](README.md)`, add a clear **“Deployment”** section with:
    - Live API URL (and frontend URL if served together).
    - High-level steps performed on the host.
  - In `[docs/TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md)`, add a short subsection summarising the deployment environment and how it aligns with local setup.

## 6. Documentation and API PDF

- **6.1 Enhance technical report**
  - In `TECHNICAL_REPORT.md`:
    - Add an **“Advanced analytics”** section describing:
      - Market value history per player and how it is computed from `player_market_value`.
      - New analytics endpoints (top assists, youngest stars, optional similar players) and the SQL/aggregation rationale.
    - Add an **“Alternatives considered”** subsection:
      - REST vs GraphQL and why REST was chosen.
      - SQLite vs server DB for deployment and why SQLite (or your chosen DB) fits the coursework.
      - Large single “details” endpoint vs multiple small endpoints.
    - Ensure **Limitations & Future work** explicitly mention remaining gaps (e.g. no per-user auth, no live data updates).
- **6.2 API documentation PDF**
  - Generate an API documentation PDF from FastAPI docs (`/docs` or `/redoc`) and add it under `[docs/](docs/)` (e.g. `docs/API_Documentation.pdf`).
  - In `README.md`, add a link to this PDF and mention interactive docs (`/docs`) and the live URL if deployed.
  - In the technical report, reference the PDF as the formal API documentation deliverable.

## 7. GenAI declaration and reflection

- **7.1 Complete GENAI_DECLARATION.md**
  - Fill in the tools table with actual tools used (Cursor, Claude/ChatGPT, etc.) and specific purposes (design discussion, code generation, test suggestions, documentation structuring).
  - Add 2–4 **short conversation excerpts** that demonstrate:
    - Design exploration (e.g. REST vs GraphQL, how to structure a player details endpoint).
    - Analytics ideas (e.g. computing youngest stars or value history).
  - Write a reflection paragraph explaining how you used GenAI at a **high level** (design and alternatives, not just boilerplate), and how you validated and understood all generated content.
- **7.2 Reference GenAI use in the report**
  - In `TECHNICAL_REPORT.md`, include a small subsection summarising GenAI use and pointing to the declaration and logs as appendices.

## 8. Final verification

- **8.1 Manual test run**
  - Locally, run the server and manually walk through:
    - Players tab: list, filters, click player → details modal with chart.
    - Favourite lists tab: create list, add/remove players, view list players.
    - Analytics tab: verify all analytics tables/cards load correctly.
- **8.2 Automated tests and lints**
  - Run `pytest` and ensure all tests (including new ones) pass.
  - Optionally run any linters/formatters you use to keep code style consistent.

This plan keeps you within your existing dataset and tech stack while adding depth, polish, and clearly documented design and GenAI usage to align with an Outstanding-level submission.