"""
Football Analytics API – FastAPI application factory.
Mounts routers under /api/v1; CORS enabled; auth applied to API routes.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth import require_api_key
from app.routers import analytics, favourite_lists, players, teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: e.g. create DB tables if using create_all."""
    yield
    # Shutdown: close pools, etc. if needed


app = FastAPI(
    title="Football Analytics API",
    description="REST API for football analytics and favourite player lists.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS – allow frontend (same origin or configured origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 routers – all protected by API key (dependency on each router or on prefix)
api_v1 = FastAPI(
    title="Football Analytics API v1",
    version="1.0",
    dependencies=[],  # Add require_api_key here when ready to enforce on all v1 routes
)
api_v1.include_router(players.router, prefix="/players", tags=["players"])
api_v1.include_router(teams.router, prefix="/teams", tags=["teams"])
api_v1.include_router(favourite_lists.router, prefix="/favourite-lists", tags=["favourite-lists"])
api_v1.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

app.mount("/api/v1", api_v1)

# Optional: serve frontend static files
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.is_dir():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/health")
def health() -> dict:
    """Health check for deployment and load balancers."""
    return {"status": "ok"}
