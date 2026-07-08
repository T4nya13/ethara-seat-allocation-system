"""Project model.

``projects`` is the root table in the hierarchy — created before employees
because ``employees.project_id`` references it.

Fields (from requirements.md §2):
    id            — UUID PK
    name          — unique project identifier (e.g. "Indigo", "Serfy")
    description   — optional long text
    manager_name  — plain string; no User/Auth model in scope
    status        — active | closed  (soft-delete via status change)
    created_at    — server-set on INSERT

Relationships:
    employees      — all employees currently assigned to this project
    allocations    — all seat-allocation records that captured this project
                     at allocation time (may include former employees)
"""

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum as SAEnum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ProjectStatus

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.seat_allocation import SeatAllocation


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A project that employees are assigned to."""

    __tablename__ = "projects"

    # ── Domain columns ────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,       # business-rule: no duplicate project names
        index=True,        # fast look-ups by name
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    manager_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(
            ProjectStatus,
            name="projectstatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ProjectStatus.active,
        server_default=ProjectStatus.active.value,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="project",
        lazy="select",
    )
    allocations: Mapped[List["SeatAllocation"]] = relationship(
        "SeatAllocation",
        back_populates="project",
        lazy="select",
    )

    # ── Table-level args ──────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_projects_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r} status={self.status}>"
