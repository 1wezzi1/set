import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite по умолчанию, можно переопределить через env:
#   export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./debts.db")

_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False, "timeout": 10}

engine = create_engine(
    DATABASE_URL, future=True, connect_args=_connect_args
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()