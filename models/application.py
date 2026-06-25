from sqlalchemy import Column, Integer, Float, String, ForeignKey

from models.base import Base


class Application(Base):

    __tablename__ = "applications"

    application_id = Column(Integer, primary_key=True)

    candidate_id = Column(
        Integer,
        ForeignKey("candidates.candidate_id", ondelete="CASCADE")
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.job_id", ondelete="CASCADE")
    )

    match_score = Column(Float)

    status = Column(String(50))
