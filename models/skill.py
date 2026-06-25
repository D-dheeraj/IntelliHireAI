from sqlalchemy import Column, Integer, String, ForeignKey

from models.base import Base


class Skill(Base):

    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True)

    candidate_id = Column(
        Integer,
        ForeignKey("candidates.candidate_id", ondelete="CASCADE")
    )

    skill_name = Column(String(100))
