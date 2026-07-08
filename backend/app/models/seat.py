"""Seat model.

``seats`` represents a physical desk location identified by
``(floor, zone, bay, seat_number)``.  No "Building" entity — architecture.md
explicitly removed it; floor is just an integer column.

Fields (from requirements.md §2):
    id           — UUID PK
    floor        — integer floor number (1–N)
    zone         — zone label within the floor (e.g. "A", "B", "Z10")
    bay          — bay within the zone (e.g. "Bay-1")
    seat_number  — seat label within the bay (e.g. "A1-05")
    status       — available | occupied | reserved | maintenance
    created_at   — server-set on INSERT

Constraints:
    UNIQUE(floor, zone, seat_number)   — rule #7 — no duplicate seat per location

Indexes:
    (floor, zone)   — the most common filter combination in the API
    status          — fast "available seats" queries
    floor           — floor-utilisation dashboard query

Note: ``status`` must be kept in sync with active ``SeatAllocation`` rows
by the service layer (not enforced here at the model level — that is
business logic coming later).
"""

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum as SAEnum, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SeatStatus

if TYPE_CHECKING:
    from app.models.seat_allocation import SeatAllocation


class Seat(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A physical seat / desk location."""

    __tablename__ = "seats"

    # ── Domain columns ────────────────────────────────────────────────────────
    floor: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Floor number (integer, e.g. 1–5)",
    )
    zone: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Zone label within the floor, e.g. 'A', 'B', 'Z10'",
    )
    bay: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Bay within the zone, e.g. 'Bay-1'",
    )
    seat_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Seat identifier within the bay, e.g. 'A1-05'",
    )
    status: Mapped[SeatStatus] = mapped_column(
        SAEnum(
            SeatStatus,
            name="seatstatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=SeatStatus.available,
        server_default=SeatStatus.available.value,
        # index defined explicitly in __table_args__ below
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    allocations: Mapped[List["SeatAllocation"]] = relationship(
        "SeatAllocation",
        back_populates="seat",
        lazy="select",
        order_by="SeatAllocation.allocation_date.desc()",
    )

    # ── Table-level constraints & indexes ─────────────────────────────────────
    __table_args__ = (
        # Rule #7: unique seat per floor/zone combination
        UniqueConstraint(
            "floor", "zone", "seat_number",
            name="uq_seat_location",
        ),
        # Compound index for the most common API filter: ?floor=2&zone=B
        Index("ix_seats_floor_zone", "floor", "zone"),
        # Individual floor index for the floor-utilisation dashboard
        Index("ix_seats_floor", "floor"),
        # Status index for "available seats" queries
        Index("ix_seats_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Seat id={self.id} floor={self.floor} zone={self.zone!r} "
            f"bay={self.bay!r} seat_number={self.seat_number!r} status={self.status}>"
        )
