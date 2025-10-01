# Tech Context

Stack

- FastAPI, Uvicorn
- SQLAlchemy 2.x, SQLite (file)
- Pydantic v2
- OpenAI Python SDK (gpt-4o-mini for NLU)
- pytest, httpx (testing)

Local setup

- Python 3.11+
- `python -m venv .venv` and install `requirements.txt`

Environment

- `DATABASE_URL` (optional; defaults to SQLite file `./revin.db`)
- `LOG_LEVEL` (INFO default)
- `OPENAI_API_KEY` (optional; enables LLM-crafted proposal SMS)
