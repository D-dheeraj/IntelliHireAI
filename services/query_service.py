from database.connection import SessionLocal
from models.candidate import Candidate
from models.agent_log import AgentLog


def get_candidates():
    db = SessionLocal()
    data = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    db.close()
    return data


def get_logs_for_candidate(candidate_id):
    db = SessionLocal()
    data = (
        db.query(AgentLog)
        .filter(AgentLog.candidate_id == candidate_id)
        .order_by(AgentLog.created_at.asc())
        .all()
    )
    db.close()
    return data
