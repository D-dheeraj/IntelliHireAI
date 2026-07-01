"""
IntelliHire AI — Manager Agent
================================
Orchestrates the full resume-screening pipeline:

    Resume Agent  →  extracts candidate info (name, email, experience …)
    Skill Agent   →  identifies technical & soft skills
    Matching Agent →  scores candidate vs job description

All database writes and audit logging go through the IntelliHire MCP Server
(mcp/server.py).  The MCP tools are called *in-process* here, which keeps
the code 100 % cloud-safe while still using the real FastMCP tool definitions
that can be exercised via `mcp dev mcp/server.py` locally.

Architecture
------------
                  ┌─────────────────────────────┐
                  │      Manager Agent          │
                  │  (this file)                │
                  └──────────┬──────────────────┘
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    Resume Agent       Skill Agent      Matching Agent
    (Gemini call)      (Gemini call)    (Gemini call)
           └─────────────────┼─────────────────┘
                             ▼
                  ┌──────────────────────┐
                  │  IntelliHire MCP     │
                  │  Server (FastMCP)    │
                  │  mcp/server.py       │
                  │  ─────────────────   │
                  │  • save_candidate_record  │
                  │  • log_agent_action       │
                  │  • link_logs_to_candidate │
                  │  • get_all_candidates     │
                  │  • get_candidate_audit_trail│
                  │  • remove_candidate       │
                  └──────────┬───────────┘
                             ▼
                      SQLite / PostgreSQL DB
"""

import importlib.util
import os
import sys

from agents.resume_agent import analyze_resume
from agents.skill_agent import extract_skills
from agents.matching_agent import match_candidate

# ── Import MCP tool functions ──────────────────────────────────────────────────
# We load mcp/server.py via importlib to avoid a name collision with the
# `mcp` package's own `mcp.server` sub-module. The tool functions defined
# with @mcp.tool() are called in-process here (cloud-safe), while the same
# server can be run standalone with `mcp dev mcp/server.py` for local demos.
_server_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mcp", "server.py",
)
_spec = importlib.util.spec_from_file_location("intellihire_mcp_server", _server_path)
_mcp_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mcp_module)

save_candidate_record    = _mcp_module.save_candidate_record
log_agent_action         = _mcp_module.log_agent_action
link_logs_to_candidate   = _mcp_module.link_logs_to_candidate
get_all_candidates       = _mcp_module.get_all_candidates
get_candidate_audit_trail = _mcp_module.get_candidate_audit_trail


def run_intellihire(resume_text: str, job_description: str) -> dict:
    """
    Full IntelliHire pipeline: parse resume → extract skills → match job.

    Takes raw resume text and a job description, runs it through all three
    specialist agents, persists everything via MCP tools, and returns a
    structured result dict.

    Args:
        resume_text:     Plain-text content of the uploaded resume.
        job_description: Job requirements entered by the recruiter.

    Returns:
        dict with keys: candidate, resume, skills, match
    """

    # ── Step 0: Log pipeline start ─────────────────────────────────────────────
    log_agent_action(
        agent_name="Manager Agent",
        action="Workflow started",
    )

    # ── Step 1: Resume Agent — extract structured candidate info ───────────────
    log_agent_action(
        agent_name="Resume Agent",
        action="Analyzing resume",
        input_data=resume_text[:300],   # store first 300 chars for audit
    )
    resume_data = analyze_resume(resume_text)
    log_agent_action(
        agent_name="Resume Agent",
        action="Resume analyzed",
        output_data=str(resume_data),
    )

    # ── Step 2: Skill Agent — identify technical & soft skills ─────────────────
    log_agent_action(
        agent_name="Skill Agent",
        action="Extracting skills",
    )
    skill_data = extract_skills(resume_text)
    log_agent_action(
        agent_name="Skill Agent",
        action="Skills extracted",
        output_data=skill_data.get("skills_text", ""),
    )

    # ── Step 3: Matching Agent — score candidate vs job description ────────────
    log_agent_action(
        agent_name="Matching Agent",
        action="Matching candidate against job description",
        input_data=skill_data.get("skills_text", ""),
    )
    match_data = match_candidate(
        skill_data.get("skills_text", ""),
        job_description,
    )
    log_agent_action(
        agent_name="Matching Agent",
        action="Match complete",
        output_data=str(match_data),
    )

    # ── Step 4: Persist via MCP — save_candidate_record tool ──────────────────
    log_agent_action(
        agent_name="Manager Agent",
        action="Persisting candidate record via MCP",
    )
    saved = save_candidate_record(
        name=resume_data.get("name"),
        email=resume_data.get("email"),
        phone=resume_data.get("phone"),
        experience=resume_data.get("experience"),
        education=resume_data.get("education"),
        resume_text=resume_text,
        skills=skill_data.get("skills_text", ""),
        match_score=match_data.get("match_score", 0),
        ai_summary=resume_data.get("ai_summary", ""),
        recommendation=match_data.get("recommendation", ""),
    )

    candidate_id = saved.get("candidate_id")

    # ── Step 5: Link audit logs to this candidate via MCP ─────────────────────
    if candidate_id:
        link_logs_to_candidate(candidate_id=candidate_id, limit=10)

    # ── Step 6: Log workflow completion ────────────────────────────────────────
    log_agent_action(
        agent_name="Manager Agent",
        action="Workflow complete",
        candidate_id=candidate_id,
        output_data=f"score={match_data.get('match_score', 0)}, "
                    f"rec={match_data.get('recommendation', '')}",
    )

    # ── Fetch the persisted ORM object for the Streamlit UI ───────────────────
    # The UI expects a Candidate ORM object at result["candidate"]. We retrieve
    # it from the DB so the Streamlit app doesn't need any changes.
    candidate_orm = _get_candidate_orm(candidate_id)

    return {
        "candidate": candidate_orm,
        "resume":    resume_data,
        "skills":    skill_data,
        "match":     match_data,
    }


def _get_candidate_orm(candidate_id: int | None):
    """
    Fetch the ORM Candidate object by ID for the Streamlit UI layer.
    Returns None if candidate_id is None or lookup fails.
    """
    if candidate_id is None:
        return None
    try:
        from database.connection import SessionLocal
        from models.candidate import Candidate

        db = SessionLocal()
        candidate = db.query(Candidate).filter(
            Candidate.candidate_id == candidate_id
        ).first()
        db.close()
        return candidate
    except Exception:
        return None
