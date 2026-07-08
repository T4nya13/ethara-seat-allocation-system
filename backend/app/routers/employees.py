from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.employee import Employee
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