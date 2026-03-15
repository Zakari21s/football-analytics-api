# Generative AI Declaration

**Module:** COMP3011 Web Services and Web Data  
**Assignment:** Coursework 1 – Individual Web Services API Development Project  
**Project:** Football Analytics API

---

## 1. Tools used and purpose

| Tool / platform | Purpose |
|-----------------|--------|
| **Cursor (AI-assisted editor)** | Architecture and API design; code generation and refactoring for FastAPI, SQLAlchemy, and Pydantic; CORS and routing (e.g. trailing-slash and redirect behaviour); frontend structure and styling (favourite lists, list picker modal, analytics-style layout). |
| **Claude / Codex (via Cursor)** | Python implementation (routers, services, schemas, models); test design and validation behaviour; README and API documentation; data design (e.g. club logos, player details, career summary, analytics endpoints). |
| **Other** | None. |

All use was declared; no undisclosed tools were used.

---

## 2. Sample conversation excerpts (summary)

The following summarise representative exchanges. Exported conversation logs are provided as supplementary material (see technical report appendix).

**Excerpt 1 – API key and router design**  
I asked how to enforce X-API-Key on all `/api/v1` routes. The suggestion was a single dependency (e.g. `require_api_key`) that validates the header and returns 401 if missing or invalid, attached to the API v1 router via `APIRouter(..., dependencies=[Depends(require_api_key)])`. I implemented this so every route under `/api/v1` is protected without duplicating checks in handlers.

**Excerpt 2 – Player details endpoint**  
I asked how to return current market value, full market value history, and a career summary from one endpoint. The suggestion was a single `GET /players/{id}/details` response: current value from the latest row per player in `player_market_value`; history as all rows for that player ordered by date; career with seasons played and previous clubs (distinct team names from performances/teams or transfers). I implemented the service, Pydantic schema (`PlayerDetailsResponse` with `market_value_history`, `career`), and router accordingly.

**Excerpt 3 – Analytics: top assists and youngest stars**  
I requested analytics endpoints for top assists (sum of assists per player, optional season/competition filters) and youngest stars (players under an age limit, aggregated minutes and goals, configurable sort). I was given SQLAlchemy patterns (group by player, joins, age from `date_of_birth`). I implemented the routes and response schemas (`TopAssistsResponse`, `YoungestStarResponse`) and aligned query parameters with existing analytics endpoints.

**Excerpt 4 – Test cases**  
I asked for tests for the new player-details and analytics endpoints without altering the test DB. The suggestion covered: (1) `test_player_details_ok` – GET players with limit, take first id, GET details, assert 200 and required fields; (2) `test_player_details_404` for invalid id; (3) tests for top assists and youngest stars asserting 200, list shape, and optional order. I added these to `test_players.py` and `test_analytics.py` and ran pytest to verify.

**Excerpt 5 – CORS and frontend behaviour**  
I described 307 redirects and failed preflight for `/api/v1/favourite-lists` when using trailing slashes. The suggestion was to use consistent trailing-slash URLs and to allow Codespaces origins in CORS (e.g. `allow_origin_regex` for `*.app.github.dev`). I applied the URL and CORS changes so POSTs from the frontend succeed in Codespaces and locally.

---

## 3. Reflection and analysis of GenAI use

I used generative AI in a **methodologically sound** way: for both high-level design (REST structure, endpoint semantics, analytics ideas, frontend layout) and implementation (code, tests, documentation). I did not copy output verbatim; I evaluated every suggestion against the brief, security (e.g. API key handling), and consistency (status codes, validation, error shapes), adapted it where needed, and verified behaviour with tests and manual checks.

I also used GenAI for **creative, solution-level** tasks: exploring alternative designs (e.g. single details endpoint vs. multiple calls), reimagining the frontend (list cards, analytics-style panels, list picker modal), and integrating additional data (club logos, career summary with previous clubs). I can explain and justify every design and implementation choice in this submission.

---

## 4. Supplementary material

Exported conversation logs (examples of the interactions summarised above) are included in the technical report appendix and/or the repository as required by the coursework brief.
