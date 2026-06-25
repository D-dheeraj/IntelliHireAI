from sqlalchemy import Column, Integer, String, Text

from models.base import Base


class Job(Base):

    __tablename__ = "jobs"

    job_id = Column(
        Integer,
        primary_key=True
    )

    job_title = Column(
        String(100)
    )

    required_skills = Column(
        Text
    )

    experience_required = Column(
        Integer
    )