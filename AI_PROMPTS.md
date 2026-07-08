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

*(to be filled when models + migrations are created)*

---

## 3. Backend APIs

*(to be filled when CRUD endpoints are implemented)*

---

## 4. Seat Allocation Logic

*(to be filled when allocate/release logic is implemented)*

---

## 5. AI Assistant

*(to be filled when /ai/query endpoint is implemented)*

---

## 6. Frontend

*(to be filled when frontend pages are built)*

---

## 7. Testing

*(to be filled when tests are written)*

---

## 8. Debugging

*(to be filled as issues arise)*

---

## 9. Deployment

*(to be filled when deployment config is finalized)*

---

## 10. Refactoring

*(to be filled when refactoring passes are made)*
