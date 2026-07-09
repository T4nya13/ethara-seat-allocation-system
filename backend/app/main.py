"""FastAPI application entry point.

Exposes:
  GET  /                → API info
  GET  /health          → liveness + DB reachability check
  ---  /projects        → project CRUD
  ---  /employees       → employee CRUD + soft-delete
  ---  /seats           → seat CRUD + allocate/release
  GET  /dashboard/stats → live aggregate stats
  POST /ai/query        → natural-language assistant
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import projects, employees, seats, dashboard, ai



# ── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Nothing to initialise at scaffold stage — models + migrations come next.
    yield
    await engine.dispose()


# ── App factory ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Ethara Seat Allocation API",
    description=(
        "REST API for managing seat allocation, project mapping, and employee "
        "records for ~5,000 employees across multiple floors and zones."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(projects.router)
app.include_router(employees.router)
app.include_router(seats.router)
app.include_router(dashboard.router)
app.include_router(ai.router)

@app.get("/", tags=["root"])
async def root() -> dict:
    """API root — returns basic metadata."""
    return {
        "message": "Ethara Seat Allocation API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["root"])
async def health() -> dict:
    """Liveness + DB reachability check."""
    db_status = "unreachable"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass

    return {
        "status": "ok",
        "environment": settings.environment,
        "db": db_status,
    }
