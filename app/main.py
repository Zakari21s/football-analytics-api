"""
Football Analytics API – FastAPI application factory.
Routers under /api/v1; CORS enabled; all /api/v1/* protected by X-API-Key.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth import require_api_key
from app.database import get_db
from app.routers import analytics, favourite_lists, players, teams
from app.schemas.common import PaginatedResponse
from app.schemas.competition import CompetitionResponse
from app.schemas.player import PlayerResponse
from app.schemas.season import SeasonResponse
from app.services import player_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: e.g. create DB tables if using create_all."""
    yield


app = FastAPI(
    title="Football Analytics API",
    description="REST API for football analytics and favourite player lists. All `/api/v1` endpoints require `X-API-Key` header.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project root (directory containing `app/`) and frontend dir as absolute path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


# ---- Root and frontend (before mount so explicit routes take precedence) ----

@app.get("/")
def _root():
    """Redirect to frontend at /app/."""
    return RedirectResponse(url="/app/", status_code=302)


@app.get("/app")
def _app_redirect():
    """Redirect /app to /app/ so relative assets resolve correctly."""
    return RedirectResponse(url="/app/", status_code=302)


@app.get("/app/")
def _app_index():
    """Serve frontend index.html so /app/ loads the app; uses absolute path from project root."""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path, media_type="text/html")


# Mount static files under /app (styles.css, script.js, etc.); explicit /app/ route above handles the index
if FRONTEND_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


# ---- Health and API (unchanged) ----

@app.get("/health")
def health() -> dict:
    """Health check for deployment and load balancers."""
    return {"status": "ok"}


api_v1_router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])


@api_v1_router.get("", summary="API v1 root")
def _api_v1_root() -> dict:
    """Protected by X-API-Key; use for auth testing."""
    return {"api": "v1"}


@api_v1_router.get(
    "/competitions",
    response_model=list[CompetitionResponse],
    summary="List competitions (leagues)",
    description="Distinct leagues from player performances for use in filters.",
)
def _list_competitions(db: Session = Depends(get_db)) -> list[CompetitionResponse]:
    rows = player_service.get_competitions(db)
    return [CompetitionResponse(**r) for r in rows]


@api_v1_router.get(
    "/seasons",
    response_model=list[SeasonResponse],
    summary="List seasons",
    description="Distinct seasons from player performances for use in filters.",
)
def _list_seasons(db: Session = Depends(get_db)) -> list[SeasonResponse]:
    rows = player_service.get_seasons(db)
    return [SeasonResponse(**r) for r in rows]


# Search players by name (explicit path so it never 404s)
@api_v1_router.get(
    "/player-search",
    response_model=PaginatedResponse[PlayerResponse],
    summary="Search players by name",
)
def _player_search(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Search term"),
    limit: int = Query(10, ge=1, le=50),
    competition_id: str | None = Query(None, description="Filter by league (e.g. GB1, ES1)"),
    season: str | None = Query(None, description="Filter by season (e.g. 2023, 08/09)"),
) -> PaginatedResponse[PlayerResponse]:
    search_term = (q or "").strip()
    if not search_term:
        return PaginatedResponse(data=[], page=1, total_pages=0, total_count=0)
    data, total_count = player_service.get_players(
        db, page=1, limit=limit, sort_by="name", order="asc", search=search_term,
        competition_id=competition_id, season=season,
    )
    total_pages = (total_count + limit - 1) // limit if total_count else 0
    return PaginatedResponse(
        data=[PlayerResponse(**d) for d in data],
        page=1,
        total_pages=total_pages,
        total_count=total_count,
    )


api_v1_router.include_router(players.router, prefix="/players", tags=["players"])
api_v1_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_v1_router.include_router(favourite_lists.router, prefix="/favourite-lists", tags=["favourite-lists"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(api_v1_router)


# Temporary debug print to verify which routes exist when the app is imported by uvicorn.
# This helps diagnose why /openapi.json only shows /health in some runs.
try:  # pragma: no cover - debug only
    route_paths = [r.path for r in app.routes]
    print("DEBUG_ROUTES_ON_IMPORT:", route_paths)
except Exception:
    # Avoid failing app import if something goes wrong with debug logging.
    pass
