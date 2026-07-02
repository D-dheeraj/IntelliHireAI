# IntelliHire AI 🧠

Hiring is exhausting. Screening 50 resumes for one job opening takes hours — and even then, you might miss the best candidate. I built IntelliHire AI to fix that.

Upload a resume PDF, paste the job description, and the system does the rest. It reads every resume, extracts the important details, scores each candidate against your requirements, and gives you a straight answer: hire, maybe, or no.

Powered by **Google Gemini**. Built with a **multi-agent pipeline**, a real **FastMCP server**, **role-based authentication**, and **Streamlit**.

---

## Live Demo

**Try it here →** https://intellihireai-j7giq7gmf7svpy6whnt8b2.streamlit.app/

- **Candidates** — upload your resume, get an instant AI score. No login needed.
- **Recruiters** — sign in with admin credentials to access the full dashboard.

---

## What it actually does

When a resume and job description are submitted, here's the full pipeline:

1. Resume PDF is parsed and raw text is extracted
2. **Resume Agent** → extracts name, email, phone, experience, and education via Gemini
3. **Skill Agent** → identifies all technical and soft skills via Gemini
4. **Matching Agent** → compares candidate skills against job requirements, scores 0–100 via Gemini
5. **MCP Server** → all database writes go through the FastMCP server (agents are fully stateless)
6. Results are stored persistently in PostgreSQL (Neon) — visible to recruiters in the dashboard

The output includes a match score, recommendation (Strong Hire / Hire / Maybe / No Hire), matched skills, and skill gaps.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| UI | Streamlit |
| AI / LLM | Google Gemini API (`google-genai`) |
| **MCP Server** | **FastMCP (`mcp[cli]>=1.0.0`)** |
| PDF Parsing | pypdf |
| Database | **Neon (PostgreSQL)** for cloud / SQLite for local |
| ORM | SQLAlchemy |
| Charts | Plotly |
| Authentication | Session-state based role system (Admin + Candidate) |
| Environment | python-dotenv |

---

## Authentication

The app has two access levels:

| Role | Access | How to enter |
|---|---|---|
| **Candidate** | Upload & analyze own resume only | Click "Continue as Candidate" — no login needed |
| **Admin / Recruiter** | Full dashboard, all candidates, delete, batch screening | Username + password login |

Admin credentials are set via environment variables — never hardcoded.

---

## MCP Server — Model Context Protocol

IntelliHire AI uses a real **FastMCP server** (`mcp/server.py`) that exposes all database operations as protocol-compliant MCP tools. No agent touches the database directly — all persistence flows through the MCP server.

### Architecture

```
Streamlit UI
     │
     ├── Candidate View  (resume upload → own result only)
     └── Admin View      (dashboard, all candidates, batch screening)
          │
          ▼
     Manager Agent
       ├── Resume Agent    ──► Gemini API  (name, email, experience…)
       ├── Skill Agent     ──► Gemini API  (technical & soft skills)
       └── Matching Agent  ──► Gemini API  (match score, recommendation)
            │
            │  MCP tools called in-process (Streamlit Cloud safe)
            ▼
     ┌─────────────────────────────────────────┐
     │   IntelliHire MCP Server (FastMCP)     │
     │   mcp/server.py                        │
     │   ──────────────────────────────────── │
     │   • save_candidate_record              │
     │   • log_agent_action                   │
     │   • link_logs_to_candidate             │
     │   • get_all_candidates                 │
     │   • get_candidate_audit_trail          │
     │   • remove_candidate                   │
     └─────────────────┬───────────────────────┘
                       │
                       ▼
              Neon PostgreSQL (cloud) / SQLite (local)
```

### MCP Tools (6 total)

| Tool | What it does |
|---|---|
| `save_candidate_record` | Persist full candidate profile to DB |
| `log_agent_action` | Write a structured audit log for every agent step |
| `link_logs_to_candidate` | Backfill log rows with candidate ID after save |
| `get_all_candidates` | Fetch all candidates (recruiter dashboard) |
| `get_candidate_audit_trail` | Full audit trail for one candidate |
| `remove_candidate` | Delete candidate and all associated logs |

### Run MCP Demo locally

```bash
source .venv/bin/activate

# See all 6 MCP tools in action (great for demo / video)
python demo_mcp.py

# Run as standalone MCP server (stdio transport)
mcp run mcp/server.py

# Launch MCP Inspector browser UI (requires Node.js)
mcp dev mcp/server.py
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
GEMINI_API_KEY=your_gemini_api_key_here      # required
GEMINI_MODEL=gemini-flash-latest             # optional (default)
DATABASE_URL=sqlite:///intellihire.db        # local SQLite (default)
# DATABASE_URL=postgresql://...              # Neon / Supabase for cloud
ADMIN_USERNAME=admin                         # recruiter login username
ADMIN_PASSWORD=your_strong_password_here     # recruiter login password
```

