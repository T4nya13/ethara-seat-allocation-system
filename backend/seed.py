"""seed.py — Populate the Ethara database with realistic baseline data.

Target metrics:
    Projects  : 11 (named, realistic)
    Employees : ~5,000
    Seats     : 5 floors × 10 zones × 12 bays × 10 seats = 6,000 physical seats
    Allocations: ~80% of active employees get a seat

Usage (from backend/ directory):
    python seed.py                   # uses SYNC_DATABASE_URL from .env
    python seed.py --employees 500   # smaller run for dev
    python seed.py --dry-run         # print stats, don't write to DB

The script is idempotent — it checks for existing data and skips if the
table already has rows, so it is safe to re-run after a failed partial seed.
"""

import argparse
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

# ── Load .env before importing anything from app/ ────────────────────────────
from dotenv import load_dotenv
load_dotenv()

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

# ── Patch sys.path so app.* imports resolve ──────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from app.models.project import Project
from app.models.employee import Employee
from app.models.seat import Seat
from app.models.seat_allocation import SeatAllocation
from app.models.enums import (
    AllocationStatus, EmployeeStatus, ProjectStatus, SeatStatus
)
from app.database import Base

try:
    from faker import Faker
except ImportError:
    print("ERROR: faker is not installed. Run: pip install faker")
    sys.exit(1)


# ── Config ────────────────────────────────────────────────────────────────────
SYNC_URL = os.environ.get("SYNC_DATABASE_URL") or os.environ.get(
    "DATABASE_URL", ""
).replace("postgresql+asyncpg://", "postgresql+psycopg2://")

PROJECTS = [
    "Project Atlas",
    "Project Helios",
    "Project Orion",
    "Project Nova",
    "Project Titan",
    "Project Apex",
    "Project Nexus",
    "Project Horizon",
    "Project Zenith",
    "Project Aurora",
    "Project Vanguard",
]

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Data Science",
    "Finance", "Legal", "HR", "Operations", "Marketing", "DevOps",
]

FLOORS = [1, 2, 3, 4, 5]
ZONES = [chr(c) for c in range(ord("A"), ord("K"))]   # A-J (10 zones)
BAYS_PER_ZONE = [f"Bay-{i}" for i in range(1, 13)]    # Bay-1 ... Bay-12 (12 bays)
# seat_number embeds the bay so it is unique within (floor, zone)
# e.g. "B01-S01" = Bay-1, Seat-01 ... "B12-S10" = Bay-12, Seat-10
# Total per floor: 10 zones x 12 bays x 10 seats = 1200 seats/floor, 6000 total
SEATS_PER_BAY = [f"S{i:02d}" for i in range(1, 11)]   # S01...S10 (10 seats per bay)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _random_date(start_year: int = 2018, end_year: int = 2025) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def _chunk(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


# ── Seeding functions ─────────────────────────────────────────────────────────
def seed_projects(session: Session) -> list[Project]:
    existing = session.scalar(select(func.count()).select_from(Project))
    if existing:
        print(f"  Projects already seeded ({existing} rows) — skipping.")
        return list(session.scalars(select(Project)).all())

    fake = Faker()
    projects = []
    for name in PROJECTS:
        projects.append(
            Project(
                name=name,
                description=fake.sentence(nb_words=10),
                manager_name=fake.name(),
                status=ProjectStatus.active,
            )
        )
    session.add_all(projects)
    session.commit()
    for p in projects:
        session.refresh(p)
    print(f"  Created {len(projects)} projects.")
    return projects


def seed_seats(session: Session) -> list[Seat]:
    existing = session.scalar(select(func.count()).select_from(Seat))
    if existing:
        print(f"  Seats already seeded ({existing} rows) -- skipping.")
        return list(session.scalars(select(Seat)).all())

    rows = []
    for floor in FLOORS:
        for zone in ZONES:
            for bay_idx, bay in enumerate(BAYS_PER_ZONE, start=1):
                for seat_num in SEATS_PER_BAY:
                    # seat_number = "B01-S01" ... "B12-S10"
                    # unique within (floor, zone) as required by uq_seat_location
                    seat_number = f"B{bay_idx:02d}-{seat_num}"
                    rows.append({
                        "id": str(uuid.uuid4()),
                        "floor": floor,
                        "zone": zone,
                        "bay": bay,
                        "seat_number": seat_number,
                        "status": SeatStatus.available.value,
                    })

    # Core INSERT ON CONFLICT DO NOTHING — idempotent, safe after partial failures
    seat_table = Seat.__table__
    for chunk in _chunk(rows, 500):
        session.execute(
            seat_table.insert().values(chunk).prefix_with("OR IGNORE")
            if session.bind and session.bind.dialect.name == "sqlite"
            else sa.dialects.postgresql.insert(seat_table)
              .values(chunk)
              .on_conflict_do_nothing(constraint="uq_seat_location")
        )
        session.commit()

    total = session.scalar(select(func.count()).select_from(Seat)) or 0
    print(
        f"  Created {total} seats "
        f"({len(FLOORS)} floors x {len(ZONES)} zones x "
        f"{len(BAYS_PER_ZONE)} bays x {len(SEATS_PER_BAY)} seats)."
    )
    return list(session.scalars(select(Seat)).all())



