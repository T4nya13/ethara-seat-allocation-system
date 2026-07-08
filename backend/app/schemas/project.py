from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    manager_name: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    manager_name: str | None
    status: ProjectStatus
    created_at: datetime