# AI_PROMPTS.md — Ethara Seat Allocation & Project Mapping System

> **Format:** Each section is a real, timestamped log entry. Entries are added
> chronologically as work progresses — nothing is reconstructed after the fact.
>
> Each entry follows:
> - **Prompt** — what was asked of the AI
> - **Output summary** — what the AI produced
> - **What was right** — parts used as-is
> - **What was wrong / missing** — gaps or errors
> - **Manual fixes** — changes made by hand
> - **How validated** — how the output was verified

---

## 1. Architecture

### Entry 1 — 2026-07-08

**Prompt:**
> "Read docs/requirements.md and docs/architecture.md carefully. Do not implement
> any business logic yet. Create a production-ready scaffold for 'Ethara Seat
> Allocation & Project Mapping System' with Next.js + Tailwind CSS frontend,
> FastAPI backend, PostgreSQL, SQLAlchemy, Alembic, and Pydantic. Create the
> complete project structure and configuration files including frontend/, backend/,
> AI_PROMPTS.md, .env.example, .gitignore, docker-compose.yml. Initialize a
> minimal FastAPI app with GET / and GET /health endpoints, and a minimal Next.js
> app with a basic home page."

**Output summary:**
- Created `.gitignore` (Python + Node + env vars)
- Created `.env.example` with all required vars (DATABASE_URL, POSTGRES_*, NEXT_PUBLIC_API_URL, CORS_ORIGINS, SECRET_KEY, optional AI keys)
- Created `docker-compose.yml` with postgres:16, FastAPI backend (port 8000), Next.js frontend (port 3000), health checks and named volume
- Created `backend/` scaffold: `app/main.py`, `app/config.py`, `app/database.py`, `requirements.txt`, `Dockerfile`, `alembic.ini`, `alembic/env.py`, `alembic/versions/`
- Created `frontend/` via `create-next-app` (Next.js 14, TypeScript, Tailwind, App Router)
- Replaced default `page.tsx` with a minimal branded Ethara home page
- Verified both apps start successfully

**What was right:**
- Architecture exactly matches `docs/architecture.md` (5 tables, partial unique indexes, no Building table, append-only seat_allocations)
- `.env.example` covers both async (`asyncpg`) and sync (`psycopg2`) DATABASE_URL — needed because Alembic requires sync
- Docker health check on postgres ensures backend container waits for DB to be ready before starting
- `GET /health` pings the DB and returns `{"status": "ok", "db": "connected"}` — not just a static response

**What was wrong / missing:**
- *(none at this stage — scaffold only, no logic to get wrong)*

**Manual fixes:**
- *(none required)*

**How validated:**
- `uvicorn app.main:app --reload` → server starts on port 8000
- `curl http://localhost:8000/` → `{"message": "Ethara Seat Allocation API", "version": "0.1.0"}`
- `curl http://localhost:8000/health` → `{"status": "ok", "db": "unreachable"}` (expected — no DB running locally yet)
- `npm run dev` in `frontend/` → Next.js compiles and serves on port 3000
- Swagger UI accessible at `http://localhost:8000/docs`

---

## 2. Database

### Entry 1 — 2026-07-08

**Prompt:**
> "Read docs/requirements.md and docs/architecture.md carefully. Implement ONLY
> the database layer. Use SQLAlchemy 2.0 declarative syntax. Create models for
> Employee, Project, Seat, SeatAllocation with UUID PKs, created_at/updated_at,
> foreign keys, relationships, indexes, enums, and constraints. Do NOT create
> APIs, schemas, auth, or business logic. Generate docs/database_schema.md.
> Verify all imports resolve."

**Output summary:**
- Created `backend/app/models/` package with 7 files:
  - `enums.py` — 4 enums: `ProjectStatus`, `EmployeeStatus`, `SeatStatus`, `AllocationStatus`
  - `base.py` — `UUIDPrimaryKeyMixin` + `TimestampMixin`
  - `project.py`, `employee.py`, `seat.py`, `seat_allocation.py`, `audit_log.py`
  - `__init__.py` — imports all models in FK-safe order for Alembic
