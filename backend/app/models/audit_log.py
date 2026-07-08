"""AuditLog model.

A write-only ledger for significant events.  Not required by the spec's
schema, but called out in architecture.md (§2) as "cheap insurance":

    "useful for showing 'the AI assistant actually logs and can be audited',
     which is a nice detail for the AI Assistant section of the writeup."

Fields:
    id         — UUID PK
    action     — short event type, e.g. 'seat_allocated', 'seat_released',
                 'employee_deactivated', 'ai_query'
    payload    — JSONB blob with context specific to the action
    created_at — server-set on INSERT

No ``updated_at`` — audit rows are immutable by design.

Note: ``payload`` is typed as ``dict | None`` in Python; SQLAlchemy maps it
to PostgreSQL ``JSONB`` (fastest binary JSON type).
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Immutable event record for audit and debugging."""

    __tablename__ = "audit_logs"

    # ── Domain columns ────────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Event type, e.g. 'seat_allocated', 'ai_query'",
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Contextual data for the event (JSONB)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When the event occurred (server-set)",
    )

    # ── Table-level indexes ───────────────────────────────────────────────────
    __table_args__ = (
        # Compound index for "show all ai_query events in last 24h" queries
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r} created_at={self.created_at}>"
