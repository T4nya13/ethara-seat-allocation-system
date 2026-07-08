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