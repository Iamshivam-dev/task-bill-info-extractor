import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Session # For type hinting in dependencies
from .config import BASE_DIR


DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "receipts.db")



engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables defined in your models
def create_db_and_tables():
    """Creates all database tables based on Base metadata."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")