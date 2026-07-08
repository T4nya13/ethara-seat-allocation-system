# Requirements — Ethara Seat Allocation & Project Mapping System

> Source: **official assessment PDF** ("Vibe Coding Assessment: Ethara Seat Allocation
> & Project Mapping System"), received from Avinash Yadav. This supersedes the earlier
> version of this file, which was reconstructed from the email alone.

## 1. Objective

Full-stack app managing seat allocation for ~5,000 employees. Must let employees,
HR, Admin, and Project teams quickly answer:

- Where an employee is seated
- Which project they're assigned to
- Which floor/zone/seat is available
- Whether a new joiner has been allocated a seat
- Seat utilization by project, floor, team
- AI-based assistance for seat/project queries

## 2. Entities & Fields

### Employee
`id, employee_code, name, email, department, role, joining_date, status, project_id, created_at, updated_at`
(email must be unique; one active project per employee)

### Project
`id, name, description, manager_name, status, created_at`

Sample project names to seed: Indigo, Indreed, Mydreed, Preed, Serfy, Oreed,
bedegreed, Opreed, Serry, Kaary, Mered (11 given — spec requires minimum 10).

### Seat
`id, floor, zone, bay, seat_number, status, created_at`
Status enum: **Available / Occupied / Reserved / Maintenance**

Note: **no "Building" entity** — seat location is just floor/zone/bay/seat_number.

### SeatAllocation
`id, employee_id, seat_id, project_id, allocation_status, allocation_date, released_date`

## 3. Core Business Rules (must be enforced, not just implied)

1. One employee can have only one active seat.
2. One seat can be allocated to only one active employee.
3. Released seats become available again (history preserved, not deleted).
4. Reserved seats cannot be allocated unless status is explicitly changed.
5. New joiners should be prioritized for available seats near their project team;
   if none available in the preferred zone, suggest alternate zones.
6. Duplicate employee email not allowed.
7. Duplicate seat number on the same floor/zone not allowed.
8. Dashboard must reflect updated numbers after every allocation/release.

## 4. Required API Endpoints

**Employee**
- `POST /employees` — create
- `GET /employees` — list
- `GET /employees/{id}` — detail
- `PUT /employees/{id}` — update
- `DELETE /employees/{id}` — deactivate (not hard delete)

**Project**
- `POST /projects` — create
- `GET /projects` — list
- `GET /projects/{id}/employees` — employees on a project

**Seat**
- `POST /seats` — create
- `GET /seats` — list
- `GET /seats/available` — list available seats
- `POST /seats/allocate` — allocate seat to employee
- `POST /seats/release` — release seat

**Dashboard**
- `GET /dashboard/summary` — total seats, occupied, available, employee count
- `GET /dashboard/project-utilization` — project-wise allocation
- `GET /dashboard/floor-utilization` — floor-wise occupancy

**AI Assistant**
- `POST /ai/query`
  ```json
  // request
  { "query": "Where is my seat? My email is amit@ethara.ai" }
  // response
  { "answer": "You are allocated Floor 2, Zone B, Bay 4, Seat B4-23. Your project is Talos." }
  ```

## 5. AI Assistant — Minimum vs Advanced

**Minimum requirement:** answer things like *"Where is employee Amit seated?"* →
*"Amit is seated on Floor 2, Zone B, Bay 4, Seat B4-23. He is assigned to Project Talos."*

**Advanced (stretch):** use an LLM API or LangChain to handle a broader range of
natural-language questions about seat, project, availability, team location,
utilization. **Fallback allowed:** a keyword/intent-based assistant is explicitly
acceptable if no AI API is available — this is not a hard requirement to use a live
LLM.

Questions it should handle at minimum:
- "Where is my seat?"
- "Which project am I assigned to?"
- "Show all available seats on Floor 3."
- "Who is sitting near me?"
- "How many seats are occupied for Project Talos?"
- "Allocate a seat for a new employee joining today."

## 6. Tech Stack

| Layer | Recommended | Notes |
|---|---|---|
| Frontend | React.js / Next.js + Tailwind | responsive UI |
| Backend | Python FastAPI | REST |
| Database | PostgreSQL preferred | SQLite OK for local demo; MongoDB OK if justified |
| Deployment | Railway / Render / Vercel+Railway / Netlify+Render / Docker | pick one combo |

Optional (not required, but adds polish): Docker, Redis caching, LangChain,
OpenAI/Claude/Gemini API, CSV upload for employee-seat data.

## 7. Seed Data — Minimums

| Item | Minimum |
|---|---|
| Employees | 5,000 |
| Floors | 5 |
| Zones | 10 |
| Seats | 5,500 |
| Projects | 10 |
| Available seats | 500 |
| Reserved seats | 100 |
| Employees pending allocation | 50 |

## 8. AI_PROMPTS.md — Required Structure

Must be a real, running log (not reconstructed after the fact). Required prompt
categories, each with **output summary / what was right / what was wrong / manual
fixes / how validated**:

1. Architecture
2. Database
3. Backend APIs
4. Seat Allocation Logic
5. AI Assistant
6. Frontend
7. Testing
8. Debugging
9. Deployment
10. Refactoring

## 9. Submission Checklist

- [ ] GitHub repository
- [ ] Live frontend URL
- [ ] Live backend URL
- [ ] `README.md`
- [ ] `AI_PROMPTS.md` (structured per Section 8 above)
- [ ] Database schema
- [ ] Sample seed data
- [ ] Screenshots
- [ ] API documentation (Swagger link acceptable)
- [ ] Debugging notes
- [ ] Deployment notes
- [ ] Sample login credentials — **only if you add authentication** (not required)

## 10. Deadline

24–48 hours from receipt of assessment (per original email).