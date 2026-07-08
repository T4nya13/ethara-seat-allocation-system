"""Employee model.

``employees`` holds the person record. It carries a *live* FK to the
employee's current project (``project_id``). It does **not** carry a seat FK
— seat history lives in ``seat_allocations`` (append-only, rule #3).

Fields (from requirements.md §2):
    id              — UUID PK
    employee_code   — unique opaque identifier (e.g. "EMP-00042")
    name            — display name
    email           — unique login / contact address (rule #6)
    department      — plain string column, not a FK table (per architecture.md)
    role            — job title / role string
    joining_date    — DATE of joining (used for new-joiner priority logic)
    status          — active | inactive  (soft-delete via status flip)
    project_id      — FK → projects.id  (nullable: joiners before assignment)
    created_at      — server-set on INSERT
    updated_at      — refreshed on every UPDATE

Relationships:
    project         — current Project object (many-to-one)
    allocations     — full seat-allocation history (one-to-many)
                      Active allocation = allocation where status == 'active'.

Constraints / indexes (besides PK):
    UNIQUE(email)          — rule #6
    UNIQUE(employee_code)  — natural key
    INDEX(project_id)      — fast "employees on project X" queries
    INDEX(department)      — filterable by the API
    INDEX(status)          — filter active employees quickly
    INDEX(joining_date)    — seed / new-joiner queries
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import EmployeeStatus

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.seat_allocation import SeatAllocation


class Employee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A person who can be assigned to a project and allocated a seat."""

    __tablename__ = "employees"

    # ── Domain columns ────────────────────────────────────────────────────────
    employee_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Opaque human-readable ID, e.g. EMP-00042",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,    # rule #6 — enforced at DB level
        index=True,     # AI assistant looks up employees by email
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Plain string; not a separate table (per architecture.md)",
    )
    role: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    joining_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date of joining; used to identify new joiners (no active allocation)",
    )
    status: Mapped[EmployeeStatus] = mapped_column(
        SAEnum(
            EmployeeStatus,
            name="employeestatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=EmployeeStatus.active,
        server_default=EmployeeStatus.active.value,
        index=True,
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Current project; NULL means unassigned/new joiner",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="employees",
        lazy="select",
    )
    allocations: Mapped[List["SeatAllocation"]] = relationship(
        "SeatAllocation",
        back_populates="employee",
        lazy="select",
        order_by="SeatAllocation.allocation_date.desc()",
    )

    # ── Table-level constraints ────────────────────────────────────────────────
    __table_args__ = (
        # Composite index to speed up name-based searches (LIKE '%query%')
        Index("ix_employees_name", "name"),
        # Documented in table_args to be visible in Alembic DDL output
        UniqueConstraint("email", name="uq_employees_email"),
        UniqueConstraint("employee_code", name="uq_employees_code"),
    )

    def __repr__(self) -> str:
        return (
            f"<Employee id={self.id} code={self.employee_code!r} "
            f"email={self.email!r} status={self.status}>"
        )
