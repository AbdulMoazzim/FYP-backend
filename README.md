# FYP Backend — Milestone 1

**Deliverable:** a working FastAPI backend that stores requirements and creates events for them, backed by PostgreSQL.

This is the foundation for the Multi-Agent Scrum Platform described in the project proposal. It doesn't do any AI/agent reasoning yet — it just gives the platform a reliable place to record requirements and the events they generate, which is what the Event Processing Engine / Agent Orchestrator will read from later.

## What's included

- `Project`, `Requirement`, `Event` SQLAlchemy models
- Requirement API: create, list (filterable by project), get, update, delete
- **Requirement → Event creation**: creating, updating, or deleting a requirement automatically writes a matching row to the `events` table (`requirement_created`, `requirement_updated`, `requirement_deleted`), in the same DB transaction
- Event retrieval API: read-only, filterable by project, requirement, and event type
- Auto-generated interactive docs via FastAPI (Swagger UI + ReDoc)

## Why it's structured this way

- **`events` is one generic table, not one table per event type.** The orchestrator that reacts to events (a later milestone) needs to handle many event kinds — sprint events, task events, meeting events, etc. — so `event_type` + a JSON `payload` column keeps that extensible without a schema migration every time a new event type is added.
- **Event creation lives in `crud.py`, not the route handler.** `create_requirement`, `update_requirement`, and `delete_requirement` all write their event as part of the same function/transaction, so a requirement can never exist in the DB without its corresponding event (no risk of the API layer forgetting to log one).
- **No POST endpoint for events.** Events are a side effect of other actions, not something a client should be able to fabricate directly — that would break the audit trail the agents will eventually rely on for reasoning.

## Project layout

```
fyp-backend/
├── app/
│   ├── main.py            # FastAPI app, mounts routers, creates tables
│   ├── config.py          # Settings (reads DATABASE_URL from .env)
│   ├── database.py        # Engine, session, declarative Base
│   ├── models.py          # Project, Requirement, Event ORM models
│   ├── schemas.py         # Pydantic request/response models
│   ├── crud.py            # DB logic, incl. the Requirement -> Event hook
│   └── routers/
│       ├── projects.py    # Minimal Project endpoints (create/list/get)
│       ├── requirements.py
│       └── events.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Install PostgreSQL and create a database

```bash
# Using psql, once PostgreSQL is running locally:
createdb fyp_platform
```

### 2. Set up the Python environment

```bash
cd fyp-backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# then edit .env with your actual Postgres credentials, e.g.:
# DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/fyp_platform
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

On first run, `Base.metadata.create_all()` creates the `projects`, `requirements`, and `events` tables automatically — no manual migration needed for this milestone. (Once the schema starts changing after data exists, switch to Alembic — it's already in `requirements.txt` and ready to be initialized with `alembic init alembic`.)

The API is now available at `http://localhost:8000`, with interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API reference

### Projects
*(Minimal — just enough to attach requirements to something. Full project management is a later milestone.)*

| Method | Path              | Description        |
|--------|-------------------|---------------------|
| POST   | `/projects`       | Create a project    |
| GET    | `/projects`       | List projects        |
| GET    | `/projects/{id}`  | Get one project      |

### Requirements

| Method | Path                    | Description                                  |
|--------|-------------------------|-----------------------------------------------|
| POST   | `/requirements`         | Create a requirement → also emits `requirement_created` event |
| GET    | `/requirements`         | List requirements (optional `?project_id=`)  |
| GET    | `/requirements/{id}`    | Get one requirement                          |
| PATCH  | `/requirements/{id}`    | Update a requirement → emits `requirement_updated` event |
| DELETE | `/requirements/{id}`    | Delete a requirement → emits `requirement_deleted` event |

### Events *(read-only)*

| Method | Path            | Description                                                                 |
|--------|-----------------|-------------------------------------------------------------------------------|
| GET    | `/events`       | List events, optionally filtered by `project_id`, `requirement_id`, `event_type` |
| GET    | `/events/{id}`  | Get one event                                                                |

## Example walkthrough

This mirrors the "Requirement Added" example from the project proposal:

```bash
# 1. Create a project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "E-Commerce Platform"}'
# -> note the returned "id"

# 2. Add a requirement (this is Step 1 from the proposal's walkthrough)
curl -X POST http://localhost:8000/requirements \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id_from_above>",
    "title": "Stripe payments",
    "description": "Users should be able to pay using Stripe."
  }'
# -> a "requirement_created" event is written automatically

# 3. Confirm the event was generated
curl "http://localhost:8000/events?project_id=<project_id_from_above>"
```

## What's intentionally NOT here

Per the project's scope, this milestone does not include:
- Agent logic / reasoning / orchestration (that consumes `/events` — future milestone)
- Sprint, backlog, or task models
- Authentication/authorization
- Alembic migrations (create_all is fine until the schema needs to change under real data)

## Testing

A quick way to sanity-check the API without a real Postgres instance is FastAPI's `TestClient` with a SQLite URL:

```bash
export DATABASE_URL="sqlite:///./test.db"
python3 -c "
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
print(client.get('/health').json())
"
```
