# Generative AI tools – Declaration

**Module**: COMP3011  
**Project**: Football Analytics API

---

## 1. Tools used and purpose

| Tool / platform | Purpose |
|-----------------|--------|
| **Cursor (AI-assisted editor)** | Design and architecture discussion; code generation for FastAPI routers, Pydantic schemas, SQLAlchemy models, and service layer functions; refactoring (e.g. moving from mounted sub-app to single app with router dependencies). |
| **Claude / Codex (via Cursor)** | Writing and editing Python (app code, scripts, tests); drafting README and API descriptions; suggesting test cases and validation behaviour (e.g. 422 for empty name, 404 for invalid player_id). |
| **Other** | None. |

---

## 2. Sample conversation logs (appendix)

**Excerpt 1 – API key dependency and router setup**  
I asked how to require X-API-Key on all `/api/v1` routes. The suggestion was to add a dependency (e.g. `require_api_key`) that reads the header and returns 401 if missing or invalid, and to attach it to the API v1 router via `APIRouter(..., dependencies=[Depends(require_api_key)]). I applied this so every route under `/api/v1` is protected without repeating the check in each handler.

**Excerpt 2 – Player details endpoint design**  
I asked how to return current market value, full market value history, and a career summary from one endpoint. The suggestion was a single `GET /players/{id}/details` response with: current value as the latest row per player in `player_market_value` (max date); history as all rows for that player ordered by date; career with seasons played (distinct from performances) and previous clubs (distinct team names from performances/teams or transfers). I implemented the service and Pydantic response schema (e.g. `PlayerDetailsResponse` with `market_value_history`, `career`) as suggested and wired the router.

**Excerpt 3 – Top assists and youngest stars queries**  
I requested analytics endpoints for top assists (sum of assists per player, optional season/competition filters) and youngest stars (players under an age limit, aggregated minutes and goals, sorted by minutes then goals). I was given SQLAlchemy query patterns (group by player, join performances/players, filter by age from date_of_birth). I implemented the routes and response schemas (e.g. `TopAssistsResponse`, `YoungestStarResponse`) and added the same optional query parameters as the existing analytics endpoints.

**Excerpt 4 – Test cases for new endpoints**  
I asked for tests for the new player details and analytics endpoints without changing the test DB. The suggestion was: (1) test_player_details_ok – GET players?limit=1, take first id, GET details, assert 200 and presence of player_id, player_name, current_market_value, market_value_history, career (seasons_played, previous_clubs); (2) test_player_details_404 for id 999999999; (3) test_top_assists and test_youngest_stars – GET with limit, assert 200 and list shape, and if non-empty assert first item keys and optionally descending order. I added these to test_players.py and test_analytics.py and ran pytest until green.

---

## 3. Reflection on "creative, high-level" use

I used GenAI for both high-level design (e.g. REST structure, endpoint design, analytics ideas) and implementation (code, tests, documentation). I checked and adapted all suggestions—for example around security (API key handling), error handling (401/404/422), and validation (request/response schemas)—and ran tests to confirm behaviour. I understand and can explain all code and design choices in this submission.

---

*Declaration to be completed by the student and submitted with the technical report as required by the coursework brief. Replace placeholders with your actual tool names, excerpts, and reflection.*
