from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AllocationStatus


class SeatAllocationCreate(BaseModel):
    employee_id: UUID
    seat_id: UUID


class SeatAllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    seat_id: UUID
    project_id: UUID | None = None
    allocation_status: AllocationStatus
    allocation_date: datetime
    released_date: datetime | None = None