> **`.env` is never committed to GitHub** — it is in `.gitignore`. Never paste secrets in code.

Get a free Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### Streamlit Cloud Secrets

For the deployed app, add these in **App Settings → Secrets**:

```toml
GEMINI_API_KEY = "your_key"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your_password"
DATABASE_URL   = "postgresql://user:pass@host/db?sslmode=require"
```

---

## Cloud Database — Neon (PostgreSQL)

For persistent data on Streamlit Cloud, the app uses [Neon](https://neon.tech) — a free serverless PostgreSQL service. Tables are created automatically on first run via SQLAlchemy's `create_all()`.

**To set up Neon:**
1. Create a free account at [neon.tech](https://neon.tech)
2. Create a new project (e.g. `intellihire`)
3. Copy the connection string from the dashboard
4. Add it as `DATABASE_URL` in Streamlit Secrets

> Without a PostgreSQL URL, the app falls back to SQLite — which resets on every Streamlit Cloud restart.

---

## Running it locally

You'll need Python 3.11+ and a Google Gemini API key.

**Step 1 — Clone**

```bash
git clone https://github.com/D-dheeraj/IntelliHireAI.git
cd IntelliHireAI
```

**Step 2 — Configure environment**

```bash
cp .env.example .env
# Open .env and fill in GEMINI_API_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
```

**Step 3 — Run setup**

```bash
bash setup.sh
```

This creates the virtual environment, installs all dependencies (including `mcp[cli]`), initializes the database, and starts the app.

Open **http://localhost:8501** in your browser.

---

## Project Structure

```
IntelliHireAI/
│
├── app/
│   └── streamlit_app.py        ← main UI with auth routing (Admin / Candidate)
│
├── agents/
│   ├── manager_agent.py        ← pipeline orchestrator, calls MCP tools
│   ├── resume_agent.py         ← extracts candidate info from resume text
│   ├── skill_agent.py          ← extracts technical & soft skills
│   └── matching_agent.py       ← scores candidate vs job description
│
├── mcp/
│   └── server.py               ← FastMCP server with 6 @mcp.tool() endpoints
│
├── services/
│   ├── gemini_service.py       ← Gemini API client with retry logic
│   ├── pdf_service.py          ← PDF text extraction
│   ├── database_service.py     ← raw DB operations (used by MCP server)
│   └── query_service.py        ← read-only query helpers
│
├── models/                     ← SQLAlchemy ORM models (Candidate, AgentLog…)
├── database/
│   └── connection.py           ← auto-selects SQLite or PostgreSQL from env
├── dashboards/
│   └── dashboard.py            ← Plotly charts for recruiter dashboard
│
├── demo_mcp.py                 ← live demo of all 6 MCP tools (local only)
├── create_tables.py            ← manual DB setup (run once if needed)
├── setup.sh                    ← one-command local setup script
├── .env.example                ← copy to .env and add credentials
├── docker-compose.yml          ← optional local PostgreSQL via Docker
└── pyproject.toml              ← Python dependencies
```

---

## Database

**Local:** SQLite — `intellihire.db` is created automatically, no setup needed.

**Cloud (Streamlit):** Neon PostgreSQL — add the connection string to Streamlit Secrets. Tables are created automatically on first run.

**Optional local PostgreSQL** via Docker:

```bash
docker compose up -d
# Then set DATABASE_URL in .env:
DATABASE_URL=postgresql://admin:admin123@localhost:5432/intellihire
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Run `bash setup.sh` |
| App loads but freezes on analysis | Check `GEMINI_API_KEY` is set in `.env` |
| API key error | Confirm `.env` has `GEMINI_API_KEY=your_actual_key` |
| Port 8502 or 8503 instead of 8501 | Port was busy — new port still works fine |
| Database error on first run | Run `python create_tables.py` manually |
| `psycopg2.OperationalError` | Set `DATABASE_URL=sqlite:///intellihire.db` in `.env` |
| Streamlit Cloud data resets on restart | Add Neon PostgreSQL `DATABASE_URL` to Streamlit Secrets |
| Admin login not working | Check `ADMIN_USERNAME` and `ADMIN_PASSWORD` in Secrets / `.env` |
| `mcp dev` fails (Node.js error) | Use `python demo_mcp.py` instead |

---

## Author

Made by **Dheeraj Kumar Singh**

© 2026 — All Rights Reserved. See [LICENSE](LICENSE) for details.
