from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.employee import Employee
from app.models.seat import Seat
from app.models.seat_allocation import SeatAllocation
from app.models.enums import AllocationStatus, EmployeeStatus, SeatStatus
from app.schemas.employee import EmployeeCreate, EmployeeResponse


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db)
):
    employee = Employee(**employee_data.model_dump())

    db.add(employee)
    await db.flush()
    await db.commit()
    await db.refresh(employee)

    return employee


@router.get("/", response_model=list[EmployeeResponse])
async def get_employees(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Employee))
    employees = result.scalars().all()

    return employees


@router.delete("/{employee_id}", status_code=200)
async def deactivate_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an employee.

    - Sets employee.status = inactive (never hard-deletes the row).
    - If the employee has an active seat allocation, releases it:
        * allocation_status → released, released_date stamped
        * seat.status → available
    """
    # ── 1. Fetch employee ─────────────────────────────────────────────────────
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.status == EmployeeStatus.inactive:
        raise HTTPException(status_code=409, detail="Employee is already inactive")

    # ── 2. Release active seat allocation if one exists ───────────────────────
    active_allocation = await db.scalar(
        select(SeatAllocation).where(
            SeatAllocation.employee_id == employee_id,
            SeatAllocation.allocation_status == AllocationStatus.active,
        )
    )

    if active_allocation is not None:
        seat = await db.get(Seat, active_allocation.seat_id)

        active_allocation.allocation_status = AllocationStatus.released
        active_allocation.released_date = datetime.now(timezone.utc)

        if seat is not None:
            seat.status = SeatStatus.available

    # ── 3. Mark employee inactive ─────────────────────────────────────────────
    employee.status = EmployeeStatus.inactive

    await db.commit()

    return {
        "message": f"Employee {employee.name!r} deactivated successfully",
        "seat_released": active_allocation is not None,
    }