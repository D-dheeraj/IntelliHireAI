"""
IntelliHire AI — MCP Server
============================
A proper Model Context Protocol (MCP) server built with FastMCP.

Exposes database and logging operations as MCP tools so that agents
remain fully stateless and all persistence goes through this server.

Run standalone (for local development / MCP Inspector):
    mcp dev mcp/server.py
    mcp run mcp/server.py

The agents call these same tool functions in-process when running on
Streamlit Cloud (no subprocess needed — cloud-safe fallback).
"""

import sys
import os

# Make sure the project root is on the path when server is started
# directly (e.g. `mcp run mcp/server.py` from any directory).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from services.database_service import (
    save_candidate,
    save_agent_log,
    update_logs_candidate_id,
    delete_candidate as _delete_candidate,
    delete_all_candidates as _delete_all_candidates,
)
from services.query_service import get_candidates, get_logs_for_candidate

# ── MCP Server instance ────────────────────────────────────────────────────────
mcp = FastMCP(
    name="IntelliHire MCP Server",
    instructions=(
        "Provides database persistence and logging tools for the "
        "IntelliHire AI multi-agent hiring pipeline. "
        "All DB writes and reads go through this server so agents stay stateless."
    ),
)


# ── Tool 1: Save a candidate ───────────────────────────────────────────────────
@mcp.tool()
def save_candidate_record(
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    experience: str | None = None,
    education: str | None = None,
    resume_text: str | None = None,
    skills: str | None = None,
    match_score: int | None = None,
    ai_summary: str | None = None,
    recommendation: str | None = None,
) -> dict:
    """
    Persist a full candidate record to the database.

    Called by the Manager Agent after all three sub-agents (Resume, Skill,
    Matching) have finished their work. Returns the saved candidate's ID
    and name so subsequent tools can reference the record.

    Args:
        name: Full name extracted from the resume.
        email: Email address extracted from the resume.
        phone: Phone number extracted from the resume.
        experience: Work experience summary (e.g. "3 years").
        education: Highest qualification (e.g. "B.Tech Computer Science").
        resume_text: Full raw text of the resume (for audit / re-processing).
        skills: Comma-separated list of skills extracted by the Skill Agent.
        match_score: Integer 0-100 produced by the Matching Agent.
        ai_summary: 2-3 sentence professional summary produced by the Resume Agent.
        recommendation: One of "Strong Hire", "Hire", "Maybe", "No Hire".

    Returns:
        dict with keys: candidate_id, name, status
    """
    candidate_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "experience": experience,
        "education": education,
        "resume_text": resume_text,
        "skills": skills,
        "match_score": match_score,
        "ai_summary": ai_summary,
        "recommendation": recommendation,
    }
    candidate = save_candidate(candidate_data)
    if candidate:
        return {
            "candidate_id": candidate.candidate_id,
            "name": candidate.name,
            "status": "saved",
        }
    return {"candidate_id": None, "name": name, "status": "error"}


# ── Tool 2: Log an agent action ────────────────────────────────────────────────
@mcp.tool()
def log_agent_action(
    agent_name: str,
    action: str,
    candidate_id: int | None = None,
    input_data: str | None = None,
    output_data: str | None = None,
) -> dict:
    """
    Write a structured audit-log entry for an agent action.

    Provides full traceability of every step in the multi-agent pipeline
    (Manager → Resume Agent → Skill Agent → Matching Agent).

    Args:
        agent_name: Which agent is logging (e.g. "Resume Agent").
        action: Short description of what the agent did (e.g. "Resume analyzed").
        candidate_id: Optional FK to link this log row to a candidate.
        input_data: Serialised input passed to the agent (for debugging).
        output_data: Serialised output produced by the agent (for debugging).

    Returns:
        dict with keys: log_id, agent_name, action, status
    """
    log = save_agent_log(
        agent_name=agent_name,
        action=action,
        candidate_id=candidate_id,
        input_data=input_data,
        output_data=output_data,
    )
    if log:
        return {
            "log_id": log.id,
            "agent_name": agent_name,
            "action": action,
            "status": "logged",
        }
    return {"log_id": None, "agent_name": agent_name, "action": action, "status": "error"}


# ── Tool 3: Link recent logs to a candidate ────────────────────────────────────
@mcp.tool()
def link_logs_to_candidate(candidate_id: int, limit: int = 10) -> dict:
    """
    Retroactively attach a candidate_id to the most recent un-linked log rows.

    Because log entries are written *before* the candidate record exists (we
    log each agent step as it happens), this tool is called right after
    save_candidate_record to backfill the FK.

    Args:
        candidate_id: The ID returned by save_candidate_record.
        limit: Maximum number of recent un-linked logs to update (default 10).

    Returns:
        dict with keys: candidate_id, updated_count (approximate), status
    """
    update_logs_candidate_id(candidate_id, limit=limit)
    return {
        "candidate_id": candidate_id,
        "updated_count": limit,
        "status": "linked",
    }


# ── Tool 4: Fetch all candidates (summary list) ────────────────────────────────
@mcp.tool()
def get_all_candidates() -> dict:
    """
    Return a summary list of all candidates stored in the database.

    Useful for the Manager Agent to check existing records before
    processing a new resume (deduplication) and for dashboard queries.

    Returns:
        dict with key: candidates (list of dicts with id, name, score, recommendation)
    """
    candidates = get_candidates()
    return {
        "candidates": [
            {
                "candidate_id": c.candidate_id,
                "name": c.name,
                "email": c.email,
                "match_score": c.match_score,
                "recommendation": c.recommendation,
            }
            for c in candidates
        ]
    }


# ── Tool 5: Fetch logs for a specific candidate ────────────────────────────────
@mcp.tool()
def get_candidate_audit_trail(candidate_id: int) -> dict:
    """
    Return the full audit trail (all agent log entries) for a candidate.

    Useful for debugging a pipeline run or reviewing exactly what each
    agent did when processing a specific resume.

    Args:
        candidate_id: The candidate whose logs to retrieve.

    Returns:
        dict with key: logs (list of dicts with agent_name, action, timestamps)
    """
    logs = get_logs_for_candidate(candidate_id)
    return {
        "logs": [
            {
                "log_id": log.id,
                "agent_name": log.agent_name,
                "action": log.action,
                "input_data": log.input_data,
                "output_data": log.output_data,
                "created_at": str(log.created_at),
            }
            for log in logs
        ]
    }


# ── Tool 6: Delete a candidate ─────────────────────────────────────────────────
@mcp.tool()
def remove_candidate(candidate_id: int) -> dict:
    """
    Delete a candidate and all their associated audit-log rows.

    Args:
        candidate_id: ID of the candidate to remove.

    Returns:
        dict with keys: candidate_id, status
    """
    _delete_candidate(candidate_id)
    return {"candidate_id": candidate_id, "status": "deleted"}


# ── Entrypoint (for `mcp run mcp/server.py`) ──────────────────────────────────
if __name__ == "__main__":
    mcp.run()
