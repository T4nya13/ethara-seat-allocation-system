from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.models.seat import Seat
from app.models.employee import Employee
from app.models.seat_allocation import SeatAllocation
from app.models.enums import SeatStatus, AllocationStatus

from app.schemas.seat import SeatCreate, SeatResponse
from app.schemas.seat_allocation import (
    SeatAllocationCreate,
    SeatAllocationResponse,
    SeatReleaseRequest,
)


router = APIRouter(
    prefix="/seats",
    tags=["Seats"]
)


@router.post("/", response_model=SeatResponse)
async def create_seat(
    seat_data: SeatCreate,
    db: AsyncSession = Depends(get_db)
):
    seat = Seat(**seat_data.model_dump())

    db.add(seat)
    await db.commit()
    await db.refresh(seat)

    return seat


@router.get("/", response_model=list[SeatResponse])
async def get_seats(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Seat))
    seats = result.scalars().all()

    return seats


@router.get("/available", response_model=list[SeatResponse])
async def get_available_seats(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Seat).where(Seat.status == SeatStatus.available)
    )

    seats = result.scalars().all()

    return seats


@router.post("/allocate", response_model=SeatAllocationResponse)
async def allocate_seat(
    allocation_data: SeatAllocationCreate,
    db: AsyncSession = Depends(get_db),
):
    # ── 1. Employee must exist ────────────────────────────────────────────────
    employee = await db.get(Employee, allocation_data.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    # ── 2. Seat must exist ────────────────────────────────────────────────────
    seat = await db.get(Seat, allocation_data.seat_id)
    if seat is None:
        raise HTTPException(status_code=404, detail="Seat not found")

    # ── 3. Seat must be available (not occupied / reserved / maintenance) ─────
    if seat.status != SeatStatus.available:
        raise HTTPException(
            status_code=409,
            detail=f"Seat is already {seat.status.value} and cannot be allocated",
        )

    # ── 4. Employee must not already hold an active allocation ────────────────
    existing_allocation = await db.scalar(
        select(SeatAllocation).where(
            SeatAllocation.employee_id == allocation_data.employee_id,
            SeatAllocation.allocation_status == AllocationStatus.active,
        )
    )
    if existing_allocation:
        raise HTTPException(
            status_code=409,
            detail="Employee already has an active seat allocation",
        )

    # ── 5. Create allocation + flip seat status ───────────────────────────────
    allocation = SeatAllocation(
        employee_id=allocation_data.employee_id,
        seat_id=allocation_data.seat_id,
        project_id=employee.project_id,
    )
    seat.status = SeatStatus.occupied
    db.add(allocation)

    try:
        await db.flush()
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Allocation conflict: another request may have allocated this seat or employee simultaneously",
        )

    await db.refresh(allocation)
    await db.refresh(seat)
    return allocation



@router.post("/release")
async def release_seat(
    release_data: SeatReleaseRequest,
    db: AsyncSession = Depends(get_db),
):
    allocation = await db.scalar(
        select(SeatAllocation).where(
            SeatAllocation.employee_id == release_data.employee_id,
            SeatAllocation.allocation_status == AllocationStatus.active,
        )
    )

    if allocation is None:
        raise HTTPException(
            status_code=404,
            detail="No active seat allocation found for this employee",
        )

    seat = await db.get(Seat, allocation.seat_id)

    if seat is None:
        raise HTTPException(
            status_code=404,
            detail="Seat not found",
        )

    allocation.allocation_status = AllocationStatus.released
    allocation.released_date = datetime.now(timezone.utc)
    seat.status = SeatStatus.available

    await db.commit()

    return {
        "message": "Seat released successfully"
    }