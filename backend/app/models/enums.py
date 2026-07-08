"""Shared enums for all SQLAlchemy models.

All enums inherit `str` so that:
- FastAPI can serialise them directly to JSON strings.
- SQLAlchemy stores/retrieves the `.value` without extra coercion.
- Comparisons like `status == 'active'` work without importing the enum class.
"""

import enum


class ProjectStatus(str, enum.Enum):
    """Lifecycle state of a project."""

    active = "active"
    closed = "closed"


class EmployeeStatus(str, enum.Enum):
    """Employment status.  Soft-delete uses ``inactive`` (never hard delete)."""

    active = "active"
    inactive = "inactive"


class SeatStatus(str, enum.Enum):
    """Physical state of a seat.

    Must be kept in sync with ``SeatAllocation.allocation_status``:
    - ``available``   — no active allocation, open for assignment.
    - ``occupied``    — has an active ``SeatAllocation`` row.
    - ``reserved``    — held for future use; cannot be allocated without
                        explicitly changing status first (rule #4).
    - ``maintenance`` — temporarily out of service.
    """

    available = "available"
    occupied = "occupied"
    reserved = "reserved"
    maintenance = "maintenance"


class AllocationStatus(str, enum.Enum):
    """State of a seat-allocation record.

    ``seat_allocations`` is append-only (rule #3).  A seat is released by
    setting this to ``released`` and stamping ``released_date`` — the row
    is never deleted so the history is preserved.
    """

    active = "active"
    released = "released"
