# Architecture — Ethara Seat Allocation & Project Mapping System

> Matches `docs/requirements.md` (built from the official assessment PDF). Supersedes
> any earlier architecture draft that included Building/Floor/Department tables —
> the real spec doesn't call for them.

## 1. Entity-Relationship Overview

```
Employee (many) --- (1) Project
Employee (1) --- (0..1 active) SeatAllocation --- (1) Seat
SeatAllocation (many) --- (1) Project      [project at time of allocation]
```

- An Employee has **one active project** (`employees.project_id`).
- A Seat has **at most one active allocation** at a time.
- `seat_allocations` is the append-only history table — releasing a seat sets
  `released_date` and flips status; it does not delete the row. This is what lets
  the dashboard and "who used to sit here" queries work, and it's an explicit
  business rule (#3) in the spec.

## 2. Database Schema (PostgreSQL / SQLAlchemy)

```sql
CREATE TABLE projects (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    description   TEXT,
    manager_name  VARCHAR(100),
    status        VARCHAR(20) NOT NULL DEFAULT 'active', -- active | closed
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE employees (
    id              SERIAL PRIMARY KEY,
    employee_code   VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    department      VARCHAR(100),          -- plain field, not a table (per spec)
    role            VARCHAR(100),
    joining_date    DATE NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'active', -- active | inactive
    project_id      INTEGER REFERENCES projects(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE seats (
    id            SERIAL PRIMARY KEY,
    floor         INTEGER NOT NULL,
    zone          VARCHAR(10) NOT NULL,
    bay           VARCHAR(10) NOT NULL,
    seat_number   VARCHAR(20) NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'available',
                  -- available | occupied | reserved | maintenance
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_seat_location UNIQUE (floor, zone, seat_number) -- rule #7
);

CREATE TABLE seat_allocations (
    id                  SERIAL PRIMARY KEY,
    employee_id         INTEGER NOT NULL REFERENCES employees(id),
    seat_id             INTEGER NOT NULL REFERENCES seats(id),
    project_id          INTEGER REFERENCES projects(id),
    allocation_status   VARCHAR(20) NOT NULL DEFAULT 'active', -- active | released
    allocation_date     TIMESTAMPTZ NOT NULL DEFAULT now(),
    released_date       TIMESTAMPTZ
);

-- Rule #1: one ACTIVE seat per employee
CREATE UNIQUE INDEX uq_active_seat_per_employee
    ON seat_allocations (employee_id)
    WHERE allocation_status = 'active';

-- Rule #2: one ACTIVE allocation per seat
CREATE UNIQUE INDEX uq_active_alloc_per_seat
    ON seat_allocations (seat_id)
    WHERE allocation_status = 'active';

CREATE TABLE audit_logs (
    id          SERIAL PRIMARY KEY,
    action      VARCHAR(50) NOT NULL,   -- e.g. 'seat_allocated', 'ai_query'
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Why partial unique indexes instead of app-level checks alone:** rules #1 and #2 are
the two constraints reviewers are most likely to test by hammering the API with
concurrent requests. A DB-level constraint makes double-booking impossible even under
race conditions; an API-level check alone can still race. Keep the API-level check
too (for a clean error message), but the DB index is the real guarantee.

`audit_logs` isn't in the spec's suggested schema but is cheap insurance — it's
useful for showing "the AI assistant actually logs and can be audited," which is a
nice detail for the AI Assistant section of the writeup.

## 3. API Surface

Matches `docs/requirements.md` Section 4 exactly — do not add extra top-level
resources beyond what's listed unless you have time to spare after the core is done.

| Method | Path | Notes |
|---|---|---|
| POST | `/employees` | 400 on duplicate email |
| GET | `/employees` | paginated, filterable by name/id/email/project/department |
| GET | `/employees/{id}` | includes current seat + project, if any |
| PUT | `/employees/{id}` | |
| DELETE | `/employees/{id}` | soft delete → status = inactive, releases seat |
| POST | `/projects` | |
| GET | `/projects` | |
| GET | `/projects/{id}/employees` | |
| POST | `/seats` | 400 on duplicate floor+zone+seat_number |
| GET | `/seats` | filterable by floor/zone/status |
| GET | `/seats/available` | |
| POST | `/seats/allocate` | body: `employee_id, seat_id` → 409 if either already active |
| POST | `/seats/release` | body: `seat_id` (or `employee_id`) → sets released_date |
| GET | `/dashboard/summary` | total/occupied/available/reserved seats, employee count |
| GET | `/dashboard/project-utilization` | seats per project |
| GET | `/dashboard/floor-utilization` | occupancy per floor |
| POST | `/ai/query` | see below — match request/response shape exactly |

## 4. AI Assistant

**Go with intent-classification + fallback keyword matching, not open NL-to-SQL.**
The spec explicitly allows a fallback keyword-based assistant if no AI API is
available, and even the "advanced" tier just asks for an LLM to help classify —
not free-form SQL generation against a 5,000-row PostgreSQL DB. Intent-based is
faster to build, fully testable, and can't be tricked into a bad query.

Contract (verbatim from spec):
```json
// POST /ai/query
{ "query": "Where is my seat? My email is amit@ethara.ai" }

// response
{ "answer": "You are allocated Floor 2, Zone B, Bay 4, Seat B4-23. Your project is Talos." }
```

Suggested intents to cover (matches spec's example questions):
1. `find_my_seat` — needs employee identifier (email or name) in the query
2. `find_employee_seat` — "where is employee X seated"
3. `project_assignment` — "which project is X assigned to"
4. `available_seats_by_floor` — "show available seats on floor N"
5. `nearby_employees` — "who is sitting near me" (same floor/zone/bay as requester)
6. `seat_utilization_by_project` — "how many seats occupied for project X"
7. `allocate_new_joiner` — "allocate a seat for new employee joining today"

Implementation: a small rules/regex or embedding-similarity classifier picks the
intent, extracts entities (name/email/floor/project), runs the matching
parameterized query, and formats the answer as a template string. Log every
query + matched intent + result to `audit_logs`. If you have time, wire an LLM
(Gemini free tier, since you're already in Antigravity) to do the classification
step instead of regex — same downstream logic either way, so it's a safe upgrade
to bolt on later without redoing anything.

## 5. Seed Data Plan

Meet or exceed spec minimums (Section 7 of requirements.md): 5,000 employees, 5
floors, 10 zones, 5,500 seats, 10+ projects, 500 available seats, 100 reserved, 50
employees pending allocation.

`seed.py` outline:
1. Create 10–11 projects (use the spec's sample names).
2. Create seats: 5 floors × 10 zones × ~110 seats/zone ≈ 5,500 seats. Assign ~500 as
   `available`, ~100 as `reserved`, rest start `available` and get filled by step 4.
3. Create 5,000 employees via Faker, distributed across projects and departments.
4. Allocate seats to ~4,950 employees (leave 50 unallocated = "pending", per spec),
   respecting the one-active-seat-per-employee/seat constraint.
5. Print row counts per table at the end — this is your proof-of-run for
   `AI_PROMPTS.md`, not just "it should have worked."

## 6. Build Order

1. Backend scaffold (FastAPI + SQLAlchemy + Alembic), boots with empty DB
2. Models + migrations for the 5 tables above
3. Seed script, run it, verify counts
4. Core CRUD (employees, projects) 
5. Seat allocate/release logic (this is where the constraints matter most)
6. Dashboard endpoints
7. `/ai/query` (intent-based)
8. Frontend pages against a working backend
9. Deploy (Railway/Render + Vercel)
10. Docs: README, AI_PROMPTS.md, screenshots, schema export

## 7. Deltas from the Original (email-only) Draft

For anyone comparing to the first architecture pass done before the PDF arrived:
- Dropped `Building` and `Floor` and `Department` as separate tables — the real
  schema is flatter (floor is just an int column on `seats`; department is a
  string column on `employees`).
- Dropped `NewJoiner` as its own table — "new joiner" is just an employee with no
  active `seat_allocations` row; the pending-allocation count is a query, not a
  stored state.
- Project count target changed from 80 → 10+ (spec gives 11 sample names).