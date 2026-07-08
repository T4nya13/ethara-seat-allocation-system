"""Reusable mixins shared by all models.

Provides:
- ``UUIDPrimaryKeyMixin``  — UUID v4 primary key (not SERIAL).
- ``TimestampMixin``       — ``created_at`` + ``updated_at`` with server defaults.

Using UUID PKs instead of SERIAL because:
- IDs are safe to expose in URLs without leaking row counts.
- Works across distributed / replicated write paths.
- Matches modern FastAPI / Pydantic conventions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Adds a UUID v4 primary key column named ``id``."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        # Store as native UUID in PostgreSQL; falls back to CHAR(32) on SQLite.
        sort_order=-100,  # renders before all other columns in DDL
    )


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns with UTC defaults.

    - ``created_at`` is set by the DB server on INSERT (``server_default``).
    - ``updated_at`` is set by the DB server on INSERT and refreshed on every
      UPDATE via the Python-side ``onupdate`` callable (emits ``func.now()``).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=100,  # renders after all domain columns in DDL
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        sort_order=101,
    )
