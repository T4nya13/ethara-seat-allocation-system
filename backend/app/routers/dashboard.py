"""Dashboard router — aggregate statistics over the live database.

GET /dashboard/stats
    Returns a single JSON object with employee/project/seat counts and
    an occupancy percentage, computed via SQLAlchemy func.count() so that
    the numbers are always up to date after every allocation or release.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.employee import Employee
from app.models.project import Project
from app.models.seat import Seat
from app.models.seat_allocation import SeatAllocation
from app.models.enums import SeatStatus, AllocationStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """Return live aggregate stats: employees, projects, seats, occupancy."""

    # ── Employee count ────────────────────────────────────────────────────────
    employee_count: int = await db.scalar(
        select(func.count()).select_from(Employee)
    ) or 0

    # ── Project count ─────────────────────────────────────────────────────────
    project_count: int = await db.scalar(
        select(func.count()).select_from(Project)
    ) or 0

    # ── Seat counts by status ─────────────────────────────────────────────────
    total_seats: int = await db.scalar(
        select(func.count()).select_from(Seat)
    ) or 0

    occupied_seats: int = await db.scalar(
        select(func.count()).select_from(Seat).where(
            Seat.status == SeatStatus.occupied
        )
    ) or 0

    available_seats: int = await db.scalar(
        select(func.count()).select_from(Seat).where(
            Seat.status == SeatStatus.available
        )
    ) or 0

    reserved_seats: int = await db.scalar(
        select(func.count()).select_from(Seat).where(
            Seat.status == SeatStatus.reserved
        )
    ) or 0

    # ── Active allocations (cross-check) ──────────────────────────────────────
    active_allocations: int = await db.scalar(
        select(func.count()).select_from(SeatAllocation).where(
            SeatAllocation.allocation_status == AllocationStatus.active
        )
    ) or 0

    # ── Occupancy % ───────────────────────────────────────────────────────────
    occupancy_pct: float = round(
        (occupied_seats / total_seats * 100) if total_seats > 0 else 0.0, 2
    )

    return {
        "employees": employee_count,
        "projects": project_count,
        "total_seats": total_seats,
        "occupied_seats": occupied_seats,
        "available_seats": available_seats,
        "reserved_seats": reserved_seats,
        "active_allocations": active_allocations,
        "occupancy_percentage": occupancy_pct,
    }
