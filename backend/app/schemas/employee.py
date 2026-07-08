from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import EmployeeStatus


class EmployeeCreate(BaseModel):
    employee_code: str
    name: str
    email: str
    department: str | None = None
    role: str | None = None
    joining_date: date
    project_id: UUID | None = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    name: str
    email: str
    department: str | None = None
    role: str |None = None
    joining_date: date
    project_id: UUID | None = None
    status: EmployeeStatus
    created_at: datetime