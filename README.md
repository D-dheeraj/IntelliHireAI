# IntelliHire AI 🧠

Hiring is exhausting. Screening 50 resumes for one job opening takes hours — and even then, you might miss the best candidate. I built IntelliHire AI to fix that.

Upload the PDFs, paste the job description, and the system does the rest. It reads every resume, pulls out the important stuff, scores each candidate against your requirements, and gives you a straight answer: hire, maybe, or no.

Powered by Google Gemini. Built with Python and Streamlit.

---

## Live Demo

**Try it here →** [intellihireai.streamlit.app](https://intellihireai.streamlit.app)

No setup, no account needed. Just open the link and upload a resume.

---

## What it actually does

When you upload a resume and paste a job description, here's what happens behind the scenes:

- The resume PDF gets parsed and the raw text is extracted
- A resume agent pulls out name, email, phone, experience, and education
- A separate skill agent identifies all the technical and soft skills mentioned
- A matching agent compares those skills against the job requirements and assigns a score from 0 to 100
- Everything gets stored in a database so you can review candidates later

The final output shows you a match score, a recommendation (Strong Hire / Hire / Maybe / No Hire), which skills matched, and which ones are missing. You can analyze 10 resumes in the time it used to take to read one.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| UI | Streamlit |
| AI / LLM | Google Gemini API (`google-genai`) |
| PDF Parsing | pypdf |
| Database | SQLite (default) / PostgreSQL |
| ORM | SQLAlchemy |
| Charts | Plotly |
| Environment | python-dotenv |

---


## Running it locally

You'll need Python 3.11+ and a Google API key. The key is free — get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

**Step 1 — Clone the repo**

```bash
git clone https://github.com/dheerajkumarsingh/IntelliHireAI.git
cd IntelliHireAI
```

**Step 2 — Set up your API key**

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your actual key:

```
GOOGLE_API_KEY=your_key_here
```

**Step 3 — Run the setup script**

```bash
bash setup.sh
```

This handles everything — creates the virtual environment, installs dependencies, sets up the database, and launches the app. You don't need Docker or any other external tool. The app runs on SQLite by default, which just creates a local file.

Once it's running, open **http://localhost:8501** in your browser.

---



## Project layout

```
IntelliHireAI/
│
├── app/streamlit_app.py        ← the main UI
│
├── agents/
│   ├── manager_agent.py        ← coordinates the whole pipeline
│   ├── resume_agent.py         ← pulls info from resume text
│   ├── skill_agent.py          ← finds technical + soft skills
│   └── matching_agent.py       ← scores candidate vs job description
│
├── services/
│   ├── gemini_service.py       ← handles all Gemini API calls
│   ├── pdf_service.py          ← extracts text from uploaded PDFs
│   ├── database_service.py     ← saves and fetches candidate records
│   └── query_service.py        ← query helpers
│
├── models/                     ← SQLAlchemy database models
├── database/connection.py      ← auto-picks SQLite or PostgreSQL
├── dashboards/dashboard.py     ← plotly charts for the dashboard
│
├── create_tables.py            ← run once to set up the database
├── setup.sh                    ← one-command setup script
├── .env.example                ← copy this and fill in your key
├── docker-compose.yml          ← optional PostgreSQL setup via Docker
└── pyproject.toml              ← project dependencies
```

---

## Database

The app uses SQLite by default — no setup needed. When you run `bash setup.sh` or `python create_tables.py`, a file called `intellihire.db` gets created automatically in the project folder.

If you prefer PostgreSQL (better for production or multi-user scenarios), Docker is included. Start the database with:

```bash
docker compose up -d
```

Then uncomment this line in your `.env`:

```
DATABASE_URL=postgresql://admin:admin123@localhost:5432/intellihire
```

---

## Manual setup (if the script doesn't work)

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install streamlit google-genai google-generativeai pandas plotly \
            psycopg2-binary pypdf python-dotenv sqlalchemy

python create_tables.py
streamlit run app/streamlit_app.py
```

---

## Common problems

| What's happening | How to fix it |
|---|---|
| `streamlit: command not found` | Run `bash setup.sh` — it installs everything |
| App loads but freezes | Check that your API key is in `.env` |
| API key error | Make sure `.env` exists and has the key |
| App opens on port 8502 or 8503 | Port 8501 was busy — the new port still works |
| Database error on first run | Run `python create_tables.py` manually |

---

## Author

Made by **Dheeraj Kumar Singh**

© 2026 — All Rights Reserved. See [LICENSE](LICENSE) for details.
