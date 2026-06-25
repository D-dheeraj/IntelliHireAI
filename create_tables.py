from database.connection import engine
from models.base import Base

from models.candidate import Candidate
from models.job import Job
from models.application import Application
from models.skill import Skill
from models.agent_log import AgentLog


print("Creating tables...")

Base.metadata.create_all(bind=engine)

print("Tables created successfully ✅")