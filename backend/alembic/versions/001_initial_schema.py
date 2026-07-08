"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-07-08

Creates all five tables from scratch on an empty database:
    - projects
    - seats
    - employees         (FK → projects)
    - seat_allocations  (FK → employees, seats, projects)
    - audit_logs

Includes:
    - 4 native PostgreSQL ENUM types
    - All unique constraints and indexes
    - Two partial unique indexes enforcing business rules #1 and #2

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── PostgreSQL enum types ─────────────────────────────────────────────────────
# Declared here so we can create them before tables and drop them on downgrade.

projectstatus = postgresql.ENUM(
    "active", "closed",
    name="projectstatus",
    create_type=False,
)
employeestatus = postgresql.ENUM(
    "active", "inactive",
    name="employeestatus",
    create_type=False,
)
seatstatus = postgresql.ENUM(
    "available", "occupied", "reserved", "maintenance",
    name="seatstatus",
    create_type=False,
)
allocationstatus = postgresql.ENUM(
    "active", "released",
    name="allocationstatus",
    create_type=False,
)


def upgrade() -> None:
    # ── 1. Create ENUM types ─────────────────────────────────────────────────
    projectstatus.create(op.get_bind(), checkfirst=True)
    employeestatus.create(op.get_bind(), checkfirst=True)
    seatstatus.create(op.get_bind(), checkfirst=True)
    allocationstatus.create(op.get_bind(), checkfirst=True)

    # ── 2. projects ──────────────────────────────────────────────────────────
    # Created first — employees and seat_allocations reference it.
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("manager_name", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("active", "closed", name="projectstatus", create_type=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Unique index on name (also enforces uniqueness)
    op.create_index("ix_projects_name", "projects", ["name"], unique=True)
    # Status index for active/closed filtering
    op.create_index("ix_projects_status", "projects", ["status"], unique=False)

    # ── 3. seats ─────────────────────────────────────────────────────────────
    # Created before employees — seat_allocations references both.
    op.create_table(
        "seats",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("zone", sa.String(length=10), nullable=False),
        sa.Column("bay", sa.String(length=10), nullable=False),
        sa.Column("seat_number", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "available", "occupied", "reserved", "maintenance",
                name="seatstatus",
                create_type=False,
            ),
            server_default="available",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        # Rule #7: no duplicate seat number on same floor + zone
        sa.UniqueConstraint("floor", "zone", "seat_number", name="uq_seat_location"),
    )
    op.create_index("ix_seats_floor", "seats", ["floor"], unique=False)
    op.create_index("ix_seats_floor_zone", "seats", ["floor", "zone"], unique=False)
    op.create_index("ix_seats_status", "seats", ["status"], unique=False)

    # ── 4. employees ─────────────────────────────────────────────────────────
    op.create_table(
        "employees",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employee_code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("active", "inactive", name="employeestatus", create_type=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        # Rule #6: no duplicate email addresses
        sa.UniqueConstraint("email", name="uq_employees_email"),
        sa.UniqueConstraint("employee_code", name="uq_employees_code"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_employees_project_id",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_employees_department", "employees", ["department"], unique=False)
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"], unique=True)
    op.create_index("ix_employees_joining_date", "employees", ["joining_date"], unique=False)
    op.create_index("ix_employees_name", "employees", ["name"], unique=False)
    op.create_index("ix_employees_project_id", "employees", ["project_id"], unique=False)
    op.create_index("ix_employees_status", "employees", ["status"], unique=False)

    # ── 5. seat_allocations ───────────────────────────────────────────────────
    op.create_table(
        "seat_allocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("seat_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column(
            "allocation_status",
            postgresql.ENUM("active", "released", name="allocationstatus", create_type=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "allocation_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("released_date", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_seat_alloc_employee_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seat_id"],
            ["seats.id"],
            name="fk_seat_alloc_seat_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_seat_alloc_project_id",
            ondelete="SET NULL",
        ),
    )
    # Regular performance indexes
    op.create_index(
        "ix_seat_alloc_employee_id", "seat_allocations", ["employee_id"], unique=False
    )
    op.create_index(
        "ix_seat_alloc_seat_id", "seat_allocations", ["seat_id"], unique=False
    )
    op.create_index(
        "ix_seat_alloc_status", "seat_allocations", ["allocation_status"], unique=False
    )
    op.create_index(
        "ix_seat_alloc_date", "seat_allocations", ["allocation_date"], unique=False
    )
    op.create_index(
        "ix_seat_alloc_project_status",
        "seat_allocations",
        ["project_id", "allocation_status"],
        unique=False,
    )
    # ── Critical partial unique indexes ──────────────────────────────────────
    # Rule #1: one ACTIVE seat per employee
    op.create_index(
        "uq_active_seat_per_employee",
        "seat_allocations",
        ["employee_id"],
        unique=True,
        postgresql_where=sa.text("allocation_status = 'active'"),
    )
    # Rule #2: one ACTIVE allocation per seat
    op.create_index(
        "uq_active_alloc_per_seat",
        "seat_allocations",
        ["seat_id"],
        unique=True,
        postgresql_where=sa.text("allocation_status = 'active'"),
    )

    # ── 6. audit_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)
    op.create_index(
        "ix_audit_logs_action_created",
        "audit_logs",
        ["action", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    # ── Drop in reverse order (child tables first) ────────────────────────────

    # seat_allocations indexes
    op.drop_index("uq_active_alloc_per_seat", table_name="seat_allocations")
    op.drop_index("uq_active_seat_per_employee", table_name="seat_allocations")
    op.drop_index("ix_seat_alloc_project_status", table_name="seat_allocations")
    op.drop_index("ix_seat_alloc_date", table_name="seat_allocations")
    op.drop_index("ix_seat_alloc_status", table_name="seat_allocations")
    op.drop_index("ix_seat_alloc_seat_id", table_name="seat_allocations")
    op.drop_index("ix_seat_alloc_employee_id", table_name="seat_allocations")
    op.drop_table("seat_allocations")

    # employees indexes
    op.drop_index("ix_employees_status", table_name="employees")
    op.drop_index("ix_employees_project_id", table_name="employees")
    op.drop_index("ix_employees_name", table_name="employees")
    op.drop_index("ix_employees_joining_date", table_name="employees")
    op.drop_index("ix_employees_employee_code", table_name="employees")
    op.drop_index("ix_employees_email", table_name="employees")
    op.drop_index("ix_employees_department", table_name="employees")
    op.drop_table("employees")

    # seats indexes
    op.drop_index("ix_seats_status", table_name="seats")
    op.drop_index("ix_seats_floor_zone", table_name="seats")
    op.drop_index("ix_seats_floor", table_name="seats")
    op.drop_table("seats")

    # projects indexes
    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_name", table_name="projects")
    op.drop_table("projects")

    # audit_logs
    op.drop_index("ix_audit_logs_action_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")

    # ── Drop ENUM types last ──────────────────────────────────────────────────
    allocationstatus.drop(op.get_bind(), checkfirst=True)
    seatstatus.drop(op.get_bind(), checkfirst=True)
    employeestatus.drop(op.get_bind(), checkfirst=True)
    projectstatus.drop(op.get_bind(), checkfirst=True)
