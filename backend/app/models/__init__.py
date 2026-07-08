"""models package — imports every model so SQLAlchemy's metadata registry
is populated.

Import order matters: models with no foreign keys first, then dependants.

    Project          (no FKs)
    Seat             (no FKs)
    Employee         (FK → Project)
    SeatAllocation   (FK → Employee, Seat, Project)
    AuditLog         (no FKs)

Alembic's ``env.py`` imports ``Base`` from ``app.database`` and this package
ensures all model classes are registered on ``Base.metadata`` before
``--autogenerate`` runs.
"""

from app.models.project import Project
from app.models.seat import Seat
from app.models.employee import Employee
from app.models.seat_allocation import SeatAllocation
from app.models.audit_log import AuditLog

__all__ = [
    "Project",
    "Seat",
    "Employee",
    "SeatAllocation",
    "AuditLog",
]
