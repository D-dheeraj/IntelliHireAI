# IntelliHire AI 🧠

Hiring is exhausting. Screening 50 resumes for one job opening takes hours — and even then, you might miss the best candidate. I built IntelliHire AI to fix that.

Upload the PDFs, paste the job description, and the system does the rest. It reads every resume, pulls out the important stuff, scores each candidate against your requirements, and gives you a straight answer: hire, maybe, or no.

Powered by Google Gemini. Built with a multi-agent pipeline, FastMCP server, and Streamlit.

---

## Live Demo

**Try it here →** https://intellihireai-j7giq7gmf7svpy6whnt8b2.streamlit.app/

No setup, no account needed. Just open the link and upload a resume.

---

## What it actually does

When you upload a resume and paste a job description, here's what happens behind the scenes:

1. The resume PDF gets parsed and the raw text is extracted
2. **Resume Agent** → pulls out name, email, phone, experience, and education (Gemini)
3. **Skill Agent** → identifies all technical and soft skills mentioned (Gemini)
4. **Matching Agent** → compares skills against job requirements, scores 0–100 (Gemini)
5. **MCP Server** → all database writes go through the FastMCP server (stateless agents)
6. Results are stored in a database so you can review candidates later

The final output shows you a match score, a recommendation (Strong Hire / Hire / Maybe / No Hire), which skills matched, and which ones are missing.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| UI | Streamlit |
| AI / LLM | Google Gemini API (`google-genai`) |
| **MCP Server** | **FastMCP (`mcp[cli]>=1.0.0`)** |
| PDF Parsing | pypdf |
| Database | SQLite (default) / PostgreSQL |
| ORM | SQLAlchemy |
| Charts | Plotly |
| Environment | python-dotenv |

---

## MCP Server — Model Context Protocol

IntelliHire AI uses a real **FastMCP server** (`mcp/server.py`) to expose all database operations as protocol-compliant MCP tools. Every agent is fully stateless — no agent touches the database directly. All persistence flows through the MCP server.

### Architecture

```
Streamlit UI
     │
     ▼
Manager Agent
  ├── Resume Agent    ──► Gemini API  (extracts name, email, experience…)
  ├── Skill Agent     ──► Gemini API  (identifies technical & soft skills)
  └── Matching Agent  ──► Gemini API  (scores candidate vs job description)
       │
       │  calls MCP tools in-process (cloud-safe)
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
            SQLite / PostgreSQL DB
```

### MCP Tools (6 total)

| Tool | What it does |
|---|---|
| `save_candidate_record` | Persist full candidate data to DB |
| `log_agent_action` | Write a structured audit log for every agent step |
| `link_logs_to_candidate` | Backfill log rows with candidate ID after save |
| `get_all_candidates` | Fetch all candidates (used by dashboard) |
| `get_candidate_audit_trail` | Get full audit trail for one candidate |
| `remove_candidate` | Delete a candidate and all their logs |

### Run MCP Demo / Server standalone

```bash
source .venv/bin/activate

# See all 6 tools in action — great for video demo
python demo_mcp.py

# Run as a standalone MCP server (stdio transport)
mcp run mcp/server.py

# Launch MCP Inspector browser UI (requires Node.js)
mcp dev mcp/server.py
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```
GEMINI_API_KEY=your_gemini_key_here       ← required
GEMINI_MODEL=gemini-flash-latest          ← optional (default)
DATABASE_URL=sqlite:///intellihire.db     ← optional (default)
```

> **`.env` is NOT committed to GitHub** — it is listed in `.gitignore`. Never paste your API key in code.

Get a free Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

---

## Running it locally

You'll need Python 3.11+ and a Google API key.

**Step 1 — Clone the repo**

```bash
git clone https://github.com/D-dheeraj/IntelliHireAI.git
cd IntelliHireAI
```

**Step 2 — Set up your environment**

```bash
cp .env.example .env
# Open .env and add your GEMINI_API_KEY
```

**Step 3 — Run the setup script**

```bash
bash setup.sh
```

This handles everything — creates the virtual environment, installs dependencies (`mcp[cli]` included), sets up the database, and launches the app.

Once it's running, open **http://localhost:8501** in your browser.

---

## Project layout

```
IntelliHireAI/
│
├── app/streamlit_app.py        ← the main UI
│
├── agents/
│   ├── manager_agent.py        ← orchestrates pipeline, calls MCP tools
│   ├── resume_agent.py         ← pulls info from resume text (Gemini)
│   ├── skill_agent.py          ← extracts technical + soft skills (Gemini)
│   └── matching_agent.py       ← scores candidate vs job description (Gemini)
│
├── mcp/
│   └── server.py               ← FastMCP server with 6 @mcp.tool() tools
│
├── services/
│   ├── gemini_service.py       ← Gemini API client with retry logic
│   ├── pdf_service.py          ← extracts text from uploaded PDFs
│   ├── database_service.py     ← raw DB operations (called by MCP server)
│   └── query_service.py        ← read-only query helpers
│
├── models/                     ← SQLAlchemy ORM models
├── database/connection.py      ← auto-picks SQLite or PostgreSQL
├── dashboards/dashboard.py     ← Plotly charts
│
├── demo_mcp.py                 ← run all 6 MCP tools live (demo / video)
├── create_tables.py            ← run once to set up the database
├── setup.sh                    ← one-command local setup script
├── .env.example                ← copy this → .env and add your API key
├── docker-compose.yml          ← optional PostgreSQL via Docker
└── pyproject.toml              ← Python dependencies
```

---

## Database

The app uses **SQLite by default** — no setup needed. A file called `intellihire.db` is created automatically on first run.

For PostgreSQL (multi-user / production):

```bash
docker compose up -d
# Then in .env:
DATABASE_URL=postgresql://admin:admin123@localhost:5432/intellihire
```

---

## Manual setup (if setup.sh doesn't work)

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install streamlit google-genai google-generativeai pandas plotly \
            psycopg2-binary pypdf python-dotenv sqlalchemy "mcp[cli]"

python create_tables.py
streamlit run app/streamlit_app.py
```

---

## Common problems

| What's happening | How to fix it |
|---|---|
| `streamlit: command not found` | Run `bash setup.sh` — it installs everything |
| App loads but freezes | Check that your API key is in `.env` |
| API key error | Make sure `.env` has `GEMINI_API_KEY` set correctly |
| App opens on port 8502 or 8503 | Port 8501 was busy — the new port still works |
| Database error on first run | Run `python create_tables.py` manually |
| `psycopg2.OperationalError` | Add `DATABASE_URL=sqlite:///intellihire.db` to `.env` |
| `mcp dev` fails (Node.js error) | Run `python demo_mcp.py` instead — shows all MCP tools working |

---

## Author

Made by **Dheeraj Kumar Singh**

© 2026 — All Rights Reserved. See [LICENSE](LICENSE) for details.
