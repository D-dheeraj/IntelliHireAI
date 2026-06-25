from database.connection import SessionLocal
from models.candidate import Candidate
from models.agent_log import AgentLog


def save_candidate(candidate_data: dict):
    """Save a candidate record. Accepts a dict of fields."""
    db = SessionLocal()

    candidate = Candidate(
        name=candidate_data.get("name"),
        email=candidate_data.get("email"),
        phone=candidate_data.get("phone"),
        experience=candidate_data.get("experience"),
        education=candidate_data.get("education"),
        resume_text=candidate_data.get("resume_text"),
        skills=candidate_data.get("skills"),
        match_score=candidate_data.get("match_score"),
        ai_summary=candidate_data.get("ai_summary"),
        recommendation=candidate_data.get("recommendation"),
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    db.close()

    return candidate


def save_agent_log(agent_name, action, candidate_id=None, input_data=None, output_data=None):
    """Save an agent log entry, optionally linked to a candidate."""
    db = SessionLocal()

    log = AgentLog(
        candidate_id=candidate_id,
        agent_name=agent_name,
        action=action,
        input_data=str(input_data) if input_data is not None else None,
        output_data=str(output_data) if output_data is not None else None,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    db.close()

    return log


def update_logs_candidate_id(candidate_id, limit=10):
    """
    Attach a candidate_id to the most recent logs that have none.
    Called after save_candidate so pipeline logs are linked.
    """
    db = SessionLocal()

    logs = (
        db.query(AgentLog)
        .filter(AgentLog.candidate_id.is_(None))
        .order_by(AgentLog.id.desc())
        .limit(limit)
        .all()
    )

    for log in logs:
        log.candidate_id = candidate_id

    db.commit()
    db.close()


def delete_candidate(candidate_id: int):
    """Delete a candidate and all their linked logs."""
    db = SessionLocal()
    candidate = db.query(Candidate).filter(
        Candidate.candidate_id == candidate_id
    ).first()
    if candidate:
        db.delete(candidate)
        db.commit()
    db.close()


def delete_all_candidates():
    """Delete all candidates and their logs."""
    db = SessionLocal()
    db.query(AgentLog).delete()
    db.query(Candidate).delete()
    db.commit()
    db.close()