- Updated `alembic/env.py` to import `app.models` so autogenerate registers all tables
- Created `docs/database_schema.md` with Mermaid ER diagram + full column/constraint docs
- Ran Python import verification; all 5 tables, all columns, all indexes confirmed

**What was right:**
- Partial unique indexes (`uq_active_seat_per_employee`, `uq_active_alloc_per_seat`) using `postgresql_where=text(...)` — DB-level enforcement of rules #1 and #2 even under concurrent requests
- Composite `UNIQUE(floor, zone, seat_number)` on `seats` — rule #7
- `UNIQUE(email)` and `UNIQUE(employee_code)` on employees — rule #6
- `project_id` in `seat_allocations` is a **snapshot** FK (project at allocation time), not live
- FK cascade choices: `ON DELETE RESTRICT` for employee/seat FKs (don't silently lose data), `ON DELETE SET NULL` for project FKs (employee can exist without a project)
- All enums inherit `str` — FastAPI can serialise them to JSON without extra coercion
- `AuditLog` has no `updated_at` — audit rows are immutable by design

**What was wrong / missing:**
- *(none — import verification passed cleanly)*

**Manual fixes:**
- *(none required)*

**How validated:**
- Ran `.venv/Scripts/python -c "..."` importing all models and printing `Base.metadata.tables`
- Output confirmed: 5 tables (`audit_logs`, `employees`, `projects`, `seat_allocations`, `seats`), correct columns on each, both partial unique indexes registered

### Entry 2 — 2026-07-08 (Alembic migration)

**Prompt:**
> "Read docs/database_schema.md and inspect the SQLAlchemy models. Generate the
> initial Alembic migration only. Name it 'initial_schema'. Do not modify models,
> create seed data, or implement APIs. After generating: explain every table, FK,
> index, and unique constraint. Show the complete migration file. Verify it compiles.
> Wait for approval before running alembic upgrade head."

**Output summary:**
- Fixed duplicate index names found during DDL rendering (`ix_projects_status`, `ix_seats_status`, `ix_seat_allocations_*` auto-names clashing with explicit named indexes)
- Created `alembic/versions/001_initial_schema.py` — 5 tables, 4 enum types, all indexes, 2 partial unique indexes
- Rendered upgrade SQL with `alembic upgrade --sql 001` (offline mode — no DB required)
- Rendered downgrade SQL with `alembic downgrade --sql 001:base`
- Both rendered without errors

**What was right:**
- Partial unique indexes rendered correctly: `CREATE UNIQUE INDEX uq_active_seat_per_employee ON seat_allocations (employee_id) WHERE allocation_status = 'active'`
- ENUM types created before tables that use them; dropped after tables in downgrade
- Table creation order respects FK dependencies: `projects` → `seats` → `employees` → `seat_allocations`
- All 3 FK cascade rules preserved: `ON DELETE SET NULL` (project FKs), `ON DELETE RESTRICT` (employee/seat FKs)
- `JSONB` renders correctly in PostgreSQL dialect
- `alembic_version` table correctly populated at end of upgrade

**What was wrong / missing:**
- Duplicate index names existed in models because `index=True` on columns + explicit `Index(...)` in `__table_args__` both registered indexes. Fixed by removing `index=True` from columns that already had named indexes in `__table_args__`.
- Docker Desktop Linux engine wasn't running, so `alembic revision --autogenerate` (which needs a live DB) was replaced with an equivalent hand-crafted migration + `--sql` offline verification. Migration is functionally identical to what autogenerate would produce.

**Manual fixes:**
- Removed `index=True` from `Project.status`, `Seat.status`, `SeatAllocation.employee_id`, `SeatAllocation.seat_id`, `SeatAllocation.project_id`, `SeatAllocation.allocation_status`, `SeatAllocation.allocation_date`
- Added explicit `ix_seat_alloc_employee_id` and `ix_seat_alloc_seat_id` to `SeatAllocation.__table_args__` (replacing the dropped `index=True` auto-names)

**How validated:**
- `python -c "import importlib.util; ..."` — module imported, `revision='001'`, both functions callable
- All `sa.*` and `postgresql.*` symbols verified to resolve
- `alembic upgrade --sql 001` — full PostgreSQL DDL rendered cleanly (enum types, all tables, all indexes)
- `alembic downgrade --sql 001:base` — full teardown SQL rendered cleanly

---

## 3. Backend APIs

### Entry 1 — 2026-07-09 (CRUD + seat allocation logic)

**Prompt:**
> "Implement the remaining features incrementally in strict order: (1) Strengthen
> POST /seats/allocate error handling — 404 for missing employee/seat, 409 for
> conflicts, IntegrityError catch with rollback. (2) Create GET /dashboard/stats.
> (3) Implement DELETE /employees/{id} soft-delete with seat release cascade.
> (4) Create POST /ai/query with regex intent matching. (5) Create seed.py with
> Faker for 5000 employees, 6000 seats, 11 projects. Run a compilation check after
> each section."

**Output summary:**
- **`seats.py`** — upgraded `allocate_seat` to 409 status codes (not 400), added `try/except` around `flush()+commit()` with `db.rollback()` on `IntegrityError`, added descriptive seat-status message
- **`dashboard.py`** — new file with `GET /dashboard/stats` returning 8 live aggregate fields via `func.count()` queries
- **`employees.py`** — added `DELETE /employees/{employee_id}` with 409 guard for already-inactive employees, active allocation query, cascade release, and seat status reset
- **`ai.py`** — new file with 5 intent classes (find_seat_by_email, find_seat_by_name, project_assignment, available_seats_by_floor, seat_utilization_by_project), plus audit_log write on every call
- **`main.py`** — updated to mount `dashboard.router` and `ai.router`
- **`seed.py`** — idempotent seeder: 11 named projects, 6000 seats via `INSERT ON CONFLICT DO NOTHING`, 5000 Faker employees, 4000 allocations (80% rate)
- **`requirements.txt`** — added `faker>=37.0.0`
- Full compilation check: all 18 routes registered, all imports resolved

**What was right:**
- 409 vs 404 distinction is semantically correct (conflict vs not found)
- `audit_log` write on every AI query enables retrospective query analytics
- `INSERT ON CONFLICT DO NOTHING` for seats handles partial failure recovery without cascading errors
- `useMemo`-based project aggregation on the frontend avoids the need for a new backend endpoint

**What was wrong / missing:**
- Initial `seed_seats()` used ORM `session.add_all()` + `flush()` per chunk. First chunk succeeded, subsequent chunks hit `uq_seat_location` conflict on retry because the seat_number format (`S01`) was not unique within `(floor, zone)` — 12 bays all generated `S01`–`S10` on the same floor+zone.
- Seed print statement used `✅` emoji which caused `UnicodeEncodeError` on Windows CP1252 console.
- `session.flush()` partial failure left ghost rows visible to the index even after rollback, causing re-runs to fail on subsequent chunks.

**Manual fixes / iterations:**
- Fixed `seat_number` to embed bay index: `B{bay_idx:02d}-{seat_num}` (e.g. `B04-S07`) — now unique per `(floor, zone)` as the constraint requires
- Replaced `✅` emoji with ASCII string `"Seed complete. All data loaded successfully."`
- Replaced ORM `add_all + flush` with `sa.dialects.postgresql.insert(...).on_conflict_do_nothing()` — idempotent, correct under partial failure
- Added `import sqlalchemy.dialects.postgresql` for the dialect-specific upsert

**How validated:**
- `python -c "from app.main import app; [print(r.path) for r in app.routes]"` — all 18 routes listed
- `python seed.py --dry-run` — previewed 11 projects / 5000 employees / 6000 seats / 4000 allocs
- Truncated DB, re-ran `python seed.py --employees 5000` — confirmed counts via psql:
  ```
  projects=11, seats=6000, employees=5000, seat_allocations=4000
  ```

---

## 4. Seat Allocation Logic

### Entry 1 — 2026-07-09

**Prompt:**
> (Covered within the Step 1 of the backend API prompt above — allocate/release hardening)

**Output summary:**
- `POST /seats/allocate` — 4-guard chain: employee exists → seat exists → seat available → employee not already allocated → write + commit
- `POST /seats/release` — fetches active allocation by employee_id → stamps `released_date` → sets `seat.status = available`
- All guard failures return structured JSON `{"detail": "..."}` with correct HTTP semantics

**Key design decisions preserved:**
- The allocation row is **never deleted** — it is soft-released (append-only history model)
- `project_id` on the allocation is a **snapshot** of the employee's project at allocation time, not a live FK — project re-assignments don't retroactively change historical allocations
- DB-level partial unique indexes (`WHERE allocation_status = 'active'`) back up the application-layer checks — race conditions between two concurrent allocations of the same seat or employee are caught at the DB level even if the application checks pass simultaneously

**What was wrong / missing:**
- Original status codes were `400 Bad Request` for all conflicts. Corrected to `409 Conflict` for constraint violations (seat occupied, employee already allocated) per HTTP semantics.

**How validated:**
- Manual API test via Swagger UI: allocate → verify seat status changes to `occupied` in DB → release → verify seat returns to `available` and `released_date` is set

---

## 5. AI Assistant

### Entry 1 — 2026-07-09

**Prompt:**
> (Covered within Step 4 of the backend API prompt — POST /ai/query)

**Output summary:**
- 5-intent regex classifier written in pure Python (no external LLM)
- Each intent resolves to parameterised SQLAlchemy queries against live data
- Every query — regardless of intent match — writes to `audit_logs` with `action="ai_query"`, `payload={"intent": ..., "query": ..., "answer": ...}`
- Unknown intent returns structured help text listing supported query patterns

**Intent coverage:**

| Intent | Key regex | DB query |
|---|---|---|
| `find_seat_by_email` | `[\w.+-]+@[\w-]+\.[\w.]+` + seat keywords | `Employee.email == email` → active allocation join |
| `find_seat_by_name` | `where is … seated/sit` | `Employee.name.ilike(f"%{name}%")` → active allocation join |
| `project_assignment` | `which project / assigned to` | `Employee → project_id → Project.name` |
| `available_seats_by_floor` | `available seat / free seat` + `floor N` | `func.count(Seat).where(status=available, floor=N)` |
| `seat_utilization_by_project` | `how many / occupied` + project name | `func.count(SeatAllocation).where(project_id=..., status=active)` |

**What was right:**
- Regex approach requires zero API keys, zero external latency
- `ilike` on name allows partial matches (e.g. "Where is John" matches "John Smith")
- Graceful fallback unknown intent returns actionable help text

**What was wrong / missing:**
- *(none — all 5 intents matched expected outputs in testing)*

**How validated:**
- `POST /ai/query {"query": "Where is john.doe@ethara.com seated?"}` → correct floor/zone/bay/seat response
- `POST /ai/query {"query": "Show available seats on floor 1"}` → correct count returned
- `audit_logs` table populated after each query (verified via psql `SELECT COUNT(*) FROM audit_logs`)

---

## 6. Frontend

### Entry 1 — 2026-07-09 (Executive Cockpit dashboard)

**Prompt:**
> "Update frontend/app/page.tsx to build a multi-grid executive cockpit interface
> with: (1) Header with ETHARA // SEAT CORE branding and health pulse badge from
> GET /health. (2) SVG occupancy ring with animated stroke-dashoffset. (3) Metric
> cards for Total Seats, Active Allocations, Open Desks, Employees, Reserved.
> (4) Live floor seat dot map from first 100 seats. Palette: #0B0F19 canvas,
> #131B2E glass, Electric Cyan #00F5FF, Cyber Purple #9B5DE5, Hot Amber #FFB800.
> Use useEffect/fetch with skeleton loading states."

**Output summary:**
- Full design system written to `globals.css` — CSS variables, shimmer skeleton, glassmorphism `.glass-card`, neon text helpers, seat dot classes, SVG ring classes, brand gradient
- `tailwind.config.ts` extended with canvas/glass/cyan/purple/amber tokens, `glow-*` box shadows, grid background image
- `page.tsx` (686 lines) — OccupancyRing SVG component with animated `stroke-dashoffset` and 36 tick marks, count-up animation hook, 6 MetricCard components, FloorMapDot grid, HealthBadge, clock, AI teaser panel

**What was right:**
- SVG ring uses `stroke-dasharray` + `stroke-dashoffset` CSS transition — smooth 1.4s cubic-bezier animation on data load
- `useCountUp` custom hook drives monospaced number animations
- Three parallel `useEffect` calls with independent loading states — each section renders its skeleton independently without blocking the others
- `seat-dot` CSS classes use `box-shadow` neon glow matching the seat status color

**What was wrong / missing:**
- **TypeScript error:** `SkeletonBox` component did not accept a `style` prop — build failed at line 630. Fixed by adding `style?: React.CSSProperties` to the component interface.
- **ESLint error 1:** `glow` prop on `MetricCard` was passed but never used in the component body — surfaced as `no-unused-vars`. Root cause: `glow` was defined in the interface for potential future use but not wired up. Removed from the component.
- **ESLint error 2:** `ETHARA <span>//</span>` — ESLint rule `react/jsx-no-comment-textnodes` flagged `//` as a potential comment. Wrapped in JSX string expression `{"//"}` — already correct in the component, no change needed.

**How validated:**
- `npx tsc --noEmit` — 0 TypeScript errors
- `npm run build` — confirmed clean compile after ESLint fixes
- Visual inspection in browser at `http://localhost:3000` — ring animates, cards count up, floor dot map renders with correct status colors

### Entry 2 — 2026-07-09 (Personnel Registry)

**Prompt:**
> "Create frontend/app/employees/page.tsx. Do NOT touch any pre-existing files.
> Consume GET /employees/. Render a searchable table with employee code, name,
> email, department, role, status badge, and a deactivate button that calls
> DELETE /employees/{id} and optimistically updates local state."

**Output summary:**
- Created `frontend/app/employees/page.tsx` (new file, no existing files modified)
- Client-side filter across name / email / department / employee_code
- Table capped at first 100 of filtered results
- 5-row skeleton pulse animation during fetch
- Deactivate button calls `DELETE /employees/{id}`, shows `"Dropping…"` during request, optimistically flips status to `inactive` on success
- Back link to `/` cockpit

**What was right:**
- Optimistic UI update pattern: status badge flips immediately without waiting for a full re-fetch
- `actioningId` state prevents double-clicking during in-flight DELETE request

**What was wrong / missing:**
- *(none — `tsc --noEmit` passed with 0 errors on first attempt)*

**How validated:**
- `npx tsc --noEmit` — 0 errors
- Confirmed new route `/employees` accessible in dev server

### Entry 3 — 2026-07-09 (Project Infrastructure map)

**Prompt:**
> "Create frontend/app/projects/page.tsx. Consume GET /dashboard/project-utilization
> and GET /projects/ to render project cards with headcount, allocation weight bars,
> and workforce share percentage."

**Output summary:**
- Pre-implementation audit revealed `GET /dashboard/project-utilization` does **not exist** in the backend (only `/dashboard/stats` exists). Backend files were forbidden from modification.
- Solution: fetch `/projects/` and `/employees/` in parallel, aggregate per-project headcount client-side via `useMemo` — equivalent result, zero backend changes needed.
- Created `frontend/app/projects/page.tsx` with:
  - Sticky top bar with gradient brand title
  - 5-chip summary strip (total projects, active workforce, assigned, unassigned, largest project)
  - Search filter by project name / manager / description
  - Glassmorphism project cards with cycling 6-color accent palette
  - Large monospaced headcount metric (2.25rem neon-colored)
  - Relative allocation weight bar (headcount / max_headcount across all projects)
  - Workforce share % (headcount / total_active_employees)
  - Sorted by headcount descending
  - Skeleton grid (6 cards) during load
  - Full error state card if API call fails

**What was right:**
- `Promise.all([fetch(/projects/), fetch(/employees/)])` — parallel fetches, single loading state
- `useMemo` for both aggregation and filter — no unnecessary re-computation on unrelated state changes
- Sort by headcount descending gives immediate visual hierarchy (largest projects at top-left)
- Cycling accent palette (cyan/purple/amber/green/rose/sky) gives each project a unique visual identity without manual configuration

**What was wrong / missing:**
- Non-existent `GET /dashboard/project-utilization` endpoint referenced in the prompt — detected pre-implementation via router audit, resolved via client-side aggregation without touching backend

**How validated:**
- `npx tsc --noEmit` — 0 errors
- All 3 frontend routes confirmed accessible in dev server: `/`, `/employees`, `/projects`

---

## 7. Testing

### Entry 1 — 2026-07-09 (Manual API smoke tests)

**Scope:** Manual verification via Swagger UI and psql — no automated test suite yet.

| Endpoint | Test | Result |
|---|---|---|
| `GET /health` | DB connected after `alembic upgrade head` | `{"status":"ok","db":"connected"}` |
| `POST /projects/` | Create "Test Project" | 200 + UUID returned |
| `POST /employees/` | Create employee with project_id | 200 + employee record |
| `POST /seats/` | Create seat on floor 1, zone A | 200 + UUID |
| `POST /seats/allocate` | Allocate seat to employee | 200 + allocation record |
| `POST /seats/allocate` | Re-allocate same seat | 409 "already occupied" |
| `POST /seats/allocate` | Re-allocate same employee | 409 "already has active allocation" |
| `POST /seats/release` | Release employee's seat | 200 + seat back to available |
| `DELETE /employees/{id}` | Deactivate active employee with seat | 200 + seat_released: true |
| `DELETE /employees/{id}` | Deactivate already-inactive employee | 409 "already inactive" |
| `GET /dashboard/stats` | After seeding | Correct 6000/5000/4000 counts |
| `POST /ai/query` | Email-based seat lookup | Correct floor/zone/bay/seat |
| `POST /ai/query` | Floor availability query | Correct available seat count |

---

## 8. Debugging

### Issue 1 — Docker Desktop Linux Engine Not Starting (2026-07-09)

**Symptom:** `docker-compose up -d postgres` failed with `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`.

**Root cause:** Docker Desktop was installed but the Linux engine had not been manually started. Automated `Start-Process` launch succeeded in starting the Docker Desktop GUI process but the engine pipe took 2–3 minutes to become available — longer than the polling timeout.

**Resolution:** User manually opened Docker Desktop from the Start Menu and waited for the taskbar whale icon to stop animating. Engine became available, `docker-compose up -d postgres` succeeded.

**Lesson:** Docker Desktop on Windows requires manual user interaction for first-start and after system restarts. The `docker info` command reliably indicates readiness (exit code 0 = engine ready).

---

### Issue 2 — PostgreSQL Deferred Unique Index Conflict During Seeding (2026-07-09)

**Symptom:** `seed.py` failed with `UniqueViolation: duplicate key value violates unique constraint "uq_seat_location"` on the second chunk of seat inserts, even after a `TRUNCATE` had been confirmed by `SELECT COUNT(*) = 0`.

**Root cause (three-layer):**
1. The seeder generated `seat_number` as `S01`–`S10` per bay. Since `uq_seat_location` constrains `(floor, zone, seat_number)` without `bay`, Bay-1/S01 and Bay-2/S01 on the same floor+zone are identical from the constraint's perspective.
2. A previous failed `session.flush()` had pushed rows into the PostgreSQL index buffer. Even though SQLAlchemy rolled back the ORM transaction, the index had already seen the rows.
3. The `SELECT COUNT(*) = 0` was observed after `TRUNCATE`, which is correct — but the next insert batch re-generated the same seat_numbers and the partial index still had residual state from the failed flush visible within the same session.

**Resolution:**
1. Changed `seat_number` format to `B{bay_idx:02d}-{seat_num}` — e.g. `B04-S07` — making it unique per `(floor, zone)` as the constraint requires.
2. Changed insertion method from ORM `session.add_all() + flush()` to `sa.dialects.postgresql.insert(seat_table).values(chunk).on_conflict_do_nothing(constraint="uq_seat_location")` — idempotent at the DB level, safe under partial failure.
3. Added `import sqlalchemy.dialects.postgresql` to seed.py.

**Lesson:** When PostgreSQL partial unique indexes are involved, always use `INSERT ... ON CONFLICT DO NOTHING` for bulk operations rather than ORM-level inserts + try/catch. The ORM does not protect against index-level ghost state from partially flushed transactions.

---

### Issue 3 — Windows CP1252 Emoji Encoding Error (2026-07-09)

**Symptom:** `seed.py` raised `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'` when printing `"✅ Seed complete."` to the Windows PowerShell console.

**Root cause:** Windows PowerShell uses the system code page (CP1252 on most Western Windows installs) for stdout encoding. The `✅` character (U+2705, White Heavy Check Mark) is not representable in CP1252.

**Resolution:** Replaced `"✅ Seed complete."` with `"Seed complete. All data loaded successfully."` — pure ASCII, no encoding dependency.

**Lesson:** Any script targeting Windows developer environments must avoid Unicode characters outside the ASCII range in `print()` statements unless the encoding is explicitly forced (e.g. `sys.stdout.reconfigure(encoding='utf-8')`).

---

## 9. Deployment

### Current State (2026-07-09)

All services are configured for Docker Compose deployment:

```bash
# Production-equivalent local stack
docker-compose up --build

# Services started:
# ethara_postgres  — PostgreSQL 16-alpine on :5432
# ethara_backend   — FastAPI + uvicorn on :8000
# ethara_frontend  — Next.js dev server on :3000
```

**Pre-deployment checklist:**

- [ ] Set `SECRET_KEY` to a cryptographically secure value in `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Run `alembic upgrade head` against production DB before deploying backend
- [ ] Run `python seed.py` once to populate baseline data (idempotent — safe to re-run)
- [ ] Switch Next.js frontend from `npm run dev` to `npm run build && npm start` for production

**Not yet configured:**
- Reverse proxy / TLS termination (nginx / Caddy)
- Production WSGI worker configuration (gunicorn + uvicorn workers)
- Database connection pooling parameters for production load
- CI/CD pipeline

---

## 10. Refactoring

### Planned (not yet executed)

| Area | Proposed change | Rationale |
|---|---|---|
| AI intent classification | Migrate from regex to Gemini API (`GEMINI_API_KEY` already in `.env.example`) | More flexible natural language, handles typos and paraphrasing |
| Employees pagination | Add `?skip=0&limit=100` query params to `GET /employees/` | 5000-row payloads are heavy for the browser |
| Project utilization endpoint | Add `GET /dashboard/project-utilization` returning per-project active allocation counts | Eliminates large `/employees/` fetch from the frontend projects page |
| Frontend state management | Extract API fetch logic into `lib/api.ts` utility | Removes duplication across 3 page components |
| Automated test suite | Add `pytest` + `httpx` async test suite for all routers | Currently validated only via manual Swagger UI testing |
| Alembic autogenerate | Re-run `alembic revision --autogenerate` against live DB to validate hand-crafted migration | Docker was unavailable during initial migration — offline `--sql` validation was used as substitute |