def seed_employees(
    session: Session,
    projects: list[Project],
    target_count: int = 5_000,
) -> list[Employee]:
    existing = session.scalar(select(func.count()).select_from(Employee))
    if existing:
        print(f"  Employees already seeded ({existing} rows) — skipping.")
        return list(session.scalars(select(Employee)).all())

    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    employees = []
    used_emails: set[str] = set()
    used_codes: set[str] = set()
    counter = 1

    while len(employees) < target_count:
        first = fake.first_name()
        last = fake.last_name()
        base_email = f"{first.lower()}.{last.lower()}@ethara.com"
        # Deduplicate email
        email = base_email
        suffix = 1
        while email in used_emails:
            email = f"{first.lower()}.{last.lower()}{suffix}@ethara.com"
            suffix += 1
        used_emails.add(email)

        code = f"EMP-{counter:05d}"
        while code in used_codes:
            counter += 1
            code = f"EMP-{counter:05d}"
        used_codes.add(code)
        counter += 1

        project = random.choice(projects) if random.random() > 0.05 else None

        employees.append(
            Employee(
                employee_code=code,
                name=f"{first} {last}",
                email=email,
                department=random.choice(DEPARTMENTS),
                role=fake.job()[:100],
                joining_date=_random_date(),
                status=EmployeeStatus.active,
                project_id=project.id if project else None,
            )
        )

    for chunk in _chunk(employees, 200):
        session.add_all(chunk)
        session.flush()
    session.commit()
    print(f"  Created {len(employees)} employees.")
    return employees


def seed_allocations(
    session: Session,
    employees: list[Employee],
    seats: list[Seat],
    allocation_rate: float = 0.80,
) -> None:
    existing = session.scalar(select(func.count()).select_from(SeatAllocation))
    if existing:
        print(f"  Allocations already seeded ({existing} rows) — skipping.")
        return

    random.seed(42)

    # Pick employees to allocate (80% of active)
    active_employees = [e for e in employees if e.status == EmployeeStatus.active]
    to_allocate = random.sample(
        active_employees,
        k=min(int(len(active_employees) * allocation_rate), len(seats)),
    )
    # Shuffle seats so allocation is spread across floors/zones
    available_seats = [s for s in seats if s.status == SeatStatus.available]
    random.shuffle(available_seats)

    allocations = []
    seat_iter = iter(available_seats)

    for employee in to_allocate:
        try:
            seat = next(seat_iter)
        except StopIteration:
            break

        alloc_date = datetime(
            *_random_date(2022, 2025).timetuple()[:3], tzinfo=timezone.utc
        )
        allocations.append(
            SeatAllocation(
                employee_id=employee.id,
                seat_id=seat.id,
                project_id=employee.project_id,
                allocation_status=AllocationStatus.active,
                allocation_date=alloc_date,
            )
        )
        seat.status = SeatStatus.occupied

    for chunk in _chunk(allocations, 200):
        session.add_all(chunk)
        session.flush()
    session.commit()
    print(f"  Created {len(allocations)} seat allocations "
          f"({len(allocations) / max(len(active_employees), 1) * 100:.1f}% occupancy).")


# ── Main ──────────────────────────────────────────────────────────────────────
def main(employee_count: int = 5_000, dry_run: bool = False) -> None:
    if not SYNC_URL:
        print("ERROR: SYNC_DATABASE_URL is not set in .env")
        sys.exit(1)

    if dry_run:
        total_seats = (
            len(FLOORS) * len(ZONES) * len(BAYS_PER_ZONE) * len(SEATS_PER_BAY)
        )
        print("=== DRY RUN — no DB writes ===")
        print(f"  Projects  : {len(PROJECTS)}")
        print(f"  Employees : {employee_count}")
        print(f"  Seats     : {total_seats}")
        print(f"  Allocs    : ~{int(employee_count * 0.80)} (80% rate)")
        return

    print(f"Connecting to: {SYNC_URL[:60]}...")
    engine = create_engine(SYNC_URL, echo=False, pool_pre_ping=True)

    with Session(engine) as session:
        print("\n[1/4] Projects")
        projects = seed_projects(session)

        print("\n[2/4] Seats")
        seats = seed_seats(session)

        print("\n[3/4] Employees")
        employees = seed_employees(session, projects, target_count=employee_count)

        print("\n[4/4] Seat Allocations")
        seed_allocations(session, employees, seats)

    print("\nSeed complete. All data loaded successfully.")
    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Ethara database.")
    parser.add_argument(
        "--employees", type=int, default=5_000,
        help="Number of employees to create (default: 5000)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print stats without writing to DB"
    )
    args = parser.parse_args()
    main(employee_count=args.employees, dry_run=args.dry_run)
