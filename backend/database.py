import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()  # Load .env file automatically

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./logistics_v3.db")

# Supabase / Render PostgreSQL URLs start with postgres:// — SQLAlchemy needs postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"sslmode": "require"}

# Connection pooling for PostgreSQL (production)
pool_kwargs = {}
if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    pool_kwargs = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,  # Detects stale connections
    }

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, **pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
