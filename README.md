# Ethara — Seat Allocation & Project Mapping System

> **Production-grade workspace intelligence platform** for managing physical seat allocation, project assignments, and workforce distribution across 5,000+ employees — with a natural-language AI assistant and a real-time executive dashboard.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Local Quickstart](#4-local-quickstart)
5. [API Reference](#5-api-reference)
6. [Database Architecture](#6-database-architecture)
7. [Frontend Pages](#7-frontend-pages)
8. [Seed Data](#8-seed-data)
9. [Architecture Decision Notes](#9-architecture-decision-notes)
10. [Environment Variables](#10-environment-variables)

---

## 1. System Overview

Ethara solves the classic enterprise problem: **who is sitting where, and what are they working on?**

| Capability | Detail |
|---|---|
| Seat allocation | Assign / release physical desk seats to employees |
| Project mapping | Map employees to one of 11 active business projects |
| Occupancy dashboard | Live metrics — 6,000 seats, 5,000 employees, 80% occupancy baseline |
| AI assistant | Natural-language queries resolved via regex intent + parameterised DB queries |
| Soft-delete | Deactivating an employee auto-releases their seat (no orphaned data) |
| Audit trail | Every AI query is written to `audit_logs` as an immutable append-only event |

---

## 2. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Backend API** | FastAPI | 0.115.5 |
| **ORM** | SQLAlchemy (async) | 2.0.36 |
| **Migrations** | Alembic | 1.14.0 |
| **Schema validation** | Pydantic + pydantic-settings | v2 |
| **Database** | PostgreSQL | 16-alpine (Docker) |
| **Async driver** | asyncpg | 0.30.0 |
| **Sync driver** (Alembic) | psycopg2-binary | 2.9.10 |
| **Frontend** | Next.js 14 (App Router) | 14.2.35 |
| **Styling** | Tailwind CSS | 3.4.x |
| **Language** | TypeScript | 5.x |
| **Seed tool** | Faker | 40.x |
| **Container runtime** | Docker Desktop (WSL2) | — |

---

## 3. Project Structure

```
ethara-seat-allocation-system/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory + router mounts
│   │   ├── config.py          # pydantic-settings config
│   │   ├── database.py        # async engine + session factory
│   │   ├── models/            # SQLAlchemy 2.0 ORM models
│   │   │   ├── enums.py       # ProjectStatus, EmployeeStatus, SeatStatus, AllocationStatus
│   │   │   ├── project.py
│   │   │   ├── employee.py
│   │   │   ├── seat.py
│   │   │   ├── seat_allocation.py
│   │   │   └── audit_log.py
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── routers/
│   │       ├── projects.py    # GET/POST /projects/
│   │       ├── employees.py   # GET/POST /employees/, DELETE /employees/{id}
│   │       ├── seats.py       # GET/POST /seats/, /available, /allocate, /release
│   │       ├── dashboard.py   # GET /dashboard/stats
│   │       └── ai.py          # POST /ai/query
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── seed.py                # Idempotent Faker-based data seeder
│   └── requirements.txt
├── frontend/
│   └── app/
│       ├── page.tsx           # Executive Cockpit dashboard (/)
│       ├── employees/
│       │   └── page.tsx       # Personnel Registry (/employees)
│       └── projects/
│           └── page.tsx       # Project Infrastructure map (/projects)
├── docs/
│   └── database_schema.md     # Mermaid ER diagram + full schema docs
├── docker-compose.yml
├── .env.example
├── .gitignore
├── AI_PROMPTS.md
└── README.md
```

---

## 4. Local Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (with WSL2 Linux engine running)
- Git

---

### Step 1 — Clone and configure environment

```bash
git clone https://github.com/your-org/ethara-seat-allocation-system.git
cd ethara-seat-allocation-system

# Copy environment template
cp .env.example .env
# Edit .env if needed — defaults work for local Docker setup
```

---

### Step 2 — Start PostgreSQL via Docker

```bash
docker-compose up -d postgres
```

Wait for the healthcheck to pass (≈ 10 seconds):

```bash
docker ps        # STATUS should show "(healthy)"
```

---

### Step 3 — Set up the Python virtual environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

### Step 4 — Run database migrations

```bash
# From backend/
alembic upgrade head
```

This creates all 5 tables and 4 PostgreSQL ENUM types:

| Table | Purpose |
|---|---|
| `projects` | Business project registry |
| `employees` | Workforce records |
| `seats` | Physical desk inventory (floor / zone / bay / seat) |
| `seat_allocations` | Append-only allocation history |
| `audit_logs` | Immutable event ledger (AI queries, admin actions) |

---

### Step 5 — Seed baseline data

```bash
# From backend/
python seed.py

# Smaller run for development
python seed.py --employees 500

# Preview what would be created without writing to DB
python seed.py --dry-run
```

**Expected output:**

```
[1/4] Projects  — Created 11 projects.
[2/4] Seats     — Created 6000 seats (5 floors x 10 zones x 12 bays x 10 seats).
[3/4] Employees — Created 5000 employees.
[4/4] Seat Allocations — Created 4000 seat allocations (80.0% occupancy).
Seed complete. All data loaded successfully.
```

The seeder is **idempotent** — re-running it on a populated database safely skips all steps.

---

### Step 6 — Start the FastAPI backend

```bash
# From backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)  
ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)  
Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 7 — Start the Next.js frontend

```bash
cd frontend
npm install
npm run dev
```

App: [http://localhost:3000](http://localhost:3000)

---

### Full Docker stack (optional)

```bash
# Start all services (postgres + backend + frontend)
docker-compose up --build

# Stop all services
docker-compose down

# Destroy database volume (full reset)
docker-compose down -v
```

---

## 5. API Reference

### Root

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API metadata |
| `GET` | `/health` | Liveness + DB reachability (`{"status":"ok","db":"connected"}`) |

---

### Projects — `/projects`

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `GET` | `/projects/` | — | List all projects |
| `POST` | `/projects/` | `{name, description?, manager_name?}` | Create a project |

---

### Employees — `/employees`

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `GET` | `/employees/` | — | List all employees |
| `POST` | `/employees/` | `{employee_code, name, email, department?, role?, joining_date, project_id?}` | Create an employee |
| `DELETE` | `/employees/{id}` | — | Soft-deactivate + auto-release active seat |

**Soft-delete cascade:**
1. Sets `employee.status = inactive`
2. Finds active `SeatAllocation` for this employee (if any)
3. Sets `allocation.allocation_status = released`, stamps `released_date`
4. Sets `seat.status = available`
5. Returns `{"seat_released": true/false}`

---

### Seats — `/seats`

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `GET` | `/seats/` | — | List all seats |
| `POST` | `/seats/` | `{floor, zone, bay, seat_number}` | Register a new seat |
| `GET` | `/seats/available` | — | List only available seats |
| `POST` | `/seats/allocate` | `{employee_id, seat_id}` | Allocate a seat to an employee |
| `POST` | `/seats/release` | `{employee_id}` | Release the employee's active seat |

**Allocate error codes:**

| Code | Condition |
|---|---|
| `404` | Employee or seat not found |
| `409` | Seat already occupied/reserved |
| `409` | Employee already has an active allocation |
| `409` | Concurrent write conflict (IntegrityError) |

---

### Dashboard — `/dashboard`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/stats` | Live aggregate metrics |

**Response shape:**

```json
{
  "employees": 5000,
  "projects": 11,
  "total_seats": 6000,
  "occupied_seats": 4000,
  "available_seats": 2000,
  "reserved_seats": 0,
  "active_allocations": 4000,
  "occupancy_percentage": 66.67
}
```

All values are computed on request via `func.count()` aggregations — never cached.

---

### AI Assistant — `/ai`

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/ai/query` | `{"query": "<free text>"}` | Natural-language seat/project lookup |

**Intent classification (regex-based, no external LLM required):**

| Intent | Trigger pattern | Example query |
|---|---|---|
| `find_seat_by_email` | Email regex + `seat/where/sitting` | `"Where is jane.smith@ethara.com seated?"` |
| `find_seat_by_name` | `where is … seated/sit` | `"Where is John Smith seated?"` |
| `project_assignment` | `which project / assigned to` | `"Which project is Sara assigned to?"` |
| `available_seats_by_floor` | `available seat / free seat` + optional `floor N` | `"Show available seats on floor 3"` |
| `seat_utilization_by_project` | `how many / occupied / utilization` + project name | `"How many seats are occupied for Project Atlas?"` |
| `unknown` | No match | Returns help text listing supported queries |

Every call — regardless of intent — appends an entry to `audit_logs` with `action = "ai_query"`, the matched intent, query text, and generated answer.

---

## 6. Database Architecture

### Entity Relationships

```
projects (1) ──── (N) employees
projects (1) ──── (N) seat_allocations  [snapshot FK, SET NULL on delete]
employees (1) ─── (N) seat_allocations  [RESTRICT on delete]
seats (1) ──────── (N) seat_allocations  [RESTRICT on delete]
```

### Key Constraints

| Constraint | Type | Enforces |
|---|---|---|
| `uq_active_seat_per_employee` | **Partial UNIQUE** `WHERE allocation_status='active'` | One active seat per employee |
| `uq_active_alloc_per_seat` | **Partial UNIQUE** `WHERE allocation_status='active'` | One active occupant per seat |
| `uq_seat_location` | `UNIQUE(floor, zone, seat_number)` | No duplicate seat addresses |
| `uq_employees_email` | `UNIQUE(email)` | No duplicate employee emails |
| `uq_employees_code` | `UNIQUE(employee_code)` | No duplicate employee codes |

### Seat Address Format (seeded)

Seats are addressed as `floor / zone / bay / seat_number`.  
`seat_number` embeds the bay index to satisfy `uq_seat_location`:

```
Floor 2, Zone C, Bay-4, B04-S07
        └─ unique within (floor=2, zone=C)
```

---

## 7. Frontend Pages

| Route | File | Description |
|---|---|---|
| `/` | `app/page.tsx` | Executive Cockpit — occupancy ring, metric cards, live seat dot map, AI teaser |
| `/employees` | `app/employees/page.tsx` | Personnel Registry — searchable table, soft-delete button |
| `/projects` | `app/projects/page.tsx` | Project Infrastructure — headcount cards, allocation weight bars, workforce share |

All pages:
- Use the `"use client"` directive
- Fetch from `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)
- Render skeleton shimmer during data load
- Display error states if the API is unreachable
- Apply the shared obsidian design system from `globals.css`

---

## 8. Seed Data

`backend/seed.py` is an **idempotent** standalone script (separate from Alembic) that populates the database with realistic baseline data.

| Dimension | Value |
|---|---|
| Projects | 11 named (Atlas, Helios, Orion, Nova, Titan, Apex, Nexus, Horizon, Zenith, Aurora, Vanguard) |
| Floors | 5 |
| Zones per floor | 10 (A–J) |
| Bays per zone | 12 |
| Seats per bay | 10 |
| **Total seats** | **6,000** |
| Employees | 5,000 (Faker-generated, deterministic seed=42) |
| Allocation rate | 80% → **4,000 active allocations** |
| Departments | 10 (Engineering, Product, Design, Data Science, Finance, Legal, HR, Operations, Marketing, DevOps) |

**Idempotency mechanism:** Each seeding function checks `SELECT COUNT(*) FROM <table>` before writing. If rows exist, it prints a skip message and returns the existing data. `INSERT ... ON CONFLICT DO NOTHING` is used for seats (handles partial failure recovery against the `uq_seat_location` constraint).

---

## 9. Architecture Decision Notes

### UUID Primary Keys

All tables use `UUID` PKs generated at the application layer (`uuid.uuid4()`), not `SERIAL` integers. This enables:
- Distributed ID generation without DB round-trips
- Safe data migration between environments
- Frontend-predictable IDs (can optimistically insert with known ID)

### Append-Only Seat Allocations

`seat_allocations` is never updated in place — it is append-only history.  
When a seat is released, a new `released_date` is stamped and `allocation_status` is set to `released`. The original allocation row is preserved intact. This enables:
- Full audit trail of who sat where and when
- Time-range queries (`when did employee X leave desk Y?`)
- Partial unique indexes that only constrain `active` rows, allowing historical duplicates

### Partial Unique Indexes (PostgreSQL-specific)

```sql
CREATE UNIQUE INDEX uq_active_seat_per_employee
  ON seat_allocations (employee_id)
  WHERE allocation_status = 'active';

CREATE UNIQUE INDEX uq_active_alloc_per_seat
  ON seat_allocations (seat_id)
  WHERE allocation_status = 'active';
```

Standard `UNIQUE` constraints would block re-allocating a seat after release. Partial indexes only enforce uniqueness on active rows, so history accumulates freely.

### New Joiner Flow

New employees are created via `POST /employees/` without a seat. Seating is a separate intentional step via `POST /seats/allocate`. This decouples onboarding from physical desk availability — a new joiner can be in the system (and assigned to a project) before a desk is ready.

### Soft Delete Design

Employees are never hard-deleted. `DELETE /employees/{id}` marks `status = inactive` and cascade-releases the seat. Inactive employees remain in `seat_allocations` history. This preserves:
- Historical seat occupancy data
- Audit trail integrity
- Project assignment history

### AI Query — No External LLM Dependency

The `POST /ai/query` endpoint uses regex-based intent classification rather than an external LLM. This means:
- Zero API cost
- Zero latency for intent resolution
- Fully deterministic and testable
- Extensible: intents can be added as new regex patterns

LLM integration (Gemini / OpenAI) is designed as an opt-in upgrade via `GEMINI_API_KEY` / `OPENAI_API_KEY` in `.env`.

### Client-Side Project Utilization Aggregation

The `/projects` frontend page intentionally does **not** require a `/dashboard/project-utilization` backend endpoint. It fetches `/projects/` and `/employees/` in parallel and aggregates `project_id` counts with `useMemo`. This:
- Avoids a backend schema change
- Keeps the backend stateless and thin
- Remains accurate because employee records are the single source of truth for project assignments

---

## 10. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | App environment label |
| `SECRET_KEY` | *(must set)* | JWT / session signing key |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async SQLAlchemy connection (app runtime) |
| `SYNC_DATABASE_URL` | `postgresql+psycopg2://...` | Sync connection (Alembic + seed.py) |
| `POSTGRES_USER` | `ethara` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `ethara_password` | PostgreSQL password |
| `POSTGRES_DB` | `ethara_db` | PostgreSQL database name |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed CORS origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL exposed to Next.js browser client |
| `GEMINI_API_KEY` | *(optional)* | Gemini API key for future LLM intent upgrade |
| `OPENAI_API_KEY` | *(optional)* | OpenAI API key for future LLM intent upgrade |

---

## License

Internal engineering project — Ethara Seat Allocation System.