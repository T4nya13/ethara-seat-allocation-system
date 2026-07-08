"""SeatAllocation model — the heart of the system.

``seat_allocations`` is an **append-only history table**.  Rules from the spec:

    Rule #1 — One employee can have only one ACTIVE seat.
    Rule #2 — One seat can have only one ACTIVE allocation.
    Rule #3 — Released seats become available again; history preserved.

These rules are enforced at TWO levels:
    1. DB level  — partial unique indexes (below) make double-booking
                   impossible even under concurrent requests.
    2. API level — explicit checks before INSERT for a clean 409 error.
                   (API layer comes later; indexes are the real guarantee.)

Fields (from requirements.md §2):
    id                — UUID PK
    employee_id       — FK → employees.id  (NOT NULL)
    seat_id           — FK → seats.id      (NOT NULL)
    project_id        — FK → projects.id   (nullable — project at allocation time,
                         captured as a snapshot in case the employee moves later)
    allocation_status — active | released
    allocation_date   — when the seat was allocated (server default = now())
    released_date     — set when the seat is released; NULL while active

Partial unique indexes (PostgreSQL native):
    uq_active_seat_per_employee  UNIQUE(employee_id) WHERE allocation_status='active'
    uq_active_alloc_per_seat     UNIQUE(seat_id)     WHERE allocation_status='active'

Additional indexes:
    ix_seat_alloc_employee_id   — employee history queries
    ix_seat_alloc_seat_id       — seat history queries
    ix_seat_alloc_status        — "active allocations" count queries (dashboard)
    ix_seat_alloc_date          — time-range queries / auditing
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import AllocationStatus

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.project import Project
    from app.models.seat import Seat


class SeatAllocation(UUIDPrimaryKeyMixin, Base):
    """A seat-assignment event.  Append-only; never deleted."""

    __tablename__ = "seat_allocations"

    # ── Foreign keys ──────────────────────────────────────────────────────────
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Employee who was allocated the seat",
    )
    seat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seats.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The seat that was allocated",
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Project the employee was on AT THE TIME of allocation (snapshot)",
    )

    # ── Domain columns ────────────────────────────────────────────────────────
    allocation_status: Mapped[AllocationStatus] = mapped_column(
        SAEnum(
            AllocationStatus,
            name="allocationstatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=AllocationStatus.active,
        server_default=AllocationStatus.active.value,
        index=True,
    )
    allocation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
        comment="When the seat was allocated",
    )
    released_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Set when the seat is released; NULL while allocation is active",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="allocations",
        lazy="select",
    )
    seat: Mapped["Seat"] = relationship(
        "Seat",
        back_populates="allocations",
        lazy="select",
    )
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="allocations",
        lazy="select",
    )

    # ── Table-level constraints & indexes ─────────────────────────────────────
    __table_args__ = (
        # ── Critical partial unique indexes ──────────────────────────────────
        # Rule #1: one ACTIVE seat per employee (DB-level guarantee)
        Index(
            "uq_active_seat_per_employee",
            "employee_id",
            unique=True,
            postgresql_where=text("allocation_status = 'active'"),
        ),
        # Rule #2: one ACTIVE allocation per seat (DB-level guarantee)
        Index(
            "uq_active_alloc_per_seat",
            "seat_id",
            unique=True,
            postgresql_where=text("allocation_status = 'active'"),
        ),
        # ── Performance indexes ───────────────────────────────────────────────
        Index("ix_seat_alloc_status", "allocation_status"),
        Index("ix_seat_alloc_date", "allocation_date"),
        # Compound index: fetch all active allocations for a project efficiently
        Index("ix_seat_alloc_project_status", "project_id", "allocation_status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SeatAllocation id={self.id} employee_id={self.employee_id} "
            f"seat_id={self.seat_id} status={self.allocation_status}>"
        )
