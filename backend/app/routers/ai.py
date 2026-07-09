"""AI assistant router — intent-based natural language query endpoint.

POST /ai/query
    Accepts: { "query": "<free text>" }
    Returns: { "answer": "<natural language response>" }

Strategy: regex-based intent classification + parameterised DB queries.
No external LLM required (keyword fallback is explicitly allowed by the spec).

Supported intents (from architecture.md §4):
    1. find_seat_by_email       — "where is my seat … email is x@y.com"
    2. find_seat_by_name        — "where is [Name] seated"
    3. project_assignment       — "which project is [Name/email] assigned to"
    4. available_seats_by_floor — "show available seats on floor N"
    5. seat_utilization_by_project — "how many seats occupied for project X"
    6. unknown                  — fallback with help text

Every query + matched intent + answer is written to audit_logs.
"""

import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.project import Project
from app.models.seat import Seat
from app.models.seat_allocation import SeatAllocation
from app.models.enums import AllocationStatus, SeatStatus

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


# ── Pydantic I/O ──────────────────────────────────────────────────────────────
class AIQueryRequest(BaseModel):
    query: str


class AIQueryResponse(BaseModel):
    answer: str


# ── Regex patterns ────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_FLOOR_RE = re.compile(r"\bfloor\s*(\d+)\b", re.IGNORECASE)
_PROJECT_RE = re.compile(
    r"project\s+([A-Za-z][A-Za-z0-9_\- ]+?)(?:\s*\?|$|\.|\s+for|\s+on)", re.IGNORECASE
)


# ── Helper: log to audit_logs ─────────────────────────────────────────────────
async def _log(db: AsyncSession, intent: str, query: str, answer: str) -> None:
    log = AuditLog(
        action="ai_query",
        payload={"intent": intent, "query": query, "answer": answer},
    )
    db.add(log)
    await db.commit()


# ── Helper: active-allocation lookup ─────────────────────────────────────────
async def _get_active_allocation(db: AsyncSession, employee: Employee):
    """Return (SeatAllocation, Seat, Project | None) for the employee's active seat."""
    alloc = await db.scalar(
        select(SeatAllocation).where(
            SeatAllocation.employee_id == employee.id,
            SeatAllocation.allocation_status == AllocationStatus.active,
        )
    )
    if alloc is None:
        return None, None, None

    seat = await db.get(Seat, alloc.seat_id)
    project = await db.get(Project, alloc.project_id) if alloc.project_id else None
    return alloc, seat, project


# ── Helper: format seat location ─────────────────────────────────────────────
def _fmt_seat(seat: Seat) -> str:
    return f"Floor {seat.floor}, Zone {seat.zone}, Bay {seat.bay}, Seat {seat.seat_number}"


