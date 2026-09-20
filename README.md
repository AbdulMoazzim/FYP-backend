# FYP Backend 

Day 3

One of three agents in AGILIRO (with Product Owner Agent & Knowledge Agent). Takes project/sprint/backlog data and produces evidence-linked recommendations for blockers, risks, sprint planning, and sprint monitoring. Every recommendation cites its source and requires human approval before affecting any artifact.

## Status (Day 3)

- ✅ FastAPI skeleton (`api/`, `core/`, `db/`) + `agent_results` DB migration
- ✅ Context ingestion + prompt builder working
- 🟡 `POST /agents/scrum-master/run` live, returns hardcoded `AgentResult` for now
- ⏳ Real LLM reasoning core — Day 4

## Setup

```bash
pip install -r requirements.txt
python smoke_test.py          # end-to-end check, no LLM needed
uvicorn app.main:app --reload # run the API
```

Python · FastAPI · PostgreSQL (SQLAlchemy + Alembic) · LangChain/LangGraph · Groq

## Contributors

Abdul Moazzim · Taha Naqvi
