from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from models.base import Base


class AgentLog(Base):

    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True)

    candidate_id = Column(
        Integer,
        ForeignKey("candidates.candidate_id", ondelete="SET NULL"),
        nullable=True
    )

    agent_name = Column(String(100))

    action = Column(String(200))

    input_data = Column(Text)

    output_data = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
