from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import SeatStatus


class SeatCreate(BaseModel):
    floor: int
    zone: str
    bay: str
    seat_number: str


class SeatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    floor: int
    zone: str
    bay: str
    seat_number: str
    status: SeatStatus
    created_at: datetime