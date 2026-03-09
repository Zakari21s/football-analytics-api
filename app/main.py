"""
Football Analytics API – FastAPI application factory.
Routers under /api/v1; CORS enabled; all /api/v1/* protected by X-API-Key.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth import require_api_key
from app.routers import analytics, favourite_lists, players, teams


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

# All routes under /api/v1 require valid X-API-Key (consistent 401 JSON if missing/invalid)
api_v1_router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])


@api_v1_router.get("", summary="API v1 root")
def _api_v1_root() -> dict:
    """Protected by X-API-Key; use for auth testing."""
    return {"api": "v1"}


api_v1_router.include_router(players.router, prefix="/players", tags=["players"])
api_v1_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_v1_router.include_router(favourite_lists.router, prefix="/favourite-lists", tags=["favourite-lists"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(api_v1_router)


@app.get("/health")
def health() -> dict:
    """Health check for deployment and load balancers."""
    return {"status": "ok"}


# Serve frontend at /app so API routes (/api, /docs, /health) are not shadowed
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.is_dir():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

    @app.get("/")
    def _root() -> RedirectResponse:
        """Redirect to frontend."""
        return RedirectResponse(url="/app/", status_code=302)
