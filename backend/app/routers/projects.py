from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    project = Project(**project_data.model_dump())

    db.add(project)
    await db.flush()
    await db.refresh(project)

    return project


@router.get("/", response_model=list[ProjectResponse])
async def get_projects(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Project))
    projects = result.scalars().all()

    return projects