# ── Main endpoint ─────────────────────────────────────────────────────────────
@router.post("/query", response_model=AIQueryResponse)
async def ai_query(
    body: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> AIQueryResponse:
    q = body.query.strip()
    q_lower = q.lower()
    intent = "unknown"
    answer = ""

    # ── Intent 1: find seat by email ─────────────────────────────────────────
    email_match = _EMAIL_RE.search(q)
    if email_match and any(kw in q_lower for kw in ("seat", "where", "sitting", "located")):
        intent = "find_seat_by_email"
        email = email_match.group(0).lower()

        employee = await db.scalar(
            select(Employee).where(Employee.email == email)
        )
        if employee is None:
            answer = f"No employee found with email '{email}'."
        else:
            _, seat, project = await _get_active_allocation(db, employee)
            if seat is None:
                answer = f"{employee.name} does not currently have an active seat allocation."
            else:
                proj_str = f" They are assigned to project {project.name}." if project else ""
                answer = f"{employee.name} is seated at {_fmt_seat(seat)}.{proj_str}"

    # ── Intent 2: find seat by name ──────────────────────────────────────────
    elif any(kw in q_lower for kw in ("where is", "seat of", "sitting", "seated")):
        intent = "find_seat_by_name"
        # Extract name — everything after "where is" / "seat of" etc.
        name_match = re.search(
            r"(?:where\s+is|seat\s+of|where\s+does)\s+([A-Z][a-zA-Z\s]+?)(?:\s+sit|\s+seat|\?|$)",
            q, re.IGNORECASE
        )
        if name_match:
            name_fragment = name_match.group(1).strip()
            employee = await db.scalar(
                select(Employee).where(
                    Employee.name.ilike(f"%{name_fragment}%")
                )
            )
            if employee is None:
                answer = f"No employee found matching name '{name_fragment}'."
            else:
                _, seat, project = await _get_active_allocation(db, employee)
                if seat is None:
                    answer = f"{employee.name} does not currently have an active seat allocation."
                else:
                    proj_str = f" Assigned to project {project.name}." if project else ""
                    answer = f"{employee.name} is seated at {_fmt_seat(seat)}.{proj_str}"
        else:
            answer = "Please provide an employee name or email so I can locate their seat."

    # ── Intent 3: project assignment ─────────────────────────────────────────
    elif any(kw in q_lower for kw in ("which project", "what project", "assigned to")):
        intent = "project_assignment"
        employee = None

        if email_match:
            employee = await db.scalar(
                select(Employee).where(Employee.email == email_match.group(0).lower())
            )
        else:
            name_match = re.search(r"is\s+([A-Z][a-zA-Z\s]+?)\s+assigned", q, re.IGNORECASE)
            if name_match:
                employee = await db.scalar(
                    select(Employee).where(
                        Employee.name.ilike(f"%{name_match.group(1).strip()}%")
                    )
                )

        if employee is None:
            answer = "Please provide an employee name or email to look up their project assignment."
        elif employee.project_id is None:
            answer = f"{employee.name} is not currently assigned to any project."
        else:
            project = await db.get(Project, employee.project_id)
            answer = (
                f"{employee.name} is assigned to project {project.name}."
                if project else f"{employee.name} has a project_id but the project was not found."
            )

    # ── Intent 4: available seats by floor ───────────────────────────────────
    elif any(kw in q_lower for kw in ("available seat", "free seat", "open seat")):
        intent = "available_seats_by_floor"
        floor_match = _FLOOR_RE.search(q)

        if floor_match:
            floor_num = int(floor_match.group(1))
            count: int = await db.scalar(
                select(func.count()).select_from(Seat).where(
                    Seat.floor == floor_num,
                    Seat.status == SeatStatus.available,
                )
            ) or 0
            answer = f"There are {count} available seat(s) on Floor {floor_num}."
        else:
            count = await db.scalar(
                select(func.count()).select_from(Seat).where(
                    Seat.status == SeatStatus.available,
                )
            ) or 0
            answer = f"There are {count} available seats across all floors."

    # ── Intent 5: seat utilisation by project ────────────────────────────────
    elif any(kw in q_lower for kw in ("how many", "occupied", "utilization", "utilisation")):
        intent = "seat_utilization_by_project"
        proj_match = _PROJECT_RE.search(q)

        if proj_match:
            proj_name = proj_match.group(1).strip()
            project = await db.scalar(
                select(Project).where(Project.name.ilike(f"%{proj_name}%"))
            )
            if project is None:
                answer = f"No project found matching '{proj_name}'."
            else:
                count: int = await db.scalar(
                    select(func.count()).select_from(SeatAllocation).where(
                        SeatAllocation.project_id == project.id,
                        SeatAllocation.allocation_status == AllocationStatus.active,
                    )
                ) or 0
                answer = f"Project {project.name} has {count} actively occupied seat(s)."
        else:
            # Overall occupied count
            total_occupied: int = await db.scalar(
                select(func.count()).select_from(Seat).where(
                    Seat.status == SeatStatus.occupied,
                )
            ) or 0
            answer = f"There are {total_occupied} occupied seats across all projects."

    # ── Fallback ──────────────────────────────────────────────────────────────
    else:
        intent = "unknown"
        answer = (
            "I can help you with: finding where an employee is seated, "
            "checking which project someone is assigned to, "
            "listing available seats on a specific floor, or "
            "checking how many seats are occupied for a project. "
            "Try asking: \"Where is John Smith seated?\" or "
            "\"Show available seats on Floor 3.\""
        )

    # ── Log every query ───────────────────────────────────────────────────────
    await _log(db, intent, q, answer)

    return AIQueryResponse(answer=answer)
