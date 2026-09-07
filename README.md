# Screen / RAG

A role-based AI technical interview system. The interview is built from the candidate's uploaded resume, selected role, and retrieved passages from the supplied ML books. The backend persists the full context -> question -> answer -> evaluation chain.

## Architecture

```mermaid
flowchart LR
  Resume[PDF/TXT resume] --> Parser[Extract and normalize]
  Parser --> Analyzer[Structured resume analysis]
  Analyzer --> Context[Role + candidate query]
  Books[Provided books] --> Ingest[Extract, chunk, index]
  Ingest --> Vector[(Local vector index)]
  Context --> Retrieve[Role-filtered retrieval]
  Vector --> Retrieve
  Retrieve --> Generate[Structured question generation]
  Generate --> Interview[FastAPI session]
  Interview --> DB[(SQLite)
  ]
  DB --> Report[Persisted summary]
```

## System flow

Resume -> Processing -> Context construction -> RAG -> Question generation -> Interview -> Storage -> Results.

## Implemented features

- PDF and TXT resume upload with size/type validation and extraction errors.
- Conservative, non-fabricating resume analysis for skills, technologies, domains, and project evidence.
- Role registry for AI/ML Engineer, Backend Engineer, and Data Science / Applied ML.
- Supplied books ingested into a persisted local TF-IDF-style vector index with source, page, role, and chunk metadata.
- Dynamic candidate/role/topic queries and traceable retrieved context on every question.
- Structured five-question interview sessions with persisted answers, validated evaluations, and final topic analysis.
- Responsive React UI with loading, validation, error, progress, interview, and results states.

## Setup

Python 3.11+ is recommended. This workspace is configured for Python 3.14.

```powershell
cd E:\ai-interview-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH="backend"
python -m ingestion.ingest "Knowledge-base ingestion"
uvicorn app.main:app --app-dir backend --reload --port 8000
```

The ingestion command reads the provided PDFs only; it does not embed or fabricate external content. It writes `data/vector_index.pkl` and keeps the original books in place.

Frontend requires Node.js/npm:

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` in `frontend/.env` for deployment. The API docs are available at `http://localhost:8000/docs`.

## Environment variables

Copy `.env.example` to `.env`. `DATABASE_URL`, `VECTOR_DB_PATH`, `CORS_ORIGINS`, upload limits, model names, and optional `OPENAI_API_KEY` are configurable. When `OPENAI_API_KEY` is set, question generation and answer evaluation call the configured OpenAI model with JSON output and Pydantic validation. When it is absent or unavailable, the local deterministic fallback keeps the development flow runnable and records the same retrieval trace.

## API lifecycle

- `GET /api/roles`
- `POST /api/resumes` multipart upload
- `POST /api/sessions` with `candidate_id` and `role`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/questions/{question_id}/answers`
- `GET /api/sessions/{session_id}/results`

The session creation response includes an access token. Send it as `X-Session-Token` on all subsequent session, answer, and results requests. The database stores only a SHA-256 hash of this token.

For local development, SQLite tables are created on startup when `AUTO_CREATE_SCHEMA=true`. Production should set `AUTO_CREATE_SCHEMA=false` and use Alembic migrations instead.

If an older local SQLite database was created before session tokens were added, the development startup performs a non-destructive schema repair in place. Existing rows are preserved; newly created sessions receive fresh tokens. For a clean production database, use Alembic rather than this development repair path.

## PostgreSQL migration

Install the backend requirements, then create an empty PostgreSQL database and set its connection URL in `.env`:

```powershell
DATABASE_URL=postgresql+psycopg://screen_user:strong_password@localhost:5432/screen_rag
AUTO_CREATE_SCHEMA=false
```

Run migrations from the backend directory:

```powershell
cd E:\ai-interview-system\backend
$env:PYTHONPATH="."
..\.venv\Scripts\python.exe -m alembic upgrade head
```

Check the current revision with `..\.venv\Scripts\python.exe -m alembic current`. For a model change, create a revision with `..\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe change"`, inspect the generated file, then apply it with `upgrade head`. Roll back one revision with `downgrade -1`.

For a fresh Docker deployment, the backend image can be started after the database is reachable, then the same `alembic upgrade head` command should be run once before starting application workers. Do not use `create_all()` in production.

## Testing

```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

The tests cover parsing, analysis, dynamic context, retrieval metadata, report structure, API validation, five-question progression, answer persistence, and final results without external API calls.

## Deployment and demo

Run the FastAPI app behind a production ASGI server and build the frontend with `npm run build`, serving `frontend/dist` from a static host. Configure the deployed API URL and CORS origins through environment variables. A demo video URL is intentionally not claimed until one is recorded against the working deployment.

For a containerized local deployment, copy `.env.example` to `.env`, then run `docker compose up --build`. The frontend is served by Nginx and the backend persists its SQLite database and vector index in the `app-data` volume. A PostgreSQL deployment should replace the Compose SQLite URL with `postgresql+psycopg://...`, set `AUTO_CREATE_SCHEMA=false`, and run Alembic before serving traffic.
