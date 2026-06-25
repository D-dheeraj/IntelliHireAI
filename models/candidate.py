from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from models.base import Base


class Candidate(Base):

    __tablename__ = "candidates"


    candidate_id = Column(
        Integer,
        primary_key=True
    )


    name = Column(
        String(100)
    )


    email = Column(
        String(100),
        nullable=True
    )


    phone = Column(
        String(20),
        nullable=True
    )


    experience = Column(
        String(100),
        nullable=True
    )


    education = Column(
        String(200),
        nullable=True
    )


    resume_text = Column(
        Text
    )


    skills = Column(
        Text,
        nullable=True
    )


    match_score = Column(
        Integer,
        nullable=True
    )


    ai_summary = Column(
        Text,
        nullable=True
    )


    recommendation = Column(
        Text,
        nullable=True
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )