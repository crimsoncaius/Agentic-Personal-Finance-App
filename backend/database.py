# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sqlite3
import os

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./finance.db"
DATABASE_PATH = "./finance.db"

# Create the engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal is used to get database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_connection():
    """Get a raw SQLite database connection."""
    # Ensure the database file exists
    if not os.path.exists(DATABASE_PATH):
        Base.metadata.create_all(bind=engine)

    try:
        # Create a connection with row factory to return dictionaries
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise RuntimeError(f"Failed to connect to database: {str(e)}")
