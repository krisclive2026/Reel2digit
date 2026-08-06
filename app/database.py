import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
 
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./reeltodigit_v2.db")
 
# Some hosts hand out URLs starting with "postgres://", but SQLAlchemy
# 1.4+/2.x requires the "postgresql://" scheme.
if DB_PATH.startswith("postgres://"):
    DB_PATH = DB_PATH.replace("postgres://", "postgresql://", 1)
 
# Force the pg8000 driver (pure Python, no compiled C extension needed).
# This keeps the image portable across the self-hosted Postgres container
# (docker-compose service "db") without worrying about psycopg2's compiled
# binary matching the container's base image/architecture.
if DB_PATH.startswith("postgresql://") and "+pg8000" not in DB_PATH:
    DB_PATH = DB_PATH.replace("postgresql://", "postgresql+pg8000://", 1)
 
is_sqlite = DB_PATH.startswith("sqlite")
is_postgres = DB_PATH.startswith("postgresql")
 
engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif is_postgres:
    engine_kwargs["pool_pre_ping"] = True  # drop stale connections instead of erroring
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
 
engine = create_engine(DB_PATH, **engine_kwargs)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
Base = declarative_base()
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
