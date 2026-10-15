# Scholarship Finder

React frontend, FastAPI backend, scholarship discovery through the fastn MCP gateway.

## Phase 1: backend core and fastn connection

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # then set FASTN_API_KEY and confirm the gateway URL/auth settings
python -m scripts.verify_fastn          # connect and list tools
pytest                                  # unit tests
uvicorn app.main:app --reload           # http://localhost:8000/docs
```

Diagnostics: `GET /api/health`, `GET /api/fastn/status`, `GET /api/fastn/tools`.

`/api/fastn/status` returns connection diagnostics even when the gateway is
unavailable. `/api/fastn/tools` returns the discovered MCP tools or a typed
error response. The local health endpoint does not depend on fastn availability.

No database in Phase 1. Folders `agent/`, `tools/`, `vector/`, `services/` are placeholders for Phase 2.
