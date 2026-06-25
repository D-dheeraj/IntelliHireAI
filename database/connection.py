import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Detect Streamlit Cloud environment
IS_STREAMLIT_CLOUD = os.getenv("STREAMLIT_SERVER_PORT") is not None or os.path.exists("/mount/src")

if IS_STREAMLIT_CLOUD:
    # Default to SQLite on Streamlit Cloud if DATABASE_URL is not set in secrets
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///intellihire.db")
else:
    # Default to PostgreSQL for local Docker setup
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/intellihire")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()